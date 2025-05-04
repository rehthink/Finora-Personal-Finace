import pandas as pd

def preprocess_data(df):
    df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
    df["Month"] = df["Date"].dt.strftime("%B")
    return df

def filter_by_month(df, month):
    if month and month != "All":
        return df[df["Month"] == month]
    return df
