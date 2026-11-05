
const runBtn = document.getElementById("runBtn");
const results = document.getElementById("results");
const status = document.getElementById("status");

runBtn.addEventListener("click", async function () {
    status.innerText = "Processing candidates...";
    results.innerHTML = "";

    try {
        const response = await fetch("http://127.0.0.1:8000/run-recruitment");

        if (!response.ok) {
            throw new Error("Backend error: " + response.status);
        }

        const data = await response.json();

        status.innerText = "Recruitment process completed!";

        data.evaluations.forEach(candidate => {
            const card = document.createElement("div");
            card.className = "candidate";

            card.innerHTML = `
                <h3>${candidate.candidate_name}</h3>
                <p><b>Job:</b> ${candidate.job_title}</p>
                <p><b>Skill Match:</b> ${candidate.skill_score}%</p>
                <p><b>Recommendation:</b> ${candidate.recommendation}</p>
            `;

            results.appendChild(card);
        });

        data.interviews.forEach(candidate => {
            const card = document.createElement("div");
            card.className = "candidate";

            const heading = document.createElement("h3");
            heading.textContent = "Interview Questions: " + candidate.candidate_name;

            const questions = document.createElement("p");
            questions.textContent = candidate.interview_questions;

            card.appendChild(heading);
            card.appendChild(questions);
            results.appendChild(card);
        });

    } catch (error) {
        status.innerText = "Error: " + error.message;
        console.error(error);
    }
});

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

    try {
        const response = await fetch(
            "http://127.0.0.1:8000/upload-resume",
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Upload failed");
        }

        uploadStatus.innerText = "Resume analysed successfully!";

        const heading = document.createElement("h3");
        heading.textContent = data.filename;

        const analysis = document.createElement("pre");
        analysis.textContent = data.analysis;
        analysis.style.whiteSpace = "pre-wrap";

        uploadResult.appendChild(heading);
        uploadResult.appendChild(analysis);

    } catch (error) {
        uploadStatus.innerText = "Error: " + error.message;
        console.error(error);
    }
});
