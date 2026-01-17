import streamlit as st
import pandas as pd
import os

# --- 1. Setup & Functions ---
FILE_NAME = "expenses.csv"

def load_data():
    """Loads the CSV file if it exists, otherwise creates an empty one."""
    if os.path.exists(FILE_NAME):
        return pd.read_csv(FILE_NAME)
    else:
        return pd.DataFrame(columns=["Date", "Category", "Amount", "Description"])

def save_data(df):
    """Saves the updated dataframe to CSV."""
    df.to_csv(FILE_NAME, index=False)

# --- 2. App Layout ---
st.set_page_config(page_title="My Monthly Expense Tracker", layout="centered")
st.title("💰 Monthly Expense Tracker")

# Load existing data
df = load_data()

# --- 3. Input Form (Sidebar) ---
st.sidebar.header("Add New Expense")
with st.sidebar.form("expense_form", clear_on_submit=True):
    date = st.date_input("Date")
    category = st.selectbox("Category", ["Food", "Transport", "Rent", "Entertainment", "Utilities", "Other"])
    amount = st.number_input("Amount", min_value=0.0, format="%.2f")
    description = st.text_input("Description (Optional)")
    
    submitted = st.form_submit_button("Add Expense")

    if submitted:
        new_data = pd.DataFrame({
            "Date": [date],
            "Category": [category],
            "Amount": [amount],
            "Description": [description]
        })
        # Combine old data with new data
        df = pd.concat([df, new_data], ignore_index=True)
        save_data(df)
        st.sidebar.success("Expense added!")

# --- 4. Dashboard (Main Panel) ---
if not df.empty:
    # Basic Stats
    total_spent = df["Amount"].sum()
    st.metric("Total Spent", f"${total_spent:,.2f}")

    # Show Dataframe
    st.subheader("Recent Expenses")
    st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)

    # Simple Chart
    st.subheader("Expenses by Category")
    category_totals = df.groupby("Category")["Amount"].sum()
    st.bar_chart(category_totals)
else:
    st.info("No expenses added yet. Use the sidebar to add your first expense!")
