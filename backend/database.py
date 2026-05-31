import sqlite3

# =========================================
# CREATE DATABASE CONNECTION
# =========================================

conn = sqlite3.connect("users.db")

cursor = conn.cursor()

# =========================================
# CREATE USERS TABLE
# =========================================

cursor.execute("""

CREATE TABLE IF NOT EXISTS users (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    fullname TEXT,

    username TEXT UNIQUE,

    email TEXT,

    phone TEXT,

    address TEXT,

    password TEXT

)

""")

conn.commit()

conn.close()

print("Database and users table created successfully.")