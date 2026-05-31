with open('app.py', encoding='utf-8') as f:
    content = f.read()

# ── FIX 1: Add AI match score to apply route ──
old = '''        conn.execute(
            """INSERT INTO applications
               (job_id, applicant, ats_score, cover_note, portfolio_url, status, created_at)
               VALUES (?,?,?,?,?,?,?)""",
            (job_id, session["user"], ats_score,
             data.get("cover_note", ""), data.get("portfolio_url", ""),
             "pending", datetime.now().isoformat())
        )
        conn.commit()
        return jsonify({"success": True})'''

new = '''        # Get job description for AI match
        job = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        ai_match_score = 0
        ai_match_summary = ""

        if job:
            # Get jobseeker's latest resume text from candidates table
            candidate = conn.execute(
                "SELECT skills_json, notes FROM candidates WHERE user_id=? ORDER BY created_at DESC LIMIT 1",
                (session["user"],)
            ).fetchone()

            if candidate:
                import json as _json
                skills = _json.loads(candidate["skills_json"] or "[]")
                job_skills_raw = job["skills"] if job["skills"] else "[]"
                try:
                    job_skills = _json.loads(job_skills_raw)
                except:
                    job_skills = []

                # Rule-based match
                if job_skills and skills:
                    matched = [s for s in skills if any(s.lower() in js.lower() or js.lower() in s.lower() for js in job_skills)]
                    ai_match_score = min(100, int(len(matched) / max(len(job_skills), 1) * 100))
                else:
                    ai_match_score = ats_score

                # Try Gemini for better match
                try:
                    match_prompt = f"""You are a recruitment AI. Given this job and candidate, return ONLY a JSON object, no markdown.

Job Title: {job["title"]}
Job Skills Required: {", ".join(job_skills)}
Job Description: {(job["description"] or "")[:500]}

Candidate Skills: {", ".join(skills)}
Candidate ATS Score: {ats_score}

Return exactly:
{{"match_score": <0-100>, "summary": "<one sentence why they are or aren't a good fit>", "matched_skills": ["skill1","skill2"], "missing_skills": ["skill3"]}}"""

                    ai_resp = call_gemini(match_prompt)
                    if ai_resp:
                        import re as _re
                        clean = _re.sub(r"```json|```", "", ai_resp).strip()
                        ai_data = _json.loads(clean)
                        ai_match_score = ai_data.get("match_score", ai_match_score)
                        ai_match_summary = ai_data.get("summary", "")
                except Exception as e:
                    print(f"DEBUG: AI match error: {e}")

        # Add ai_match_score column if missing
        try:
            conn.execute("ALTER TABLE applications ADD COLUMN ai_match_score INTEGER DEFAULT 0")
            conn.commit()
        except:
            pass
        try:
            conn.execute("ALTER TABLE applications ADD COLUMN ai_match_summary TEXT DEFAULT ''")
            conn.commit()
        except:
            pass

        conn.execute(
            """INSERT INTO applications
               (job_id, applicant, ats_score, cover_note, portfolio_url, status, created_at, ai_match_score, ai_match_summary)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (job_id, session["user"], ats_score,
             data.get("cover_note", ""), data.get("portfolio_url", ""),
             "pending", datetime.now().isoformat(), ai_match_score, ai_match_summary)
        )
        conn.commit()
        return jsonify({"success": True, "ai_match_score": ai_match_score, "ai_match_summary": ai_match_summary})'''

if old in content:
    content = content.replace(old, new)
    print("Fix 1 applied: AI match score on apply")
else:
    print("Fix 1 NOT found - check spacing")

# ── FIX 2: Add notification when recruiter updates status ──
old2 = '''    conn = get_screening_db()
    try:
        conn.execute("UPDATE applications SET status=? WHERE id=?", (status, app_id))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()'''

new2 = '''    conn = get_screening_db()
    try:
        # Get application details for notification
        app_row = conn.execute(
            "SELECT applicant, job_id FROM applications WHERE id=?", (app_id,)
        ).fetchone()
        job_title = ""
        if app_row:
            job_row = conn.execute("SELECT title FROM jobs WHERE id=?", (app_row["job_id"],)).fetchone()
            job_title = job_row["title"] if job_row else ""

        conn.execute("UPDATE applications SET status=? WHERE id=?", (status, app_id))
        conn.commit()

        # Store notification for jobseeker
        try:
            conn.execute("""CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                type TEXT DEFAULT 'info',
                is_read INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )""")
            conn.commit()

            if app_row:
                if status == "shortlisted":
                    notif_title = "🎉 You've been Shortlisted!"
                    notif_body = f"Congratulations! Your application for {job_title} has been shortlisted. Expect to hear more soon."
                elif status == "rejected":
                    notif_title = "Application Update"
                    notif_body = f"Thank you for applying to {job_title}. Unfortunately your application was not selected this time."
                else:
                    notif_title = "Application Status Updated"
                    notif_body = f"Your application for {job_title} status changed to {status}."

                conn.execute(
                    "INSERT INTO notifications (username, title, body, type) VALUES (?,?,?,?)",
                    (app_row["applicant"], notif_title, notif_body, status)
                )
                conn.commit()
        except Exception as e:
            print(f"DEBUG: Notification error: {e}")

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()'''

if old2 in content:
    content = content.replace(old2, new2)
    print("Fix 2 applied: jobseeker notifications on status change")
else:
    print("Fix 2 NOT found - check spacing")

# ── FIX 3: Add /api/notifications endpoint ──
old3 = '# JOBSEEKER — MY APPLICATIONS PAGE'
new3 = '''# ── NOTIFICATIONS API ──
@app.route("/api/notifications")
def api_get_notifications():
    if "user" not in session:
        return jsonify([])
    conn = get_screening_db()
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            type TEXT DEFAULT 'info',
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )""")
        rows = conn.execute(
            "SELECT * FROM notifications WHERE username=? ORDER BY created_at DESC LIMIT 20",
            (session["user"],)
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()

@app.route("/api/notifications/read", methods=["POST"])
def api_mark_notifications_read():
    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401
    conn = get_screening_db()
    try:
        conn.execute("UPDATE notifications SET is_read=1 WHERE username=?", (session["user"],))
        conn.commit()
        return jsonify({"success": True})
    finally:
        conn.close()

# JOBSEEKER — MY APPLICATIONS PAGE'''

if old3 in content:
    content = content.replace(old3, new3)
    print("Fix 3 applied: notifications API endpoints")
else:
    print("Fix 3 NOT found - check comment")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done! Restart python app.py")