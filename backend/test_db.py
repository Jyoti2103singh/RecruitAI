import sqlite3
from datetime import datetime

c = sqlite3.connect('screening_system.db')
c.execute('''INSERT INTO candidates 
    (name, email, phone, skills_json, score, status, notes, created_at, updated_at, user_id) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
    ("Test User", "test@test.com", "9999999999", "[]", 75, "shortlisted", 
     "test", datetime.now().isoformat(), datetime.now().isoformat(), "admin")
)
c.commit()
print("Inserted!")
rows = c.execute("SELECT id, name, email, score, status FROM candidates").fetchall()
print("All candidates:", rows)