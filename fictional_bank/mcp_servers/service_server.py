"""
MCP server exposing Service request tools only.
"""
import sys
import logging
from mcp.server.fastmcp import FastMCP

from fictional_bank.tools.service_tools import (
    get_service_requests as get_service_requests_tool,
    get_request_status as get_request_status_tool,
    get_pending_requests as get_pending_requests_tool,
    count_service_requests as count_service_requests_tool,
)
from fictional_bank.src.utilities import call_existing_tool

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
mcp = FastMCP("service", instructions="Read-only service request and status queries.")


@mcp.tool()
def get_service_requests(customer_id: str, limit: int = 50) -> dict:
    """Get a customer's service requests, newest first."""
    return call_existing_tool(get_service_requests_tool, customer_id=customer_id, limit=limit)

@mcp.tool()
def get_request_status(customer_id: str, request_id: str) -> dict:
    """Get details and status of a specific service request."""
    return call_existing_tool(get_request_status_tool, customer_id=customer_id, request_id=request_id)


@mcp.tool()
def get_pending_requests(customer_id: str, limit: int = 50) -> dict:
    """Get a customer's pending service requests."""
    return call_existing_tool(get_pending_requests_tool, customer_id=customer_id, limit=limit)


@mcp.tool()
def count_service_requests(customer_id: str) -> dict:
    """Count service requests by status and type."""
    return call_existing_tool(count_service_requests_tool, customer_id=customer_id)


if __name__ == "__main__":
    mcp.run(transport="stdio")
