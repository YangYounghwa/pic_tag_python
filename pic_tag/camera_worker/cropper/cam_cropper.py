import cv2
import time
import os
from ultralytics import YOLO
import datetime
import queue
import threading

# --- 모든 저장 이미지를 위한 전역 순차 번호 카운터 ---
global_image_sequence_counter = 0

# --- 큐 객체 생성 ---
# 1. 탐지된 사람 정보(DB 스키마)를 위한 큐
person_data_queue = queue.Queue(maxsize=10) 
# 2. 화면 표시(imshow)를 위한 프레임 큐 (가장 최신 프레임만 유지)
display_frame_queue = queue.Queue(maxsize=2) 


def model_load(model_name):
    try:
        model = YOLO(model_name)
        print(f"'{model_name}' model loaded successfully.")
        return model
    except Exception as e:
        print(f"Error loading '{model_name}': {e}")
        return None


def make_folder(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"{folder_name} folder created.")


def draw_bounding_box(
    image, bbox, class_name, confidence, color=(0, 255, 0), thickness=2, track_id=None
):
    x1, y1, x2, y2 = map(int, bbox)
    cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
    label = f"{class_name}: {confidence:.2f}"
    if track_id is not None:
        label = f"ID{track_id}-{label}"
    cv2.putText(
        image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness
    )
    return image


def capture_frames(cam_num, person_data_queue_instance, display_frame_queue_instance, web_link=None):
    global global_image_sequence_counter

    main_data_folder = "data"
    sub_data_folder = "img"
    main_data_folder_path = main_data_folder
    sub_data_folder_path = os.path.join(main_data_folder, sub_data_folder)
    make_folder(main_data_folder_path)
    make_folder(sub_data_folder_path)

    cap = cv2.VideoCapture(cam_num)

    if not cap.isOpened():
        print(f"Failed to open webcam (camera index {cam_num}). Please check if the webcam is connected and available.")
        # 큐에 종료 신호를 보낼 수 있다면 더 좋음
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        fps = 30
        print(f"Warning: Could not retrieve FPS from webcam, defaulting to {fps} FPS.")
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Webcam opened with resolution: {width}x{height} at {fps} FPS.")

    model_name = "yolov8n.pt"
    model = model_load(model_name)
    if model is None:
        print(f"{model_name} model loading failed. Exiting capture_frames.")
        cap.release()
        # cv2.destroyAllWindows() # 스레드에서는 GUI 함수 호출하지 않음
        return

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

    while True:
        ret, frame = cap.read()
        frame_count += 1

        if not ret:
            print(f"Webcam stream for cam_num {cam_num} ended or error occured.")
            break

        current_time_dt = datetime.datetime.now()
        timestamp_str = current_time_dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        # --- 객체 탐지 및 트래킹 ---
        results = model.track(
            frame, persist=True, tracker="bytetrack.yaml", verbose=False, classes=person_class_id, conf=0.5
        )

        annotated_frame = frame.copy() # 원본 프레임 복사

        is_this_a_saving_frame = False
        if int(fps) > 0 and frame_count % int(fps) == 0: 
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
                        
                        if crop_x2 > crop_x1 and crop_y2 > crop_y1:
                            object_crop = frame[crop_y1:crop_y2, crop_x1:crop_x2]

                            tracked_images_folder = os.path.join(
                                sub_data_folder_path, f"person_track{track_id:04d}"
                            )
                            make_folder(tracked_images_folder)

                            pic_name = f"hsw-{global_image_sequence_counter:06d}.png"
                            image_filepath = os.path.join(tracked_images_folder, pic_name)

                            try:
                                cv2.imwrite(image_filepath, object_crop)
                                print(f"Saved: {image_filepath}")
                            except Exception as e:
                                print(f"Error saving image {image_filepath}: {e}")
                                image_filepath = None

                        person_detection_data = {
                            "timestamp": timestamp_str,
                            "person_id": track_id,
                            "embedding": None,
                            "file_path": image_filepath,
                            "camera_id": cam_num,
                            "bb_x1": x1,
                            "bb_y1": y1,
                            "bb_x2": x2,
                            "bb_y2": y2
                        }
                        
                        try:
                            person_data_queue_instance.put(person_detection_data, block=False)
                        except queue.Full:
                            print(f"Person data queue full, skipping data for person ID {track_id} at {timestamp_str}")
        
        # --- 어노테이션된 프레임을 디스플레이 큐에 넣기 ---
        # 큐가 가득 찼으면 가장 오래된 프레임을 버리고 최신 프레임을 넣음 (peek-pop 방식)
        try:
            # 큐에 공간이 없다면, 가장 오래된 아이템을 제거하고 새로운 아이템을 넣습니다.
            while display_frame_queue_instance.qsize() >= display_frame_queue_instance.maxsize:
                display_frame_queue_instance.get_nowait() # 논블로킹 방식으로 꺼냄
            display_frame_queue_instance.put_nowait(annotated_frame) # 논블로킹 방식으로 넣음
        except queue.Full:
            pass # maxsize=2라서 거의 발생하지 않음
        except queue.Empty:
            pass # get_nowait() 호출 시 큐가 비어있는 경우 (무시)


    # --- 루프 종료 후 자원 해제 ---
    cap.release()
    print(f"Capture for cam_num {cam_num} stopped. Total frames processed: {frame_count}")
    # 큐에 종료 신호를 보낼 수 있다면 더 좋음
    return {"status": "completed", "total_frames": frame_count, "camera_id": cam_num}


# --- 메인 실행 블록 ---
if __name__ == "__main__":
    # 큐 인스턴스 (전역 변수 사용)
    # my_frame_queue는 이제 person_data_queue로 이름이 변경됨
    # 새로운 display_frame_queue를 사용
    
    # capture_frames 함수를 별도의 스레드에서 실행
    capture_thread = threading.Thread(
        target=capture_frames, 
        args=(0, person_data_queue, display_frame_queue)
    )
    capture_thread.daemon = True 
    capture_thread.start()

    print("Capture thread started. Main thread can now perform other tasks (e.g., consume from queue and display frames).")

    # 메인 스레드에서 큐에서 데이터를 소비하고 화면을 표시하는 루프
    try:
        while True:
            # 1. 사람 데이터 큐에서 정보 소비 (비교/저장 로직)
            if not person_data_queue.empty():
                data_from_queue = person_data_queue.get()
                print(f"Main thread received person data:")
                for key, value in data_from_queue.items():
                    if key == "embedding" and value is None:
                        print(f"  {key}: None (embedding not generated in capture_frames)")
                    else:
                        print(f"  {key}: {value}")
            
            # 2. 디스플레이 프레임 큐에서 프레임 가져와 화면 표시
            if not display_frame_queue.empty():
                frame_to_display = display_frame_queue.get()
                if frame_to_display is not None and frame_to_display.size > 0:
                    cv2.imshow('Live Preview with YOLO Tracking (Press "q" to stop)', frame_to_display)
                else:
                    print("Warning: Received empty or invalid frame for display.")
            
            # 3. 키 입력 대기 및 종료 조건 확인 (메인 스레드에서만)
            # cv2.waitKey는 GUI 이벤트를 처리하고 키 입력을 받음
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("'q' 키 입력으로 작업을 중지합니다.")
                break
            
            # CPU 점유율 조절 (두 큐를 모두 확인하므로 너무 짧지 않게)
            time.sleep(0.01) 

            # capture_thread가 종료되면 메인 스레드도 종료되도록 함
            if not capture_thread.is_alive():
                print("Capture thread finished. Main thread is also stopping.")
                break

    except KeyboardInterrupt:
        print("Main thread received KeyboardInterrupt. Exiting.")
    finally:
        # 종료 전 모든 OpenCV 창 닫기 (메인 스레드에서 호출)
        cv2.destroyAllWindows() 
        
        # 큐에 남아있는 데이터 처리 (선택 사항)
        print("Processing any remaining data in the person data queue...")
        while not person_data_queue.empty():
            data_from_queue = person_data_queue.get()
            print(f"  Remaining person data: {data_from_queue['timestamp']}, Person ID: {data_from_queue['person_id']}")
        
        print("Processing any remaining frames in the display queue...")
        while not display_frame_queue.empty():
            _ = display_frame_queue.get() # 프레임은 버림
        
        print("Program terminated.")