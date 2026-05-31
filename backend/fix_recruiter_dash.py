with open('app.py', encoding='utf-8') as f:
    content = f.read()

old = '    return render_template("dashboard_layer/recruiter-dashboard.html",\n                           total=total, hired=hired, shortlisted=shortlisted, rejected=rejected, recent=recent)'
new = '    username = session.get("user", "Recruiter")\n    return render_template("recruiter/recruiter-dashboard.html",\n                           total=total, hired=hired, shortlisted=shortlisted, rejected=rejected, recent=recent, username=username)'

if old in content:
    content = content.replace(old, new)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Fixed!')
else:
    print('Not found - check spacing')