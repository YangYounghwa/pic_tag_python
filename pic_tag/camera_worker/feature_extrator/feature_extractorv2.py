import os
import time
import queue
import numpy as np
from PIL import Image
from datetime import datetime
from time import sleep
from openvino.runtime import Core
import torchvision.transforms as transforms

from utils import ResizePad  # Make sure ResizePad is defined or imported

def extract_features(frame_queue, feature_queue, stop_event=None):
    print("Feature extraction thread started.")
    sleep(4)
    print("Starting feature extraction thread...")

    # Load OpenVINO model
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_xml_path = os.path.join(base_dir, "reid_model.xml")  # change if filename differs
    print(f"Loading OpenVINO model from: {model_xml_path}")

    core = Core()
    model_ov = core.read_model(model=model_xml_path)
    compiled_model = core.compile_model(model_ov, "CPU")

    input_layer = compiled_model.input(0)
    output_layer = compiled_model.output(0)

    print(f"✅ Feature extraction model loaded with OpenVINO. Input shape: {input_layer.shape}")

    while not stop_event.is_set():
        try:
            frame_data = frame_queue.get(timeout=0.05)
            frame_queue.task_done()
        except queue.Empty:
            now = datetime.now().strftime("%H:%M:%S")
            print(f"FE : {now} : Frame queue is empty, sleeping for a while...")
            sleep(0.1)
            continue

        if frame_data is None:
            print("No more frames to process, sleeping for a while...")
            sleep(0.1)
            continue

        image = frame_data["cropped_image_rgb"]
        x1 = frame_data["bb_x1"]
        y1 = frame_data["bb_y1"]
        x2 = frame_data["bb_x2"]
        y2 = frame_data["bb_y2"]
        timestamp = frame_data["timestamp"]
        cam_id = frame_data["camera_id"]
        image_filepath = frame_data["file_path"]

        # Feature extraction using OpenVINO
        features = extract_embedding_from_np(image, compiled_model, input_layer, output_layer)
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

def extract_embedding_from_np(rgb_np_image, compiled_model, input_layer, output_layer):
    # Preprocess using same ResizePad + normalization
    image = Image.fromarray(rgb_np_image)
    transform = transforms.Compose([
        ResizePad((256, 128)),
        transforms.ToTensor(),
        transforms.Normalize([0.5]*3, [0.5]*3)
    ])
    input_tensor = transform(image).unsqueeze(0).numpy()  # numpy array for OpenVINO

    # Run inference
    with np.errstate(all='ignore'):  # suppress any runtime warnings (e.g., NaNs)
        result = compiled_model([input_tensor])[output_layer]

    return result.squeeze(0)