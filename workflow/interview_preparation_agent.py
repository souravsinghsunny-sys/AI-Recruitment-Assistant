from workflow.candidate_evaluation_agent import evaluate_candidates
from agent.ai_model import get_ai_model


def prepare_interviews(evaluations=None):
    if evaluations is None:
        evaluations = evaluate_candidates()
    llm = get_ai_model()

    interview_results = []

    for candidate in evaluations:

        prompt = f"""
        You are an experienced technical interviewer.

        Candidate name: {candidate['candidate_name']}
        Job role: {candidate['job_title']}
        Matched skills: {candidate['matched_skills']}
        Skill match: {candidate['skill_score']}%
        Experience requirement met: {candidate['experience_match']}

        Evaluation:
        {candidate['ai_evaluation']}

        Generate:
        1. Five technical interview questions.
        2. Two practical scenario-based questions.
        3. One project-related question.

        Make questions relevant to the job role.
        Do not assume qualifications not provided.
        Return clear, numbered questions.
        """

        response = llm.invoke(prompt)

        interview_results.append({
            "candidate_name": candidate["candidate_name"],
            "job_title": candidate["job_title"],
            "interview_questions": response.content
        })

    return interview_results