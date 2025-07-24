


from ast import arg
import sqlite3
import threading
from cropper import capture_frames
from feature_extrator import extract_features
from grouper import IdentityEngine
import queue as Queue

frame_queue = Queue.Queue()
feature_queue = Queue.Queue()



def start_all_cameras():
    # Connect to the SQLite database to retrieve camera configurations in real production
   
   
    
    feature_extractor_thread = threading.Thread(target=extract_features,args=(frame_queue, feature_queue,))
    feature_extractor_thread.start()
    engine = IdentityEngine(similarity_threshold=0.2)
    grouper_thread = threading.Thread(target=engine.run, args=(0,))  # Assuming camera_id 0 for the grouper
    grouper_thread.start()
    
    
    for i in range(1):
        camera_id = i
        camera_thread = threading.Thread(target=capture_frames, args=(camera_id,frame_queue,))
        camera_thread.start()