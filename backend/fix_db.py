import sqlite3

conn = sqlite3.connect("screening_system.db")

# Add missing ats_score column
try:
    conn.execute("ALTER TABLE applications ADD COLUMN ats_score INTEGER DEFAULT 0")
    conn.commit()
    print("ats_score column added!")
except Exception as e:
    print("Note:", e)

conn.close()
print("Done!")