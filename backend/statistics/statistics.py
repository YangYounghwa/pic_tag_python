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
                # 이상치 필터 기준 설정 (예시)
        self.min_stay_seconds = 10      # 10초 미만 체류는 이상치
        self.max_stay_seconds = 60*60*8 # 8시간 초과 체류는 이상치

    def filter_outliers(self, statistics):
        """이상치(예: 너무 짧거나 긴 체류, 잘못된 bounding box 등) row를 제외."""
        # 1. 체류 시간 계산
        stay_times = self.calculate_stay_times(statistics)
        filtered = []
        for row in statistics:
            person_id = row[2]
            # 2. 체류 시간이 기준에 맞지 않으면 제외
            stay_time = stay_times.get(person_id, 0)
            if stay_time < self.min_stay_seconds or stay_time > self.max_stay_seconds:
                continue
            # 3. bounding box 좌표가 음수이거나, 너무 크면 제외
            if any(coord is not None and (coord < 0 or coord > 10000) for coord in row[6:10]):
                continue
            # 4. person_id, timestamp, file_path 등 결측값 제외
            if person_id is None or not row[1] or not row[4]:
                continue
            filtered.append(row)
        return filtered

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
    
    # 현재 체류 중인 방문자 수를 계산하는 메소드
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
    
    """"
    get_recent_people(minute,db, timestamp=None) 
    timestamp=None -> 최근 minute 분간 카메라에 보인 인원 계산 (timestamp 기준으로 선정),
    반환값 : 인원수, list[ timestamp, person_id, file_path, bounding_box, camera_id]
    if(timestamp) -> 해당 시간 기준으로 N 분전까지 카메라에 보인 인원 계산
    반환값 : 인원수, list [ timestamp, person_id, boundingbox, file_path, camera_id ]

    get_num_people_left()
    최근 24시간 기준으로 나간 인원수 (get_recent_people(60*24,) - get_recent_people(60,))를 숫자로 반환

    get_id_logs(person_id)
    해당 id가 최근 24시간동안 보인 시간대 표시, 단 3분 주기로 기록, 3분보다 가까운 값들은 삭제
    반환값 : list [ timestamp, cam_num , boundingbox, file_path ]
    """
        
    def get_recent_people(self, minute, statistics, timestamp=None):
        """Get the number of unique visitors in the last 'minute' minutes."""  
        if not self.validate_statistics(statistics):
            return 0, []
        
        if timestamp is None:
            latest_time = max(datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S") for row in statistics)
        else:
            latest_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        
        start_time = latest_time - timedelta(minutes=minute)
        
        recent_people = [
            (row[1], row[2], row[4], (row[6], row[7], row[8], row[9]), row[5])
            for row in statistics
            if start_time <= datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S") <= latest_time
        ]
        
        unique_person_ids = {row[1] for row in recent_people}
        return len(unique_person_ids), recent_people

    def get_num_people_left(self, statistics):
        """Get the number of people who have left in the last 24 hours."""
        if not self.validate_statistics(statistics):
            return 0
        
        latest_time = max(datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S") for row in statistics)
        one_day_ago = latest_time - timedelta(days=1)
        
        # 최근 24시간 동안의 방문자 아이디 집합
        recent_visitors = {
            row[2]
            for row in statistics
            if one_day_ago < datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S") <= latest_time
        }
        
        # 현재 체류 중인 방문자 아이디 집합
        current_visitors = {
            row[2]
            for row in statistics
            if datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S") > one_day_ago
        }
        
        # 나간 인원 수 계산
        return len(recent_visitors - current_visitors)
    
    def get_id_logs(self, person_id, statistics):
        """Get logs for a specific person_id in the last 24 hours."""
        if not self.validate_statistics(statistics):
            return []
        
        latest_time = max(datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S") for row in statistics)
        one_day_ago = latest_time - timedelta(days=1)
        
        id_logs = [
            (row[1], row[5], (row[6], row[7], row[8], row[9]), row[4])
            for row in statistics
            if row[2] == person_id and one_day_ago < datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S") <= latest_time
        ]
        
        # 3분 주기로 기록된 로그만 반환
        filtered_logs = []
        last_timestamp = None
        for log in id_logs:
            timestamp = datetime.strptime(log[0], "%Y-%m-%d %H:%M:%S")
            if last_timestamp is None or (timestamp - last_timestamp).total_seconds() >= 180:
                filtered_logs.append(log)
                last_timestamp = timestamp
        
        return filtered_logs

    # # 최근 5명의 방문자 아이디를 반환하는 메소드
    # def get_recent_visitors(self, statistics, limit=5):
    #     """Get the most recent visitor IDs based on the latest timestamps."""
    #     if not self.validate_statistics(statistics):
    #         return []
    #     if not statistics:
    #         return []
        
    #     # 데이터 내 가장 최근 timestamp 찾기
    #     latest_time = max(datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S") for row in statistics)
    #     one_minute_ago = latest_time - timedelta(minutes=1)
        
    #     # 1분 이내에 기록된 person_id 집합
    #     recent_visitors = {
    #         row[2]
    #         for row in statistics
    #         if one_minute_ago < datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S") <= latest_time
    #     }
        
    #     # 최근 방문자 아이디를 리스트로 변환하고 정렬
    #     return sorted(recent_visitors, reverse=True)[:limit]
    
    # # 선택한 방문자 아이디의 저장된 이미지 주소를 반환하는 메소드
    # def get_visitor_images(self, person_id):
    #     """Get file paths of images for a specific visitor by person_id."""
    #     try:
    #         cursor = self.db_connection.cursor()
    #         cursor.execute(
    #             "SELECT file_path FROM identity_log WHERE person_id = ?",
    #             (person_id,)
    #         )
    #         rows = cursor.fetchall()
    #         cursor.close()
    #         return [row[0] for row in rows]
    #     except sqlite3.Error as e:
    #         print(f"Database error: {e}")
    #         return []

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
    rows = stats.filter_outliers(rows)  # 이상치 제거
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
    

    # 추가된 기능들에 대한 테스트
    recent_visitors = stats.get_recent_visitors(rows, limit=5)
    assert len(recent_visitors) <= 5, f"Expected at most 5 recent visitors, but got {len(recent_visitors)}"

    visitor_images = stats.get_visitor_images(1)  # person_id 1에 대한 이미지 경로 조회
    assert len(visitor_images) > 0, "Expected to find images for person_id 0"
    print(f"Visitor images for person_id 1: {visitor_images}")

    # 최근 방문자 수 계산
    recent_count, recent_people = stats.get_recent_people(60, rows)
    assert recent_count > 0, "Expected to find recent visitors"
    print(f"Recent visitors in the last 60 minutes: {recent_count}")

    # 최근 24시간 동안 나간 인원 수 계산
    num_left = stats.get_num_people_left(rows)
    assert num_left >= 0, f"Expected non-negative number of people left, but got {num_left}"
    print(f"Number of people who have left in the last 24 hours: {num_left}")

    # 특정 person_id의 로그 조회
    id_logs = stats.get_id_logs(1, rows)
    assert len(id_logs) > 0, "Expected to find logs for person_id 1"
    print(f"Logs for person_id 1: {id_logs}")

    # 최근 5명의 방문자 아이디 조회
    recent_visitors = stats.get_recent_visitors(rows, limit=5)
    assert len(recent_visitors) <= 5, f"Expected at most 5 recent visitors, but got {len(recent_visitors)}"
    print(f"Recent visitors: {recent_visitors}")

    # 선택한 방문자 아이디의 저장된 이미지 주소 조회
    visitor_images = stats.get_visitor_images(1)
    assert len(visitor_images) > 0, "Expected to find images for person_id 1"
    print(f"Visitor images for person_id 1: {visitor_images}")  

    # 데이터베이스 연결 종료
    print(f"All tests passed! Database: {db_path}, CSV: {output_path}")
    stats.close_connection()

    
if __name__ == "__main__":
    test_statistics_from_db()

