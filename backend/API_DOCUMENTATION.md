# AI Resume Screening System - Complete API Documentation

## Base URL
```
http://localhost:5000
```

---

## 1. AUTHENTICATION ENDPOINTS

### 1.1 User Sign Up
**Endpoint:** `POST /api/signup`

**Request:**
```json
{
    "fullname": "John Doe",
    "username": "johndoe",
    "email": "john@example.com",
    "phone": "1234567890",
    "address": "123 Main St",
    "password": "securepassword"
}
```

**Response:**
```json
{
    "success": true,
    "message": "User registered successfully",
    "redirect": "/login"
}
```

---

### 1.2 User Login
**Endpoint:** `POST /api/login` | `POST /login`

**Request (Form Data):**
```
username: johndoe
password: securepassword
```

**Response:**
```json
{
    "success": true,
    "message": "Login successful",
    "redirect": "/dashboard"
}
```

**Session Created:** `session['user'] = username`

---

### 1.3 User Logout
**Endpoint:** `GET /logout`

**Response:**
```json
{
    "success": true,
    "message": "Logged out successfully",
    "redirect": "/"
}
```

---

## 2. DASHBOARD ENDPOINTS

### 2.1 Get Dashboard Statistics
**Endpoint:** `GET /api/dashboard-stats`

**Authentication:** Required (session)

**Response:**
```json
{
    "total_resumes": 15,
    "total_candidates": 12,
    "avg_score": 72.5,
    "shortlisted": 5
}
```

---

## 3. RESUME PIPELINE ENDPOINTS

### 3.1 Upload Resume
**Endpoint:** `POST /api/upload-resume`

**Authentication:** Required (session)

**Request (multipart/form-data):**
```
file: [PDF/DOCX file]
candidate_name: "Jane Smith"
candidate_email: "jane@example.com"
```

**Response:**
```json
{
    "success": true,
    "resume_id": 1,
    "message": "Resume uploaded successfully"
}
```

**Files Created:**
- Saved in `/uploads` folder
- Text extracted and stored in database

---

### 3.2 Set Job Requirements
**Endpoint:** `POST /api/job-requirements`

**Authentication:** Required (session)

**Request:**
```json
{
    "job_title": "Senior Python Developer",
    "required_skills": "Python, Flask, SQL, AWS",
    "experience_level": "Senior",
    "description": "Looking for experienced developers"
}
```

**Response:**
```json
{
    "success": true,
    "job_requirement_id": 1,
    "message": "Job requirements saved"
}
```

---

### 3.3 Screen Resume (AI Analysis)
**Endpoint:** `POST /api/screen-resume`

**Authentication:** Required (session)

**Request:**
```json
{
    "resume_id": 1,
    "job_requirement_id": 1
}
```

**Response:**
```json
{
    "success": true,
    "screening_id": 1,
    "candidate_id": 1,
    "score": 82.5,
    "decision": "HIRE",
    "feedback": {
        "strengths": [
            "Strong Python programming knowledge",
            "Database and SQL understanding"
        ],
        "weaknesses": [
            "No cloud platform experience detected"
        ],
        "suggestions": [
            "Build and deploy real-world full-stack projects"
        ],
        "insight": "Strong candidate for mid-level roles"
    },
    "message": "Screening completed"
}
```

---

## 4. RESULTS ENDPOINTS

### 4.1 Get Screening Results
**Endpoint:** `GET /api/screening-results/<screening_id>`

**Authentication:** Required (session)

**Response:**
```json
{
    "id": 1,
    "score": 82.5,
    "decision": "HIRE",
    "strengths": ["Python", "SQL", "Flask"],
    "weaknesses": ["No AWS"],
    "suggestions": ["Learn AWS"]
}
```

---

## 5. AI MODULES ENDPOINTS

### 5.1 Generate AI Feedback
**Endpoint:** `POST /api/ai-feedback`

**Authentication:** Required (session)

**Request:**
```json
{
    "resume_id": 1
}
```

**Response:**
```json
{
    "success": true,
    "feedback": {
        "strengths": [...],
        "weaknesses": [...],
        "suggestions": [...],
        "insight": "Strong candidate"
    }
}
```

---

### 5.2 Compare Candidates
**Endpoint:** `POST /api/compare-candidates`

**Authentication:** Required (session)

**Request:**
```json
{
    "candidate_ids": [1, 2, 3]
}
```

**Response:**
```json
{
    "success": true,
    "comparison": {
        "total_candidates": 3,
        "top_candidate": {
            "name": "Jane Smith",
            "score": 85,
            "decision": "HIRE"
        },
        "ranking": [
            {
                "name": "Jane Smith",
                "score": 85,
                "decision": "HIRE"
            },
            {
                "name": "John Doe",
                "score": 72,
                "decision": "SHORTLIST"
            }
        ]
    }
}
```

---

## 6. TALENT SYSTEM ENDPOINTS

### 6.1 Get All Candidates
**Endpoint:** `GET /api/candidates`

**Authentication:** Required (session)

**Response:**
```json
{
    "candidates": [
        {
            "id": 1,
            "name": "Jane Smith",
            "email": "jane@example.com",
            "score": 85,
            "status": "shortlisted",
            "skills": ["Python", "SQL", "Flask"]
        }
    ]
}
```

---

### 6.2 Get Candidate Profile
**Endpoint:** `GET /api/candidate/<candidate_id>`

**Authentication:** Required (session)

**Response:**
```json
{
    "id": 1,
    "name": "Jane Smith",
    "email": "jane@example.com",
    "phone": "1234567890",
    "score": 85,
    "status": "shortlisted",
    "notes": "Great fit for the role",
    "skills": ["Python", "SQL", "Flask", "AWS"],
    "tags": ["python", "senior", "aws"],
    "resume": {
        "filename": "jane_smith_resume.pdf",
        "path": "/uploads/jane_smith_resume.pdf"
    },
    "feedback": {
        "strengths": [...],
        "weaknesses": [...],
        "suggestions": [...]
    }
}
```

---

### 6.3 Update Candidate
**Endpoint:** `POST /api/candidate/<candidate_id>/update`

**Authentication:** Required (session)

**Request:**
```json
{
    "status": "hired",
    "notes": "Offer accepted",
    "skills": ["Python", "SQL", "Flask", "AWS", "Docker"]
}
```

**Response:**
```json
{
    "success": true,
    "message": "Candidate updated"
}
```

---

### 6.4 Manage Candidate Tags
**Endpoint:** `GET /api/candidate-tags` | `POST /api/candidate-tags`

**Authentication:** Required (session)

**GET Response:**
```json
{
    "tags": ["python", "senior", "aws", "backend"]
}
```

**POST Request:**
```json
{
    "candidate_id": 1,
    "tag_name": "frontend"
}
```

**POST Response:**
```json
{
    "success": true,
    "message": "Tag added"
}
```

---

## 7. HISTORY ENDPOINTS

### 7.1 Get Screening History
**Endpoint:** `GET /api/screening-history`

**Authentication:** Required (session)

**Response:**
```json
{
    "history": [
        {
            "id": 1,
            "action_type": "resume_upload",
            "timestamp": "2024-01-15T10:30:00",
            "details": {
                "filename": "jane_smith_resume.pdf",
                "candidate": "Jane Smith"
            }
        },
        {
            "id": 2,
            "action_type": "resume_screened",
            "timestamp": "2024-01-15T10:35:00",
            "details": {
                "score": 85,
                "decision": "HIRE"
            }
        }
    ]
}
```

---

## 8. ANALYTICS & REPORTING ENDPOINTS

### 8.1 Get Analytics Dashboard
**Endpoint:** `GET /api/analytics`

**Authentication:** Required (session)

**Response:**
```json
{
    "total_resumes": 15,
    "total_candidates": 12,
    "avg_score": 72.5,
    "hired": 2,
    "rejected": 5,
    "shortlisted": 5,
    "pass_rate": 58.33
}
```

---

## 9. COMPARISON ENGINE ENDPOINTS

### 9.1 Comparative AI Analysis
**Endpoint:** `POST /api/comparative-ai`

**Authentication:** Required (session)

**Request:**
```json
{
    "candidate_ids": [1, 2, 3, 4, 5]
}
```

**Response:**
```json
{
    "success": true,
    "comparison": {
        "total_candidates": 5,
        "ranking": [...],
        "top_candidate": {...}
    }
}
```

---

### 9.2 Get Market Insights
**Endpoint:** `GET /api/market-insights`

**Authentication:** Required (session)

**Response:**
```json
{
    "top_skills": {
        "Python": 12,
        "SQL": 11,
        "Flask": 8,
        "AWS": 7
    },
    "avg_experience_years": 5.2,
    "market_trends": "High demand for Python and Cloud"
}
```

---

### 9.3 Get Ranking Analysis
**Endpoint:** `GET /api/ranking-analysis`

**Authentication:** Required (session)

**Response:**
```json
{
    "rankings": [
        {
            "rank": 1,
            "name": "Jane Smith",
            "score": 85,
            "status": "shortlisted"
        }
    ]
}
```

---

## 10. ERROR RESPONSES

### Standard Error Format
```json
{
    "error": "Error message describing what went wrong",
    "success": false
}
```

### Common Error Codes

| Code | Message | Description |
|------|---------|-------------|
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required |
| 404 | Not Found | Resource not found |
| 500 | Server Error | Internal server error |

### Example Error Response
```json
{
    "error": "Resume not found",
    "success": false
}
```

---

## 11. AUTHENTICATION FLOW DIAGRAM

```
User → Sign Up → Login → Session Created → Dashboard
                                    ↓
                           Access Protected Routes
                                    ↓
                        (All API calls require session)
```

---

## 12. REQUIRED HEADERS

All `POST` requests with JSON body should include:
```
Content-Type: application/json
```

File upload requests should use:
```
Content-Type: multipart/form-data
```

---

## 13. STATUS CODES SUMMARY

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 404 | Not Found |
| 500 | Server Error |

---

## 14. DATA STORAGE & PERSISTENCE

All data is stored in SQLite database: `screening_system.db`

**Key Tables:**
- `users` - User accounts
- `resumes` - Uploaded resumes
- `screening_results` - AI screening results
- `candidates` - Candidate profiles
- `ai_feedback` - AI analysis feedback
- `candidate_tags` - Candidate categorization
- `screening_history` - Activity log
- `analytics_summary` - Aggregated statistics

---

## 15. FILE UPLOAD SPECIFICATIONS

**Supported Formats:** PDF, DOCX, DOC

**Max File Size:** 16 MB

**Storage Location:** `/uploads` folder

**Naming Convention:** `YYYYMMDD_HHMMSS_original_filename.ext`

---

## 16. USAGE EXAMPLES

### Complete Resume Screening Flow

```bash
# 1. User signs up
POST /api/signup
{
    "username": "recruiter1",
    "email": "recruiter@company.com",
    "password": "secure123"
}

# 2. User logs in
POST /login
username=recruiter1&password=secure123

# 3. Upload resume
POST /api/upload-resume
[multipart file upload]
→ Returns: resume_id = 5

# 4. Set job requirements
POST /api/job-requirements
{
    "job_title": "Senior Python Developer",
    "required_skills": "Python, Flask, AWS"
}
→ Returns: job_requirement_id = 3

# 5. Screen resume
POST /api/screen-resume
{
    "resume_id": 5,
    "job_requirement_id": 3
}
→ Returns: screening_id = 12, candidate_id = 8, score = 85

# 6. Get results
GET /api/screening-results/12
→ Returns detailed feedback and analysis

# 7. View candidate profile
GET /api/candidate/8
→ Returns full candidate profile with all data

# 8. Compare candidates
POST /api/compare-candidates
{
    "candidate_ids": [8, 7, 6]
}
→ Returns ranked comparison

# 9. Update candidate status
POST /api/candidate/8/update
{
    "status": "hired"
}

# 10. View analytics
GET /api/analytics
→ Returns comprehensive statistics
```

---

## 17. BEST PRACTICES

1. **Authentication:** Always check session before accessing protected routes
2. **Error Handling:** Always check `success` field in response
3. **Pagination:** Use limit/offset for large datasets (TODO: implement)
4. **Rate Limiting:** Consider implementing rate limiting (TODO)
5. **Data Validation:** Validate input on both frontend and backend
6. **File Security:** Uploaded files stored outside web root in `/uploads`

