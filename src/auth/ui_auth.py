import streamlit as st
from src.auth.auth_handler import AuthHandler

def render_login():
    st.title("🔐 Login to Berlin Geo Heatmap")
    
    handler = AuthHandler()
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        email = st.text_input("Email", key="l_mail")
        password = st.text_input("Password", type="password", key="l_pass")
        if st.button("Login"):
            user, msg = handler.login(email, password)
            if user:
                st.session_state['user'] = user
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    with tab2:
        email = st.text_input("Email", key="s_mail")
        password = st.text_input("Password", type="password", key="s_pass")
        role = st.selectbox("Role", ["user", "operator"], key="s_role")
        if st.button("Sign Up"):
            success, msg = handler.signup(email, password, role)
            if success: st.success(msg)
            else: st.error(msg)