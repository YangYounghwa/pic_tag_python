


from time import sleep
import os
import glob
import xml.etree.ElementTree as ET
import time
import xml.etree.ElementTree as ET


import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision.ops import RoIAlign
from torchvision import transforms
from ultralytics import YOLO

from .ReID_modelv2 import YOLOv11ReID
import random
import numpy as np
import time
import time
import queue

def extract_features(frame_queue,feature_queue ):
    
    print("Starting feature extraction thread...")  
    
    # Load the YOLOv11 ReID model
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    device = torch.device("cpu")
    
    model3 = YOLOv11ReID()
    model3.load_state_dict(torch.load(os.path.join(base_dir, "reid_model_state_dict_0724_2.pth"), map_location=device))

    model3.eval()
    model3.to(device)
   
    # Debug line to confirm model loading
    print(f"Feature extraction model loaded and ready on {device}.")

    
    
    while True:
        # Get a frame from the queue
        try:
            frame_data = frame_queue.get(timeout=0.2)
        except queue.Empty as e:
            # print("Frame queue is empty, exiting feature extraction.")
            continue

        if frame_data is None:
            # print("No more frames to process, exiting feature extraction.")
            sleep(0.1)
            continue  # Skip if no frame data is available
        # Debug line to show which frame is being processed

        print(f"[{time.strftime('%H:%M:%S')}] Extracting features from frame: {frame_data['file']}")
        image = frame_data["cropped_image_rgb"]
        x1 = frame_data["bb_x1"]
        y1 = frame_data["bb_y1"]
        x2 = frame_data["bb_x2"]
        y2 = frame_data["bb_y2"]
        timestamp = frame_data["timestamp"]
        # track_id = frame_data["track_id"]  // not used in feature extraction
        cam_id = frame_data["camera_id"]
        image_filepath = frame_data["file_path"]
        
        features = model3(image)
        features = features.cpu().numpy()
        features = features.flatten()
        feature_data = {
            "timestamp": timestamp,
            "file_path": image_filepath,
            "camera_id": cam_id,
            "bb_x1": x1,
            "bb_y1": y1,
            "bb_x2": x2,
            "bb_y2": y2,
            "features": features,
        }


        feature_queue.put(feature_data)
        # Mark the task as done
        frame_queue.task_done()