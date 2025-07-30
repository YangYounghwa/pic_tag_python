import platform

if "intel" in platform.processor().lower():
    import cam_cropperv2 as cam_cropper
else:
    import cam_cropper as cam_cropper
    
from .video_cropper import capture_video_frames
from .cropper_utils import model_load, make_folder, draw_bounding_box
