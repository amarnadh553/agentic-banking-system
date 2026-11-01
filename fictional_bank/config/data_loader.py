import os
from pathlib import Path
import pandas as pd
# DATA_DIR = os.getcwd()+os.sep+'data'
# DATA_DIR = Path.cwd() / "data"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR = PROJECT_ROOT / "data"
def load_csv(file_name:str) -> pd.DataFrame:
    path = DATA_DIR / file_name
    if not path.exists():
        raise FileNotFoundError(f"File {file_name} not found in {DATA_DIR}")
    df = pd.read_csv(path)
    df = df.loc[:, ~df.columns.str.match('^Unnamed')]

    for column in df.select_dtypes(include=['object', 'str']).columns:
        df[column] = df[column].str.strip()
    return df

accounts_df = load_csv('accounts.csv')
customers_df = load_csv('customers.csv')
transactions_df = load_csv("transactions.csv")
service_requests_df = load_csv("service_requests.csv")

transactions_df['transaction_date'] = pd.to_datetime(transactions_df['transaction_date'], errors='coerce')
service_requests_df['request_date'] = pd.to_datetime(service_requests_df['request_date'], errors='coerce')

def _same_id(series: pd.Series, customer_id) -> pd.Series:
    return series.astype(str).str.strip().str.upper() == str(customer_id).strip().upper()

def get_customer_accounts_df(customer_id:str)->pd.DataFrame:
    """Get Accounts for a given customer ID"""
    customer_accounts_df = accounts_df[_same_id(accounts_df['customer_id'], customer_id)]
    return customer_accounts_df


def get_customer_transactions_based_on_customer_id(customer_id:str)->pd.DataFrame:
    """Get Transactions for a given customer ID"""
    customer_accounts_df = get_customer_accounts_df(customer_id)
    customer_transactions = customer_accounts_df['account_id'].to_list()
    customer_transactions_df = transactions_df[transactions_df['account_id'].isin(customer_transactions)]
    return customer_transactions_df

def get_customer_service_requests_based_on_customer_id(customer_id):
    return service_requests_df[service_requests_df["customer_id"].astype(str).str.strip().str.upper() == str(customer_id).strip().upper()]
# 
# print(accounts_df.head(1))
# print(customers_df.head(1))
# print(transactions_df.head(1))
# print(service_requests_df.head(1))
