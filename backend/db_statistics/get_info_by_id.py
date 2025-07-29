from .db_connect import DatabaseManager
from .db_preprocess import DataPreprocessor
from .db_statistics import StatisticsCalculator
from .db_postprocess import StatisticsPostprocessor
from .db_test_utils import generate_dummy_rows


def get_info_by_id(db_path_arg,id):
    """_summary_
    
    한 사람 (id)에 대해서 조회를 하였을 때에 내보내는 값들 입니다.

    한 사람의 체류시간, 
    한 사람의 행동 list등이 있습니다.

    Args:
        db_path_arg (_type_): _description_
        id (_type_): _description_

    Returns:
        _type_: _description_
    """
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
    
    return { 
            "unique_visitor": visitor_count,
            
            }
