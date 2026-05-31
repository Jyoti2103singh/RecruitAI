import sys
sys.path.insert(0, '.')
exec(open('app.py', encoding='utf-8').read().split('if __name__')[0])

result = call_gemini('Return this exact JSON with no markdown: {"test": "ok"}')
print('Gemini says:', result)