from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
import cv2
import base64
import numpy as np
from .services.rtsp_pool import CameraPool
import configparser

class CameraStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.camera_id = self.scope['url_route']['kwargs']['camera_id']
        self.rtsp_url = self.get_rtsp_url_from_config(self.camera_id)

        if not self.rtsp_url:
            await self.close()
            return

        print(f"Connecting to: {self.rtsp_url}")
        self.cap = cv2.VideoCapture(self.rtsp_url)

        if not self.cap.isOpened():
            print("❌ Failed to open camera.")
            await self.close()
            return

        await self.accept()
        self.running = True
        self.stream_task = asyncio.create_task(self.send_stream())

    async def disconnect(self, close_code):
        self.running = False
        if hasattr(self, 'cap'):
            self.cap.release()
        if hasattr(self, 'stream_task'):
            self.stream_task.cancel()

    async def send_stream(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                _, jpeg = cv2.imencode('.jpg', frame)
                b64 = base64.b64encode(jpeg.tobytes()).decode('utf-8')
                await self.send(text_data=b64)
            await asyncio.sleep(0.1)

    def get_rtsp_url_from_config(self, camera_name):
        config = configparser.ConfigParser()
        config.read("pw/camera_config.ini")

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