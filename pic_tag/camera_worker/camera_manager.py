


import sqlite3
import threading
from cropper import capture_frames
from feature_extrator import extract_features



def start_all_cameras():
    # Connect to the SQLite database to retrieve camera configurations in real production
   
    
    feature_extractor_thread = threading.Thread(target=extract_features)
    feature_extractor_thread.start() 
    
    for i in range(1):
        camera_id = i
        camera_thread = threading.Thread(target=capture_frames, args=(camera_id,))
        camera_thread.start()