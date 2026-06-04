# 🤖 RecruitAI

An AI-powered recruitment platform built with Flask and Groq (LLaMA 3.3), designed to streamline hiring for recruiters and job searching for candidates.

## ✨ Features

### For Candidates
- 📄 **Resume Builder** — Build professional resumes with 8+ templates, live preview, and PDF/DOCX export
- 🧠 **AI Resume Parser** — Upload your existing resume (DOCX) and auto-fill the builder
- 📊 **ATS Score** — Get instant ATS compatibility score with improvement tips
- 🚀 **AI Career Tools** — Generate portfolio project ideas and career roadmaps
- 💼 **Job Board** — Browse and apply to jobs with one click

### For Recruiters
- 📋 **Job Posting** — Post and manage job listings
- 🔍 **AI Resume Screening** — Automatically screen and rank candidates
- 📊 **Analytics Dashboard** — Track applications, views, and hiring metrics
- 🤝 **Candidate Comparison** — Compare candidates side by side with AI insights
- 🎤 **AI Interview Questions** — Generate role-specific interview questions

## 🛠 Tech Stack

- **Backend** — Python, Flask, SQLite
- **AI** — Groq API (LLaMA 3.3 70B)
- **Frontend** — HTML, CSS, JavaScript
- **PDF Export** — html2pdf.js
- **DOCX Export** — docx.js

## 🚀 Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/Jyoti2103singh/RecruitAI.git
cd RecruitAI/backend
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
Create a `.env` file in the `backend/` folder: