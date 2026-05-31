with open('app.py', encoding='utf-8') as f:
    content = f.read()

old = '''    return jsonify({
        "success": True,
        "name": candidate_name,
        "email": candidate_email,
        "score": ats_score,
        "skills": skills,
        "job_role": job_role
    })'''

new = '''    # ── AI FEEDBACK via Gemini ──
    experience_score = 0
    skills_score = min(100, len(skills) * 10)
    education_score = 0

    exp_keywords = ["experience", "worked", "years", "internship", "engineer", "developer", "analyst", "manager"]
    edu_keywords = ["bachelor", "master", "b.tech", "m.tech", "bsc", "msc", "degree", "university", "college", "phd"]

    text_lower2 = raw_text.lower()
    exp_matches = sum(1 for k in exp_keywords if k in text_lower2)
    edu_matches = sum(1 for k in edu_keywords if k in text_lower2)

    experience_score = min(100, exp_matches * 15)
    education_score = min(100, edu_matches * 20)

    strengths = []
    improvements = []

    gemini_prompt = f"""You are an expert resume reviewer. Analyze this resume and respond ONLY with valid JSON, no markdown, no extra text.

Resume text:
{raw_text[:3000]}

Respond with exactly this JSON structure:
{{
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "improvements": ["improvement 1", "improvement 2", "improvement 3"],
  "experience_score": <number 0-100>,
  "skills_score": <number 0-100>,
  "education_score": <number 0-100>,
  "summary": "One sentence overall assessment"
}}"""

    try:
        ai_response = call_gemini(gemini_prompt)
        if ai_response:
            import re as re2
            clean = re2.sub(r"```json|```", "", ai_response).strip()
            ai_data = json.loads(clean)
            strengths = ai_data.get("strengths", [])
            improvements = ai_data.get("improvements", [])
            experience_score = ai_data.get("experience_score", experience_score)
            skills_score = ai_data.get("skills_score", skills_score)
            education_score = ai_data.get("education_score", education_score)
    except Exception as e:
        print(f"DEBUG: Gemini feedback error: {e}")

    return jsonify({
        "success": True,
        "name": candidate_name,
        "email": candidate_email,
        "score": ats_score,
        "skills": skills,
        "job_role": job_role,
        "experience_score": experience_score,
        "skills_score": skills_score,
        "education_score": education_score,
        "strengths": strengths,
        "improvements": improvements
    })'''

if old in content:
    content = content.replace(old, new)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Fixed!')
else:
    print('Not found - check spacing')