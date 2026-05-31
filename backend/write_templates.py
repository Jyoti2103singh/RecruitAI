cat > /mnt/user-data/outputs/write_templates.py << 'PYEOF'
import os

BASE = r'C:\Users\anura\OneDrive\Desktop\resume screening\backend\templates'

# Shared UI Elements (Sidebar Styles and Base layouts)
COMMON_STYLE = """
  :root{--bg:#0a0a0f;--bg2:#111118;--bg3:#1a1a24;--border:rgba(255,255,255,0.07);--purple:#7c5cbf;--purple-bright:#9b7de8;--purple-glow:rgba(124,92,191,0.25);--text:#e8e8f0;--muted:#6b6b80;--success:#4ade80;--danger:#f87171;--warn:#fbbf24;}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;min-height:100vh;display:flex;}
  .sidebar{width:220px;min-height:100vh;background:var(--bg2);border-right:1px solid var(--border);display:flex;flex-direction:column;padding:24px 0;position:fixed;left:0;top:0;bottom:0;}
  .logo{padding:0 20px 28px;font-family:'Space Mono',monospace;font-size:18px;font-weight:700;color:var(--purple-bright);}
  .logo span{color:var(--text);}
  .nav-section{padding:0 12px;margin-bottom:8px;}
  .nav-label{font-size:10px;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted);padding:0 8px;margin-bottom:6px;}
  .nav-item{display:flex;align-items:center;gap:10px;padding:9px 12px;border-radius:8px;color:var(--muted);font-size:13.5px;text-decoration:none;transition:all 0.2s;margin-bottom:2px;}
  .nav-item:hover{background:var(--bg3);color:var(--text);}
  .nav-item.active{background:var(--purple-glow);color:var(--purple-bright);}
  .nav-item i{width:16px;text-align:center;font-size:13px;}
  .sidebar-bottom{margin-top:auto;padding:0 12px;}
  .logout-btn{display:flex;align-items:center;gap:10px;padding:9px 12px;border-radius:8px;color:var(--danger);font-size:13.5px;text-decoration:none;transition:all 0.2s;width:100%;background:none;border:none;cursor:pointer;font-family:inherit;}
  .logout-btn:hover{background:rgba(248,113,113,0.08);}
  .main{margin-left:220px;flex:1;padding:40px;}
  .page-header{margin-bottom:28px;}
  .page-header h1{font-family:'Space Mono',monospace;font-size:26px;font-weight:700;}
  .page-header p{color:var(--muted);margin-top:6px;font-size:14px;}
  .stats-row{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:28px;}
  .stat-card{background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:18px 20px;}
  .stat-val{font-family:'Space Mono',monospace;font-size:26px;font-weight:700;margin-bottom:4px;}
  .stat-label{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:0.8px;}
  .stat-val.purple{color:var(--purple-bright);}.stat-val.green{color:var(--success);}.stat-val.yellow{color:var(--warn);}
  .table-wrap{background:var(--bg2);border:1px solid var(--border);border-radius:12px;overflow:hidden;}
  table{width:100%;border-collapse:collapse;}
  th{background:var(--bg3);padding:11px 14px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--muted);font-weight:600;border-bottom:1px solid var(--border);}
  td{padding:12px 14px;font-size:13px;border-bottom:1px solid var(--border);vertical-align:middle;}
  tr:last-child td{border-bottom:none;}
  tr:hover td{background:rgba(255,255,255,0.015);}
  .empty{text-align:center;padding:48px 20px;color:var(--muted);}
  .empty i{font-size:32px;margin-bottom:12px;display:block;}
  #toast{position:fixed;bottom:24px;right:24px;background:var(--bg3);border:1px solid var(--border);border-radius:10px;padding:12px 18px;font-size:13px;box-shadow:0 8px 32px rgba(0,0,0,0.5);transform:translateY(80px);opacity:0;transition:all 0.3s cubic-bezier(.34,1.56,.64,1);z-index:999;}
  #toast.show{transform:translateY(0);opacity:1;}
  #toast.success{border-color:var(--success);color:var(--success);}
  #toast.error{border-color:var(--danger);color:var(--danger);}
  .panel{background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:22px;}
  .panel-title{font-family:'Space Mono',monospace;font-size:14px;font-weight:700;margin-bottom:18px;color:var(--purple-bright);}
  .form-group{margin-bottom:14px;}
  label{display:block;font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--muted);font-weight:600;margin-bottom:6px;}
  input,select,textarea{width:100%;background:var(--bg3);border:1px solid var(--border);border-radius:8px;color:var(--text);font-family:'DM Sans',sans-serif;font-size:13.5px;padding:9px 12px;outline:none;transition:border-color 0.2s;}
  input:focus,select:focus,textarea:focus{border-color:var(--purple);}
  .btn-primary{width:100%;padding:11px;background:var(--purple);color:#fff;border:none;border-radius:9px;font-family:'Space Mono',monospace;font-size:13px;font-weight:700;cursor:pointer;transition:all 0.2s;}
  .btn-primary:hover{background:var(--purple-bright);box-shadow:0 4px 20px var(--purple-glow);}
  .hidden{display:none;}
"""

NAV_TEMPLATE = """
  <div class="sidebar">
    <div class="logo">AI<span>Screen</span></div>
    <div class="nav-section">
      <div class="nav-label">Navigation</div>
      <a href="/dashboard" class="nav-item {dash_act}"><i class="fa-solid fa-chart-pie"></i>Dashboard</a>
      <a href="/jobs" class="nav-item {jobs_act}"><i class="fa-solid fa-briefcase"></i>Jobs</a>
      <a href="/interviews" class="nav-item {int_act}"><i class="fa-solid fa-calendar-days"></i>Interviews</a>
    </div>
    <div class="sidebar-bottom">
      <a href="/logout" class="logout-btn"><i class="fa-solid fa-right-from-bracket"></i>Logout</a>
    </div>
  </div>
"""

# ==================== 1. DASHBOARD TEMPLATE ====================
DASHBOARD_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Dashboard | AIScreen</title>
<link href="https://googleapis.com" rel="stylesheet"/>
<link href="https://cloudflare.com" rel="stylesheet"/>
<style>
  {COMMON_STYLE}
  .dash-grid {{display:grid; grid-template-columns: 2fr 1fr; gap:20px;}}
  .match-badge {{font-family:'Space Mono',monospace; font-weight:700; padding:3px 8px; border-radius:6px; font-size:12px;}}
  .match-high {{background:rgba(74,222,128,0.1); color:var(--success);}}
  .match-mid {{background:rgba(251,191,36,0.1); color:var(--warn);}}
</style>
</head>
<body>
  {NAV_TEMPLATE.format(dash_act="active", jobs_act="", int_act="")}
  <div class="main">
    <div class="page-header">
      <h1>Overview Dashboard</h1>
      <p>Real-time analytics and resume assessment metrics pipeline.</p>
    </div>
    
    <div class="stats-row">
      <div class="stat-card"><div class="stat-val purple" id="stat-jobs">0</div><div class="stat-label">Active Jobs</div></div>
      <div class="stat-card"><div class="stat-val green" id="stat-resumes">0</div><div class="stat-label">Processed Resumes</div></div>
      <div class="stat-card"><div class="stat-val yellow" id="stat-avg">0%</div><div class="stat-label">Average Match Score</div></div>
    </div>

    <div class="dash-grid">
      <div>
        <h3 style="margin-bottom:14px; font-family:'Space Mono'; font-size:15px;">Recent Top Candidates</h3>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Name</th><th>Position Target</th><th>Match Score</th></tr></thead>
            <tbody id="candidates-tbody"></tbody>
          </table>
        </div>
      </div>
      <div class="panel">
        <div class="panel-title">System Status</div>
        <p style="font-size:13px; color:var(--muted); line-height:1.6;">AI Scoring Engine running optimized. Model context mapping complete with automated extraction loops active.</p>
      </div>
    </div>
  </div>
  <script>
    async function loadDash() {{
      try {{
        const [j, c] = await Promise.all([fetch('/api/jobs'), fetch('/api/candidates')]);
        const jobs = await j.json(); const candidates = await c.json();
        
        document.getElementById('stat-jobs').textContent = jobs.length;
        document.getElementById('stat-resumes').textContent = candidates.length;
        
        if(candidates.length > 0) {{
          const avg = Math.round(candidates.reduce((acc, curr) => acc + curr.score, 0) / candidates.length);
          document.getElementById('stat-avg').textContent = avg + '%';
        }}
        
        const tbody = document.getElementById('candidates-tbody');
        if(candidates.length === 0) {{
          tbody.innerHTML = '<tr><td colspan="3" class="empty">No parsed profiles detected.</td></tr>';
          return;
        }}
        tbody.innerHTML = candidates.slice(0,5).map(can => `
          <tr>
            <td style="font-weight:600;">${{can.name}}</td>
            <td>${{can.job_title}}</td>
            <td><span class="match-badge ${{can.score >= 75 ? 'match-high':'match-mid'}}">${{can.score}}%</span></td>
          </tr>
        `).join('');
      }} catch {{}}
    }}
    window.addEventListener('DOMContentLoaded', loadDash);
  </script>
</body>
</html>
"""

# ==================== 2. JOBS MANAGEMENT TEMPLATE ====================
JOBS_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Job Board Config | AIScreen</title>
<link href="https://googleapis.com" rel="stylesheet"/>
<link href="https://cloudflare.com" rel="stylesheet"/>
<style>
  {COMMON_STYLE}
  .jobs-layout {{display:grid; grid-template-columns: 1fr 340px; gap:20px;}}
</style>
</head>
<body>
  {NAV_TEMPLATE.format(dash_act="", jobs_act="active", int_act="")}
  <div class="main">
    <div class="page-header">
      <h1>Job Vacancies</h1>
      <p>Create and inspect application thresholds for automated screening.</p>
    </div>

    <div class="jobs-layout">
      <div class="table-wrap">
