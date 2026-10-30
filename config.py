import os
BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "data", "attendance.db")
CAMERA_INDEX = 0          # change if you have multiple cameras
TOLERANCE = 0.5           # lower = stricter matching (default dlib is 0.6)
SCALE = 0.25              # frames are shrunk before detection for speed
PROCESS_EVERY_N = 3       # run recognition on every Nth frame
SAMPLES_PER_USER = 5      # face images captured at registration
UNKNOWN_COOLDOWN = 30     # seconds between logged "unknown" events
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
