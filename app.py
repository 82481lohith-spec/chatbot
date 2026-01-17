import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# --- 1. Setup & Functions ---
FILE_NAME = "expenses.csv"

def load_data():
    """Loads the CSV file and ensures the Date column is actually dates."""
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        # FIX: Convert the 'Date' column to datetime objects
        df["Date"] = pd.to_datetime(df["Date"])
        return df
    else:
        return pd.DataFrame(columns=["Date", "Category", "Amount", "Description"])

def save_data(df):
    """Saves the updated dataframe to CSV."""
    df.to_csv(FILE_NAME, index=False)

def convert_df_to_excel(df):
    """Converts the dataframe to an Excel file in memory."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Expenses')
    processed_data = output.getvalue()
    return processed_data

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
            "Date": [pd.to_datetime(date)],  # Ensure new data is also datetime
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

    # --- PIE CHART FEATURE ---
    st.subheader("Expenses by Category")
    # Group data by category to sum amounts
    category_totals = df.groupby("Category")["Amount"].sum().reset_index()
    
    # Create the chart
    fig = px.pie(category_totals, values='Amount', names='Category', 
                 title='Where is your money going?', hole=0.3)
    st.plotly_chart(fig, use_container_width=True)

    # Show Dataframe sorted by Date
    st.subheader("Recent Expenses")
    st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)

    # --- EXCEL DOWNLOAD FEATURE ---
    st.subheader("Download Data")
    excel_data = convert_df_to_excel(df)
    st.download_button(
        label="📥 Download as Excel",
        data=excel_data,
        file_name='my_expenses.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

else:
    st.info("No expenses added yet. Use the sidebar to add your first expense!")
def load_data():
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        # ⬇️ THIS LINE IS REQUIRED TO FIX THE SORTING ERROR
        df["Date"] = pd.to_datetime(df["Date"]) 
        return df
    else:
        return pd.DataFrame(columns=["Date", "Category", "Amount", "Description"])
