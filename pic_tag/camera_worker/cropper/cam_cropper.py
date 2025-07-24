import cv2
import time
import os

from pic_tag.camera_worker import frame_queue

def make_folder(folder_name):

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"'{folder_name}' folder has been made.")
    else:
        print(f"{folder_name} folder already exist.")


def draw_bounding_box(
        image,
        bbox,
        class_name,
        confidence,
        color=(0,255,0),
        thickness=2,
        track_id=None
):
    x1, y1, x2, y2 = map(int, bbox)
    cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
    label = f"{class_name}: {confidence}"
    if track_id is not None:
        label = f"ID{track_id}-{label}"
    cv2.putText(image, label, (x1, y1 - 10)), 


"""

"""

    

def capture_frames(cam_num, rtsp_url):

    # 현재 경로에 이미지를 저장할 폴더 확인/생성
    make_folder("detected_images")

    # cap = cv2.VideoCapture(rtsp_url)
    cap = cv2.VideoCapture(
        0
    )  # Use 0 for webcam or replace with rtsp_url for RTSP stream

    # 코드 수정 시작
    if not cap.isOpened():
        print("Failed to open stream")
        return
    while True:
        ret, frame = cap.read()
        if not ret:
            break  # Stream ended or error
        result = simple_analyze(frame)

        result = None
        # 만약에 아무것도 탐지가 안되면 None으로 설정
        # result should be
        # img, bounding_box, timeStamp, camera_id, img_name
        data_transfer = {
            "img": result[0],
            "bounding_box": result[1],
            "timeStamp": result[2],
            "camera_id": cam_num,
            "img_name": result[3],
        }

        # 코드 수정 끝
        if result is None:
            continue
        frame_queue.put(data_transfer)  # send data to the consumer
        # small sleep or frame rate cap to avoid overwhelming consumer
        time.sleep(0.01)
