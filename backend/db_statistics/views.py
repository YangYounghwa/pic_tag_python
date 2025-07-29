from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .page_sync import get_page_sync
from .get_info_by_id import get_info_by_id
from pathlib import Path

class PageSyncAPIView(APIView):
    def get(self, request):
        # DB 경로 설정
        base_dir = Path(__file__).resolve().parent.parent.parent
        folder = base_dir / "data"
        folder.mkdir(parents=True, exist_ok=True)
        log_db_path = folder / "db" / "identity_log.db"

        # get_page_sync 호출
        result = get_page_sync(str(log_db_path))
        if "error" in result:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(result, status=status.HTTP_200_OK)

class PersonDetailAPIView(APIView):
    def get(self, request, person_id):
        # DB 경로 설정
        base_dir = Path(__file__).resolve().parent.parent.parent
        folder = base_dir / "data"
        folder.mkdir(parents=True, exist_ok=True)
        log_db_path = folder / "db" / "identity_log.db"

        # get_info_by_id 호출
        result = get_info_by_id(str(log_db_path), person_id)
        if "error" in result:
            if "No data found" in result["error"]:
                return Response(result, status=status.HTTP_404_NOT_FOUND)
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(result, status=status.HTTP_200_OK)