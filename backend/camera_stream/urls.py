from django.urls import path    

from . import views


urlpatterns = [
    path("<str:camera_id>/", views.mjpeg_stream, name="mjpeg_stream"),
]