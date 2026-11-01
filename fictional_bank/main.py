import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fictional_bank.config import Config
from fictional_bank.services import FictionalBankApplication
from fictional_bank.mcp_client import MCPToolClient
from fictional_bank.src import Logger
from fictional_bank.config import Config
from fictional_bank.routers import banking_router, evaluation_router
from fictional_bank.config.config import Config


logger = Logger().get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Connect to domain MCP servers when FastAPI starts."""
    logger.info("Starting Banking API")
    try:
        async with MCPToolClient() as client:

            logger.info("Accounts tools: %s", [tool.name for tool in client.tools_for("accounts")],)
            logger.info("Transactions tools: %s", [tool.name for tool in client.tools_for("transactions")])
            logger.info("Service tools: %s", [tool.name for tool in client.tools_for("service")])

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



@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Register API routers
app.include_router(banking_router)
app.include_router(evaluation_router)


def start():
    config=Config()
    """Start the Fictional Banking API."""
    uvicorn.run("fictional_bank.main:app", host=config.API_HOST, port=int(config.API_PORT), reload=config.RELOAD)

if __name__ == "__main__":
    start()

