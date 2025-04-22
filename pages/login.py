# login.py
import streamlit as st
import requests
import json
import datetime
from utils import verify_password


st.title("🔐 Login")

username = st.text_input("Username")
password = st.text_input("Password", type="password")
USER_DB = "users.json"

def load_users():
    with open(USER_DB, "r") as f:
        return json.load(f)
    

if st.button("Login"):
    if username and password:
        res = requests.post("http://localhost:8000/login", json={"username": username, "password": password})
        if res.json().get("success"):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("Login successful!")
            st.switch_page("ui.py")  # 'ui' is the name of your main page file without .py
        else:
            st.error(res.json().get("detail", "Login failed"))
    else:
        st.warning("Please fill in both fields.")

if st.button("Go to Sign Up"):
    st.switch_page("pages/signup.py")  # Switch to signup page (without '.py')
