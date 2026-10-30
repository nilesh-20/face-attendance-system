import io, time, datetime as dt
from functools import wraps
import pandas as pd
from flask import (Flask, render_template, request, redirect, url_for, session,
                   Response, flash, send_file, jsonify)
import config, db
from engine import recognizer

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
db.init()

def login_required(f):
    @wraps(f)
    def w(*a, **k):
        if not session.get("admin"):
            return redirect(url_for("login"))
        return f(*a, **k)
    return w

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == config.ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("dashboard"))
        flash("Incorrect password.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("login"))

@app.route("/")
@login_required
def dashboard():
    today = dt.date.today().isoformat()
    total, present, unknown = db.stats()
    return render_template("dashboard.html", today=today, total=total, present=present,
                           unknown=unknown, rows=db.present_on(today), absent=db.absent_on(today))

@app.route("/live")
@login_required
def live():
    return render_template("live.html", on=recognizer.recognizing)

def _stream():
    while True:
        if recognizer.jpeg:
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + recognizer.jpeg + b"\r\n"
        time.sleep(0.04)

@app.route("/video_feed")
@login_required
def video_feed():
    return Response(_stream(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/api/events")
@login_required
def events():
    return jsonify(list(recognizer.events))

@app.route("/toggle", methods=["POST"])
@login_required
def toggle():
    recognizer.recognizing = not recognizer.recognizing
    return redirect(url_for("live"))

@app.route("/register", methods=["GET", "POST"])
@login_required
def register():
    if request.method == "POST":
        roll, name = request.form["roll_no"].strip(), request.form["name"].strip()
        if not roll or not name:
            flash("Enter both a roll number and a name.")
        else:
            was = recognizer.recognizing
            recognizer.recognizing = False          # don't mark attendance while enrolling
            encs, err = recognizer.capture_samples()
            recognizer.recognizing = was
            if err:
                flash(err)
            else:
                try:
                    db.add_user(roll, name, encs); recognizer.reload()
                    flash(f"{name} registered with {len(encs)} face samples.")
                    return redirect(url_for("users"))
                except Exception:
                    flash(f"Roll number {roll} is already registered.")
    return render_template("register.html")

@app.route("/users")
@login_required
def users():
    return render_template("users.html", users=db.list_users())

@app.route("/users/<int:uid>/delete", methods=["POST"])
@login_required
def delete(uid):
    db.delete_user(uid); recognizer.reload()
    flash("User and their records removed."); return redirect(url_for("users"))

@app.route("/attendance")
@login_required
def attendance():
    date = request.args.get("date", dt.date.today().isoformat())
    month = request.args.get("month", date[:7])
    days, summary = db.month_summary(month)
    return render_template("attendance.html", date=date, month=month, rows=db.present_on(date),
                           days=days, summary=summary)

@app.route("/export")
@login_required
def export():
    month, fmt = request.args.get("month", dt.date.today().isoformat()[:7]), request.args.get("fmt", "csv")
    df = pd.DataFrame([dict(r) for r in db.month_records(month)],
                      columns=["roll_no", "name", "date", "time", "confidence"])
    buf = io.BytesIO()
    if fmt == "xlsx":
        df.to_excel(buf, index=False); mime, ext = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx"
    else:
        buf.write(df.to_csv(index=False).encode()); mime, ext = "text/csv", "csv"
    buf.seek(0)
    return send_file(buf, mimetype=mime, as_attachment=True, download_name=f"attendance_{month}.{ext}")

if __name__ == "__main__":
    recognizer.start()
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
