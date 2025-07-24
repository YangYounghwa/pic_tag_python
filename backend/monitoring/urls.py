from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('monitoring/', views.monitoring, name='monitoring'),
    path('detection/', views.detection, name='detection'),
    path('statistics/', views.statistics, name='statistics'),
    path('settings/', views.settings, name='settings'),
]