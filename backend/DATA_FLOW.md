# AI Resume Screening System - Complete Data Flow Architecture

## System Overview
```
USER → AUTHENTICATION → DASHBOARD → RESUME PIPELINE → AI PROCESSING → RESULTS → REPORTING
                                                ↓
                                        CANDIDATE COMPARISON
                                        TALENT MANAGEMENT
                                        HISTORY TRACKING
```

---

## 1. AUTHENTICATION FLOW
```
Landing Page (landing_page_1.html)
    ↓
    → Signup: POST /signup 
        → Store in `users` table
        → Redirect to /login
    
    → Login: POST /login
        → Verify credentials from `users` table
        → Create session
        → Redirect to /dashboard
    
    → Logout: /logout
        → Clear session
        → Redirect to /
```

**Database Table: `users`**
- id, fullname, username, email, phone, address, password

---

## 2. DASHBOARD FLOW
```
/dashboard (requires auth)
    ↓
Recruiter Dashboard displays:
    → Resume Upload Counter (from `resumes` table)
    → Screening Results Summary (from `screening_results` table)
    → Candidate Pool (from `candidates` table)
    → Recent History (from `screening_history` table)
    → Quick Actions Links
```

---

## 3. RESUME PIPELINE FLOW
```
STEP 1: Upload Resume
POST /api/upload-resume
    ↓
    → Receive file (PDF/DOCX)
    → Extract text using pdfplumber/python-docx
    → Store in `resumes` table (filename, original_text, user_id, timestamp)
    → Save file to /uploads folder
    → Return resume_id to frontend

STEP 2: Initial Processing
/upload-2
    ↓
    → Display job requirements form
    → User inputs: job_title, required_skills, experience_level
    → Store in `job_requirements` table

STEP 3: AI Screening
POST /api/screen-resume
    ↓
    → Retrieve resume from `resumes` table
    → Retrieve job requirements from `job_requirements` table
    → Run AI analysis (ai_feedback module)
    → Generate screening result
    → Store in `screening_results` table
    → Store in `screening_history` table for tracking
    → Return to /results

STEP 4: Display Results
/results
    ↓
    → Fetch from `screening_results` table
    → Display: score, strengths, weaknesses, suggestions
    → Offer actions: Accept, Reject, Shortlist
```

---

## 4. AI MODULES FLOW

### 4A. AI Feedback Module
```
/api/ai-feedback (POST)
    ↓
    Resume Text → generate_ai_feedback()
    ↓
    Returns:
    {
        "strengths": [...],
        "weaknesses": [...],
        "suggestions": [...],
        "insight": "...",
        "score": X
    }
    ↓
    Store in `ai_feedback` table
    ↓
    Display on /ai-feedback page
```

### 4B. Candidate Comparison
```
/api/compare-candidates (POST)
    ↓
    [candidate_id_1, candidate_id_2, ...] from `candidates` table
    ↓
    compare_candidates() function from utils/ai_compare.py
    ↓
    Returns:
    {
        "total_candidates": X,
        "top_candidate": {...},
        "ranking": [{...}, ...]
    }
    ↓
    Store in `comparison_results` table
    ↓
    Display on /compare-candidates page
```

### 4C. Resume Intelligence
```
/api/resume-intelligence (POST)
    ↓
    Resume ID → Fetch from `resumes` table
    ↓
    Advanced analysis (parsing skills, experience gaps, career trajectory)
    ↓
    Returns: detailed insights
    ↓
    Store in `resume_intelligence` table
```

### 4D. AI Interviewer
```
/api/ai-interviewer (POST)
    ↓
    Candidate ID → Fetch from `candidates` table
    ↓
    Generate interview questions based on resume
    ↓
    Store in `interview_questions` table
    ↓
    Display on /ai-interviewer page
```

---

## 5. COMPARISON ENGINE FLOW

### 5A. Comparative AI
```
/api/comparative-ai (POST)
    ↓
    Multiple resume IDs from `resumes` table
    ↓
    Run compare_candidates()
    ↓
    Store in `comparison_results` table
    ↓
    Display comparison matrix
```

### 5B. Market Insights
```
/api/market-insights (GET)
    ↓
    Aggregate data from `screening_results` table
    ↓
    Analyze: salary ranges, skill demand, experience trends
    ↓
    Generate insights
    ↓
    Display on /market-insights page
```

### 5C. Ranking Analysis
```
/api/ranking-analysis (GET)
    ↓
    Fetch top candidates from `candidates` table (sorted by score)
    ↓
    Generate ranking visualization
    ↓
    Display on /ranking-analysis page
```

---

## 6. TALENT SYSTEM FLOW

### 6A. Candidates List
```
/api/candidates (GET)
    ↓
    Fetch all from `candidates` table
    ↓
    Filter by: status, score, skills
    ↓
    Display paginated list on /candidates page
```

### 6B. Candidate Profile
```
/api/candidate/<id> (GET)
    ↓
    Fetch from `candidates` table
    ↓
    Fetch related data:
        → Resume from `resumes` table
        → Screening results from `screening_results` table
        → AI feedback from `ai_feedback` table
        → Interview history from `interview_questions` table
    ↓
    Display comprehensive profile on /candidate-profile page
    
POST /api/candidate/<id>/update
    ↓
    Update candidate status, tags, notes
    ↓
    Store in `candidates` table
```

### 6C. Candidate Tags
```
/api/candidate-tags (GET/POST)
    ↓
    Manage tags in `candidate_tags` table
    ↓
    Link to `candidates` table via candidate_id
    ↓
    Allow filtering by tags
```

---

## 7. HISTORY TRACKING FLOW

```
/api/screening-history (GET)
    ↓
    Fetch from `screening_history` table
    ↓
    Show timeline of:
        → Uploads
        → Screening events
        → Actions taken
        → Changes made
    ↓
    Display on /history page
```

---

## 8. REPORTING & ANALYTICS FLOW

### 8A. Analytics Dashboard
```
/api/analytics (GET)
    ↓
    Query data from:
        → `screening_results` - for scoring trends
        → `candidates` - for pool analysis
        → `screening_history` - for activity metrics
        → `comparison_results` - for comparison insights
    ↓
    Generate KPIs:
        → Total resumes screened
        → Pass rate
        → Top skills required
        → Average scores
        → Candidate pool composition
    ↓
    Display on /analytics page
```

### 8B. Download Report
```
/api/download-report (GET/POST)
    ↓
    Fetch data for report period
    ↓
    Format as PDF/Excel
    ↓
    Send as download on /download-report page
```

---

## Database Schema

### Table: users
```
id | fullname | username | email | phone | address | password | created_at
```

### Table: resumes
```
id | user_id | filename | original_text | extracted_text | upload_path | 
candidate_name | candidate_email | created_at
```

### Table: job_requirements
```
id | user_id | job_title | required_skills | experience_level | 
description | created_at
```

### Table: screening_results
```
id | resume_id | job_requirement_id | score | status | strengths_json | 
weaknesses_json | suggestions_json | decision | created_at
```

### Table: candidates
```
id | resume_id | user_id | name | email | phone | skills_json | 
score | status (applied/shortlisted/rejected/hired) | notes | created_at
```

### Table: ai_feedback
```
id | resume_id | strengths_json | weaknesses_json | suggestions_json | 
insight | score | created_at
```

### Table: comparison_results
```
id | candidate_ids_json | ranking_json | top_candidate_json | created_at
```

### Table: resume_intelligence
```
id | resume_id | skills_json | experience_gaps_json | career_trajectory_json | 
insights_json | created_at
```

### Table: interview_questions
```
id | candidate_id | questions_json | created_at
```

### Table: screening_history
```
id | user_id | action_type | resume_id | candidate_id | details_json | created_at
```

### Table: candidate_tags
```
id | candidate_id | tag_name | created_at
```

---

## Data Flow Sequence Diagram

```
User Login
    ↓
    [session created]
    ↓
Dashboard View
    ↓
    [query: users.db for stats]
    ↓
Upload Resume Page
    ↓
    POST /api/upload-resume (file)
        ↓
        [stored in resumes table]
        ↓
Job Requirements Page
    ↓
    POST /api/job-requirements (form)
        ↓
        [stored in job_requirements table]
        ↓
AI Screening
    ↓
    POST /api/screen-resume (resume_id, job_req_id)
        ↓
        [AI analysis → stored in screening_results]
        ↓
Results Display
    ↓
    GET /api/screening-results/<id>
        ↓
        [fetch from screening_results table]
        ↓
Candidate Management
    ↓
    [move to candidates table with status]
    ↓
Comparison
    ↓
    [load multiple candidates, run comparison]
        ↓
Analytics & Reporting
    ↓
    [aggregate all data for insights]
```

---

## API Endpoints Summary

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| POST | /api/signup | Register new user | No |
| POST | /api/login | User login | No |
| POST | /api/logout | User logout | Yes |
| GET | /api/dashboard-stats | Get dashboard data | Yes |
| POST | /api/upload-resume | Upload resume file | Yes |
| POST | /api/job-requirements | Set job requirements | Yes |
| POST | /api/screen-resume | Run AI screening | Yes |
| GET | /api/screening-results/<id> | Fetch screening result | Yes |
| POST | /api/ai-feedback | Generate AI feedback | Yes |
| POST | /api/compare-candidates | Compare multiple candidates | Yes |
| GET | /api/candidates | List all candidates | Yes |
| GET | /api/candidate/<id> | Get candidate profile | Yes |
| POST | /api/candidate/<id>/update | Update candidate | Yes |
| GET | /api/candidate-tags | Get all tags | Yes |
| POST | /api/candidate-tags | Add tag to candidate | Yes |
| GET | /api/screening-history | Get activity history | Yes |
| GET | /api/analytics | Get analytics data | Yes |
| POST | /api/download-report | Generate downloadable report | Yes |
| POST | /api/market-insights | Get market trends | Yes |
| GET | /api/ranking-analysis | Get candidate rankings | Yes |

---

## Key Integration Points

1. **Upload → Screening**: resume_id passed from upload to screening
2. **Screening → Results**: screening_results used for both display and candidate pool
3. **Candidates → Comparison**: candidate_id list fed to comparison engine
4. **Results → History**: All actions logged to screening_history
5. **Analytics**: All tables feed into analytics calculations
6. **AI Modules**: All output stored in respective tables for persistence

