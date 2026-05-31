"""
Configuration and Environment Setup for AI Resume Screening System
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'lumina_secret_key_secure')
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    DATABASE = 'screening_system.db'
    DEBUG = os.getenv('DEBUG', 'True') == 'True'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    DATABASE = 'test.db'

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}

# Scoring configuration
SCORE_CONFIG = {
    'base_score': 50,
    'strength_weight': 10,
    'weakness_weight': -5,
    'hire_threshold': 80,
    'shortlist_threshold': 60
}

# Decision mappings
DECISION_MAP = {
    'high': 'HIRE',
    'medium': 'SHORTLIST',
    'low': 'REJECT'
}

# Status values
CANDIDATE_STATUS = {
    'applied': 'Recently Applied',
    'screening_completed': 'Screening Complete',
    'shortlisted': 'Shortlisted',
    'rejected': 'Rejected',
    'hired': 'Hired',
    'interview': 'Interview Scheduled'
}

# AI Analysis parameters
AI_ANALYSIS = {
    'languages': ['python', 'java', 'javascript', 'c++', 'c#', 'go', 'rust'],
    'frameworks': ['flask', 'django', 'react', 'angular', 'vue', 'express'],
    'tools': ['docker', 'kubernetes', 'jenkins', 'git', 'aws', 'azure', 'gcp'],
    'databases': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis']
}

print("✓ Configuration loaded successfully")
