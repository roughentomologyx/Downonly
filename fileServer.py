from flask import Flask, request, send_file
from time import sleep
import random, string, os
from zipfile import ZipFile
import zipfile
import io
from threading import Thread, Event
import requests
import ffmpeg
from pydub import AudioSegment

app = Flask(__name__)

current_task = None
task_event = Event()

def generate_files(post_data, stop_event):
    try:
        json_filename = f"{post_data['fullname']}.json"
        mp4_filename = f"{post_data['fullname']}.mp4"
        glb_filename = f"{post_data['fullname']}.glb"              
        
        if os.path.exists(json_filename):
            os.remove(json_filename)
        if os.path.exists(mp4_filename):
            os.remove(mp4_filename)
        if os.path.exists(glb_filename):
            os.remove(glb_filename)
            
        create_json(json_filename, post_data, stop_event)
        create_mp4(mp4_filename, post_data, stop_event)
        create_glb(glb_filename, post_data, stop_event)

    except Exception as e:
        print(e)

def generate_files_unity(post_data):
    
    try:
        
        headers = {'X-API-Key': 'your-api-key'}
        unity_server_render_fall_url = 'http://127.0.0.1:5001/renderFall'
        
        response = requests.post(unity_server_render_fall_url, json=post_data, headers=headers, timeout=30)
        response.raise_for_status()

    except Exception as e:
        print(e)

def read_json(filename, post_data, stop_event, randostring=None):
    if stop_event.is_set():
        return
    
    with open(filename, 'w') as f:
        f.write(randostring)

def create_json(filename, post_data, stop_event):
    if stop_event.is_set():
        return
    randostring = f"{post_data['figure']}_{post_data['surface']}_{post_data['obstacle']}.json"
    sleep(10)  # Simulate file creation time
    if stop_event.is_set():
        return
    with open(filename, 'w') as f:
        f.write(randostring)

def create_mp4(filename, post_data, stop_event):
    if stop_event.is_set():
        return
    randostring = f"{post_data['figure']}_{post_data['surface']}_{post_data['obstacle']}.mp4"
    sleep(10)  # Simulate file creation time
    if stop_event.is_set():
        return
    with open(filename, 'w') as f:
        f.write(randostring)
        
def create_glb(filename, post_data, stop_event):
    if stop_event.is_set():
        return
    randostring = f"{post_data['figure']}_{post_data['surface']}_{post_data['obstacle']}.glb"
    sleep(10)  # Simulate file creation time
    if stop_event.is_set():
        return
    with open(filename, 'w') as f:
        f.write(randostring)

@app.route('/', methods=['POST'])
def handle_post():
    global current_task, task_event
    try:           
    
        saveFilesPath = 'C:\\UnityProjects\\DownOnly\\SaveFiles\\'
            
        api_key = request.headers.get('X-API-Key')
        if api_key != 'your-api-key':
            return "Unauthorized", 401
        post_data = request.get_json()
        json_filename = f"{saveFilesPath + post_data['fullname']}.json"
        mp4_filename = f"{saveFilesPath + post_data['fullname']}_noaudio.mp4"        
        glb_filename = f"{saveFilesPath + post_data['fullname']}.glb"
        thumbnail_filename = f"{saveFilesPath + post_data['fullname']}.jpeg"
        gif_filename = f"{saveFilesPath + post_data['fullname']}.gif"
        merged_mp4_filename= f"{saveFilesPath + post_data['fullname']}.mp4"
        
        master_audio_filename = f"{saveFilesPath + post_data['fullname']}_MasterBus.wav"
        characters_audio_filename = f"{saveFilesPath + post_data['fullname']}_CharactersBus.wav"
        obstacles_audio_filename = f"{saveFilesPath + post_data['fullname']}_ObstaclesBus.wav"
        environments_audio_filename = f"{saveFilesPath + post_data['fullname']}_EnvironmentsBus.wav"
        reverbs_audio_filename = f"{saveFilesPath + post_data['fullname']}_ReverbsBus.wav"
        substances_audio_filename = f"{saveFilesPath + post_data['fullname']}_SubstancesBus.wav"

        mp3_filename = f"{saveFilesPath + post_data['fullname']}.mp3"

        generate_files_unity(post_data);
        # if current_task and current_task.is_alive():
            # task_event.set()
            # current_task.join()

        # task_event.clear()
        # current_task = Thread(target=generate_files_unity, args=(post_data, task_event))
        # current_task.start()
        # current_task.join()  # Wait for the thread to finish

        sleep(20)
        # sleep(2)

        # Generating Thumbnail for video
        ffmpeg.input(mp4_filename, ss=0.1).filter("scale", 1920, -1).output(thumbnail_filename, vframes=1).overwrite_output().run(capture_stdout=True, capture_stderr=True)
        
        # sleep(2)
        sleep(5) 
        
        #Generating gif from video
        ffmpeg.input(mp4_filename).filter("scale", 960, -1).filter("fps", 8).output(gif_filename).run()
       
        # sleep(2)
        sleep(5)      
        
        # Merging Master audio and video
        input_video = ffmpeg.input(mp4_filename)
        input_audio = ffmpeg.input(master_audio_filename)
        ffmpeg.concat(input_video, input_audio, v=1, a=1).output(merged_mp4_filename).run()
        
        # Convert master bus to mp3
        given_audio = AudioSegment.from_file(master_audio_filename, format="wav")
        given_audio.export(mp3_filename, format="mp3", bitrate="128k")   
        
        
        if not (os.path.isfile(json_filename) 
            and os.path.isfile(merged_mp4_filename)            
            and os.path.isfile(thumbnail_filename)
            and os.path.isfile(gif_filename)
            and os.path.isfile(glb_filename)
            and os.path.isfile(master_audio_filename)
            and os.path.isfile(characters_audio_filename)
            and os.path.isfile(obstacles_audio_filename)
            and os.path.isfile(environments_audio_filename)
            and os.path.isfile(reverbs_audio_filename)
            and os.path.isfile(substances_audio_filename)
            and os.path.isfile(mp3_filename)):
            raise FileNotFoundError("One or more input files do not exist")
                
        with ZipFile(f"{post_data['fullname']}.zip", 'w') as zip_file:
            zip_file.write(json_filename, os.path.basename(json_filename))
            zip_file.write(merged_mp4_filename, os.path.basename(merged_mp4_filename))            
            zip_file.write(thumbnail_filename, os.path.basename(thumbnail_filename))
            zip_file.write(gif_filename, os.path.basename(gif_filename))
            zip_file.write(glb_filename, os.path.basename(glb_filename))
            zip_file.write(master_audio_filename, os.path.basename(master_audio_filename))
            zip_file.write(characters_audio_filename, os.path.basename(characters_audio_filename))
            zip_file.write(obstacles_audio_filename, os.path.basename(obstacles_audio_filename))
            zip_file.write(environments_audio_filename, os.path.basename(environments_audio_filename))
            zip_file.write(reverbs_audio_filename, os.path.basename(reverbs_audio_filename))
            zip_file.write(substances_audio_filename, os.path.basename(substances_audio_filename))
            zip_file.write(mp3_filename, os.path.basename(mp3_filename))
        

        return send_file(f"{post_data['fullname']}.zip", mimetype='application/zip', as_attachment=True, download_name='files.zip')
    except Exception as e:
        print(e)
        return "Internal Server Error", 500        

if __name__ == "__main__":
    app.run(port=5000, host='0.0.0.0')