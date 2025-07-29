
from django.urls import path
from . import consumers
from django.urls import re_path
from .consumers import CameraStreamConsumer
print("[camera.routing] LOADED")

async def test_ws_view(scope, receive, send):
    print("🔥 test_ws_view called")
    await send({
        "type": "websocket.accept"
    })
    await send({
        "type": "websocket.close"
    })

websocket_urlpatterns = [
    re_path(r'ws/camera/(?P<camera_id>[^/]+)/$', consumers.CameraStreamConsumer.as_asgi()),
]
