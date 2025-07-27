from django.urls import path
from . import views
from django.shortcuts import redirect

urlpatterns = [
    path("", lambda request: redirect("dashboard/")),
    path("dashboard/", views.dashboard, name="dashboard"),
]