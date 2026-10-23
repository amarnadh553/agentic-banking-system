from typing import TypedDict


class AgentState(TypedDict, total=False):
    """Data that moves between the graph nodes."""
    question: str            # what the user asked
    selected_agent: str      # routes chosen by the router, e.g. "accounts,transactions"
    reasoning: str           # why the router chose them
    tasks: list[dict]        # router's plan: [{"agent": "accounts", "question": "..."}]
    accounts_answer: str     # each specialist writes only its own key,
    transactions_answer: str # so agents can run in parallel without clashing
    service_answer: str
    response: str            # final reply returned to the user
