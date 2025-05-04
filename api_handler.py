import requests
import pandas as pd

API_BASE_URL = "https://script.google.com/macros/s/AKfycbxj7Z4J2dwkJvxzJsv2qEewjTcERV3IULhw4kZ4JYMr0x258eDq4RCn3baeMQISFCw_iQ"  # Replace with actual base

def fetch_transactions():
    response = requests.get(f"{API_BASE_URL}/exec")
    response.raise_for_status()
    data = response.json()

    # Define the headers manually
    headers = ["TransactionId","Date", "Amount", "Method", "Category", "Remark", "Type", "Month"]

    # Convert to DataFrame
    df = pd.DataFrame(data, columns=headers)

    # Optional: Standardize column names
    df.columns = df.columns.str.strip().str.title()

    return df

def add_transaction(transaction):
    try:
        response = requests.post(f"{API_BASE_URL}/exec", json=transaction)
        response.raise_for_status()
        
        # Try parsing JSON response (if your API supports it)
        try:
            return response.json()
        except ValueError:
            # Response is not JSON, but still succeeded
            return {"status": "success", "message": "Transaction added successfully (no JSON response)."}
    
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"API error: {e}")
