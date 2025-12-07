"""End-to-end workflow for candidate screening, interviewing, and HR report generation.

This module integrates:
- Resume parsing and scoring using predefined tools.
- Multi-round interview scheduling with routing logic.
- Automated feedback + decision-making simulation.
- HR-friendly report generation using an LLM.
- A LangGraph-powered state machine to orchestrate all steps.

The logic here coordinates various workflow nodes to move a candidate from
resume screening → interview rounds → final HR report.
"""

import os

from typing import Literal
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END

from .state import ScreeningResult, State, CandidateInterview, InterviewRound

from .tools import (
    parse_resume,
    score_against_jd,
    get_panel_availability,
    book_slot,
    simulate_feedback,
    decide_next_step
)

load_dotenv()
model_name = os.getenv('MODEL_NAME')
model_provider = os.getenv('MODEL_PROVIDER')
llm = init_chat_model(model=model_name, model_provider=model_provider)


# ---------------------------------------------------
# Node 1 - Screen Resumes
# ---------------------------------------------------
def screen_resumes_node(state: State) -> State:
    """Processes resumes by parsing and scoring each candidate.

    For every resume in the `state`, this node:
    1. Parses the resume text.
    2. Scores it against the job description.
    3. Records the screening decision.

    Args:
        state (State): Current global workflow state containing resumes
            and job description.

    Returns:
        State: Updated state with a new list of screening results.
    """
    jd = state['job_description']
    results: list[ScreeningResult] = []

    for idx, resume in enumerate(state['resumes']):
        profile = parse_resume(resume)
        score_info = score_against_jd(jd, profile)
        results.append(
            {
                "candidate_id": f"cand-{idx + 1}",
                "score": score_info["score"],
                "decision": score_info["decision"],
                "reasons": score_info["reasons"]
            }
        )
    state["screening_results"] = results
    return state


# ---------------------------------------------------
# Node 2 - Initialize Interview State
# ---------------------------------------------------
def init_interviews_node(state: State) -> State:
    """Initializes interview metadata for all shortlisted candidates.

    Any candidate marked as "shortlist" in screening results is added to the
    interview pipeline with round number set to 0.

    Args:
        state (State): Workflow state containing screening results.

    Returns:
        State: Updated state with initialized interview entries.
    """
    interviews: list[CandidateInterview] = []

    for screening_result in state["screening_results"]:
        if screening_result["decision"] == "shortlist":
            interviews.append({
                "candidate_id": screening_result["candidate_id"],
                "status": "pending_first_round",
                "current_round": 0,
                "history": []
            })
    state["interviews"] = interviews
    return state


# ---------------------------------------------------
# Node 3 - Router Node
# ---------------------------------------------------
def router_node(state: State) -> State:
    """Acts as a pass-through node before conditional routing.

    Args:
        state (State): Current workflow state.

    Returns:
        State: Unmodified state.
    """
    return state


def route_next(state: State) -> Literal["schedule_round", "collect_feedback", "generate_hr_report"]:
    """Decides the next step in the interview workflow.

    Routing logic:
    - If any candidate needs to be scheduled → schedule_round
    - If any candidate is awaiting feedback → collect_feedback
    - Otherwise → generate_hr_report

    Args:
        state (State): Current workflow state.

    Returns:
        Literal: Next node to execute.
    """
    interviews = state.get("interviews", [])

    # Anyone waiting to be scheduled (first or next round)
    if any(
        interview["status"] in ["pending_first_round", "next_round_pending"] 
        for interview in interviews):
        return "schedule_round"
    
    # Anyone waiting for feedback?
    if any(
        interview["status"] == "waiting_feedback"
        for interview in interviews):
        return "collect_feedback"
    
    # Otherwise generate a hr report
    return "generate_hr_report"


# ---------------------------------------------------
# Node 4 - Schedule Interview Round
# ---------------------------------------------------
def schedule_round_node(state: State) -> State:
    """Schedules the next interview round for candidates needing a slot.

    This node:
    1. Fetches available panel slots.
    2. Assigns one slot per eligible candidate.
    3. Advances interview status to `waiting_feedback`.

    Args:
        state (State): Workflow state containing interview progress.

    Returns:
        State: Updated state with new scheduled slots.
    """
    interviews = state["interviews"]

    # todo: fix required to get the role
    slots = get_panel_availability("backend_engineer")

    for interview in interviews:
        if interview["status"] not in ["pending_first_round", "next_round_pending"]:
            continue

        if not slots:
            # No slots are left
            # todo: handle
            continue
        
        chosen = slots.pop(0)
        booking = book_slot(interview['candidate_id'], chosen)
        if booking["status"] != "confirmed":
            # todo: to be fixed
            continue

        interview["current_round"] += 1
        interview["status"] = "waiting_feedback"
        interview["history"].append({
            "round_number": interview["current_round"],
            "slot": chosen,
            "feedback": None,
            "decision": None
        })
    state["interviews"] = interviews
    return state


# ---------------------------------------------------
# Node 5 - Collect Feedback
# ---------------------------------------------------
def collect_feedback_node(state: State) -> State:
    """Collects feedback and determines candidate progression.

    For each candidate waiting for feedback:
    - Simulates interviewer comments.
    - Decides next action: next round / reject / offer.
    - Updates interview history and status.

    Args:
        state (State): Workflow state with candidate interview history.

    Returns:
        State: Updated state after applying feedback decisions.
    """
    interviews = state["interviews"]
    for interview in interviews:
        if interview["status"] != "waiting_feedback":
            continue

        last_round = interview["history"][-1]
        round_no = last_round["round_number"]

        feedback = simulate_feedback(round_no)
        decision = decide_next_step(feedback, round_no)

        last_round["feedback"] = feedback
        last_round["decision"] = decision

        if decision == "next_round":
            interview["status"] = "next_round_pending"
        elif decision == "reject":
            interview["status"] = "rejected"
        elif decision == "offer":
            interview["status"] = "offer_made"
    
    state["interviews"] = interviews
    return state


# ---------------------------------------------------
# Node 6 - HR Report Generation (LLM)
# ---------------------------------------------------
def generate_hr_report_node(state: State) -> State:
    """Generates a human-readable HR summary using an LLM.

    The report covers:
    - Pipeline summary
    - Shortlisted candidates & interview journey
    - Rejections + reasons
    - Offer recommendations

    Args:
        state (State): Workflow state with screening & interview lifecycle.

    Returns:
        State: Updated state with `hr_report` filled in.
    """
    interviews = state["interviews"]
    screening_results = state['screening_results']
    prompt = f"""
You are a HR specialist

Create a clear summary report for the hiring manager.

Job Description:
{state['job_description']}

Screening Results:
{screening_results}

Interview Lifecycle:
{interviews}

The report should include
1. Overall pipeline summary
2. Shortlisted candidates and their interview rounds
3. Rejected Candidates and main reasons.
4. Candidates for whom an offer is recommnded

Use bullet points and Short paragraphs.
"""
    result = llm.invoke(prompt)
    state["hr_report"] = result.content
    return state


# ---------------------------------------------------
# Graph Builder
# ---------------------------------------------------
def build_graph():
    """Builds and compiles the full LangGraph workflow.

    The graph consists of:
    - Linear first steps (screen → init → router)
    - Conditional routing based on interview progress
    - Loops to support multiple interview rounds
    - Terminal HR report node

    Returns:
        Graph: A compiled LangGraph state machine ready for execution.
    """
    builder = StateGraph(State)

    builder.add_node("screen_resumes", screen_resumes_node)
    builder.add_node("init_interviews", init_interviews_node)
    builder.add_node("router", router_node)
    builder.add_node("schedule_round", schedule_round_node)
    builder.add_node("collect_feedback", collect_feedback_node)
    builder.add_node("generate_hr_report", generate_hr_report_node)

    builder.set_entry_point("screen_resumes")

    # Linear
    builder.add_edge("screen_resumes", "init_interviews")
    builder.add_edge("init_interviews", "router")

    # conditional edges from router
    builder.add_conditional_edges(
        "router",
        route_next,
        {
            "schedule_round": "schedule_round",
            "collect_feedback": "collect_feedback",
            "generate_hr_report": "generate_hr_report"
        },
    )

    # Loops for multi-round flow
    builder.add_edge("schedule_round", "router")
    builder.add_edge("collect_feedback", "router")

    builder.add_edge("generate_hr_report", END)
    return builder.compile()
