<<<<<<< Updated upstream:backend/statistics/main.py
from backend.statistics.db import DatabaseManager
from backend.statistics.preprocess import DataPreprocessor
from backend.statistics.statistics import StatisticsCalculator
from backend.statistics.postprocess import StatisticsPostprocessor
from backend.statistics.test_utils import generate_dummy_rows

def main():
    # 1. DB 연결 및 테이블 준비
    db_path = "backend/statistics/database.db"
    db = DatabaseManager(db_path)
    db.clear_table()

    # 2. 더미 데이터 생성 및 삽입
    dummy_rows = generate_dummy_rows(100)
    db.insert_dummy_data(dummy_rows)

    # 3. DB에서 데이터 조회
    rows = db.fetch_statistics()

    # 4. 행 단위 전처리
    pre = DataPreprocessor()
    rows = pre.filter_row_outliers(rows)

    # 5. 통계 계산
    calc = StatisticsCalculator()
    visitor_count = calc.calculate_visitor_count(rows)
    stay_times = calc.calculate_stay_times(rows)
    current_visitors_per_row = calc.calculate_current_visitors(rows)

    # 6. 후처리 (예: 체류 시간 기준 person_id 필터링)
    post = StatisticsPostprocessor()
    filtered_rows = post.filter_by_stay_time(rows, stay_times, min_seconds=30, max_seconds=3600)

    # 7. 결과 출력 (간단 예시)
    print(f"유니크 방문자 수: {visitor_count}")
    print(f"person_id별 체류 시간(초): {stay_times}")
    print(f"각 행 기준 1분 이내 체류 인원: {list(current_visitors_per_row.items())[:5]} ...")
    print(f"후처리(체류시간 기준) 후 row 수: {len(filtered_rows)}")

    # 8. DB 연결 종료
    db.close()

if __name__ == "__main__":
    main()
=======
# backend/db_statistics/page_sync.py

from pathlib import Path
from .db_connect import DatabaseManager
from .db_preprocess import DataPreprocessor
from .db_statistics import StatisticsCalculator
from .db_postprocess import StatisticsPostprocessor
from .db_test_utils import generate_dummy_rows

def get_page_sync(db_path):
    """페이지 전체 통계 데이터를 딕셔너리 형태로 반환.

    Args:
        db_path (str): SQLite 데이터베이스 파일 경로.

    Returns:
        dict: 유니크 방문자 수, 체류 시간, 현재 체류 인원, 필터링된 행 수를 포함.
        get_page_sync 의 return 값
        { "current_on_CCTV" :  current_on_CCTV(최근20초내 있는 인원),
        "last_24_people" : last_24_people,
        "current_people" : current_people(최근 15분간 감지된 인원),
        "recent_5_list" : recent_5_list }
    """
    # 1. DB 연결
    db = DatabaseManager(db_path)
    
    try:
        # 테스트용 더미 데이터 생성 (개발 중에만 사용)
        generate_dummy_rows(db, 100)  # 주석 처리하여 실제 데이터베이스 사용

        # 2. DB에서 데이터 조회
        rows = db.fetch_statistics()
        if not rows:
            return {"error": "No data found in the database."}

        # 3. 행 단위 전처리
        pre = DataPreprocessor()
        rows = pre.filter_row_outliers(rows)

        # 4. 통계 계산
        calc = StatisticsCalculator()
        visitor_count = calc.calculate_visitor_count(rows)
        stay_times = calc.calculate_stay_times(rows)
        current_visitors_per_row = calc.calculate_current_visitors(rows)

        # 5. 후처리 (체류 시간 기준 필터링)
        post = StatisticsPostprocessor()
        filtered_rows = post.filter_by_stay_time(rows, stay_times, min_seconds=30, max_seconds=3600)

        # 6. 결과 딕셔너리 구성
        result = {
            "current_on_CCTV": calc.get_current_on_CCTV(rows),
            "last_24_people": calc.get_last_24_people(rows),
            "current_people": calc.get_current_people(rows, time_window_minutes=15),
            "recent_5_list": calc.get_recent_5_list(rows)
        }

        # 7. 테스트용 출력
        print(f"Filtered Rows: {len(filtered_rows)}")
        print(f"Result: {result}")
        
        return result
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()
>>>>>>> Stashed changes:backend/db_statistics/page_sync.py
