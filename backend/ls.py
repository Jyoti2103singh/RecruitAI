import os

# Check what folders exist
for root, dirs, files in os.walk('templates'):
    for f in files:
        print(os.path.join(root, f))
