
const API_URL = "http://127.0.0.1:8000";

// Recruitment Process
const runBtn = document.getElementById("runBtn");

runBtn.addEventListener("click", async function () {
    const status = document.getElementById("status");
    const results = document.getElementById("results");

    status.innerText = "Running AI recruitment process...";
    results.innerHTML = "";
    runBtn.disabled = true;

    try {
        const response = await fetch(API_URL + "/run-recruitment");
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Recruitment process failed");
        }

        document.getElementById("candidateCount").innerText = data.candidates.length;
        document.getElementById("evaluationCount").innerText = data.evaluations.length;
        document.getElementById("interviewCount").innerText = data.interviews.length;

        status.innerText = "Recruitment process completed successfully!";

        data.evaluations.forEach(function (candidate) {
            const card = document.createElement("div");
            card.className = "candidate-card";

            const name = document.createElement("h3");
            name.innerText = candidate.candidate_name;

            const job = document.createElement("p");
            job.innerText = "Job Role: " + candidate.job_title;

            const score = document.createElement("p");
            score.innerText = "Skill Match: " + candidate.skill_score + "%";

            const experience = document.createElement("p");
            experience.innerText = "Experience Match: " +
                (candidate.experience_match ? "Yes" : "No");

            const recommendation = document.createElement("p");
            recommendation.innerText = "Recommendation: " + candidate.recommendation;

            const evaluationTitle = document.createElement("h4");
            evaluationTitle.innerText = "AI Evaluation";

            const evaluation = document.createElement("p");
            evaluation.innerText = candidate.ai_evaluation;

            card.appendChild(name);
            card.appendChild(job);
            card.appendChild(score);
            card.appendChild(experience);
            card.appendChild(recommendation);
            card.appendChild(evaluationTitle);
            card.appendChild(evaluation);

            const interview = data.interviews.find(function (item) {
                return item.candidate_name === candidate.candidate_name &&
                    item.job_title === candidate.job_title;
            });

            if (interview) {
                const interviewTitle = document.createElement("h4");
                interviewTitle.innerText = "Interview Questions";

                const questions = document.createElement("pre");
                questions.innerText = interview.interview_questions;
                questions.style.whiteSpace = "pre-wrap";

                card.appendChild(interviewTitle);
                card.appendChild(questions);
            }

            results.appendChild(card);
        });

    } catch (error) {
        status.innerText = "Error: " + error.message;
        console.error(error);

    } finally {
        runBtn.disabled = false;
    }
});


// Single PDF Resume Upload
const uploadBtn = document.getElementById("uploadBtn");

uploadBtn.addEventListener("click", async function () {
    const fileInput = document.getElementById("resumeFile");
    const uploadStatus = document.getElementById("uploadStatus");
    const uploadResult = document.getElementById("uploadResult");

    if (!fileInput.files.length) {
        uploadStatus.innerText = "Please select a PDF resume.";
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    uploadStatus.innerText = "Uploading and analysing resume...";
    uploadResult.innerHTML = "";
    uploadBtn.disabled = true;

    try {
        const response = await fetch(API_URL + "/upload-resume", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Upload failed");
        }

        uploadStatus.innerText = "Resume analysed successfully!";

        const heading = document.createElement("h3");
        heading.innerText = data.filename;

        const analysis = document.createElement("pre");
        analysis.innerText = data.analysis;
        analysis.style.whiteSpace = "pre-wrap";

        uploadResult.appendChild(heading);
        uploadResult.appendChild(analysis);

    } catch (error) {
        uploadStatus.innerText = "Error: " + error.message;
        console.error(error);

    } finally {
        uploadBtn.disabled = false;
    }
});


// Compare Two PDF Resumes
const compareBtn = document.getElementById("compareBtn");

if (compareBtn) {
    compareBtn.addEventListener("click", async function () {
        const file1 = document.getElementById("resumeFile1");
        const file2 = document.getElementById("resumeFile2");
        const jobId = document.getElementById("jobId");
        const compareStatus = document.getElementById("compareStatus");
        const compareResults = document.getElementById("compareResults");

        compareResults.innerHTML = "";

        if (!file1.files.length || !file2.files.length) {
            compareStatus.innerText = "Please select both PDF resumes.";
            return;
        }

        if (
            !file1.files[0].name.toLowerCase().endsWith(".pdf") ||
            !file2.files[0].name.toLowerCase().endsWith(".pdf")
        ) {
            compareStatus.innerText = "Please select PDF files only.";
            return;
        }

        const formData = new FormData();
        formData.append("file1", file1.files[0]);
        formData.append("file2", file2.files[0]);
        formData.append("job_id", jobId ? jobId.value : "201");

        compareStatus.innerText = "Comparing both resumes using AI...";
        compareBtn.disabled = true;

        try {
            const response = await fetch(API_URL + "/compare-resumes", {
                method: "POST",
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Resume comparison failed");
            }

            compareStatus.innerText =
                "Comparison completed! Candidates analysed: " + data.total_candidates;

            data.candidates.forEach(function (candidate, index) {
                const card = document.createElement("div");
                card.className = "candidate-card";

                const heading = document.createElement("h3");
                heading.innerText = (index + 1) + ". " + candidate.candidate_name;

                const score = document.createElement("h2");
                score.innerText = candidate.overall_score + "%";

                const filename = document.createElement("p");
                filename.innerText = "Resume: " + candidate.filename;

                const skills = document.createElement("p");
                skills.innerText = "Matched Skills: " +
                    candidate.matched_skills.join(", ");

                const missing = document.createElement("p");
                missing.innerText = "Missing Skills: " +
                    candidate.missing_skills.join(", ");

                const experience = document.createElement("p");
                experience.innerText = "Experience: " +
                    candidate.experience_years + " years";

                const project = document.createElement("p");
                project.innerText = "Project Relevance: " +
                    candidate.project_relevance_score + "%";

                const recommendation = document.createElement("p");
                recommendation.innerText =
                    "Recommendation: " + candidate.recommendation;

                card.appendChild(heading);
                card.appendChild(score);
                card.appendChild(filename);
                card.appendChild(skills);
                card.appendChild(missing);
                card.appendChild(experience);
                card.appendChild(project);
                card.appendChild(recommendation);

                compareResults.appendChild(card);
            });

        } catch (error) {
            compareStatus.innerText = "Error: " + error.message;
            console.error(error);

        } finally {
            compareBtn.disabled = false;
        }
    });
}
