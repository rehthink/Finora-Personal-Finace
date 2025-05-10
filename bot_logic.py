# bot_logic.py
from groq import Groq
from dotenv import load_dotenv
import pandas as pd
from duckduckgo_search import DDGS
import os
import streamlit as st


# Try to load from Streamlit secrets
try:
    groq_api_key = st.secrets.get("GROQ_API_KEY")
except (AttributeError, KeyError, FileNotFoundError):
    # Fallback to .env if not found
    load_dotenv()
    groq_api_key = os.getenv("GROQ_API_KEY")

# Raise error if nothing is found
if not groq_api_key:
    raise ValueError("❌ GROQ_API_KEY not found in Streamlit secrets or .env!")

# Initialize the client
client = Groq(api_key=groq_api_key)


RELEVANT_KEYWORDS = [
    "revenue", "profit", "loss", "expense", "growth", "sales",
    "forecast", "summary", "trend", "balance", "income", "debt",
    "budget", "earning", "spending", "financial", "finance", "monthly budget"
    "annual budget", "cash flow", "investment", "asset", "liability","transactionid"
]

def search_web(query):
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=3)
        return "\n\n".join([r['body'] for r in results if 'body' in r])

def format_df_context(df: pd.DataFrame) -> str:
    """
    Convert a portion of the DataFrame to a human-readable string.
    """
    return df.to_string(index=False)

def is_relevant_query(query: str) -> bool:
    """
    Check if the query is related to finance.
    """
    return any(kw in query.lower() for kw in RELEVANT_KEYWORDS)

def financial_chatbot(df: pd.DataFrame, user_query: str, chat_history: list) -> str:
    """
    Handles query using Groq API with Gemma 2 9B IT model based on dataframe.
    """
    if not is_relevant_query(user_query):
        response_from_web = search_web(user_query)
        if response_from_web:
            return f"❌ I couldn’t find a direct answer from your financial data.\n\n🌐 However, Here’s some information I found on web that might help:\n\n{response_from_web}"

    context_data = format_df_context(df)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful financial assistant. "
                "Only use the provided financial data to answer the questions. "
                "Be concise, accurate, and admit if data is missing."
            )
        }
    ]

    for user_msg, bot_msg in chat_history:
        messages.append({"role": "user", "content": user_msg})
        messages.append({"role": "assistant", "content": bot_msg})

    messages.append({
        "role": "user",
        "content": f"Here is the data:\n{context_data}\n\nQuestion: {user_query}"
    })

    response = client.chat.completions.create(
        model="gemma2-9b-it", 
        messages=messages,
        temperature=0.5
    )

    return response.choices[0].message.content.strip()
