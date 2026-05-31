import re
with open('app.py', encoding='utf-8') as f:
    content = f.read()

# Find notification route
notif = re.findall(r'@app\.route.*?notifications.*?\n', content)
print('NOTIFICATION ROUTES:', notif)

# Find dashboard quick actions route
dash = re.findall(r'@app\.route.*?dashboard.*?\n', content)
print('DASHBOARD ROUTES:', dash)

# Check if smtplib/email imports exist
print('SMTP:', 'smtplib' in content)
print('JSON import:', 'import json' in content)
