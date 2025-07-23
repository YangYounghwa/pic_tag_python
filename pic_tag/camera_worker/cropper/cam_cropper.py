import cv2
import time

from pic_tag.camera_worker import frame_queue



def capture_frames(cam_num, rtsp_url):
    # cap = cv2.VideoCapture(rtsp_url)
    cap = cv2.VideoCapture(0)  # Use 0 for webcam or replace with rtsp_url for RTSP stream
    if not cap.isOpened():
        print("Failed to open stream")
        return
    while True:
        ret, frame = cap.read()
        if not ret:
            break  # Stream ended or error
        result = simple_analyze(frame)
        # result should be
        # img, bounding_box, timeStamp, camera_id
        
        frame_queue.put(result)      # send data to the consumer
        # small sleep or frame rate cap to avoid overwhelming consumer
        time.sleep(0.01)