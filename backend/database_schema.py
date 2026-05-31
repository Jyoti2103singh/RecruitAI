"""
Complete Database Schema for AI Resume Screening System
Creates all necessary tables with proper relationships
"""
import sqlite3
import os

def create_all_tables():
    """Initialize all database tables"""
    
    db_path = "screening_system.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # ========================================
    # 1. USERS TABLE
    # ========================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        address TEXT,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # ========================================
    # 2. RESUMES TABLE
    # ========================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        upload_path TEXT NOT NULL,
        original_text TEXT NOT NULL,
        extracted_text TEXT,
        candidate_name TEXT,
        candidate_email TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)
    
    # ========================================
    # 3. JOB REQUIREMENTS TABLE
    # ========================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS job_requirements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        job_title TEXT NOT NULL,
        required_skills TEXT,
        experience_level TEXT,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)
    
    # ========================================
    # 4. SCREENING RESULTS TABLE
    # ========================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS screening_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resume_id INTEGER NOT NULL,
        job_requirement_id INTEGER,
        user_id INTEGER NOT NULL,
        score REAL,
        status TEXT,
        strengths_json TEXT,
        weaknesses_json TEXT,
        suggestions_json TEXT,
        decision TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resume_id) REFERENCES resumes(id),
        FOREIGN KEY (job_requirement_id) REFERENCES job_requirements(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)
    
    # ========================================
    # 5. CANDIDATES TABLE
    # ========================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resume_id INTEGER,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        skills_json TEXT,
        score REAL,
        status TEXT DEFAULT 'applied',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resume_id) REFERENCES resumes(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)
    
    # ========================================
    # 6. AI FEEDBACK TABLE
    # ========================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resume_id INTEGER,
        candidate_id INTEGER,
        strengths_json TEXT,
        weaknesses_json TEXT,
        suggestions_json TEXT,
        insight TEXT,
        score REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resume_id) REFERENCES resumes(id),
        FOREIGN KEY (candidate_id) REFERENCES candidates(id)
    )
    """)
    
    # ========================================
    # 7. COMPARISON RESULTS TABLE
    # ========================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comparison_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        candidate_ids_json TEXT,
        ranking_json TEXT,
        top_candidate_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)
    
    # ========================================
    # 8. RESUME INTELLIGENCE TABLE
    # ========================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resume_intelligence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resume_id INTEGER,
        skills_json TEXT,
        experience_gaps_json TEXT,
        career_trajectory_json TEXT,
        insights_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resume_id) REFERENCES resumes(id)
    )
    """)
    
    # ========================================
    # 9. INTERVIEW QUESTIONS TABLE
    # ========================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interview_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER,
        questions_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (candidate_id) REFERENCES candidates(id)
    )
    """)
    
    # ========================================
    # 10. SCREENING HISTORY TABLE
    # ========================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS screening_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        action_type TEXT,
        resume_id INTEGER,
        candidate_id INTEGER,
        details_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (resume_id) REFERENCES resumes(id),
        FOREIGN KEY (candidate_id) REFERENCES candidates(id)
    )
    """)
    
    # ========================================
    # 11. CANDIDATE TAGS TABLE
    # ========================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidate_tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER NOT NULL,
        tag_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (candidate_id) REFERENCES candidates(id)
    )
    """)
    
    # ========================================
    # 12. ANALYTICS SUMMARY TABLE
    # ========================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analytics_summary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total_resumes INTEGER,
        total_candidates INTEGER,
        avg_score REAL,
        pass_rate REAL,
        top_skills_json TEXT,
        summary_data_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print(f"✓ Database schema created successfully: {db_path}")
    return db_path

if __name__ == "__main__":
    create_all_tables()
