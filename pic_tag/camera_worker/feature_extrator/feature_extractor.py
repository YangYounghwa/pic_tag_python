


from time import sleep
import os
import glob
import xml.etree.ElementTree as ET
import time
import xml.etree.ElementTree as ET

from PIL import Image

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision.ops import RoIAlign
from torchvision import transforms
from ultralytics import YOLO


from .ReID_attenv2 import ReIDAtten_v2
import random
import numpy as np
import time
import time
import queue

from .resizePad import ResizePad

def extract_features(frame_queue, feature_queue, stop_event=None):
    print("Feature extraction thread started.")
    sleep(4) 
    print("Starting feature extraction thread...")  
    
    # Load the YOLOv11 ReID model
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    device = torch.device("cpu")
    
    model3 = ReIDAtten_v2()
    model3.load_state_dict(torch.load(os.path.join(base_dir, "ReIDAttenv2_14999.pth"), map_location=device))

    model3.eval()
    model3.to(device)
   
    # Debug line to confirm model loading
    print(f"Feature extraction model loaded and ready on {device}.")



    while not stop_event.is_set():
        # Get a frame from the queue
        frame_data = None
        try:
            frame_data = frame_queue.get(timeout=0.05)
            # Mark the task as done
            frame_queue.task_done()
        except queue.Empty as e:
            print("Frame queue is empty, sleeping for a while...")
            sleep(0.1)
            continue

        if frame_data is None:
            print("No more frames to process, sleeping for a while...")
            sleep(0.1)
            continue  # Skip if no frame data is available
        # Debug line to show which frame is being processed

        # print(f"[{time.strftime('%H:%M:%S')}] Extracting features from frame: {frame_data['file_path']}")
        image = frame_data["cropped_image_rgb"]
        x1 = frame_data["bb_x1"]
        y1 = frame_data["bb_y1"]
        x2 = frame_data["bb_x2"]
        y2 = frame_data["bb_y2"]
        timestamp = frame_data["timestamp"]
        # track_id = frame_data["track_id"]  // not used in feature extraction
        cam_id = frame_data["camera_id"]
        image_filepath = frame_data["file_path"]

        features = extract_embedding_from_np(image, model3, device)
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


def extract_embedding_from_np(rgb_np_image, model, device):
    image = Image.fromarray(rgb_np_image)
    transform = transforms.Compose([
        ResizePad((256, 128)),
        transforms.ToTensor(),
        transforms.Normalize([0.5]*3, [0.5]*3)
    ])
    input_tensor = transform(image).unsqueeze(0).to(device)
    model.eval()
    with torch.no_grad():
        emb = model(input_tensor)
    return emb.squeeze(0).cpu()