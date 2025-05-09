import streamlit as st
from api_handler import fetch_transactions, add_transaction
from utils import preprocess_data, filter_by_month

import plotly.express as px
import pandas as pd

# Set up page configuration
st.set_page_config(page_title="Finora", layout="wide")

# Create a cached function for fetching and preprocessing data
@st.cache_data(ttl=300)  # Cache for 5 minutes (300 seconds)
def get_cached_data():
    """Fetch and preprocess data with caching"""
    try:
        df = fetch_transactions()
        return preprocess_data(df)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Load data using the cached function
df = get_cached_data()
if df is None:
    st.stop()


st.markdown("""
    <h1 style='text-align: center; font-size: 28px; margin-top: 0;'>
       Finora - Finance Tracker
    </h1>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Summary", "📄 Transactions", "➕ Manage"])

# === Page: Summary ===
with tab1:
    #st.markdown("<h2 style='text-align: left; font-size: 20px;'>📊 Finance Summary</h2>", unsafe_allow_html=True)

    # Month Filter
    months = ["All"] + sorted(df["Month"].dropna().unique())
    selected_month = st.selectbox("📅 Filter by Month", months)
    
    # Use cached filter function
    @st.cache_data
    def get_filtered_data(dataframe, month):
        return filter_by_month(dataframe, month)
    
    filtered_df = get_filtered_data(df, selected_month)

    # Calculate summary statistics
    @st.cache_data
    def calculate_summary(dataframe):
        income = dataframe[dataframe['Type'] == 'Income']['Amount'].sum()
        expense = dataframe[dataframe['Type'] == 'Expenses']['Amount'].sum()
        savings = income - expense
        return income, expense, savings
    
    income, expense, savings = calculate_summary(filtered_df)
    st.markdown(
        f"""
            <div style="display: flex; gap: 1px;">
                <div style="text-align: center;">
                    <p style="font-weight: bold; font-size: 20px;">💲 Total Income</p>
                    <p style="font-size: 18px; text-align: center;">₹ {income:,.2f}</p>                            
                    </div>
                    <div style="text-align: center; margin-left: 35px;">
                            <p style="font-weight: bold; font-size: 20px;">📊 Total Expense</p>
                            <p style="font-size: 18px; text-align: center;">₹ {expense:,.2f}</p>
                    </div>
                    <div style="text-align: center; margin-left: 35px;">
                            <p style="font-weight: bold; font-size: 20px;">💰 Total Savings</p>
                            <p style="font-size: 18px; text-align: center;">₹ {savings:,.2f}</p>
                    </div>
                </div>

                    """,
                    unsafe_allow_html=True
        )


    st.markdown("---")
    st.markdown("<h2 style='text-align: left; font-size: 24px;'>📉 Income vs Expense (Monthly)</h2>", unsafe_allow_html=True)
    
    # Cache chart data preparation
    @st.cache_data
    def prepare_monthly_chart_data(dataframe):
        return dataframe.groupby(["Month", "Type"])["Amount"].sum().reset_index()
    
    hist_df = prepare_monthly_chart_data(filtered_df)
    
    fig_hist = px.bar(
        hist_df,
        x="Amount",
        y="Month",
        color="Type",
        barmode="group",
        title="Monthly Income and Expenses Comparison",
        orientation='h'  # Change to horizontal
    )

    fig_hist.update_traces(
        texttemplate='₹%{x:,.2f}',
        textposition='inside',
        insidetextanchor='middle'
    )

    # Set figure layout size and spacing
    fig_hist.update_layout(
        height=200,   # Adjust height for better bar spacing
        width=500,   # Optional: specify width (or omit to use container width)
        bargap=.2,   # Space between bar groups
        margin=dict(l=80, r=40, t=60, b=60)
    )

    st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("### 📦 Income & Expense by Category")
    
    # Cache stacked chart data preparation
    @st.cache_data
    def prepare_stacked_chart_data(dataframe):
        stacked_df = dataframe.groupby(["Category", "Type"])["Amount"].sum().reset_index()
        stacked_pivot = stacked_df.pivot(index="Category", columns="Type", values="Amount").fillna(0).reset_index()
        return pd.melt(stacked_pivot, id_vars=["Category"], value_vars=["Income", "Expenses"],
                        var_name="Type", value_name="Amount")
    
    stacked_melted = prepare_stacked_chart_data(filtered_df)

    fig_stacked = px.bar(
        stacked_melted,
        x="Amount",
        y="Category",
        color="Type",
        title="Income and Expenses by Category",
        text="Amount",
        orientation='h'
    )

    fig_stacked.update_traces(texttemplate='₹%{text:.2s}', textposition='inside',insidetextanchor='middle')
    #fig_stacked.update_layout(barmode="stack", xaxis_title="Amount (₹)", yaxis_title="Category")
    # Set figure layout size and spacing
    fig_stacked.update_layout(
        height=400,   # Adjust height for better bar spacing
        width=500,   # Optional: specify width (or omit to use container width)
        bargap=.2,   # Space between bar groups
        margin=dict(l=80, r=40, t=60, b=60)
    )

    st.plotly_chart(fig_stacked, use_container_width=True)

    st.markdown("### 📊 Income & Expense Distribution")
    col1, col2 = st.columns(2)


    # Prepare pie chart data (cached for performance)
    @st.cache_data
    def prepare_pie_chart_data(dataframe, type_filter):
        return dataframe[dataframe['Type'] == type_filter]

    # Title
    st.markdown("### 🔍 Category-wise Summary")
    #st.write("Click to expand each chart and explore category-wise distribution.")

    # Expenses Chart
    expenses_pie_data = prepare_pie_chart_data(filtered_df, 'Expenses')
    exp_fig = px.pie(
        expenses_pie_data,
        names="Category",
        values="Amount",
        title="Expenses by Category",
        hole=0.4
    )
    exp_fig.update_traces(
        textinfo='percent+label',
        pull=[0.05]*len(expenses_pie_data),
        hoverinfo='label+percent+value'
    )
    exp_fig.update_layout(
        margin=dict(t=40, b=10),
        legend_title_text='Categories',
        showlegend=True
    )

    with st.expander("📉 View Expenses by Category", expanded=True):
        st.plotly_chart(exp_fig, use_container_width=True)

    # Income Chart
    income_pie_data = prepare_pie_chart_data(filtered_df, 'Income')
    inc_fig = px.pie(
        income_pie_data,
        names="Category",
        values="Amount",
        title="Income by Category",
        hole=0.4
    )
    inc_fig.update_traces(
        textinfo='percent+label',
        pull=[0.05]*len(income_pie_data),
        hoverinfo='label+percent+value'
    )
    inc_fig.update_layout(
        margin=dict(t=40, b=10),
        legend_title_text='Categories',
        showlegend=True
    )

    with st.expander("💰 View Income by Category", expanded=True):
        st.plotly_chart(inc_fig, use_container_width=True)

    # Refresh Button with cache clearing
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

# === Page: Transactions ===
with tab2:
    st.markdown("<h2 style='text-align: left; font-size: 20px;'>📄 All Transactions</h2>", unsafe_allow_html=True)

    transaction_id_col = df.columns[1]
    
    @st.cache_data
    def get_valid_transactions(dataframe, id_col):
        return dataframe[dataframe[id_col].notnull()]
    
    valid_transactions = get_valid_transactions(df, transaction_id_col)

    # Display filtered data
    if valid_transactions.empty:
        st.info("No transactions available for the selected month.")
    else:
        st.dataframe(valid_transactions.sort_values(by="Date", ascending=False), use_container_width=True)

    st.markdown("---")

    # Download button for CSV
    # csv = filtered_df.to_csv(index=False).encode('utf-8')
    # st.download_button("📥 Download as CSV", data=csv, file_name="transactions.csv", mime="text/csv")

# === Page: Add Transaction ===
with tab3:
    st.markdown("<h2 style='text-align: left; font-size: 20px;'>➕ Register New Transaction</h2>", unsafe_allow_html=True)

    with st.expander("📝 Add Transaction", expanded=True):
      with st.form("new_transaction", clear_on_submit=True):
        st.markdown("<h2 style='text-align: left; font-size: 20px;'>🧾 Transaction Details</h2>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("📅 Date")
            amount = st.number_input("💰 Amount (₹)", min_value=0.0, format="%.2f")
        with col2:
            method = st.selectbox("💳 Payment Method", ["Cash", "Card", "UPI", "Other"])
            txn_type = st.selectbox("📂 Type", ["Expenses", "Income"])

        st.markdown("#### 🗂️ Category & Remarks")
        category = st.selectbox("🏷️ Category", [
            "Home", "Food", "Utilities", "Other", "Salary", "Investments", "EMI", 
            "Medical", "Travelling", "Family", "Outing", "Interest", "Savings"
        ])
        remark = st.text_area("📝 Remark")

        st.markdown("")
        submitted = st.form_submit_button("✅ Add Transaction")
        if submitted:
            txn_data = {
                "date": str(date),
                "amount": amount,
                "method": method,
                "category": category,
                "remark": remark,
                "type": txn_type
            }
            try:
                result = add_transaction(txn_data)
                # Clear all cached data when a new transaction is added
                st.cache_data.clear()
                st.success("✅ Transaction added successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to add transaction: {e}")