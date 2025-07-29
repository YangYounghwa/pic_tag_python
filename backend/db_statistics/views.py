
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
        result = {
            "one" : "one",
            "two" : "two"
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