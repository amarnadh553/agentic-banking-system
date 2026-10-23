
import logging
import sys
import traceback

from mcp.server.fastmcp import FastMCP

from fictional_bank.config import Config
from fictional_bank.main import FictionalBankApplication
from fictional_bank.mcp_client import MCPToolClient
from fictional_bank.src import Logger


logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("banking-agent-mcp")

mcp = FastMCP(
    "banking_agent",
    instructions=(
        "Route all banking questions through the LangGraph Coordinator and "
        "its specialist agents. This entry point supports read-only account, "
        "transaction, and service-request questions."
    ),
)


@mcp.tool()
async def ask_banking_agent(question: str) -> dict:
    """Ask the LangGraph banking system a question."""
    if not question or not question.strip():
        return {"error": "Please provide a banking question."}
    try:
        async with MCPToolClient() as client:
            app = FictionalBankApplication(
                config=Config(),
                logger=Logger().get_logger(),
                accounts_tools=client.tools_for("accounts"),
                transactions_tools=client.tools_for("transactions"),
                service_tools=client.tools_for("service"),
            )

            result = await app.run(question.strip())

            return {
                "selected_agent": result.get("selected_agent", ""),
                "reasoning": result.get("reasoning", ""),
                "response": result.get("response", ""),
            }

    except Exception as exc:
        # Logs the complete traceback, including nested TaskGroup exceptions.
        logger.exception("ask_banking_agent failed")

        return {
            "error": str(exc),
            "traceback": "".join(
                traceback.format_exception(exc)
            ),
        }


if __name__ == "__main__":
    mcp.run(transport="stdio")
