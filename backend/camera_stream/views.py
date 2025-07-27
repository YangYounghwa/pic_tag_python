import cv2
import configparser
from django.http import StreamingHttpResponse, HttpResponseNotFound
import os
import time

def mjpeg_stream(request, camera_id):
    # Load RTSP config
    config_path = os.path.join(os.path.dirname(__file__), "pw", "camera_config.ini")
    config = configparser.ConfigParser()
    config.read(config_path)

    if camera_id not in config:
        return HttpResponseNotFound("Camera not found")

    cam = config[camera_id]
    ip = cam.get("ip")
    username = cam.get("username")
    password = cam.get("password")
    path = cam.get("path2")

    if not all([ip, username, password, path]):
        return HttpResponseNotFound("Incomplete camera info")

    rtsp_url = f"rtsp://{username}:{password}@{ip}/{path}"
    cap = cv2.VideoCapture(rtsp_url)

    def frame_generator():
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            _, jpeg = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            time.sleep(0.05)

    return StreamingHttpResponse(frame_generator(), content_type='multipart/x-mixed-replace; boundary=frame')