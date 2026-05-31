with open('app.py', encoding='utf-8') as f:
    content = f.read()

marker = '# JOBSEEKER — MY APPLICATIONS PAGE'
print('Marker found:', marker in content)
print('app.py length:', len(content))
