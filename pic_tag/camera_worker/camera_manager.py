

import os
from ast import arg
import sqlite3
import threading
from .cropper import capture_frames
from .feature_extrator import extract_features
from .grouper import IdentityEngine
import queue as Queue
from .grouper.id_logger import IdentityLogger
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
    path = cam.get("path2")  # or "path1"

    if not all([ip, username, password, path]):
        print(f"❌ Missing values for camera: {camera_name}")
        return None

    return f"rtsp://{username}:{password}@{ip}/{path}"



def start_all_cameras(folder: Path = None):
    # Connect to the SQLite database to retrieve camera configurations in real production
   
    
    base_dir = Path(__file__).resolve().parent.parent.parent  # ⬅️ if __file__ is inside /project/app/core/
    if not folder:
        folder = base_dir / "data"
    folder.mkdir(parents=True, exist_ok=True)
    log_db_path = folder / "db" / "identity_log.db"
    log_db_path.parent.mkdir(parents=True, exist_ok=True) 


    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), "pw", "camera_config.ini")
    config.read(config_path)
    camera_names = config.sections()
    
    
    logger = IdentityLogger(log_db_path)
    frame_queue = Queue.Queue(maxsize=250)
    feature_queue = Queue.Queue(maxsize=250)

    project_dir = Path(__file__).resolve().parent 
    data_dir = project_dir.parent / 'data'
    
    
    feature_extractor_thread = threading.Thread(target=extract_features,args=(frame_queue, feature_queue,))
    feature_extractor_thread.start()
    engine = IdentityEngine(feature_queue, sim_threshold=0.2,logger=logger, max_history=20000, max_age_sec=86400)
    grouper_thread = threading.Thread(target=engine.run)  # Assuming camera_id 0 for the grouper
    grouper_thread.start()
    
    
    # for i in range(1):
    #     camera_id = i
    #     camera_thread = threading.Thread(target=capture_frames, args=(camera_id, frame_queue, data_dir, None)  )
    #     camera_thread.start()

    for camera_name in camera_names:
        rtsp_url = get_rtsp_url_from_config(camera_name)
        if not rtsp_url:
            continue

        camera_thread = threading.Thread(
            target=capture_frames,
            args=(rtsp_url, frame_queue, data_dir, None)
        )
        camera_thread.start()