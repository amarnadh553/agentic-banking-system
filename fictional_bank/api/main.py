from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from fictional_bank.config import Config
from fictional_bank.main import FictionalBankApplication
from fictional_bank.mcp_client import MCPToolClient
from fictional_bank.src import Logger
from fictional_bank.src.utilities import remove_newlines

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
                service_mcp_tools=client.tools_for("service"),
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
    question: str = Field(
        ...,
        min_length=1,
        description="Banking question, including customer ID when relevant.",
        examples=["What accounts does customer C001 have?"],
    )


class BankingResponse(BaseModel):
    selected_agent: str
    reasoning: str
    response: str


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
        result = await app.state.banking_app.run(question)
        logger.info("Banking request completed; selected_agent=%s", result.get("selected_agent", "UNKNOWN"))
        return BankingResponse(
            selected_agent=result.get("selected_agent", ""),
            reasoning=result.get("reasoning", ""),
            response=remove_newlines(result.get("response", "")),
        )

    except Exception as exc:
        logger.exception("Banking request processing failed")
        raise HTTPException(status_code=500, detail="Failed to process the banking request.")