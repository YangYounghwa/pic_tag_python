import sqlite3
import os

class IdentityLogger:
    def __init__(self, db_path=".\\..\\..\\data\\db\\identity_log.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        with self.conn:
            self.conn.execute('''
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
            ''')

    def log(self, timestamp, person_id, embedding, bounding_box, file_path, camera_id):
        emb_str = ",".join(f"{x:.6f}" for x in embedding.tolist())
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Format timestamp to string
        bounding_box = bounding_box if bounding_box else (0, 0, 0, 0)
        camera_id = camera_id if camera_id is not None else 0  # Default to
        with self.conn:
            self.conn.execute(
                "INSERT INTO identity_log (timestamp, person_id, embedding, file_path, camera_id, bb_x1, bb_y1, bb_x2, bb_y2) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (timestamp_str, person_id, emb_str, file_path, camera_id, *bounding_box)
            )

    def close(self):
        self.conn.close()