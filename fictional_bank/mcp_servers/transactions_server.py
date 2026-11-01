"""
MCP server exposing Transaction domain tools only.
"""
import logging
import sys

from mcp.server.fastmcp import FastMCP

from fictional_bank.tools.transaction_tools import (
    get_recent_transactions as recent_transactions_tool,
    search_transactions_by_date as search_transactions_tool,
    filter_transactions_by_type as filter_by_type_tool,
    calculate_total_debits as total_debits_tool,
    calculate_total_credits as total_credits_tool,
)
from fictional_bank.src.utilities import call_existing_tool

logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(asctime)s [transactions-mcp] %(levelname)s %(message)s")

logger = logging.getLogger("transactions-mcp")

mcp = FastMCP("transactions", instructions="Read-only transaction queries. Dates use DD-MM-YYYY.")

@mcp.tool()
def get_recent_transactions(customer_id: str, limit: int = 10) -> dict:
    """Get a customer's most recent transactions, newest first."""
    return call_existing_tool(recent_transactions_tool, customer_id=customer_id, limit=limit)

@mcp.tool()
def search_transactions_by_date(customer_id: str, start_date: str, end_date: str, limit: int = 50) -> dict:
    """Search transactions within an inclusive date range (DD-MM-YYYY)."""
    return call_existing_tool(search_transactions_tool,customer_id=customer_id, start_date=start_date, end_date=end_date, limit=limit)

@mcp.tool()
def filter_transactions_by_type(customer_id: str, transaction_type: str, limit: int = 50) -> dict:
    """Filter transactions by transaction type, such as debit or credit."""
    return call_existing_tool(filter_by_type_tool, customer_id=customer_id, transaction_type=transaction_type, limit=limit)

@mcp.tool()
def calculate_total_debits(customer_id: str, start_date: str | None = None, end_date: str | None = None) -> dict:
    """Calculate total debits, optionally within a date range."""
    return call_existing_tool(total_debits_tool, customer_id=customer_id, start_date=start_date, end_date=end_date)

@mcp.tool()
def calculate_total_credits(customer_id: str, start_date: str | None = None, end_date: str | None = None) -> dict:
    """Calculate total credits, optionally within a date range."""
    return call_existing_tool(total_credits_tool, customer_id=customer_id, start_date=start_date, end_date=end_date)

if __name__ == "__main__":
    mcp.run(transport="stdio")
