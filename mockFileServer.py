from flask import Flask, request, send_file
import os
import random
from zipfile import ZipFile
import io

app = Flask(__name__)

@app.route('/', methods=['POST'])
def handle_post():
    try:
        # Define the directory to pick files from
        test_data_dir = './testdata'

        # Get all the available test files in the directory by type
        json_files = [f for f in os.listdir(test_data_dir) if f.endswith('.json')]
        mp4_files = [f for f in os.listdir(test_data_dir) if f.endswith('.mp4')]
        glb_files = [f for f in os.listdir(test_data_dir) if f.endswith('.glb')]
        jpeg_files = [f for f in os.listdir(test_data_dir) if f.endswith('.jpeg')]
        mp3_files = [f for f in os.listdir(test_data_dir) if f.endswith('.mp3')]
        gif_files = [f for f in os.listdir(test_data_dir) if f.endswith('.gif')]
        # Randomly pick one file from each type if available
        selected_json = random.choice(json_files) if json_files else None
        selected_mp4 = random.choice(mp4_files) if mp4_files else None
        selected_glb = random.choice(glb_files) if glb_files else None
        selected_jpeg = random.choice(jpeg_files) if jpeg_files else None
        selected_mp3 = random.choice(mp3_files) if mp3_files else None
        selected_gif = random.choice(gif_files) if gif_files else None

        # Check if all required file types are available
        if not (selected_json and selected_mp4 and selected_glb and selected_jpeg and selected_mp3):
            return "Not enough files in /testdata to create a zip", 500

        # Get the 'fullname' from the request data
        post_data = request.get_json()
        fullname = post_data.get('fullname', 'default_name')

        # Create a zip file in memory
        zip_buffer = io.BytesIO()
        with ZipFile(zip_buffer, 'w') as zip_file:
            # Rename files to match fullname and add them to the zip
            zip_file.write(os.path.join(test_data_dir, selected_json), arcname=f"{fullname}.json")
            zip_file.write(os.path.join(test_data_dir, selected_mp4), arcname=f"{fullname}.mp4")
            zip_file.write(os.path.join(test_data_dir, selected_glb), arcname=f"{fullname}.glb")
            zip_file.write(os.path.join(test_data_dir, selected_jpeg), arcname=f"{fullname}.jpeg")
            zip_file.write(os.path.join(test_data_dir, selected_mp3), arcname=f"{fullname}.mp3")
            zip_file.write(os.path.join(test_data_dir, selected_gif), arcname=f"{fullname}.gif")
        zip_buffer.seek(0)

        # Return the zip file as a response
        return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='mock_files.zip')

    except Exception as e:
        print(e)
        return "Internal Server Error", 500

if __name__ == "__main__":
    app.run(port=5000, host='0.0.0.0')
