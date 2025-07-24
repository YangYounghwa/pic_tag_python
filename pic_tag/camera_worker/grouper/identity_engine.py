import time
import threading
import numpy as np
from queue import Queue, Empty
from collections import defaultdict, deque
from sklearn.metrics.pairwise import cosine_similarity

class IdentityEngine:
    def __init__(self, similarity_threshold=0.2, max_history=20000, max_age_sec=86400):
        self.queue = Queue()
        self.lock = threading.Lock()

        self.centroids = {}  # id -> centroid (np.ndarray)
        self.history = defaultdict(deque)  # id -> deque of (timestamp, embedding)
        self.next_id = 0
        self.sim_threshold = similarity_threshold
        self.max_history = max_history
        self.max_age_sec = max_age_sec

    def add_embedding(self, embedding):
        """Add a new embedding (as list or np.ndarray of shape (128,)) to the queue."""
        if isinstance(embedding, list):
            embedding = np.array(embedding, dtype=np.float32)
        embedding = embedding / np.linalg.norm(embedding)  # Normalize
        self.queue.put((time.time(), embedding))

    def run(self):
        """Start processing loop for identity assignment."""
        while True:
            try:
                timestamp, embedding = self.queue.get(timeout=1.0)
                with self.lock:
                    self._remove_old_entries()
                    person_id = self._assign_identity(embedding, timestamp)
                    print(f"[INFO] Assigned ID: {person_id}")
                self.queue.task_done()
            except Empty:
                time.sleep(0.2)

    def _assign_identity(self, embedding, timestamp):
        if not self.centroids:
            return self._create_new_identity(embedding, timestamp)

        all_ids = list(self.centroids.keys())
        all_centroids = np.stack([self.centroids[id_] for id_ in all_ids])

        sims = cosine_similarity([embedding], all_centroids)[0]
        best_match_idx = np.argmax(sims)
        best_sim = sims[best_match_idx]

        if best_sim >= self.sim_threshold:
            person_id = all_ids[best_match_idx]
            self._update_identity(person_id, embedding, timestamp)
        else:
            person_id = self._create_new_identity(embedding, timestamp)

        return person_id

    def _update_identity(self, person_id, embedding, timestamp):
        self.history[person_id].append((timestamp, embedding))
        if len(self.history[person_id]) > 100:
            self.history[person_id].popleft()
        # Update centroid
        embeddings = np.stack([e for _, e in self.history[person_id]])
        self.centroids[person_id] = np.mean(embeddings, axis=0)
        self.centroids[person_id] /= np.linalg.norm(self.centroids[person_id])

    def _create_new_identity(self, embedding, timestamp):
        person_id = self.next_id
        self.next_id += 1
        self.history[person_id].append((timestamp, embedding))
        self.centroids[person_id] = embedding
        return person_id

    def _remove_old_entries(self):
        now = time.time()
        all_entries = []
        for person_id, emb_deque in list(self.history.items()):
            self.history[person_id] = deque(
                [(ts, emb) for ts, emb in emb_deque if now - ts <= self.max_age_sec],
                maxlen=100
            )
            if not self.history[person_id]:
                self.history.pop(person_id)
                self.centroids.pop(person_id)