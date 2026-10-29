from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class BankingRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Banking question, including customer ID when relevant.", examples=["What accounts does customer C001 have?"])
    visualize_graph: bool = Field(default=False, description="Whether to generate the banking graph visualization.")


class ExecutionTrace(BaseModel):
    """How the answer was produced. Remove this key from the response if you do not need it."""
    model_config = ConfigDict(protected_namespaces=())   # allows the field name "model_name"

    selected_agent: str
    selected_agents: list[dict] = Field(default_factory=list)   # [{"agent": "accounts", "question": "..."}]
    selected_tools: list[dict] = Field(default_factory=list)    # [{"agent": "accounts", "tool": "...", "args": {...}}]
    model_name: str = ""
    latency_seconds: float = 0.0   # time the server took to answer (router + agents + tools)


class BankingResponse(BaseModel):
    reasoning: str
    response: str
    trace: ExecutionTrace
    graph_image_url: Optional[str] = None