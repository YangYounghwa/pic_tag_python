import torch
import torch.nn as nn
from ultralytics import YOLO
from torchvision import transforms

class VisionAttentionLayer(nn.Module):
    """
    A standard Multi-Head Self-Attention layer for vision tasks.
    This layer is a core component of Vision Transformers (ViT).

    Args:
        dim (int): The embedding dimension of the input tokens.
        heads (int): The number of attention heads.
        dim_head (int, optional): The dimension of each attention head.
                                  Defaults to dim // heads.
        dropout (float, optional): Dropout rate. Defaults to 0.0.
    """
    def __init__(self, dim: int, heads: int = 8, dim_head: int = 64, dropout: float = 0.0):
        super().__init__()
        inner_dim = dim_head * heads
        project_out = not (heads == 1 and dim_head == dim)

        self.heads = heads
        # The scale factor is a crucial detail for stabilizing training.
        # It's the inverse square root of the head dimension.
        self.scale = dim_head ** -0.5

        self.to_qkv = nn.Linear(dim, inner_dim * 3, bias=False)
        self.softmax = nn.Softmax(dim=-1)
        self.dropout = nn.Dropout(dropout)

        self.to_out = nn.Sequential(
            nn.Linear(inner_dim, dim),
            nn.Dropout(dropout)
        ) if project_out else nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x input shape: (batch_size, num_patches, dim)

        # 1. Project input to Q, K, V
        # Shape: (batch_size, num_patches, inner_dim * 3)
        qkv = self.to_qkv(x).chunk(3, dim=-1)

        # 2. Reshape Q, K, V for multi-head attention
        # Change shape to: (batch_size, heads, num_patches, dim_head)
        q, k, v = map(
            lambda t: t.reshape(t.shape[0], t.shape[1], self.heads, -1).permute(0, 2, 1, 3),
            qkv
        )

        # 3. Calculate scaled dot-product attention scores
        # (q @ k.transpose) -> (b, h, n, d) @ (b, h, d, n) -> (b, h, n, n)
        dots = torch.matmul(q, k.transpose(-1, -2)) * self.scale

        # 4. Apply softmax to get attention weights
        attn_weights = self.softmax(dots)
        attn_weights = self.dropout(attn_weights)

        # 5. Apply attention weights to V (values)
        # (attn_weights @ v) -> (b, h, n, n) @ (b, h, n, d) -> (b, h, n, d)
        attended_values = torch.matmul(attn_weights, v)

        # 6. Concatenate heads and project output
        # First, reshape to (b, n, h*d) where h*d = inner_dim
        out = attended_values.permute(0, 2, 1, 3).reshape(x.shape[0], x.shape[1], -1)

        # Finally, project back to the original embedding dimension `dim`
        return self.to_out(out)
    

class ReIDAtten_v2(nn.Module):
    '''
    ReID Atten v2
    Reduced backbone of YOLOv11 
    Uses Attention Layer for head.
    157,024 parameters. 
    '''
    def __init__(self, yolo_weights='yolo11n.pt', emb_dim=128):
        super().__init__()

        yolo_model = YOLO(yolo_weights)
        self.backbone = nn.Sequential(*yolo_model.model.model[:5])
        
        self.avg_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.max_pool = nn.AdaptiveMaxPool2d((1, 1))
        self.backbone_output_dim = self._get_feat_dim()
        # Caveat : dim = dim_head = heads
        self.attn = VisionAttentionLayer(
            dim=self.backbone_output_dim, 
            heads=4, 
            dim_head=self.backbone_output_dim // 4)
        self.embed = nn.Linear(self.backbone_output_dim, emb_dim)

    def _get_feat_dim(self):
        x = torch.zeros((1, 3, 256, 128))
        with torch.no_grad():
            x = self.backbone(x)
            return x.shape[1]  # fix here
    def forward(self, x):
        x = self.backbone(x)          # (B, C, H, W)


        flat = x.flatten(2).transpose(1, 2)  # (B, H*W, C)
        # print("input to atten:", flat.shape)
        att = self.attn(flat)              # (B, H*W, C)
        # print(att.shape)
        att = att.mean(dim=1) 
        # print(att.shape)            # (B, C)
        embed = self.embed(att)             # (B, 128)
        return nn.functional.normalize(embed, dim=1)
