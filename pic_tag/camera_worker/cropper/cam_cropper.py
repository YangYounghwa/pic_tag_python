# File: pic_tag/camera_worker/cropper/cam_cropper.py

import cv2
import time
import os
from ultralytics import YOLO
import datetime
import queue
import threading
from pathlib import Path
from .cropper_utils import make_folder, model_load, draw_bounding_box, is_model_download

# --- Global image sequence counter ---
global_image_sequence_counter = 0

def capture_frames(
    cam_num, person_data_queue_instance, destination_folder: Path = None, video=True, max_fps=6, stop_event=None, cam_index=1
):
    global global_image_sequence_counter

    print(f"Starting capture_frames for camera {cam_num}, index {cam_index}")
    if destination_folder is None:
        destination_folder = Path("../data")
        print(f"Destination folder not provided. Using default: {destination_folder}")
    main_data_folder = destination_folder
    if not main_data_folder.exists():
        print(f"Destination folder {main_data_folder} does not exist. Creating it.")
        main_data_folder.mkdir(parents=True, exist_ok=True)
    sub_data_folder = "img"
    main_data_folder_path = main_data_folder
    sub_data_folder_path = main_data_folder / sub_data_folder
    make_folder(main_data_folder_path)
    make_folder(sub_data_folder_path)

    # Load model before camera initialization
    model_name = "yolov8n.pt"
    print(f"Loading model: {model_name}")
    model_path = is_model_download(model_name)
    if model_path is None:
        print(f"Failed to get model path for {model_name}. Exiting capture_frames.")
        return
    model = model_load(model_path)
    if model is None:
        print(f"{model_name} model loading failed. Exiting capture_frames.")
        return
    print("Model loaded successfully")

    # Initialize camera
    print(f"Attempting to open camera {cam_num}")
    cap = cv2.VideoCapture(cam_num)
    if not cap.isOpened():
        print(f"Failed to open camera {cam_num}. Checking backend support...")
        backends = [cv2.CAP_FFMPEG, cv2.CAP_GSTREAMER, cv2.CAP_ANY]
        for backend in backends:
            print(f"Trying backend {backend}")
            cap = cv2.VideoCapture(cam_num, backend)
            if cap.isOpened():
                print(f"Camera {cam_num} opened with backend {backend}")
                break
        if not cap.isOpened():
            print(f"Failed to open camera {cam_num} with any backend. Please check RTSP URL, credentials, network, or FFmpeg support.")
            return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        fps = 30
        print(f"Warning: Could not retrieve FPS from camera, defaulting to {fps} FPS.")
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Camera opened with resolution: {width}x{height} at {fps} FPS.")

    frame_count = 0
    person_class_id = None
    find_class = "person"
    
    for k, v in model.names.items():
        if v == find_class:
            person_class_id = k
            break
    if person_class_id is None:
        print(f"Error: '{find_class}' class not found in the loaded model. Person tracking might not work.")
        cap.release()
        return

    desired_frame_time = 1.0 / max_fps if max_fps > 0 else 0

    while not stop_event.is_set():
        frame_start_time = time.time()
        ret, frame = cap.read()
        frame_count += 1

        if not ret:
            print(f"Failed to read frame from camera {cam_num}. Stream may have ended or disconnected.")
            break

        current_time_dt = datetime.datetime.now()
        timestamp = current_time_dt  

        results = model.track(
            frame, persist=True, tracker="bytetrack.yaml", verbose=False, classes=person_class_id, conf=0.5
        )

        annotated_frame = frame.copy()

        # Uncomment to visualize frames for debugging
        # cv2.imshow(f"Camera {cam_num}", annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        is_this_a_saving_frame = True

        if results and results[0].boxes.id is not None:
            boxes_data = results[0].boxes.cpu().numpy()

            for i in range(len(boxes_data.xyxy)):
                class_id = int(boxes_data.cls[i])
                class_name = model.names[class_id]
                confidence = float(boxes_data.conf[i])
                bbox_xyxy = boxes_data.xyxy[i]
                track_id = int(boxes_data.id[i])

                if class_name == "person":
                    x1, y1, x2, y2 = map(int, bbox_xyxy)
                    annotated_frame = draw_bounding_box(
                        annotated_frame, (x1, y1, x2, y2), class_name, confidence, track_id=track_id
                    )

                    if is_this_a_saving_frame:
                        global_image_sequence_counter += 1
                        crop_x1 = max(0, x1)
                        crop_y1 = max(0, y1)
                        crop_x2 = min(width, x2)
                        crop_y2 = min(height, y2)
                        
                        image_filepath = None
                        cropped_image_rgb = None
                        
                        if crop_x2 > crop_x1 and crop_y2 > crop_y1:
                            object_crop = frame[crop_y1:crop_y2, crop_x1:crop_x2]
                            cropped_image_rgb = cv2.cvtColor(object_crop, cv2.COLOR_BGR2RGB)
                            tracked_images_folder = os.path.join(sub_data_folder_path, f"camera_{cam_index}")
                            make_folder(tracked_images_folder)
                            pic_name = f"hsw-{global_image_sequence_counter:06d}.jpg"
                            image_filepath = os.path.join(tracked_images_folder, pic_name)

                            try:
                                cv2.imwrite(image_filepath, object_crop, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
                            except Exception as e:
                                print(f"Error saving image {image_filepath}: {e}")
                                image_filepath = None

                        person_detection_data = {
                            "timestamp": timestamp,
                            "person_id": track_id,
                            "file_path": image_filepath,
                            "cropped_image_rgb": cropped_image_rgb,
                            "camera_id": cam_num,
                            "bb_x1": x1,
                            "bb_y1": y1,
                            "bb_x2": x2,
                            "bb_y2": y2
                        }
                        
                        try:
                            person_data_queue_instance.put(person_detection_data, block=False)
                        except queue.Full:
                            print(f"Person data queue full, skipping data for person ID {track_id} at {timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")

        frame_end_time = time.time()
        time_taken = frame_end_time - frame_start_time
        if desired_frame_time > time_taken:
            time.sleep(desired_frame_time - time_taken)

    cap.release()
    print(f"Capture for cam_num {cam_num} stopped. Total frames processed: {frame_count}")
    return {"status": "completed", "total_frames": frame_count, "camera_id": cam_num}
