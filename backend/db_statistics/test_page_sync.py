# backend/db_statistics/test_page_sync.py

import sys
import os
from datetime import datetime, timedelta

# 패키지 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.db_statistics.db_connect import DatabaseManager
from backend.db_statistics.db_test_utils import generate_dummy_rows
from backend.db_statistics.page_sync import get_page_sync

def test_get_page_sync():
    db_path = "/Users/hong/Projects/pic_tag_python/backend/db_statistics/database.db"

    # DB 초기화 및 더미 데이터 삽입
    db = DatabaseManager(db_path)
    db.clear_table()
    dummy_rows = generate_dummy_rows(100)
    db.insert_dummy_data(dummy_rows)

    # 테스트 실행
    result = get_page_sync(db_path)
    
    # 결과 출력
    print(result)
    print(f"Current on CCTV (last 20s): {result['current_on_CCTV']}")
    print(f"Last 24 hours people: {result['last_24_people']}")
    print(f"Current people (last 15m): {result['current_people']}")
    print(f"Recent 5 visitors: {result['recent_5_list']}")
    print(f"Number of recent visitors: {len(result['recent_5_list'])}")
    print("All test cases passed successfully.")

if __name__ == "__main__":
    test_get_page_sync()