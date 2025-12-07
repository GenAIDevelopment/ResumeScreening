"""Data models for tracking candidate screening, interviews, and hiring workflow.

This module defines strongly typed structures using `TypedDict` to represent:
- Screening results for candidates
- Interview round details
- Candidate interview progression across rounds
- Overall hiring state for an HR agent or workflow manager
"""

from typing import TypedDict, List, Literal


class ScreeningResult(TypedDict):
    """Represents the automated or manual screening outcome for a candidate.

    Attributes:
        candidate_id (str): Unique identifier of the candidate.
        score (float): Screening score assigned to the candidate.
        decision (Literal["shortlist", "reject"]): Screening decision.
        reasons (str): Explanation or notes behind the decision.
    """
    candidate_id: str
    score: float
    decision: Literal["shortlist", "reject"]
    reasons: str


class InterviewRound(TypedDict):
    """Represents the details and outcome of a single interview round.

    Attributes:
        round_number (int): Index of the interview round.
        slot (str): Scheduled time slot for the interview.
        feedback (str | None): Interviewer feedback, if available.
        decision (Literal["next_round", "reject", "offer"] | None):
            Outcome of the round; may be None if undecided.
    """
    round_number: int
    slot: str
    feedback: str | None
    decision: Literal["next_round", "reject", "offer"] | None


class CandidateInterview(TypedDict):
    """Represents the interview progression and status for a candidate.

    Attributes:
        candidate_id (str): Unique identifier of the candidate.
        status (Literal[
            "pending_first_round",
            "waiting_feedback",
            "next_round_pending",
            "rejected",
            "offer_made"
        ]): Current stage of the candidate in the interview pipeline.
        current_round (int): Most recent or upcoming interview round number.
        history (List[InterviewRound]): List of completed interview rounds.
    """
    candidate_id: str
    status: Literal[
        "pending_first_round",
        "waiting_feedback",
        "next_round_pending",
        "rejected",
        "offer_made"
    ]
    current_round: int
    history: List[InterviewRound]


class State(TypedDict):
    """Represents the overall hiring and interview management state.

    Attributes:
        job_id (str): Unique identifier for the job opening.
        job_description (str): Description of the job role.
        resumes (list[str]): List of candidate resume file paths or identifiers.
        screening_result (list[ScreeningResult]): Results from resume screening.
        interviews (List[CandidateInterview]):
            Interview progress for all candidates.
        hr_report (str): Final or intermediate HR summary report.
    """
    job_id: str
    job_description: str
    resumes: list[str]
    screening_result: list[ScreeningResult]
    interviews: List[CandidateInterview]
    hr_report: str
