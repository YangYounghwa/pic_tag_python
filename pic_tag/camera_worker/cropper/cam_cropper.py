import cv2
import time

from pic_tag.camera_worker import frame_queue



def capture_frames(cam_num, rtsp_url):
    # cap = cv2.VideoCapture(rtsp_url)
    cap = cv2.VideoCapture(0)  # Use 0 for webcam or replace with rtsp_url for RTSP stream
    
    
    #코드 수정 시작
    if not cap.isOpened():
        print("Failed to open stream")
        return
    while True:
        ret, frame = cap.read()
        if not ret:
            break  # Stream ended or error
        result = simple_analyze(frame)
        
        result = None; # 만약에 아무것도 탐지가 안되면 None으로 설정
        # result should be
        # img, bounding_box, timeStamp, camera_id, img_name
        data_transfer = {            "img": result[0],
            "bounding_box": result[1],
            "timeStamp": result[2],
            "camera_id": cam_num,
            "img_name": result[3]
            }
        
        # 코드 수정 끝
        if result is None:
            continue
        frame_queue.put(data_transfer)      # send data to the consumer
        # small sleep or frame rate cap to avoid overwhelming consumer
        time.sleep(0.01)