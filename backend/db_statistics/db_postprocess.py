class StatisticsPostprocessor:
    def filter_by_stay_time(self, rows, stay_times, min_seconds=10, max_seconds=60*60*8):
        """
        집계된 체류 시간(stay_times) 기준으로 person_id를 필터링하여
        해당 기준에 맞는 row만 반환합니다.
        """
        valid_person_ids = {pid for pid, t in stay_times.items() if min_seconds <= t <= max_seconds}
        filtered = [row for row in rows if row[2] in valid_person_ids]
        return filtered

    def filter_by_min_visits(self, rows, min_visits=2):
        """
        최소 방문 횟수(min_visits) 미만인 person_id의 row를 제외합니다.
        """
        from collections import Counter
        visit_counts = Counter(row[2] for row in rows)
        valid_person_ids = {pid for pid, cnt in visit_counts.items() if cnt >= min_visits}
        filtered = [row for row in rows if row[2] in valid_person_ids]
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
        return [row for row in rows if in_range(row[1])]