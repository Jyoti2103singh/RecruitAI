import sqlite3
conn = sqlite3.connect('screening_system.db')
conn.row_factory = sqlite3.Row
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
for t in tables:
    print(t['name'])
    cols = conn.execute(f"PRAGMA table_info({t['name']})").fetchall()
    for c in cols:
        print('  ', c['name'], c['type'])
conn.close()