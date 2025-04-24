import streamlit as st

if not st.session_state.get("logged_in"):
    st.switch_page("login.py")