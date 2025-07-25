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
        self.max_age_sec = max_age_sec
        self.person_counter = 0
        self.lock = threading.Lock()
        self.running = True

        # New structure: person_id → list of (timestamp, embedding)
        self.identity_db = defaultdict(list)

    def run(self):
        while self.running:
            try:
                feature_data = self.queue.get(timeout=0.1)
                if not feature_data:
                    print("No more feature data to process, sleeping for a while...")
                    time.sleep(0.25)
                    continue

                # Extract data
                embedding = feature_data["features"]
                timestamp = feature_data["timestamp"]
                x1 = feature_data["bb_x1"]
                y1 = feature_data["bb_y1"]
                x2 = feature_data["bb_x2"]
                y2 = feature_data["bb_y2"]
                bounding_box = (x1, y1, x2, y2)
                file_path = feature_data["file_path"]
                camera_id = feature_data["camera_id"]

                # Preprocess embedding
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

                # Assign ID
                person_id = self._assign_identity(
                    timestamp, embedding, bounding_box, file_path, camera_id
                )

                self.queue.task_done()

            except Empty:
                time.sleep(0.1)
                continue

    def stop(self):
        self.running = False

    def _assign_identity(self, timestamp, embedding: np.ndarray, bounding_box, file_path, camera_id=None):
        embedding = embedding.astype(np.float32)
        embedding = embedding / np.linalg.norm(embedding)

        with self.lock:
            self._clean_old_entries(timestamp)

            if not self.identity_db:
                return self._create_new_identity(embedding, timestamp, bounding_box, file_path, camera_id)

            centroids = []
            pids = []
            for pid, entries in self.identity_db.items():
                embs = np.stack([e for ts, e in entries])
                centroid = np.mean(embs, axis=0)
                centroid /= np.linalg.norm(centroid)
                centroids.append(centroid)
                pids.append(pid)

            centroids = np.stack(centroids)
            sims = centroids @ embedding
            best_idx = int(np.argmax(sims))
            best_sim = float(sims[best_idx])
            best_pid = pids[best_idx]

            if best_sim >= self.sim_threshold:
                self.identity_db[best_pid].append((timestamp, embedding))
                if self.logger:
                    self.logger.log(timestamp, best_pid, embedding, bounding_box, file_path, camera_id)
                return best_pid
            else:
                return self._create_new_identity(embedding, timestamp, bounding_box, file_path, camera_id)

    def _create_new_identity(self, embedding, timestamp, bounding_box, file_path, camera_id=None):
        self.person_counter += 1
        pid = self.person_counter
        self.identity_db[pid].append((timestamp, embedding))
        if self.logger:
            self.logger.log(timestamp, pid, embedding, bounding_box, file_path, camera_id)
        return pid

    def _clean_old_entries(self, current_time):
        for pid in list(self.identity_db.keys()):
            self.identity_db[pid] = [
            (ts, emb) for ts, emb in self.identity_db[pid]
            if (current_time - ts).total_seconds() <= self.max_age_sec
        ]
            if not self.identity_db[pid]:
                del self.identity_db[pid]