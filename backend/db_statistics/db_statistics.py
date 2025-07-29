from datetime import datetime, timedelta

class StatisticsCalculator:
    def calculate_visitor_count(self, rows):
        """유니크 방문자 수 계산"""
        return len({row[2] for row in rows})

    def calculate_stay_times(self, rows):
        """person_id별 체류 시간(초) 계산"""
        stay_times = {}
        for row in rows:
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

    def calculate_current_visitors(self, rows, window_minutes=1):
        """각 행의 timestamp 기준 window_minutes 이내 체류 인원(중복 없는 person_id 수) 반환"""
        result = {}
        time_person = [(row[0], datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S"), row[2]) for row in rows]
        for row_id, ts, _ in time_person:
            window_start = ts - timedelta(minutes=window_minutes)
            visitors = {pid for _, t, pid in time_person if window_start < t <= ts}
            result[row_id] = len(visitors)
        return result
    
    # 최근 5명 방문자 ID, 이미지 경로 반환
    def calculate_recent_visitors(self, rows, count=5):
        """최근 방문자 ID와 이미지 경로 반환"""
        recent_visitors = sorted(rows, key=lambda x: x[1], reverse=True)[:count]
        return [(row[2], row[3]) for row in recent_visitors]
