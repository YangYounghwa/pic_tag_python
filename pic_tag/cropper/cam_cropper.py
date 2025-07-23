import cv2
import time

def capture_frames(rtsp_url):
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        print("Failed to open stream")
        return
    while True:
        ret, frame = cap.read()
        if not ret:
            break  # Stream ended or error
        result = simple_analyze(frame)  
        frame_queue.put(result)      # send data to the consumer
        # small sleep or frame rate cap to avoid overwhelming consumer
        time.sleep(0.01)