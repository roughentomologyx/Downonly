import time, os, requests, zipfile

import dbFunctions
def sendRequest2Renderer(surface, obstacle, figure, mintID, fullname):
    renderer_url = 'http://192.168.1.3:5000/'
    post_data = {
        'fullname': fullname,
        'fallID': mintID,
        'character': figure,
        'environment': surface,
        'obstacle': obstacle
    }

    headers = {'X-API-Key': os.getenv('X-API-Key')}
    try:
        response = requests.post(renderer_url, json=post_data, headers=headers, timeout=120)
        response.raise_for_status()
        print(response.content)
        zip_dir = 'zips'
        os.makedirs(zip_dir, exist_ok=True)
        zip_path = os.path.join(zip_dir, f'{fullname}.zip')

        with open(zip_path, 'wb') as f:
            f.write(response.content)

        # Unpack and check the files
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(zip_dir)
            expected_files = [f"{fullname}.json", f"{fullname}.mp4", f"{fullname}.glb"]
            extracted_files = zip_ref.namelist()

            if all(file in extracted_files for file in expected_files):
                print(f"All expected files {expected_files} are present.")
                return True
            else:
                print(f"Missing expected files in the zip: {expected_files}")
                return False


    except requests.RequestException as e:
        print(f"Error: {e}")
