


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

from .ReID_model import YOLOv11ReID

import random
import numpy as np


def extract_features(feature_queue, frame_queue):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model3 = torch.load(os.path.join(base_dir, "reid_model_full_v0.1.pth"), map_location=torch.device('cpu'),weights_only=False)
    model3.eval()
    device = torch.device("cpu")
    model3.to(device)

    
    
    while True:
        # Get a frame from the queue
        frame_data = frame_queue.get()
        if frame_data is None:
            sleep(0.1)
            continue  # Skip if no frame data is available
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