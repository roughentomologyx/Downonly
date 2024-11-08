import logging
import json
import dbFunctions
from web3 import Web3
import requests, os
from typing import Dict, Any
from pathlib import Path
import logging
from helper import *
import shutil

CONTRACT_PATH = './contracts/dutchAuction.json'
INFURA_URL = os.getenv('INFURA_URL')
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')
STATE_FILE = 'motorNoMintPushCount.txt'
PUSH_COUNT_FILE = 'pushMotorOnNoMintAll.txt'
distance = os.getenv('NOMINT_DISTANCE')
dbhost=os.getenv('DBHOST')
backup_user=os.getenv('BACKUP_USER')
backup_pass=os.getenv('BACKUP_PW')



def load_contract_abi_and_address(path):
    """Load contract ABI and address from a JSON file."""
    try:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Contract ABI file not found at path: {path}")
        with open(path, 'r') as file:
            print(path)
            contract_data = json.load(file)
        #print(contract_data)
        return contract_data
    except FileNotFoundError:
        logging.error(f"Contract ABI file not found at path: {path}")
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from the contract ABI file at {path}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error loading contract ABI from {path}: {e}")

    return None

def getLastUnsuccessfulBCObject(web3, contract_abi, contract_address, last_known_block):
    """
    Fetches the oldest event from the specified smart contract starting from the last known block
    where jobState is not "done".
    """
    contract = web3.eth.contract(address=contract_address, abi=contract_abi)
    print("test")
    event_filter = contract.events.AuctionSale.create_filter(from_block=int(last_known_block))
    events = event_filter.get_all_entries()
    #mintID as anchor
    if len(events) >= 2:
        print("..........")
        print(events)
        print(len(events))
        print("..........")
        print("multiple events found")
    for event in events:


        print("1")
        mintID = event["args"]["mintID"]

        jobState = dbFunctions.read_value_from_column('jobState', mintID)  # Utilize the read_value_from_column function
        print("jobstate")
        print(jobState)
        if jobState != "done":
            return Web3.to_json(event)  # Return the first event that meets the criteria
    print("BCquery returned none")
    return None  # Return None if no suitable event is found


def convert_ipfs_url(url):
    if url.startswith("https://ipfs.io/ipfs/"):
        return "ipfs://" + url.split("/")[-1]
    else:
        raise ValueError("URL does not match the expected IPFS format")






def create_ipfsjson(name, character, obstacle, surface, picIPFS, vidIPFS, glbIPFS):
    '''
    {"description": "Ugly f*cker", "external_url": "https://nikitadiakur.com/", "image": "ipfs://QmUYxWDCcXAbVe4UCTV52MdYRfmUoKhhdGMab2m68NabN5", "animation_url": "ipfs://QmVHsPUUoxmWvP4yogUf9GnnKXoPMjBVRsipyzLUYEvEPc", "name": "Frank 3", "attributes": [{"trait_type": "character", "value": "asd"}, {"trait_type": "obstacle", "value": "asd2"}, {"trait_type": "surface", "value": "asd3"}]}

    :return:
    '''
    picbaseIPFS = converted_url = convert_ipfs_url(picIPFS)
    glbbaseIPFS = convert_ipfs_url(glbIPFS)
    dictionary = {

        "description": f"video: [{vidIPFS}]({vidIPFS})",
        "external_url": "https://nikitadiakur.com/",
        "image": picbaseIPFS,
        "animation_url": glbbaseIPFS,
        "name": name,
        "attributes": [
            {
                "trait_type": "character",
                "value": character
            },
            {
                "trait_type": "obstacle",
                "value": obstacle
            },
            {
                "trait_type": "surface",
                "value": surface
            }]
    }
    # Serializing json
    json_object = json.dumps(dictionary)  # , indent = 4
    print(json_object)
    # Writing to sample.json
    with open("./"+name+".json", "w") as outfile:
        outfile.write(json_object)
        outfile.close()
    return "./"+name+".json"



def pinContentToIPFS(
    firstUnsuccess: Dict[str, Any], pinata_api_key: str, pinata_secret: str
) -> Dict[str, Any]:

    HEADERS = {
        "pinata_api_key": pinata_api_key,
        "pinata_secret_api_key": pinata_secret,
    }

    endpoint_uri = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    base_path = "./falldata/" + firstUnsuccess['fullname']
    extensions = ["json", "glb", "mp4","gif","jpeg","mp3"]
    responses = {}
    mvsource = os.path.join("..", firstUnsuccess['fullname']+".json")
    mvdestination = base_path = "./falldata/" + firstUnsuccess['fullname']+".json"

    # Move and overwrite if the file exists
    shutil.copy2(mvsource, mvdestination)
    for ext in extensions:
        file_path = Path(f"{base_path}.{ext}")

        if file_path.exists():
            print(f"The file '{file_path}' exists.")
        else:
            print(f"The file '{file_path}' does not exist.")
            #responses[ext] = {"error": f"The file '{file_path}' does not exist."}
            raise Exception (f"The file '{file_path}' does not exist.")

        try:
            with open(file_path, 'rb') as fp:
                response = requests.post(
                    endpoint_uri, files={"file": (file_path.name, fp)}, headers=HEADERS
                )
                response.raise_for_status()
                response_data = response.json()

                if response_data:
                    print(response_data)
                else:
                    raise Exception ("wtf")
               # responses[ext] = response_data
                if ext == "gif":
                    ipfs_hash = response_data.get('IpfsHash')
                    if ipfs_hash:
                        ipfs_link = f"https://ipfs.io/ipfs/{ipfs_hash}"
                        dbFunctions.update_column('ipfsGIF', ipfs_link, firstUnsuccess['id'])
                    else:
                        print("IPFS hash not found in the response for the gif file.")
                        raise Exception
                # If the file is an mp4, update the database
                if ext == "mp3":
                    ipfs_hash = response_data.get('IpfsHash')
                    if ipfs_hash:
                        ipfs_link = f"https://ipfs.io/ipfs/{ipfs_hash}"
                        dbFunctions.update_column('ipfsMP3', ipfs_link, firstUnsuccess['id'])
                    else:
                        print("IPFS hash not found in the response for the mp3 file.")
                        raise Exception
                if ext == "mp4":
                    ipfs_hash = response_data.get('IpfsHash')
                    if ipfs_hash:
                        ipfs_link = f"https://ipfs.io/ipfs/{ipfs_hash}"
                        dbFunctions.update_column('ipfsMP4', ipfs_link, firstUnsuccess['id'])
                    else:
                        print("IPFS hash not found in the response for the mp4 file.")
                        raise Exception
                if ext == "glb":
                    ipfs_hash = response_data.get('IpfsHash')
                    if ipfs_hash:
                        ipfs_link = f"https://ipfs.io/ipfs/{ipfs_hash}"
                        dbFunctions.update_column('ipfsGLB', ipfs_link, firstUnsuccess['id'])
                    else:
                        print("IPFS hash not found in the response for the glb file.")
                        raise Exception
                if ext == "jpeg":
                    ipfs_hash = response_data.get('IpfsHash')
                    if ipfs_hash:
                        ipfs_link = f"https://ipfs.io/ipfs/{ipfs_hash}"
                        dbFunctions.update_column('ipfsJPG', ipfs_link, firstUnsuccess['id'])
                    else:
                        print("IPFS hash not found in the response for the jpeg file.")
                        raise Exception
                if ext == "json":
                    ipfs_hash = response_data.get('IpfsHash')
                    if ipfs_hash:
                        ipfs_link = f"https://ipfs.io/ipfs/{ipfs_hash}"
                        dbFunctions.update_column('ipfsJSON', ipfs_link, firstUnsuccess['id'])
                    else:
                        print("IPFS hash not found in the response for the json file.")
                        raise Exception
        except requests.exceptions.RequestException as e:
            print(f"HTTP request failed for {file_path}: {e}")
            raise Exception (f"HTTP request failed for {file_path}: {e}")
        except Exception as e:
            print(f"An error occurred with {file_path}: {e}")

            raise Exception (f"An error occurred with {file_path}: {e}")



def mint(tokenURI, to_address, contract_address, owner_private_key, owner_address, provider_url):
    # Connect to Ethereum node
    web3 = Web3(Web3.HTTPProvider(provider_url))

    # Check connection
    if not web3.is_connected():
        raise Exception("Error: Cannot connect to Ethereum node.")

    # Load contract ABI
    with open('./contracts/NFT.json', 'r') as abi_file:
        contract_abi_nft = json.load(abi_file)

    # Create contract instance
    contract_nft = web3.eth.contract(address=contract_address, abi=contract_abi_nft)

    # Build the transaction
    tx = contract_nft.functions.mintNFT(to_address, tokenURI).build_transaction({
        'from': owner_address,
        'nonce': web3.eth.get_transaction_count(owner_address),
        'gas': 300000,
        'gasPrice': web3.to_wei('20', 'gwei')
    })

    # Sign the transaction
    signed_tx = web3.eth.account.sign_transaction(tx, private_key=owner_private_key)

    # Send the transaction
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

    # Get transaction receipt
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

    print(f"Transaction successful with hash: {web3.to_hex(tx_hash)}")
    return tx_receipt

def load_state_nomintpush():
    if not os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'w') as f:
            f.write('0')
        return 0
    else:
        with open(STATE_FILE, 'r') as f:
            return int(f.read().strip())

def save_state_nomintpush(value):
    with open(STATE_FILE, 'w') as f:
        f.write(str(value))

def increment_push_count():
    if not os.path.exists(PUSH_COUNT_FILE):
        with open(PUSH_COUNT_FILE, 'w') as f:
            f.write('0')
    with open(PUSH_COUNT_FILE, 'r') as f:
        count = int(f.read().strip())
    with open(PUSH_COUNT_FILE, 'w') as f:
        f.write(str(count + 1))

def pushMotorOnNoMint():
    motorPush(distance)
    increment_push_count()

def check4NoMintPush(web3, contract_address, contract_abi):
    try:
        # Load state from file
        contract = web3.eth.contract(address=contract_address, abi=contract_abi)
        current_state = load_state_nomintpush()
        # Get blockchain value from the contract
        motor_push_count = contract.functions.getMotorPushesWithoutBuy().call()
        if motor_push_count == current_state:
            print("No change in motor push count, doing nothing.")
        elif motor_push_count > current_state:
            for i in range(current_state, motor_push_count):
                pushMotorOnNoMint()
            save_state_nomintpush(motor_push_count)
        elif motor_push_count < current_state:
            save_state_nomintpush("0")
    except Exception as e:
        error_message = f"An error occurred: {str(e)}. Retrying..."  # Explicitly convert exception to string
        print(error_message)
        send_alert_email(f"check4NoMintPush failed: {str(e)}")  # Make sure to properly format the message



#mint("ipfs://QmUPK1fuTqkcyxsKnwsKpEZrdibSaM1hoCo3a44CCFcin2","0x6F49498A063d4AB25106aD49c1f050088633268f", "0xBc0F5A496A99C2bF8De5cdB0B8DA82d162039336","ae21cc85edcb8851d7b6d2e4a10eb0a3efa1436c80cfd5e304750a849bee18db","0x6F49498A063d4AB25106aD49c1f050088633268f", "https://sepolia.infura.io/v3/0bef952f5c6841ab967e005dc69f6c21")
#create_ipfsjson("1_knight_windPark_shoppingcart", "knight", "shoppingcart", "windPark","https://ipfs.io/ipfs/QmY12QfNQokXMZ1GwEQAAMX53rE1WSRBXW7FKUD5dvMumK","https://ipfs.io/ipfs/QmNqC62ZkwGDNxMKmiNfYL43sYUhN8RYkSdP7TRe9kNkcf", "https://ipfs.io/ipfs/QmRwgzgbZEXEgZLJdEXo4TaAy9B7oVmtn7NtakJ8yLUYpz")