"""
MCP server exposing Account domain tools only.
"""


# Standard library
import logging
import sys

# Third-party packages
from mcp.server.fastmcp import FastMCP

# Local imports
from fictional_bank.tools import customer_details_tool, customer_accounts_tool, account_balance_tool, total_balance_tool
from fictional_bank.src.utilities import call_existing_tool

logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(asctime)s [accounts-mcp] %(levelname)s %(message)s")
logger = logging.getLogger("accounts-mcp")

mcp = FastMCP("accounts", instructions="Read-only customer profile, account and balance queries.")

@mcp.tool()
def get_customer_details_based_on_id(customer_id: str) -> dict:
    """Get profile details for a customer ID."""
    return call_existing_tool(customer_details_tool, customer_id=customer_id)

@mcp.tool()
def get_customer_accounts_based_on_customer_id(customer_id: str) -> dict:
    """List accounts owned by a customer."""
    return call_existing_tool(customer_accounts_tool, customer_id=customer_id)

@mcp.tool()
def get_account_balance(customer_id: str, account_id: str) -> dict:
    """Get the balance of one account belonging to a customer."""
    return call_existing_tool(account_balance_tool, customer_id=customer_id, account_id=account_id)


@mcp.tool()
def get_total_balance(customer_id: str) -> dict:
    """Get a customer's total balances grouped by currency."""
    return call_existing_tool(total_balance_tool, customer_id=customer_id)

if __name__ == "__main__":
    mcp.run(transport="stdio")
