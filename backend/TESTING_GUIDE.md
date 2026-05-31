# AI Resume Screening System - Testing & Integration Guide

## STEP 1: Environment Setup

### Install Dependencies
```bash
pip install flask pdfplumber python-docx sqlite3 python-dotenv werkzeug
```

### Create .env File
```
SECRET_KEY=lumina_secret_key_secure
DEBUG=True
UPLOAD_FOLDER=uploads
MAX_FILE_SIZE=16777216
DATABASE=screening_system.db
```

### Directory Structure
```
resume screening/
├── backend/
│   ├── app.py (or app_enhanced.py → rename to app.py)
│   ├── database_schema.py
│   ├── config.py
│   ├── utils_helpers.py
│   ├── requirements.txt
│   ├── uploads/ (auto-created)
│   ├── templates/
│   │   ├── public/
│   │   ├── authentication/
│   │   ├── dashboard_layer/
│   │   ├── resume_pipeline_layer/
│   │   ├── ai_modules/
│   │   ├── comparison_engine/
│   │   ├── talent_system/
│   │   ├── reporting_system/
│   │   ├── history/
│   │   └── results/
│   ├── static/
│   ├── utils/
│   │   └── ai_compare.py
│   ├── ai_modules/
│   │   └── ai_feedback.py
│   ├── DATA_FLOW.md
│   ├── API_DOCUMENTATION.md
│   └── screening_system.db (auto-created)
```

---

## STEP 2: Database Initialization

### Initialize Database
```python
python database_schema.py
# Output: ✓ Database schema created successfully: screening_system.db
```

This creates 12 tables with proper relationships:
- users
- resumes
- job_requirements
- screening_results
- candidates
- ai_feedback
- comparison_results
- resume_intelligence
- interview_questions
- screening_history
- candidate_tags
- analytics_summary

---

## STEP 3: Application Launch

### Start Flask Application
```bash
# Using enhanced app
python app_enhanced.py

# OR using original app (with modifications)
python app.py

# Output:
# ✓ Database schema created successfully
# WARNING in app.run() ...
# * Running on http://127.0.0.1:5000
```

---

## STEP 4: Manual Testing (Postman or cURL)

### Test 1: User Registration
```bash
curl -X POST http://localhost:5000/api/signup \
  -H "Content-Type: application/json" \
  -d '{
    "fullname": "John Recruiter",
    "username": "recruiter1",
    "email": "recruiter@company.com",
    "password": "securepass123",
    "phone": "1234567890",
    "address": "123 Main St"
  }'
```

**Expected Response:** 201 Created

---

### Test 2: User Login
```bash
# Get session cookie
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -c cookies.txt \
  -d 'username=recruiter1&password=securepass123'
```

---

### Test 3: Upload Resume
```bash
curl -X POST http://localhost:5000/api/upload-resume \
  -b cookies.txt \
  -F "file=@/path/to/resume.pdf" \
  -F "candidate_name=Jane Smith" \
  -F "candidate_email=jane@example.com"
```

**Expected Response:**
```json
{
    "success": true,
    "resume_id": 1,
    "message": "Resume uploaded successfully"
}
```

---

### Test 4: Set Job Requirements
```bash
curl -X POST http://localhost:5000/api/job-requirements \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "Senior Python Developer",
    "required_skills": "Python, Flask, SQL, AWS",
    "experience_level": "Senior",
    "description": "Looking for experienced backend developers"
  }'
```

---

### Test 5: Screen Resume
```bash
curl -X POST http://localhost:5000/api/screen-resume \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": 1,
    "job_requirement_id": 1
  }'
```

**Expected Response:**
```json
{
    "success": true,
    "screening_id": 1,
    "candidate_id": 1,
    "score": 75.5,
    "decision": "SHORTLIST",
    "feedback": {...}
}
```

---

### Test 6: Get Dashboard Stats
```bash
curl -X GET http://localhost:5000/api/dashboard-stats \
  -b cookies.txt
```

---

### Test 7: Compare Candidates
```bash
curl -X POST http://localhost:5000/api/compare-candidates \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_ids": [1, 2, 3]
  }'
```

---

### Test 8: Get Candidates
```bash
curl -X GET http://localhost:5000/api/candidates \
  -b cookies.txt
```

---

### Test 9: Get Analytics
```bash
curl -X GET http://localhost:5000/api/analytics \
  -b cookies.txt
```

---

### Test 10: Get Screening History
```bash
curl -X GET http://localhost:5000/api/screening-history \
  -b cookies.txt
```

---

## STEP 5: Data Flow Verification

### Verify Complete Flow
1. ✓ User created in `users` table
2. ✓ Resume uploaded → stored in `resumes` table
3. ✓ Resume text extracted → `extracted_text` field populated
4. ✓ Job requirements stored → `job_requirements` table
5. ✓ AI screening executed → results in `screening_results` table
6. ✓ Candidate profile created → `candidates` table
7. ✓ AI feedback stored → `ai_feedback` table
8. ✓ Action logged → `screening_history` table

### Database Queries to Verify
```sql
-- Check users
SELECT * FROM users;

-- Check resumes
SELECT id, filename, candidate_name, created_at FROM resumes;

-- Check screening results
SELECT * FROM screening_results;

-- Check candidates
SELECT id, name, score, status FROM candidates;

-- Check history
SELECT action_type, created_at FROM screening_history ORDER BY created_at DESC;

-- Check analytics
SELECT AVG(score) as avg_score, COUNT(*) as total FROM candidates;
```

---

## STEP 6: Frontend Integration

### JavaScript Integration Example

#### Upload Resume
```javascript
const uploadResume = async (formData) => {
    const response = await fetch('/api/upload-resume', {
        method: 'POST',
        body: formData  // Contains file and candidate_name/email
    });
    const data = await response.json();
    return data.resume_id;
}
```

#### Screen Resume
```javascript
const screenResume = async (resumeId, jobReqId) => {
    const response = await fetch('/api/screen-resume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            resume_id: resumeId,
            job_requirement_id: jobReqId
        })
    });
    return await response.json();
}
```

#### Get Candidates
```javascript
const getCandidates = async () => {
    const response = await fetch('/api/candidates');
    const data = await response.json();
    return data.candidates;
}
```

#### Compare Candidates
```javascript
const compareCandidates = async (candidateIds) => {
    const response = await fetch('/api/compare-candidates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidate_ids: candidateIds })
    });
    return await response.json();
}
```

---

## STEP 7: Connection Verification Checklist

### Authentication
- [ ] Signup creates user entry
- [ ] Login creates session
- [ ] Session persists across requests
- [ ] Logout clears session
- [ ] Protected routes redirect to login

### Resume Pipeline
- [ ] File upload saves to disk
- [ ] Text extracted from PDF/DOCX
- [ ] Resume stored in database
- [ ] Candidate info captured

### AI Screening
- [ ] AI feedback generated
- [ ] Score calculated (0-100)
- [ ] Decision made (HIRE/SHORTLIST/REJECT)
- [ ] Results stored in database
- [ ] Candidate profile created

### Candidate Management
- [ ] Candidates list retrieved
- [ ] Candidate profile loaded
- [ ] Candidate status updated
- [ ] Tags added/removed

### Comparison
- [ ] Multiple candidates compared
- [ ] Ranking calculated
- [ ] Results stored

### Analytics
- [ ] Statistics aggregated
- [ ] History tracked
- [ ] Reports generated

### Data Persistence
- [ ] All data persists after restart
- [ ] Relationships maintained
- [ ] Foreign keys working

---

## STEP 8: Performance Optimization

### Database Indexes (Recommended)
```sql
CREATE INDEX idx_resumes_user ON resumes(user_id);
CREATE INDEX idx_candidates_user ON candidates(user_id);
CREATE INDEX idx_screening_results_user ON screening_results(user_id);
CREATE INDEX idx_history_user ON screening_history(user_id);
```

### Query Optimization
- Use pagination for large candidate lists
- Cache dashboard statistics
- Batch process multiple resumes

---

## STEP 9: Troubleshooting

### Common Issues

**Issue:** "database is locked"
- Solution: Ensure only one process accessing database
- Close existing connections

**Issue:** "Module not found" (pdfplumber, python-docx)
- Solution: Run `pip install -r requirements.txt`

**Issue:** "No resumes uploaded"
- Solution: Check `/uploads` folder exists
- Verify file permissions

**Issue:** "Session not persisting"
- Solution: Check SECRET_KEY is set
- Verify cookies enabled in browser

**Issue:** "AI feedback not generating"
- Solution: Ensure `ai_modules/ai_feedback.py` exists
- Check import statements

---

## STEP 10: Production Deployment Checklist

- [ ] Use production database (migrate from SQLite to PostgreSQL)
- [ ] Set DEBUG=False
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS
- [ ] Implement rate limiting
- [ ] Add input validation
- [ ] Implement CORS properly
- [ ] Add logging
- [ ] Set up monitoring
- [ ] Implement backup strategy
- [ ] Use production WSGI server (Gunicorn)
- [ ] Configure reverse proxy (Nginx)

---

## STEP 11: Security Measures

### Implemented
- ✓ Password storage (NOTE: Use bcrypt in production)
- ✓ Session management
- ✓ File upload validation
- ✓ File type checking
- ✓ Max file size limit

### Recommended
- [ ] Password hashing with bcrypt
- [ ] CSRF protection
- [ ] SQL injection prevention (using parameterized queries ✓)
- [ ] XSS protection
- [ ] Rate limiting
- [ ] API authentication (JWT)
- [ ] HTTPS enforcement

---

## STEP 12: Monitoring & Logging

### Add Logging
```python
import logging

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

### Log Important Actions
- User registration/login
- Resume uploads
- Screening results
- Candidate updates
- Error events

