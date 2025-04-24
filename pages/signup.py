# signup.py
import streamlit as st
import requests
import json
from utils import hash_password

st.set_page_config(page_title="Signup", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {display: none;}
    [data-testid="collapsedControl"] {display: none;}
    </style>
""", unsafe_allow_html=True)

st.title("📝 Sign Up")

username = st.text_input("Choose a username")
password = st.text_input("Choose a password", type="password")

USER_DB = "users.json"

def load_users():
    with open(USER_DB, "r") as f:
        return json.load(f)


if st.button("Sign Up"):
    if username and password:
        res = requests.post("http://localhost:8000/signup", json={"username": username, "password": password})
        if res.json().get("success"):
            st.success("Signup successful!")
            st.session_state.logged_in = True
            st.session_state.username = username
            st.switch_page("pages/ui.py")  # Switch to ui page after successful signup
        else:
            st.error(res.json().get("detail", "Signup failed"))
    else:
        st.warning("Please fill in both fields.")

if st.button("Go to Login"):
    st.switch_page("login.py")  # Switch to login page (without '.py')