from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
import cv2
import base64
import numpy as np
from .services.rtsp_pool import CameraPool
import configparser
import os
from urllib.parse import parse_qs
# from turbojpeg import TurboJPEG
# jpeg = TurboJPEG()


class CameraStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.camera_id = self.scope['url_route']['kwargs']['camera_id']
        self.query_params = parse_qs(self.scope["query_string"].decode())
        self.is_thumbnail = self.query_params.get("thumb", ["0"])[0] == "1"

        self.rtsp_url = self.get_rtsp_url_from_config(self.camera_id)
        if not self.rtsp_url:
            await self.close()
            return

        self.camera = CameraPool.get_camera(self.camera_id, self.rtsp_url)
        await self.accept()

        self.running = True
        self.stream_task = asyncio.create_task(self.send_stream())

    async def disconnect(self, close_code):
        self.running = False
        if hasattr(self, 'stream_task'):
            self.stream_task.cancel()
        print(f"⚠️ WebSocket disconnected for {self.camera_id}")

    async def send_stream(self):
        while self.running:
            frame = self.camera.get_frame()
            if frame is not None:
                if self.is_thumbnail:
                    frame = cv2.resize(frame, (320, 180))  # or 160x90

                _, jpeg = cv2.imencode('.jpg', frame)
                b64 = base64.b64encode(jpeg.tobytes()).decode('utf-8')
                await self.send(text_data=b64)

            await asyncio.sleep(0.2 if self.is_thumbnail else 0.05)
    #960x540
    def get_rtsp_url_from_config(self, camera_name):
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), "pw", "camera_config.ini")
        config.read(config_path)

        if camera_name not in config:
            print(f"❌ Camera '{camera_name}' not found in config.")
            return None

        cam = config[camera_name]
        ip = cam.get("ip")
        username = cam.get("username")
        password = cam.get("password")
        path = cam.get("path2")  # or path1

        if not all([ip, username, password, path]):
            print(f"❌ Missing values for camera: {camera_name}")
            return None

        return f"rtsp://{username}:{password}@{ip}/{path}"