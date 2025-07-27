"""
ASGI config for backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import sys
# from channels.auth import AuthMiddlewareStack
# from channels.routing import ProtocolTypeRouter, URLRouter
# from django.core.asgi import get_asgi_application

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


import monitoring.routing
import camera.routing


# print("[DEBUG] camera.routing module path:", camera.routing.__file__)

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     "websocket": AuthMiddlewareStack(
#         URLRouter(
#             camera.routing.websocket_urlpatterns
#         )
#     ),
# })


import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import camera.routing  # must be importable

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

print("🔥 asgi.py is loaded")  # this should show up

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(
        camera.routing.websocket_urlpatterns
    ),
})