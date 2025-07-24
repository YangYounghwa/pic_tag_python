import torch
import torch.nn as nn
from ultralytics import YOLO
import random
import numpy as np



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
        self.avg_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.max_pool = nn.AdaptiveMaxPool2d((1, 1))
        self.dropout = nn.Dropout(p=0.2)

        self.fc = nn.Sequential(
            nn.Linear(self._get_feat_dim(), emb_dim, bias=False),
            nn.BatchNorm1d(emb_dim)
        )
        for param in self.backbone[:4].parameters():
          param.requires_grad = False

        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(self._get_feat_dim(), emb_dim)

    def _get_feat_dim(self):
        x = torch.zeros((1, 3, 256, 128))
        with torch.no_grad():
            f = self.backbone(x)
            avg_feat = self.avg_pool(f)
            max_feat = self.max_pool(f)
            feat = (avg_feat+max_feat)/2
            return feat.flatten(1).shape[1]


    def forward(self, x):
        x = self.backbone(x)

        avg_feat = self.avg_pool(x)
        max_feat = self.max_pool(x)
        f = (avg_feat + max_feat) / 2
        f = f.flatten(1)
        f = self.dropout(f)
        emb = self.fc(f)
        return nn.functional.normalize(emb, dim=1)