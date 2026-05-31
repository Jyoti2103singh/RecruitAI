import re

# =========================
# PATCH app.py
# =========================
with open('app.py', encoding='utf-8') as f:
    app = f.read()

# Add imports
if 'import smtplib' not in app:
    app = app.replace('from flask import', 'import smtplib\nfrom email.mime.text import MIMEText\nfrom flask import')

# Add notifications API
if '/api/notifications' not in app:
    notif_code = '''

# =========================
# NOTIFICATIONS API
# =========================
@app.route("/api/notifications")
def notifications():
    return jsonify([
        {"title":"New candidate applied","time":"2 min ago"},
        {"title":"Interview booked","time":"10 min ago"},
        {"title":"Resume screening complete","time":"25 min ago"}
    ])

# =========================
# EMAIL HELPER
# =========================
def send_email(to_email, subject, body):
    try:
        sender = "your_email@gmail.com"
        password = "your_app_password"

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = to_email

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender, password)
        server.send_message(msg)
        server.quit()

        print("Email sent")
    except Exception as e:
        print("Email failed:", e)

# =========================
# APPLY WITH RESUME BUILDER
# =========================
@app.route("/api/resume-builder/apply", methods=["POST"])
def apply_with_resume():
    data = request.json

    send_email(
        data.get("email", "test@example.com"),
        "Application Submitted",
        f"You successfully applied for {data.get('job','a job')}."
    )

    return jsonify({
        "success": True,
        "message": "Application submitted successfully"
    })
'''
    app += notif_code

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app)

print("app.py patched")

# =========================
# PATCH recruiter dashboard
# =========================
dash_path = 'templates/recruiter/recruiter-dashboard.html'

with open(dash_path, encoding='utf-8') as f:
    dash = f.read()

if '/recruiter/interviews' not in dash:
    insert_after = '<a class="action-btn" href="/candidates">'
    new_btn = '''
<a class="action-btn" href="/recruiter/interviews">
  <div class="icon">🎤</div>
  <div>
    <div>Interviews</div>
    <small>Manage Slots</small>
  </div>
</a>

<a class="action-btn" href="/candidates">
'''
    dash = dash.replace(insert_after, new_btn)

with open(dash_path, 'w', encoding='utf-8') as f:
    f.write(dash)

print("Dashboard patched")

# =========================
# PATCH resume-builder.html
# =========================
resume_path = 'templates/jobseeker/resume-builder.html'

with open(resume_path, encoding='utf-8') as f:
    resume = f.read()

if 'applyBuiltResume' not in resume:
    apply_btn = '''
<button onclick="applyBuiltResume()" style="
margin-top:12px;
width:100%;
padding:12px;
border:none;
border-radius:10px;
background:#7c5cf5;
color:white;
font-weight:700;
cursor:pointer;
">
Apply With Resume
</button>

<script>
async function applyBuiltResume(){
    const payload = {
        email: "candidate@example.com",
        job: "Frontend Developer"
    };

    const res = await fetch('/api/resume-builder/apply',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify(payload)
    });

    const data = await res.json();
    alert(data.message || "Applied");
}
</script>
'''

    resume = resume.replace('</body>', apply_btn + '\n</body>')

with open(resume_path, 'w', encoding='utf-8') as f:
    f.write(resume)

print("Resume Builder patched")

print("\\nALL FEATURES ADDED SUCCESSFULLY")
