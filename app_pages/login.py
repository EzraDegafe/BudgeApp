import streamlit as st

from budgeapp.db.connection import get_session
from budgeapp.db.repositories import UserRepo


def _log_in(user_id: int, username: str) -> None:
    st.session_state.user_id = user_id
    st.session_state.username = username
    st.rerun()  # app.py rebuilds the navigation with the logged-in pages


st.title("Budget app")
st.caption("Log in or create an account to see your transactions.")

login_tab, register_tab = st.tabs(["Log in", "Register"])

with login_tab:
    with st.form("login"):
        username = st.text_input("Username").strip()
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in", type="primary")

    if submitted:
        with get_session() as session:
            user = UserRepo(session).authenticate(username, password)
            user_id = user.id if user else None
        if user_id is None:
            st.error("Wrong username or password.")
        else:
            _log_in(user_id, username)

with register_tab:
    with st.form("register"):
        new_username = st.text_input("Username", key="reg_username").strip()
        new_password = st.text_input("Password", type="password", key="reg_password")
        confirm = st.text_input("Confirm password", type="password", key="reg_confirm")
        created = st.form_submit_button("Create account", type="primary")

    if created:
        if not new_username or not new_password:
            st.error("Enter a username and a password.")
        elif len(new_username) > 50:
            st.error("Usernames can be at most 50 characters.")
        elif new_password != confirm:
            st.error("The passwords don't match.")
        else:
            try:
                with get_session() as session:
                    user_id = UserRepo(session).register(new_username, new_password).id
            except ValueError:
                st.error("That username is already taken.")
            else:
                _log_in(user_id, new_username)
