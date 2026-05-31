import os

# Fix 1: copy interview.html to interviews.html
with open('templates/recruiter/interview.html', encoding='utf-8') as f:
    content = f.read()
with open('templates/recruiter/interviews.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('interviews.html created from interview.html')

# Fix 2: patch app.py dashboard_layer references
with open('app.py', encoding='utf-8') as f:
    app = f.read()

fixed = app.replace('dashboard_layer/recruiter-dashboard.html', 'recruiter/recruiter-dashboard.html')
fixed = fixed.replace('dashboard_layer/', 'recruiter/')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(fixed)
print('app.py patched')

# Verify
checks = ['recruiter/recruiter-dashboard.html', 'dashboard_layer']
for c in checks:
    print(c, 'FOUND' if c in open('app.py', encoding='utf-8').read() else 'GONE')
