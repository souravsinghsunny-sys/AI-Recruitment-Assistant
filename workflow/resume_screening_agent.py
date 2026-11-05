import json
from pathlib import Path
from agent.ai_model import get_ai_model

BASE_DIR = Path(__file__).resolve().parent.parent
CANDIDATES_FILE = BASE_DIR / "data" / "candidates.json"


def screen_resumes():

    with open(CANDIDATES_FILE, "r", encoding="utf-8") as file:
        candidates = json.load(file)

    llm = get_ai_model()

    screened_candidates = []

    for candidate in candidates:

        prompt = f"""
        You are an AI recruitment assistant.

        Analyse the following candidate profile.

        Candidate details:
        {json.dumps(candidate)}

        Provide:
        1. A short professional profile summary.
        2. Key technical strengths.
        3. Relevant project experience.

        Only use the information provided.
        Do not invent qualifications or experience.
        Do not make a final hiring decision.
        """

        response = llm.invoke(prompt)

        candidate["ai_screening_summary"] = response.content

        screened_candidates.append(candidate)

    return screened_candidates