"""Streamlit authentication UI components."""

import streamlit as st

from src.shared.auth.application.services.AuthService import AuthService
from src.shared.auth.infrastructure.repositories.UserRepository import SqliteUserRepository
from src.shared.auth.domain.exceptions import (
    InvalidCredentialsError,
    UserNotApprovedError,
    UserAlreadyExistsError,
    InvalidEmail,
)
from src.shared.auth.domain.value_objects.Password import WeakPasswordError


def render_login():
    """
    Streamlit login/signup UI.
    Uses AuthService from application layer.
    """
    st.title("🔐 Login to Berlin Geo Heatmap")
    
    # Initialize service
    user_repo = SqliteUserRepository()
    auth_service = AuthService(user_repo)
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        email = st.text_input("Email", key="l_mail")
        password = st.text_input("Password", type="password", key="l_pass")
        
        if st.button("Login"):
            if not password.strip():
                st.error("Please enter your password.")
            else:
                try:
                    user = auth_service.login(email, password)
                    st.session_state['user'] = user
                    st.success(f"Welcome, {user.email.value}!")
                    st.rerun()
                except (InvalidCredentialsError, UserNotApprovedError) as e:
                    st.error(str(e))

    with tab2:
        email = st.text_input("Email", key="s_mail")
        password = st.text_input("Password", type="password", key="s_pass")
        role = st.selectbox("Role", ["user", "operator"], key="s_role")
        
        station_label = None
        if role == "operator":
            station_label = st.text_input("Station Name", key="s_station")
        
        if st.button("Sign Up"):
            try:
                user = auth_service.signup(
                    email_str=email,
                    plain_password=password,
                    role_str=role,
                    station_label=station_label
                )
                
                if user.role.requires_approval():
                    st.info("Account created! Awaiting admin approval.")
                else:
                    st.success("Account created! You can login now.")
                    
            except (InvalidEmail, WeakPasswordError, ValueError, UserAlreadyExistsError) as e:
                st.error(str(e))
