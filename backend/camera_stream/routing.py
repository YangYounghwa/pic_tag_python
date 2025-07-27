
from django.urls import path
from . import consumers

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
    path("ws/test/", test_ws_view),
    path("ws/camera/<str:camera_id>/", consumers.CameraStreamConsumer.as_asgi()),
]