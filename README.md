# 🤖 RecruitAI

> **AI-Powered Recruitment & Resume Screening Platform**

RecruitAI is a web-based recruitment platform designed to simplify and automate the hiring process. It helps recruiters manage candidates, analyze resumes, shortlist applicants, and track recruitment activities through a centralized dashboard.

The project combines **Artificial Intelligence, Web Development, and Database Management** to create a practical recruitment management solution.

---

## 📌 Overview

Traditional recruitment can involve manually reviewing large numbers of resumes, maintaining candidate information, and tracking applicants across different stages of the hiring process.

**RecruitAI** aims to reduce this workload by providing a centralized platform where recruiters can:

* Upload and analyze candidate resumes
* Screen candidates using AI-assisted analysis
* Manage candidate information
* Shortlist suitable candidates
* Track interview-related information
* Generate recruitment-related reports
* Manage recruitment data through a centralized database

---

## ✨ Features

### 👤 Candidate Management

* Add and manage candidate information
* Maintain candidate records
* View candidate details from the recruiter dashboard

### 📄 Resume Screening

* Upload candidate resumes
* Extract information from PDF resumes
* Analyze resumes using AI
* Assist recruiters in identifying suitable candidates

### 🎯 Candidate Shortlisting

* Evaluate candidates based on resume information
* Help recruiters identify potentially suitable candidates
* Organize shortlisted candidates

### 📊 Recruiter Dashboard

* Centralized recruitment management
* Candidate overview
* Resume screening workflow
* Recruitment information management

### 📝 Interview Tracking

* Maintain interview-related information
* Track candidates during the recruitment process

### 📑 Report Generation

* Generate recruitment-related reports
* Export information for further use

### 🔐 Environment Configuration

* API credentials are managed using environment variables
* Sensitive keys are not stored directly in the source code

---

## 🛠️ Tech Stack

| Technology             | Purpose                     |
| ---------------------- | --------------------------- |
| **Python**             | Backend development         |
| **Flask**              | Web framework               |
| **SQLite**             | Database                    |
| **HTML**               | Page structure              |
| **Tailwind CSS**       | UI styling                  |
| **JavaScript**         | Frontend interactions       |
| **Gemini API**         | AI-assisted resume analysis |
| **pdfplumber / pypdf** | PDF processing              |
| **python-docx**        | Document processing         |
| **ReportLab**          | Report generation           |
| **Git & GitHub**       | Version control             |

---

## 🏗️ System Architecture

```text
                    ┌─────────────────────┐
                    │       Recruiter     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   RecruitAI Web UI  │
                    │ HTML + Tailwind CSS │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     Flask Backend   │
                    │    Python / APIs    │
                    └──────┬───────┬──────┘
                           │       │
                ┌──────────┘       └──────────┐
                ▼                             ▼
       ┌────────────────┐             ┌────────────────┐
       │ SQLite Database│             │   AI Analysis  │
       │  Candidate Data│             │   Gemini API   │
       └────────────────┘             └───────┬────────┘
                                              │
                                              ▼
                                    ┌──────────────────┐
                                    │ Resume Analysis  │
                                    │ & Screening      │
                                    └──────────────────┘
```

---

## 🔄 Recruitment Workflow

```text
Candidate Resume
       │
       ▼
   Upload PDF
       │
       ▼
 Resume Text Extraction
       │
       ▼
   AI Analysis
       │
       ▼
 Candidate Evaluation
       │
       ▼
 Shortlisting
       │
       ▼
 Interview Tracking
       │
       ▼
 Recruitment Reports
```

---

## 📂 Project Structure

```text
RecruitAI/
│
├── app.py
├── requirements.txt
├── README.md
├── .env
├── screening.db
│
├── templates/
│   ├── recruiter-dashboard.html
│   ├── ...
│
├── static/
│   ├── css/
│   ├── js/
│   └── ...
│
├── uploads/
│   └── ...
│
└── reports/
    └── ...
```

> **Note:** Do not upload your `.env` file or API keys to GitHub.

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Jyoti2103singh/RecruitAI.git
```

### 2. Navigate to the Project

```bash
cd RecruitAI
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Virtual Environment

**Windows:**

```bash
venv\Scripts\activate
```

**Linux / macOS:**

```bash
source venv/bin/activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_KEY=your_gemini_api_key
```

Replace `your_gemini_api_key` with your own API key.

**Never commit your `.env` file to GitHub.**

Add it to `.gitignore`:

```text
.env
venv/
__pycache__/
*.pyc
```

---

## ▶️ Running the Application

After installing the dependencies and configuring the environment variables:

```bash
python app.py
```

The Flask development server will start locally.

Open the local URL shown in your terminal in a web browser.

---

## 🧠 AI Resume Screening

RecruitAI uses AI-assisted analysis to process resume information and help recruiters evaluate candidates.

The general process is:

```text
PDF Resume
     ↓
Text Extraction
     ↓
Resume Information
     ↓
AI Processing
     ↓
Candidate Analysis
     ↓
Recruiter Decision
```

The AI is intended to **assist recruiters**, rather than completely replace human decision-making.

---

## 🗄️ Database

RecruitAI currently uses **SQLite** for storing recruitment-related information.

The database can contain information related to:

* Candidates
* Resumes
* Screening results
* Recruitment records
* Interview information

---

## 🔒 Security Considerations

RecruitAI follows basic security practices such as:

* Keeping API keys in environment variables
* Avoiding hard-coded secrets
* Using `.gitignore` for sensitive files
* Separating application configuration from source code

For production deployment, additional security measures should be implemented, including stronger authentication, authorization, input validation, secure file handling, and production-grade database configuration.

---

## 🚀 Future Enhancements

Possible future improvements include:

* 🔐 Role-based authentication
* 📧 Automated candidate email notifications
* 📊 Advanced recruitment analytics
* 🤝 Job description matching
* 📈 Candidate ranking dashboard
* 🧠 Improved AI-based candidate matching
* 📅 Automated interview scheduling
* ☁️ Cloud deployment
* 🗃️ PostgreSQL/MySQL support
* 🔍 Advanced candidate search and filtering
* 📱 Improved mobile responsiveness

---

## 🎯 Project Objectives

The main objectives of RecruitAI are:

1. Reduce manual resume screening effort.
2. Centralize candidate information.
3. Assist recruiters in candidate evaluation.
4. Improve recruitment workflow management.
5. Demonstrate practical implementation of AI in recruitment.
6. Build a scalable full-stack web application.

---

## 💡 Why RecruitAI?

RecruitAI demonstrates how **AI can be integrated with a traditional web application** to solve a real-world problem.

Instead of creating an AI model in isolation, the project combines:

**Frontend + Backend + Database + AI + Document Processing**

into a single recruitment workflow.

---

## 📸 Screenshots

Add screenshots of your application here:

```text
screenshots/
├── dashboard.png
├── resume-upload.png
├── screening-result.png
└── candidate-management.png
```

Example:

```markdown
![Recruiter Dashboard](screenshots/dashboard.png)
```

---

## 🧪 Development Status

**Status:** 🚧 Active Development

RecruitAI is being developed as a practical recruitment management and AI-assisted resume screening project.

---

## 👩‍💻 Developer

**Jyoti Singh**

B.Tech — Computer Science & Engineering

GitHub:
https://github.com/Jyoti2103singh

---

## 📜 License

This project is intended for educational and portfolio purposes.

You may modify and extend the project according to your requirements.

---

## ⭐ Support

If you find this project useful, consider giving the repository a ⭐ on GitHub!
