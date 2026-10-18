import pandas as pd
from langchain_core.tools import tool
from fictional_bank.config.data_loader import accounts_df, transactions_df, customers_df, get_customer_accounts_df



@tool
def get_customer_details_based_on_id(customer_id:str) -> list[dict]:
    """
    Get Customer Details for a given customer ID
    """
    customer_df = customers_df[customers_df['customer_id'].astype(str) == str(customer_id)]
    if customer_df.empty:
        return {"message": f"No customer found with ID {customer_id}"}
    return {"customer_details": customer_df.to_dict("records")}


@tool
def get_customer_accounts_based_on_customer_id(customer_id:str)->list[dict]:
    """
    Get all bank accounts belonging to a given customer ID.
    """
    customer_accounts_df = get_customer_accounts_df(customer_id)
    if customer_accounts_df.empty:
        return {"message": f"No accounts found for customer ID {customer_id}"}
    return {"accounts": customer_accounts_df.to_dict("records")}

@tool
def get_account_balance(customer_id:str, account_id:str) -> list[dict]:
    """
    Get Account Balance for a given Customer ID and Account ID
    """
    customer_accounts_df = get_customer_accounts_df(customer_id)
    if customer_accounts_df.empty:
        return {"message": f"No accounts found for customer ID {customer_id}"}
    matching_account = customer_accounts_df[customer_accounts_df['account_id'].astype(str) == str(account_id)]
    if matching_account.empty:
        return {"message": (f"Account {account_id} was not found "f"for customer ID {customer_id}")}
    return {"account": matching_account.to_dict("records")}
@tool
def get_total_balance(customer_id:str) -> list[dict]:
    """
    Get total balances for a customer, grouped by currency.
    """
    customer_accounts_df = get_customer_accounts_df(customer_id)
    if customer_accounts_df.empty:
        return {"message": f"No accounts found for customer ID {customer_id}"}

    totals = customer_accounts_df.groupby('currency')['balance'].sum()
    return {"customer_id" : customer_id, "total_balance_by_currency" : {str(currency): float(amount) for currency, amount in totals.items()}}


ACCOUNTS_TOOLS = [
    get_customer_details_based_on_id,
    get_customer_accounts_based_on_customer_id,
    get_account_balance,
    get_total_balance,
]