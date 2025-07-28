import time
import threading
import numpy as np
from queue import Queue, Empty
from collections import defaultdict, deque
from sklearn.metrics.pairwise import cosine_similarity

class IdentityEnginev2(threading.Thread):
    def __init__(self, shared_queue: Queue, logger=None,
                 sim_threshold=0.7, max_history=20000, max_age_sec=86400, max_embeddings_per_id=100):
        super().__init__()
        self.queue = shared_queue
        self.logger = logger
        self.sim_threshold = sim_threshold
        self.max_age_sec = max_age_sec
        self.max_embeddings_per_id = max_embeddings_per_id
        self.person_counter = 0
        self.lock = threading.Lock()
        self.identity_db = defaultdict(deque)  # person_id → deque[(timestamp, embedding)]
        self.daemon = True  # Allow thread to be killed with main

    def run(self, stop_event=None):
        stop_event = stop_event or threading.Event()
        while not stop_event.is_set():
            try:
                feature_data = self.queue.get(timeout=0.5)
            except Empty:
                continue

            try:
                if not feature_data:
                    continue

                embedding = self._preprocess_embedding(feature_data["features"])
                if embedding is None:
                    print(f"[{time.strftime('%H:%M:%S')}] Empty or bad embedding received, skipping.")
                    continue

                timestamp = feature_data["timestamp"]
                bbox = (
                    feature_data["bb_x1"],
                    feature_data["bb_y1"],
                    feature_data["bb_x2"],
                    feature_data["bb_y2"]
                )
                file_path = feature_data["file_path"]
                camera_id = feature_data["camera_id"]

                self._assign_identity(timestamp, embedding, bbox, file_path, camera_id)

            finally:
                self.queue.task_done()  # only called after a successful get()
    def _preprocess_embedding(self, emb_raw):
        emb = np.array(emb_raw, dtype=np.float32).flatten()
        if emb.size == 0:
            return None
        norm = np.linalg.norm(emb)
        if norm == 0:
            return None
        return emb / norm

    def _assign_identity(self, timestamp, embedding, bounding_box, file_path, camera_id=None):
        with self.lock:
            self._clean_old_entries(timestamp)

            if not self.identity_db:
                return self._create_new_identity(embedding, timestamp, bounding_box, file_path, camera_id)

            centroids, pids = [], []
            for pid, entries in self.identity_db.items():
                embs = np.stack([e for ts, e in entries])
                centroid = embs.mean(axis=0)
                centroid /= np.linalg.norm(centroid)
                centroids.append(centroid)
                pids.append(pid)

            centroids = np.stack(centroids)
            sims = centroids @ embedding
            best_idx = int(np.argmax(sims))
            best_sim = float(sims[best_idx])
            best_pid = pids[best_idx]

            if best_sim >= self.sim_threshold:
                self._append_embedding(best_pid, timestamp, embedding)
                if self.logger:
                    self.logger.log(timestamp, best_pid, embedding, bounding_box, file_path, camera_id)
                return best_pid
            else:
                return self._create_new_identity(embedding, timestamp, bounding_box, file_path, camera_id)

    def _append_embedding(self, pid, timestamp, embedding):
        if len(self.identity_db[pid]) >= self.max_embeddings_per_id:
            self.identity_db[pid].popleft()
        self.identity_db[pid].append((timestamp, embedding))

    def _create_new_identity(self, embedding, timestamp, bounding_box, file_path, camera_id=None):
        self.person_counter += 1
        pid = self.person_counter
        self.identity_db[pid].append((timestamp, embedding))
        if self.logger:
            self.logger.log(timestamp, pid, embedding, bounding_box, file_path, camera_id)
        return pid

    def _clean_old_entries(self, current_time):
        for pid in list(self.identity_db.keys()):
            self.identity_db[pid] = deque([
                (ts, emb) for ts, emb in self.identity_db[pid]
                if (current_time - ts).total_seconds() <= self.max_age_sec
            ])
            if not self.identity_db[pid]:
                del self.identity_db[pid]