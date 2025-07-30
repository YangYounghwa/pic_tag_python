import sqlite3
import os
import base64
from datetime import datetime, timedelta
from collections import Counter
from typing import List, Dict, Any, Tuple

class IdentityAnalytics:
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_person_images_by_id(self, person_id: int) -> List[Dict[str, Any]]:
        """
        person_id에 해당하는 이미지 파일들을 조회해서 base64로 반환
        """
        conn = self._get_connection()
        
        # 해당 person_id의 이미지 파일 경로들 조회
        query = """
        SELECT file_path, timestamp, camera_id, bb_x1, bb_y1, bb_x2, bb_y2
        FROM identity_log 
        WHERE person_id = ? AND file_path IS NOT NULL
        ORDER BY timestamp DESC
        LIMIT 10
        """
        
        cursor = conn.execute(query, (person_id,))
        rows = cursor.fetchall()
        
        images = []
        for row in rows:
            file_path = row['file_path']
            
            # jpg 또는 png 파일만 처리
            if file_path and (file_path.lower().endswith('.jpg') or file_path.lower().endswith('.png')):
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'rb') as img_file:
                            img_data = base64.b64encode(img_file.read()).decode('utf-8')
                        
                        images.append({
                            'filename': os.path.basename(file_path),
                            'data': img_data,
                            'timestamp': row['timestamp'],
                            'camera_id': row['camera_id'],
                            'bounding_box': {
                                'x1': row['bb_x1'],
                                'y1': row['bb_y1'],
                                'x2': row['bb_x2'],
                                'y2': row['bb_y2']
                            },
                            'type': 'image/jpeg' if file_path.lower().endswith('.jpg') else 'image/png'
                        })
                    except Exception as e:
                        print(f"이미지 로드 실패: {file_path}, {e}")
                        continue
        
        conn.close()
        return images
    
    def get_recent_people(self, minute: int, timestamp: str = None) -> Tuple[int, List[Dict[str, Any]]]:
        """
        최근 N분간 카메라에 보인 인원 계산
        """
        conn = self._get_connection()
        
        if timestamp is None:
            end_time = datetime.now()
        else:
            end_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        start_time = end_time - timedelta(minutes=minute)
        
        query = """
        SELECT timestamp, person_id, file_path, camera_id, bb_x1, bb_y1, bb_x2, bb_y2
        FROM identity_log 
        WHERE timestamp BETWEEN ? AND ?
        ORDER BY timestamp DESC
        """
        
        cursor = conn.execute(query, (start_time.isoformat(), end_time.isoformat()))
        rows = cursor.fetchall()
        
        # 빈도가 낮은 person_id 필터링 (3회 미만 등장하는 경우 제외)
        person_counter = Counter(row['person_id'] for row in rows)
        valid_person_ids = {pid for pid, count in person_counter.items() if count >= 3}
        
        filtered_results = []
        unique_person_ids = set()
        
        for row in rows:
            if row['person_id'] in valid_person_ids:
                unique_person_ids.add(row['person_id'])
                bounding_box = {
                    'x1': row['bb_x1'],
                    'y1': row['bb_y1'], 
                    'x2': row['bb_x2'],
                    'y2': row['bb_y2']
                }
                
                filtered_results.append({
                    'timestamp': row['timestamp'],
                    'person_id': row['person_id'],
                    'file_path': row['file_path'],
                    'bounding_box': bounding_box,
                    'camera_id': row['camera_id']
                })
        
        conn.close()
        return len(unique_person_ids), filtered_results
    
    def get_num_people_left(self) -> int:
        """
        최근 24시간 기준으로 나간 인원수
        (24시간 전체 인원 - 최근 1시간 인원)
        """
        people_24h, _ = self.get_recent_people(60 * 24)
        people_1h, _ = self.get_recent_people(60)
        
        return max(0, people_24h - people_1h)
    
    def get_id_logs(self, person_id: int) -> List[Dict[str, Any]]:
        """
        해당 ID가 최근 24시간동안 보인 시간대 표시 (3분 주기로 기록)
        3분보다 가까운 값들은 삭제
        """
        conn = self._get_connection()
        
        # 최근 24시간
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        query = """
        SELECT timestamp, camera_id, file_path, bb_x1, bb_y1, bb_x2, bb_y2
        FROM identity_log 
        WHERE person_id = ? AND timestamp BETWEEN ? AND ?
        ORDER BY timestamp ASC
        """
        
        cursor = conn.execute(query, (person_id, start_time.isoformat(), end_time.isoformat()))
        rows = cursor.fetchall()
        
        # 3분 간격으로 필터링
        filtered_results = []
        last_timestamp = None
        
        for row in rows:
            current_timestamp = datetime.fromisoformat(row['timestamp'])
            
            if last_timestamp is None or (current_timestamp - last_timestamp).total_seconds() >= 180:  # 3분 = 180초
                bounding_box = {
                    'x1': row['bb_x1'],
                    'y1': row['bb_y1'],
                    'x2': row['bb_x2'], 
                    'y2': row['bb_y2']
                }
                
                filtered_results.append({
                    'timestamp': row['timestamp'],
                    'cam_num': row['camera_id'],
                    'boundingbox': bounding_box,
                    'file_path': row['file_path']
                })
                
                last_timestamp = current_timestamp
        
        conn.close()
        return filtered_results
