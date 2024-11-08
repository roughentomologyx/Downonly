import os
import requests
import zipfile, json
from itertools import product
from dotenv import load_dotenv
load_dotenv()
def sendRequest2Renderer(surface, obstacle, figure, mintID, fullname):
    renderer_url = 'http://100.120.130.1:5000/'

    # Locate the appropriate JSON file from /falldata2 based on mintID - 1
    falldata_dir = 'falldata'
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
        'fallID': str(mintID),
        'character': figure,
        'environment': surface,
        'obstacle': obstacle,
        'lastFallDataJsonString': lastFallData
    }
    print(post_data)
    headers = {'X-API-Key': os.getenv('X-API-Key')}
    try:
        response = requests.post(renderer_url, json=post_data, headers=headers, timeout=120)
        response.raise_for_status()
        #print(response.content)

        zip_dir = 'zips'
        falldata_dir = 'falldata'
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
        expected_files = [f"{fullname}.json", f"{fullname}.mp4", f"{fullname}.glb", f"{fullname}.mp3",
                          f"{fullname}.gif", f"{fullname}.jpeg"]
        extracted_files = os.listdir(falldata_dir)

        if all(file in extracted_files for file in expected_files):
            print(f"All expected files {expected_files} are present.")
            return True
        else:
            raise Exception(f"Missing expected files in the falldata2 directory: {expected_files}")

    except requests.RequestException as e:
        print(f"Error: {e}")
        raise Exception(e)


def main():
    characters = ["business", "astronaut", "knight", "clown", "chef", "police", "ski", "construction", "farm", "bath",
                  "judge"]
    obstacles = ["shoppingcart", "balloons", "satellite", "toilet", "books", "horse", "snowCannon", "piano", "stove",
                 "money", "transporter"]
    surfaces = ["antenna", "livingRoom", "windPark", "court", "castle", "ferris", "scaffolding", "cruise", "snowPark",
                "victoryColumn", "escalator"]

    mintID = 1  # Starting mintID, modify as needed
    completed_requests_file = 'completed_requests.json'
    try:
        # Load completed requests from file if it exists
        if os.path.exists(completed_requests_file):
            with open(completed_requests_file, 'r') as f:
                completed_requests = json.load(f)
        else:
            completed_requests = []

        # Iterate over all combinations of characters, obstacles, and surfaces
        #for figure, obstacle, surface in product(characters, obstacles, surfaces):
        #    fullname = f"{mintID}_{figure}_{surface}_{obstacle}"

        # Iterate randomly
        import random

        # Number of random combinations you want to generate
        num_combinations = 20

        for _ in range(num_combinations):
            figure = random.choice(characters)
            obstacle = random.choice(obstacles)
            surface = random.choice(surfaces)
            fullname = f"{mintID}_{figure}_{surface}_{obstacle}"
            print(fullname)
            # Skip if this combination has already been processed
            if fullname in completed_requests:
                mintID += 1
                continue

            # Send request and update completed requests
            success = sendRequest2Renderer(surface, obstacle, figure, mintID, fullname)
            if success:
                completed_requests.append(fullname)
                mintID += 1

                # Save progress to file
                with open(completed_requests_file, 'w') as f:
                    json.dump(completed_requests, f)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()
