import streamlit as st
import requests
from utils import extract_text_from_file, query_rag, query_rag_with_context, extract_audio_from_mp4, transcribe_audio
import datetime
import json
import os
import tempfile
import pyperclip
import uuid
import base64
import pyperclip
from utils import store_feedback, regenerate_answer  # Import the functions

CONVERSATION_FILE = "conversation_history.json"

st.set_page_config(page_title="BMS chatbot", layout="centered", initial_sidebar_state="collapsed")

# Convert background image to base64
def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Encode and set background
bg_img = get_base64_image("informatico3.jpg")
st.markdown(
    f"""
    <style>
    html, body {{
        height: 100%;
        margin: 0;
        padding: 0;
    }}

    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css');
    .icon-button {{
        display: inline-block;
        background-color: transparent;
        border: none;
        padding: 10px;
        cursor: pointer;
    }}
    .icon-button i {{
        font-size: 24px;
    }}

    .stApp {{
        background-image: url("data:image/png;base64,{bg_img}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
        min-height: 100vh;
    }}

    [data-testid="stSidebarNav"] {{ display: none; }}
    [data-testid="collapsedControl"] {{ display: none; }}

    .block-container {{
        flex: 1;
        display: flex;
        flex-direction: column;
    }}
    
    .st-emotion-cache-1s2v671.e1gk92lc0 {{
        display: none !important;  /* Hides the label element */
    }}

    .st-emotion-cache-12fmjuu {{
        background-color: transparent !important;  /* Makes the background transparent */
    }}

    .stFileUploader{{
        background-color: transparent !important;
    }}
    
    .stChatInput {{
        background-color: transparent !important;
        border-radius: 10px;
        padding: 10px;
    }}

    .stFileUploader {{
        border-radius: 10px;
        padding: 10px;
    }}

    .css-1d391kg {{
        background-color: rgba(255, 255, 255, 0.9) !important;
    }}
    .st-emotion-cache-1ghhuty {{
        background-color: #89C4F4 !important;  /* Example background color */
    }}

    .st-emotion-cache-bho8sy {{
        background-color: #1F4788 !important;  /* Example background color */
    }}

    .st-emotion-cache-128upt6{{
        background-color: transparent !important;  
    }}

    </style>

    """,
    unsafe_allow_html=True
)

#--------LOGIN AND SIGNUP ----------
def main_ui():
    if not st.session_state.get("logged_in"):
        st.warning("You must be logged in to use the app.")
        st.stop()

    st.title("Welcome to BMS Chatbot")
    st.write(f"Hello, {st.session_state.username}!")

    # Add this check to run main_ui() only if imported directly
    if __name__ == "__main__" or "streamlit" in __name__:
        main_ui()

def load_conversation_history():
    if os.path.exists(CONVERSATION_FILE):
        with open(CONVERSATION_FILE, 'r') as f:
            try:
                data = json.load(f)
                if st.session_state.get("username"):
                    for date, conversations in data.items():
                        for conv in conversations:
                            if "username" not in conv:
                                conv["username"] = st.session_state.username  # Patch old ones
                return data
            except json.JSONDecodeError:
                return {}
    return {}

def save_conversation_history(conversations):
    with open(CONVERSATION_FILE, 'w') as f:
        json.dump(conversations, f, indent=4)

#--------------Login/signup ----------------------------------

def logout():
    st.session_state.clear()
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.email = None
    st.session_state.last_login = None
    st.experimental_rerun()  # Or use st.switch_page("login.py") if needed

# --- Session State Initialization ---
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = load_conversation_history()

if not isinstance(st.session_state.conversation_history, dict):
    st.session_state.conversation_history = {}

if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_mode" not in st.session_state:
    st.session_state.conversation_mode = "new"  # values: "new", "viewing"

# --- Save Function ---
def save_current_conversation():
    if st.session_state.messages and st.session_state.conversation_mode == "new":
        date_key = datetime.datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        if date_key not in st.session_state.conversation_history:
            st.session_state.conversation_history[date_key] = []

        conversation = {
            "timestamp": timestamp,
            "username": st.session_state.username,  # ✅ Add username field
            "messages": st.session_state.messages.copy()
        }

        st.session_state.conversation_history[date_key].append(conversation)
        save_conversation_history(st.session_state.conversation_history)
        st.session_state.messages = []

# --- UI Layout ---
st.markdown("""
    <div style='text-align: center;'>
        <h1 style='margin-bottom: -20px; font-size: 3.5rem;'>Chatbot</h1>
        <h1>Battery Management System</h1>
    </div>
""", unsafe_allow_html=True)

with st.sidebar:
    if st.session_state.get("logged_in"):
        st.markdown(f"👤 **Connected as :** `{st.session_state.username}`")
        st.markdown("---")
    if st.button("🔒 Logout", key="logout_button", use_container_width=True):
        st.switch_page("login.py")
    if st.button("➕ New Conversation", key="new_conversation_button", use_container_width=True):
        if st.session_state.conversation_mode == "new":
            save_current_conversation()
        st.session_state.messages = []
        st.session_state.conversation_mode = "new"

    st.header("📅 Conversation History")

    sorted_dates = sorted(st.session_state.conversation_history.keys(), reverse=True)

    if sorted_dates:
        for date in sorted_dates:
            st.subheader(f"📆 {date}")
            conversations = [
                conv for conv in st.session_state.conversation_history.get(date, [])
                if conv.get("username") == st.session_state.username
            ]

            total = len(conversations)
            for idx, conversation in enumerate(reversed(conversations)):
                actual_index = total - 1 - idx
                col1, col2 = st.columns([8, 1])
                with col1:
                    first_msg = conversation["messages"][0]["content"] if conversation["messages"] else "Conversation"
                    title_preview = (first_msg[:30] + "...") if len(first_msg) > 30 else first_msg
                    if st.button(f"🗂️ {title_preview}", key=f"conversation_{date}_{idx}"):
                        st.session_state.messages = conversation["messages"].copy()
                        st.session_state.conversation_mode = "viewing"
                with col2:
                    if st.button("🗑️", key=f"delete_{date}_{idx}"):
                        del st.session_state.conversation_history[date][actual_index]
                        if not st.session_state.conversation_history[date]:
                            del st.session_state.conversation_history[date]
                        save_conversation_history(st.session_state.conversation_history)
                        st.session_state.messages = []
                        st.session_state.conversation_mode = "new"
                        st.rerun()
    else:
        st.write("No conversation history available.")

# --- File upload section ---
uploaded_file = st.file_uploader("", type=["pdf", "docx", "xlsx", "pptx", "mp4"])
file_text = ""

if uploaded_file is not None:
    if uploaded_file.type == "video/mp4":
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
            tmp_video.write(uploaded_file.read())
            tmp_video_path = tmp_video.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            temp_audio_path = temp_audio.name

        extract_audio_from_mp4(tmp_video_path, temp_audio_path)
        transcription = transcribe_audio(temp_audio_path)

        st.write(f"✅ Audio successfully extracted.")
        display_extracted = st.checkbox("Show transcription?")
        if display_extracted:
            st.write("Audio transcription:")
            st.text(transcription)

        file_text = transcription
    else:
        file_text = extract_text_from_file(uploaded_file)
        display_extracted = st.checkbox("Show extracted content?")
        if display_extracted:
            st.write("Extracted content:")
            st.text(file_text)

# --- Display past messages ---
# Temporary placeholder for a regenerated message if needed
regenerated_message = None
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] == "assistant":
            col1, col2, col3 = st.columns([1, 1, 2])

            # 👍 Thumbs up button with icon inside
            with col1:
                thumbs_up_html = f"""
                <button class="st-emotion-cache-ocsh0s em9zgd02" style="background-color: transparent; border: none; cursor: pointer; font-size: 24px;" 
                        title="Thumbs Up" onclick="window.location.href = '#thumbs_up_{i}'">
                    <i class="fas fa-thumbs-up"></i>
                </button>
                """
                st.markdown(thumbs_up_html, unsafe_allow_html=True)
                thumbs_up = st.button("", key=f"thumbs_up_icon_{i}", help="Thumbs Up", use_container_width=False)
                if thumbs_up:
                    feedback_data = {
                        "feedback": "thumbs_up",
                        "response": message["content"],
                        "question": st.session_state.messages[i - 1]["content"] if i > 0 else "",
                    }
                    store_feedback(feedback_data)

            # 👎 Thumbs down button with icon inside
            with col2:
                thumbs_down_html = f"""
                <button class="st-emotion-cache-ocsh0s em9zgd02" style="background-color: transparent; border: none; cursor: pointer; font-size: 24px;" 
                        title="Thumbs Down" onclick="window.location.href = '#thumbs_down_{i}'">
                    <i class="fas fa-thumbs-down"></i>
                </button>
                """
                st.markdown(thumbs_down_html, unsafe_allow_html=True)
                thumbs_down = st.button("", key=f"thumbs_down_icon_{i}", help="Thumbs Down", use_container_width=False)
                if thumbs_down:
                    feedback_data = {
                        "feedback": "thumbs_down",
                        "response": message["content"],
                        "question": st.session_state.messages[i - 1]["content"] if i > 0 else "",
                    }
                    store_feedback(feedback_data)

                    # Flag for regeneration outside the loop
                    st.session_state["regenerate_request"] = {
                        "question": feedback_data["question"]
                    }

            # 📋 Copy button with icon inside
            with col3:
                copy_btn_html = f"""
                <button class="st-emotion-cache-ocsh0s em9zgd02" style="background-color: transparent; border: none; cursor: pointer; font-size: 24px;" 
                        title="Copy" onclick="window.location.href = '#copy_{i}'">
                    <i class="fas fa-copy"></i>
                </button>
                """
                st.markdown(copy_btn_html, unsafe_allow_html=True)
                copy_btn = st.button("", key=f"copy_icon_{i}", help="Copy", use_container_width=False)
                if copy_btn:
                    pyperclip.copy(message["content"])
                    st.success("Message copied to clipboard!")

# ✅ Show regenerated answer safely (outside chat context)
if regenerated_message:
    with st.chat_message("assistant"):
        st.markdown(regenerated_message)

# 🔄 Handle regeneration outside chat_message loop
if "regenerate_request" in st.session_state:
    question_to_regen = st.session_state["regenerate_request"]["question"]
    new_answer = regenerate_answer(question_to_regen)

    st.session_state.messages.append({"role": "assistant", "content": new_answer})

    with st.chat_message("assistant"):
        st.markdown(new_answer)

    del st.session_state["regenerate_request"]

# --- Handle new user prompt ---
if prompt := st.chat_input("Ask your question here..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.conversation_mode = "new"

    if uploaded_file is not None:
        response = query_rag_with_context(prompt, file_text)
    else:
        response = query_rag(prompt)

    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
