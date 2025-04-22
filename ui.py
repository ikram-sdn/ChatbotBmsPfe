import streamlit as st
import requests
from utils import extract_text_from_file, query_rag, query_rag_with_context, extract_audio_from_mp4, transcribe_audio
import datetime
import json
import os
import tempfile

CONVERSATION_FILE = "conversation_history.json"



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
st.title("Chatbot Battery Management System")

with st.sidebar:
    if st.session_state.get("logged_in"):
        st.markdown(f"👤 **Connected as :** `{st.session_state.username}`")
        st.markdown("---")
    if st.button("🔒 Logout", key="logout_button", use_container_width=True):
        st.switch_page("pages/login.py")
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
                    if st.button(f"🗂️ Conversation {total - idx}", key=f"conversation_{date}_{idx}"):
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
        st.write("Aucune conversation enregistrée.")

# --- File upload section ---
uploaded_file = st.file_uploader("Choisissez un fichier", type=["pdf", "docx", "xlsx", "pptx", "mp4"])
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

        st.write(f"✅ Audio extrait avec succès.")
        display_extracted = st.checkbox("Afficher la transcription ?")
        if display_extracted:
            st.write("Transcription audio :")
            st.text(transcription)

        file_text = transcription
    else:
        file_text = extract_text_from_file(uploaded_file)
        display_extracted = st.checkbox("Afficher le contenu extrait ?")
        if display_extracted:
            st.write("Contenu extrait :")
            st.text(file_text)

# --- Display past messages ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Handle new user prompt ---
if prompt := st.chat_input("Posez votre question ici..."):
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
