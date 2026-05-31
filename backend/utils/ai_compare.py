# ==========================
# AI COMPARE - utils/ai_compare.py
# ==========================

def compare_candidates(candidate_list):
    """
    Candidate Comparison Engine
    Input: list of dicts
    Output: ranked analysis + recommendation
    """

    if not candidate_list:
        return {
            "total_candidates": 0,
            "top_candidate": None,
            "ranking": [],
            "error": "No candidates provided"
        }

    results = []

    for candidate in candidate_list:

        name = candidate.get("name", "Unknown")
        skills = candidate.get("skills", [])
        score = candidate.get("score", 0)
        experience = candidate.get("experience", 0)  # years
        education = candidate.get("education", "")

        # -------------------------
        # SCORING LOGIC
        # -------------------------
        skill_weight = len(skills) * 10
        experience_weight = experience * 5

        # Education bonus
        education_bonus = 0
        if "phd" in education.lower():
            education_bonus = 20
        elif "master" in education.lower():
            education_bonus = 15
        elif "bachelor" in education.lower():
            education_bonus = 10

        final_score = score + skill_weight + experience_weight + education_bonus

        # Cap score at 100
        final_score = min(final_score, 100)

        # -------------------------
        # DECISION ENGINE
        # -------------------------
        if final_score >= 80:
            decision = "Hire"
            badge = "🟢"
        elif final_score >= 60:
            decision = "Shortlist"
            badge = "🟡"
        elif final_score >= 40:
            decision = "Maybe"
            badge = "🟠"
        else:
            decision = "Reject"
            badge = "🔴"

        # -------------------------
        # STRENGTH ANALYSIS
        # -------------------------
        strengths = []
        weaknesses = []

        if len(skills) >= 5:
            strengths.append("Strong skill set")
        else:
            weaknesses.append("Limited skills")

        if experience >= 3:
            strengths.append("Good experience")
        else:
            weaknesses.append("Low experience")

        if score >= 70:
            strengths.append("High base score")
        else:
            weaknesses.append("Low base score")

        if education_bonus >= 15:
            strengths.append("Strong educational background")

        results.append({
            "name": name,
            "skills": skills,
            "experience": experience,
            "education": education,
            "base_score": score,
            "final_score": final_score,
            "decision": decision,
            "badge": badge,
            "strengths": strengths,
            "weaknesses": weaknesses
        })

    # -------------------------
    # SORT BY SCORE (RANKING)
    # -------------------------
    results = sorted(results, key=lambda x: x["final_score"], reverse=True)

    # Add rank number
    for i, candidate in enumerate(results):
        candidate["rank"] = i + 1

    # -------------------------
    # TOP CANDIDATE INSIGHT
    # -------------------------
    top = results[0] if results else None

    # -------------------------
    # STATS SUMMARY
    # -------------------------
    scores = [r["final_score"] for r in results]
    avg_score = round(sum(scores) / len(scores), 2)
    hire_count = len([r for r in results if r["decision"] == "Hire"])
    shortlist_count = len([r for r in results if r["decision"] == "Shortlist"])
    reject_count = len([r for r in results if r["decision"] == "Reject"])

    summary = {
        "total_candidates": len(results),
        "top_candidate": top,
        "average_score": avg_score,
        "hire_count": hire_count,
        "shortlist_count": shortlist_count,
        "reject_count": reject_count,
        "ranking": results
    }

    return summary