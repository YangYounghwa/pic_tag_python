import sqlite3
import os
import threading
import queue
import time
from datetime import datetime

class IdentityLogger(threading.Thread):
    def __init__(self, db_path="./../../data/db/identity_log.db", flush_interval=0.2, max_buffer_size=50):
        super().__init__()
        self.db_path = db_path
        self.flush_interval = flush_interval
        self.max_buffer_size = max_buffer_size
        self.log_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.daemon = True

        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
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
                    camera_id TEXT,
                    bb_x1 INTEGER,
                    bb_y1 INTEGER,
                    bb_x2 INTEGER,
                    bb_y2 INTEGER
                )
            ''')

    def run(self):
        
        
        buffer = []

                    
        last_flush_time = time.time()

        while not self.stop_event.is_set() or not self.log_queue.empty():
            now = time.time()
            try:
                log_item = self.log_queue.get(timeout=self.flush_interval)
                buffer.append(log_item)
            except queue.Empty:
                pass  # still flush on time even if queue is empty

            if buffer and (now - last_flush_time >= self.flush_interval):
                self._flush(buffer)
                buffer.clear()
                last_flush_time = now

    def log(self, timestamp, person_id, embedding, bounding_box, file_path, camera_id):
        emb_str = ",".join(f"{x:.6f}" for x in embedding.tolist())
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        bb = bounding_box if bounding_box else (0, 0, 0, 0)
        log_item = (timestamp_str, person_id, emb_str, file_path, camera_id or "", *bb)
        self.log_queue.put(log_item)

    def _flush(self, items):
        with self.conn:
            self.conn.executemany(
                '''
                INSERT INTO identity_log (
                    timestamp, person_id, embedding, file_path, camera_id, bb_x1, bb_y1, bb_x2, bb_y2
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                items
            )

    def close(self):
        self.stop_event.set()
        self.join()  # Wait for logger thread to finish
        self.conn.close()
