# backend/db_statistics/db_preprocess.py

class DataPreprocessor:
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

    def validate(self, rows):
        """행 단위 데이터 유효성 검사."""
        if not rows:
            return False
        for row in rows:
            if len(row) < 9:
                return False
            if not isinstance(row["id"], int) or not isinstance(row["timestamp"], str):
                return False
            if not isinstance(row["person_id"], int) or not isinstance(
                row["embedding"], str
            ):
                return False
            if not isinstance(row["file_path"], str) or not isinstance(
                row["camera_id"], str
            ):
                return False
            if not isinstance(row["bb_x1"], int) or not isinstance(row["bb_y1"], int):
                return False
            if not isinstance(row["bb_x2"], int) or not isinstance(row["bb_y2"], int):
                return False
        print("All rows validated successfully.")
        return True

    def filter_row_outliers(self, rows):
        """행 단위로 바로 판단 가능한 이상치(결측, 타입, bounding box 등)만 제거."""
        filtered = []
        for row in rows:
            # 결측값
            if row["person_id"] is None or not row["timestamp"] or not row["file_path"]:
                continue
            # bounding box 좌표가 음수이거나 너무 크면 제외
            if any(
                coord is not None and (coord < 0 or coord > 10000)
                for coord in [row["bb_x1"], row["bb_y1"], row["bb_x2"], row["bb_y2"]]
            ):
                continue
            # 타입 검사
            if not isinstance(row["id"], int) or not isinstance(row["person_id"], int):
                continue
            filtered.append(row)
        print(f"Filtered outliers: {len(filtered)} rows remain.")
        return filtered


"""
# test code: 테스트 용 예시 데이터를 생성하여, 유효성 검사 및 이상치 제거 메서드 테스트

if __name__ == "__main__":
    example_rows = [
        {'id': 1, 'timestamp': '2023-10-01 12:00:00', 'person_id': 101, 'embedding': '...', 'file_path': '/path/to/file1', 'camera_id': 'cam1', 'bb_x1': 10, 'bb_y1': 20, 'bb_x2': 30, 'bb_y2': 40},
        {'id': 2, 'timestamp': '2023-10-01 12:05:00', 'person_id': 102, 'embedding': '...', 'file_path': '/path/to/file2', 'camera_id': 'cam1', 'bb_x1': 15, 'bb_y1': 25, 'bb_x2': 35, 'bb_y2': 45},
        {'id': 3, 'timestamp': None, 'person_id': None, 'embedding': '', 'file_path': '/path/to/file3', 'camera_id': '', 'bb_x1': -5, 'bb_y1': 30, 'bb_x2': 40, 'bb_y2': 50}, # 이상치
    ]
    
    preprocessor = DataPreprocessor()
    valid_rows = preprocessor.validate(example_rows)
    print(f"Validation result: {valid_rows}")
    
    filtered_rows = preprocessor.filter_row_outliers(example_rows)
    print(f"Filtered rows: {filtered_rows}")
    print(f"All tests completed.")
"""
