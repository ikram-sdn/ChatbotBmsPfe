import streamlit as st
import requests
from utils import extract_text_from_file, query_rag, query_rag_with_context, extract_audio_from_mp4, transcribe_audio
import datetime
import json
import os
import tempfile

CONVERSATION_FILE = "conversation_history.json"

def load_conversation_history():
    if os.path.exists(CONVERSATION_FILE):
        with open(CONVERSATION_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_conversation_history(conversations):
    with open(CONVERSATION_FILE, 'w') as f:
        json.dump(conversations, f, indent=4)

def logout():
    st.session_state.clear()
    st.rerun()

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = load_conversation_history()

if not isinstance(st.session_state.conversation_history, dict):
    st.session_state.conversation_history = {}

if "messages" not in st.session_state:
    st.session_state.messages = []

def save_current_conversation():
    if st.session_state.messages:
        date_key = datetime.datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        if date_key not in st.session_state.conversation_history:
            st.session_state.conversation_history[date_key] = []

        conversation = {"timestamp": timestamp, "messages": st.session_state.messages.copy()}
        st.session_state.conversation_history[date_key].append(conversation)

        save_conversation_history(st.session_state.conversation_history)
        st.session_state.messages = []

# --- UI Layout ---
st.title("Chatbot Battery Management System")

with st.sidebar:
    st.button("🔒 Logout", key="logout_button", on_click=logout, use_container_width=True)

    if st.button("➕ New Conversation", key="new_conversation_button", use_container_width=True):
        save_current_conversation()

    st.header("📅 Historique des Conversations")

    sorted_dates = sorted(st.session_state.conversation_history.keys(), reverse=True)

    if sorted_dates:
        for date in sorted_dates:
            st.subheader(f"📆 {date}")
            for idx, conversation in enumerate(reversed(st.session_state.conversation_history.get(date, []))):
                col1, col2 = st.columns([8, 1])
                with col1:
                    if st.button(f"🗂️ Conversation {len(st.session_state.conversation_history[date]) - idx}", key=f"conversation_{date}_{idx}"):
                        st.session_state.messages = conversation["messages"]
                        st.session_state.updated = True
                with col2:
                    if st.button("🗑️", key=f"delete_{date}_{idx}"):
                        del st.session_state.conversation_history[date][idx]
                        if not st.session_state.conversation_history[date]:
                            del st.session_state.conversation_history[date]
                        save_conversation_history(st.session_state.conversation_history)
                        st.rerun()
    else:
        st.write("Aucune conversation enregistrée.")

# File upload section
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

# Display past messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle new question
if prompt := st.chat_input("Posez votre question ici..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    if uploaded_file is not None:
        response = query_rag_with_context(prompt, file_text)
    else:
        response = query_rag(prompt)

    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
