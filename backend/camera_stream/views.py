import cv2
import configparser
from django.http import StreamingHttpResponse, HttpResponseNotFound
import os
import time
from .services.rtsp_pool import CameraPool
from turbojpeg import TurboJPEG

jpeg = TurboJPEG()

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

    # 🔁 Use shared camera from pool
    camera = CameraPool.get_camera(camera_id, rtsp_url)

    def frame_generator():
        while True:
            frame = camera.get_frame()
            if frame is not None:
                # Optional: resize for lighter MJPEG
                resized = cv2.resize(frame, (640, 360))  # or (320, 180) for ultra-low
                jpeg_bytes = jpeg.encode(resized, quality=70)

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' +
                       jpeg_bytes + b'\r\n')

            time.sleep(0.05)  # ~10 FPS (adjust for lower server load)

    return StreamingHttpResponse(frame_generator(), content_type='multipart/x-mixed-replace; boundary=frame')