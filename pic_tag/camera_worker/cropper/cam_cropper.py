import cv2
import time
import os
from ultralytics import YOLO
import datetime
import queue # 테스트용 임포트
import threading # 스레딩 추가

# --- 모든 저장 이미지를 위한 전역 순차 번호 카운터 ---
global_image_sequence_counter = 0


# --- 큐 객체 생성 (이 큐를 통해 데이터를 전달할 것입니다) ---
# 이 큐는 메인 스레드와 capture_frames 스레드 간의 통신에 사용됩니다.
frame_data_queue = queue.Queue(maxsize=10) # 큐 사이즈를 제한하여 메모리 과부하 방지


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


def capture_frames(cam_num, frame_data_queue_instance, web_link=None): # rtsp_url 인자를 제거
    # 위에서 선언했던 전역 변수 사용 명시
    global global_image_sequence_counter

    # 이미지를 저장할 폴더 경로 지정/생성
    main_data_folder = "data"
    sub_data_folder = "img"
    main_data_folder_path = main_data_folder
    sub_data_folder_path = os.path.join(main_data_folder, sub_data_folder)
    make_folder(main_data_folder_path)
    make_folder(sub_data_folder_path)

    # --- 웹캠 사용을 위해 VideoCapture 인자를 cam_num으로 변경 ---
    cap = cv2.VideoCapture(cam_num) # cam_num은 0 (기본 웹캠) 또는 다른 카메라 인덱스/URL이 될 수 있음

    # 예외 처리: 카메라 미동작 시 에러 메시지 출력
    if not cap.isOpened():
        print(f"Failed to open webcam (camera index {cam_num}). Please check if the webcam is connected and available.")
        return

    # fps 설정: 카메라의 fps를 가져오되, 불가하다면 30으로 설정
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        fps = 30
        print(f"Warning: Could not retrieve FPS from webcam, defaulting to {fps} FPS.")
    
    # 화면 크기 설정: 카메라의 높이/너비를 가져온다
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Webcam opened with resolution: {width}x{height} at {fps} FPS.")

    # 모델 로드 (yolov8n.pt 또는 yolov11n.pt 사용)
    model_name = "yolov8n.pt" # 또는 "yolov11n.pt"
    model = model_load(model_name)
    if model is None:
        print(f"{model_name} model loading failed. Exiting capture_frames.")
        cap.release()
        cv2.destroyAllWindows()
        return

    # 관련 변수 선언: frame/person_class_id/find_class
    frame_count = 0
    person_class_id = None
    find_class = "person"
    
    # model.names는 딕셔너리이므로 .items()를 사용하여 순회
    for k, v in model.names.items():
        if v == find_class:
            person_class_id = k
            break
    if person_class_id is None:
        print(f"Error: '{find_class}' class not found in the loaded model. Person tracking might not work.")
        return

    # 카메라 실행
    while True:
        ret, frame = cap.read()
        frame_count += 1

        if not ret:
            print(f"Webcam stream for cam_num {cam_num} ended or error occured.")
            break

        # 현재 시간 정보 (DB 스키마의 timestamp 필드에 사용)
        current_time_dt = datetime.datetime.now() # datetime 객체로 저장
        timestamp_str = current_time_dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] # DB용 타임스탬프 (밀리초 포함)

        # --- 객체 탐지 및 트래킹 ---
        # classes=person_class_id를 사용하여 'person'만 탐지하도록 필터링
        # conf=0.5는 신뢰도 임계값, 이 값보다 낮은 탐지는 무시
        results = model.track(
            frame, persist=True, tracker="bytetrack.yaml", verbose=False, classes=person_class_id, conf=0.5
        )

        # 탐지된 프레임 변수에 저장 (미리보기용으로 원본 프레임을 복사)
        annotated_frame = frame.copy()
        
        # --- 이미지 저장 조건 (이 프레임이 저장 주기에 해당되는가?) ---
        # 예: 1초에 1번 저장 (fps는 보통 초당 프레임 수)
        is_this_a_saving_frame = False
        if int(fps) > 0 and frame_count % int(fps) == 0: 
            is_this_a_saving_frame = True

        # 트랙한 결과물이 존재하고, 추적 ID가 있는 경우에만 처리
        if results and results[0].boxes.id is not None:
            boxes_data = results[0].boxes.cpu().numpy() # GPU 텐서 -> CPU NumPy 배열

            # 각 탐지된 객체(사람)에 대해 반복
            for i in range(len(boxes_data.xyxy)):
                class_id = int(boxes_data.cls[i])
                class_name = model.names[class_id]
                confidence = float(boxes_data.conf[i])
                bbox_xyxy = boxes_data.xyxy[i] # [x1, y1, x2, y2]
                track_id = int(boxes_data.id[i]) # 이 값이 DB 스키마의 person_id에 해당

                # 'person' 클래스인 경우에만 처리
                if class_name == "person":
                    x1, y1, x2, y2 = map(int, bbox_xyxy)
                    
                    # 미리보기용 바운딩 박스 그리기
                    annotated_frame = draw_bounding_box(
                        annotated_frame, (x1, y1, x2, y2), class_name, confidence, track_id=track_id
                    )

                    # --- 이미지 저장 및 큐에 데이터 전송 (저장 주기에 해당되면 각 탐지된 사람마다) ---
                    if is_this_a_saving_frame:
                        global_image_sequence_counter += 1 # 전역 카운터 증가

                        # 이미지 크롭 범위 유효성 검사 및 조정
                        crop_x1 = max(0, x1)
                        crop_y1 = max(0, y1)
                        crop_x2 = min(width, x2)
                        crop_y2 = min(height, y2)
                        
                        image_filepath = None # 이미지 저장 경로 초기화

                        # 유효한 크롭 영역인 경우에만 이미지 저장
                        if crop_x2 > crop_x1 and crop_y2 > crop_y1:
                            object_crop = frame[crop_y1:crop_y2, crop_x1:crop_x2]

                            # 트랙 ID별 폴더 생성 (예: data/img/person_track0001/)
                            tracked_images_folder = os.path.join(
                                sub_data_folder_path, f"person_track{track_id:04d}"
                            )
                            make_folder(tracked_images_folder)

                            # 이미지 파일 이름은 전역 순차 번호 및 트랙 ID 포함 (예: hsw-000001.png)
                            pic_name = f"hsw-{global_image_sequence_counter:06d}.png"
                            image_filepath = os.path.join(tracked_images_folder, pic_name)

                            try:
                                cv2.imwrite(image_filepath, object_crop)
                                print(f"Saved: {image_filepath}") # 저장 확인용
                            except Exception as e:
                                print(f"Error saving image {image_filepath}: {e}")
                                image_filepath = None # 저장 실패 시 경로 없음으로 처리

                        # DB 스키마에 맞춘 데이터 구조를 큐에 전송 (이미지 저장 여부와 관계없이 탐지 정보 전송)
                        # embedding 필드는 현재 단계에서 생성되지 않으므로 None으로 설정
                        person_detection_data = {
                            "timestamp": timestamp_str,
                            "person_id": track_id,
                            "embedding": None, # 이 부분에 얼굴 임베딩 데이터가 들어갈 예정 (현재는 None)
                            "file_path": image_filepath, # 저장된 크롭 이미지의 전체 경로 (저장 실패 시 None)
                            "camera_id": cam_num,
                            "bb_x1": x1,
                            "bb_y1": y1,
                            "bb_x2": x2,
                            "bb_y2": y2
                        }
                        
                        # 큐에 데이터 삽입 시도 (큐가 가득 찼으면 삽입하지 않음)
                        try:
                            frame_data_queue_instance.put(person_detection_data, block=False)
                        except queue.Full:
                            print(f"Queue is full, skipping data for person ID {track_id} at {timestamp_str}")



        # --- 미리보기 화면 표시 및 종료 조건 --- (이 부분이 최종적으로 실행되어야 합니다)
        # 여기에 `annotated_frame` 유효성 검사를 추가해도 됩니다.
        if annotated_frame is None or annotated_frame.size == 0:
            print("Warning: final annotated_frame is empty or invalid, skipping imshow.")
            # 이 경우, 다음 프레임으로 건너뛰거나 루프를 중단하는 로직을 추가할 수 있습니다.
            # continue
        else:
            cv2.imshow(f'Live Preview (Cam {cam_num}) with YOLO Tracking (Press "q" to stop)', annotated_frame)
            
            # 'q' 키를 누르면 루프 종료
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("'q' 키 입력으로 작업을 중지합니다.")
                break
        
        # CPU 점유율을 줄이기 위해 아주 짧은 지연을 줄 수도 있지만,
        # 실시간 성능에 영향을 줄 수 있으므로 기본적으로는 주석 처리하거나 신중하게 사용
        # time.sleep(0.001)


    # --- 루프 종료 후 자원 해제 ---
    cap.release()
    cv2.destroyAllWindows()
    print(f"Capture for cam_num {cam_num} stopped. Total frames processed: {frame_count}")
    return {"status": "completed", "total_frames": frame_count, "camera_id": cam_num}


# --- 메인 실행 블록 ---
if __name__ == "__main__":
    # 데이터 전송을 위한 큐 인스턴스 생성
    my_frame_queue = queue.Queue(maxsize=10) # 큐 사이즈 제한

    # capture_frames 함수를 별도의 스레드에서 실행
    # target: 스레드가 실행할 함수
    # args: 함수에 전달할 인자 (튜플 형태)
    capture_thread = threading.Thread(target=capture_frames, args=(0, my_frame_queue))
    capture_thread.daemon = True # 메인 스레드 종료 시 capture_thread도 함께 종료되도록 설정 (권장)
    capture_thread.start() # 스레드 시작

    print("Capture thread started. Main thread can now perform other tasks (e.g., consume from queue).")

    # 메인 스레드에서 큐에서 데이터를 소비하는 예시 (이 부분이 실제 객체 비교 함수가 처리할 부분입니다)
    try:
        while True:
            # 큐에 데이터가 있다면 가져와서 처리
            if not my_frame_queue.empty():
                data_from_queue = my_frame_queue.get()
                # 여기에 데이터 처리 로직을 추가합니다 (예: DB 저장, 임베딩 비교 등)
                print(f"Main thread received data:")
                for key, value in data_from_queue.items():
                    # 임베딩이 None일 수 있으므로 특별 처리
                    if key == "embedding" and value is None:
                        print(f"  {key}: None (embedding not generated in capture_frames)")
                    else:
                        print(f"  {key}: {value}")
                
                # 큐에서 데이터를 가져왔으므로 큐에 공간이 생겼음을 알림 (task_done은 join 시에 유용)
                # my_frame_queue.task_done()

            # 큐를 너무 빠르게 확인하지 않도록 잠시 대기
            time.sleep(0.1) 

            # capture_thread가 종료되면 메인 스레드도 종료되도록 함
            if not capture_thread.is_alive():
                print("Capture thread finished. Main thread is also stopping.")
                break

    except KeyboardInterrupt:
        # Ctrl+C 입력 시 프로그램 종료
        print("Main thread received KeyboardInterrupt. Exiting.")
    finally:
        # 프로그램 종료 전에 큐에 남아있는 데이터가 있다면 처리 (선택 사항)
        print("Processing any remaining data in the queue...")
        while not my_frame_queue.empty():
            data_from_queue = my_frame_queue.get()
            print(f"  Remaining data: {data_from_queue['timestamp']}, Person ID: {data_from_queue['person_id']}")
        
        # daemon=True 설정으로 인해 명시적인 join()이 필요 없을 수 있지만,
        # 모든 작업이 완료될 때까지 기다리려면 join()을 사용할 수 있습니다.
        # capture_thread.join()
        print("Program terminated.")