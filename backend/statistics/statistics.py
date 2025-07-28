import sqlite3
import csv
import os
from datetime import datetime, timedelta
from pathlib import Path


class StatisticsFromDB:
    def __init__(self, db_path):
        """Initialize with a file-based SQLite database."""
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)  # 디렉토리 생성
        self.db_connection = sqlite3.connect(db_path)
        self.db_connection.row_factory = sqlite3.Row
        self._create_table()

    # 테스트를 위해 데이터 베이스 생성하는 코드, 추후 주석 처리 혹은 삭제 예정
    def _create_table(self):
        """Create identity_log table if it doesn't exist."""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS identity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    person_id INTEGER NOT NULL,
                    embedding TEXT NOT NULL,
                    file_path TEXT,
                    camera_id INTEGER,
                    bb_x1 INTEGER,
                    bb_y1 INTEGER,
                    bb_x2 INTEGER,
                    bb_y2 INTEGER
                )
            """
            )
            self.db_connection.commit()
            cursor.close()
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")

    # 테스트용 메소드, 추후 주석 처리 혹은 삭제 예정
    def clear_table(self):
        # Clear all data from identity_log table.
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("DELETE FROM identity_log")
            self.db_connection.commit()
            cursor.close()
        except sqlite3.Error as e:
            print(f"Error clearing table: {e}")

    def generate_dummy_data(self, num_entries=100):
        """Generate dummy data with varying stay times per person_id."""
        cursor = self.db_connection.cursor()
        base_time = datetime(2023, 10, 1, 12, 0, 0)
        entries_per_person = num_entries // 10  # 10 person_ids (0-9)

        for person_id in range(10):
            stay_duration = (person_id + 1) * 10  # 체류 시간(분): 10, 20, ..., 100
            for i in range(entries_per_person):
                minutes_offset = (
                    i * (stay_duration / (entries_per_person - 1))
                    if entries_per_person > 1
                    else 0
                )
                timestamp = (base_time + timedelta(minutes=minutes_offset)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                cursor.execute(
                    "INSERT INTO identity_log (timestamp, person_id, embedding, file_path, camera_id, bb_x1, bb_y1, bb_x2, bb_y2) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        timestamp,
                        person_id,
                        f"embedding_{person_id}_{i}",
                        f"/path/to/image_{person_id}_{i}.jpg",
                        person_id % 5,
                        i * 10,
                        i * 15,
                        i * 20 + 50,
                        i * 25 + 50,
                    ),
                )
        self.db_connection.commit()
        cursor.close()

    def get_statistics(self, start_time=None, end_time=None):
        """Retrieve statistics from identity_log table."""
        try:
            cursor = self.db_connection.cursor()
            query = "SELECT * FROM identity_log"
            params = []
            if start_time and end_time:
                query += " WHERE timestamp BETWEEN ? AND ?"
                params = (start_time, end_time)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            return rows
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []

    def validate_statistics(self, statistics):
        """Validate the structure and types of statistics data."""
        if not statistics:
            return False
        for row in statistics:
            if len(row) < 9:
                return False
            if not isinstance(row[0], int) or not isinstance(row[2], int):
                return False
            if not isinstance(row[3], str) or not isinstance(row[4], str):
                return False
            if not isinstance(row[5], int) or not isinstance(row[6], int):
                return False
            if not isinstance(row[7], int) or not isinstance(row[8], int):
                return False
        return True

    def calculate_visitor_count(self, statistics):
        """Calculate the number of unique visitors from validated statistics."""
        if not self.validate_statistics(statistics):
            return 0
        visitor_ids = {row[2] for row in statistics}
        return len(visitor_ids)

    def calculate_stay_times(self, statistics):
        """Calculate stay time per person from validated statistics.
        Returns:
            dict: {person_id: stay_time_in_seconds}
        """
        if not self.validate_statistics(statistics):
            return {}
        stay_times = {}
        for row in statistics:
            person_id = row[2]
            timestamp = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
            if person_id not in stay_times:
                stay_times[person_id] = [timestamp, timestamp]
            else:
                stay_times[person_id][0] = min(stay_times[person_id][0], timestamp)
                stay_times[person_id][1] = max(stay_times[person_id][1], timestamp)

        return {
            person_id: (end - start).total_seconds()
            for person_id, (start, end) in stay_times.items()
        }

    def calculate_current_visitors(self, statistics):
        """Calculate the number of visitors present at the latest timestamp in the data."""
        if not self.validate_statistics(statistics):
            return 0
        if not statistics:
            return 0
        # 데이터 내 가장 마지막 timestamp 찾기
        latest_time = max(datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S") for row in statistics)
        one_minute_ago = latest_time - timedelta(minutes=1)
        current_visitors = {
            row[2]
            for row in statistics
            if one_minute_ago < datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S") <= latest_time
        }
        return len(current_visitors)

    def calculate_current_visitors_per_row(self, statistics):
        """각 행의 timestamp 기준 1분 이내 체류 인원(중복 없는 person_id 수) 반환.
        Returns:
            dict: {row_id: current_visitors_count}
        """
        if not self.validate_statistics(statistics):
            return {}
        # 미리 timestamp, person_id만 추출
        time_person = [(row[0], datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S"), row[2]) for row in statistics]
        result = {}
        for row_id, ts, _ in time_person:
            one_minute_ago = ts - timedelta(minutes=1)
            # 1분 이내에 기록된 person_id 집합
            visitors = {pid for _, t, pid in time_person if one_minute_ago < t <= ts}
            result[row_id] = len(visitors)
        return result

    def save_statistics_to_csv(self, output_path, statistics):
        """Save statistics and computed metrics to a CSV file."""
        try:
            visitor_count = self.calculate_visitor_count(statistics)
            stay_times = self.calculate_stay_times(statistics)
            current_visitors_per_row = self.calculate_current_visitors_per_row(statistics)

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = [
                    "id",
                    "timestamp",
                    "person_id",
                    "embedding",
                    "file_path",
                    "camera_id",
                    "bb_x1",
                    "bb_y1",
                    "bb_x2",
                    "bb_y2",
                    "visitor_count",
                    "stay_time",
                    "current_visitors",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for row in statistics:
                    person_id = row[2]
                    writer.writerow(
                        {
                            "id": row[0],
                            "timestamp": row[1],
                            "person_id": person_id,
                            "embedding": row[3],
                            "file_path": row[4],
                            "camera_id": row[5],
                            "bb_x1": row[6],
                            "bb_y1": row[7],
                            "bb_x2": row[8],
                            "bb_y2": row[9] if len(row) > 9 else None,
                            "visitor_count": visitor_count,
                            "stay_time": stay_times.get(person_id, 0),
                            "current_visitors": current_visitors_per_row.get(row[0], 0),
                        }
                    )
            print(f"Statistics saved to {output_path}")
        except Exception as e:
            print(f"Error saving to CSV: {e}")

    def close_connection(self):
        """Close the database connection."""
        self.db_connection.close()



# 테스트 코드 (주석 처리)
def test_statistics_from_db(db_path=None):
    default_db_path = "/Users/hong/Projects/pic_tag_python/backend/statistics/database.db"
    output_path = "/Users/hong/Projects/pic_tag_python/backend/statistics/statistics_output.csv"
    
    # db_path가 제공되지 않으면 환경 변수 또는 기본 경로 사용
    db_path = db_path or os.environ.get("DB_PATH", default_db_path)
    
    # 데이터베이스 초기화
    stats = StatisticsFromDB(db_path)
    
    # 테이블 비우기
    stats.clear_table()
    
    # 더미 데이터 생성
    stats.generate_dummy_data(num_entries=100)
    
    # 통계 조회
    rows = stats.get_statistics()
    assert len(rows) == 100, f"Expected 100 rows, but got {len(rows)}"
    
    # 데이터 유효성 검사
    assert stats.validate_statistics(rows), "Data validation failed"
    
    # 방문자 수 계산
    visitor_count = stats.calculate_visitor_count(rows)
    assert visitor_count == 10, f"Expected 10 unique visitors, but got {visitor_count}"
    
    # 방문자별 체류 시간 계산
    stay_times = stats.calculate_stay_times(rows)
    expected_stay_times = {i: (i + 1) * 10 * 60 for i in range(10)}  # 10분, 20분, ..., 100분
    for person_id, stay_time in stay_times.items():
        expected = expected_stay_times[person_id]
        assert abs(stay_time - expected) < 1e-5, f"Expected {expected} seconds for person {person_id}, but got {stay_time}"

    # 현재 체류 중인 방문자 수 계산
    current_visitors = stats.calculate_current_visitors(rows)
    # assert current_visitors == 10, f"Expected 10 current visitors, but got {current_visitors}"
    
    # CSV로 저장
    stats.save_statistics_to_csv(output_path, rows)
    
    print(f"All tests passed! Database: {db_path}, CSV: {output_path}")
    stats.close_connection()

if __name__ == "__main__":
    test_statistics_from_db()

