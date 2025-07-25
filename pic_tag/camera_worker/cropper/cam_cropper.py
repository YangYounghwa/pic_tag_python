import cv2
import time
import os
from ultralytics import YOLO
import datetime

# 코드가 없어서 임시 테스트용 코드로 대체
# from pic_tag.camera_worker import frame_queue
import queue # 테스트용 임포트


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

    # --- 웹캠 사용을 위해 VideoCapture 인자를 0으로 변경 ---
    cap = cv2.VideoCapture(0) # 0은 보통 시스템의 기본 웹캠을 의미합니다.

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

    # 모델 로드
    model_name = "yolo8n.pt"
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
    for k, v in model.names.items():
        if v == find_class:
            person_class_id = k
            break
    
    if person_class_id is None:
        print("Error: 'person' class not found in the loaded model. Person tracking might not work.")


    while True:
        ret, frame = cap.read()
        frame_count += 1

        if not ret:
            print(f"Webcam stream for cam_num {cam_num} ended or error occured.")
            break

        current_time = datetime.datetime.now()
        timestamp_str = current_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        img_name_for_frame = f"frame_{current_time.strftime('%Y%m%d_%H%M%S_%f')[:-3]}.jpg"

        # --- 객체 탐지 및 트래킹 ---
        # classes=person_class_id를 사용하여 'person'만 탐지하도록 필터링
        results = model.track(
            frame, persist=True, tracker="bytetrack.yaml", verbose=False, classes=person_class_id, conf=0.5
        )

        annotated_frame = frame.copy()
        detected_person_bboxes_for_queue = []
        
        # --- 이미지 저장 조건 (이 프레임이 저장 주기에 해당되는가?) ---
        is_this_a_saving_frame = False
        if frame_count % int(fps) == 0: # fps를 정수형으로 변환하여 사용 (예: 1초에 한 번)
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
                    detected_person_bboxes_for_queue.append([x1, y1, x2, y2])

                    annotated_frame = draw_bounding_box(
                        annotated_frame, (x1, y1, x2, y2), class_name, confidence, track_id=track_id
                    )

                    # --- 이미지 저장 (각 탐지된 사람마다 저장) ---
                    # is_this_a_saving_frame이 True이면, 이 프레임에서 탐지된 모든 사람의 이미지를 저장
                    if is_this_a_saving_frame:
                        global_image_sequence_counter += 1 # 전역 카운터 증가

                        crop_x1 = max(0, x1)
                        crop_y1 = max(0, y1)
                        crop_x2 = min(width, x2)
                        crop_y2 = min(height, y2)
                        
                        if crop_x2 > crop_x1 and crop_y2 > crop_y1:
                            object_crop = frame[crop_y1:crop_y2, crop_x1:crop_x2]

                            # 트랙 ID별 폴더 생성 (이전 로직 복원)
                            tracked_images_folder = os.path.join(
                                main_detected_images_folder, f"person_track{track_id:04d}"
                            )
                            make_folder(tracked_images_folder)

                            # 이미지 파일 이름은 전역 순차 번호 사용
                            pic_name = f"hsw-{global_image_sequence_counter:06d}.png"
                            image_filepath = os.path.join(tracked_images_folder, pic_name)

                            try:
                                cv2.imwrite(image_filepath, object_crop)
                            except Exception as e:
                                print(f"Error saving image {image_filepath}: {e}")
                        

        # --- 큐에 데이터 전송 ---
        if detected_person_bboxes_for_queue:
            data_transfer = {
                "img": annotated_frame,
                "bounding_box": detected_person_bboxes_for_queue,
                "timeStamp": timestamp_str,
                "camera_id": cam_num,
                "img_name": img_name_for_frame,
            }

            frame_data_queue_instance.put(data_transfer) # 올바른 큐 인스턴스 사용



        # --- 미리보기 및 종료 조건 ---
        cv2.imshow('Live Preview with YOLO Tracking (Press "q" to stop)', annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("'q' 키 입력으로 작업을 중지합니다.")
            break
        
        time.sleep(0.01)


    # --- 루프 종료 후 정리 ---
    cap.release()
    cv2.destroyAllWindows()
    return {"status": "completed", "total_frames": frame_count, "camera_id": cam_num}


# --- 함수 호출 예시 (웹캠 사용) ---
if __name__ == "__main__":
    my_frame_queue = queue.Queue(maxsize=10)
    capture_frames(cam_num=0, frame_data_queue_instance=my_frame_queue)