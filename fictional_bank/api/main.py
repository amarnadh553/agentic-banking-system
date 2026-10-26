import time
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict

from fictional_bank.config import Config
from fictional_bank.main import FictionalBankApplication
from fictional_bank.mcp_client import MCPToolClient
from fictional_bank.src import Logger
from fictional_bank.src.utilities import remove_newlines, generate_graph

logger = Logger().get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Connect to domain MCP servers when FastAPI starts."""
    logger.info("Starting Banking API")
    try:
        async with MCPToolClient() as client:
            logger.info("Accounts tools: %s", [tool.name for tool in client.tools_for("accounts")])
            logger.info(
                "Accounts tools: %s",
                [tool.name for tool in client.tools_for("accounts")],
            )
            logger.info("MCP servers connected successfully")
            app.state.banking_app = FictionalBankApplication(
                config=Config(),
                logger=Logger().get_logger(),
                accounts_tools=client.tools_for("accounts"),
                transactions_tools=client.tools_for("transactions"),
                service_tools=client.tools_for("service"),
            )
            logger.info("Banking application initialized successfully")
            yield
    except Exception:
        logger.exception("Banking API startup or runtime failed")
        raise

    finally:
        logger.info("Banking API shutdown completed")


app = FastAPI(
    title="Fictional Banking Agent API",
    description="REST API powered by LangGraph and MCP.",
    version="1.0.0",
    lifespan=lifespan,
)


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

def get_selected_agents(result: dict, question: str) -> list[dict]:
    """The agents the router picked, each with the sub-question it was given."""
    tasks = result.get("tasks") or [{"agent": "clarification", "question": question}]
    return [{"agent": task["agent"], "question": task["question"]} for task in tasks]

def get_selected_tools(result: dict) -> list[dict]:
    """Every tool the agents called, in order, one dict per call."""
    return [{"agent": agent, "tool": call["name"], "args": call["args"]} for agent, calls in (result.get("tool_calls") or {}).items() for call in calls]

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/api/v1/banking/ask", response_model=BankingResponse)
async def ask_banking_agent(request: BankingRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Please provide a banking question.")
    logger.info("Banking request received")
    try:
        started = time.perf_counter()
        banking_app = app.state.banking_app
        result = await banking_app.run(question)
        print("RES START", result, "RES END")
        logger.info("Banking request completed; selected_agent=%s", result.get("selected_agent", "UNKNOWN"))
        graph_image_url = None
        if request.visualize_graph:
            generate_graph(banking_app)
        latency_seconds = round(time.perf_counter() - started, 3)
        # return BankingResponse(
        #     selected_agents=get_selected_agents(result, question),
        #     selected_tools=get_selected_tools(result),
        #     model_name=banking_app.config.LLM_MODEL_NAME,
        #     latency_seconds=latency_seconds,
        #     selected_agent=result.get("selected_agent", ""),
        #     reasoning=result.get("reasoning", ""),
        #     response=remove_newlines(result.get("response", "")),
        # )
        return BankingResponse(
            reasoning=result.get("reasoning", ""),
            response=remove_newlines(result.get("response", "")),
            trace=ExecutionTrace(
                selected_agent=result.get("selected_agent", ""),
                selected_agents=get_selected_agents(result, question),
                selected_tools=get_selected_tools(result),
                model_name=banking_app.config.LLM_MODEL_NAME,
                latency_seconds=latency_seconds,
            ),
        )

    except Exception as exc:
        logger.exception("Banking request processing failed")
        raise HTTPException(status_code=500, detail=f"""Failed to process the banking request.{exc}""")