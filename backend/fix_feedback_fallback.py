with open('app.py', encoding='utf-8') as f:
    content = f.read()

old = '''    try:
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
        print(f"DEBUG: Gemini feedback error: {e}")'''

new = '''    try:
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
        # Fallback rule-based feedback
        if len(skills) >= 5:
            strengths.append(f"Strong technical profile with {len(skills)} relevant skills detected including {', '.join(skills[:3])}.")
        if len(raw_text) > 800:
            strengths.append("Resume has good detail and length — likely to pass ATS length filters.")
        if candidate_email != "N/A":
            strengths.append("Contact information is clearly present and detectable by ATS systems.")
        if len(skills) < 5:
            improvements.append("Add more technical skills relevant to your target role to improve ATS scoring.")
        if len(raw_text) < 500:
            improvements.append("Resume appears too short — expand your experience and project descriptions.")
        if experience_score < 40:
            improvements.append("Add more work experience details with action verbs like built, designed, led, improved.")
        if education_score < 40:
            improvements.append("Make sure your education section clearly mentions your degree and university name.")
        if not strengths:
            strengths.append("Resume was successfully parsed and key information was extracted.")
        if not improvements:
            improvements.append("Consider tailoring your resume to each specific job description for better match scores.")'''

if old in content:
    content = content.replace(old, new)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Fixed!')
else:
    print('Not found')