# signup.py
import streamlit as st
import requests
import json
import datetime
import base64
from utils import hash_password

st.set_page_config(page_title="Signup", layout="centered", initial_sidebar_state="collapsed")

# Convert background image to base64
def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Encode and set background
bg_img = get_base64_image("informatico3.jpg")  # Adjust the path to go one level up to the parent folder
st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{bg_img}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    .st-emotion-cache-12fmjuu{{
        background-color: transparent !important;
    }}

    [data-testid="stSidebarNav"] {{display: none;}}
    [data-testid="collapsedControl"] {{display: none;}}

    .stButton > button {{
        background-color: white;
        color: #1E90FF;
        border: 2px solid #1E90FF;
        border-radius: 20px;
    }}
    .stButton > button:hover {{
        background-color: #f0f0f0;
        color: #187bcd;
        border: 2px solid #187bcd;
    }}
    .welcome {{
        text-align: center;
        font-size: 1.1em;
        margin-bottom: 2em;
    }}
    .logo-container {{
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 2em 0;
    }}
    .logo-container img {{
        max-width: 100%;
        height: auto;
        width: 1000px;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# Create a centered container
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    # Center the logo
    st.image("logo.png", use_container_width=True)
    
    # Add welcome message
    st.markdown('<p class="welcome">Join our community! Create an account to get started.</p>', unsafe_allow_html=True)
    
    # Form elements
    st.markdown("---")
    username = st.text_input("Choose a username")
    password = st.text_input("Choose a password", type="password")
    st.markdown("---")
    
    # Create two columns for buttons
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("Sign Up", use_container_width=True):
            if username and password:
                res = requests.post("http://localhost:8000/signup", json={"username": username, "password": password})
                if res.json().get("success"):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("Signup successful!")
                    st.switch_page("pages/ui.py")
                else:
                    st.error(res.json().get("detail", "Signup failed"))
            else:
                st.warning("Please fill in both fields.")

    with col_btn2:
        if st.button("Go to Login", use_container_width=True):
            st.switch_page("login.py")
