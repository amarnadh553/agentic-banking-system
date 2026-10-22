import operator
from typing import Annotated, TypedDict


class AgentTask(TypedDict):
    """One unit of work for one specialist agent."""
    agent: str      # accounts | transactions | service
    question: str   # self-contained sub-question for that agent


class AgentAnswer(TypedDict):
    agent: str
    question: str
    answer: str


class AgentState(TypedDict):
    """Carries the question, the router's plan, each specialist's answer and the final response."""
    question: str
    selected_agent: str     # comma-separated route names, e.g. "accounts,transactions"
    reasoning: str
    tasks: list[AgentTask]  # router's plan (one task per specialist)
    # Specialists run in parallel; the reducer appends their answers instead of overwriting.
    answers: Annotated[list[AgentAnswer], operator.add]
    response: str
