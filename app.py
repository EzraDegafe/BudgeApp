import streamlit as st

from budgeapp.db.connection import init_db

st.set_page_config(page_title="Budget app", page_icon="💰", layout="wide")


@st.cache_resource
def _setup_db() -> None:
    # Runs once per server process, not on every rerun.
    init_db()


_setup_db()

pages = [
    st.Page("app_pages/home.py", title="Home", icon=":material/home:", default=True),
    st.Page("app_pages/analytics.py", title="Analytics", icon=":material/bar_chart:"),
    st.Page("app_pages/upload.py", title="Import", icon=":material/upload_file:"),
]

nav = st.navigation(pages)
nav.run()
