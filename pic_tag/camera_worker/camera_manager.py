

import os
from ast import arg
import sqlite3
import threading
from .cropper import capture_frames
from .feature_extrator import extract_features
from .grouper import IdentityEngine
import queue as Queue
from .grouper.id_logger import IdentityLogger

from pathlib import Path

def start_all_cameras(folder: Path = None):
    # Connect to the SQLite database to retrieve camera configurations in real production
   
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    if not folder:
        folder = Path(base_dir) / "data"
    if not folder.exists():
        folder.mkdir(parents=True, exist_ok=True) 
    log_db_path = folder / "db" / "identity_log.db"
    log_db_path.parent.mkdir(parents=True, exist_ok=True)
    
    
    logger = IdentityLogger(log_db_path)
    frame_queue = Queue.Queue()
    feature_queue = Queue.Queue()

    project_dir = Path(__file__).resolve().parent 
    data_dir = project_dir.parent / 'data'
    
    
    feature_extractor_thread = threading.Thread(target=extract_features,args=(frame_queue, feature_queue,))
    feature_extractor_thread.start()
    engine = IdentityEngine(feature_queue, sim_threshold=0.2,logger=logger, max_history=20000, max_age_sec=86400)
    grouper_thread = threading.Thread(target=engine.run)  # Assuming camera_id 0 for the grouper
    grouper_thread.start()
    
    
    for i in range(1):
        camera_id = i
        camera_thread = threading.Thread(target=capture_frames, args=(camera_id, frame_queue, data_dir, None)  )
        camera_thread.start()