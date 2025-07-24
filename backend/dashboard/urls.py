from django.urls import path
from . import views 

app_name = 'dashboard'

urlpatterns = [
    path("", views.dashboard_page, name="dashboard_page"),
]
