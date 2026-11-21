import logging

import streamlit as st

from budgeapp.db.connection import get_session
from budgeapp.db.repositories import UserRepo

logger = logging.getLogger("budgeapp.pages.login")

DB_ERROR = "Something went wrong talking to the database. See logs/budgeapp.log for details."


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
        logger.info("Login attempt for %r", username)
        try:
            with get_session() as session:
                user = UserRepo(session).authenticate(username, password)
                user_id = user.id if user else None
        except Exception:
            logger.exception("Login for %r crashed", username)
            st.error(DB_ERROR)
        else:
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
        logger.info("Registration attempt for %r", new_username)
        problem = None
        if not new_username or not new_password:
            problem = "Enter a username and a password."
        elif len(new_username) > 50:
            problem = "Usernames can be at most 50 characters."
        elif new_password != confirm:
            problem = "The passwords don't match."

        if problem:
            logger.info("Registration for %r refused: %s", new_username, problem)
            st.error(problem)
        else:
            try:
                with get_session() as session:
                    user_id = UserRepo(session).register(new_username, new_password).id
            except ValueError:
                st.error("That username is already taken.")
            except Exception:
                logger.exception("Registration for %r crashed", new_username)
                st.error(DB_ERROR)
            else:
                _log_in(user_id, new_username)
