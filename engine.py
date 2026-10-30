import threading, time
from collections import deque
import cv2, numpy as np, face_recognition as fr
import config, db

class Recognizer:
    """Owns the camera. Streams annotated frames and marks attendance in a background thread."""
    def __init__(self):
        self.raw = None; self.jpeg = None
        self.running = False; self.recognizing = True
        self.events = deque(maxlen=8)          # recent recognitions shown on the live page
        self.last_unknown = 0
        self.reload()
        
    def reload(self):
        db.init()                      # make sure tables exist before reading
        self.enc, self.owner, self.names = db.load_known()

    def start(self):
        if self.running: return
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        cap = cv2.VideoCapture(config.CAMERA_INDEX)
        n, results = 0, []
        while self.running:
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.2); continue
            self.raw = frame.copy()
            n += 1
            if self.recognizing and n % config.PROCESS_EVERY_N == 0:
                results = self._recognize(frame)
            elif not self.recognizing:
                results = []
            for (t, r, b, l), label, known in results:
                color = (110, 118, 15) if known else (4, 100, 220)   # BGR
                cv2.rectangle(frame, (l, t), (r, b), color, 2)
                cv2.rectangle(frame, (l, b - 24), (r, b), color, -1)
                cv2.putText(frame, label, (l + 6, b - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
            self.jpeg = cv2.imencode(".jpg", frame)[1].tobytes()
        cap.release()

    def _recognize(self, frame):
        small = cv2.cvtColor(cv2.resize(frame, (0, 0), fx=config.SCALE, fy=config.SCALE), cv2.COLOR_BGR2RGB)
        locs = fr.face_locations(small)
        encs = fr.face_encodings(small, locs)
        s = 1 / config.SCALE
        cands = []                              # (face index, user id, distance)
        for i, e in enumerate(encs):
            if self.enc:
                d = fr.face_distance(self.enc, e)
                j = int(np.argmin(d))
                if d[j] <= config.TOLERANCE:
                    cands.append((i, self.owner[j], float(d[j])))
        # If two faces claim the same person, only the closer match keeps the identity.
        best = {}
        for i, uid, d in cands:
            if uid not in best or d < best[uid][1]:
                best[uid] = (i, d)
        assigned = {i: (uid, d) for uid, (i, d) in best.items()}
        out = []
        for i, (t, r, b, l) in enumerate(locs):
            box = (int(t * s), int(r * s), int(b * s), int(l * s))
            if i in assigned:
                uid, d = assigned[i]
                new = db.mark(uid, 1 - d)
                name = self.names.get(uid, "?")
                if new:
                    self.events.appendleft(f"{time.strftime('%H:%M:%S')}  {name} marked present")
                out.append((box, f"{name} {1 - d:.0%}", True))
            else:
                if time.time() - self.last_unknown > config.UNKNOWN_COOLDOWN:
                    db.log_unknown(); self.last_unknown = time.time()
                out.append((box, "Unknown", False))
        return out

    def capture_samples(self, n=config.SAMPLES_PER_USER, timeout=25):
        """Grab n encodings of exactly one face, ~0.6s apart. Returns (encodings, error)."""
        encs, start = [], time.time()
        while len(encs) < n and time.time() - start < timeout:
            time.sleep(0.6)
            if self.raw is None: continue
            rgb = cv2.cvtColor(self.raw, cv2.COLOR_BGR2RGB)
            locs = fr.face_locations(rgb)
            if len(locs) != 1: continue
            encs.append(fr.face_encodings(rgb, locs)[0])
        if len(encs) < n:
            return None, "Could not capture clear samples. Make sure exactly one face is visible and well lit."
        return encs, None

recognizer = Recognizer()
