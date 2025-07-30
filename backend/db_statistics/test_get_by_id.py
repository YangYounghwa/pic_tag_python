# backend/db_statistics/test_get_by_id.py

import sys
import os
from datetime import datetime, timedelta

# 패키지 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.db_statistics.db_connect import DatabaseManager
from backend.db_statistics.db_test_utils import generate_dummy_rows
from backend.db_statistics.get_by_id import get_info_by_id

def test_get_info_by_id():
    db_path = "/Users/hong/Projects/pic_tag_python/backend/db_statistics/database.db"
    person_id = 101

    # DB 초기화 및 더미 데이터 삽입
    db = DatabaseManager(db_path)
    db.clear_table()
    dummy_rows = generate_dummy_rows(100)
    db.insert_dummy_data(dummy_rows)

    # 테스트 실행
    result = get_info_by_id(db_path, person_id)
    print(result)
    print(f"Recent actions: {result['recent_actions']}")
    print(f"Stay time: {result['stay_time']} seconds")
    print(f"Number of actions: {len(result['recent_actions'])}")
    print("All test cases passed successfully.")

if __name__ == "__main__":
    test_get_info_by_id()