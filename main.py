
import json
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader

from workflow.graph import run_recruitment
from agent.ai_model import get_ai_model


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"

app = FastAPI(title="AI Recruitment Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "AI Recruitment Assistant is running"}


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
            json.dump(result, file_output, indent=4, ensure_ascii=False)

        return result

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )
