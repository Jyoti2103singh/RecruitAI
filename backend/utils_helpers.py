"""
Utility Functions and Helpers for AI Resume Screening System
"""
import json
import sqlite3
from datetime import datetime
from config import SCORE_CONFIG, CANDIDATE_STATUS, DECISION_MAP

def calculate_final_score(base_strengths, base_weaknesses):
    """
    Calculate final score for a resume/candidate
    
    Args:
        base_strengths: Number of identified strengths
        base_weaknesses: Number of identified weaknesses
    
    Returns:
        Final score (0-100) and decision category
    """
    score = SCORE_CONFIG['base_score']
    score += base_strengths * SCORE_CONFIG['strength_weight']
    score += base_weaknesses * SCORE_CONFIG['weakness_weight']
    
    # Clamp between 0-100
    final_score = max(0, min(100, score))
    
    # Determine decision
    if final_score >= SCORE_CONFIG['hire_threshold']:
        decision = DECISION_MAP['high']
    elif final_score >= SCORE_CONFIG['shortlist_threshold']:
        decision = DECISION_MAP['medium']
    else:
        decision = DECISION_MAP['low']
    
    return final_score, decision

def format_response(success=True, data=None, error=None, message=None):
    """
    Format API response consistently
    
    Args:
        success: Boolean indicating success
        data: Response data
        error: Error message if failed
        message: Additional message
    
    Returns:
        Dictionary formatted for JSON response
    """
    response = {
        'success': success,
        'timestamp': datetime.now().isoformat()
    }
    
    if data is not None:
        response['data'] = data
    if error:
        response['error'] = error
    if message:
        response['message'] = message
    
    return response

def parse_json_safe(json_string, default=None):
    """
    Safely parse JSON string
    
    Args:
        json_string: JSON string to parse
        default: Default value if parsing fails
    
    Returns:
        Parsed object or default
    """
    try:
        return json.loads(json_string) if json_string else default
    except (json.JSONDecodeError, TypeError):
        return default or {}

def format_candidate_data(candidate_row):
    """
    Format candidate database row for API response
    
    Args:
        candidate_row: sqlite3.Row object
    
    Returns:
        Dictionary with formatted candidate data
    """
    return {
        'id': candidate_row['id'],
        'name': candidate_row['name'],
        'email': candidate_row['email'],
        'phone': candidate_row['phone'],
        'score': candidate_row['score'],
        'status': CANDIDATE_STATUS.get(candidate_row['status'], candidate_row['status']),
        'status_key': candidate_row['status'],
        'skills': parse_json_safe(candidate_row['skills_json'], []),
        'notes': candidate_row['notes'],
        'created_at': candidate_row['created_at']
    }

def format_screening_result(result_row):
    """
    Format screening result database row for API response
    
    Args:
        result_row: sqlite3.Row object
    
    Returns:
        Dictionary with formatted result data
    """
    return {
        'id': result_row['id'],
        'score': result_row['score'],
        'decision': result_row['decision'],
        'status': result_row['status'],
        'strengths': parse_json_safe(result_row['strengths_json'], []),
        'weaknesses': parse_json_safe(result_row['weaknesses_json'], []),
        'suggestions': parse_json_safe(result_row['suggestions_json'], []),
        'created_at': result_row['created_at']
    }

def extract_skills_from_text(text):
    """
    Extract skills from resume text (simple pattern matching)
    
    Args:
        text: Resume text
    
    Returns:
        List of detected skills
    """
    from config import AI_ANALYSIS
    
    text_lower = text.lower()
    found_skills = []
    
    # Check for languages
    for lang in AI_ANALYSIS['languages']:
        if lang in text_lower:
            found_skills.append(lang.upper())
    
    # Check for frameworks
    for framework in AI_ANALYSIS['frameworks']:
        if framework in text_lower:
            found_skills.append(framework.upper())
    
    # Check for tools
    for tool in AI_ANALYSIS['tools']:
        if tool in text_lower:
            found_skills.append(tool.upper())
    
    # Check for databases
    for db in AI_ANALYSIS['databases']:
        if db in text_lower:
            found_skills.append(db.upper())
    
    return list(set(found_skills))  # Remove duplicates

def generate_analytics_summary(user_id, conn=None):
    """
    Generate comprehensive analytics summary for user
    
    Args:
        user_id: User ID
        conn: Database connection (optional, creates new if not provided)
    
    Returns:
        Dictionary with analytics summary
    """
    should_close = False
    if conn is None:
        conn = sqlite3.connect("screening_system.db")
        conn.row_factory = sqlite3.Row
        should_close = True
    
    try:
        # Basic counts
        total_resumes = conn.execute(
            "SELECT COUNT(*) as count FROM resumes WHERE user_id = ?",
            (user_id,)
        ).fetchone()['count']
        
        total_candidates = conn.execute(
            "SELECT COUNT(*) as count FROM candidates WHERE user_id = ?",
            (user_id,)
        ).fetchone()['count']
        
        # Scoring
        avg_score = conn.execute(
            "SELECT AVG(score) as avg FROM candidates WHERE user_id = ?",
            (user_id,)
        ).fetchone()['avg'] or 0
        
        max_score = conn.execute(
            "SELECT MAX(score) as max FROM candidates WHERE user_id = ?",
            (user_id,)
        ).fetchone()['max'] or 0
        
        min_score = conn.execute(
            "SELECT MIN(score) as min FROM candidates WHERE user_id = ?",
            (user_id,)
        ).fetchone()['min'] or 0
        
        # Status breakdown
        hired = conn.execute(
            "SELECT COUNT(*) as count FROM candidates WHERE user_id = ? AND status = 'hired'",
            (user_id,)
        ).fetchone()['count']
        
        rejected = conn.execute(
            "SELECT COUNT(*) as count FROM candidates WHERE user_id = ? AND status = 'rejected'",
            (user_id,)
        ).fetchone()['count']
        
        shortlisted = conn.execute(
            "SELECT COUNT(*) as count FROM candidates WHERE user_id = ? AND status = 'shortlisted'",
            (user_id,)
        ).fetchone()['count']
        
        # Calculations
        pass_rate = (shortlisted + hired) / max(total_candidates, 1) * 100
        
        return {
            'total_resumes': total_resumes,
            'total_candidates': total_candidates,
            'avg_score': round(avg_score, 2),
            'max_score': max_score,
            'min_score': min_score,
            'hired': hired,
            'rejected': rejected,
            'shortlisted': shortlisted,
            'pass_rate': round(pass_rate, 2)
        }
    
    finally:
        if should_close:
            conn.close()

def validate_file_extension(filename, allowed_extensions={'pdf', 'docx', 'doc'}):
    """
    Validate if file has allowed extension
    
    Args:
        filename: Filename to validate
        allowed_extensions: Set of allowed extensions
    
    Returns:
        Boolean indicating if file is allowed
    """
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in allowed_extensions

print("✓ Utility functions loaded successfully")
