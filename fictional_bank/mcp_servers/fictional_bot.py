# # Standard library
# import logging
# import sys

# # Third-party packages
# from mcp.server.fastmcp import FastMCP

# # Local imports
# from fictional_bank.tools import customer_details_tool, customer_accounts_tool, account_balance_tool, total_balance_tool
# from fictional_bank.tools.transaction_tools import (
#     get_recent_transactions as recent_transactions_tool,
#     search_transactions_by_date as search_transactions_tool,
#     filter_transactions_by_type as filter_by_type_tool,
#     calculate_total_debits as total_debits_tool,
#     calculate_total_credits as total_credits_tool,
# )

# from fictional_bank.tools.service_tools import (
#     get_service_requests as get_service_requests_tool,
#     get_request_status as get_request_status_tool,
#     get_pending_requests as get_pending_requests_tool,
#     count_service_requests as count_service_requests_tool,
# )
# from fictional_bank.src.utilities import call_existing_tool

# mcp = FastMCP("fictional_bot")

# # Accounts Tools
# @mcp.tool()
# def get_customer_details_based_on_id(customer_id: str) -> dict:
#     return call_existing_tool(customer_details_tool, customer_id=customer_id)

# @mcp.tool()
# def get_customer_accounts_based_on_customer_id(customer_id: str) -> dict:
#     return call_existing_tool(customer_accounts_tool, customer_id=customer_id)

# @mcp.tool()
# def get_account_balance(customer_id: str, account_id: str) -> dict:
#     return call_existing_tool(account_balance_tool, customer_id=customer_id, account_id=account_id)

# @mcp.tool()
# def get_total_balance(customer_id: str) -> dict:
#     return call_existing_tool(total_balance_tool, customer_id=customer_id)

# # ---------------------------------------------------------------------------------------------
# # ---------------------------------------------------------------------------------------------
# # ---------------------------------------------------------------------------------------------
# # Transactions Tools
# @mcp.tool()
# def get_recent_transactions(customer_id: str, limit: int = 10) -> dict:
#     """Get a customer's most recent transactions, newest first."""
#     return call_existing_tool(recent_transactions_tool, customer_id=customer_id, limit=limit)

# @mcp.tool()
# def search_transactions_by_date(customer_id: str, start_date: str, end_date: str, limit: int = 50) -> dict:
#     """Search transactions within an inclusive date range."""
#     return call_existing_tool(search_transactions_tool,customer_id=customer_id, start_date=start_date, end_date=end_date, limit=limit)

# @mcp.tool()
# def filter_transactions_by_type(customer_id: str, transaction_type: str, limit: int = 50) -> dict:
#     """Filter a customer's transactions by debit or credit."""
#     return call_existing_tool(filter_by_type_tool, customer_id=customer_id, transaction_type=transaction_type, limit=limit)

# @mcp.tool()
# def calculate_total_debits(customer_id: str,start_date: str | None = None, end_date: str | None = None) -> dict:
#     """Calculate total debits, optionally within a date range."""
#     return call_existing_tool(total_debits_tool, customer_id=customer_id, start_date=start_date, end_date=end_date)

# @mcp.tool()
# def calculate_total_credits(customer_id: str,start_date: str | None = None, end_date: str | None = None) -> dict:
#     """Calculate total credits, optionally within a date range."""
#     return call_existing_tool(total_credits_tool, customer_id=customer_id, start_date=start_date, end_date=end_date)


# # ---------------------------------------------------------------------------------------------
# # ---------------------------------------------------------------------------------------------
# # ---------------------------------------------------------------------------------------------
# # Service Tools
# @mcp.tool()
# def get_service_requests(customer_id: str, limit: int = 50) -> dict:
#     """Get a customer's service requests, newest first."""
#     return call_existing_tool(get_service_requests_tool, customer_id=customer_id, limit=limit)

# @mcp.tool()
# def get_request_status(customer_id: str, request_id: str) -> dict:
#     """Get the details and status of a specific service request."""
#     return call_existing_tool(get_request_status_tool, customer_id=customer_id, request_id=request_id)


# @mcp.tool()
# def get_pending_requests(customer_id: str, limit: int = 50) -> dict:
#     """Get a customer's pending service requests."""
#     return call_existing_tool(get_pending_requests_tool, customer_id=customer_id, limit=limit)


# @mcp.tool()
# def count_service_requests(customer_id: str) -> dict:
#     """Count service requests by status and request type."""
#     return call_existing_tool(count_service_requests_tool, customer_id=customer_id)

# if __name__ == "__main__":
#     mcp.run(transport="stdio")