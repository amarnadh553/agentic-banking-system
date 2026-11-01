import pandas as pd
from langchain_core.tools import tool
from fictional_bank.config.data_loader import get_customer_service_requests_based_on_customer_id

DATE_FORMAT = "%d-%m-%Y"
DEFAULT_LIMIT = 50
MAX_LIMIT = 100

# Statuses that mean a request is finished. Anything else counts as pending/open.
# Check these against the real values in the `status` column of service_requests.csv.
# CLOSED_STATUSES = {'completed', 'processing', 'rejected', 'submitted'}
# CLOSED_STATUSES = {'completed', 'rejected', 'cancelled', 'closed', 'processing', 'submitted'}
CLOSED_STATUSES = {'completed', 'rejected', 'cancelled', 'closed'}


# Helpers for Service tools

def load_requests(customer_id: str):
    """Return a copy of the customer's service requests with parsed dates, or None if there are none."""
    df = get_customer_service_requests_based_on_customer_id(customer_id)
    if df is None or df.empty:
        return None
    df = df.copy()
    df["request_date"] = pd.to_datetime(df["request_date"], errors="coerce")
    return df


def normalize(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower()


def newest_first(df):
    return df.sort_values(by="request_date", ascending=False, na_position="last")


def to_records(df, limit: int) -> list[dict]:
    """Take the first `limit` rows as JSON-friendly dicts (dates as DD-MM-YYYY, NaN as None)."""
    out = df.head(limit).copy()
    out["request_date"] = out["request_date"].dt.strftime(DATE_FORMAT)
    out = out.astype(object).where(out.notna(), None)
    return out.to_dict("records")


def paged_result(customer_id: str, df, limit: int, **extra) -> dict:
    total_matches = len(df)
    records = to_records(newest_first(df), limit)
    result = {
        "customer_id": customer_id,
        **extra,
        "total_matches": total_matches,
        "returned_count": len(records),
        "truncated": total_matches > len(records),
        "requests": records,
    }
    if result["truncated"]:
        result["note"] = f"Showing the {len(records)} newest of {total_matches} matching requests."
    return result


def validate_limit(limit: int):
    if not 1 <= limit <= MAX_LIMIT:
        return {"error": f"Limit must be between 1 and {MAX_LIMIT}"}
    return None


# Tools for Service Requests

@tool
def get_service_requests(customer_id: str, limit: int = DEFAULT_LIMIT) -> dict:
    """
    Get all service requests for a customer, newest first.
    Returns at most `limit` requests (1-100, default 50). If truncated is true,
    more requests exist than were returned.
    """
    error = validate_limit(limit)
    if error:
        return error
    df = load_requests(customer_id)
    if df is None:
        return {"message": f"No service requests found for customer ID {customer_id}"}
    return paged_result(customer_id, df, limit)


@tool
def get_request_status(customer_id: str, request_id: str) -> dict:
    """
    Get the status and details of ONE service request for a given customer ID and request ID.
    """
    df = load_requests(customer_id)
    if df is None:
        return {"message": f"No service requests found for customer ID {customer_id}"}
    wanted = str(request_id).strip().lower()
    match = df[normalize(df["request_id"]) == wanted]
    if match.empty:
        return {"message": f"Request {request_id} was not found for customer ID {customer_id}"}
    return {"customer_id": customer_id, "request": to_records(match, 1)[0]}


@tool
def get_pending_requests(customer_id: str, limit: int = DEFAULT_LIMIT) -> dict:
    """
    Get a customer's pending (not yet completed, rejected, cancelled or closed) service
    requests, newest first. Returns at most `limit` requests (1-100, default 50).
    """
    error = validate_limit(limit)
    if error:
        return error
    df = load_requests(customer_id)
    if df is None:
        return {"message": f"No service requests found for customer ID {customer_id}"}
    pending_df = df[~normalize(df["status"]).isin(CLOSED_STATUSES)]
    if pending_df.empty:
        return {
            "customer_id": customer_id,
            "total_matches": 0,
            "returned_count": 0,
            "truncated": False,
            "requests": [],
            "message": "No pending service requests found.",
        }
    return paged_result(customer_id, pending_df, limit)


@tool
def count_service_requests(customer_id: str) -> dict:
    """
    Count a customer's service requests: the total, plus a breakdown by status and by request type.
    """
    df = load_requests(customer_id)
    if df is None:
        return {"message": f"No service requests found for customer ID {customer_id}"}
    by_status = df["status"].fillna("UNKNOWN").astype(str).str.strip().value_counts()
    by_type = df["request_type"].fillna("UNKNOWN").astype(str).str.strip().value_counts()
    return {
        "customer_id": customer_id,
        "total_requests": int(len(df)),
        "by_status": {str(k): int(v) for k, v in by_status.items()},
        "by_request_type": {str(k): int(v) for k, v in by_type.items()},
    }


SERVICE_TOOLS = [
    get_service_requests,
    get_request_status,
    get_pending_requests,
    count_service_requests,
]