
import json
from email.message import EmailMessage
import smtplib
#import helper
from dotenv import load_dotenv
import os

import blockchainFunctions, dbFunctions
from web3 import Web3
import logging, time

from blockchainFunctions import pinContentToIPFS

load_dotenv()
from helper import send_alert_email, motorPush, sftp_backup_file, sendRequest2Renderer, getFallHeight, transform_ipfs_link, push_motor_from_wei

initialBlockHeight = 6311981
logging.basicConfig(filename='app.log', level=logging.DEBUG,  # Changed to DEBUG to capture more details
                    format='%(asctime)s:%(levelname)s:%(message)s')

CONTRACT_PATH = './contracts/dutchAuction.json'
INFURA_URL = os.getenv('INFURA_URL')
logging.debug("INFURA_URL: %s", INFURA_URL)
CONTRACT_ADDRESS = os.getenv('AUCTIONCONTRACT_ADDRESS')
logging.debug("CONTRACT_ADDRESS: %s", CONTRACT_ADDRESS)
web3 = Web3(Web3.HTTPProvider(INFURA_URL))
pinata_api_key = os.getenv('PINATA_API_KEY')
pinata_secret = os.getenv('PINATA_SECRET')
dbhost = os.getenv('DBHOST')
backup_user = os.getenv('BACKUP_USER')
backup_pass = os.getenv('BACKUP_PW')

if web3.is_connected():
    logging.info("Connected to Ethereum node")
else:
    logging.error("Failed to connect to Ethereum node")

def mintNFT(firstUnsuccess):
    # rotate Motor
    try:
        if dbFunctions.nextinc() != firstUnsuccess['obstacle']:
            print("break here")
            #raise Exception ("cannot mint, as mintid does not match")
        logging.debug("mintNFT called with: %s", firstUnsuccess)
        contract_address = os.getenv("NFTCONTRACT_ADDRESS")
        owner_private_key = os.getenv("PRIVATE_KEY")
        owner_address = os.getenv("OWNER_ADDRESS")
        provider_url = os.getenv("INFURA_URL")
        blockchainFunctions.mint(transform_ipfs_link(firstUnsuccess['ipfsJSON']), firstUnsuccess['buyerAddress'], contract_address, owner_private_key, owner_address, provider_url, firstUnsuccess['id'])
        backupfile = "./zips/" + firstUnsuccess['fullname'] + ".zip"
        #sftp_backup_file(backupfile, dbhost, backup_user, backup_pass, ".files")
        dbFunctions.update_column('jobState', 'done', firstUnsuccess['id'])
        print("mintprice:")
        print(firstUnsuccess['mintprice'])
        #push_motor_from_wei(firstUnsuccess['mintprice'])
        #lastSuccess['blockHeight']
    except Exception as e:
        logging.error("An error occurred in mintNFT: %s", e, exc_info=True)
        raise Exception(e)

def uploadFiles2IPFS(firstUnsuccess):
    # uploads the files to IPFS and returns the CID/IPFS Link on success
    try:
        logging.debug("uploadFiles2IPFS called with: %s", firstUnsuccess)

        blockchainFunctions.pinContentToIPFS(firstUnsuccess, os.getenv("PINATA_API_KEY"), os.getenv("PINATA_SECRET"))
        blockchainFunctions.create_ipfsjson(firstUnsuccess["fullname"], firstUnsuccess["figure"], firstUnsuccess["obstacle"], firstUnsuccess["surface"], firstUnsuccess["ipfsGIF"], firstUnsuccess["ipfsMP4"], firstUnsuccess["ipfsGLB"])
        blockchainFunctions.uploadJsonToIPFS(firstUnsuccess, os.getenv("PINATA_API_KEY"), os.getenv("PINATA_SECRET"))
        dbFunctions.update_column('jobState', 'uploaded2IPFS', firstUnsuccess['id'])
        mintNFT(firstUnsuccess)
    except Exception as e:
        logging.error("Failed to upload files to IPFS: %s", e, exc_info=True)
        raise Exception("Failed to upload files to IPFS" + "\n" + str(e))

def getFilesFromRenderer(firstUnsuccess):
    # sends post request to a rendering machine, receiving back files
    logging.debug("getFilesFromRenderer called with: %s", firstUnsuccess)
    if sendRequest2Renderer(firstUnsuccess['surface'], firstUnsuccess['obstacle'], firstUnsuccess['figure'], firstUnsuccess['id'], firstUnsuccess['fullname']):
        logging.info("Files successfully retrieved from renderer")

        dbFunctions.update_column('jobState', 'rendered', firstUnsuccess['id'])

        fullname = str(firstUnsuccess["id"]) + '_' + firstUnsuccess["figure"] + '_' + firstUnsuccess["surface"] + '_' + firstUnsuccess["obstacle"]
        print("fallhight")
        fallHeight = getFallHeight(fullname)
        print("fallhight")
        print(fallHeight)
        dbFunctions.update_column('fullname', fullname, firstUnsuccess['id'])
        dbFunctions.update_column('fallDistance', fallHeight, firstUnsuccess['id'])
        uploadFiles2IPFS(firstUnsuccess)
    else:
        logging.error("Renderer did not return all files, alerting via email")
        send_alert_email("Renderer did not return all files")
        resumeJob(firstUnsuccess)

def resumeJob(firstUnsuccess):
    logging.info("Resuming job at state: %s", firstUnsuccess.get("jobState"))
    if firstUnsuccess.get("jobState") == "paid":
        getFilesFromRenderer(firstUnsuccess)
    elif firstUnsuccess.get("jobState") == "rendered":
        uploadFiles2IPFS(firstUnsuccess)
    elif firstUnsuccess.get("jobState") == "uploaded2IPFS":
        mintNFT(firstUnsuccess)
    elif firstUnsuccess.get("jobState") == "no_unsuc":
        logging.info("No unsuccessful jobs available")
    else:
        logging.error("DatabaseError: %s is an invalid Jobstate, fix database", firstUnsuccess.get("jobState"))
        send_alert_email("DatabaseError: " + firstUnsuccess.get("jobState", "Unknown") + " invalid Jobstate, fix database")

def main():
    while True:
        time.sleep(5)
        try:
            logging.info("Attempting to retrieve first unsuccessful job")
            firstUnsuccess = dbFunctions.getFirstUnsuccess()
            if firstUnsuccess is None:
                logging.debug("No unsuccessful job found, continuing loop")
                continue

            lastSuccess = dbFunctions.getLastSuccess()
            if lastSuccess is None:
                logging.debug("No last successful job found, using initial block height")
                lastSuccess = {'blockHeight': initialBlockHeight}
            elif lastSuccess.get('blockHeight') is None:
                lastSuccess['blockHeight'] = initialBlockHeight
            logging.info("Last successful block height: %s", lastSuccess)

            contract_abi = blockchainFunctions.load_contract_abi_and_address(CONTRACT_PATH)
            logging.debug("Loaded contract ABI: %s", contract_abi)
            last_unsuc_bc0 = blockchainFunctions.getLastUnsuccessfulBCObject(web3, contract_abi, CONTRACT_ADDRESS, lastSuccess['blockHeight'])
            logging.debug("Last unsuccessful blockchain object: %s", last_unsuc_bc0)


            if last_unsuc_bc0:
                last_unsuc_bc = json.loads(last_unsuc_bc0)
                print("1:last_unsuc_bc0")
                print(last_unsuc_bc0)
                print("2:last_unsuc_bc")
                print(last_unsuc_bc)
                fullname = str(last_unsuc_bc["args"]["mintID"]) + '_' + last_unsuc_bc["args"]["character"] + '_' + \
                           last_unsuc_bc["args"]["surface"] + '_' + last_unsuc_bc["args"]["obstacle"]
                logging.info("Found unsuccessful transaction:")
                logging.debug("Transaction details: %s", last_unsuc_bc)

                dbFunctions.write2Mints(
                    "paid",
                    last_unsuc_bc["args"]["surface"], last_unsuc_bc["args"]["obstacle"],
                    last_unsuc_bc["args"]["character"],
                    last_unsuc_bc["args"]["amount"], last_unsuc_bc["args"]["buyer"], last_unsuc_bc["transactionHash"],
                    lastSuccess['blockHeight'], last_unsuc_bc["args"]["mintID"], fullname
                )
            else:
                logging.info("No new unsuccessful transactions found, retrying in 3 seconds")

            # find first NFT that is paid but not done
            logging.info("Keys and values in firstUnsuccess dictionary:")
            for key, value in firstUnsuccess.items():
                logging.debug(f"{key}: {value}")

            if firstUnsuccess["jobState"] == "no_unsuc":  # no_unsuc
                try:
                    logging.info("No unsuccessful transactions found, checking last block:")
                    logging.debug("Block height: %s", lastSuccess['blockHeight'])



                except Exception as e:
                    logging.error("An error occurred while processing transactions: %s", e, exc_info=True)
                    raise Exception(e)

            else:
                resumeJob(firstUnsuccess)

        except Exception as e:
            logging.error("An error occurred in the main loop: %s", e, exc_info=True)
            continue

if __name__ == "__main__":
    main()


