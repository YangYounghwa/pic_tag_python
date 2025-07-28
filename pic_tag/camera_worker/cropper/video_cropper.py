from .cropper_utils import make_folder, model_load, draw_bounding_box
import os
import cv2

from pathlib import Path
import datetime
import queue



def capture_video_frames(video_path, person_data_queue_instance, destination_folder: Path = None, max_fps=10, stop_event=None,t_id = 0):
    """_summary_

    Args:
        video_path (_type_): _description_
        person_data_queue_instance (_type_): _description_
        destination_folder (Path, optional): _description_. Defaults to None.
        max_fps (int, optional): _description_. Defaults to 12.
        stop_event (_type_, optional): _description_. Defaults to None.

    Returns:
        _type_: _description_
    """
    global_image_sequence_counter = 0

    if destination_folder is None:
        destination_folder = Path("../data")
    main_data_folder = destination_folder
    if not main_data_folder.exists():
        print(f"Destination folder {main_data_folder} does not exist. Creating it.")
        main_data_folder.mkdir(parents=True, exist_ok=True)
    sub_data_folder = "img"
    sub_data_folder_path = main_data_folder / sub_data_folder
    make_folder(main_data_folder)
    make_folder(sub_data_folder_path)
    
    file_path = video_path
    filename = os.path.basename(file_path)  # Gets "image.jpg"
    filename_without_extension = os.path.splitext(filename)[0]  # Splits and takes the first element
    print(filename_without_extension)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Failed to open video file: {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Video loaded: {video_path} | {width}x{height} at {fps:.2f} FPS")

    model = model_load("yolov8n.pt")
    if model is None:
        cap.release()
        return
    
    
    skip_rate = 6  # process every 6th frame
    
    skip_rate = int(fps)//max_fps 
    
    frame_count = 0
    person_class_id = next((k for k, v in model.names.items() if v == "person"), None)
    if person_class_id is None:
        print("❌ 'person' class not found in model.")
        cap.release()
        return


    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        if frame_count % skip_rate != 0:
            continue  # Skip non-target frames

        # Use relative timestamp from video
        timestamp_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
        timestamp = datetime.timedelta(milliseconds=timestamp_ms)

        results = model.track(
            frame, persist=True, tracker="bytetrack.yaml", verbose=False,
            classes=person_class_id, conf=0.5
        )

        annotated_frame = frame.copy()
        cv2.imshow(f"Video {video_path}", annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        if results and results[0].boxes.id is not None:
            boxes_data = results[0].boxes.cpu().numpy()
            for i in range(len(boxes_data.xyxy)):
                class_id = int(boxes_data.cls[i])
                if model.names[class_id] != "person":
                    continue

                confidence = float(boxes_data.conf[i])
                bbox_xyxy = boxes_data.xyxy[i]
                track_id = int(boxes_data.id[i])
                x1, y1, x2, y2 = map(int, bbox_xyxy)

                annotated_frame = draw_bounding_box(annotated_frame, (x1, y1, x2, y2), "person", confidence, track_id=track_id)

                global_image_sequence_counter += 1
                crop_x1, crop_y1 = max(0, x1), max(0, y1)
                crop_x2, crop_y2 = min(width, x2), min(height, y2)

                cropped_image_rgb = None
                image_filepath = None

                if crop_x2 > crop_x1 and crop_y2 > crop_y1:
                    object_crop = frame[crop_y1:crop_y2, crop_x1:crop_x2]
                    cropped_image_rgb = cv2.cvtColor(object_crop, cv2.COLOR_BGR2RGB)
                    

                    tracked_folder = sub_data_folder_path / f"video{t_id}_{filename_without_extension}"
                    make_folder(tracked_folder)

                    pic_name = f"hsw-{global_image_sequence_counter:06d}.png"
                    image_filepath = str(tracked_folder / pic_name)

                    try:
                        cv2.imwrite(image_filepath, object_crop)
                    except Exception as e:
                        print(f"❌ Failed to save image: {e}")
                        image_filepath = None

                person_data = {
                    "timestamp": timestamp,
                    "person_id": track_id,
                    "file_path": image_filepath,
                    "cropped_image_rgb": cropped_image_rgb,
                    "camera_id": video_path,
                    "bb_x1": x1,
                    "bb_y1": y1,
                    "bb_x2": x2,
                    "bb_y2": y2
                }

                try:
                    person_data_queue_instance.put(person_data, block=False)
                except queue.Full:
                    print(f"⚠️ Queue full. Dropping person ID {track_id} at {timestamp}")

    cap.release()
    print(f"🎞️ Finished video: {video_path} | Frames processed: {frame_count}")
    return {"status": "completed", "total_frames": frame_count, "video_path": video_path}