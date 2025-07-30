

import os
from ast import arg
import sqlite3
import threading
from .cropper import capture_frames
from .cropper import capture_video_frames
from .feature_extractor import extract_features
from .grouper import IdentityEngine
import queue as Queue
from .grouper import IdentityLogger
import configparser
from pathlib import Path


def get_rtsp_url_from_config(camera_name):
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), "pw", "camera_config.ini")
    config.read(config_path)
    


    if camera_name not in config:
        print(f"❌ Camera '{camera_name}' not found in config.")
        return None

    cam = config[camera_name]
    ip = cam.get("ip")
    username = cam.get("username")
    password = cam.get("password")
    path = cam.get("path2")  # "path1" or "path2"

    if not all([ip, username, password, path]):
        print(f"❌ Missing values for camera: {camera_name}")
        return None

    return f"rtsp://{username}:{password}@{ip}/{path}"



def start_all_cameras(folder: Path = None, live: bool = True, camera_path_list: list = None,max_fps=3):
    # Connect to the SQLite database to retrieve camera configurations in real production
   
    stop_event = threading.Event()
    threads = []    
    base_dir = Path(__file__).resolve().parent.parent.parent  
    if not folder:
        folder = base_dir / "data"
    folder.mkdir(parents=True, exist_ok=True)
    log_db_path = folder / "db" / "identity_log.db"
    
    if not live:
        log_db_path = folder / "db" / "video_identity_log.db"
    log_db_path.parent.mkdir(parents=True, exist_ok=True) 

    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), "pw", "camera_config.ini")
    config.read(config_path)
    camera_names = config.sections()
    
    logger = IdentityLogger(log_db_path)
    logger.start()  # <-- required for thread to runa
    
    frame_queue = Queue.Queue(maxsize=250)
    feature_queue = Queue.Queue(maxsize=250)

    
    data_dir = folder
    
    
    feature_extractor_thread = threading.Thread(target=extract_features,args=(frame_queue, feature_queue,stop_event))
    
    
    feature_extractor_thread.start()
    threads.append(feature_extractor_thread)
    

    engine = IdentityEngine(feature_queue, sim_threshold=0.775,logger=logger, max_history=2000, max_age_sec=86400)
    grouper_thread = threading.Thread(target=engine.run,args=(stop_event,)) # Assuming camera_id 0 for the grouper
    grouper_thread.start()
    threads.append(grouper_thread)
    
    # for i in range(1):
    #     camera_id = i
    #     camera_thread = threading.Thread(target=capture_frames, args=(camera_id, frame_queue, data_dir, None)  )
    #     camera_thread.start()
    
    if live:
        for index, camera_name in enumerate(camera_names):
            print(f"Starting camera: {camera_name}")
            rtsp_url = get_rtsp_url_from_config(camera_name)
            if not rtsp_url:
                continue

            camera_thread = threading.Thread(
                target=capture_frames,
                args=(rtsp_url, frame_queue, data_dir,  False, max_fps, stop_event,index)
            )
            camera_thread.start()
            threads.append(camera_thread)
    if not live:
        for index, video_file in enumerate(camera_path_list):
            print(f"Processing video file: {video_file}")
            camera_thread = threading.Thread(
                target=capture_video_frames,
                args=(video_file, frame_queue, data_dir, True, max_fps, stop_event,index)
            )
            camera_thread.start()
            threads.append(camera_thread)
        
        
        
        
    print("Press 'q' and Enter to stop...")
    while True:
        user_input = input()
        if user_input.strip().lower() == 'q':
            print("Stopping...")
            stop_event.set()
            break
        
        
        
    for t in threads:
        t.join()

    print("All threads stopped.")