


from time import sleep
import os
import glob
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


def extract_features(feature_queue, frame_queue):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    device = torch.device("cpu")
    
    model3 = YOLOv11ReID()
    model3.load_state_dict(torch.load(os.path.join(base_dir, "reid_model_state_dictv2.0.pth"), map_location=device))

    model3.eval()
    model3.to(device)

    
    
    while True:
        # Get a frame from the queue
        frame_data = frame_queue.get()
        if frame_data is None:
            sleep(0.1)
            continue  # Skip if no frame data is available
        # Debug line to show which frame is being processed
        print(f"[{time.strftime('%H:%M:%S')}] Extracting features from frame: {frame_data['img_name']}")
        image = frame_data["img"]
        box = frame_data["bounding_box"]
        timestamp = frame_data["timeStamp"]
        cam_id = frame_data["camera_id"]
        img_name = frame_data["img_name"]
        features = model3(image)
        features = features.cpu().numpy()
        features = features.flatten()
        feature_data = {
            "features": features,
            "bounding_box": box,
            "timeStamp": timestamp,
            "camera_id": cam_id,
            "img_name": img_name
        }
        feature_queue.put(feature_data)
        # Mark the task as done
        frame_queue.task_done()