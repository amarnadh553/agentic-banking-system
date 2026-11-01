from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class BankingRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Banking question, including customer ID when relevant.", examples=["What accounts does customer C001 have?"])
    visualize_graph: bool = Field(default=False, description="Whether to generate the banking graph visualization.")
    keep_formatting: bool = Field(default=False, description="Keep line breaks (markdown lists and tables) in the response. Used by the Streamlit UI.")
    include_trace: bool = Field(default=True, description="Return the execution trace (agents, tools, tokens, cost, latency). Meant for debugging and evaluation.")


class ExecutionTrace(BaseModel):
    """How the answer was produced. Only returned when the request sets include_trace=true."""
    model_config = ConfigDict(protected_namespaces=())   # allows the field name "model_name"

    selected_agent: str
    selected_agents: list[dict] = Field(default_factory=list)   # [{"agent": "accounts", "question": "..."}]
    selected_tools: list[dict] = Field(default_factory=list)    # [{"agent": "accounts", "tool": "...", "args": {...}}]
    model_name: str = ""
    latency_seconds: float = 0.0   # time the server took to answer (router + agents + tools)
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0


class BankingResponse(BaseModel):
    reasoning: str
    response: str
    trace: Optional[ExecutionTrace] = None
    graph_image_url: Optional[str] = None