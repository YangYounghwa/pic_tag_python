import cv2
import threading
import time

class RTSPCamera:
    def __init__(self, rtsp_url):
        self.rtsp_url = rtsp_url
        self.cap = cv2.VideoCapture(rtsp_url)
        self.frame = None
        self.running = True
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def _capture_loop(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame
            else:
                print(f"[{self.rtsp_url}] RTSP read failed.")
            time.sleep(0.05)

    def get_frame(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def stop(self):
        self.running = False
        self.cap.release()


class CameraPool:
    _instances = {}
    _lock = threading.Lock()

    @classmethod
    def get_camera(cls, camera_id, rtsp_url):
        with cls._lock:
            if camera_id not in cls._instances:
                cls._instances[camera_id] = RTSPCamera(rtsp_url)
            return cls._instances[camera_id]

    @classmethod
    def stop_all(cls):
        for cam in cls._instances.values():
            cam.stop()
        cls._instances.clear()