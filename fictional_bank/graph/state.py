from typing import TypedDict


class AgentState(TypedDict, total=False):
    """Data that moves between the graph nodes."""
    question: str              # what the user asked
    selected_agent: str        # routes chosen by the router, e.g. "accounts,transactions"
    reasoning: str             # why the router chose them
    tasks: list[dict]          # router's plan: [{"agent": "accounts", "question": "..."}]
    accounts_result: dict      # each specialist writes only its own key, so agents can run in parallel.
    transactions_result: dict  # A result is {"answer": str, "tool_calls": [{"name": ..., "args": {...}}]}
    service_result: dict
    response: str              # final reply returned to the user
    tool_calls: dict           # tools used per agent, e.g. {"accounts": [...], "transactions": [...]}
