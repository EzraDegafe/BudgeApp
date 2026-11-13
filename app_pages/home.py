from datetime import date

import pandas as pd
import streamlit as st

from budgeapp.db.connection import get_session
from budgeapp.db.repositories import TransactionRepo

st.title("Budget dashboard")
st.caption("A quick look at this month.")

today = date.today()
month_start = today.replace(day=1)

with get_session() as session:
    txns = TransactionRepo(session).list_between(month_start, today)
    rows = [
        {
            "Date": t.txn_date,
            "Name": t.name,
            "Type": t.txn_type,
            "Amount": t.amount_cents / 100,
            "Recurring": t.is_recurring,
        }
        for t in txns
    ]

df = pd.DataFrame(rows, columns=["Date", "Name", "Type", "Amount", "Recurring"])

income = df.loc[df["Type"] == "deposit", "Amount"].sum()
spending = df.loc[df["Type"] == "expense", "Amount"].sum()

col1, col2, col3 = st.columns(3)
col1.metric("Income", f"${income:,.2f}", border=True)
col2.metric("Spending", f"${spending:,.2f}", border=True)
col3.metric("Net", f"${income - spending:,.2f}", border=True)

st.subheader("Recent transactions")
if df.empty:
    st.info("No transactions yet this month. Import a file to get started.")
else:
    st.dataframe(
        df.head(10),
        hide_index=True,
        column_config={"Amount": st.column_config.NumberColumn(format="dollar")},
    )

st.divider()
st.subheader("Get started")
with st.container(horizontal=True):
    st.page_link("app_pages/upload.py", label="Import a file", icon=":material/upload_file:")
    st.page_link("app_pages/analytics.py", label="View analytics", icon=":material/bar_chart:")
