
from pic_tag.camera_worker import frame_queue



import os
import glob
import xml.etree.ElementTree as ET


import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision.ops import RoIAlign
from torchvision import transforms

import random
import numpy as np


def extract_features():
    
    model3 = torch.load(r"pic_tag\camera_worker\feature_extrator\reid_model_full_v0.1.pth",map_location=torch.device('cpu'))
    model3.eval()
    device = torch.device("cpu")
    model3.to(device)

    
    
    while True:
        # Get a frame from the queue
        frame_data = frame_queue.get()
        image = frame_data["img"]
        box = frame_data["bounding_box"]
        timestamp = frame_data["timeStamp"]
        cam_id = frame_data["camera_id"]
        img_name = frame_data["img_name"]
        features = model3(image)
        
        
        
        
        
        
        
        
        
class YOLOv11ReID(nn.Module):
    def __init__(self, yolo_weights='yolo11n.pt', emb_dim=128):
        super().__init__()
        yolo_model = YOLO(yolo_weights)


        self.backbone = nn.Sequential(
          yolo_model.model.model[0],
          yolo_model.model.model[1],
          yolo_model.model.model[2],
          yolo_model.model.model[3],
          yolo_model.model.model[4],
          yolo_model.model.model[5],
          yolo_model.model.model[6],
          yolo_model.model.model[7],
          )

        
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(self._get_feat_dim(), emb_dim)

    def _get_feat_dim(self):
        x = torch.zeros((1, 3, 256, 128))
        with torch.no_grad():
            f = self.backbone(x)

            
            # f = self.pool(f).flatten(1)
            return f.shape[1]

    def forward(self, x):
        x = self.backbone(x)


        

        f = self.pool(x).flatten(1)
        pooled = self.pool(x).flatten(1)  # ✅ apply once
        emb = self.fc(pooled)
        return nn.functional.normalize(emb, dim=1)