from datetime import datetime, timedelta

def generate_dummy_rows(num_entries=100):
    """더미 데이터 row 리스트 반환 (DB insert용)"""
    base_time = datetime(2023, 10, 1, 12, 0, 0)
    entries_per_person = num_entries // 10
    rows = []
    for person_id in range(10):
        stay_duration = (person_id + 1) * 10
        for i in range(entries_per_person):
            minutes_offset = (
                i * (stay_duration / (entries_per_person - 1))
                if entries_per_person > 1
                else 0
            )
            timestamp = (base_time + timedelta(minutes=minutes_offset)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            rows.append((
                timestamp,
                person_id,
                f"embedding_{person_id}_{i}",
                f"/path/to/image_{person_id}_{i}.jpg",
                person_id % 5,
                i * 10,
                i * 15,
                i * 20 + 50,
                i * 25 + 50,
            ))
    return rows