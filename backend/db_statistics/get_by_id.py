# backend/db_statistics/get_by_id.py

from .db_connect import DatabaseManager
from .db_preprocess import DataPreprocessor
from .db_statistics import StatisticsCalculator
from .db_postprocess import StatisticsPostprocessor
from datetime import datetime
import os
import base64


def get_info_by_id(db_path, person_id):
    """
    특정 person_id에 대한 체류 시간과 행동 리스트를 반환.

    Args:
        db_path (str): 데이터베이스 파일 경로
        person_id (int): 조회할 person_id

    Returns:
        dict: {"recent_actions": [{"cam_num": str, "timestamp": str, "bounding_box": [int, int, int, int]}], "stay_time": float}
              행동 리스트는 최소 3분 간격으로 필터링됨.
    """
    # 1. DB 연결
    db = DatabaseManager(db_path)

    # 2. 데이터 조회
    query = "SELECT * FROM identity_log WHERE person_id = ?"
    cursor = db.conn.execute(query, (person_id,))
    rows = [dict(row) for row in cursor.fetchall()]

    # 3. 데이터 전처리
    pre = DataPreprocessor()
    if not pre.validate(rows):
        db.close()
        return {"recent_actions": [], "stay_time": 0.0}

    rows = pre.filter_row_outliers(rows)
    if not rows:
        db.close()
        return {"recent_actions": [], "stay_time": 0.0}

    # 4. 체류 시간 계산
    calc = StatisticsCalculator()
    stay_times = calc.calculate_stay_times(rows)
    stay_time = stay_times.get(person_id, 0.0)

    # 5. 후처리: 체류 시간 기준 필터링
    post = StatisticsPostprocessor()
    filtered_rows = post.filter_by_stay_time(
        rows, stay_times, min_seconds=30, max_seconds=3600
    )
    filtered_rows = post.filter_by_min_visits(filtered_rows, min_visits=1)

    # 6. 행동 리스트 생성 (최소 3분 간격)
    recent_actions = []
    last_timestamp = None
    for row in sorted(filtered_rows, key=lambda x: x["timestamp"], reverse=True):
        current_ts = datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S")
        if (
            last_timestamp is None
            or (last_timestamp - current_ts).total_seconds() >= 180
        ):
            recent_actions.append(
                {
                    "cam_num": row["camera_id"],
                    "timestamp": row["timestamp"],
                    "bounding_box": [
                        row["bb_x1"],
                        row["bb_y1"],
                        row["bb_x2"],
                        row["bb_y2"],
                    ],
                }
            )
            last_timestamp = current_ts

    # 7. DB 연결 종료
    db.close()

    return {"recent_actions": recent_actions, "stay_time": stay_time}


def get_person_images_by_id(db_path, person_id): 
    """
    person_id에 해당하는 이미지 파일들을 조회해서 base64로 반환
    """
    
    from .db_connect import DatabaseManager
    
    db = DatabaseManager(db_path)
    
    #해당 person_id의 이미지 파일 경로들 조회
    query = """
    SELECT file_path, timestamp, camera_id
    FROM identity_log
    WHERE person_id = ? AND file_path IS NOT NULL
    ORDER BY timestamp DESC
    LIMIT 10
    """
    
    cursor = db.conn.execute(query, (person_id,))
    rows = cursor.fetchall()
    
    images = []
    for row in rows:
        file_path = row[0]
        timestamp = row[1]
        camera_id = row[2]

        if file_path and (file_path.endswith('.jpg') or file_path.endswith('.png')):
            if os.path.exists(file_path):
                try: 
                    with open(file_path, "rb") as img_file:
                        img_data = base64.b64encode(img_file.read()).decode('utf-8')
                        
                    images.append({
                        'filename': os.path.basename(file_path),
                        'data': img_data,
                        'timestamp': row[1],
                        'camera_id': row[2],
                        'type': 'image/jpeg' if file_path.endswith('.jpg') else 'image/png'
                    })
                    
                except:
                    continue # 파일 읽기 실패하면 건너뛰기
                
    return images
