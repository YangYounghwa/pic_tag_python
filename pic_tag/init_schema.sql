CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    cam_name TEXT NOT NULL,

    coord_x1 REAL NOT NULL,
    coord_y1 REAL NOT NULL,
    coord_x2 REAL NOT NULL,
    coord_y2 REAL NOT NULL,

    -- 128D feature embedding stored as a JSON string (list of doubles)
    feature TEXT NOT NULL,

);