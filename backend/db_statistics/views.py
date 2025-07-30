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
