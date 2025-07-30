# backend/db_statistics/db_statistics.py

from datetime import datetime, timedelta


# row를 이용하지 않고, 데이터 베이스의 열 이름을 사용하는 함수로 리팩토링 --- IGNORE ---
class StatisticsCalculator:
    """
    CREATE TABLE IF NOT EXISTS identity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    person_id INTEGER NOT NULL,
                    embedding TEXT NOT NULL,
                    file_path TEXT,
                    camera_id TEXT,
                    bb_x1 INTEGER,
                    bb_y1 INTEGER,
                    bb_x2 INTEGER,
                    bb_y2 INTEGER
                )
    """

    def calculate_visitor_count(self, rows):
        """유니크 방문자 수 계산"""
        print(f"Calculating unique visitor count from {len(rows)} rows.")
        return len({row["person_id"] for row in rows})

    def calculate_stay_times(self, rows):
        """person_id별 체류 시간(초) 계산"""
        stay_times = {}
        for row in rows:
            person_id = row["person_id"]
            timestamp = datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S")
            if person_id not in stay_times:
                stay_times[person_id] = [timestamp, timestamp]
            else:
                stay_times[person_id][0] = min(stay_times[person_id][0], timestamp)
                stay_times[person_id][1] = max(stay_times[person_id][1], timestamp)
        print(f"Calculated stay times for {len(stay_times)} unique person_ids.")
        return {
            person_id: (end - start).total_seconds()
            for person_id, (start, end) in stay_times.items()
        }

    def calculate_current_visitors(self, rows, window_minutes=1):
        """각 행의 timestamp 기준 window_minutes 이내 체류 인원(중복 없는 person_id 수) 반환"""
        result = {}
        time_person = [
            (
                row["id"],
                datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S"),
                row["person_id"],
            )
            for row in rows
        ]
        for row_id, ts, _ in time_person:
            window_start = ts - timedelta(minutes=window_minutes)
            visitors = {pid for _, t, pid in time_person if window_start < t <= ts}
            result[row_id] = len(visitors)
        print(f"Calculated current visitors for {len(result)} rows.")
        return result

    # 최근 5명 방문자 ID, 이미지 경로 반환
    def calculate_recent_visitors(self, rows, count=5):
        """최근 방문자 ID와 이미지 경로 반환"""
        recent_visitors = sorted(rows, key=lambda x: x["timestamp"], reverse=True)[
            :count
        ]
        print(f"Recent visitors: {len(recent_visitors)} rows.")
        return [(row["person_id"], row["file_path"]) for row in recent_visitors]


"""
# test code: 주석 부분은 테스트 용 예시 데이터를 생성하여, 통계 계산 메서드를 테스트합니다.
if __name__ == "__main__":
    example_rows = [
        {'id': 1, 'timestamp': '2023-10-01 12:00:00', 'person_id': 101, 'embedding': '...', 'file_path': '/path/to/file1', 'camera_id': 'cam1', 'bb_x1': 10, 'bb_y1': 20, 'bb_x2': 30, 'bb_y2': 40},
        {'id': 2, 'timestamp': '2023-10-01 12:05:00', 'person_id': 102, 'embedding': '...', 'file_path': '/path/to/file2', 'camera_id': 'cam1', 'bb_x1': 15, 'bb_y1': 25, 'bb_x2': 35, 'bb_y2': 45},
        {'id': 3, 'timestamp': '2023-10-01 12:10:00', 'person_id': 101, 'embedding': '...', 'file_path': '/path/to/file3', 'camera_id': 'cam1', 'bb_x1': 20, 'bb_y1': 30, 'bb_x2': 40, 'bb_y2': 50},
    ]
    
    calculator = StatisticsCalculator()
    visitor_count = calculator.calculate_visitor_count(example_rows)
    stay_times = calculator.calculate_stay_times(example_rows)
    current_visitors = calculator.calculate_current_visitors(example_rows)
    recent_visitors = calculator.calculate_recent_visitors(example_rows)

    print(f"Visitor Count: {visitor_count}")
    print(f"Stay Times: {stay_times}")
    print(f"Current Visitors: {current_visitors}")
    print(f"Recent Visitors: {recent_visitors}")
    print("Statistics calculation completed.")
"""
