from .db_connect import DatabaseManager
from .db_preprocess import DataPreprocessor
from .db_statistics import StatisticsCalculator
from .db_postprocess import StatisticsPostprocessor
from .db_test_utils import generate_dummy_rows

def get_page_sync(db_path_arg):
    """_summary_
    한페이지 전체 조회를 하였을 때에

    페이지 전체에 내보내는 통계 값들을 dictionary 형태로 내보냅니다.

     
    Args:
        db_path_arg (_type_): _description_

    Returns:
        _type_: _description_
    """
    # 1. DB 연결 및 테이블 준비
    db_path = db_path_arg
    db = DatabaseManager(db_path)
    # db.clear_table()

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
    
    ### RETURN MUST BE IN FORM OF DICTIONARY
    
     
    return { 
            "unique_visitor": visitor_count,
            
            }
