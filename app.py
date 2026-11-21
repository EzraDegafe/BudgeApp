import streamlit as st

from budgeapp.db.connection import init_db

st.set_page_config(page_title="Budget app", page_icon="💰", layout="wide")


@st.cache_resource
def _setup_db() -> None:
    # Runs once per server process, not on every rerun.
    init_db()


_setup_db()

if "user_id" not in st.session_state:
    # Not logged in: the login page is the only page.
    pages = [st.Page("app_pages/login.py", title="Log in", icon=":material/login:")]
else:
    pages = [
        st.Page("app_pages/home.py", title="Home", icon=":material/home:", default=True),
        st.Page("app_pages/analytics.py", title="Analytics", icon=":material/bar_chart:"),
        st.Page("app_pages/upload.py", title="Import", icon=":material/upload_file:"),
    ]
    with st.sidebar:
        st.write(f"Logged in as **{st.session_state.username}**")
        if st.button("Log out", icon=":material/logout:"):
            st.session_state.clear()
            st.rerun()

nav = st.navigation(pages)
nav.run()
