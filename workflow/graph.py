from langgraph.graph import StateGraph, END
from typing import TypedDict

from workflow.resume_screening_agent import screen_resumes
from workflow.candidate_evaluation_agent import evaluate_candidates
from workflow.interview_preparation_agent import prepare_interviews


class RecruitmentState(TypedDict):
    candidates: list
    evaluations: list
    interviews: list


def screening_step(state: RecruitmentState):
    candidates = screen_resumes()
    return {"candidates": candidates}


def evaluation_step(state: RecruitmentState):
    evaluations = evaluate_candidates(state["candidates"])
    return {"evaluations": evaluations}


def interview_step(state: RecruitmentState):
    interviews = prepare_interviews(state["evaluations"])
    return {"interviews": interviews}


workflow = StateGraph(RecruitmentState)

workflow.add_node("screening", screening_step)
workflow.add_node("evaluation", evaluation_step)
workflow.add_node("interview", interview_step)

workflow.set_entry_point("screening")

workflow.add_edge("screening", "evaluation")
workflow.add_edge("evaluation", "interview")
workflow.add_edge("interview", END)

recruitment_app = workflow.compile()


def run_recruitment():
    return recruitment_app.invoke({
        "candidates": [],
        "evaluations": [],
        "interviews": []
    })