import time, os, requests, zipfile

#import dbFunctions



import os
import requests
import zipfile
import os
import json
from web3 import Web3
from dotenv import load_dotenv
import paramiko, web3



import time

load_dotenv()
CONTRACT_PATH = './contracts/dutchAuction.json'
INFURA_URL = os.getenv('INFURA_URL')
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')
STATE_FILE = 'motorNoMintPushCount.txt'
PUSH_COUNT_FILE = 'pushMotorOnNoMintAll.txt'
distance = os.getenv('NOMINT_DISTANCE')
dbhost=os.getenv('DBHOST')
backup_user=os.getenv('BACKUP_USER')
backup_pass=os.getenv('BACKUP_PW')
renderer_url= os.getenv('RENDERER_URL')

def sendRequest2Renderer(surface, obstacle, figure, mintID, fullname):
    #renderer_url = 'http://127.0.0.1:5000/'

    # Locate the appropriate JSON file from /falldata2 based on mintID - 1
    falldata_dir = 'falldata2'
    previous_mint_id = int(mintID) - 1
    json_filename = None

    # Search for a file starting with the correct mintID - 1
    for filename in os.listdir(falldata_dir):
        if filename.startswith(f"{previous_mint_id}_") and filename.endswith('.json'):
            json_filename = filename
            break

    if not json_filename:
        print(f"No matching JSON file for mintID: {previous_mint_id} in {falldata_dir}")
        return  # Exit the function if the file is not found

    json_filepath = os.path.join(falldata_dir, json_filename)

    try:
        with open(json_filepath, 'r') as f:
            lastFallData = f.read()
    except Exception as e:
        print("JSON unreadable")
        return  # Ensure the function exits if the file is unreadable

    post_data = {
        'fullname': fullname,
        'fallID': mintID,
        'character': figure,
        'environment': surface,
        'obstacle': obstacle,
        'lastFallDataJsonString': lastFallData
    }

    headers = {'X-API-Key': os.getenv('X-API-Key')}
    try:
        response = requests.post(renderer_url, json=post_data, headers=headers, timeout=120)
        response.raise_for_status()
        print(response.content)

        zip_dir = 'zips'
        falldata_dir = 'falldata2'
        os.makedirs(zip_dir, exist_ok=True)
        os.makedirs(falldata_dir, exist_ok=True)

        zip_path = os.path.join(zip_dir, f'{fullname}.zip')

        # Save the received zip file in the zips directory
        with open(zip_path, 'wb') as f:
            f.write(response.content)

        # Extract all files to the falldata2 directory
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(falldata_dir)

        # Verification step for expected files
        expected_files = [f"{fullname}.json", f"{fullname}.mp4", f"{fullname}.glb", f"{fullname}.mp3",f"{fullname}.gif",f"{fullname}.jpeg"]
        extracted_files = os.listdir(falldata_dir)

        if all(file in extracted_files for file in expected_files):
            print(f"All expected files {expected_files} are present.")
            return True
        else:

           raise Exception (f"Missing expected files in the falldata2 directory: {expected_files}")

    except requests.RequestException as e:
        print(f"Error: {e}")
        raise Exception (e)

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


import os


def sftp_backup_file(source_file, backup_host, backup_username, backup_password, backup_folder):
    # Initialize the SSH client
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    sftp = None  # Initialize sftp as None

    try:
        # Connect to the backup server
        ssh_client.connect(backup_host, username=backup_username, password=backup_password)
        sftp = ssh_client.open_sftp()

        # Ensure the backup folder exists on the remote server
        try:
            sftp.stat(backup_folder)
        except FileNotFoundError:
            sftp.mkdir(backup_folder)

        # Define the remote file path
        remote_file = f"{backup_folder}/{source_file.split('/')[-1]}"
        print(remote_file)
        # Upload the file
        sftp.put(source_file, remote_file)
        print(f"File backed up: {source_file} -> {remote_file}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if sftp:  # Only attempt to close sftp if it was successfully assigned
            sftp.close()
        ssh_client.close()


def getFallHeight(name):
    file_path = f"falldata2/{name}.json"
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return None

    with open(file_path, 'r') as file:
        data = json.load(file)
    print("here")
    y_coordinate = str(data.get("startXYZ", {}).get("y"))
    return y_coordinate



#print(getFallHeight("../testdata/JsonTest3"))