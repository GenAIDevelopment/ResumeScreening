## Project Setup

* Create a Project Structure
```bash
mkdir resumescreening
uv init --pacakage .
uv sync
```

* Installing dependencies
```bash
uv add langgraph python-dotenv
```

* Models:
    * We will start with gemini models from GCP
    * We will use open ai gpt
    * We will use Bedrock from AWS
    * We will use Azure AI Foundry/Azure Open AI
    * We will be using local models hosted on ollama



### PART 1 - Defining the State

* InterviewRound
```python
class InterviewRound(TypedDict):
    round_number: int
    slot: str
    feedback: str|None
    decision: Literal["next_round", "reject", "offer"]


class CanditateInterview(TypedDict):
    candidate_id: str
    status: str
    current_round: int
    history: List[InterviewRound]

class State(TypedDict):
    job_id: str
    job_description: str
    resumes: list[str]
    screening_result: list[dict]
    interviews: List[CandidateInterview]
    hr_report: str

```