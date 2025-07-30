# backend/db_statistics/db_postprocess.py

class StatisticsPostprocessor:
    def filter_by_stay_time(
        self, rows, stay_times, min_seconds=10, max_seconds=60 * 60 * 8
    ):
        """
        집계된 체류 시간(stay_times) 기준으로 person_id를 필터링하여
        해당 기준에 맞는 row만 반환합니다.
        """
        valid_person_ids = {
            pid for pid, t in stay_times.items() if min_seconds <= t <= max_seconds
        }
        filtered = [row for row in rows if row["person_id"] in valid_person_ids]
        print(f"Filtered by stay time: {len(filtered)} rows remain.")
        return filtered

    def filter_by_min_visits(self, rows, min_visits=2):
        """
        최소 방문 횟수(min_visits) 미만인 person_id의 row를 제외합니다.
        """
        from collections import Counter

        visit_counts = Counter(row["person_id"] for row in rows)
        valid_person_ids = {
            pid for pid, cnt in visit_counts.items() if cnt >= min_visits
        }
        filtered = [row for row in rows if row["person_id"] in valid_person_ids]
        print(f"Filtered by min visits: {len(filtered)} rows remain.")
        return filtered

    def filter_by_time_range(self, rows, start_time=None, end_time=None):
        """
        특정 시간 범위(start_time ~ end_time)에 해당하는 row만 반환합니다.
        시간 포맷: "YYYY-MM-DD HH:MM:SS"
        """
        from datetime import datetime

        def in_range(ts):
            dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            if start_time and dt < datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S"):
                return False
            if end_time and dt > datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S"):
                return False
            return True

        filtered = [row for row in rows if in_range(row["timestamp"])]
        print(f"Filtered by time range: {len(filtered)} rows remain.")
        return filtered


"""
test code: 주석 부분은 테스트용 예시 데이터를 생성하여, 필터링 메서드를 테스트합니다.

# 테스트 용 예시 데이터를 생성하여, 필터링 메서드 테스트
if __name__ == "__main__":
    example_rows = [
        {'id': 1, 'timestamp': '2023-10-01 12:00:00', 'person_id': 101, 'embedding': '...', 'file_path': '/path/to/file1', 'camera_id': 1, 'bb_x1': 10, 'bb_y1': 20, 'bb_x2': 30, 'bb_y2': 40},
        {'id': 2, 'timestamp': '2023-10-01 12:05:00', 'person_id': 102, 'embedding': '...', 'file_path': '/path/to/file2', 'camera_id': 1, 'bb_x1': 15, 'bb_y1': 25, 'bb_x2': 35, 'bb_y2': 45},
        {'id': 3, 'timestamp': '2023-10-01 12:10:00', 'person_id': 101, 'embedding': '...', 'file_path': '/path/to/file3', 'camera_id': 1, 'bb_x1': 20, 'bb_y1': 30, 'bb_x2': 40, 'bb_y2': 50},
    ]
    
    example_stay_times = {101: 15, 102: 5} # person_id: stay_time in seconds

    processor = StatisticsPostprocessor()
    filtered_by_stay_time = processor.filter_by_stay_time(example_rows, example_stay_times)
    filtered_by_min_visits = processor.filter_by_min_visits(filtered_by_stay_time)
    filtered_by_time_range = processor.filter_by_time_range(filtered_by_min_visits, start_time='2023-10-01 12:00:00', end_time='2023-10-01 12:10:00')

"""
