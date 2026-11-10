
import json
import re
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from pypdf import PdfReader

from workflow.graph import run_recruitment
from agent.ai_model import get_ai_model


# PROJECT PATHS
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
JOBS_FILE = BASE_DIR / "data" / "jobs.json"


# CREATE FASTAPI APPLICATION
app = FastAPI(title="AI Recruitment Assistant")


# CORS CONFIGURATION
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# HOME API
@app.get("/")
def home():
    return {"message": "AI Recruitment Assistant is running"}


# RUN COMPLETE RECRUITMENT WORKFLOW
@app.get("/run-recruitment")
def run_assistant():

    result = run_recruitment()

    OUTPUT_DIR.mkdir(exist_ok=True)

    with open(
        OUTPUT_DIR / "recruitment_results.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(result, file, indent=4, ensure_ascii=False)

    return result


# SINGLE RESUME UPLOAD API
@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF."
        )

    try:
        reader = PdfReader(file.file)

        resume_text = ""

        for page in reader.pages:
            resume_text += page.extract_text() or ""

        if not resume_text.strip():
            raise HTTPException(
                status_code=400,
                detail="No readable text found in this PDF."
            )

        llm = get_ai_model()

        prompt = f"""
        Analyse this candidate resume.

        Resume:
        {resume_text}

        Provide:
        1. Professional summary
        2. Technical skills
        3. Education
        4. Experience
        5. Projects

        Use only information in the resume.
        Do not invent qualifications or experience.
        """

        response = llm.invoke(prompt)

        result = {
            "filename": file.filename,
            "analysis": response.content
        }

        OUTPUT_DIR.mkdir(exist_ok=True)

        with open(
            OUTPUT_DIR / "uploaded_resume_results.json",
            "w",
            encoding="utf-8"
        ) as file_output:
            json.dump(
                result,
                file_output,
                indent=4,
                ensure_ascii=False
            )

        return result

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


# AI RESUME ANALYSIS
def analyse_resume_with_ai(resume_text, job):

    llm = get_ai_model()

    prompt = f"""
    You are an AI resume analysis assistant.

    JOB DETAILS:
    Job title: {job['job_title']}
    Required skills: {job['required_skills']}
    Minimum experience: {job['minimum_experience']} years
    Job description: {job['job_description']}

    RESUME:
    {resume_text}

    Analyse the resume and return ONLY valid JSON.
    Do not use Markdown or code fences.

    Use this exact JSON structure:

    {{
        "candidate_name": "Name found in resume or Unknown",
        "skills": ["skill1", "skill2"],
        "experience_years": 2,
        "education": "Education found in resume or Unknown",
        "projects": ["project1", "project2"],
        "professional_summary": "Short summary",
        "project_relevance_score": 75,
        "project_relevance_explanation": "Explain relevance using resume evidence",
        "job_relevance_explanation": "Explain how the candidate's stated experience relates to this job"
    }}

    IMPORTANT:
    - Use only information actually present in the resume.
    - Do not invent skills, qualifications, projects or experience.
    - Use null for experience_years if it cannot be established.
    - project_relevance_score must be between 0 and 100.
    - Assess project relevance against the supplied job description.
    - If project information is missing, use a score of 0 and explain that.
    - Return valid JSON only.
    """

    response = llm.invoke(prompt)

    content = response.content

    if not isinstance(content, str):
        raise ValueError("AI returned an unexpected response format.")

    content = re.sub(r"^```(?:json)?\s*", "", content.strip())
    content = re.sub(r"\s*```$", "", content)

    result = json.loads(content)

    required_fields = [
        "candidate_name",
        "skills",
        "experience_years",
        "education",
        "projects",
        "professional_summary",
        "project_relevance_score",
        "project_relevance_explanation",
        "job_relevance_explanation"
    ]

    for field in required_fields:
        if field not in result:
            raise ValueError(f"AI response is missing: {field}")

    return result


# CALCULATE CANDIDATE COMPARISON SCORE
def calculate_candidate_score(candidate, job):

    required_skills = job["required_skills"]
    candidate_skills = candidate["skills"]

    matched_skills = []
    missing_skills = []

    for required_skill in required_skills:

        found = any(
            required_skill.lower() == skill.lower()
            for skill in candidate_skills
        )

        if found:
            matched_skills.append(required_skill)
        else:
            missing_skills.append(required_skill)

    skill_score = (
        len(matched_skills) / len(required_skills) * 100
        if required_skills else 0
    )

    experience = candidate["experience_years"]
    minimum_experience = job["minimum_experience"]

    if experience is None:
        experience_score = 0
        experience_match = None
    else:
        experience_score = min(
            experience / minimum_experience * 100, 100
        ) if minimum_experience > 0 else 100

        experience_match = experience >= minimum_experience

    project_score = candidate["project_relevance_score"]

    # Skills = 60%, Experience = 25%, Projects = 15%
    overall_score = (
        skill_score * 0.60
        + experience_score * 0.25
        + project_score * 0.15
    )

    candidate["matched_skills"] = matched_skills
    candidate["missing_skills"] = missing_skills
    candidate["skill_score"] = round(skill_score, 2)
    candidate["experience_score"] = round(experience_score, 2)
    candidate["experience_match"] = experience_match
    candidate["overall_score"] = round(overall_score, 2)

    candidate["recommendation"] = (
        "Strong match for further human review"
        if overall_score >= 75
        else "Needs further human review"
    )

    return candidate


# COMPARE TWO RESUMES AGAINST ONE JOB
@app.post("/compare-resumes")
async def compare_resumes(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    job_id: int = Form(201)
):

    files = [file1, file2]

    for file in files:

        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail=f"{file.filename} is not a PDF."
            )

    try:

        # Read job information
        with open(JOBS_FILE, "r", encoding="utf-8") as job_file:
            jobs = json.load(job_file)

        # Find selected job
        job = next(
            (item for item in jobs if item["job_id"] == job_id),
            None
        )

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="Job ID not found."
            )

        candidate_results = []

        # Process both resumes
        for file in files:

            reader = PdfReader(file.file)

            resume_text = ""

            for page in reader.pages:
                resume_text += page.extract_text() or ""

            if not resume_text.strip():
                raise HTTPException(
                    status_code=400,
                    detail=f"No readable text found in {file.filename}."
                )

            # AI analyses the resume
            candidate = analyse_resume_with_ai(
                resume_text,
                job
            )

            candidate["filename"] = file.filename

            # Python calculates the score
            candidate = calculate_candidate_score(
                candidate,
                job
            )

            candidate_results.append(candidate)

        # Sort candidates from highest to lowest score
        candidate_results.sort(
            key=lambda item: item["overall_score"],
            reverse=True
        )

        # Prepare comparison result
        result = {
            "job_title": job["job_title"],
            "job_id": job["job_id"],
            "comparison_criteria": {
                "technical_skills": "60%",
                "experience": "25%",
                "project_relevance": "15%"
            },
            "total_candidates": len(candidate_results),
            "candidates": candidate_results,
            "notice": (
                "AI-generated comparison for recruiter assistance only. "
                "Human review is required before hiring decisions."
            )
        }

        # Save comparison result
        OUTPUT_DIR.mkdir(exist_ok=True)

        with open(
            OUTPUT_DIR / "resume_comparison_results.json",
            "w",
            encoding="utf-8"
        ) as output_file:

            json.dump(
                result,
                output_file,
                indent=4,
                ensure_ascii=False
            )

        return result

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


# CUSTOM OPENAPI SCHEMA FOR SWAGGER
def custom_openapi():

    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version="0.1.0",
        routes=app.routes,
        openapi_version="3.0.3"
    )

    def fix_file_schema(schema):

        if isinstance(schema, dict):

            if (
                schema.get("type") == "string"
                and schema.get("contentMediaType")
            ):
                schema.pop("contentMediaType", None)
                schema["format"] = "binary"

            for value in schema.values():
                fix_file_schema(value)

        elif isinstance(schema, list):

            for item in schema:
                fix_file_schema(item)

    fix_file_schema(openapi_schema)

    app.openapi_schema = openapi_schema

    return app.openapi_schema


app.openapi = custom_openapi
