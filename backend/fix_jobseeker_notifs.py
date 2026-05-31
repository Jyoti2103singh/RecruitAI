with open('templates/jobseeker/dashboard.html', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Add notification bell to header
old = '''  <div class="page-header">
    <div class="page-title">Job Seeker <span>Dashboard</span></div>
  </div>'''

new = '''  <div class="page-header">
    <div class="page-title">Job Seeker <span>Dashboard</span></div>
    <div style="position:relative;">
      <button class="notif-btn" onclick="toggleNotifications()" id="notifBtn"
        style="background:var(--surface);border:1px solid var(--border);color:var(--text);padding:8px 14px;border-radius:8px;cursor:pointer;font-size:1rem;position:relative;">
        🔔
        <div id="notifDot" style="display:none;position:absolute;top:4px;right:4px;width:8px;height:8px;background:var(--red);border-radius:50%;"></div>
      </button>
      <div id="notifPanel" style="display:none;position:fixed;top:70px;right:32px;width:340px;background:var(--surface);border:1px solid var(--border);border-radius:14px;z-index:500;box-shadow:0 20px 60px rgba(0,0,0,0.5);max-height:440px;overflow-y:auto;">
        <div style="padding:16px 20px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;">
          <div style="font-size:0.95rem;font-weight:700;">🔔 Notifications</div>
          <button onclick="markAllRead()" style="font-size:0.75rem;color:var(--accent);background:none;border:none;cursor:pointer;">Mark all read</button>
        </div>
        <div id="notifList"><div style="padding:40px 20px;text-align:center;color:var(--muted);font-size:0.85rem;">No notifications yet</div></div>
      </div>
    </div>
  </div>'''

if old in content:
    content = content.replace(old, new)
    print("Fix 1 applied: notification bell added")
else:
    print("Fix 1 NOT found")

# Fix 2: Show AI match score in my applications
old2 = '''            Applied ${formatDate(app.created_at)}
            ${app.ats_score ? ` · ATS Score: <span style="color:var(--accent)">${app.ats_score}</span>` : ''}'''

new2 = '''            Applied ${formatDate(app.created_at)}
            ${app.ats_score ? ` · ATS Score: <span style="color:var(--accent)">${app.ats_score}</span>` : ''}
            ${app.ai_match_score ? ` · AI Match: <span style="color:${app.ai_match_score>=70?'var(--green)':app.ai_match_score>=45?'var(--yellow)':'var(--red)'}">${app.ai_match_score}%</span>` : ''}
            ${app.ai_match_summary ? `<div style="margin-top:6px;font-size:0.78rem;color:var(--muted);font-style:italic;">${app.ai_match_summary}</div>` : ''}'''

if old2 in content:
    content = content.replace(old2, new2)
    print("Fix 2 applied: AI match score in applications")
else:
    print("Fix 2 NOT found")

# Fix 3: Add notification functions before helpers
old3 = '  // ── HELPERS ──'
new3 = '''  // ── NOTIFICATIONS ──
  async function loadNotifications() {
    try {
      const res = await fetch('/api/notifications');
      const notifs = await res.json();
      const unread = notifs.filter(n => !n.is_read).length;
      document.getElementById('notifDot').style.display = unread > 0 ? 'block' : 'none';
      const list = document.getElementById('notifList');
      if (!notifs.length) {
        list.innerHTML = '<div style="padding:40px 20px;text-align:center;color:var(--muted);font-size:0.85rem;">No notifications yet</div>';
        return;
      }
      list.innerHTML = notifs.map(n => `
        <div style="padding:14px 20px;border-bottom:1px solid var(--border);background:${n.is_read?'':'rgba(124,106,245,0.06)'};">
          <div style="font-size:0.85rem;font-weight:600;margin-bottom:3px;">${n.title}</div>
          <div style="font-size:0.78rem;color:var(--muted);line-height:1.4;">${n.body}</div>
          <div style="font-size:0.7rem;color:var(--muted);margin-top:4px;font-family:var(--font-mono);">${formatDate(n.created_at)}</div>
        </div>
      `).join('');
    } catch(e) { console.warn('Notifications error', e); }
  }

  async function toggleNotifications() {
    const panel = document.getElementById('notifPanel');
    const isOpen = panel.style.display === 'block';
    panel.style.display = isOpen ? 'none' : 'block';
    if (!isOpen) {
      await fetch('/api/notifications/read', { method: 'POST' });
      document.getElementById('notifDot').style.display = 'none';
    }
  }

  async function markAllRead() {
    await fetch('/api/notifications/read', { method: 'POST' });
    document.getElementById('notifDot').style.display = 'none';
    loadNotifications();
  }

  document.addEventListener('click', e => {
    if (!e.target.closest('#notifPanel') && !e.target.closest('#notifBtn')) {
      const panel = document.getElementById('notifPanel');
      if (panel) panel.style.display = 'none';
    }
  });

  // ── HELPERS ──'''

if old3 in content:
    content = content.replace(old3, new3)
    print("Fix 3 applied: notification functions")
else:
    print("Fix 3 NOT found")

# Fix 4: Call loadNotifications on init
old4 = '  renderNotifications();'
new4 = '  loadNotifications();'

if old4 in content:
    content = content.replace(old4, new4)
    print("Fix 4 applied: init call updated")
else:
    # add it to the init block
    old4b = '  loadMyApplications();'
    new4b = '  loadMyApplications();\n  loadNotifications();'
    if old4b in content:
        content = content.replace(old4b, new4b, 1)
        print("Fix 4 applied: loadNotifications added to init")
    else:
        print("Fix 4 NOT found")

with open('templates/jobseeker/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")