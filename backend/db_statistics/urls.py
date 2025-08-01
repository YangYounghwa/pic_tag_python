# backend/db_statistics/urls.py

from django.urls import path
from .views import PageSyncAPIView, PersonDetailAPIView

urlpatterns = [
    path('page/', PageSyncAPIView.as_view(), name='pageSync'),
    path('get_by_id/<int:person_id>/', PersonDetailAPIView.as_view(), name='personDetail')
]

'''
from django.urls import path
from .views import PersonDetailAPIView
from .views import PageSyncAPIView 
urlpatterns = [
    path('page/', PageSyncAPIView.as_view(), name='pageSync'),
    path('get_by_id/<int:person_id>/',PersonDetailAPIView.as_view(), name='personDetail')
]
'''