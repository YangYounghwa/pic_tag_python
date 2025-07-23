
from pic_tag.camera_worker import frame_queue


def extract_features(frame):
    # Dummy feature extraction logic
    features = {"mean_color": frame.mean(axis=(0, 1))}
    return features