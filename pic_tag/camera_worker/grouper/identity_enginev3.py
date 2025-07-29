import threading
from queue import Queue, Empty
from collections import defaultdict, deque
import numpy as np
import time


class IdentityEngine(threading.Thread):
    def __init__(self, shared_queue: Queue, logger=None,
                 sim_threshold=0.7, max_age_sec=86400,
                 max_prototypes=3, spatial_bias=0.10,
                 spatial_window_size=50, spatial_distance_thresh=50,max_history=20000):
        super().__init__()
        self.queue = shared_queue
        self.logger = logger
        self.sim_threshold = sim_threshold
        self.max_age_sec = max_age_sec
        self.max_prototypes = max_prototypes
        self.spatial_bias = spatial_bias
        self.spatial_window_size = spatial_window_size
        self.spatial_distance_thresh = spatial_distance_thresh
        self.max_history = max_history
        self.person_counter = 0
        self.lock = threading.Lock()

        # Core structures
        self.embedding_history = defaultdict(deque)       # pid → deque[(timestamp, embedding)]
        self.prototype_db = defaultdict(list)             # pid → [embedding1, embedding2, ...]
        self.recent_detections = defaultdict(deque)       # camera_id → deque[(timestamp, pid, bbox)]

        self.daemon = True

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
                    print(f"[{time.strftime('%H:%M:%S')}] Invalid embedding.")
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
                self.queue.task_done()

    def _preprocess_embedding(self, emb_raw):
        emb = np.array(emb_raw, dtype=np.float32).flatten()
        if emb.size == 0:
            return None
        norm = np.linalg.norm(emb)
        if norm == 0:
            return None
        return emb / norm

    def _assign_identity(self, timestamp, embedding, bbox, file_path, camera_id):
        with self.lock:
            self._clean_old_entries(timestamp)

            best_pid, best_sim = None, -1

            for pid, prototypes in self.prototype_db.items():
                sims = [np.dot(embedding, proto) for proto in prototypes]
                max_sim = max(sims)

                # Add spatial bias if seen recently from same camera
                for ts_recent, seen_pid, seen_bbox in self.recent_detections[camera_id]:
                    if seen_pid == pid and self._bbox_distance(bbox, seen_bbox) < self.spatial_distance_thresh:
                        max_sim += self.spatial_bias
                        break  # one bonus is enough

                if max_sim > best_sim:
                    best_sim = max_sim
                    best_pid = pid

            if best_sim >= self.sim_threshold:
                self._update_identity(best_pid, timestamp, embedding, bbox, camera_id)
                if self.logger:
                    self.logger.log(timestamp, best_pid, embedding, bbox, file_path, camera_id)
                return best_pid
            else:
                return self._create_new_identity(embedding, timestamp, bbox, file_path, camera_id)

    def _update_identity(self, pid, timestamp, embedding, bbox, camera_id):
        self.embedding_history[pid].append((timestamp, embedding))
        self._trim_history(pid)

        # Keep prototypes updated
        prototypes = self.prototype_db[pid]
        sims = [np.dot(embedding, p) for p in prototypes]

        if max(sims) < self.sim_threshold:
            if len(prototypes) < self.max_prototypes:
                prototypes.append(embedding)
            else:
                min_idx = int(np.argmin(sims))
                prototypes[min_idx] = embedding
        else:
            best_idx = int(np.argmax(sims))
            updated = (prototypes[best_idx] + embedding) / 2
            prototypes[best_idx] = updated / np.linalg.norm(updated)

        # Track spatial detection history
        self._update_recent_detections(camera_id, timestamp, pid, bbox)

    def _create_new_identity(self, embedding, timestamp, bbox, file_path, camera_id):
        self.person_counter += 1
        pid = self.person_counter

        self.embedding_history[pid].append((timestamp, embedding))
        self._trim_history(pid)
        self.prototype_db[pid].append(embedding)

        self._update_recent_detections(camera_id, timestamp, pid, bbox)

        if self.logger:
            self.logger.log(timestamp, pid, embedding, bbox, file_path, camera_id)
        return pid

    def _update_recent_detections(self, camera_id, timestamp, pid, bbox):
        q = self.recent_detections[camera_id]
        q.append((timestamp, pid, bbox))
        if len(q) > self.spatial_window_size:
            q.popleft()

    def _clean_old_entries(self, current_time):
        for pid in list(self.embedding_history.keys()):
            self.embedding_history[pid] = deque([
                (ts, emb) for ts, emb in self.embedding_history[pid]
                if (current_time - ts).total_seconds() <= self.max_age_sec
            ])
            if not self.embedding_history[pid]:
                del self.embedding_history[pid]
                self.prototype_db.pop(pid, None)
                for q in self.recent_detections.values():
                    q = deque([(ts, p, b) for ts, p, b in q if p != pid])

    def _bbox_distance(self, b1, b2):
        c1 = ((b1[0] + b1[2]) / 2, (b1[1] + b1[3]) / 2)
        c2 = ((b2[0] + b2[2]) / 2, (b2[1] + b2[3]) / 2)
        return np.linalg.norm(np.array(c1) - np.array(c2))

    def get_active_identity_count(self):
        with self.lock:
            return len(self.prototype_db)
        
    def _trim_history(self, pid):
        history = self.embedding_history[pid]
        while len(history) > self.max_history:
            history.popleft()