# Face Attendance System

Marks attendance automatically from a live camera using face recognition (OpenCV + `face_recognition`/dlib), with a Flask admin dashboard and SQLite storage.

## Setup
1. Python 3.9+ and a webcam. `face_recognition` needs dlib, which needs CMake and a C++ compiler
   (Windows: install "Desktop development with C++" from Visual Studio Build Tools, then `pip install cmake`).
2. `python -m venv venv` and activate it
3. `pip install -r requirements.txt`
4. Optional: set `ADMIN_PASSWORD` and `SECRET_KEY` environment variables (default password is `admin123`).
5. `python app.py`, then open http://127.0.0.1:5000
.\venv\Scripts\Activate.ps1
python app.py
cd D:\face-attendance



## Using it
- **Register face**: enter roll number and name, then capture. 5 samples are taken, one face only in frame.
- **Live camera**: recognised people are marked present once per day; unknown faces are boxed in orange and only counted, never marked.
- **Records**: view a day, a monthly summary with attendance %, and download CSV or Excel.
- **Users**: remove a person (also deletes their records).

## Tuning (config.py)
`TOLERANCE` (lower = stricter), `PROCESS_EVERY_N` (higher = faster, laggier), `CAMERA_INDEX`, `SAMPLES_PER_USER`.

## Layout
`app.py` routes and exports | `engine.py` camera, detection, matching | `db.py` SQLite | `templates/`, `static/` UI

## Limitations and next steps
- No liveness detection yet: a printed photo can fool it (add blink or depth checks).
- Accuracy drops in poor light or at steep angles; register samples in the lighting you will use.
- Face encodings are biometric data: keep `data/attendance.db` private and get consent from registered users.
