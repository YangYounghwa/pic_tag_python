# backend/db_statistics/get_by_id.py

from .db_connect import DatabaseManager
from .db_preprocess import DataPreprocessor
from .db_statistics import StatisticsCalculator
from .db_postprocess import StatisticsPostprocessor
from datetime import datetime, timedelta

def get_page_sync(db_path):
    """페이지 전체 통계 데이터를 반환.

    Args:
        db_path (str): 데이터베이스 파일 경로

    Returns:
        dict: {
            "current_on_CCTV": int (최근 20초 내 인원),
            "last_24_people": int (최근 24시간 내 인원),
            "current_people": int (최근 15분 내 인원),
            "recent_5_list": list [(person_id, file_path), ...]
        }
    """
    # 1. DB 연결
    db = DatabaseManager(db_path)

    # 2. 데이터 조회
    now = datetime.now()
    start_20s = (now - timedelta(seconds=20)).strftime("%Y-%m-%d %H:%M:%S")
    start_15m = (now - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
    start_24h = (now - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")

    rows_20s = db.fetch_statistics(start_time=start_20s)
    rows_15m = db.fetch_statistics(start_time=start_15m)
    rows_24h = db.fetch_statistics(start_time=start_24h)

    # 3. 데이터 전처리
    pre = DataPreprocessor()
    if not pre.validate(rows_24h):
        db.close()
        return {
            "current_on_CCTV": 0,
            "last_24_people": 0,
            "current_people": 0,
            "recent_5_list": []
        }

    rows_20s = pre.filter_row_outliers(rows_20s)
    rows_15m = pre.filter_row_outliers(rows_15m)
    rows_24h = pre.filter_row_outliers(rows_24h)

    # 4. 통계 계산
    calc = StatisticsCalculator()
    current_on_CCTV = calc.calculate_visitor_count(rows_20s)
    current_people = calc.calculate_visitor_count(rows_15m)
    last_24_people = calc.calculate_visitor_count(rows_24h)
    recent_5_list = calc.calculate_recent_visitors(rows_24h, count=5)

    # 5. 후처리
    post = StatisticsPostprocessor()
    rows_24h = post.filter_by_stay_time(rows_24h, calc.calculate_stay_times(rows_24h), min_seconds=30, max_seconds=3600)

    # 6. DB 연결 종료
    db.close()

    return {
        "current_on_CCTV": current_on_CCTV,
        "last_24_people": last_24_people,
        "current_people": current_people,
        "recent_5_list": recent_5_list
    }
