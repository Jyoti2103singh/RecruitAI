import re

# Read working key from test_gemini.py
with open('test_gemini.py', 'r') as f:
    test_content = f.read()

match = re.search(r'api_key = "([^"]+)"', test_content)
if not match:
    print("ERROR: Could not find key in test_gemini.py")
    exit()

working_key = match.group(1)
print(f"Working key found: {working_key[:10]}...{working_key[-4:]}")

# Update app.py
with open('app.py', 'r', encoding='utf-8') as f:
    app_content = f.read()

# Replace any AIza key in app.py
new_content = re.sub(r'api_key = "[^"]+"', f'api_key = "{working_key}"', app_content)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Done! app.py updated with working key.")

# Verify
with open('app.py') as f:
    for i, line in enumerate(f):
        if working_key in line:
            print(f"Confirmed on line {i+1}: {line.strip()}")