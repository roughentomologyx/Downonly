import json
from email.message import EmailMessage
import smtplib
import helper
import requests
from dotenv import load_dotenv
import os
import threading
import blockchainFunctions, dbFunctions
from web3 import Web3
import logging, time
#import motorControl
load_dotenv()
# todo:
# notPayedAndNotPaused



initialBlockHeight = 6311981
logging.basicConfig(filename='app.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

CONTRACT_PATH = './contracts/dutchAuction.json'
INFURA_URL = os.getenv('INFURA_URL')
print(INFURA_URL)
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')
web3 = Web3(Web3.HTTPProvider(INFURA_URL))
if web3.is_connected():
    print("Connected to Ethereum node")
def motorPush(cm):
    print("pushed motor by "+ cm + " cm")
    try:
    # Read the current value from the file
        with open("./motorTimeRemaining.txt", 'r') as file:
            current_value = int(file.read().strip())
            print(current_value)
    # Add x seconds to the current value
        updated_value = current_value + int(cm)
    # Write the updated value back to the file
        with open("./motorTimeRemaining.txt", 'w') as file:
            file.write(str(updated_value))

        print(f"Updated value: {updated_value}")
    except FileNotFoundError:
        print(f"Error: The file motorstatefile' does not exist.")
    except ValueError:
        print("Error: The file does not contain a valid integer.")
    except Exception as e:
        print(f"An error occurred: {e}")




def mintNFT(firstUnsuccess):
    # rotate Motor
    print("mintedNFT")
    time.sleep(3)
    motorPush("10")
    dbFunctions.update_column('jobState', 'done', firstUnsuccess['id'])
def uploadFiles2IPFS(firstUnsuccess):
    # uploads the files to IPFS and returns the CID/IPFS Link on success
    if blockchainFunctions.pinContentToIPFS(firstUnsuccess,  os.getenv("PINATA_API_KEY"), os.getenv("PINATA_SECRET")):
        time.sleep(3)
        
        #dbFunctions.update_column('ipfsVideo', 'ipfs://QmVHsPUUoxmWvP4yogUf9GnnKXoPMjBVRsipyzLUYEvEPc', firstUnsuccess['id'])
        #dbFunctions.update_column('ipfsAudio', 'asdasdasd', firstUnsuccess['id'])
        blockchainFunctions.create_ipfsjson(firstUnsuccess["fullname"], "character", "obstacle", "surface", "picIPFS", "vidIPFS")
        dbFunctions.update_column('jobState', 'uploaded2IPFS', firstUnsuccess['id'])
        mintNFT(firstUnsuccess)
    else:
        print("failed to upload files to IPFS")

def getFilesFromRenderer(firstUnsuccess):
    # sends post request to a rendering machine, receiving back files

    if helper.sendRequest2Renderer(firstUnsuccess['surface'], firstUnsuccess['obstacle'], firstUnsuccess['figure'], firstUnsuccess['id'], firstUnsuccess['fullname']):
        print("getFilesFromRenderer")
        time.sleep(3)
        dbFunctions.update_column('jobState', 'rendered', firstUnsuccess['id'])
        fullname = str(firstUnsuccess["id"]) + '_' + firstUnsuccess["figure"] + '_' + firstUnsuccess["surface"]+'_' + firstUnsuccess["obstacle"]
        dbFunctions.update_column('fullname', fullname, firstUnsuccess['id'])
        print("upload 2 ipfs")
        uploadFiles2IPFS(firstUnsuccess)
    else:
        send_alert_email("renderer did not return all files")
        #break
        time.sleep(10)
        resumeJob(firstUnsuccess)
# Send an alert email for error handling
""" def mockgetFilesFromRenderer(firstUnsuccess):
    # sends post request to a rendering machine, receiving back files

    if helper.sendRequest2Renderer(firstUnsuccess['surface'], firstUnsuccess['obstacle'], firstUnsuccess['figure'], firstUnsuccess['id'], firstUnsuccess['fullname']):
        print("getFilesFromRenderer")
        time.sleep(3)
        dbFunctions.update_column('jobState', 'rendered', firstUnsuccess['id'])
        fullname = str(last_unsuc_bc["args"]["mintID"]) + '_' + last_unsuc_bc["args"]["character"] + '_' + last_unsuc_bc["args"]["surface"]+'_' + last_unsuc_bc["args"]["obstacle"]
        dbFunctions.update_column('fullname', fullname, firstUnsuccess['id'])
        uploadFiles2IPFS(firstUnsuccess)
    else:
        send_alert_email("renderer did not return all files")
        #break
        time.sleep(10) """

def send_alert_email(msg):
    '''
    msg = EmailMessage()
    msg.set_content('Error: Blockchain event ID is less than database ID.')
    msg['Subject'] = 'Job Processing Error'
    msg['From'] = 'your_email@example.com'
    msg['To'] = 'admin_email@example.com'

    # Send the email via your own SMTP server.
    with smtplib.SMTP('localhost') as s:
        s.send_message(msg)
    '''
    print("ALERTMAIL")
    print(msg)
def resumeJob(firstUnsuccess):
    print("resumedJob at " + str(firstUnsuccess["jobState"]))
    if firstUnsuccess["jobState"] == "paid":
        getFilesFromRenderer(firstUnsuccess)
    elif firstUnsuccess["jobState"] == "rendered":
        uploadFiles2IPFS(firstUnsuccess)
    elif firstUnsuccess["jobState"] == "uploaded2IPFS":
        mintNFT(firstUnsuccess)
    elif firstUnsuccess["jobState"] == "no_unsuc":
        print("no_unsuc")
    else:
        send_alert_email("DatabaseError: " + firstUnsuccess["jobState"] +" invalid Jobstate, fix database")
# Placeholder function for requesting rendering

def main():
    while True:
        print("line108")
        time.sleep(5)
        #sanity check and inventory
        lastSuccess=dbFunctions.getLastSuccess()
        print(lastSuccess)
        if lastSuccess:
            if lastSuccess['blockHeight']  == None:
                lastSuccess['blockHeight'] = initialBlockHeight
                #print(web3.eth.block_number)
        else:
            print("line119")
            time.sleep(3)

        firstUnsuccess=dbFunctions.getFirstUnsuccess()
        # Print all keys and their associated values in the dictionary
        print("Keys and values in firstUnsuccess dictionary:")
        for key, value in firstUnsuccess.items():
            print(f"{key}: {value}")
        print("jobstate")
        print(firstUnsuccess["jobState"])
        #print(firstUnsuccess["id"])
        # testing here, no_unsuc if e
        if firstUnsuccess["jobState"]=="no_unsuc": #no_unsuc
            try:
                
                contract_abi = blockchainFunctions.load_contract_abi_and_address(CONTRACT_PATH)
                contract_address = CONTRACT_ADDRESS
                print("Block:")
                print(lastSuccess['blockHeight'])
                last_unsuc_bc0 = blockchainFunctions.getLastUnsuccessfulBCObject(web3, contract_abi, contract_address, lastSuccess['blockHeight'])
                print(last_unsuc_bc0)

                if last_unsuc_bc0:
                  
                    last_unsuc_bc = json.loads(last_unsuc_bc0)
                    fullname = str(last_unsuc_bc["args"]["mintID"]) + '_' + last_unsuc_bc["args"]["character"] + '_' + last_unsuc_bc["args"]["surface"]+'_' + last_unsuc_bc["args"]["obstacle"]
                    print("found unsuccessful tx:")
                    print(last_unsuc_bc)
                    
                    dbFunctions.write2Mints(
                        "paid",
                        last_unsuc_bc["args"]["surface"], last_unsuc_bc["args"]["obstacle"], last_unsuc_bc["args"]["character"],
                        last_unsuc_bc["args"]["amount"], last_unsuc_bc["args"]["buyer"], last_unsuc_bc["transactionHash"], lastSuccess['blockHeight'],last_unsuc_bc["args"]["mintID"] ,fullname
                    )
                else:
                    print("no new/so far unsuccessful tx found, retry in 3 sec")
            except Exception as e:
                print("e?")
                print(e)

        else:
            resumeJob(firstUnsuccess)


if __name__ == "__main__":
    main()
