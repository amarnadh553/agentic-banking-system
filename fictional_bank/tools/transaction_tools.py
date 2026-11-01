import pandas as pd
from typing import Optional
from langchain_core.tools import tool
from fictional_bank.config.data_loader import get_customer_transactions_based_on_customer_id

DATE_FORMAT = "%d-%m-%Y"
DEFAULT_LIMIT = 50
MAX_LIMIT = 100


# Helpers for Transactions Tools

def load_transactions(customer_id: str):
    """Return a copy of the customer's transactions with parsed dates, or None if there are none."""
    df = get_customer_transactions_based_on_customer_id(customer_id)
    if df is None or df.empty:
        return None
    df = df.copy()
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    return df

def validate_limit(limit: int):
    """Return an error dict if the limit is invalid, otherwise None."""
    if not 1 <= limit <= MAX_LIMIT:
        return {"error": f"Limit must be between 1 and {MAX_LIMIT}"}
    return None

def parse_date_range(start_date: str, end_date: str):
    """Parse DD-MM-YYYY dates. Returns (start, end, error)."""
    try:
        start = pd.to_datetime(start_date, format=DATE_FORMAT, errors="raise").normalize()
        end = pd.to_datetime(end_date, format=DATE_FORMAT, errors="raise").normalize()
    except (ValueError, TypeError):
        return None, None, {"error": "Use DD-MM-YYYY for both dates"}
    if start > end:
        return None, None, {"error": "Start date must not be after end date"}
    return start, end, None


def filter_by_date_range(df, start, end):
    """Keep rows whose date falls between start and end, inclusive of the whole end day."""
    df = df.dropna(subset=["transaction_date"])
    dates = df["transaction_date"]
    return df[(dates >= start) & (dates < end + pd.Timedelta(days=1))]


def filter_by_type(df, transaction_type: str):
    return df[df["transaction_type"].astype(str).str.strip().str.lower() == transaction_type]


def newest_first(df):
    return df.sort_values(by="transaction_date", ascending=False, na_position="last")


def to_records(df, limit: int) -> list[dict]:
    """Take the first `limit` rows and convert them to JSON-friendly dicts (dates as DD-MM-YYYY)."""
    out = df.head(limit).copy()
    out["transaction_date"] = out["transaction_date"].dt.strftime(DATE_FORMAT)
    out = out.astype(object).where(out.notna(), None)
    return out.to_dict("records")


def paged_result(customer_id: str, df, limit: int, **extra) -> dict:
    """Build a result with a cap, newest first, and clear truncation information."""
    total_matches = len(df)
    records = to_records(newest_first(df), limit)
    result = {
        "customer_id": customer_id,
        **extra,
        "total_matches": total_matches,
        "returned_count": len(records),
        "truncated": total_matches > len(records),
        "transactions": records,
    }
    if result["truncated"]:
        result["note"] = f"Showing the {len(records)} newest of {total_matches} matching transactions."
    return result


def total_for_type(customer_id: str, transaction_type: str, start_date: Optional[str], end_date: Optional[str]) -> dict:
    """Sum amounts for one transaction type, grouped by currency, optionally within a date range."""
    if (start_date is None) != (end_date is None):
        return {"error": "Provide both start_date and end_date, or neither."}

    start = end = None
    if start_date is not None:
        start, end, error = parse_date_range(start_date, end_date)
        if error:
            return error

    df = load_transactions(customer_id)
    if df is None:
        return {"message": f"No transactions found for customer ID {customer_id}"}
    df = filter_by_type(df, transaction_type)
    period = "all time"
    if start is not None:
        df = filter_by_date_range(df, start, end)
        period = {"start_date": start.strftime(DATE_FORMAT), "end_date": end.strftime(DATE_FORMAT)}
    df = df.copy()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["amount"])
    if df.empty:
        return {
            "customer_id": customer_id,
            "transaction_type": transaction_type,
            "period": period,
            "totals_by_currency": {},
            "transaction_count": 0,
            "message": f"No {transaction_type} transactions found.",
        }
    if "currency" in df.columns:
        currency = df["currency"].fillna("UNKNOWN").astype(str)
    else:
        currency = pd.Series("NOT_SPECIFIED", index=df.index)
    grouped = df.groupby(currency)["amount"].agg(["sum", "count"])
    return {
        "customer_id": customer_id,
        "transaction_type": transaction_type,
        "period": period,
        "totals_by_currency": {str(c): float(row["sum"]) for c, row in grouped.iterrows()},
        "transaction_count": int(grouped["count"].sum()),
    }


# Tools for Transaction Agent

@tool
def get_recent_transactions(customer_id: str, limit: int = 10) -> dict:
    """
    Get a customer's most recent transactions, newest first.
    Limit must be between 1 and 100 (default 10).
    """
    error = validate_limit(limit)
    if error:
        return error
    df = load_transactions(customer_id)
    if df is None:
        return {"message": f"No transactions found for customer ID {customer_id}"}
    return paged_result(customer_id, df, limit)


@tool
def search_transactions_by_date(customer_id: str, start_date: str, end_date: str, limit: int = DEFAULT_LIMIT) -> dict:
    """
    Find a customer's transactions between two dates, inclusive, newest first.
    Use DD-MM-YYYY format for both dates.
    Returns at most `limit` transactions (1-100, default 50). If truncated is true,
    more matching transactions exist than were returned.
    """
    error = validate_limit(limit)
    if error:
        return error
    start, end, error = parse_date_range(start_date, end_date)
    if error:
        return error
    df = load_transactions(customer_id)
    if df is None:
        return {"message": f"No transactions found for customer ID {customer_id}"}
    filtered_df = filter_by_date_range(df, start, end)
    period = {"start_date": start.strftime(DATE_FORMAT), "end_date": end.strftime(DATE_FORMAT)}
    if filtered_df.empty:
        return {
            "customer_id": customer_id,
            **period,
            "total_matches": 0,
            "returned_count": 0,
            "truncated": False,
            "transactions": [],
            "message": "No transactions found within the specified date range.",
        }
    return paged_result(customer_id, filtered_df, limit, **period)


@tool
def filter_transactions_by_type(customer_id: str, transaction_type: str, limit: int = DEFAULT_LIMIT) -> dict:
    """
    Filter a customer's transactions by type, "debit" or "credit", newest first.
    Returns at most `limit` transactions (1-100, default 50). If truncated is true,
    more matching transactions exist than were returned.
    """
    error = validate_limit(limit)
    if error:
        return error
    transaction_type = transaction_type.strip().lower()
    if transaction_type not in ("debit", "credit"):
        return {"error": "Transaction type must be debit or credit."}
    df = load_transactions(customer_id)
    if df is None:
        return {"message": f"No transactions found for customer ID {customer_id}"}
    filtered_df = filter_by_type(df, transaction_type)
    if filtered_df.empty:
        return {
            "customer_id": customer_id,
            "transaction_type": transaction_type,
            "total_matches": 0,
            "returned_count": 0,
            "truncated": False,
            "transactions": [],
            "message": f"No {transaction_type} transactions found.",
        }
    return paged_result(customer_id, filtered_df, limit, transaction_type=transaction_type)


@tool
def calculate_total_debits(customer_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> dict:
    """
    Calculate the total debit amount for a customer, grouped by currency.
    Optionally limit to a period by giving BOTH start_date and end_date in DD-MM-YYYY
    format (inclusive). With no dates, all debits are included.
    """
    return total_for_type(customer_id, "debit", start_date, end_date)


@tool
def calculate_total_credits(customer_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> dict:
    """
    Calculate the total credit amount for a customer, grouped by currency.
    Optionally limit to a period by giving BOTH start_date and end_date in DD-MM-YYYY
    format (inclusive). With no dates, all credits are included.
    """
    return total_for_type(customer_id, "credit", start_date, end_date)


TRANSACTIONS_TOOLS = [
    get_recent_transactions,
    search_transactions_by_date,
    filter_transactions_by_type,
    calculate_total_debits,
    calculate_total_credits,
]