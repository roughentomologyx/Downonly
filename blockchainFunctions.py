import logging
import json
import dbFunctions
from web3 import Web3
import requests, os
from typing import Dict, Any
from pathlib import Path
import logging

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
    event_filter = contract.events.AuctionSale.create_filter(fromBlock=int(last_known_block))
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






def create_ipfsjson(name, character, obstacle, surface, picIPFS, vidIPFS):
    '''
    {"description": "Ugly f*cker", "external_url": "https://nikitadiakur.com/", "image": "ipfs://QmUYxWDCcXAbVe4UCTV52MdYRfmUoKhhdGMab2m68NabN5", "animation_url": "ipfs://QmVHsPUUoxmWvP4yogUf9GnnKXoPMjBVRsipyzLUYEvEPc", "name": "Frank 3", "attributes": [{"trait_type": "character", "value": "asd"}, {"trait_type": "obstacle", "value": "asd2"}, {"trait_type": "surface", "value": "asd3"}]}

    :return:
    '''


    dictionary = {

        "description": "Ugly f*cker",
        "external_url": "https://nikitadiakur.com/",
        "image": picIPFS,
        "animation_url": vidIPFS,
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

#





def pinContentToIPFS(
    firstUnsuccess: Dict[str, Any], pinata_api_key: str, pinata_secret: str
) -> Dict[str, Any]:

    HEADERS = {
        "pinata_api_key": pinata_api_key,
        "pinata_secret_api_key": pinata_secret,
    }

    endpoint_uri = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    base_path = "./zips/" + firstUnsuccess['fullname']
    extensions = ["json", "glb", "mp4"]
    responses = {}

    for ext in extensions:
        file_path = Path(f"{base_path}.{ext}")

        if file_path.exists():
            print(f"The file '{file_path}' exists.")
        else:
            print(f"The file '{file_path}' does not exist.")
            responses[ext] = {"error": f"The file '{file_path}' does not exist."}
            continue

        try:
            with open(file_path, 'rb') as fp:
                response = requests.post(
                    endpoint_uri, files={"file": (file_path.name, fp)}, headers=HEADERS
                )
                response.raise_for_status()
                response_data = response.json()
                responses[ext] = response_data

                # If the file is an mp4, update the database
                if ext == "mp4":
                    ipfs_hash = response_data.get('IpfsHash')
                    if ipfs_hash:
                        ipfs_link = f"ipfs://{ipfs_hash}"
                        dbFunctions.update_column('ipfsVideo', ipfs_link, firstUnsuccess['id'])
                    else:
                        print("IPFS hash not found in the response for the mp4 file.")

        except requests.exceptions.RequestException as e:
            print(f"HTTP request failed for {file_path}: {e}")
            responses[ext] = {"error": str(e)}
        except Exception as e:
            print(f"An error occurred with {file_path}: {e}")
            responses[ext] = {"error": str(e)}

    return responses

