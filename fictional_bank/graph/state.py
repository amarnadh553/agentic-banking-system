from typing import TypedDict

class AgentState(TypedDict):
    """This state carries the user's question, routing decision, reasoning, and final response between graph nodes."""
    question:str
    selected_agent:str
    reasoning:str
    response:str
