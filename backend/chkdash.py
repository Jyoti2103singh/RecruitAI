with open('templates/recruiter/recruiter-dashboard.html', encoding='utf-8') as f:
    lines = f.readlines()
for i, l in enumerate(lines):
    if 'quick' in l.lower() or 'action' in l.lower() or 'interview' in l.lower():
        print(i, l.rstrip())
