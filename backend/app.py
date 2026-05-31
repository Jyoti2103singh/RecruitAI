import os
import json
import sqlite3
import requests
from datetime import datetime
from io import BytesIO

from flask import (
    Flask,
    render_template_string,
    request,
    redirect,
    session,
    jsonify,
    send_file,
)
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
try:
    from pdfminer.high_level import extract_text as pdf_extract_text
    PDF_EXTRACT_OK = True
except ImportError:
    PDF_EXTRACT_OK = False

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

GEMINI_KEY = os.getenv("GEMINI_KEY")
DB_PATH = "screening.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_tables():
    conn = get_db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'jobseeker',
        full_name TEXT,
        email TEXT,
        phone TEXT,
        city TEXT,
        state TEXT,
        job_title TEXT,
        experience TEXT,
        education TEXT,
        company_name TEXT,
        company_size TEXT,
        industry TEXT,
        designation TEXT,
        created_at TEXT
    )""")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS resume_drafts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        draft_json TEXT,
        updated_at TEXT
    )""")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS resume_analytics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        views INTEGER DEFAULT 0,
        downloads INTEGER DEFAULT 0,
        ats_score INTEGER DEFAULT 0
    )""")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS resume_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        version_name TEXT,
        resume_json TEXT,
        created_at TEXT
    )""")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recruiter TEXT,
        title TEXT,
        company TEXT,
        location TEXT,
        job_type TEXT DEFAULT 'Full-time',
        description TEXT,
        skills_required TEXT,
        salary TEXT,
        posted_at TEXT,
        active INTEGER DEFAULT 1
    )""")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        job_id INTEGER,
        job_title TEXT,
        company TEXT,
        status TEXT DEFAULT 'Applied',
        applied_at TEXT,
        resume_json TEXT
    )""")
    conn.commit()
    conn.close()

def gemini(prompt):
    if not GEMINI_KEY:
        return "AI unavailable (no GEMINI_KEY set)"
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        r = requests.post(url, json=payload, timeout=20)
        data = r.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"AI error: {str(e)}"

@app.route("/")
def index():
    if "user" not in session:
        return redirect("/login")
    return redirect("/recruiter/dashboard" if session.get("role") == "recruiter" else "/dashboard")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "jobseeker")
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=? AND role=?",
            (username, password, role)
        ).fetchone()
        conn.close()
        if user:
            session["user"] = username
            session["role"] = user["role"]
            return redirect("/recruiter/dashboard" if user["role"] == "recruiter" else "/dashboard")
        return render_template_string(LOGIN_HTML, error="Invalid credentials or wrong role selected")
    return render_template_string(LOGIN_HTML, error=None)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "jobseeker")
        if not username or not password:
            return render_template_string(REGISTER_HTML, error="All fields required")
        conn = get_db()
        if conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone():
            conn.close()
            return render_template_string(REGISTER_HTML, error="Username already taken")
        conn.execute("""
            INSERT INTO users (username, password, role, full_name, email, phone,
            city, state, job_title, experience, education,
            company_name, company_size, industry, designation, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            username, password, role,
            request.form.get("full_name"),
            request.form.get("email"),
            request.form.get("phone"),
            request.form.get("city"),
            request.form.get("state"),
            request.form.get("job_title"),
            request.form.get("experience"),
            request.form.get("education"),
            request.form.get("company_name"),
            request.form.get("company_size"),
            request.form.get("industry"),
            request.form.get("designation"),
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
        session["user"] = username
        session["role"] = role
        return redirect("/recruiter/dashboard" if role == "recruiter" else "/dashboard")
    return render_template_string(REGISTER_HTML, error=None)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# CANDIDATE DASHBOARD
@app.route("/dashboard")
def candidate_dashboard():
    if "user" not in session: return redirect("/login")
    if session.get("role") == "recruiter": return redirect("/recruiter/dashboard")
    conn = get_db()
    analytics = conn.execute("SELECT * FROM resume_analytics WHERE username=?", (session["user"],)).fetchone()
    applications = conn.execute("SELECT * FROM applications WHERE username=? ORDER BY id DESC LIMIT 5", (session["user"],)).fetchall()
    total_apps = conn.execute("SELECT COUNT(*) as c FROM applications WHERE username=?", (session["user"],)).fetchone()["c"]
    shortlisted = conn.execute("SELECT COUNT(*) as c FROM applications WHERE username=? AND status='Shortlisted'", (session["user"],)).fetchone()["c"]
    conn.close()
    stats = dict(analytics) if analytics else {"views": 0, "downloads": 0, "ats_score": 0}
    return render_template_string(CANDIDATE_DASHBOARD_HTML,
        username=session["user"],
        stats=stats,
        applications=applications,
        total_apps=total_apps,
        shortlisted=shortlisted
    )

# RESUME BUILDER
@app.route("/resume-builder")
def resume_builder():
    if "user" not in session: return redirect("/login")
    if session.get("role") == "recruiter": return redirect("/recruiter/dashboard")
    return render_template_string(RESUME_BUILDER_HTML)

# RECRUITER DASHBOARD
@app.route("/recruiter/dashboard")
def recruiter_dashboard():
    if "user" not in session: return redirect("/login")
    if session.get("role") != "recruiter": return redirect("/dashboard")
    conn = get_db()
    jobs = conn.execute("SELECT * FROM jobs WHERE recruiter=? ORDER BY id DESC", (session["user"],)).fetchall()
    total_apps = conn.execute(
        "SELECT COUNT(*) as c FROM applications WHERE job_id IN (SELECT id FROM jobs WHERE recruiter=?)",
        (session["user"],)
    ).fetchone()["c"]
    shortlisted = conn.execute(
        "SELECT COUNT(*) as c FROM applications WHERE status='Shortlisted' AND job_id IN (SELECT id FROM jobs WHERE recruiter=?)",
        (session["user"],)
    ).fetchone()["c"]
    hired = conn.execute(
        "SELECT COUNT(*) as c FROM applications WHERE status='Hired' AND job_id IN (SELECT id FROM jobs WHERE recruiter=?)",
        (session["user"],)
    ).fetchone()["c"]
    rejected = conn.execute(
        "SELECT COUNT(*) as c FROM applications WHERE status='Rejected' AND job_id IN (SELECT id FROM jobs WHERE recruiter=?)",
        (session["user"],)
    ).fetchone()["c"]
    recent_apps = conn.execute(
        """SELECT a.*, j.title as job_title FROM applications a
           JOIN jobs j ON a.job_id = j.id
           WHERE j.recruiter=? ORDER BY a.id DESC LIMIT 8""",
        (session["user"],)
    ).fetchall()
    conn.close()
    return render_template_string(RECRUITER_DASHBOARD_HTML,
        username=session["user"],
        jobs=jobs,
        total_jobs=len(jobs),
        total_apps=total_apps,
        shortlisted=shortlisted,
        hired=hired,
        rejected=rejected,
        recent_apps=recent_apps
    )

# POST JOB
@app.route("/recruiter/post-job", methods=["GET", "POST"])
def post_job():
    if "user" not in session or session.get("role") != "recruiter":
        return redirect("/login")
    if request.method == "POST":
        conn = get_db()
        conn.execute("""
            INSERT INTO jobs (recruiter, title, company, location, job_type, description, skills_required, salary, posted_at)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            session["user"],
            request.form.get("title"),
            request.form.get("company"),
            request.form.get("location"),
            request.form.get("job_type", "Full-time"),
            request.form.get("description"),
            request.form.get("skills_required"),
            request.form.get("salary"),
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
        return redirect("/recruiter/dashboard")
    return render_template_string(POST_JOB_HTML)

# VIEW APPLICANTS
@app.route("/recruiter/job/<int:job_id>/applicants")
def view_applicants(job_id):
    if "user" not in session or session.get("role") != "recruiter":
        return redirect("/login")
    conn = get_db()
    job = conn.execute("SELECT * FROM jobs WHERE id=? AND recruiter=?", (job_id, session["user"])).fetchone()
    if not job:
        conn.close()
        return "Job not found", 404
    applicants = conn.execute("SELECT * FROM applications WHERE job_id=? ORDER BY id DESC", (job_id,)).fetchall()
    conn.close()
    return render_template_string(APPLICANTS_HTML, job=job, applicants=applicants)

# RECRUITER - ALL CANDIDATES
@app.route("/recruiter/candidates")
def recruiter_candidates():
    if "user" not in session or session.get("role") != "recruiter":
        return redirect("/login")
    conn = get_db()
    candidates = conn.execute("""
        SELECT a.*, j.title as job_title FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE j.recruiter=? ORDER BY a.id DESC
    """, (session["user"],)).fetchall()
    conn.close()
    return render_template_string(CANDIDATES_LIST_HTML, candidates=candidates, username=session["user"])

# UPDATE STATUS
@app.route("/api/recruiter/update-status", methods=["POST"])
def update_status():
    if "user" not in session or session.get("role") != "recruiter":
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    conn = get_db()
    conn.execute("UPDATE applications SET status=? WHERE id=?", (data["status"], data["app_id"]))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

# JOB BOARD
@app.route("/jobs")
def job_board():
    if "user" not in session: return redirect("/login")
    conn = get_db()
    query = request.args.get("q", "")
    if query:
        jobs = conn.execute(
            "SELECT * FROM jobs WHERE active=1 AND (title LIKE ? OR company LIKE ? OR skills_required LIKE ?) ORDER BY id DESC",
            (f"%{query}%", f"%{query}%", f"%{query}%")
        ).fetchall()
    else:
        jobs = conn.execute("SELECT * FROM jobs WHERE active=1 ORDER BY id DESC").fetchall()
    conn.close()
    return render_template_string(JOB_BOARD_HTML, jobs=jobs, query=query)

# APPLY
@app.route("/api/jobs/apply", methods=["POST"])
def apply_to_job():
    if "user" not in session: return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    job_id = data.get("job_id")
    conn = get_db()
    existing = conn.execute("SELECT id FROM applications WHERE username=? AND job_id=?", (session["user"], job_id)).fetchone()
    if existing:
        conn.close()
        return jsonify({"error": "Already applied"})
    job = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    draft = conn.execute("SELECT draft_json FROM resume_drafts WHERE username=?", (session["user"],)).fetchone()
    conn.execute("""
        INSERT INTO applications (username, job_id, job_title, company, applied_at, resume_json)
        VALUES (?,?,?,?,?,?)
    """, (
        session["user"], job_id,
        job["title"] if job else "Unknown",
        job["company"] if job else "Unknown",
        datetime.now().isoformat(),
        draft["draft_json"] if draft else "{}"
    ))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

# ANALYTICS
@app.route("/analytics")
def analytics_page():
    if "user" not in session: return redirect("/login")
    conn = get_db()
    analytics = conn.execute("SELECT * FROM resume_analytics WHERE username=?", (session["user"],)).fetchone()
    applications = conn.execute("SELECT * FROM applications WHERE username=? ORDER BY id DESC", (session["user"],)).fetchall()
    conn.close()
    stats = dict(analytics) if analytics else {"views": 0, "downloads": 0, "ats_score": 0}
    return render_template_string(ANALYTICS_HTML, stats=stats, applications=applications, username=session["user"])

@app.route("/api/resume-analytics")
def resume_analytics_api():
    if "user" not in session: return jsonify({"error": "Unauthorized"}), 401
    conn = get_db()
    row = conn.execute("SELECT * FROM resume_analytics WHERE username=?", (session["user"],)).fetchone()
    conn.close()
    return jsonify(dict(row) if row else {"views": 0, "downloads": 0, "ats_score": 0})

# AI ROUTES
@app.route("/api/ai/suggest-skills", methods=["POST"])
def ai_suggest_skills():
    if "user" not in session: return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    job_title = data.get("job_title", "Software Engineer")
    prompt = f"""You are a career coach. Suggest exactly 10 highly relevant technical and soft skills for the job title: "{job_title}".
Return ONLY a JSON array of strings, nothing else. Example: ["Python", "SQL", "Problem Solving"]"""
    result = gemini(prompt)
    try:
        result = result.strip()
        if "```" in result:
            result = result.split("```")[1].replace("json","").strip()
        skills = json.loads(result)
        return jsonify({"skills": skills})
    except:
        return jsonify({"skills": ["Python", "Communication", "Problem Solving", "Teamwork", "SQL"]})

@app.route("/api/ai/ats-score", methods=["POST"])
def ai_ats_score():
    if "user" not in session: return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    resume_text = json.dumps(data.get("resume", {}))
    job_desc = data.get("job_description", "")
    prompt = f"""You are an ATS expert. Score this resume against the job description.
RESUME DATA: {resume_text}
JOB DESCRIPTION: {job_desc if job_desc else "General software engineering role"}
Respond ONLY with valid JSON (no extra text):
{{"score": 78, "grade": "B+", "strengths": ["Clear work experience", "Relevant skills listed"], "improvements": ["Add more keywords", "Quantify achievements"], "keyword_match": 65}}"""
    result = gemini(prompt)
    try:
        result = result.strip()
        if "```" in result:
            result = result.split("```")[1].replace("json","").strip()
        parsed = json.loads(result)
        conn = get_db()
        conn.execute("""
            INSERT INTO resume_analytics (username, ats_score) VALUES (?,?)
            ON CONFLICT(username) DO UPDATE SET ats_score=excluded.ats_score
        """, (session["user"], parsed.get("score", 0)))
        conn.commit()
        conn.close()
        return jsonify(parsed)
    except:
        return jsonify({"score": 60, "grade": "C+", "strengths": ["Resume submitted"], "improvements": ["Add more detail"], "keyword_match": 50})

@app.route("/api/ai/job-match", methods=["POST"])
def ai_job_match():
    if "user" not in session: return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    resume_data = data.get("resume", {})
    job_id = data.get("job_id")
    conn = get_db()
    job = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    conn.close()
    if not job:
        return jsonify({"error": "Job not found"}), 404
    prompt = f"""You are a recruitment AI. Calculate job match percentage.
CANDIDATE RESUME: {json.dumps(resume_data)}
JOB TITLE: {job['title']}
JOB DESCRIPTION: {job['description']}
REQUIRED SKILLS: {job['skills_required']}
Respond ONLY with valid JSON (no extra text):
{{"match_percent": 82, "matched_skills": ["Python", "Flask"], "missing_skills": ["Docker"], "recommendation": "Strong candidate."}}"""
    result = gemini(prompt)
    try:
        result = result.strip()
        if "```" in result:
            result = result.split("```")[1].replace("json","").strip()
        return jsonify(json.loads(result))
    except:
        return jsonify({"match_percent": 70, "matched_skills": [], "missing_skills": [], "recommendation": "Good fit"})

# RESUME SAVE/LOAD/DOWNLOAD
@app.route("/api/resume-builder/save", methods=["POST"])
def save_resume_draft():
    if "user" not in session: return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    conn = get_db()
    existing = conn.execute("SELECT id FROM resume_drafts WHERE username=?", (session["user"],)).fetchone()
    if existing:
        conn.execute("UPDATE resume_drafts SET draft_json=?, updated_at=? WHERE username=?",
                     (json.dumps(data), datetime.now().isoformat(), session["user"]))
    else:
        conn.execute("INSERT INTO resume_drafts (username, draft_json, updated_at) VALUES (?,?,?)",
                     (session["user"], json.dumps(data), datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/resume-builder/load")
def load_resume_draft():
    if "user" not in session: return jsonify({})
    conn = get_db()
    row = conn.execute("SELECT draft_json FROM resume_drafts WHERE username=?", (session["user"],)).fetchone()
    conn.close()
    return jsonify(json.loads(row["draft_json"]) if row else {})

@app.route("/api/resume-builder/download", methods=["POST"])
def download_resume_pdf():
    if "user" not in session: return jsonify({"error": "Not logged in"}), 401
    data = request.get_json()
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50

    def nl(amount=15):
        nonlocal y
        y -= amount
        if y < 60:
            p.showPage()
            y = height - 50

    p.setFont("Helvetica-Bold", 24)
    p.drawString(50, y, data.get("name", "Your Name"))
    nl(25)
    p.setFont("Helvetica", 14)
    p.drawString(50, y, data.get("headline", ""))
    nl(22)
    p.setFont("Helvetica", 11)
    p.drawString(50, y, f"{data.get('email','')}  |  {data.get('phone','')}  |  {data.get('location','')}")
    nl(20)
    p.setStrokeColorRGB(0.48, 0.36, 0.96)
    p.setLineWidth(1.5)
    p.line(50, y, width-50, y)
    nl(18)

    def section_header(title):
        nonlocal y
        p.setFont("Helvetica-Bold", 13)
        p.setFillColorRGB(0.49, 0.36, 0.96)
        p.drawString(50, y, title)
        p.setFillColorRGB(0, 0, 0)
        nl(16)

    if data.get("summary"):
        section_header("SUMMARY")
        p.setFont("Helvetica", 11)
        for line in data["summary"].split("\n"):
            p.drawString(50, y, line); nl()
        nl(8)

    if data.get("experiences"):
        section_header("EXPERIENCE")
        for exp in data["experiences"]:
            p.setFont("Helvetica-Bold", 12)
            p.drawString(50, y, exp.get("title", "")); nl(14)
            p.setFont("Helvetica", 11)
            p.drawString(50, y, f"{exp.get('company','')}  |  {exp.get('start','')} – {exp.get('end','Present')}"); nl(13)
            for line in exp.get("desc","").split("\n"):
                p.drawString(60, y, line); nl()
            nl(8)

    if data.get("education"):
        section_header("EDUCATION")
        for edu in data["education"]:
            p.setFont("Helvetica-Bold", 12)
            p.drawString(50, y, edu.get("degree","")); nl(14)
            p.setFont("Helvetica", 11)
            p.drawString(50, y, f"{edu.get('college','')}  |  {edu.get('from','')} – {edu.get('to','')}"); nl(20)

    if data.get("projects"):
        section_header("PROJECTS")
        for proj in data["projects"]:
            p.setFont("Helvetica-Bold", 12)
            p.drawString(50, y, proj.get("name", proj.get("title",""))); nl(14)
            if proj.get("tech"):
                p.setFont("Helvetica-Oblique", 10)
                p.drawString(50, y, proj["tech"]); nl(13)
            p.setFont("Helvetica", 11)
            for line in proj.get("desc","").split("\n"):
                p.drawString(60, y, line); nl()
            nl(8)

    if data.get("skills"):
        section_header("SKILLS")
        p.setFont("Helvetica", 11)
        p.drawString(50, y, ", ".join(data["skills"])); nl(20)

    if data.get("languages"):
        section_header("LANGUAGES")
        p.setFont("Helvetica", 11)
        p.drawString(50, y, ", ".join(data["languages"])); nl(20)

    if data.get("certifications"):
        section_header("CERTIFICATIONS")
        p.setFont("Helvetica", 11)
        for cert in data["certifications"]:
            p.drawString(50, y, f"• {cert}"); nl()

    p.save()
    buffer.seek(0)
    _track_download(session["user"])
    return send_file(buffer, as_attachment=True, download_name="resume.pdf", mimetype="application/pdf")

def _track_download(username):
    try:
        conn = get_db()
        conn.execute("""
            INSERT INTO resume_analytics (username, downloads) VALUES (?,1)
            ON CONFLICT(username) DO UPDATE SET downloads=downloads+1
        """, (username,))
        conn.commit()
        conn.close()
    except: pass

@app.route("/api/resume/downloaded", methods=["POST"])
def resume_downloaded():
    if "user" not in session: return jsonify({"error": "Unauthorized"}), 401
    _track_download(session["user"])
    return jsonify({"success": True})

@app.route("/api/ai/ats-score-upload", methods=["POST"])
def ai_ats_score_upload():
    """Score an uploaded PDF resume against an optional job description."""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    file = request.files.get("resume_pdf")
    job_desc = request.form.get("job_description", "")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400
    try:
        pdf_bytes = file.read()
        if PDF_EXTRACT_OK:
            from io import BytesIO as _BIO
            resume_text = pdf_extract_text(_BIO(pdf_bytes))
            resume_text = resume_text[:4000]  # trim to avoid token limits
        else:
            resume_text = "(PDF text extraction unavailable)"
    except Exception as e:
        resume_text = f"(Could not extract PDF text: {e})"

    prompt = f"""You are an ATS (Applicant Tracking System) expert. Analyse this resume text and score it.

RESUME TEXT:
{resume_text}

JOB DESCRIPTION: {job_desc if job_desc else "General software/tech role"}

Respond ONLY with a valid JSON object (no extra text, no markdown):
{{
  "score": 74,
  "grade": "B",
  "summary": "2-3 sentence overall assessment of the candidate.",
  "strengths": ["Clear skills section", "Relevant experience listed"],
  "improvements": ["Add quantified achievements", "Include more keywords from job description"],
  "keyword_match": 58,
  "sections_found": ["Experience", "Education", "Skills"],
  "sections_missing": ["Summary", "Certifications"]
}}"""
    result = gemini(prompt)
    try:
        result = result.strip()
        if "```" in result:
            result = result.split("```")[1].replace("json", "").strip()
        parsed = json.loads(result)
        # Save score to analytics
        conn = get_db()
        conn.execute("""
            INSERT INTO resume_analytics (username, ats_score) VALUES (?,?)
            ON CONFLICT(username) DO UPDATE SET ats_score=excluded.ats_score
        """, (session["user"], parsed.get("score", 0)))
        conn.commit()
        conn.close()
        return jsonify(parsed)
    except Exception as e:
        return jsonify({
            "score": 60, "grade": "C+",
            "summary": "Resume received. Please ensure it has clear sections.",
            "strengths": ["Resume submitted successfully"],
            "improvements": ["Add more detail to experience", "Include a summary section"],
            "keyword_match": 50,
            "sections_found": ["Resume"],
            "sections_missing": []
        })


@app.route("/api/resume-builder/save-version", methods=["POST"])
def save_resume_version():
    if "user" not in session: return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    version_name = data.get("version_name", f"Version {datetime.now().strftime('%d %b %Y')}")
    conn = get_db()
    conn.execute(
        "INSERT INTO resume_versions (username, version_name, resume_json, created_at) VALUES (?,?,?,?)",
        (session["user"], version_name, json.dumps(data), datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/resume-builder/versions")
def list_resume_versions():
    if "user" not in session: return jsonify([])
    conn = get_db()
    rows = conn.execute(
        "SELECT id, version_name, created_at FROM resume_versions WHERE username=? ORDER BY id DESC",
        (session["user"],)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ============================================================
# HTML TEMPLATES
# ============================================================

LOGIN_HTML = """<!DOCTYPE html>
<html><head><title>Login – RecruitAI</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'DM Sans',sans-serif;background:#08090e;color:white;display:flex;align-items:center;justify-content:center;min-height:100vh;}
body::before{content:'';position:fixed;top:-200px;left:-200px;width:600px;height:600px;background:radial-gradient(circle,rgba(99,76,255,0.12) 0%,transparent 70%);pointer-events:none;}
body::after{content:'';position:fixed;bottom:-200px;right:-200px;width:500px;height:500px;background:radial-gradient(circle,rgba(168,85,247,0.08) 0%,transparent 70%);pointer-events:none;}
.box{background:#0f1018;padding:44px;border-radius:24px;width:400px;border:1px solid rgba(255,255,255,0.07);position:relative;z-index:1;}
.logo{font-size:22px;font-weight:700;color:#a78bfa;margin-bottom:6px;letter-spacing:-0.5px;}
.logo span{color:#6366f1;}
h2{font-size:26px;font-weight:700;margin-bottom:4px;letter-spacing:-0.5px;}
.sub{color:#4a4b5a;font-size:13px;margin-bottom:28px;}
.role-toggle{display:flex;gap:8px;margin-bottom:24px;background:#0a0b12;padding:4px;border-radius:14px;border:1px solid rgba(255,255,255,0.05);}
.role-btn{flex:1;padding:10px;border:none;border-radius:10px;background:transparent;color:#555;font-size:13px;font-weight:600;cursor:pointer;transition:all .2s;font-family:'DM Sans',sans-serif;}
.role-btn.active{background:#1a1b2e;color:#c4b5fd;box-shadow:0 2px 8px rgba(99,76,255,0.15);}
label{display:block;margin-bottom:5px;font-size:12px;color:#555;font-weight:500;}
input{width:100%;padding:12px 14px;border:1px solid rgba(255,255,255,0.07);outline:none;border-radius:12px;background:#0a0b12;color:white;font-size:14px;margin-bottom:14px;transition:border-color .2s;font-family:'DM Sans',sans-serif;}
input:focus{border-color:#6366f1;}
button[type=submit]{width:100%;padding:13px;border:none;border-radius:12px;background:linear-gradient(135deg,#6366f1,#a78bfa);color:white;font-weight:700;cursor:pointer;font-size:14px;font-family:'DM Sans',sans-serif;transition:opacity .2s;}
button[type=submit]:hover{opacity:.9;}
.err{color:#f87171;font-size:13px;margin-bottom:14px;background:rgba(248,113,113,.08);padding:10px 14px;border-radius:10px;border:1px solid rgba(248,113,113,.15);}
a{color:#a78bfa;text-decoration:none;font-size:13px;}
.link-row{margin-top:18px;text-align:center;color:#333;}
</style></head><body>
<div class="box">
  <div class="logo">✦ Recruit<span>AI</span></div>
  <h2>Welcome back</h2>
  <p class="sub">Sign in to your account</p>
  {% if error %}<div class="err">{{ error }}</div>{% endif %}
  <div class="role-toggle">
    <button type="button" class="role-btn active" id="btn-jobseeker" onclick="setRole('jobseeker')">👤 Candidate</button>
    <button type="button" class="role-btn" id="btn-recruiter" onclick="setRole('recruiter')">🏢 Recruiter</button>
  </div>
  <form method="POST">
    <input type="hidden" name="role" id="roleInput" value="jobseeker">
    <label>Username</label><input type="text" name="username" required placeholder="Enter your username">
    <label>Password</label><input type="password" name="password" required placeholder="Enter your password">
    <button type="submit" id="loginBtn">Sign in as Candidate</button>
  </form>
  <div class="link-row"><a href="/register">Don't have an account? <span style="color:#a78bfa;">Create one →</span></a></div>
</div>
<script>
function setRole(r){
  document.getElementById("roleInput").value=r;
  document.getElementById("btn-jobseeker").classList.toggle("active",r==="jobseeker");
  document.getElementById("btn-recruiter").classList.toggle("active",r==="recruiter");
  document.getElementById("loginBtn").textContent=r==="recruiter"?"Sign in as Recruiter":"Sign in as Candidate";
}
</script></body></html>"""

REGISTER_HTML = """<!DOCTYPE html>
<html><head><title>Register – RecruitAI</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'DM Sans',sans-serif;background:#08090e;color:white;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:30px 0;}
.box{background:#0f1018;padding:40px;border-radius:24px;width:500px;border:1px solid rgba(255,255,255,0.07);}
.logo{font-size:20px;font-weight:700;color:#a78bfa;margin-bottom:6px;}
h2{font-size:24px;font-weight:700;margin-bottom:4px;letter-spacing:-0.5px;}
.sub{color:#4a4b5a;font-size:13px;margin-bottom:24px;}
.role-toggle{display:flex;gap:8px;margin-bottom:22px;background:#0a0b12;padding:4px;border-radius:14px;border:1px solid rgba(255,255,255,0.05);}
.role-btn{flex:1;padding:10px;border:none;border-radius:10px;background:transparent;color:#555;font-size:13px;font-weight:600;cursor:pointer;transition:all .2s;font-family:'DM Sans',sans-serif;}
.role-btn.active{background:#1a1b2e;color:#c4b5fd;}
.row{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
label{display:block;margin-bottom:4px;font-size:12px;color:#555;font-weight:500;}
input,select{width:100%;padding:11px 13px;border:1px solid rgba(255,255,255,0.07);outline:none;border-radius:11px;background:#0a0b12;color:white;font-size:13px;margin-bottom:13px;transition:border-color .2s;font-family:'DM Sans',sans-serif;}
input:focus,select:focus{border-color:#6366f1;}
select option{background:#0f1018;}
.section-label{font-size:11px;color:#6366f1;text-transform:uppercase;letter-spacing:.8px;margin-bottom:10px;margin-top:2px;font-weight:600;}
button[type=submit]{width:100%;padding:13px;border:none;border-radius:12px;background:linear-gradient(135deg,#6366f1,#a78bfa);color:white;font-weight:700;cursor:pointer;font-size:14px;font-family:'DM Sans',sans-serif;}
.err{color:#f87171;font-size:13px;margin-bottom:14px;background:rgba(248,113,113,.08);padding:10px 14px;border-radius:10px;}
a{color:#a78bfa;text-decoration:none;font-size:13px;}
.link-row{margin-top:16px;text-align:center;}
.divider{border:none;border-top:1px solid rgba(255,255,255,0.05);margin:16px 0;}
.hidden{display:none !important;}
</style></head><body>
<div class="box">
  <div class="logo">✦ RecruitAI</div>
  <h2>Create Account</h2>
  <p class="sub">Register as Candidate or Recruiter</p>
  {% if error %}<div class="err">{{ error }}</div>{% endif %}
  <div class="role-toggle">
    <button type="button" class="role-btn active" id="btn-jobseeker" onclick="setRole('jobseeker')">👤 Candidate</button>
    <button type="button" class="role-btn" id="btn-recruiter" onclick="setRole('recruiter')">🏢 Recruiter</button>
  </div>
  <form method="POST">
    <input type="hidden" name="role" id="roleInput" value="jobseeker">
    <div class="section-label">Account Details</div>
    <div class="row">
      <div><label>Username *</label><input type="text" name="username" required placeholder="e.g. rahul123"></div>
      <div><label>Password *</label><input type="password" name="password" required placeholder="Min 6 characters"></div>
    </div>
    <div class="divider"></div>
    <div class="section-label">Personal Details</div>
    <div class="row">
      <div><label>Full Name *</label><input type="text" name="full_name" required placeholder="Rahul Sharma"></div>
      <div><label>Phone</label><input type="text" name="phone" placeholder="+91 98765 43210"></div>
    </div>
    <label>Email *</label><input type="email" name="email" required placeholder="rahul@email.com">
    <div class="divider"></div>
    <div class="section-label" id="extraLabel">Candidate Details</div>
    <div id="candidateFields">
      <div class="row">
        <div><label>City</label><input type="text" name="city" placeholder="Mumbai"></div>
        <div><label>State</label><input type="text" name="state" placeholder="Maharashtra"></div>
      </div>
      <label>Current Job Title</label><input type="text" name="job_title" placeholder="e.g. Software Developer">
      <label>Experience</label>
      <select name="experience">
        <option value="">Select Experience</option>
        <option>Fresher</option>
        <option>0–1 years</option>
        <option>1–3 years</option>
        <option>3–5 years</option>
        <option>5+ years</option>
      </select>
      <label>Highest Education</label>
      <select name="education">
        <option value="">Select Education</option>
        <option>High School</option>
        <option>Diploma</option>
        <option>B.Tech / B.E.</option>
        <option>BCA / B.Sc</option>
        <option>MBA</option>
        <option>MCA / M.Tech</option>
        <option>PhD</option>
      </select>
    </div>
    <div id="recruiterFields" class="hidden">
      <div class="row">
        <div><label>Company Name *</label><input type="text" name="company_name" placeholder="e.g. Infosys"></div>
        <div><label>Company Size</label>
          <select name="company_size">
            <option value="">Select Size</option>
            <option>1–10</option><option>11–50</option><option>51–200</option><option>201–500</option><option>500+</option>
          </select>
        </div>
      </div>
      <label>Industry</label>
      <select name="industry">
        <option value="">Select Industry</option>
        <option>Information Technology</option><option>Finance & Banking</option>
        <option>Healthcare</option><option>Education</option><option>E-Commerce</option>
        <option>Manufacturing</option><option>Consulting</option><option>Other</option>
      </select>
      <label>Your Designation</label>
      <input type="text" name="designation" placeholder="e.g. HR Manager, Talent Acquisition Lead">
    </div>
    <button type="submit" id="regBtn">Register as Candidate</button>
  </form>
  <div class="link-row"><a href="/login">Already have an account? <span style="color:#a78bfa;">Sign in →</span></a></div>
</div>
<script>
function setRole(r){
  document.getElementById("roleInput").value = r;
  document.getElementById("btn-jobseeker").classList.toggle("active", r==="jobseeker");
  document.getElementById("btn-recruiter").classList.toggle("active", r==="recruiter");
  document.getElementById("regBtn").textContent = r==="recruiter" ? "Register as Recruiter" : "Register as Candidate";
  document.getElementById("extraLabel").textContent = r==="recruiter" ? "Recruiter Details" : "Candidate Details";

  var cf = document.getElementById("candidateFields");
  var rf = document.getElementById("recruiterFields");

  if(r === "recruiter"){
    cf.style.display = "none";
    rf.style.display = "block";
    rf.classList.remove("hidden");
  } else {
    cf.style.display = "block";
    rf.style.display = "none";
    rf.classList.add("hidden");
  }

  /* disable hidden fields so they don't interfere with form validation */
  document.querySelectorAll("#candidateFields input, #candidateFields select").forEach(function(el){
    el.disabled = (r === "recruiter");
  });
  document.querySelectorAll("#recruiterFields input, #recruiterFields select").forEach(function(el){
    el.disabled = (r === "jobseeker");
  });
}

document.addEventListener("DOMContentLoaded", function(){ setRole("jobseeker"); });
</script></body></html>"""


# Shared sidebar CSS
SIDEBAR_CSS = """
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'DM Sans',sans-serif;background:#08090e;color:white;display:flex;min-height:100vh;}
.sidebar{width:240px;min-width:240px;background:#0c0d15;border-right:1px solid rgba(255,255,255,0.05);display:flex;flex-direction:column;padding:24px 0;height:100vh;position:fixed;left:0;top:0;}
.logo{font-size:18px;font-weight:700;color:#a78bfa;padding:0 20px 24px;letter-spacing:-0.3px;border-bottom:1px solid rgba(255,255,255,0.05);}
.logo span{color:#6366f1;}
.nav-section{padding:20px 12px 8px;flex:1;}
.nav-label{font-size:10px;color:#2a2b3a;text-transform:uppercase;letter-spacing:1px;font-weight:600;padding:0 8px;margin-bottom:6px;}
.nav-item{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:10px;color:#4a4b5e;font-size:13px;font-weight:500;text-decoration:none;transition:all .18s;margin-bottom:2px;cursor:pointer;}
.nav-item:hover{background:#12131f;color:#9ca3c0;}
.nav-item.active{background:#16172a;color:#c4b5fd;}
.nav-item .icon{width:18px;text-align:center;font-size:15px;}
.sidebar-bottom{padding:16px 12px;border-top:1px solid rgba(255,255,255,0.05);}
.user-chip{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:10px;background:#12131f;}
.avatar{width:32px;height:32px;border-radius:8px;background:linear-gradient(135deg,#6366f1,#a78bfa);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;flex-shrink:0;}
.user-info .name{font-size:13px;font-weight:600;color:#ddd;}
.user-info .role{font-size:11px;color:#444;}
.logout-link{display:block;text-align:center;margin-top:8px;font-size:12px;color:#333;text-decoration:none;padding:8px;border-radius:8px;transition:all .2s;}
.logout-link:hover{background:#12131f;color:#f87171;}
.main{margin-left:240px;flex:1;min-height:100vh;}
.topbar{padding:20px 32px;border-bottom:1px solid rgba(255,255,255,0.04);display:flex;justify-content:space-between;align-items:center;background:#08090e;position:sticky;top:0;z-index:10;}
.topbar h1{font-size:20px;font-weight:700;letter-spacing:-0.3px;}
.topbar .sub{font-size:13px;color:#3a3b4a;margin-top:2px;}
.content{padding:28px 32px;}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;margin-bottom:28px;}
.stat-card{background:#0f1018;border-radius:16px;padding:20px;border:1px solid rgba(255,255,255,0.05);transition:border-color .2s;}
.stat-card:hover{border-color:rgba(99,102,241,0.2);}
.stat-card .s-icon{font-size:20px;margin-bottom:10px;}
.stat-card .s-val{font-size:28px;font-weight:700;letter-spacing:-1px;color:#e2e8f0;}
.stat-card .s-label{font-size:11px;color:#3a3b4a;margin-top:3px;font-weight:500;text-transform:uppercase;letter-spacing:.5px;}
.stat-card .s-hint{font-size:11px;color:#2a2b38;margin-top:6px;}
.card{background:#0f1018;border-radius:16px;border:1px solid rgba(255,255,255,0.05);margin-bottom:20px;}
.card-header{padding:18px 22px;border-bottom:1px solid rgba(255,255,255,0.04);display:flex;justify-content:space-between;align-items:center;}
.card-header h2{font-size:14px;font-weight:600;color:#c4c8d8;}
.card-body{padding:4px 0;}
table{width:100%;border-collapse:collapse;}
th{padding:10px 22px;text-align:left;font-size:11px;color:#2a2b3a;text-transform:uppercase;letter-spacing:.5px;font-weight:600;}
td{padding:12px 22px;border-top:1px solid rgba(255,255,255,0.03);font-size:13px;color:#9ca3c0;}
td strong{color:#dde1ee;}
tr:hover td{background:rgba(255,255,255,0.01);}
.badge{display:inline-flex;align-items:center;padding:3px 10px;border-radius:99px;font-size:11px;font-weight:600;}
.badge-purple{background:rgba(99,102,241,0.12);color:#818cf8;}
.badge-green{background:rgba(52,211,153,0.1);color:#34d399;}
.badge-red{background:rgba(248,113,113,0.1);color:#f87171;}
.badge-yellow{background:rgba(251,191,36,0.1);color:#fbbf24;}
.badge-blue{background:rgba(96,165,250,0.1);color:#60a5fa;}
.btn{display:inline-flex;align-items:center;gap:6px;padding:8px 16px;border-radius:10px;font-size:12px;font-weight:600;border:none;cursor:pointer;transition:all .18s;text-decoration:none;font-family:'DM Sans',sans-serif;}
.btn-primary{background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;}
.btn-primary:hover{opacity:.9;}
.btn-ghost{background:#12131f;color:#6b7280;border:1px solid rgba(255,255,255,0.05);}
.btn-ghost:hover{color:#c4b5fd;border-color:rgba(99,102,241,0.3);}
.btn-sm{padding:5px 12px;font-size:11px;}
.empty-state{text-align:center;padding:60px 40px;color:#2a2b3a;}
.empty-state .e-icon{font-size:36px;margin-bottom:12px;opacity:.4;}
.empty-state h3{font-size:15px;color:#3a3b4a;margin-bottom:6px;}
.empty-state p{font-size:13px;}
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.75);z-index:200;align-items:center;justify-content:center;backdrop-filter:blur(4px);}
.modal-overlay.show{display:flex;}
.modal{background:#0f1018;border-radius:20px;padding:28px;width:480px;max-width:92vw;border:1px solid rgba(255,255,255,0.08);}
.modal-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;}
.modal-header h2{font-size:16px;font-weight:700;color:#c4b5fd;}
.modal-close{background:none;border:none;color:#444;font-size:22px;cursor:pointer;line-height:1;}
.modal-close:hover{color:#aaa;}
.score-ring{display:inline-flex;align-items:center;justify-content:center;width:80px;height:80px;border-radius:50%;border:3px solid #6366f1;font-size:24px;font-weight:700;color:#a78bfa;}
.tag{display:inline-flex;align-items:center;padding:4px 10px;border-radius:99px;font-size:11px;margin:3px;}
.tag-g{background:rgba(52,211,153,0.1);color:#34d399;}
.tag-r{background:rgba(248,113,113,0.1);color:#f87171;}
.toast{position:fixed;bottom:24px;right:24px;background:#1a1b2e;color:#c4b5fd;padding:12px 18px;border-radius:12px;font-size:13px;font-weight:500;opacity:0;transition:opacity .3s;pointer-events:none;z-index:9999;border:1px solid rgba(99,102,241,0.3);box-shadow:0 8px 32px rgba(0,0,0,0.4);}
.toast.show{opacity:1;}
"""


CANDIDATE_DASHBOARD_HTML = """<!DOCTYPE html>
<html><head><title>My Dashboard – RecruitAI</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>""" + SIDEBAR_CSS + """
.progress-track{display:flex;align-items:center;gap:0;margin:16px 0;}
.prog-step{display:flex;flex-direction:column;align-items:center;flex:1;position:relative;}
.prog-step:not(:last-child)::after{content:'';position:absolute;top:14px;left:50%;width:100%;height:2px;background:#1a1b2e;z-index:0;}
.prog-step.done:not(:last-child)::after{background:#6366f1;}
.prog-dot{width:28px;height:28px;border-radius:50%;background:#12131f;border:2px solid #1a1b2e;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;position:relative;z-index:1;transition:all .3s;}
.prog-step.done .prog-dot{background:#6366f1;border-color:#6366f1;color:white;}
.prog-step.active .prog-dot{background:#1a1b2e;border-color:#a78bfa;color:#a78bfa;box-shadow:0 0 12px rgba(99,102,241,0.3);}
.prog-label{font-size:10px;color:#2a2b3a;margin-top:6px;text-align:center;font-weight:500;}
.prog-step.done .prog-label,.prog-step.active .prog-label{color:#6b7280;}
.quick-actions{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:20px;}
.qa-btn{background:#0f1018;border:1px solid rgba(255,255,255,0.05);border-radius:14px;padding:18px;cursor:pointer;transition:all .2s;text-decoration:none;display:flex;align-items:center;gap:12px;}
.qa-btn:hover{border-color:rgba(99,102,241,0.3);background:#12131f;}
.qa-icon{width:38px;height:38px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px;}
.qa-text .qa-title{font-size:13px;font-weight:600;color:#c4c8d8;}
.qa-text .qa-sub{font-size:11px;color:#2a2b3a;margin-top:2px;}
.upload-zone{border:2px dashed rgba(99,102,241,0.3);border-radius:14px;padding:24px;text-align:center;cursor:pointer;transition:all .2s;background:#0a0b12;position:relative;}
.upload-zone:hover,.upload-zone.drag{border-color:#6366f1;background:rgba(99,102,241,0.05);}
.upload-zone input[type=file]{position:absolute;inset:0;opacity:0;cursor:pointer;width:100%;height:100%;}
.upload-zone .uz-icon{font-size:28px;margin-bottom:6px;}
.upload-zone .uz-title{font-size:13px;font-weight:600;color:#c4b5fd;margin-bottom:3px;}
.upload-zone .uz-sub{font-size:11px;color:#3a3b4a;}
.tab-row{display:flex;gap:0;background:#0a0b12;border-radius:11px;padding:3px;border:1px solid rgba(255,255,255,0.05);margin-bottom:14px;}
.tab-btn{flex:1;padding:8px;border:none;border-radius:8px;background:transparent;color:#555;font-size:12px;font-weight:600;cursor:pointer;transition:all .2s;font-family:'DM Sans',sans-serif;}
.tab-btn.active{background:#16172a;color:#c4b5fd;}
.score-ring{display:inline-flex;align-items:center;justify-content:center;width:72px;height:72px;border-radius:50%;border:3px solid #6366f1;font-size:22px;font-weight:700;color:#a78bfa;flex-shrink:0;}
</style></head><body>

<div class="sidebar">
  <div class="logo">✦ Recruit<span>AI</span></div>
  <div class="nav-section">
    <div class="nav-label">Main</div>
    <a class="nav-item active" href="/dashboard"><span class="icon">🏠</span> Dashboard</a>
    <a class="nav-item" href="/resume-builder"><span class="icon">📄</span> Resume Builder</a>
    <a class="nav-item" href="/jobs"><span class="icon">💼</span> Browse Jobs</a>
    <a class="nav-item" href="/analytics"><span class="icon">📊</span> Analytics</a>
  </div>
  <div class="sidebar-bottom">
    <div class="user-chip">
      <div class="avatar">{{ username[0].upper() }}</div>
      <div class="user-info"><div class="name">{{ username }}</div><div class="role">Candidate</div></div>
    </div>
    <a href="/logout" class="logout-link">← Sign out</a>
  </div>
</div>

<div class="main">
  <div class="topbar">
    <div>
      <h1>Welcome back, {{ username }} 👋</h1>
      <div class="sub">Here's your job search overview</div>
    </div>
    <a href="/resume-builder" class="btn btn-primary">+ Build Resume</a>
  </div>
  <div class="content">

    <div class="stats-grid">
      <div class="stat-card"><div class="s-icon">📄</div><div class="s-val">{{ stats.downloads }}</div><div class="s-label">Resume Downloads</div></div>
      <div class="stat-card"><div class="s-icon">🎯</div><div class="s-val">{{ stats.ats_score or '—' }}</div><div class="s-label">ATS Score</div></div>
      <div class="stat-card"><div class="s-icon">📨</div><div class="s-val">{{ total_apps }}</div><div class="s-label">Applications</div></div>
      <div class="stat-card"><div class="s-icon">⭐</div><div class="s-val">{{ shortlisted }}</div><div class="s-label">Shortlisted</div></div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px;">
      <div>
        <div style="font-size:13px;font-weight:600;color:#555;margin-bottom:10px;text-transform:uppercase;letter-spacing:.5px;">Quick Actions</div>
        <div class="quick-actions">
          <a href="/resume-builder" class="qa-btn">
            <div class="qa-icon" style="background:rgba(99,102,241,0.12);">✏️</div>
            <div class="qa-text"><div class="qa-title">Edit Resume</div><div class="qa-sub">Update your profile</div></div>
          </a>
          <a href="/jobs" class="qa-btn">
            <div class="qa-icon" style="background:rgba(52,211,153,0.1);">🔍</div>
            <div class="qa-text"><div class="qa-title">Browse Jobs</div><div class="qa-sub">Find opportunities</div></div>
          </a>
          <a href="/analytics" class="qa-btn">
            <div class="qa-icon" style="background:rgba(251,191,36,0.1);">📊</div>
            <div class="qa-text"><div class="qa-title">ATS Score</div><div class="qa-sub">Check resume score</div></div>
          </a>
          <a href="/analytics" class="qa-btn">
            <div class="qa-icon" style="background:rgba(248,113,113,0.1);">🤖</div>
            <div class="qa-text"><div class="qa-title">AI Skills</div><div class="qa-sub">Get suggestions</div></div>
          </a>
        </div>
      </div>
      <div>
        <div style="font-size:13px;font-weight:600;color:#555;margin-bottom:10px;text-transform:uppercase;letter-spacing:.5px;">Application Progress</div>
        <div class="card" style="padding:20px;">
          {% if applications %}
          {% set app = applications[0] %}
          <div style="font-size:13px;font-weight:600;color:#c4c8d8;margin-bottom:4px;">{{ app.job_title }}</div>
          <div style="font-size:11px;color:#333;margin-bottom:14px;">{{ app.company }}</div>
          {% set stages = ['Applied','Reviewing','Shortlisted','Interview','Offer'] %}
          {% set status_map = {'Applied':1,'Reviewing':2,'Shortlisted':3,'Interviewing':3,'Interview':4,'Hired':5,'Offer':5} %}
          {% set current = status_map.get(app.status, 1) %}
          <div class="progress-track">
            {% for i, stage in [(1,'Applied'),(2,'Review'),(3,'Shortlist'),(4,'Interview'),(5,'Offer')] %}
            <div class="prog-step {{ 'done' if current > i else ('active' if current == i else '') }}">
              <div class="prog-dot">{{ '✓' if current > i else i }}</div>
              <div class="prog-label">{{ stage }}</div>
            </div>
            {% endfor %}
          </div>
          <div style="margin-top:10px;display:inline-flex;align-items:center;gap:6px;">
            {% if app.status == 'Applied' %}<span class="badge badge-purple">{{ app.status }}</span>
            {% elif app.status in ['Shortlisted','Reviewing'] %}<span class="badge badge-green">{{ app.status }}</span>
            {% elif app.status == 'Rejected' %}<span class="badge badge-red">{{ app.status }}</span>
            {% elif app.status in ['Interviewing','Interview'] %}<span class="badge badge-yellow">{{ app.status }}</span>
            {% else %}<span class="badge badge-blue">{{ app.status }}</span>{% endif %}
          </div>
          {% else %}
          <div style="text-align:center;padding:20px;color:#2a2b3a;">
            <div style="font-size:24px;margin-bottom:8px;">📭</div>
            <div style="font-size:13px;">No applications yet</div>
            <a href="/jobs" style="color:#a78bfa;font-size:12px;text-decoration:none;">Browse jobs →</a>
          </div>
          {% endif %}
        </div>
      </div>
    </div>

    <!-- ===== RESUME UPLOAD + ATS + AI FEEDBACK ===== -->
    <div class="card" style="margin-bottom:20px;">
      <div class="card-header">
        <h2>📄 Resume Screening &amp; AI Feedback</h2>
        <span style="font-size:11px;color:#3a3b4a;">Upload your PDF resume or use your Builder resume</span>
      </div>
      <div style="padding:20px;">
        <div class="tab-row">
          <button class="tab-btn active" id="dtab-upload" onclick="dSwitchTab('upload')">📤 Upload PDF</button>
          <button class="tab-btn" id="dtab-builder" onclick="dSwitchTab('builder')">✏️ Builder Resume</button>
        </div>

        <!-- Upload panel -->
        <div id="dpanel-upload">
          <div class="upload-zone" id="dDropZone">
            <input type="file" id="dResumeFile" accept=".pdf" onchange="dOnFileSelect(this)">
            <div class="uz-icon">📄</div>
            <div class="uz-title" id="dUzTitle">Drop your resume PDF here or click to browse</div>
            <div class="uz-sub">PDF only &nbsp;•&nbsp; Max 5MB</div>
          </div>
          <textarea id="dJobDescUpload" rows="2" placeholder="Paste a job description for tailored ATS score (optional)..."
            style="width:100%;margin-top:10px;padding:10px 13px;border:1px solid rgba(255,255,255,0.07);outline:none;border-radius:11px;background:#0a0b12;color:white;font-size:12px;font-family:'DM Sans',sans-serif;resize:vertical;"></textarea>
          <button class="btn btn-primary" style="width:100%;justify-content:center;margin-top:10px;padding:12px;" onclick="dScoreUpload()">🎯 Analyse &amp; Get AI Feedback</button>
        </div>

        <!-- Builder panel -->
        <div id="dpanel-builder" style="display:none;">
          <p style="font-size:12px;color:#3a3b4a;margin-bottom:10px;">Scores your saved Resume Builder data.</p>
          <textarea id="dJobDescBuilder" rows="2" placeholder="Paste a job description for tailored ATS score (optional)..."
            style="width:100%;padding:10px 13px;border:1px solid rgba(255,255,255,0.07);outline:none;border-radius:11px;background:#0a0b12;color:white;font-size:12px;font-family:'DM Sans',sans-serif;resize:vertical;"></textarea>
          <button class="btn btn-primary" style="width:100%;justify-content:center;margin-top:10px;padding:12px;" onclick="dScoreBuilder()">🎯 Analyse &amp; Get AI Feedback</button>
        </div>

        <!-- Results -->
        <div id="dAtsResult" style="display:none;margin-top:18px;"></div>
      </div>
    </div>

    <!-- ===== RECENT APPLICATIONS ===== -->
    <div class="card">
      <div class="card-header">
        <h2>Recent Applications</h2>
        <a href="/jobs" class="btn btn-ghost btn-sm">Browse more jobs</a>
      </div>
      <div class="card-body">
        {% if applications %}
        <table>
          <thead><tr><th>Job Title</th><th>Company</th><th>Applied</th><th>Status</th></tr></thead>
          <tbody>
          {% for app in applications %}
          <tr>
            <td><strong>{{ app.job_title }}</strong></td>
            <td>{{ app.company }}</td>
            <td>{{ app.applied_at[:10] }}</td>
            <td>
              {% if app.status == 'Applied' %}<span class="badge badge-purple">{{ app.status }}</span>
              {% elif app.status in ['Shortlisted','Reviewing'] %}<span class="badge badge-green">{{ app.status }}</span>
              {% elif app.status == 'Rejected' %}<span class="badge badge-red">{{ app.status }}</span>
              {% elif app.status in ['Interviewing','Interview'] %}<span class="badge badge-yellow">{{ app.status }}</span>
              {% else %}<span class="badge badge-blue">{{ app.status }}</span>{% endif %}
            </td>
          </tr>
          {% endfor %}
          </tbody>
        </table>
        {% else %}
        <div class="empty-state"><div class="e-icon">📭</div><h3>No applications yet</h3><p><a href="/jobs" style="color:#a78bfa;text-decoration:none;">Browse jobs to apply →</a></p></div>
        {% endif %}
      </div>
    </div>

  </div>
</div>

<script>
function dSwitchTab(t){
  document.getElementById('dtab-upload').classList.toggle('active',t==='upload');
  document.getElementById('dtab-builder').classList.toggle('active',t==='builder');
  document.getElementById('dpanel-upload').style.display=t==='upload'?'block':'none';
  document.getElementById('dpanel-builder').style.display=t==='builder'?'block':'none';
  document.getElementById('dAtsResult').style.display='none';
}

function dOnFileSelect(input){
  const f=input.files[0];
  if(f) document.getElementById('dUzTitle').textContent='✅ '+f.name;
}

const dDz=document.getElementById('dDropZone');
dDz.addEventListener('dragover',e=>{e.preventDefault();dDz.classList.add('drag');});
dDz.addEventListener('dragleave',()=>dDz.classList.remove('drag'));
dDz.addEventListener('drop',e=>{
  e.preventDefault();dDz.classList.remove('drag');
  const f=e.dataTransfer.files[0];
  if(f&&f.type==='application/pdf'){
    document.getElementById('dResumeFile').files=e.dataTransfer.files;
    document.getElementById('dUzTitle').textContent='✅ '+f.name;
  }
});

function dRenderResult(d){
  const el=document.getElementById('dAtsResult');
  el.style.display='block';
  const sc=d.score>=75?'#34d399':d.score>=50?'#fbbf24':'#f87171';
  el.innerHTML=`
    <div style="border-top:1px solid rgba(255,255,255,0.05);padding-top:18px;">
      <!-- Score row -->
      <div style="display:flex;align-items:center;gap:18px;padding:16px;background:#0a0b12;border-radius:14px;border:1px solid rgba(255,255,255,0.04);margin-bottom:16px;">
        <div class="score-ring" style="border-color:${sc};color:${sc};">${d.score}</div>
        <div style="flex:1;">
          <div style="display:flex;align-items:baseline;gap:10px;margin-bottom:5px;">
            <span style="font-size:24px;font-weight:700;color:#e2e8f0;">${d.grade||'—'}</span>
            <span style="font-size:12px;color:#555;">ATS Score / 100</span>
          </div>
          <div style="background:#12131f;border-radius:99px;height:5px;margin-bottom:6px;overflow:hidden;">
            <div style="width:${d.score}%;height:100%;border-radius:99px;background:${sc};transition:width 1s;"></div>
          </div>
          <div style="font-size:11px;color:#444;">Keyword match: <span style="color:#a78bfa;font-weight:600;">${d.keyword_match||0}%</span></div>
        </div>
      </div>
      <!-- AI Summary -->
      ${d.summary?`<div style="background:#0a0b12;border-left:3px solid #6366f1;padding:12px 14px;border-radius:10px;font-size:12px;color:#9ca3c0;line-height:1.7;margin-bottom:14px;">💬 <strong style="color:#c4b5fd;">AI Feedback:</strong> ${d.summary}</div>`:''}
      <!-- Strengths + Improvements -->
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;">
        <div style="background:#0a0b12;border-radius:12px;padding:14px;border:1px solid rgba(52,211,153,0.1);">
          <div style="font-size:11px;color:#34d399;font-weight:700;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px;">✅ Strengths</div>
          ${(d.strengths||[]).map(s=>`<div style="font-size:12px;color:#9ca3c0;margin-bottom:5px;display:flex;gap:6px;"><span style="color:#34d399;">•</span>${s}</div>`).join('')}
        </div>
        <div style="background:#0a0b12;border-radius:12px;padding:14px;border:1px solid rgba(251,191,36,0.1);">
          <div style="font-size:11px;color:#fbbf24;font-weight:700;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px;">⚠️ Improvements</div>
          ${(d.improvements||[]).map(s=>`<div style="font-size:12px;color:#9ca3c0;margin-bottom:5px;display:flex;gap:6px;"><span style="color:#fbbf24;">•</span>${s}</div>`).join('')}
        </div>
      </div>
      <!-- Sections -->
      ${(d.sections_found&&d.sections_found.length)||(d.sections_missing&&d.sections_missing.length)?`
      <div style="display:flex;gap:12px;flex-wrap:wrap;">
        ${d.sections_found&&d.sections_found.length?`<div><div style="font-size:10px;color:#2a2b3a;text-transform:uppercase;letter-spacing:.5px;margin-bottom:5px;">Detected Sections</div>${d.sections_found.map(s=>`<span style="display:inline-block;background:rgba(52,211,153,0.1);color:#34d399;padding:3px 9px;border-radius:99px;font-size:11px;margin:2px;">${s}</span>`).join('')}</div>`:''}
        ${d.sections_missing&&d.sections_missing.length?`<div><div style="font-size:10px;color:#2a2b3a;text-transform:uppercase;letter-spacing:.5px;margin-bottom:5px;">Missing Sections</div>${d.sections_missing.map(s=>`<span style="display:inline-block;background:rgba(248,113,113,0.1);color:#f87171;padding:3px 9px;border-radius:99px;font-size:11px;margin:2px;">${s}</span>`).join('')}</div>`:''}
      </div>`:''}
    </div>`;
}

async function dScoreUpload(){
  const fi=document.getElementById('dResumeFile');
  if(!fi.files.length){alert('Please select a PDF file first.');return;}
  const el=document.getElementById('dAtsResult');
  el.style.display='block';
  el.innerHTML='<p style="color:#555;padding:10px 0;font-size:13px;">🔄 Extracting resume text and running AI analysis...</p>';
  const fd=new FormData();
  fd.append('resume_pdf',fi.files[0]);
  fd.append('job_description',document.getElementById('dJobDescUpload').value);
  try{
    const res=await fetch('/api/ai/ats-score-upload',{method:'POST',body:fd});
    const d=await res.json();
    if(d.error){el.innerHTML=`<p style="color:#f87171;">${d.error}</p>`;return;}
    dRenderResult(d);
  }catch(e){el.innerHTML='<p style="color:#f87171;font-size:13px;">Analysis failed. Try again.</p>';}
}

async function dScoreBuilder(){
  const el=document.getElementById('dAtsResult');
  el.style.display='block';
  el.innerHTML='<p style="color:#555;padding:10px 0;font-size:13px;">🔄 Loading resume and running AI analysis...</p>';
  try{
    const dr=await fetch('/api/resume-builder/load');
    const resume=await dr.json();
    if(!resume||!resume.name){
      el.innerHTML='<p style="color:#f87171;font-size:13px;">No saved resume found. <a href="/resume-builder" style="color:#a78bfa;">Build your resume first →</a></p>';
      return;
    }
    const res=await fetch('/api/ai/ats-score',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({resume,job_description:document.getElementById('dJobDescBuilder').value})});
    const d=await res.json();
    dRenderResult({...d,sections_found:[],sections_missing:[]});
  }catch(e){el.innerHTML='<p style="color:#f87171;font-size:13px;">Analysis failed.</p>';}
}
</script>
</body></html>"""


RECRUITER_DASHBOARD_HTML = """<!DOCTYPE html>
<html><head><title>Recruiter Dashboard – RecruitAI</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>""" + SIDEBAR_CSS + """
.jobs-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;margin-bottom:24px;}
.job-card{background:#0f1018;border-radius:14px;padding:18px;border:1px solid rgba(255,255,255,0.05);transition:border-color .2s;}
.job-card:hover{border-color:rgba(99,102,241,0.25);}
.job-card h3{font-size:14px;font-weight:600;color:#e2e8f0;margin-bottom:3px;}
.job-card .jc-company{font-size:12px;color:#6366f1;margin-bottom:10px;}
.job-card .jc-meta{display:flex;gap:10px;flex-wrap:wrap;font-size:11px;color:#2a2b3a;margin-bottom:12px;}
.job-card .jc-actions{display:flex;gap:8px;}
.donut-wrap{display:flex;align-items:center;gap:20px;}
.donut-legend{display:flex;flex-direction:column;gap:8px;}
.legend-item{display:flex;align-items:center;gap:8px;font-size:12px;color:#6b7280;}
.legend-dot{width:10px;height:10px;border-radius:50%;}
</style></head><body>

<div class="sidebar">
  <div class="logo">✦ Recruit<span>AI</span></div>
  <div class="nav-section">
    <div class="nav-label">Recruiter</div>
    <a class="nav-item active" href="/recruiter/dashboard"><span class="icon">🏠</span> Dashboard</a>
    <a class="nav-item" href="/recruiter/post-job"><span class="icon">➕</span> Post a Job</a>
    <a class="nav-item" href="/recruiter/candidates"><span class="icon">👥</span> All Candidates</a>
  </div>
  <div class="sidebar-bottom">
    <div class="user-chip">
      <div class="avatar">{{ username[0].upper() }}</div>
      <div class="user-info"><div class="name">{{ username }}</div><div class="role">Recruiter</div></div>
    </div>
    <a href="/logout" class="logout-link">← Sign out</a>
  </div>
</div>

<div class="main">
  <div class="topbar">
    <div>
      <h1>Dashboard</h1>
      <div class="sub">Manage jobs and screen candidates</div>
    </div>
    <a href="/recruiter/post-job" class="btn btn-primary">+ Post a Job</a>
  </div>
  <div class="content">

    <div class="stats-grid">
      <div class="stat-card"><div class="s-icon">💼</div><div class="s-val">{{ total_jobs }}</div><div class="s-label">Active Jobs</div><div class="s-hint">Posted by you</div></div>
      <div class="stat-card"><div class="s-icon">👥</div><div class="s-val">{{ total_apps }}</div><div class="s-label">Total Applicants</div><div class="s-hint">Across all jobs</div></div>
      <div class="stat-card"><div class="s-icon">⭐</div><div class="s-val">{{ shortlisted }}</div><div class="s-label">Shortlisted</div><div class="s-hint">Ready to interview</div></div>
      <div class="stat-card"><div class="s-icon">✅</div><div class="s-val">{{ hired }}</div><div class="s-label">Hired</div><div class="s-hint">Successful hires</div></div>
      <div class="stat-card"><div class="s-icon">❌</div><div class="s-val">{{ rejected }}</div><div class="s-label">Rejected</div><div class="s-hint">Not a fit</div></div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 320px;gap:16px;margin-bottom:24px;">
      <div class="card">
        <div class="card-header">
          <h2>Recent Applications</h2>
          <a href="/recruiter/candidates" class="btn btn-ghost btn-sm">View all</a>
        </div>
        <div class="card-body">
          {% if recent_apps %}
          <table>
            <thead><tr><th>Candidate</th><th>Job</th><th>Applied</th><th>Status</th><th>Action</th></tr></thead>
            <tbody>
            {% for app in recent_apps %}
            <tr>
              <td><strong>{{ app.username }}</strong></td>
              <td>{{ app.job_title }}</td>
              <td>{{ app.applied_at[:10] }}</td>
              <td>
                {% if app.status == 'Applied' %}<span class="badge badge-purple">{{ app.status }}</span>
                {% elif app.status in ['Shortlisted','Reviewing'] %}<span class="badge badge-green">{{ app.status }}</span>
                {% elif app.status == 'Rejected' %}<span class="badge badge-red">{{ app.status }}</span>
                {% elif app.status in ['Interviewing'] %}<span class="badge badge-yellow">{{ app.status }}</span>
                {% elif app.status == 'Hired' %}<span class="badge badge-blue">{{ app.status }}</span>
                {% else %}<span class="badge badge-purple">{{ app.status }}</span>{% endif %}
              </td>
              <td>
                <select class="status-sel" onchange="updateStatus({{ app.id }}, this.value)"
                  style="background:#0a0b12;color:#aaa;border:1px solid rgba(255,255,255,0.08);border-radius:8px;padding:4px 8px;font-size:11px;cursor:pointer;font-family:'DM Sans',sans-serif;">
                  {% for s in ['Applied','Reviewing','Shortlisted','Interviewing','Hired','Rejected'] %}
                  <option {% if app.status == s %}selected{% endif %}>{{ s }}</option>
                  {% endfor %}
                </select>
              </td>
            </tr>
            {% endfor %}
            </tbody>
          </table>
          {% else %}
          <div class="empty-state"><div class="e-icon">📭</div><h3>No applications yet</h3><p>Post a job to start receiving applications</p></div>
          {% endif %}
        </div>
      </div>

      <div>
        <div class="card" style="margin-bottom:14px;">
          <div class="card-header"><h2>Application Status</h2></div>
          <div style="padding:20px;">
            <div class="donut-wrap">
              <canvas id="donutChart" width="110" height="110"></canvas>
              <div class="donut-legend">
                <div class="legend-item"><div class="legend-dot" style="background:#6366f1;"></div>Applied ({{ total_apps - shortlisted - hired - rejected }})</div>
                <div class="legend-item"><div class="legend-dot" style="background:#34d399;"></div>Shortlisted ({{ shortlisted }})</div>
                <div class="legend-item"><div class="legend-dot" style="background:#60a5fa;"></div>Hired ({{ hired }})</div>
                <div class="legend-item"><div class="legend-dot" style="background:#f87171;"></div>Rejected ({{ rejected }})</div>
              </div>
            </div>
          </div>
        </div>
        <div class="card">
          <div class="card-header"><h2>Quick Actions</h2></div>
          <div style="padding:12px;">
            <a href="/recruiter/post-job" class="btn btn-primary" style="width:100%;justify-content:center;margin-bottom:8px;">➕ Post New Job</a>
            <a href="/recruiter/candidates" class="btn btn-ghost" style="width:100%;justify-content:center;">👥 View All Candidates</a>
          </div>
        </div>
      </div>
    </div>

    <div style="font-size:13px;font-weight:600;color:#555;margin-bottom:12px;text-transform:uppercase;letter-spacing:.5px;">Your Job Postings</div>
    {% if jobs %}
    <div class="jobs-grid">
      {% for job in jobs %}
      <div class="job-card">
        <h3>{{ job.title }}</h3>
        <div class="jc-company">{{ job.company }}</div>
        <div class="jc-meta">
          <span>📍 {{ job.location or 'Remote' }}</span>
          <span>💼 {{ job.job_type }}</span>
          {% if job.salary %}<span>💰 {{ job.salary }}</span>{% endif %}
        </div>
        <div class="jc-actions">
          <a href="/recruiter/job/{{ job.id }}/applicants" class="btn btn-primary btn-sm">View Applicants</a>
          <span class="btn btn-ghost btn-sm">{{ job.posted_at[:10] }}</span>
        </div>
      </div>
      {% endfor %}
    </div>
    {% else %}
    <div class="empty-state" style="background:#0f1018;border-radius:16px;border:1px solid rgba(255,255,255,0.05);">
      <div class="e-icon">💼</div>
      <h3>No jobs posted yet</h3>
      <p><a href="/recruiter/post-job" class="btn btn-primary" style="margin-top:12px;display:inline-flex;">+ Post your first job</a></p>
    </div>
    {% endif %}

  </div>
</div>

<script>
async function updateStatus(appId, status) {
  await fetch('/api/recruiter/update-status',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({app_id:appId,status})});
}
// Donut chart
window.addEventListener('load',()=>{
  const canvas=document.getElementById('donutChart');
  if(!canvas)return;
  const ctx=canvas.getContext('2d');
  const total={{ total_apps }};
  const applied=Math.max(0,total-{{ shortlisted }}-{{ hired }}-{{ rejected }});
  const data=[applied,{{ shortlisted }},{{ hired }},{{ rejected }}];
  const colors=['#6366f1','#34d399','#60a5fa','#f87171'];
  const sum=data.reduce((a,b)=>a+b,0)||1;
  let start=-Math.PI/2;
  const cx=55,cy=55,r=45,inner=28;
  data.forEach((v,i)=>{
    const angle=(v/sum)*Math.PI*2;
    ctx.beginPath();ctx.moveTo(cx,cy);
    ctx.arc(cx,cy,r,start,start+angle);ctx.closePath();
    ctx.fillStyle=colors[i];ctx.fill();
    start+=angle;
  });
  ctx.beginPath();ctx.arc(cx,cy,inner,0,Math.PI*2);
  ctx.fillStyle='#0f1018';ctx.fill();
  ctx.fillStyle='#6b7280';ctx.font='bold 13px DM Sans,sans-serif';
  ctx.textAlign='center';ctx.textBaseline='middle';
  ctx.fillText(total,cx,cy);
});
</script>
</body></html>"""


CANDIDATES_LIST_HTML = """<!DOCTYPE html>
<html><head><title>All Candidates – RecruitAI</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>""" + SIDEBAR_CSS + """
</style></head><body>
<div class="sidebar">
  <div class="logo">✦ Recruit<span>AI</span></div>
  <div class="nav-section">
    <div class="nav-label">Recruiter</div>
    <a class="nav-item" href="/recruiter/dashboard"><span class="icon">🏠</span> Dashboard</a>
    <a class="nav-item" href="/recruiter/post-job"><span class="icon">➕</span> Post a Job</a>
    <a class="nav-item active" href="/recruiter/candidates"><span class="icon">👥</span> All Candidates</a>
  </div>
  <div class="sidebar-bottom">
    <div class="user-chip">
      <div class="avatar">{{ username[0].upper() }}</div>
      <div class="user-info"><div class="name">{{ username }}</div><div class="role">Recruiter</div></div>
    </div>
    <a href="/logout" class="logout-link">← Sign out</a>
  </div>
</div>
<div class="main">
  <div class="topbar">
    <div><h1>All Candidates</h1><div class="sub">{{ candidates|length }} total applications</div></div>
    <a href="/recruiter/post-job" class="btn btn-primary">+ Post a Job</a>
  </div>
  <div class="content">
    <div class="card">
      <div class="card-body">
        {% if candidates %}
        <table>
          <thead><tr><th>Candidate</th><th>Job Applied</th><th>Applied</th><th>Status</th><th>AI Screen</th><th>Action</th></tr></thead>
          <tbody>
          {% for app in candidates %}
          <tr>
            <td><strong>{{ app.username }}</strong></td>
            <td>{{ app.job_title }}</td>
            <td>{{ app.applied_at[:10] }}</td>
            <td>
              {% if app.status == 'Applied' %}<span class="badge badge-purple">{{ app.status }}</span>
              {% elif app.status in ['Shortlisted','Reviewing'] %}<span class="badge badge-green">{{ app.status }}</span>
              {% elif app.status == 'Rejected' %}<span class="badge badge-red">{{ app.status }}</span>
              {% elif app.status == 'Interviewing' %}<span class="badge badge-yellow">{{ app.status }}</span>
              {% elif app.status == 'Hired' %}<span class="badge badge-blue">{{ app.status }}</span>
              {% else %}<span class="badge badge-purple">{{ app.status }}</span>{% endif %}
            </td>
            <td><button class="btn btn-ghost btn-sm" onclick="aiScreen({{ app.id }},'{{ app.resume_json|replace("'","\\'")|replace('"','\\"') }}',{{ app.job_id }})">🤖 AI Score</button></td>
            <td>
              <select onchange="updateStatus({{ app.id }}, this.value)"
                style="background:#0a0b12;color:#aaa;border:1px solid rgba(255,255,255,0.08);border-radius:8px;padding:4px 8px;font-size:11px;cursor:pointer;font-family:'DM Sans',sans-serif;">
                {% for s in ['Applied','Reviewing','Shortlisted','Interviewing','Hired','Rejected'] %}
                <option {% if app.status == s %}selected{% endif %}>{{ s }}</option>
                {% endfor %}
              </select>
            </td>
          </tr>
          {% endfor %}
          </tbody>
        </table>
        {% else %}
        <div class="empty-state"><div class="e-icon">👥</div><h3>No candidates yet</h3><p>Post a job to start receiving applications</p></div>
        {% endif %}
      </div>
    </div>
  </div>
</div>

<div class="modal-overlay" id="modal">
  <div class="modal">
    <div class="modal-header">
      <h2>🤖 AI Screening Result</h2>
      <button class="modal-close" onclick="closeModal()">×</button>
    </div>
    <div id="modalContent"><p style="color:#444;">Analysing resume...</p></div>
  </div>
</div>

<script>
async function updateStatus(appId,status){
  await fetch('/api/recruiter/update-status',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({app_id:appId,status})});
}
async function aiScreen(appId,resumeJsonStr,jobId){
  document.getElementById('modal').classList.add('show');
  document.getElementById('modalContent').innerHTML='<p style="color:#555;padding:12px 0;">🔄 Analysing with AI...</p>';
  let resumeData={};
  try{resumeData=JSON.parse(resumeJsonStr);}catch(e){}
  try{
    const res=await fetch('/api/ai/job-match',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({resume:resumeData,job_id:jobId})});
    const d=await res.json();
    document.getElementById('modalContent').innerHTML=`
      <div style="display:flex;align-items:center;gap:16px;margin-bottom:18px;">
        <div class="score-ring">${d.match_percent}%</div>
        <div><div style="font-size:13px;color:#6b7280;">Job Match Score</div><div style="font-size:22px;font-weight:700;color:#e2e8f0;margin-top:4px;">${d.match_percent >= 70 ? 'Strong Fit' : d.match_percent >= 50 ? 'Moderate Fit' : 'Weak Fit'}</div></div>
      </div>
      <div style="margin-bottom:12px;"><div style="font-size:11px;color:#2a2b3a;margin-bottom:6px;text-transform:uppercase;letter-spacing:.5px;">✅ Matched Skills</div>${(d.matched_skills||[]).map(s=>`<span class="tag tag-g">${s}</span>`).join('')||'<span style="color:#2a2b3a;font-size:12px;">None identified</span>'}</div>
      <div style="margin-bottom:16px;"><div style="font-size:11px;color:#2a2b3a;margin-bottom:6px;text-transform:uppercase;letter-spacing:.5px;">❌ Missing Skills</div>${(d.missing_skills||[]).map(s=>`<span class="tag tag-r">${s}</span>`).join('')||'<span style="color:#2a2b3a;font-size:12px;">None</span>'}</div>
      <div style="background:#0a0b12;padding:14px;border-radius:12px;font-size:13px;color:#6b7280;line-height:1.65;border:1px solid rgba(255,255,255,0.04);">💡 ${d.recommendation||'No recommendation available'}</div>`;
  }catch(e){document.getElementById('modalContent').innerHTML='<p style="color:#f87171;">AI screening failed. Try again.</p>';}
}
function closeModal(){document.getElementById('modal').classList.remove('show');}
document.getElementById('modal').addEventListener('click',function(e){if(e.target===this)closeModal();});
</script>
</body></html>"""


POST_JOB_HTML = """<!DOCTYPE html>
<html><head><title>Post a Job – RecruitAI</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>""" + SIDEBAR_CSS + """
.form-card{background:#0f1018;border-radius:16px;padding:28px;border:1px solid rgba(255,255,255,0.05);max-width:640px;}
label{display:block;margin-bottom:5px;margin-top:14px;font-size:12px;color:#555;font-weight:500;}
input,textarea,select{width:100%;padding:11px 13px;border:1px solid rgba(255,255,255,0.07);outline:none;border-radius:11px;background:#0a0b12;color:white;font-size:14px;font-family:'DM Sans',sans-serif;transition:border-color .2s;}
input:focus,textarea:focus,select:focus{border-color:#6366f1;}
select option{background:#0f1018;}
textarea{resize:vertical;}
.row{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
</style></head><body>
<div class="sidebar">
  <div class="logo">✦ Recruit<span>AI</span></div>
  <div class="nav-section">
    <div class="nav-label">Recruiter</div>
    <a class="nav-item" href="/recruiter/dashboard"><span class="icon">🏠</span> Dashboard</a>
    <a class="nav-item active" href="/recruiter/post-job"><span class="icon">➕</span> Post a Job</a>
    <a class="nav-item" href="/recruiter/candidates"><span class="icon">👥</span> All Candidates</a>
  </div>
  <div class="sidebar-bottom">
    <div class="user-chip">
      <div class="avatar" style="font-size:13px;">R</div>
      <div class="user-info"><div class="name">Recruiter</div><div class="role">Recruiter</div></div>
    </div>
    <a href="/logout" class="logout-link">← Sign out</a>
  </div>
</div>
<div class="main">
  <div class="topbar">
    <div><h1>Post a New Job</h1><div class="sub">Fill in the details to attract the right candidates</div></div>
  </div>
  <div class="content">
    <div class="form-card">
      <form method="POST">
        <label>Job Title *</label>
        <input type="text" name="title" placeholder="e.g. Senior Python Developer" required>
        <div class="row">
          <div><label>Company Name *</label><input type="text" name="company" placeholder="e.g. Infosys" required></div>
          <div><label>Location</label><input type="text" name="location" placeholder="e.g. Mumbai / Remote"></div>
        </div>
        <div class="row">
          <div><label>Job Type</label>
            <select name="job_type">
              <option>Full-time</option><option>Part-time</option><option>Contract</option><option>Internship</option><option>Remote</option>
            </select>
          </div>
          <div><label>Salary / Package</label><input type="text" name="salary" placeholder="e.g. ₹12–18 LPA"></div>
        </div>
        <label>Required Skills (comma separated)</label>
        <input type="text" name="skills_required" placeholder="e.g. Python, Flask, SQL, REST API">
        <label>Job Description *</label>
        <textarea rows="7" name="description" placeholder="Describe the role, responsibilities, and requirements..." required></textarea>
        <div style="margin-top:20px;display:flex;gap:10px;">
          <button type="submit" class="btn btn-primary" style="padding:12px 28px;font-size:14px;">🚀 Post Job</button>
          <a href="/recruiter/dashboard" class="btn btn-ghost" style="padding:12px 20px;font-size:14px;">Cancel</a>
        </div>
      </form>
    </div>
  </div>
</div>
</body></html>"""

APPLICANTS_HTML = """<!DOCTYPE html>
<html><head><title>Applicants – RecruitAI</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>""" + SIDEBAR_CSS + """
</style></head><body>
<div class="sidebar">
  <div class="logo">✦ Recruit<span>AI</span></div>
  <div class="nav-section">
    <div class="nav-label">Recruiter</div>
    <a class="nav-item" href="/recruiter/dashboard"><span class="icon">🏠</span> Dashboard</a>
    <a class="nav-item" href="/recruiter/post-job"><span class="icon">➕</span> Post a Job</a>
    <a class="nav-item active" href="/recruiter/candidates"><span class="icon">👥</span> All Candidates</a>
  </div>
  <div class="sidebar-bottom">
    <div class="user-chip">
      <div class="avatar">R</div>
      <div class="user-info"><div class="name">Recruiter</div><div class="role">Recruiter</div></div>
    </div>
    <a href="/logout" class="logout-link">← Sign out</a>
  </div>
</div>
<div class="main">
  <div class="topbar">
    <div>
      <h1>{{ job.title }}</h1>
      <div class="sub">{{ job.company }} &nbsp;•&nbsp; {{ applicants|length }} applicant(s)</div>
    </div>
    <a href="/recruiter/dashboard" class="btn btn-ghost">← Back</a>
  </div>
  <div class="content">
    <div class="card">
      <div class="card-body">
        {% if applicants %}
        <table>
          <thead><tr><th>Candidate</th><th>Applied</th><th>Status</th><th>AI Screen</th><th>Update</th></tr></thead>
          <tbody>
          {% for app in applicants %}
          <tr>
            <td><strong>{{ app.username }}</strong></td>
            <td>{{ app.applied_at[:10] }}</td>
            <td>
              {% if app.status == 'Applied' %}<span class="badge badge-purple">{{ app.status }}</span>
              {% elif app.status in ['Shortlisted','Reviewing'] %}<span class="badge badge-green">{{ app.status }}</span>
              {% elif app.status == 'Rejected' %}<span class="badge badge-red">{{ app.status }}</span>
              {% elif app.status == 'Interviewing' %}<span class="badge badge-yellow">{{ app.status }}</span>
              {% elif app.status == 'Hired' %}<span class="badge badge-blue">{{ app.status }}</span>
              {% else %}<span class="badge badge-purple">{{ app.status }}</span>{% endif %}
            </td>
            <td><button class="btn btn-ghost btn-sm" onclick="aiScreen('{{ app.resume_json|replace("'","\\'")|replace('"','\\"') }}',{{ job.id }})">🤖 AI Score</button></td>
            <td>
              <select onchange="updateStatus({{ app.id }}, this.value)"
                style="background:#0a0b12;color:#aaa;border:1px solid rgba(255,255,255,0.08);border-radius:8px;padding:4px 8px;font-size:11px;cursor:pointer;font-family:'DM Sans',sans-serif;">
                {% for s in ['Applied','Reviewing','Shortlisted','Interviewing','Hired','Rejected'] %}
                <option {% if app.status == s %}selected{% endif %}>{{ s }}</option>
                {% endfor %}
              </select>
            </td>
          </tr>
          {% endfor %}
          </tbody>
        </table>
        {% else %}
        <div class="empty-state"><div class="e-icon">📭</div><h3>No applicants yet</h3><p>Share your job posting to attract candidates</p></div>
        {% endif %}
      </div>
    </div>
  </div>
</div>

<div class="modal-overlay" id="modal">
  <div class="modal">
    <div class="modal-header">
      <h2>🤖 AI Screening Result</h2>
      <button class="modal-close" onclick="closeModal()">×</button>
    </div>
    <div id="modalContent"></div>
  </div>
</div>

<script>
async function updateStatus(appId,status){
  await fetch('/api/recruiter/update-status',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({app_id:appId,status})});
}
async function aiScreen(resumeJsonStr,jobId){
  document.getElementById('modal').classList.add('show');
  document.getElementById('modalContent').innerHTML='<p style="color:#555;padding:12px 0;">🔄 Analysing with AI...</p>';
  let resumeData={};
  try{resumeData=JSON.parse(resumeJsonStr);}catch(e){}
  try{
    const res=await fetch('/api/ai/job-match',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({resume:resumeData,job_id:jobId})});
    const d=await res.json();
    document.getElementById('modalContent').innerHTML=`
      <div style="display:flex;align-items:center;gap:16px;margin-bottom:18px;">
        <div class="score-ring">${d.match_percent}%</div>
        <div><div style="font-size:13px;color:#6b7280;">Job Match Score</div><div style="font-size:22px;font-weight:700;color:#e2e8f0;margin-top:4px;">${d.match_percent >= 70 ? 'Strong Fit' : d.match_percent >= 50 ? 'Moderate Fit' : 'Weak Fit'}</div></div>
      </div>
      <div style="margin-bottom:12px;"><div style="font-size:11px;color:#2a2b3a;margin-bottom:6px;text-transform:uppercase;letter-spacing:.5px;">✅ Matched Skills</div>${(d.matched_skills||[]).map(s=>`<span class="tag tag-g">${s}</span>`).join('')||'<span style="color:#2a2b3a;font-size:12px;">None identified</span>'}</div>
      <div style="margin-bottom:16px;"><div style="font-size:11px;color:#2a2b3a;margin-bottom:6px;text-transform:uppercase;letter-spacing:.5px;">❌ Missing Skills</div>${(d.missing_skills||[]).map(s=>`<span class="tag tag-r">${s}</span>`).join('')||'<span style="color:#2a2b3a;font-size:12px;">None</span>'}</div>
      <div style="background:#0a0b12;padding:14px;border-radius:12px;font-size:13px;color:#6b7280;line-height:1.65;border:1px solid rgba(255,255,255,0.04);">💡 ${d.recommendation||''}</div>`;
  }catch(e){document.getElementById('modalContent').innerHTML='<p style="color:#f87171;">AI screening failed.</p>';}
}
function closeModal(){document.getElementById('modal').classList.remove('show');}
document.getElementById('modal').addEventListener('click',function(e){if(e.target===this)closeModal();});
</script>
</body></html>"""


JOB_BOARD_HTML = """<!DOCTYPE html>
<html><head><title>Browse Jobs – RecruitAI</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>""" + SIDEBAR_CSS + """
.search-bar{display:flex;gap:10px;margin-bottom:22px;}
.search-bar input{flex:1;padding:12px 16px;border:1px solid rgba(255,255,255,0.07);outline:none;border-radius:12px;background:#0f1018;color:white;font-size:14px;font-family:'DM Sans',sans-serif;}
.search-bar input:focus{border-color:#6366f1;}
.search-bar button{padding:12px 22px;border:none;border-radius:12px;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;font-weight:600;font-size:14px;cursor:pointer;font-family:'DM Sans',sans-serif;}
.job-card{background:#0f1018;border-radius:16px;padding:22px;margin-bottom:12px;border:1px solid rgba(255,255,255,0.05);transition:border-color .2s;}
.job-card:hover{border-color:rgba(99,102,241,0.3);}
.job-card .jc-top{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;}
.job-card h3{font-size:16px;font-weight:600;color:#e2e8f0;margin-bottom:3px;}
.job-card .jc-company{font-size:13px;color:#6366f1;margin-bottom:8px;}
.job-card .jc-meta{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:#2a2b3a;margin-bottom:10px;}
.job-card .jc-skills{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px;}
.skill-tag{background:rgba(99,102,241,0.1);color:#818cf8;padding:4px 10px;border-radius:99px;font-size:11px;font-weight:500;}
.jc-actions{display:flex;flex-direction:column;gap:8px;align-items:flex-end;flex-shrink:0;}
.apply-btn{padding:10px 20px;border:none;border-radius:11px;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;font-weight:700;font-size:13px;cursor:pointer;font-family:'DM Sans',sans-serif;white-space:nowrap;}
.apply-btn.applied{background:#34d399;cursor:default;}
.match-btn{padding:8px 14px;border:1px solid rgba(99,102,241,0.25);border-radius:10px;background:transparent;color:#818cf8;font-size:12px;font-weight:600;cursor:pointer;font-family:'DM Sans',sans-serif;white-space:nowrap;}
.match-btn:hover{background:rgba(99,102,241,0.1);}
.jc-desc{font-size:13px;color:#2a2b3a;line-height:1.6;margin-bottom:10px;}
</style></head><body>

<div class="sidebar">
  <div class="logo">✦ Recruit<span>AI</span></div>
  <div class="nav-section">
    <div class="nav-label">Candidate</div>
    <a class="nav-item" href="/dashboard"><span class="icon">🏠</span> Dashboard</a>
    <a class="nav-item" href="/resume-builder"><span class="icon">📄</span> Resume Builder</a>
    <a class="nav-item active" href="/jobs"><span class="icon">💼</span> Browse Jobs</a>
    <a class="nav-item" href="/analytics"><span class="icon">📊</span> Analytics</a>
  </div>
  <div class="sidebar-bottom">
    <div class="user-chip">
      <div class="avatar">C</div>
      <div class="user-info"><div class="name">Candidate</div><div class="role">Job Seeker</div></div>
    </div>
    <a href="/logout" class="logout-link">← Sign out</a>
  </div>
</div>

<div class="main">
  <div class="topbar">
    <div><h1>Browse Jobs</h1><div class="sub">Find your next opportunity</div></div>
  </div>
  <div class="content">
    <form method="GET" class="search-bar">
      <input name="q" value="{{ query }}" placeholder="Search by title, company, or skill...">
      <button type="submit">🔍 Search</button>
    </form>

    {% if jobs %}
      {% for job in jobs %}
      <div class="job-card">
        <div class="jc-top">
          <div style="flex:1;">
            <h3>{{ job.title }}</h3>
            <div class="jc-company">{{ job.company }}</div>
            <div class="jc-meta">
              <span>📍 {{ job.location or 'Not specified' }}</span>
              <span>💼 {{ job.job_type }}</span>
              {% if job.salary %}<span>💰 {{ job.salary }}</span>{% endif %}
              <span>📅 {{ job.posted_at[:10] }}</span>
            </div>
            {% if job.skills_required %}
            <div class="jc-skills">
              {% for skill in job.skills_required.split(',') %}
              <span class="skill-tag">{{ skill.strip() }}</span>
              {% endfor %}
            </div>
            {% endif %}
            {% if job.description %}
            <div class="jc-desc">{{ job.description[:180] }}{% if job.description|length > 180 %}...{% endif %}</div>
            {% endif %}
          </div>
          <div class="jc-actions">
            <button class="apply-btn" id="apply-{{ job.id }}" onclick="applyJob({{ job.id }}, this)">Apply Now</button>
            <button class="match-btn" onclick="checkMatch({{ job.id }})">🤖 Match %</button>
          </div>
        </div>
      </div>
      {% endfor %}
    {% else %}
    <div class="empty-state" style="background:#0f1018;border-radius:16px;border:1px solid rgba(255,255,255,0.05);">
      <div class="e-icon">💼</div>
      <h3>{% if query %}No jobs found for "{{ query }}"{% else %}No jobs posted yet{% endif %}</h3>
      <p>{% if query %}Try a different search term{% else %}Check back soon!{% endif %}</p>
    </div>
    {% endif %}
  </div>
</div>

<div class="toast" id="toast"></div>

<div class="modal-overlay" id="modal">
  <div class="modal">
    <div class="modal-header">
      <h2>🤖 Job Match Analysis</h2>
      <button class="modal-close" onclick="closeModal()">×</button>
    </div>
    <div id="modalContent"></div>
  </div>
</div>

<script>
function showToast(msg){const t=document.getElementById('toast');t.textContent=msg;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2800);}
async function applyJob(jobId,btn){
  if(btn.classList.contains('applied'))return;
  try{
    const res=await fetch('/api/jobs/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({job_id:jobId})});
    const d=await res.json();
    if(d.success){btn.textContent='✅ Applied';btn.classList.add('applied');showToast('✅ Application submitted!');}
    else showToast('⚠️ '+(d.error||'Failed to apply'));
  }catch(e){showToast('❌ Error applying');}
}
async function checkMatch(jobId){
  document.getElementById('modal').classList.add('show');
  document.getElementById('modalContent').innerHTML='<p style="color:#555;padding:12px 0;">🔄 Analysing match...</p>';
  try{
    const draftRes=await fetch('/api/resume-builder/load');
    const resume=await draftRes.json();
    const res=await fetch('/api/ai/job-match',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({resume,job_id:jobId})});
    const d=await res.json();
    document.getElementById('modalContent').innerHTML=`
      <div style="display:flex;align-items:center;gap:16px;margin-bottom:18px;">
        <div class="score-ring">${d.match_percent}%</div>
        <div><div style="font-size:13px;color:#6b7280;">Match with this job</div><div style="font-size:22px;font-weight:700;color:#e2e8f0;margin-top:4px;">${d.match_percent >= 70 ? 'Strong Fit ✨' : d.match_percent >= 50 ? 'Moderate Fit' : 'Needs Work'}</div></div>
      </div>
      <div style="margin-bottom:12px;"><div style="font-size:11px;color:#2a2b3a;margin-bottom:6px;text-transform:uppercase;letter-spacing:.5px;">✅ You have</div>${(d.matched_skills||[]).map(s=>`<span class="tag tag-g">${s}</span>`).join('')||'<span style="color:#2a2b3a;font-size:12px;">Load your resume first</span>'}</div>
      <div style="margin-bottom:16px;"><div style="font-size:11px;color:#2a2b3a;margin-bottom:6px;text-transform:uppercase;letter-spacing:.5px;">❌ You're missing</div>${(d.missing_skills||[]).map(s=>`<span class="tag tag-r">${s}</span>`).join('')||'<span style="color:#2a2b3a;font-size:12px;">None detected</span>'}</div>
      <div style="background:#0a0b12;padding:14px;border-radius:12px;font-size:13px;color:#6b7280;line-height:1.65;border:1px solid rgba(255,255,255,0.04);">💡 ${d.recommendation||''}</div>`;
  }catch(e){document.getElementById('modalContent').innerHTML='<p style="color:#f87171;">Match failed. Make sure your resume is saved.</p>';}
}
function closeModal(){document.getElementById('modal').classList.remove('show');}
document.getElementById('modal').addEventListener('click',function(e){if(e.target===this)closeModal();});
</script>
</body></html>"""


ANALYTICS_HTML = """<!DOCTYPE html>
<html><head><title>Analytics – RecruitAI</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>""" + SIDEBAR_CSS + """
.input-row{display:flex;gap:10px;}
.input-row input,.input-row textarea{flex:1;padding:11px 13px;border:1px solid rgba(255,255,255,0.07);outline:none;border-radius:11px;background:#0a0b12;color:white;font-size:13px;font-family:'DM Sans',sans-serif;}
.input-row input:focus,.input-row textarea:focus{border-color:#6366f1;}
.skill-tag{display:inline-flex;align-items:center;padding:5px 12px;border-radius:99px;font-size:12px;margin:3px;background:rgba(99,102,241,0.1);color:#818cf8;cursor:pointer;border:1px solid transparent;transition:all .2s;}
.skill-tag:hover{border-color:#6366f1;background:rgba(99,102,241,0.2);}
.score-circle{display:inline-flex;align-items:center;justify-content:center;width:88px;height:88px;border-radius:50%;border:3px solid #6366f1;font-size:26px;font-weight:700;color:#a78bfa;flex-shrink:0;}
.upload-zone{border:2px dashed rgba(99,102,241,0.3);border-radius:14px;padding:28px;text-align:center;cursor:pointer;transition:all .2s;background:#0a0b12;position:relative;}
.upload-zone:hover,.upload-zone.drag{border-color:#6366f1;background:rgba(99,102,241,0.05);}
.upload-zone input[type=file]{position:absolute;inset:0;opacity:0;cursor:pointer;width:100%;height:100%;}
.upload-zone .uz-icon{font-size:32px;margin-bottom:8px;}
.upload-zone .uz-title{font-size:14px;font-weight:600;color:#c4b5fd;margin-bottom:4px;}
.upload-zone .uz-sub{font-size:12px;color:#3a3b4a;}
.tab-row{display:flex;gap:0;background:#0a0b12;border-radius:12px;padding:3px;border:1px solid rgba(255,255,255,0.05);margin-bottom:16px;}
.tab-btn{flex:1;padding:9px;border:none;border-radius:9px;background:transparent;color:#555;font-size:13px;font-weight:600;cursor:pointer;transition:all .2s;font-family:'DM Sans',sans-serif;}
.tab-btn.active{background:#16172a;color:#c4b5fd;}
.prog-bar-wrap{background:#12131f;border-radius:99px;height:8px;overflow:hidden;margin-top:6px;}
.prog-bar{height:100%;border-radius:99px;background:linear-gradient(90deg,#6366f1,#a78bfa);transition:width .8s ease;}
</style></head><body>

<div class="sidebar">
  <div class="logo">✦ Recruit<span>AI</span></div>
  <div class="nav-section">
    <div class="nav-label">Candidate</div>
    <a class="nav-item" href="/dashboard"><span class="icon">🏠</span> Dashboard</a>
    <a class="nav-item" href="/resume-builder"><span class="icon">📄</span> Resume Builder</a>
    <a class="nav-item" href="/jobs"><span class="icon">💼</span> Browse Jobs</a>
    <a class="nav-item active" href="/analytics"><span class="icon">📊</span> Analytics</a>
  </div>
  <div class="sidebar-bottom">
    <div class="user-chip">
      <div class="avatar">{{ username[0].upper() }}</div>
      <div class="user-info"><div class="name">{{ username }}</div><div class="role">Job Seeker</div></div>
    </div>
    <a href="/logout" class="logout-link">← Sign out</a>
  </div>
</div>

<div class="main">
  <div class="topbar">
    <div><h1>Analytics</h1><div class="sub">Track your resume performance and job activity</div></div>
  </div>
  <div class="content">

    <div class="stats-grid">
      <div class="stat-card"><div class="s-icon">📥</div><div class="s-val">{{ stats.downloads }}</div><div class="s-label">Resume Downloads</div></div>
      <div class="stat-card"><div class="s-icon">🎯</div><div class="s-val">{{ stats.ats_score or '—' }}</div><div class="s-label">Last ATS Score</div></div>
      <div class="stat-card"><div class="s-icon">📨</div><div class="s-val">{{ applications|length }}</div><div class="s-label">Total Applications</div></div>
    </div>

    <!-- ATS SCORE CARD (full width, prominent) -->
    <div class="card" style="margin-bottom:20px;">
      <div class="card-header">
        <h2>📊 Resume ATS Score & Feedback</h2>
        <span style="font-size:11px;color:#3a3b4a;">Upload your existing resume PDF or use your builder resume</span>
      </div>
      <div style="padding:20px;">
        <div class="tab-row">
          <button class="tab-btn active" id="tab-upload" onclick="switchTab('upload')">📤 Upload PDF Resume</button>
          <button class="tab-btn" id="tab-builder" onclick="switchTab('builder')">✏️ Use Builder Resume</button>
        </div>

        <!-- Upload tab -->
        <div id="panel-upload">
          <div class="upload-zone" id="dropZone">
            <input type="file" id="resumeFile" accept=".pdf" onchange="onFileSelect(this)">
            <div class="uz-icon">📄</div>
            <div class="uz-title" id="uzTitle">Drop your resume PDF here</div>
            <div class="uz-sub">or click to browse &nbsp;•&nbsp; PDF only &nbsp;•&nbsp; Max 5MB</div>
          </div>
          <textarea id="jobDescUpload" rows="3" placeholder="Paste a job description here for a tailored score (optional)..."
            style="width:100%;margin-top:12px;padding:11px 13px;border:1px solid rgba(255,255,255,0.07);outline:none;border-radius:11px;background:#0a0b12;color:white;font-size:13px;font-family:'DM Sans',sans-serif;resize:vertical;"></textarea>
          <button class="btn btn-primary" style="width:100%;justify-content:center;margin-top:12px;padding:13px;" onclick="scoreUploadedResume()">🎯 Analyse Uploaded Resume</button>
        </div>

        <!-- Builder tab -->
        <div id="panel-builder" style="display:none;">
          <p style="font-size:13px;color:#3a3b4a;margin-bottom:12px;">Uses your saved Resume Builder data for the ATS analysis.</p>
          <textarea id="jobDescBuilder" rows="3" placeholder="Paste a job description here for a tailored score (optional)..."
            style="width:100%;padding:11px 13px;border:1px solid rgba(255,255,255,0.07);outline:none;border-radius:11px;background:#0a0b12;color:white;font-size:13px;font-family:'DM Sans',sans-serif;resize:vertical;"></textarea>
          <button class="btn btn-primary" style="width:100%;justify-content:center;margin-top:12px;padding:13px;" onclick="scoreBuilderResume()">🎯 Analyse Builder Resume</button>
        </div>

        <!-- Results area -->
        <div id="atsResult" style="margin-top:20px;display:none;"></div>
      </div>
    </div>

    <!-- AI SKILLS + APPLICATIONS ROW -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px;">
      <div class="card">
        <div class="card-header"><h2>🤖 AI Skill Suggestions</h2></div>
        <div style="padding:18px;">
          <div class="input-row" style="margin-bottom:14px;">
            <input type="text" id="jobTitleInput" placeholder="Enter job title (e.g. Data Analyst)">
            <button class="btn btn-primary" onclick="suggestSkills()">Get Skills</button>
          </div>
          <div id="suggestedSkills" style="min-height:40px;"></div>
        </div>
      </div>
      <div class="card">
        <div class="card-header"><h2>📈 Application Summary</h2></div>
        <div style="padding:18px;">
          {% set total = applications|length %}
          {% set shortlisted = applications|selectattr('status','in',['Shortlisted','Reviewing'])|list|length %}
          {% set rejected = applications|selectattr('status','equalto','Rejected')|list|length %}
          {% set hired = applications|selectattr('status','equalto','Hired')|list|length %}
          <div style="margin-bottom:14px;">
            <div style="display:flex;justify-content:space-between;font-size:12px;color:#6b7280;margin-bottom:4px;"><span>Applications Sent</span><span style="color:#c4b5fd;font-weight:600;">{{ total }}</span></div>
            <div class="prog-bar-wrap"><div class="prog-bar" style="width:100%;"></div></div>
          </div>
          <div style="margin-bottom:14px;">
            <div style="display:flex;justify-content:space-between;font-size:12px;color:#6b7280;margin-bottom:4px;"><span>Shortlisted</span><span style="color:#34d399;font-weight:600;">{{ shortlisted }}</span></div>
            <div class="prog-bar-wrap"><div class="prog-bar" style="width:{{ ((shortlisted/total*100)|int if total else 0) }}%;background:linear-gradient(90deg,#34d399,#059669);"></div></div>
          </div>
          <div style="margin-bottom:14px;">
            <div style="display:flex;justify-content:space-between;font-size:12px;color:#6b7280;margin-bottom:4px;"><span>Rejected</span><span style="color:#f87171;font-weight:600;">{{ rejected }}</span></div>
            <div class="prog-bar-wrap"><div class="prog-bar" style="width:{{ ((rejected/total*100)|int if total else 0) }}%;background:linear-gradient(90deg,#f87171,#dc2626);"></div></div>
          </div>
          <div>
            <div style="display:flex;justify-content:space-between;font-size:12px;color:#6b7280;margin-bottom:4px;"><span>Hired</span><span style="color:#60a5fa;font-weight:600;">{{ hired }}</span></div>
            <div class="prog-bar-wrap"><div class="prog-bar" style="width:{{ ((hired/total*100)|int if total else 0) }}%;background:linear-gradient(90deg,#60a5fa,#2563eb);"></div></div>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <h2>My Applications</h2>
        <a href="/jobs" class="btn btn-ghost btn-sm">Browse more →</a>
      </div>
      <div class="card-body">
        {% if applications %}
        <table>
          <thead><tr><th>Job Title</th><th>Company</th><th>Applied</th><th>Status</th></tr></thead>
          <tbody>
          {% for app in applications %}
          <tr>
            <td><strong>{{ app.job_title }}</strong></td>
            <td>{{ app.company }}</td>
            <td>{{ app.applied_at[:10] }}</td>
            <td>
              {% if app.status == 'Applied' %}<span class="badge badge-purple">{{ app.status }}</span>
              {% elif app.status in ['Shortlisted','Reviewing'] %}<span class="badge badge-green">{{ app.status }}</span>
              {% elif app.status == 'Rejected' %}<span class="badge badge-red">{{ app.status }}</span>
              {% elif app.status == 'Interviewing' %}<span class="badge badge-yellow">{{ app.status }}</span>
              {% elif app.status == 'Hired' %}<span class="badge badge-blue">{{ app.status }}</span>
              {% else %}<span class="badge badge-purple">{{ app.status }}</span>{% endif %}
            </td>
          </tr>
          {% endfor %}
          </tbody>
        </table>
        {% else %}
        <div class="empty-state"><div class="e-icon">📭</div><h3>No applications yet</h3><p><a href="/jobs" style="color:#a78bfa;text-decoration:none;">Browse jobs to apply →</a></p></div>
        {% endif %}
      </div>
    </div>

  </div>
</div>

<script>
function switchTab(t){
  document.getElementById('tab-upload').classList.toggle('active',t==='upload');
  document.getElementById('tab-builder').classList.toggle('active',t==='builder');
  document.getElementById('panel-upload').style.display=t==='upload'?'block':'none';
  document.getElementById('panel-builder').style.display=t==='builder'?'block':'none';
  document.getElementById('atsResult').style.display='none';
}

function onFileSelect(input){
  const f=input.files[0];
  if(f) document.getElementById('uzTitle').textContent='📄 '+f.name;
}

const dz=document.getElementById('dropZone');
dz.addEventListener('dragover',e=>{e.preventDefault();dz.classList.add('drag');});
dz.addEventListener('dragleave',()=>dz.classList.remove('drag'));
dz.addEventListener('drop',e=>{
  e.preventDefault();dz.classList.remove('drag');
  const f=e.dataTransfer.files[0];
  if(f&&f.type==='application/pdf'){
    document.getElementById('resumeFile').files=e.dataTransfer.files;
    document.getElementById('uzTitle').textContent='📄 '+f.name;
  }
});

function renderAtsResult(d){
  const resultEl=document.getElementById('atsResult');
  resultEl.style.display='block';
  const scoreColor=d.score>=75?'#34d399':d.score>=50?'#fbbf24':'#f87171';
  const sectionsFound=(d.sections_found||[]).map(s=>`<span class="tag tag-g">${s}</span>`).join('');
  const sectionsMissing=(d.sections_missing||[]).map(s=>`<span class="tag tag-r">${s}</span>`).join('');
  resultEl.innerHTML=`
    <div style="border-top:1px solid rgba(255,255,255,0.05);padding-top:20px;">
      <div style="display:flex;align-items:center;gap:22px;margin-bottom:20px;background:#0a0b12;padding:18px;border-radius:14px;border:1px solid rgba(255,255,255,0.04);">
        <div class="score-circle" style="border-color:${scoreColor};color:${scoreColor};">${d.score}</div>
        <div style="flex:1;">
          <div style="display:flex;align-items:baseline;gap:10px;margin-bottom:6px;">
            <div style="font-size:28px;font-weight:700;color:#e2e8f0;">${d.grade||'—'}</div>
            <div style="font-size:13px;color:#6b7280;">ATS Score / 100</div>
          </div>
          <div style="background:#12131f;border-radius:99px;height:6px;margin-bottom:8px;overflow:hidden;">
            <div style="width:${d.score}%;height:100%;border-radius:99px;background:linear-gradient(90deg,${scoreColor},${scoreColor}88);transition:width 1s ease;"></div>
          </div>
          <div style="font-size:12px;color:#555;">Keyword match: <span style="color:#a78bfa;font-weight:600;">${d.keyword_match||0}%</span></div>
        </div>
      </div>
      ${d.summary?`<div style="background:#0a0b12;padding:14px 16px;border-radius:12px;font-size:13px;color:#9ca3c0;line-height:1.7;margin-bottom:16px;border-left:3px solid #6366f1;">💬 ${d.summary}</div>`:''}
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px;">
        <div><div style="font-size:11px;color:#2a2b3a;margin-bottom:7px;text-transform:uppercase;letter-spacing:.5px;font-weight:600;">✅ Strengths</div>${(d.strengths||[]).map(s=>`<div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:6px;font-size:12px;color:#9ca3c0;"><span style="color:#34d399;margin-top:2px;">•</span>${s}</div>`).join('')}</div>
        <div><div style="font-size:11px;color:#2a2b3a;margin-bottom:7px;text-transform:uppercase;letter-spacing:.5px;font-weight:600;">⚠️ Improvements</div>${(d.improvements||[]).map(s=>`<div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:6px;font-size:12px;color:#9ca3c0;"><span style="color:#fbbf24;margin-top:2px;">•</span>${s}</div>`).join('')}</div>
      </div>
      ${sectionsFound||sectionsMissing?`<div style="display:flex;gap:16px;flex-wrap:wrap;">
        ${sectionsFound?`<div><div style="font-size:11px;color:#2a2b3a;margin-bottom:5px;text-transform:uppercase;letter-spacing:.5px;">Sections Found</div>${sectionsFound}</div>`:''}
        ${sectionsMissing?`<div><div style="font-size:11px;color:#2a2b3a;margin-bottom:5px;text-transform:uppercase;letter-spacing:.5px;">Sections Missing</div>${sectionsMissing}</div>`:''}
      </div>`:''}
    </div>`;
}

async function scoreUploadedResume(){
  const fileInput=document.getElementById('resumeFile');
  if(!fileInput.files.length){
    alert('Please select a PDF file first.');return;
  }
  const resultEl=document.getElementById('atsResult');
  resultEl.style.display='block';
  resultEl.innerHTML='<p style="color:#555;padding:12px 0;">🔄 Extracting text and calculating ATS score...</p>';
  const formData=new FormData();
  formData.append('resume_pdf',fileInput.files[0]);
  formData.append('job_description',document.getElementById('jobDescUpload').value);
  try{
    const res=await fetch('/api/ai/ats-score-upload',{method:'POST',body:formData});
    const d=await res.json();
    if(d.error){resultEl.innerHTML=`<p style="color:#f87171;">${d.error}</p>`;return;}
    renderAtsResult(d);
  }catch(e){resultEl.innerHTML='<p style="color:#f87171;font-size:13px;">Analysis failed. Try again.</p>';}
}

async function scoreBuilderResume(){
  const resultEl=document.getElementById('atsResult');
  resultEl.style.display='block';
  resultEl.innerHTML='<p style="color:#555;padding:12px 0;">🔄 Loading your resume and calculating ATS score...</p>';
  try{
    const draftRes=await fetch('/api/resume-builder/load');
    const resume=await draftRes.json();
    if(!resume||!resume.name){
      resultEl.innerHTML='<p style="color:#f87171;font-size:13px;">No saved resume found. Please build and save your resume first in the <a href="/resume-builder" style="color:#a78bfa;">Resume Builder</a>.</p>';
      return;
    }
    const res=await fetch('/api/ai/ats-score',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({resume,job_description:document.getElementById('jobDescBuilder').value})});
    const d=await res.json();
    renderAtsResult({...d,sections_found:[],sections_missing:[]});
  }catch(e){resultEl.innerHTML='<p style="color:#f87171;font-size:13px;">Score failed. Save your resume first.</p>';}
}

async function suggestSkills(){
  const title=document.getElementById('jobTitleInput').value.trim();
  if(!title)return;
  const el=document.getElementById('suggestedSkills');
  el.innerHTML='<span style="color:#2a2b3a;font-size:13px;">🔄 Getting suggestions...</span>';
  try{
    const res=await fetch('/api/ai/suggest-skills',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({job_title:title})});
    const d=await res.json();
    el.innerHTML=(d.skills||[]).map(s=>`<span class="skill-tag" title="Click to copy">✦ ${s}</span>`).join('');
    el.querySelectorAll('.skill-tag').forEach(t=>{
      t.onclick=()=>{navigator.clipboard.writeText(t.textContent.replace('✦ ',''));t.style.borderColor='#34d399';t.style.color='#34d399';}
    });
  }catch(e){el.innerHTML='<span style="color:#f87171;font-size:13px;">AI unavailable</span>';}
}
</script>
</body></html>"""


RESUME_BUILDER_HTML = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Resume Builder – RecruitAI</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'DM Sans',sans-serif;background:#08090e;color:white;display:flex;min-height:100vh;}
.sidebar{width:240px;min-width:240px;background:#0c0d15;border-right:1px solid rgba(255,255,255,0.05);display:flex;flex-direction:column;padding:24px 0;height:100vh;position:fixed;left:0;top:0;}
.logo{font-size:18px;font-weight:700;color:#a78bfa;padding:0 20px 24px;letter-spacing:-0.3px;border-bottom:1px solid rgba(255,255,255,0.05);}
.logo span{color:#6366f1;}
.nav-section{padding:20px 12px 8px;flex:1;}
.nav-label{font-size:10px;color:#2a2b3a;text-transform:uppercase;letter-spacing:1px;font-weight:600;padding:0 8px;margin-bottom:6px;}
.nav-item{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:10px;color:#4a4b5e;font-size:13px;font-weight:500;text-decoration:none;transition:all .18s;margin-bottom:2px;}
.nav-item:hover{background:#12131f;color:#9ca3c0;}
.nav-item.active{background:#16172a;color:#c4b5fd;}
.nav-item .icon{width:18px;text-align:center;font-size:15px;}
.sidebar-bottom{padding:16px 12px;border-top:1px solid rgba(255,255,255,0.05);}
.user-chip{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:10px;background:#12131f;}
.avatar{width:32px;height:32px;border-radius:8px;background:linear-gradient(135deg,#6366f1,#a78bfa);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;flex-shrink:0;}
.user-info .name{font-size:13px;font-weight:600;color:#ddd;}
.user-info .role{font-size:11px;color:#444;}
.logout-link{display:block;text-align:center;margin-top:8px;font-size:12px;color:#333;text-decoration:none;padding:8px;border-radius:8px;transition:all .2s;}
.logout-link:hover{background:#12131f;color:#f87171;}
.editor{width:380px;min-width:380px;background:#0c0d15;border-right:1px solid rgba(255,255,255,0.05);padding:20px;overflow-y:auto;height:100vh;position:fixed;left:240px;top:0;}
.preview-pane{margin-left:620px;flex:1;padding:36px 40px;overflow-y:auto;min-height:100vh;background:#0e0f18;}
.editor-title{font-size:14px;font-weight:700;color:#c4b5fd;margin-bottom:16px;letter-spacing:.3px;}
.e-card{background:#0f1018;border-radius:14px;padding:16px;margin-bottom:12px;border:1px solid rgba(255,255,255,0.04);}
.e-card h3{font-size:11px;font-weight:600;color:#6366f1;text-transform:uppercase;letter-spacing:.6px;margin-bottom:10px;}
label{display:block;margin-top:8px;margin-bottom:3px;font-size:11px;color:#444;font-weight:500;}
input,textarea{width:100%;padding:9px 11px;border:1px solid rgba(255,255,255,0.06);outline:none;border-radius:9px;background:#0a0b12;color:white;font-size:12px;font-family:'DM Sans',sans-serif;transition:border-color .2s;}
input:focus,textarea:focus{border-color:#6366f1;}
textarea{resize:vertical;}
.add-btn{width:100%;margin-top:8px;padding:8px;border:none;border-radius:9px;background:#6366f1;color:white;font-weight:600;font-size:12px;cursor:pointer;font-family:'DM Sans',sans-serif;transition:opacity .2s;}
.add-btn:hover{opacity:.9;}
.ai-btn{width:100%;margin-top:5px;padding:8px;border:1px solid rgba(99,102,241,0.3);border-radius:9px;background:transparent;color:#818cf8;font-weight:600;font-size:11px;cursor:pointer;font-family:'DM Sans',sans-serif;transition:all .2s;}
.ai-btn:hover{background:rgba(99,102,241,0.1);}
.entry{background:#0a0b12;padding:8px 11px;border-radius:9px;margin-top:5px;font-size:12px;display:flex;justify-content:space-between;align-items:center;gap:8px;border:1px solid rgba(255,255,255,0.04);}
.entry span{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#9ca3c0;}
.del-btn{background:none;border:none;color:#3a3b4a;font-size:16px;cursor:pointer;flex-shrink:0;line-height:1;padding:0 2px;}
.del-btn:hover{color:#f87171;}
.action-bar{display:flex;gap:8px;margin-top:12px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.05);}
.action-bar button{flex:1;padding:10px 6px;border:none;border-radius:10px;font-weight:700;font-size:11px;cursor:pointer;font-family:'DM Sans',sans-serif;transition:all .2s;}
.a-save{background:#12131f;color:#9ca3c0;border:1px solid rgba(255,255,255,0.06);}
.a-save:hover{border-color:#6366f1;color:#c4b5fd;}
.a-pdf{background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;}
.a-jobs{background:#16172a;color:#a78bfa;border:1px solid rgba(99,102,241,0.2);}
.a-jobs:hover{background:#1d1e35;}
.preview{max-width:780px;margin:auto;background:white;color:#111;border-radius:20px;padding:50px 55px;min-height:900px;box-shadow:0 24px 80px rgba(0,0,0,0.5);}
.resume-name{font-size:30px;font-weight:700;color:#111;letter-spacing:-0.5px;}
.resume-title{font-size:15px;color:#666;margin-top:5px;}
.resume-contact{margin-top:7px;color:#888;font-size:12px;}
.divider{border:none;border-top:2px solid #6366f1;margin:14px 0 0;}
.section{margin-top:20px;}
.section h3{color:#6366f1;margin-bottom:7px;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.6px;border-bottom:1px solid #ede9ff;padding-bottom:4px;}
.item{margin-bottom:11px;}
.item-title{font-weight:700;font-size:14px;color:#111;}
.item-sub{color:#888;margin-top:2px;font-size:12px;}
.item p{margin-top:4px;font-size:12px;line-height:1.55;color:#444;}
.skill-tag{display:inline-block;background:#ede9ff;color:#5b3fcf;padding:3px 10px;border-radius:99px;margin:3px;font-size:11px;font-weight:500;}
.toast{position:fixed;bottom:20px;right:20px;background:#1a1b2e;color:#c4b5fd;padding:11px 16px;border-radius:11px;font-weight:500;font-size:12px;opacity:0;transition:opacity .3s;pointer-events:none;z-index:9999;border:1px solid rgba(99,102,241,0.3);}
.toast.show{opacity:1;}
</style></head><body>

<div class="sidebar">
  <div class="logo">✦ Recruit<span>AI</span></div>
  <div class="nav-section">
    <div class="nav-label">Candidate</div>
    <a class="nav-item" href="/dashboard"><span class="icon">🏠</span> Dashboard</a>
    <a class="nav-item active" href="/resume-builder"><span class="icon">📄</span> Resume Builder</a>
    <a class="nav-item" href="/jobs"><span class="icon">💼</span> Browse Jobs</a>
    <a class="nav-item" href="/analytics"><span class="icon">📊</span> Analytics</a>
  </div>
  <div class="sidebar-bottom">
    <div class="user-chip">
      <div class="avatar">C</div>
      <div class="user-info"><div class="name">Candidate</div><div class="role">Job Seeker</div></div>
    </div>
    <a href="/logout" class="logout-link">← Sign out</a>
  </div>
</div>

<div class="editor">
  <div class="editor-title">✏️ Edit Resume</div>

  <div class="e-card">
    <h3>Personal Info</h3>
    <label>Full Name</label><input type="text" id="name" placeholder="Rahul Sharma" oninput="renderResume()">
    <label>Headline</label><input type="text" id="headline" placeholder="Full Stack Developer" oninput="renderResume()">
    <label>Email</label><input type="email" id="email" placeholder="you@email.com" oninput="renderResume()">
    <label>Phone</label><input type="text" id="phone" placeholder="+91 98765 43210" oninput="renderResume()">
    <label>Location</label><input type="text" id="location" placeholder="Mumbai, India" oninput="renderResume()">
    <label>Summary</label><textarea rows="3" id="summary" placeholder="Brief professional summary..." oninput="renderResume()"></textarea>
  </div>

  <div class="e-card">
    <h3>Skills</h3>
    <input type="text" id="skillInput" placeholder="Type a skill and press Enter">
    <button class="add-btn" onclick="addSkill()">+ Add Skill</button>
    <button class="ai-btn" onclick="aiSuggestSkills()">🤖 AI Suggest Skills</button>
    <div id="skillsList"></div>
  </div>

  <div class="e-card">
    <h3>Experience</h3>
    <input type="text" id="jobTitle" placeholder="Job Title">
    <input type="text" id="company" placeholder="Company Name" style="margin-top:6px;">
    <input type="text" id="jobStart" placeholder="Start (Jan 2022)" style="margin-top:6px;">
    <input type="text" id="jobEnd" placeholder="End / Present" style="margin-top:6px;">
    <textarea id="jobDesc" rows="2" placeholder="Describe your role..." style="margin-top:6px;"></textarea>
    <button class="add-btn" onclick="addExperience()">+ Add Experience</button>
    <div id="experienceList"></div>
  </div>

  <div class="e-card">
    <h3>Education</h3>
    <input type="text" id="degree" placeholder="B.Tech CSE">
    <input type="text" id="college" placeholder="College / University" style="margin-top:6px;">
    <input type="text" id="eduFrom" placeholder="From (2018)" style="margin-top:6px;">
    <input type="text" id="eduTo" placeholder="To (2022)" style="margin-top:6px;">
    <button class="add-btn" onclick="addEducation()">+ Add Education</button>
    <div id="educationList"></div>
  </div>

  <div class="e-card">
    <h3>Projects</h3>
    <input type="text" id="projectName" placeholder="Project Name">
    <input type="text" id="projectTech" placeholder="Technologies" style="margin-top:6px;">
    <textarea id="projectDesc" rows="2" placeholder="What did you build?" style="margin-top:6px;"></textarea>
    <button class="add-btn" onclick="addProject()">+ Add Project</button>
    <div id="projectList"></div>
  </div>

  <div class="e-card">
    <h3>Languages</h3>
    <input type="text" id="languageInput" placeholder="e.g. English, Hindi">
    <button class="add-btn" onclick="addLanguage()">+ Add Language</button>
    <div id="languageList"></div>
  </div>

  <div class="e-card">
    <h3>Certifications</h3>
    <input type="text" id="certInput" placeholder="e.g. AWS Certified Developer">
    <button class="add-btn" onclick="addCertification()">+ Add Certification</button>
    <div id="certList"></div>
  </div>

  <div class="action-bar">
    <button class="a-save" onclick="saveDraft()">💾 SAVE</button>
    <button class="a-pdf" onclick="downloadResume()">📄 PDF</button>
    <button class="a-jobs" onclick="window.location='/jobs'">💼 JOBS</button>
  </div>
</div>

<div class="preview-pane">
  <div class="preview" id="preview"></div>
</div>

<div class="toast" id="toast"></div>

<script>
let resume={skills:[],experiences:[],education:[],projects:[],languages:[],certifications:[]};

function showToast(msg){const t=document.getElementById('toast');t.textContent=msg;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2800);}

function renderResume(){
  const name=document.getElementById('name').value||'Your Name';
  const headline=document.getElementById('headline').value;
  const email=document.getElementById('email').value;
  const phone=document.getElementById('phone').value;
  const location=document.getElementById('location').value;
  const summary=document.getElementById('summary').value;
  const contactParts=[email,phone,location].filter(Boolean);
  let html=`<div class="resume-name">${name}</div>
    ${headline?`<div class="resume-title">${headline}</div>`:''}
    ${contactParts.length?`<div class="resume-contact">${contactParts.join(' &nbsp;•&nbsp; ')}</div>`:''}
    <hr class="divider">`;
  if(summary)html+=`<div class="section"><h3>Summary</h3><p style="font-size:12px;line-height:1.65;color:#444;">${summary}</p></div>`;
  if(resume.skills.length){html+=`<div class="section"><h3>Skills</h3>`;resume.skills.forEach(s=>{html+=`<span class="skill-tag">${s}</span>`;});html+=`</div>`;}
  if(resume.experiences.length){html+=`<div class="section"><h3>Experience</h3>`;resume.experiences.forEach(e=>{html+=`<div class="item"><div class="item-title">${e.title}</div><div class="item-sub">${e.company}${e.start?' &nbsp;|&nbsp; '+e.start+' – '+(e.end||'Present'):''}</div>${e.desc?`<p>${e.desc}</p>`:''}</div>`;});html+=`</div>`;}
  if(resume.education.length){html+=`<div class="section"><h3>Education</h3>`;resume.education.forEach(e=>{html+=`<div class="item"><div class="item-title">${e.degree}</div><div class="item-sub">${e.college}${e.from?' &nbsp;|&nbsp; '+e.from+' – '+(e.to||''):''}</div></div>`;});html+=`</div>`;}
  if(resume.projects.length){html+=`<div class="section"><h3>Projects</h3>`;resume.projects.forEach(p=>{html+=`<div class="item"><div class="item-title">${p.name}</div>${p.tech?`<div class="item-sub">${p.tech}</div>`:''} ${p.desc?`<p>${p.desc}</p>`:''}</div>`;});html+=`</div>`;}
  if(resume.languages.length){html+=`<div class="section"><h3>Languages</h3>`;resume.languages.forEach(l=>{html+=`<span class="skill-tag">${l}</span>`;});html+=`</div>`;}
  if(resume.certifications.length){html+=`<div class="section"><h3>Certifications</h3>`;resume.certifications.forEach(c=>{html+=`<div class="item" style="font-size:12px;color:#333;">• ${c}</div>`;});html+=`</div>`;}
  document.getElementById('preview').innerHTML=html;
}

async function aiSuggestSkills(){
  const title=document.getElementById('headline').value.trim()||'Software Developer';
  showToast('🤖 Getting AI suggestions...');
  try{
    const res=await fetch('/api/ai/suggest-skills',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({job_title:title})});
    const d=await res.json();
    if(d.skills){d.skills.forEach(s=>{if(!resume.skills.includes(s))resume.skills.push(s);});renderSkillList();renderResume();showToast(`✅ Added ${d.skills.length} skills!`);}
  }catch(e){showToast('❌ AI unavailable');}
}

function addSkill(){const v=document.getElementById('skillInput').value.trim();if(!v)return;resume.skills.push(v);document.getElementById('skillInput').value='';renderSkillList();renderResume();}
function renderSkillList(){document.getElementById('skillsList').innerHTML=resume.skills.map((s,i)=>`<div class="entry"><span>${s}</span><button class="del-btn" onclick="removeItem('skills',${i})">×</button></div>`).join('');}
function addExperience(){const title=document.getElementById('jobTitle').value.trim();if(!title){showToast('⚠️ Job Title required');return;}resume.experiences.push({title,company:document.getElementById('company').value,start:document.getElementById('jobStart').value,end:document.getElementById('jobEnd').value,desc:document.getElementById('jobDesc').value});['jobTitle','company','jobStart','jobEnd','jobDesc'].forEach(id=>document.getElementById(id).value='');renderExperienceList();renderResume();}
function renderExperienceList(){document.getElementById('experienceList').innerHTML=resume.experiences.map((e,i)=>`<div class="entry"><span>${e.title} @ ${e.company}</span><button class="del-btn" onclick="removeItem('experiences',${i})">×</button></div>`).join('');}
function addEducation(){const degree=document.getElementById('degree').value.trim();if(!degree){showToast('⚠️ Degree required');return;}resume.education.push({degree,college:document.getElementById('college').value,from:document.getElementById('eduFrom').value,to:document.getElementById('eduTo').value});['degree','college','eduFrom','eduTo'].forEach(id=>document.getElementById(id).value='');renderEducationList();renderResume();}
function renderEducationList(){document.getElementById('educationList').innerHTML=resume.education.map((e,i)=>`<div class="entry"><span>${e.degree} — ${e.college}</span><button class="del-btn" onclick="removeItem('education',${i})">×</button></div>`).join('');}
function addProject(){const name=document.getElementById('projectName').value.trim();if(!name){showToast('⚠️ Project name required');return;}resume.projects.push({name,tech:document.getElementById('projectTech').value,desc:document.getElementById('projectDesc').value});['projectName','projectTech','projectDesc'].forEach(id=>document.getElementById(id).value='');renderProjectList();renderResume();}
function renderProjectList(){document.getElementById('projectList').innerHTML=resume.projects.map((p,i)=>`<div class="entry"><span>${p.name}</span><button class="del-btn" onclick="removeItem('projects',${i})">×</button></div>`).join('');}
function addLanguage(){const v=document.getElementById('languageInput').value.trim();if(!v)return;resume.languages.push(v);document.getElementById('languageInput').value='';renderLanguageList();renderResume();}
function renderLanguageList(){document.getElementById('languageList').innerHTML=resume.languages.map((l,i)=>`<div class="entry"><span>${l}</span><button class="del-btn" onclick="removeItem('languages',${i})">×</button></div>`).join('');}
function addCertification(){const v=document.getElementById('certInput').value.trim();if(!v)return;resume.certifications.push(v);document.getElementById('certInput').value='';renderCertList();renderResume();}
function renderCertList(){document.getElementById('certList').innerHTML=resume.certifications.map((c,i)=>`<div class="entry"><span>${c}</span><button class="del-btn" onclick="removeItem('certifications',${i})">×</button></div>`).join('');}
function removeItem(section,index){resume[section].splice(index,1);const r={skills:renderSkillList,experiences:renderExperienceList,education:renderEducationList,projects:renderProjectList,languages:renderLanguageList,certifications:renderCertList};r[section]();renderResume();}

document.getElementById('skillInput').addEventListener('keydown',e=>{if(e.key==='Enter')addSkill();});
document.getElementById('languageInput').addEventListener('keydown',e=>{if(e.key==='Enter')addLanguage();});
document.getElementById('certInput').addEventListener('keydown',e=>{if(e.key==='Enter')addCertification();});

async function saveDraft(){
  const data={name:document.getElementById('name').value,headline:document.getElementById('headline').value,email:document.getElementById('email').value,phone:document.getElementById('phone').value,location:document.getElementById('location').value,summary:document.getElementById('summary').value,...resume};
  try{const res=await fetch('/api/resume-builder/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const j=await res.json();showToast(j.success?'✅ Saved!':'❌ Save failed');}catch(e){showToast('❌ Save failed');}
}

async function downloadResume(){
  const data={name:document.getElementById('name').value,headline:document.getElementById('headline').value,email:document.getElementById('email').value,phone:document.getElementById('phone').value,location:document.getElementById('location').value,summary:document.getElementById('summary').value,...resume};
  showToast('⏳ Generating PDF...');
  try{
    const response=await fetch('/api/resume-builder/download',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
    if(!response.ok){showToast('❌ PDF failed');return;}
    const blob=await response.blob();const url=window.URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='resume.pdf';a.click();window.URL.revokeObjectURL(url);
    showToast('✅ PDF Downloaded!');
  }catch(e){showToast('❌ PDF failed');}
}

async function loadDraft(){
  try{
    const res=await fetch('/api/resume-builder/load');const data=await res.json();
    if(!data||!data.name)return;
    ['name','headline','email','phone','location','summary'].forEach(id=>{document.getElementById(id).value=data[id]||'';});
    ['skills','experiences','education','projects','languages','certifications'].forEach(k=>{if(data[k])resume[k]=data[k];});
    renderSkillList();renderExperienceList();renderEducationList();renderProjectList();renderLanguageList();renderCertList();renderResume();
    showToast('📄 Draft loaded!');
  }catch(e){}
}
loadDraft();renderResume();
</script></body></html>"""

# ============================================================
# RUN
# ============================================================

init_tables()

if __name__ == "__main__":
    app.run(debug=True)