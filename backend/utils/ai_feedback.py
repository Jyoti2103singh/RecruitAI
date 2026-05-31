def generate_ai_feedback(text):
    """
    AI Feedback Engine for Resume Screening System
    Returns structured recruiter-style feedback
    """

    text = text.lower()

    # -------------------------
    # ANALYSIS BUCKETS
    # -------------------------
    strengths = []
    weaknesses = []
    suggestions = []

    # -------------------------
    # SKILL CHECK (STRENGTHS)
    # -------------------------
    if "python" in text:
        strengths.append("Strong Python programming knowledge")

    if "sql" in text:
        strengths.append("Database and SQL understanding")

    if "flask" in text:
        strengths.append("Backend development experience with Flask")

    if "django" in text:
        strengths.append("Web development experience using Django")

    if "machine learning" in text or "ml" in text:
        strengths.append("Machine Learning knowledge present")

    if "project" in text:
        strengths.append("Has project experience mentioned")

    # -------------------------
    # WEAKNESSES DETECTION
    # -------------------------
    if "react" not in text and "frontend" not in text:
        weaknesses.append("No frontend framework experience (React/Angular missing)")

    if "aws" not in text and "azure" not in text:
        weaknesses.append("No cloud platform experience detected")

    if "docker" not in text:
        weaknesses.append("Missing DevOps / containerization skills (Docker)")

    if "github" not in text:
        weaknesses.append("No version control (GitHub) mentioned")

    if "api" not in text:
        weaknesses.append("No API development experience clearly stated")

    # -------------------------
    # SUGGESTIONS ENGINE
    # -------------------------
    suggestions.append("Build and deploy real-world full-stack projects")
    suggestions.append("Add cloud deployment experience (AWS / Azure / GCP)")
    suggestions.append("Strengthen system design fundamentals")
    suggestions.append("Contribute to open-source projects")
    suggestions.append("Include GitHub project links in resume")

    # -------------------------
    # FINAL SCORE INSIGHT
    # -------------------------
    score_insight = ""

    if len(strengths) >= 4:
        score_insight = "Strong candidate for mid-level roles"
    elif len(strengths) >= 2:
        score_insight = "Suitable for entry-level positions with guidance"
    else:
        score_insight = "Needs significant skill improvement before job readiness"

    # -------------------------
    # FORMAT FINAL OUTPUT
    # -------------------------
    feedback = {
        "strengths": strengths if strengths else ["Basic technical profile detected"],
        "weaknesses": weaknesses if weaknesses else ["No major weaknesses detected"],
        "suggestions": suggestions,
        "insight": score_insight
    }

    return feedback