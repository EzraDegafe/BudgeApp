import logging

import pandas as pd
import streamlit as st

from budgeapp.db.connection import get_session
from budgeapp.pipeline.extract import SUPPORTED_EXTENSIONS, read_file
from budgeapp.pipeline.load import load
from budgeapp.pipeline.transform import REQUIRED_COLUMNS, transform

logger = logging.getLogger("budgeapp.pages.upload")

user_id = st.session_state.user_id

st.title("Import")
st.caption(
    f"Upload a CSV or Excel file with the columns {', '.join(REQUIRED_COLUMNS)}. "
    "You'll see a preview before anything is saved."
)

# Changing the key gives a fresh, empty uploader after a successful import.
st.session_state.setdefault("uploader_key", 0)
uploaded = st.file_uploader(
    "Transactions file",
    type=[ext.lstrip(".") for ext in SUPPORTED_EXTENSIONS],
    key=f"uploader_{st.session_state.uploader_key}",
)

if "import_result" in st.session_state:
    st.success(st.session_state.pop("import_result"))
    st.page_link("app_pages/home.py", label="See them on the dashboard", icon=":material/home:")

if uploaded is None:
    st.stop()

try:
    records, errors = transform(read_file(uploaded, uploaded.name))
except ValueError as exc:
    st.error(str(exc))
    st.stop()

if errors:
    with st.expander(f"{len(errors)} rows can't be imported and will be skipped", expanded=True):
        st.dataframe(
            pd.DataFrame([{"Row": e.row, "Problem": e.reason} for e in errors]),
            hide_index=True,
        )

if not records:
    st.warning("No rows in this file could be imported.")
    st.stop()

preview = pd.DataFrame(
    [
        {
            "Date": r.txn_date,
            "Description": r.name,
            "Type": r.txn_type,
            "Amount": r.amount_cents / 100,
        }
        for r in records
    ]
)
deposits = preview.loc[preview["Type"] == "deposit", "Amount"].sum()
expenses = preview.loc[preview["Type"] == "expense", "Amount"].sum()

st.subheader("Preview")
col1, col2, col3 = st.columns(3)
col1.metric("Transactions", len(records), border=True)
col2.metric("Deposits", f"${deposits:,.2f}", border=True)
col3.metric("Expenses", f"${expenses:,.2f}", border=True)
st.dataframe(
    preview,
    hide_index=True,
    column_config={"Amount": st.column_config.NumberColumn(format="dollar")},
)

if st.button(f"Import {len(records)} transactions", type="primary"):
    try:
        with get_session() as session:
            result = load(session, user_id, records, source=uploaded.name)
    except Exception:
        logger.exception("Import of %r for user %s crashed", uploaded.name, user_id)
        st.error("The import failed and nothing was saved. See logs/budgeapp.log for details.")
    else:
        message = f"Imported {result.added} transactions from {uploaded.name}."
        if result.skipped_duplicates:
            message += f" Skipped {result.skipped_duplicates} that were already imported."
        st.session_state.import_result = message
        st.session_state.uploader_key += 1
        st.rerun()
