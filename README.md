# 🤖 RecruitAI

### AI-Powered Recruitment & Career Platform

RecruitAI is a **full-stack AI-powered recruitment platform** designed to connect **job seekers and recruiters** in one integrated system.

The platform provides candidates with tools to **build and improve resumes, check ATS compatibility, explore career opportunities, and apply for jobs**, while recruiters can **post jobs, screen applications, analyze resumes, compare candidates, and manage the hiring process**.

The goal of RecruitAI is to make recruitment more efficient for recruiters while giving candidates better tools to prepare themselves for employment.

---

## 🌟 Why RecruitAI?

The traditional hiring process creates challenges for both sides.

### For Candidates

* Creating a professional resume can be difficult.
* Candidates often don't know whether their resume is ATS-friendly.
* Finding suitable jobs can take significant time.
* Understanding career requirements for a particular role can be challenging.

### For Recruiters

* Reviewing a large number of resumes is time-consuming.
* Manually comparing candidates can be difficult.
* Managing job applications and recruitment data across different stages can become complicated.

**RecruitAI brings both sides together in one platform and uses AI to assist with these tasks.**

---

# 👥 Two-Sided Platform

```text
                         ┌───────────────────────┐
                         │       RecruitAI       │
                         │   Recruitment Platform │
                         └───────────┬───────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                 │
                    ▼                                 ▼
          ┌───────────────────┐             ┌───────────────────┐
          │     CANDIDATE     │             │     RECRUITER     │
          └─────────┬─────────┘             └─────────┬─────────┘
                    │                                 │
          ┌─────────┴─────────┐             ┌─────────┴─────────┐
          │                   │             │                   │
          ▼                   ▼             ▼                   ▼
     Resume Tools        Career Tools    Job Posting       AI Screening
          │                   │             │                   │
          ▼                   ▼             ▼                   ▼
      ATS Score          Job Search      Applications      Candidate Ranking
          │                   │             │                   │
          └──────────┐        │             │        ┌──────────┘
                     ▼        ▼             ▼        ▼
                  ┌─────────────────────────────────────┐
                  │          Recruitment Workflow       │
                  │                                     │
                  │     Candidate ↔ Recruiter           │
                  └─────────────────────────────────────┘
```

---

# 👨‍💻 Candidate Features

RecruitAI provides candidates with tools to prepare for and find employment.

### 📄 AI Resume Builder

Candidates can create professional resumes using a resume builder with multiple templates and a live preview.

Features include:

* Multiple resume templates
* Live resume preview
* Resume customization
* PDF export
* DOCX export
* Professional resume formatting

### 🧠 AI Resume Parser

Candidates can upload an existing resume and use AI-assisted parsing to extract relevant information into the resume builder.

The system can process information such as:

* Name
* Skills
* Experience
* Education
* Languages
* Professional information

### 📊 ATS Resume Analysis

Candidates can analyze their resume for ATS compatibility.

RecruitAI provides:

* ATS score
* Resume evaluation
* Improvement suggestions
* Areas that may need optimization

### 🚀 AI Career Tools

Candidates can use AI-assisted career tools for:

* Career guidance
* Portfolio project ideas
* Career roadmaps
* Role-related suggestions

### 💼 Job Search

Candidates can browse available job opportunities and apply to suitable positions.

---

# 🧑‍💼 Recruiter Features

Recruiters have a dedicated set of tools for managing the recruitment process.

### 📋 Job Posting

Recruiters can:

* Create job postings
* Define job requirements
* Manage posted jobs
* View applications

### 🔍 AI Resume Screening

RecruitAI helps recruiters analyze candidate resumes and identify candidates who match the requirements of a job.

The general workflow is:

```text
Job Requirements
       ↓
Candidate Applications
       ↓
Resume Processing
       ↓
AI Analysis
       ↓
Candidate Evaluation
       ↓
Shortlisting
```

### 📊 Recruiter Dashboard

The recruiter dashboard provides a centralized view of recruitment activities.

Recruiters can monitor:

* Job postings
* Applications
* Candidates
* Hiring-related metrics
* Recruitment activity

### 🤝 Candidate Comparison

Recruiters can compare candidates and use AI-assisted insights to help evaluate applicants.

### 🎤 AI Interview Questions

RecruitAI can generate role-specific interview questions to assist recruiters during the interview process.

---

# 🤖 AI-Powered Workflow

RecruitAI uses AI as an **assistive layer** within the recruitment platform.

```text
                    ┌────────────────────┐
                    │   User Input       │
                    └─────────┬──────────┘
                              │
             ┌────────────────┴────────────────┐
             │                                 │
             ▼                                 ▼
      Candidate Side                    Recruiter Side
             │                                 │
       Resume / Profile                  Job Requirements
             │                                 │
             └──────────────┬──────────────────┘
                            ▼
                    ┌───────────────┐
                    │ AI Processing │
                    └───────┬───────┘
                            │
             ┌──────────────┴──────────────┐
             │                             │
             ▼                             ▼
       Candidate Insights            Recruiter Insights
             │                             │
             └──────────────┬──────────────┘
                            ▼
                     Better Decisions
```

AI is intended to **assist users**, not completely replace human decision-making.

---

# 🏗️ System Architecture

RecruitAI follows a full-stack architecture consisting of a frontend, Flask backend, database, document-processing components, and AI services.

```text
                         ┌──────────────────────┐
                         │        USERS         │
                         └──────────┬───────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
             ┌──────────────┐                ┌──────────────┐
             │  Candidate   │                │  Recruiter   │
             │   Interface  │                │  Interface   │
             └──────┬───────┘                └──────┬───────┘
                    │                               │
                    └──────────────┬────────────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │    Frontend UI    │
                         │ HTML/CSS/JS       │
                         └─────────┬─────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │   Flask Backend   │
                         │   Python / APIs   │
                         └─────┬─────┬───────┘
                               │     │
                 ┌─────────────┘     └─────────────┐
                 ▼                                 ▼
        ┌──────────────────┐              ┌─────────────────┐
        │ SQLite Database  │              │   AI Services   │
        │ Users / Jobs /   │              │ Groq / LLaMA    │
        │ Applications etc.│              │                 │
        └──────────────────┘              └────────┬────────┘
                                                   │
                                                   ▼
                                         ┌──────────────────┐
                                         │ AI Analysis      │
                                         │ Resume / Career  │
                                         │ Recruitment      │
                                         └──────────────────┘
```

---

# 🔄 Complete Platform Workflow

```text
                         RECRUITAI
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
         CANDIDATE                    RECRUITER
              │                           │
              ▼                           ▼
        Create Profile              Create Account
              │                           │
              ▼                           ▼
        Build Resume                 Post Job
              │                           │
              ▼                           ▼
        ATS Analysis                 Receive Applications
              │                           │
              ▼                           ▼
        Search Jobs                  Screen Resumes
              │                           │
              ▼                           ▼
         Apply Job                  AI Candidate Analysis
              │                           │
              └─────────────┬─────────────┘
                            ▼
                     Hiring Process
```

---

# 🛠️ Technology Stack

| Layer                      | Technology              |
| -------------------------- | ----------------------- |
| **Frontend**               | HTML, CSS, JavaScript   |
| **Styling**                | Tailwind CSS            |
| **Backend**                | Python, Flask           |
| **Database**               | SQLite                  |
| **AI**                     | Groq API / LLaMA 3.3    |
| **PDF Processing**         | pdfplumber, pypdf       |
| **DOCX Processing**        | python-docx             |
| **PDF Generation**         | ReportLab / html2pdf.js |
| **DOCX Generation**        | python-docx / docx.js   |
| **Environment Management** | python-dotenv           |
| **Version Control**        | Git & GitHub            |

The current backend documentation identifies Flask, SQLite, HTML/CSS/JavaScript, and Groq/LLaMA-based AI as the main technologies.

---

# 📁 Project Structure

```text
RecruitAI/
│
├── backend/
│   │
│   ├── ai_modules/
│   │   ├── ...
│   │
│   ├── backend/
│   │   ├── ...
│   │
│   ├── frontend/
│   │   ├── ...
│   │
│   ├── static/
│   │   ├── ...
│   │
│   ├── templates/
│   │   ├── ...
│   │
│   ├── uploads/
│   │   ├── ...
│   │
│   ├── utils/
│   │   ├── ...
│   │
│   ├── app.py
│   ├── database.py
│   ├── database_schema.py
│   ├── config.py
│   ├── requirements.txt
│   ├── Procfile
│   └── API_DOCUMENTATION.md
│
├── frontend/
│   └── assets/
│
├── .gitignore
├── README.md
└── screening.db
```

This structure reflects the current repository, which contains separate frontend/backend areas and backend modules for AI, templates, static assets, uploads, utilities, database handling, and API documentation.

---

# ⚙️ Installation

## 1. Clone the Repository

```bash
git clone https://github.com/Jyoti2103singh/RecruitAI.git
```

```bash
cd RecruitAI
```

## 2. Navigate to Backend

```bash
cd backend
```

## 3. Create a Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔑 Environment Variables

Create a `.env` file inside the `backend` directory.

Example:

```env
GROQ_API_KEY=your_api_key_here
```

Do **not** upload API keys or other sensitive credentials to GitHub.

Make sure `.env` is included in `.gitignore`.

---

# ▶️ Run the Application

From the `backend` directory:

```bash
python app.py
```

The Flask development server will start locally.

Open the local address displayed in the terminal in your browser.

---

# 📄 Resume Processing

RecruitAI supports resume-related document processing for the candidate workflow.

```text
Resume Upload
      ↓
Document Processing
      ↓
Text Extraction
      ↓
Information Extraction
      ↓
AI Analysis
      ↓
Resume / Candidate Insights
```

The platform includes dedicated backend components for uploads, utilities, AI modules, and resume-related functionality.

---

# 🗄️ Database

RecruitAI currently uses **SQLite** for application data.

The database supports information required for the recruitment workflow, including areas such as:

* Users
* Candidates
* Recruiters
* Jobs
* Applications
* Recruitment information
* Resume-related information
* Notifications and other platform data

---

# 🔐 Security

RecruitAI follows basic security practices such as:

* Environment variables for API credentials
* `.gitignore` for sensitive configuration
* Backend-side processing
* Separation of frontend and backend responsibilities

For production deployment, additional security improvements should be implemented, including:

* Strong authentication
* Role-based access control
* Secure password hashing
* Input validation
* Secure file upload validation
* Production database
* HTTPS
* Rate limiting
* Secure session management

---

# 📈 Future Enhancements

RecruitAI can be further improved with:

* 🔐 Advanced role-based authentication
* 📧 Automated candidate/recruiter email notifications
* 📅 Interview scheduling
* 💬 Candidate-recruiter communication
* 📊 Advanced recruitment analytics
* 🧠 Improved AI candidate-job matching
* 📱 Progressive Web App / mobile support
* ☁️ Cloud deployment
* 🗃️ PostgreSQL/MySQL production database
* 🔔 Real-time notifications
* 📈 Advanced candidate ranking
* 🏢 Company profiles
* 🔎 Advanced job and candidate filtering

---

# 🎯 Project Objectives

The main objectives of RecruitAI are:

1. Build a platform that serves both **candidates and recruiters**.
2. Simplify resume creation and improvement for candidates.
3. Help candidates evaluate their resumes using ATS analysis.
4. Provide candidates with access to relevant job opportunities.
5. Simplify job posting and application management for recruiters.
6. Reduce manual resume screening effort.
7. Assist recruiters in evaluating and comparing candidates.
8. Demonstrate practical applications of AI in recruitment.
9. Combine frontend, backend, database, document processing, and AI technologies into one complete system.

---

# 💡 What Makes RecruitAI Different?

RecruitAI isn't designed only as an **AI resume screener**.

It brings the complete interaction between the two sides of recruitment into one platform:

```text
             CANDIDATE                         RECRUITER
                 │                                │
                 │                                │
          Build Resume                       Post Jobs
                 │                                │
          ATS Analysis                       View Applications
                 │                                │
            Find Jobs                        Screen Resumes
                 │                                │
             Apply ───────────────►         Evaluate
                 │                                │
                 └──────── Recruitment ──────────┘
                           Workflow
```

This makes RecruitAI a **two-sided recruitment ecosystem** rather than just a resume-analysis tool.

---

# 📸 Screenshots

Add screenshots of the major parts of the platform here.

### 🏠 Landing Page

```markdown
![RecruitAI Landing Page](screenshots/landing-page.png)
```

### 👨‍💻 Candidate Dashboard

```markdown
![Candidate Dashboard](screenshots/candidate-dashboard.png)
```

### 📄 Resume Builder

```markdown
![Resume Builder](screenshots/resume-builder.png)
```

### 📊 ATS Analysis

```markdown
![ATS Analysis](screenshots/ats-analysis.png)
```

### 🧑‍💼 Recruiter Dashboard

```markdown
![Recruiter Dashboard](screenshots/recruiter-dashboard.png)
```

### 🔍 AI Resume Screening

```markdown
![AI Resume Screening](screenshots/resume-screening.png)
```

---

# 🚧 Development Status

**Status: Active Development**

RecruitAI is being developed as a full-stack AI-assisted recruitment platform for both job seekers and recruiters.

---

# 👩‍💻 Developer

## Jyoti Singh

**B.Tech — Computer Science & Engineering**

GitHub:
https://github.com/Jyoti2103singh

---

# ⭐ Support

If you find RecruitAI useful or interesting, consider giving the repository a ⭐ on GitHub.

---

## 📜 License

This project is currently intended for **educational, learning, and portfolio purposes**.
