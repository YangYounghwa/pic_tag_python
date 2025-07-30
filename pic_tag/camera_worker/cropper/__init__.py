import platform

if "intel" in platform.processor().lower():
    from . import cam_cropperv2 as cropper
else:
    from . import cam_cropper as cropper
    
    
capture_frames = cropper.capture_frames
from .video_cropper import capture_video_frames
from .cropper_utils import model_load, make_folder, draw_bounding_box
