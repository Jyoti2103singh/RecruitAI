import pathlib, textwrap
content = open('templates/recruiter/interviews.html', encoding='utf-8').read() if pathlib.Path('templates/recruiter/interviews.html').exists() else ''
print('exists:', bool(content))
