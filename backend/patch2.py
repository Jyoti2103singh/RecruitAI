with open('app.py', encoding='utf-8') as f:
    content = f.read()

new_routes = '''# ============================================================
# INTERVIEW SCHEDULER
# ============================================================
@app.route("/recruiter/interviews")
def recruiter_interviews():
    if "user" not in session or session.get("role") == "jobseeker":
        return redirect("/login")
    return render_template("recruiter/interviews.html", username=session["user"])

@app.route("/api/interview-slots", methods=["GET"])
def get_interview_slots():
    if "user" not in session:
        return jsonify([])
    conn = get_screening_db()
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS interview_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recruiter TEXT NOT NULL,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            duration INTEGER DEFAULT 30,
            location TEXT DEFAULT 'Google Meet',
            job_id INTEGER,
            max_bookings INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS interview_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id INTEGER NOT NULL,
            applicant TEXT NOT NULL,
            job_id INTEGER,
            status TEXT DEFAULT 'confirmed',
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )""")
        conn.commit()
        role = session.get("role", "")
        if role == "jobseeker":
            slots = [dict(r) for r in conn.execute(
                "SELECT s.*, b.applicant as booked_by, b.id as booking_id FROM interview_slots s LEFT JOIN interview_bookings b ON s.id=b.slot_id AND b.applicant=? WHERE s.date >= date('now') ORDER BY s.date, s.time",
                (session["user"],)
            ).fetchall()]
        else:
            slots = [dict(r) for r in conn.execute(
                "SELECT s.*, COUNT(b.id) as booking_count FROM interview_slots s LEFT JOIN interview_bookings b ON s.id=b.slot_id WHERE s.recruiter=? GROUP BY s.id ORDER BY s.date, s.time",
                (session["user"],)
            ).fetchall()]
        return jsonify(slots)
    finally:
        conn.close()

@app.route("/api/interview-slots", methods=["POST"])
def create_interview_slot():
    if "user" not in session or session.get("role") == "jobseeker":
        return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json() or {}
    conn = get_screening_db()
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS interview_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recruiter TEXT NOT NULL,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            duration INTEGER DEFAULT 30,
            location TEXT DEFAULT 'Google Meet',
            job_id INTEGER,
            max_bookings INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )""")
        conn.commit()
        conn.execute(
            "INSERT INTO interview_slots (recruiter, title, date, time, duration, location, job_id, max_bookings) VALUES (?,?,?,?,?,?,?,?)",
            (session["user"], data.get("title","Interview"), data.get("date"), data.get("time"),
             data.get("duration", 30), data.get("location","Google Meet"),
             data.get("job_id"), data.get("max_bookings", 1))
        )
        conn.commit()
        return jsonify({"success": True})
    finally:
        conn.close()

@app.route("/api/interview-slots/<int:slot_id>", methods=["DELETE"])
def delete_interview_slot(slot_id):
    if "user" not in session or session.get("role") == "jobseeker":
        return jsonify({"error": "Unauthorized"}), 403
    conn = get_screening_db()
    try:
        conn.execute("DELETE FROM interview_slots WHERE id=? AND recruiter=?", (slot_id, session["user"]))
        conn.execute("DELETE FROM interview_bookings WHERE slot_id=?", (slot_id,))
        conn.commit()
        return jsonify({"success": True})
    finally:
        conn.close()

@app.route("/api/interview-slots/<int:slot_id>/book", methods=["POST"])
def book_interview_slot(slot_id):
    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401
    conn = get_screening_db()
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS interview_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id INTEGER NOT NULL,
            applicant TEXT NOT NULL,
            job_id INTEGER,
            status TEXT DEFAULT 'confirmed',
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )""")
        conn.commit()
        already = conn.execute("SELECT id FROM interview_bookings WHERE slot_id=? AND applicant=?",
                               (slot_id, session["user"])).fetchone()
        if already:
            return jsonify({"error": "Already booked"}), 400
        slot = conn.execute("SELECT * FROM interview_slots WHERE id=?", (slot_id,)).fetchone()
        if not slot:
            return jsonify({"error": "Slot not found"}), 404
        count = conn.execute("SELECT COUNT(*) FROM interview_bookings WHERE slot_id=?", (slot_id,)).fetchone()[0]
        if count >= slot["max_bookings"]:
            return jsonify({"error": "Slot fully booked"}), 400
        conn.execute("INSERT INTO interview_bookings (slot_id, applicant, job_id) VALUES (?,?,?)",
                     (slot_id, session["user"], slot["job_id"]))
        conn.commit()
        try:
            conn.execute("INSERT INTO notifications (username, title, body, type) VALUES (?,?,?,?)",
                (session["user"],
                 "Interview Booked!",
                 f"Your interview '{slot['title']}' is confirmed for {slot['date']} at {slot['time']}. Location: {slot['location']}",
                 "shortlisted"))
            conn.commit()
        except:
            pass
        return jsonify({"success": True})
    finally:
        conn.close()

@app.route("/api/interview-slots/<int:slot_id>/cancel", methods=["POST"])
def cancel_interview_booking(slot_id):
    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401
    conn = get_screening_db()
    try:
        conn.execute("DELETE FROM interview_bookings WHERE slot_id=? AND applicant=?",
                     (slot_id, session["user"]))
        conn.commit()
        return jsonify({"success": True})
    finally:
        conn.close()

@app.route("/api/interview-bookings")
def get_interview_bookings():
    if "user" not in session or session.get("role") == "jobseeker":
        return jsonify([])
    conn = get_screening_db()
    try:
        rows = conn.execute(
            """SELECT b.*, s.title, s.date, s.time, s.duration, s.location
               FROM interview_bookings b JOIN interview_slots s ON b.slot_id=s.id
               WHERE s.recruiter=? ORDER BY s.date, s.time""",
            (session["user"],)
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()

# ============================================================
# RESUME BUILDER
# ============================================================
@app.route("/jobseeker/resume-builder")
def resume_builder():
    if "user" not in session:
        return redirect("/login")
    return render_template("jobseeker/resume-builder.html", username=session["user"])

@app.route("/api/resume-builder/save", methods=["POST"])
def save_resume_draft():
    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401
    data = request.get_json() or {}
    conn = get_screening_db()
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS resume_drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            draft_json TEXT NOT NULL,
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        )""")
        conn.commit()
        existing = conn.execute("SELECT id FROM resume_drafts WHERE username=?", (session["user"],)).fetchone()
        if existing:
            conn.execute("UPDATE resume_drafts SET draft_json=?, updated_at=datetime('now','localtime') WHERE username=?",
                         (json.dumps(data), session["user"]))
        else:
            conn.execute("INSERT INTO resume_drafts (username, draft_json) VALUES (?,?)",
                         (session["user"], json.dumps(data)))
        conn.commit()
        return jsonify({"success": True})
    finally:
        conn.close()

@app.route("/api/resume-builder/load")
def load_resume_draft():
    if "user" not in session:
        return jsonify({})
    conn = get_screening_db()
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS resume_drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            draft_json TEXT NOT NULL,
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        )""")
        conn.commit()
        row = conn.execute("SELECT draft_json FROM resume_drafts WHERE username=?", (session["user"],)).fetchone()
        return jsonify(json.loads(row["draft_json"]) if row else {})
    finally:
        conn.close()

# JOBSEEKER — MY APPLICATIONS PAGE'''

content = content.replace('# JOBSEEKER — MY APPLICATIONS PAGE', new_routes, 1)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done! New length:', len(content))
