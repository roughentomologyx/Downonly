import logging
import json
import dbFunctions
from web3 import Web3
import requests, os
from typing import Dict, Any
from pathlib import Path
from helper import *
import shutil

# Setting up the logging configuration
logging.basicConfig(filename='app.log', level=logging.DEBUG,  # Changed to DEBUG to capture more details
                    format='%(asctime)s:%(levelname)s:%(message)s')

CONTRACT_PATH = './contracts/dutchAuction.json'
INFURA_URL = os.getenv('INFURA_URL')
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')
distance = os.getenv('NOMINT_DISTANCE')
dbhost = os.getenv('DBHOST')
backup_user = os.getenv('BACKUP_USER')
backup_pass = os.getenv('BACKUP_PW')


def load_contract_abi_and_address(path):
    """Load contract ABI and address from a JSON file."""
    try:
        logging.debug("Loading contract ABI from path: %s", path)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Contract ABI file not found at path: {path}")
        with open(path, 'r') as file:
            contract_data = json.load(file)
        logging.info("Contract ABI loaded successfully from: %s", path)
        return contract_data
    except FileNotFoundError:
        logging.error("Contract ABI file not found at path: %s", path)
    except json.JSONDecodeError as e:
        logging.error("Error decoding JSON from the contract ABI file at %s: %s", path, e)
    except Exception as e:
        logging.error("Unexpected error loading contract ABI from %s: %s", path, e)
    return None


def getLastUnsuccessfulBCObject(web3, contract_abi, contract_address, last_known_block):
    """
    Fetches the oldest event from the specified smart contract starting from the last known block
    where jobState is not "done".
    """
    logging.debug("Fetching last unsuccessful blockchain object starting from block: %s", last_known_block)
    try:
        contract = web3.eth.contract(address=contract_address, abi=contract_abi)
        event_filter = contract.events.AuctionSale.create_filter(from_block=int(last_known_block))
        events = event_filter.get_all_entries()
        logging.info("Number of events fetched: %d", len(events))

        if len(events) >= 2:
            logging.info("Multiple events found, processing...")

        for event in events:
            mintID = event["args"]["mintID"]
            jobState = dbFunctions.read_value_from_column('jobState', mintID)
            logging.debug("Event mintID: %s, JobState in database: %s", mintID, jobState)
            if jobState != "done":
                logging.info("Found an event that is not done, returning event data")
                return Web3.to_json(event)

        logging.info("No suitable event found that meets the criteria")
    except Exception as e:
        logging.error("Error occurred while fetching blockchain object: %s", e, exc_info=True)
    return None


def convert_ipfs_url(url):
    logging.debug("Converting IPFS URL: %s", url)
    if url.startswith("https://aqua-few-camel-178.mypinata.cloud/ipfs/"):
        converted_url = "ipfs://" + url.split("/")[-1]
        logging.info("Converted IPFS URL: %s", converted_url)
        print(converted_url)
        return converted_url
    else:
        logging.error("URL does not match the expected IPFS format: %s", url)
        raise ValueError("URL does not match the expected IPFS format")


def create_ipfsjson(name, character, obstacle, surface, picIPFS, vidIPFS, glbIPFS):
    logging.debug("Creating IPFS JSON for: %s", name)
    try:
        picbaseIPFS = convert_ipfs_url(picIPFS)
        vidbaseIPFS = convert_ipfs_url(vidIPFS)
        dictionary = {
            "description": f"3D-Modell: [{glbIPFS}]({glbIPFS}) \\n Website: [https://downonly.xyz](https://downonly.xyz)",
            "external_url": "https://nikitadiakur.com/",
            "image": picbaseIPFS,
            "animation_url": vidbaseIPFS,
            "name": name,
            "attributes": [
                {"trait_type": "character", "value": character},
                {"trait_type": "obstacle", "value": obstacle},
                {"trait_type": "surface", "value": surface}
            ]
        }
        json_object = json.dumps(dictionary)
        json_file_path = f"./{name}.json"
        with open(json_file_path, "w") as outfile:
            outfile.write(json_object)
        logging.info("IPFS JSON created successfully at: %s", json_file_path)
        return json_file_path
    except Exception as e:
        logging.error("Failed to create IPFS JSON for %s: %s", name, e, exc_info=True)
        raise


def pinContentToIPFS(firstUnsuccess: Dict[str, Any], pinata_api_key: str, pinata_secret: str) -> Dict[str, Any]:
    logging.debug("Uploading content to IPFS for: %s", firstUnsuccess.get('fullname'))
    HEADERS = {
        "pinata_api_key": pinata_api_key,
        "pinata_secret_api_key": pinata_secret,
    }
    endpoint_uri = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    base_path = "./falldata/" + firstUnsuccess['fullname']
    extensions = ["glb", "mp4", "gif", "jpeg", "mp3"]

    for ext in extensions:
        file_path = Path(f"{base_path}.{ext}")
        logging.debug("Checking existence of file: %s", file_path)
        if not file_path.exists():
            logging.error("The file '%s' does not exist.", file_path)
            raise Exception(f"The file '{file_path}' does not exist.")

        try:
            with open(file_path, 'rb') as fp:
                response = requests.post(endpoint_uri, files={"file": (file_path.name, fp)}, headers=HEADERS)
                response.raise_for_status()
                response_data = response.json()
                logging.info("File %s uploaded successfully, response: %s", file_path, response_data)

                ipfs_hash = response_data.get('IpfsHash')
                if ipfs_hash:
                    ipfs_link = f"https://aqua-few-camel-178.mypinata.cloud/ipfs/{ipfs_hash}"
                    dbFunctions.update_column(f'ipfs{ext.upper()}', ipfs_link, firstUnsuccess['id'])
                else:
                    logging.error("IPFS hash not found in the response for file: %s", file_path)
                    raise Exception("IPFS hash not found in response")
        except requests.exceptions.RequestException as e:
            logging.error("HTTP request failed for %s: %s", file_path, e, exc_info=True)
            raise Exception(f"HTTP request failed for {file_path}: {e}")
        except Exception as e:
            logging.error("An error occurred while uploading %s to IPFS: %s", file_path, e, exc_info=True)
            raise


def uploadJsonToIPFS(firstUnsuccess: Dict[str, Any], pinata_api_key: str, pinata_secret: str) -> Dict[str, Any]:
    logging.debug("Uploading JSON to IPFS for: %s", firstUnsuccess.get('fullname'))
    HEADERS = {
        "pinata_api_key": pinata_api_key,
        "pinata_secret_api_key": pinata_secret,
    }
    endpoint_uri = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    json_file_path = Path(f"./{firstUnsuccess['fullname']}.json")

    if not json_file_path.exists():
        logging.error("The JSON file '%s' does not exist.", json_file_path)
        raise FileNotFoundError(f"The JSON file '{json_file_path}' does not exist.")

    try:
        with open(json_file_path, 'rb') as fp:
            response = requests.post(endpoint_uri, files={"file": (json_file_path.name, fp)}, headers=HEADERS)
            response.raise_for_status()
            response_data = response.json()
            logging.info("JSON file uploaded successfully, response: %s", response_data)

            ipfs_hash = response_data.get('IpfsHash')
            if ipfs_hash:
                ipfs_link = f"https://ipfs.io/ipfs/{ipfs_hash}"
                dbFunctions.update_column('ipfsJSON', ipfs_link, firstUnsuccess['id'])
            else:
                logging.error("IPFS hash not found in the response for JSON file: %s", json_file_path)
                raise KeyError("IPFS hash not found in response")
    except requests.exceptions.RequestException as e:
        logging.error("HTTP request failed for %s: %s", json_file_path, e, exc_info=True)
        raise Exception(f"HTTP request failed for {json_file_path}: {e}")
    except Exception as e:
        logging.error("An error occurred while uploading JSON %s to IPFS: %s", json_file_path, e, exc_info=True)
        raise


def mint(tokenURI, to_address, contract_address, owner_private_key, owner_address, provider_url, mintID):
    logging.debug("Minting NFT with tokenURI: %s to address: %s", tokenURI, to_address)
    try:
        web3 = Web3(Web3.HTTPProvider(provider_url))
        if not web3.is_connected():
            raise Exception("Error: Cannot connect to Ethereum node.")

        with open('./contracts/NFT.json', 'r') as abi_file:
            contract_abi_nft = json.load(abi_file)
        print(tokenURI)
        contract_nft = web3.eth.contract(address=contract_address, abi=contract_abi_nft)
        tx = contract_nft.functions.mintNFT(to_address, tokenURI).build_transaction({
            'from': owner_address,
            'nonce': web3.eth.get_transaction_count(owner_address),
            'gas': 300000,
            'gasPrice': web3.to_wei('20', 'gwei')
        })

        # Calculate the estimated gas cost
        estimated_gas_cost = tx['gas'] * tx['gasPrice']
        estimated_gas_cost_eth = web3.from_wei(estimated_gas_cost, 'ether')

        # Define the threshold limit for the transaction cost (in ETH)
        max_allowed_gas_cost = 0.007  # in ETH
        print(estimated_gas_cost_eth)
        # Raise an exception if the estimated cost exceeds the limit
        if estimated_gas_cost_eth > max_allowed_gas_cost:
            raise Exception(
                f"Estimated transaction cost ({estimated_gas_cost_eth} ETH) exceeds the limit of {max_allowed_gas_cost} ETH.")

        # Sign and send the transaction
        signed_tx = web3.eth.account.sign_transaction(tx, private_key=owner_private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(str(tx_hash))
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        if tx_receipt.status == 1:
            print("Transaction succeeded.")
            logging.info("Transaction succeeded with hash: %s", web3.to_hex(tx_hash))
        else:
            logging.warning("Transaction failed with hash: %s", web3.to_hex(tx_hash))
            raise Exception("Minting Transaction failed.")
        # Update OpenSea link here
        open_sea_url = f"https://testnets.opensea.io/assets/sepolia/{contract_address}/{mintID}"
        dbFunctions.update_column("openSea", open_sea_url, mintID)

        logging.info("Transaction successful with hash: %s", web3.to_hex(tx_hash))
        return tx_receipt
    except Exception as e:
        logging.error("Failed to mint NFT: %s", e, exc_info=True)
        raise Exception(e)











