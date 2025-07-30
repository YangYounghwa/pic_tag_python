import cv2
import time
import os
from ultralytics import YOLO
import datetime
import queue
import threading
from .cropper_utils import make_folder, model_load, draw_bounding_box

from pathlib import Path

# --- 모든 저장 이미지를 위한 전역 순차 번호 카운터 ---
global_image_sequence_counter = 0

# --- 큐 객체 생성 ---
# 1. 탐지된 사람 정보(DB 스키마)를 위한 큐
# person_data_queue = queue.Queue(maxsize=10) 
# 2. 화면 표시(imshow)를 위한 프레임 큐 (가장 최신 프레임만 유지)
# display_frame_queue = queue.Queue(maxsize=2) 




def capture_frames(cam_num, person_data_queue_instance, destination_folder: Path = None, video=True, max_fps=6, stop_event=None,cam_index=1):
    
    
    global_image_sequence_counter=0

    if destination_folder is None:
        destination_folder = Path("../data")
    main_data_folder = destination_folder
    if not main_data_folder.exists():
        print(f"Destination folder {main_data_folder} does not exist. Creating it.")
        main_data_folder.mkdir(parents=True, exist_ok=True)
    sub_data_folder = "img"
    main_data_folder_path = main_data_folder
    sub_data_folder_path = main_data_folder / sub_data_folder
    make_folder(main_data_folder_path)
    make_folder(sub_data_folder_path)

    base_dir = Path(__file__).resolve().parent
    
    cap = cv2.VideoCapture(cam_num)

    if not cap.isOpened():
        print(f"Failed to open webcam (camera index {cam_num}). Please check if the webcam is connected and available.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        fps = 30
        print(f"Warning: Could not retrieve FPS from webcam, defaulting to {fps} FPS.")
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Webcam opened with resolution: {width}x{height} at {fps} FPS.")

    model_name = "yolov8n.pt"
    model_name = base_dir / "yolov8n_openvino_model/"
    
    model = model_load(model_name)
    if model is None:
        print(f"{model_name} model loading failed. Exiting capture_frames.")
        cap.release()
        return
    print("model loaded")

    frame_count = 0
    person_class_id = None
    find_class = "person"
    
    for k, v in model.names.items():
        if v == find_class:
            person_class_id = k
            break
    if person_class_id is None:
        print(f"Error: '{find_class}' class not found in the loaded model. Person tracking might not work.")
        return

    # 목표 프레임당 시간 계산
    desired_frame_time = 1.0 / max_fps if max_fps > 0 else 0


    while not stop_event.is_set():
        frame_start_time = time.time() # 프레임 처리 시작 시간 기록

        ret, frame = cap.read()
        frame_count += 1

        if not ret:
            print(f"[{datetime.datetime.now()}] ❌ Failed to read from cam_num {cam_num}. Attempting reconnection...")
            cap.release()
            time.sleep(5)  # wait before retry
            cap = cv2.VideoCapture(cam_num)
            if not cap.isOpened():
                print(f"[{datetime.datetime.now()}] ❌ Reconnection failed. Will retry...")
                continue  # try again in next iteration
            print(f"[{datetime.datetime.now()}] 🔁 Reconnected to cam_num {cam_num}")
            continue  # try reading again after reconnect

        current_time_dt = datetime.datetime.now()
        timestamp=current_time_dt  
        #timestamp_str = current_time_dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        # --- 객체 탐지 및 트래킹 ---
        results = model.track(
            frame, persist=True, tracker="bytetrack.yaml", verbose=False, classes=person_class_id, conf=0.5
        )

        annotated_frame = frame.copy() # 원본 프레임 복사

        # cv2.imshow(f"Camera {cam_num}", annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # Sleep 구문이 있어서 불필요.
        # is_this_a_saving_frame = False
        # if int(fps) > 0 and frame_count % max_fps == 0: 
        
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
                    
                    # 미리보기용 바운딩 박스 그리기
                    annotated_frame = draw_bounding_box(
                        annotated_frame, (x1, y1, x2, y2), class_name, confidence, track_id=track_id
                    )

                    # --- 이미지 저장 및 사람 데이터 큐에 전송 ---
                    if is_this_a_saving_frame:
                        global_image_sequence_counter += 1

                        crop_x1 = max(0, x1)
                        crop_y1 = max(0, y1)
                        crop_x2 = min(width, x2)
                        crop_y2 = min(height, y2)
                        
                        image_filepath = None
                        cropped_image_rgb = None # <--- 추가: 크롭된 RGB 이미지 변수 초기화
                        
                        if crop_x2 > crop_x1 and crop_y2 > crop_y1:
                            object_crop = frame[crop_y1:crop_y2, crop_x1:crop_x2]
                            
                            # <--- 추가: BGR 이미지를 RGB로 변환 ---
                            cropped_image_rgb = cv2.cvtColor(object_crop, cv2.COLOR_BGR2RGB)
                            # -----------------------------------

                            tracked_images_folder = os.path.join(
                                sub_data_folder_path, f"camera_{cam_index}"
                            )
                            make_folder(tracked_images_folder)

                            pic_name = f"hsw-{global_image_sequence_counter:06d}.jpg"
                            image_filepath = os.path.join(tracked_images_folder, pic_name)

                            try:
                                cv2.imwrite(image_filepath, object_crop, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
                                # cv2.imwrite(image_filepath, object_crop) # 파일 저장은 BGR로 해도 무방
                                # print(f"Saved: {image_filepath}")
                            except Exception as e:
                                print(f"Error saving image {image_filepath}: {e}")
                                image_filepath = None

                        person_detection_data = {
                            "timestamp": timestamp,
                            "person_id": track_id,
                            "file_path": image_filepath,
                            "cropped_image_rgb": cropped_image_rgb, # <--- 추가: RGB 이미지 데이터
                            "camera_id": cam_num,
                            "bb_x1": x1,
                            "bb_y1": y1,
                            "bb_x2": x2,
                            "bb_y2": y2
                        }
                        

                        try:
                            # print("Adding person detection data to queue.  ")
                            person_data_queue_instance.put(person_detection_data, block=False)
                        except queue.Full:
                            print(f"Person data queue full, skipping data for person ID {track_id} at {timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")

        # --- FPS 제한 로직 ---
        frame_end_time = time.time() # 프레임 처리 종료 시간 기록
        time_taken = frame_end_time - frame_start_time # 프레임 처리 소요 시간
        
        if desired_frame_time > time_taken: # 목표 시간보다 빨리 처리되었다면
            time.sleep(desired_frame_time - time_taken) # 남은 시간만큼 대기
        # ---------------------


    # --- 루프 종료 후 자원 해제 ---
    cap.release()
    print(f"Capture for cam_num {cam_num} stopped. Total frames processed: {frame_count}")
    return {"status": "completed", "total_frames": frame_count, "camera_id": cam_num}



