# backend/db_statistics/views.py

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .get_by_id import get_info_by_id
from .page_sync import get_page_sync
from pathlib import Path

class PageSyncAPIView(APIView):
    def get(self, request):
        base_dir = Path(__file__).resolve().parent.parent.parent
        folder = base_dir / "data"
        folder.mkdir(parents=True, exist_ok=True)
        log_db_path = folder / "db" / "identity_log.db"
        result = get_page_sync(str(log_db_path))
        return Response(result, status=status.HTTP_200_OK)

class PersonDetailAPIView(APIView):
    def get(self, request, person_id):
        base_dir = Path(__file__).resolve().parent.parent.parent
        folder = base_dir / "data"
        folder.mkdir(parents=True, exist_ok=True)
        log_db_path = folder / "db" / "identity_log.db"
        result = get_info_by_id(str(log_db_path), person_id)
        return Response(result, status=status.HTTP_200_OK)

'''
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .page_sync import get_page_sync
from .get_by_id import get_info_by_id
from pathlib import Path


class PageSyncAPIView(APIView):
    def get(self, request):
        base_dir = Path(__file__).resolve().parent.parent.parent
        folder = None 
        if not folder:
            folder = base_dir / "data"
        folder.mkdir(parents=True, exist_ok=True)
        log_db_path = folder / "db" / "identity_log.db"
        result = get_page_sync(log_db_path)
        
        # current_on_CCTV 
        # last_24_people 
        # current_people
        result = {
            "current_on_CCTV"  : 2,
            "last_24_people " : 59,
            "current_people" : 23,
        }
        
        return Response(result, status=status.HTTP_200_OK)
    
class PersonDetailAPIView(APIView):
    def get(self, request):
        folder = None
        base_dir = Path(__file__).resolve().parent.parent.parent  
        if not folder:
            folder = base_dir / "data"
        folder.mkdir(parents=True, exist_ok=True)
        log_db_path = folder / "db" / "identity_log.db"
        result = get_info_by_id(log_db_path)
        result = {
            "one" : "one",
            "two" : "two"
        }
         
        return Response(result, status=status.HTTP_200_OK) 
    '''