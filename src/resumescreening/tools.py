"""Utilities for resume parsing, scoring, and interview scheduling.

This module provides:
- Simple placeholder functions for parsing resumes and scoring candidates
  against a job description.
- Basic scheduling helpers for checking available interview slots and booking them.
- Feedback simulation and decision-making helpers for interview rounds.

All logic here is dummy/sample logic and should be replaced with real implementations.
"""

# ---------------------------------------------------
# Resume Parsing and scoring
# ----------------------------------------------------


def parse_resume(text: str) -> dict:
    """Parses raw resume text and extracts key profile attributes.

    Note:
        This is a placeholder/dummy parser. Replace with a real NLP-based parser.

    Args:
        text (str): Raw resume text.

    Returns:
        dict: Extracted profile information including skills, experience,
            and a summary.
    """
    # todo: Replace this with an llm call with structure output
    return {
        "skills": ["python", "fastapi", "docker"],
        "years_experience": 4,
        "summary": "Software engineer with backend experience",
    }


def score_against_jd(jd: str, profile: dict) -> dict:
    """Scores a parsed candidate profile against a job description.

    Note:
        This is a simplified dummy scoring mechanism. Replace with real
        model-based scoring logic.

    Args:
        jd (str): The job description text.
        profile (dict): Parsed candidate profile containing skills, experience, etc.

    Returns:
        dict: Scoring details including numeric score, decision, and reasons.
    """
    # todo: Replace this with an llm call with structure output
    # leave ATS score for now
    score = 0.8  # pretending computed
    reasons = "Good match for backend skills and years of experience"
    decision = "shortlist" if score >= 0.7 else "reject"
    return {
        "score": score,
        "decision": decision,
        "reasons": reasons
    }


# ---------------------------------------------------
# SCHEDULING TOOLS
# ----------------------------------------------------

# todo: lets research on any calender apis
# google calender
# outlook
# zoom ...

PANEL_SLOTS = {
    "backend_engineer": [
        "2025-12-13 10:00",
        "2025-12-13 11:00",
        "2025-12-13 15:00",
        "2025-12-13 16:00"
    ]
}
"""dict: Predefined interviewer availability for various job roles."""


BOOKED: list[str] = []
"""list[str]: Tracks the list of slots already booked by candidates."""


def get_panel_availability(role: str) -> list[str]:
    """Returns all available interview slots for a given role.

    Args:
        role (str): Job role or panel type.

    Returns:
        list[str]: List of time slots that are not yet booked.
    """
    return [s for s in PANEL_SLOTS.get(role, []) if s not in BOOKED]


def book_slot(candidate_id: str, slot: str) -> dict:
    """Attempts to book an interview slot for a candidate.

    Args:
        candidate_id (str): Unique identifier of the candidate.
        slot (str): Desired interview time slot.

    Returns:
        dict: Booking status with either `"confirmed"` or `"failed"` and
            the associated slot.
    """
    if slot in BOOKED:
        return {"status": "failed", "slot": slot}
    BOOKED.append(slot)
    return {"status": "confirmed", "slot": slot}


# ---------------------------------------------------
# FEEDBACK + DECISION
# ----------------------------------------------------


def simulate_feedback(round_no: int) -> str:
    """Generates simulated interviewer feedback for a given round.

    Note:
        This function uses placeholder logic and does not reflect real
        interviewer evaluation.

    Args:
        round_no (int): Interview round number.

    Returns:
        str: Textual feedback describing candidate strengths for that round.
    """
    if round_no == 1:
        return "Round 1 feedback: strong python and basic design skills."
    else:
        return "Round 2 feedback: strong system design and communication."


def decide_next_step(feedback: str, round_no: int) -> str:
    """Decides the next step in the interview process based on feedback.

    Args:
        feedback (str): Interviewer feedback text.
        round_no (int): Current interview round number.

    Returns:
        str: One of `"next_round"`, `"reject"`, or `"offer"` indicating
            the candidate's next step.
    """
    feedback_parsed = feedback.lower()
    if "weak" in feedback_parsed:
        return "reject"
    if "strong" in feedback_parsed and round_no >= 2:
        return "offer"
    if "strong" in feedback_parsed and round_no == 1:
        return "next_round"
    return "reject"
