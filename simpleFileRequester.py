import requests
import os
import zipfile
import io
import random
import shutil

random_ids = ["1", "10", "1000", "10000"];
random_characters = ["bath", "clown", "knight", "ski"];
random_environments = ["construction", "hospital", "redBricks", "school"];
random_obstacles = ["shoppingcart", "chair", "money", "fence"];
random_jsonfilenames = ["JsonTest1", "JsonTest2", "JsonTest3"]

clean_up_previous_attempts = True

zip_dir = './zips'

def cleanZipFiles():

    current_dir = os.getcwd()

    for root, dirs, files in os.walk(current_dir):
        for f in files:
            if '.zip' in f:
                os.unlink(os.path.join(root, f))

    for root, dirs, files in os.walk(zip_dir):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))

def getFilesFromRendererRandomized():

    if clean_up_previous_attempts:
        try:
            cleanZipFiles()
        except:
            "Failed to Clean Zip files from previous renders"
    # sent file
    json_data_path = random.choice(random_jsonfilenames)
    
    json_fall_data = ''
    
    with open(json_data_path + '.json') as f:
        json_fall_data = f.read()
    
    # getFilesFromRenderer(random.choice(random_ids), 
    getFilesFromRenderer(str(random.randint(0, 10000)), 
    random.choice(random_characters),
    random.choice(random_environments),
    random.choice(random_obstacles),
    json_fall_data)
    

def getFilesFromRenderer(mintID, figure, surface, obstacle, lastFallData):
    render_server_url = 'http://127.0.0.1:5000'
    
    fullname = mintID + "_" + figure + "_" + surface + "_" + obstacle
    
    post_data = {
        'fullname': fullname,
        'fallID': mintID,
        'character': figure,
        'environment': surface,
        'obstacle': obstacle,
        'lastFallDataJsonString': lastFallData
    }

    headers = {'X-API-Key': 'your-api-key'}
    try:
    
        print('Requesting to render Fall: ' + fullname)
    
        response = requests.post(render_server_url, json=post_data, headers=headers, timeout=120)
        response.raise_for_status()
        
        try:
            os.remove(zip_dir)
            print("% s removed successfully" % zip_dir)
        except OSError as error:
            print(error)
            print("File path can not be removed")
        
        os.makedirs(zip_dir, exist_ok=True)
        
        zip_path = os.path.join(zip_dir, f'{fullname}.zip')
        
        with open(zip_path, 'wb') as f:
            f.write(response.content)

        # Unpack and check the files
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        
            expected_files = [f"{fullname}.json", f"{fullname}.mp4", f"{fullname}.glb"]
            
            extracted_files = zip_ref.namelist()
            
            if all(file in extracted_files for file in expected_files):
                print(f"All expected files {expected_files} are present.")
            else:
                print(f"Missing expected files in the zip: {expected_files}")
        #copy json to it's own folder
        print(f"Files received and saved successfully to {zip_path}.")
    except requests.RequestException as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # getFilesFromRenderer('1', 'clown', 'castle', 'chair')
    getFilesFromRendererRandomized()
