import json
from pathlib import Path

from workflow.resume_screening_agent import screen_resumes
from agent.ai_model import get_ai_model

BASE_DIR = Path(__file__).resolve().parent.parent
JOBS_FILE = BASE_DIR / "data" / "jobs.json"


def evaluate_candidates(candidates=None):
    if candidates is None:
        candidates = screen_resumes()

    with open(JOBS_FILE, "r", encoding="utf-8") as file:
        jobs = json.load(file)

    llm = get_ai_model()
    results = []

    for job in jobs:
        for candidate in candidates:

            matched_skills = [
                skill for skill in job["required_skills"]
                if skill.lower() in [s.lower() for s in candidate["skills"]]
            ]

            skill_score = (
                len(matched_skills) / len(job["required_skills"])
            ) * 100

            experience_match = (
                candidate["experience_years"] >= job["minimum_experience"]
            )

            prompt = f"""
            You are an HR recruitment evaluation assistant.

            Job details:
            {json.dumps(job)}

            Candidate details:
            {json.dumps(candidate)}

            Skill match percentage: {round(skill_score, 2)}%
            Experience requirement met: {experience_match}

            Explain:
            1. Candidate strengths for this job.
            2. Missing required skills.
            3. Overall suitability for further human review.

            Use only the supplied information.
            Do not invent experience or qualifications.
            Do not make a final hiring decision.
            """

            response = llm.invoke(prompt)

            results.append({
                "candidate_name": candidate["name"],
                "job_title": job["job_title"],
                "matched_skills": matched_skills,
                "skill_score": round(skill_score, 2),
                "experience_match": experience_match,
                "ai_evaluation": response.content,
                "recommendation": (
                    "Suitable for further review"
                    if experience_match and skill_score >= 50
                    else "Needs further review"
                )
            })

    return results