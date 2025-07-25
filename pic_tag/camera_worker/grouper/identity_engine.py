import time
import threading
import numpy as np
from queue import Queue, Empty
from collections import defaultdict, deque
from sklearn.metrics.pairwise import cosine_similarity


class IdentityEngine(threading.Thread):
    def __init__(self, shared_queue: Queue, logger=None,
                 sim_threshold=0.2, max_history=20000, max_age_sec=86400):
        super().__init__()
        self.queue = shared_queue
        self.logger = logger
        self.sim_threshold = sim_threshold
        self.max_history = max_history
        self.max_age_sec = max_age_sec

        self.recent_data = deque()  # (timestamp, embedding, person_id)
        self.person_counter = 0
        self.lock = threading.Lock()
        self.running = True
        
        # feature_data = {
        #     "features": features,
        #     "bounding_box": box,
        #     "timeStamp": timestamp,
        #     "camera_id": cam_id,
        #     "img_name": img_name
        # }
        # feature_queue.put(feature_data)

    def run(self):
        while self.running:
            try:
                feature_data = self.queue.get(timeout=0.1)  # Adjust timeout as needed
                if not feature_data:
                    continue
                
                # Debug line
                # print(f"[{time.strftime('%H:%M:%S')}] Processing feature data: {feature_data}" )
                embedding = feature_data["features"]
                timestamp = feature_data["timeStamp"]
                bounding_box = feature_data["bounding_box"]
                file_path = feature_data["img_name"]
                camera_id = feature_data["camera_id"]  
                embedding = np.array(embedding, dtype=np.float32)
                if embedding.ndim == 1: 
                    embedding = embedding.reshape(1, -1)
                if embedding.shape[0] > 1:
                    embedding = embedding.mean(axis=0, keepdims=True)
                embedding = embedding.flatten()
                if embedding.size == 0:
                    print(f"[{time.strftime('%H:%M:%S')}] Empty embedding received, skipping.")
                    self.queue.task_done()
                    continue 
                person_id = self._assign_identity(timestamp, embedding, bounding_box, file_path, camera_id)
                # print(f"[{time.strftime('%H:%M:%S')}] Assigned ID {person_id}")
                self.queue.task_done()
            except Empty:
                time.sleep(0.1)  # Sleep briefly to avoid busy waiting
                continue

    def stop(self):
        self.running = False

    def _assign_identity(self, timestamp, embedding: np.ndarray, bounding_box, file_path, camera_id = None):
        embedding = embedding.astype(np.float32)
        with self.lock:
            self._clean_old_entries(timestamp)
            if not self.recent_data:
                pid = self._create_new_identity(embedding, timestamp)
                return pid

            embs = np.stack([e for _, e, _ in self.recent_data])
            embs = embs / np.linalg.norm(embs, axis=1, keepdims=True)
            emb = embedding / np.linalg.norm(embedding)

            sims = embs @ emb  # cosine similarity
            best_idx = int(np.argmax(sims))
            best_sim = float(sims[best_idx])
            best_pid = self.recent_data[best_idx][2]

            if best_sim >= self.sim_threshold:
                self.recent_data.append((timestamp, embedding, best_pid))
                if len(self.recent_data) > self.max_history:
                    self.recent_data.popleft()
                if self.logger:
                # "INSERT INTO identity_log (timestamp, person_id, embedding, file_path, camera_id, bb_x1, bb_y1, bb_x2, bb_y2) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                # (timestamp, person_id, emb_str, file_path, camera_id, *bounding_box)
                    self.logger.log(timestamp, best_pid, embedding, bounding_box, file_path, camera_id)
                # log(self, timestamp, person_id, embedding, bounding_box, file_path, camera_id)
                return best_pid
            else:
                return self._create_new_identity(embedding, timestamp)

    def _create_new_identity(self, embedding, timestamp):
        self.person_counter += 1
        pid = self.person_counter
        self.recent_data.append((timestamp, embedding, pid))
        if len(self.recent_data) > self.max_history:
            self.recent_data.popleft()
        if self.logger:
            self.logger.log(timestamp, pid, embedding)
        return pid

    def _clean_old_entries(self, current_time):
        while self.recent_data and current_time - self.recent_data[0][0] > self.max_age_sec:
            self.recent_data.popleft()