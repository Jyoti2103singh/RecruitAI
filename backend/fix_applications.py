with open('templates/recruiter/applications.html', encoding='utf-8') as f:
    content = f.read()

old = "onclick=\"updateStatus('+a.id+','shortlisted')\""
new = "onclick=\"updateStatus('+a.id+',\\'shortlisted\\')\""
content = content.replace(old, new)

old2 = "onclick=\"updateStatus('+a.id+','rejected')\""
new2 = "onclick=\"updateStatus('+a.id+',\\'rejected\\')\""
content = content.replace(old2, new2)

with open('templates/recruiter/applications.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed!')