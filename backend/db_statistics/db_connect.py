# backend/db_statistics/db_connect.py

import sqlite3
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self):
        """identity_log 테이블 생성 (없으면)."""
        query = """
        CREATE TABLE IF NOT EXISTS identity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            person_id INTEGER,
            embedding TEXT,
            file_path TEXT,
            camera_id INTEGER,
            bb_x1 INTEGER,
            bb_y1 INTEGER,
            bb_x2 INTEGER,
            bb_y2 INTEGER
        )
        """
        self.conn.execute(query)
        self.conn.commit()

    def clear_table(self):
        """테이블 비우기."""
        self.conn.execute("DELETE FROM identity_log")
        self.conn.commit()

    def insert_dummy_data(self, rows):
        """더미 데이터 삽입 (rows: list of tuple)."""
        query = """
        INSERT INTO identity_log (timestamp, person_id, embedding, file_path, camera_id, bb_x1, bb_y1, bb_x2, bb_y2)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.executemany(query, rows)
        self.conn.commit()

    def fetch_statistics(self, start_time=None, end_time=None):
        """통계 데이터 조회."""
        query = "SELECT * FROM identity_log"
        params = []
        if start_time and end_time:
            query += " WHERE timestamp BETWEEN ? AND ?"
            params = [start_time, end_time]
        elif start_time:
            query += " WHERE timestamp >= ?"
            params = [start_time]
        elif end_time:
            query += " WHERE timestamp <= ?"
            params = [end_time]
        cursor = self.conn.execute(query, params)
        return [tuple(row) for row in cursor.fetchall()]

    def close(self):
        self.conn.close()
