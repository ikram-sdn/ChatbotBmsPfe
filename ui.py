import streamlit as st
import requests
from utils import extract_text_from_file  # Assuming you create this function in utils.py
import datetime
import json
import os

# Filepath to store conversation history
CONVERSATION_FILE = "conversation_history.json"

# Helper function to call the API
def query_rag(prompt):
    url = 'http://localhost:8000/chat?question=' + prompt
    response = requests.get(url)
    data = response.json()
    return data['reply']

# Function to load conversation history from a file
def load_conversation_history():
    if os.path.exists(CONVERSATION_FILE):
        with open(CONVERSATION_FILE, 'r') as f:
            return json.load(f)
    return []

# Function to save conversation history to a file
def save_conversation_history(conversations):
    with open(CONVERSATION_FILE, 'w') as f:
        json.dump(conversations, f, indent=4)

# Logout function
def logout():
    st.session_state.clear()  # Clears session state
    st.rerun()  # Refreshes the app

# Load conversation history from the file
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = load_conversation_history()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Layout for main page
st.title("Chatbot Battery Management System")

# Sidebar: New Conversation button and Sessions History
with st.sidebar:
    # Custom CSS for Sidebar Layout
    st.markdown("""
    <style>
    .sidebar .sidebar-content {
        position: relative;
        height: 100vh;
    }
    .sidebar .sidebar-content .logout-button {
        position: absolute;
        top: 0;
        width: 100%;
    }
    .sidebar .sidebar-content .new-conversation-button {
        position: relative;
        margin-top: 60px; /* Ensuring some space between the buttons */
    }
    </style>
    """, unsafe_allow_html=True)

    # Logout button at the top of the sidebar
    st.button("🔒 Logout", key="logout_button", on_click=logout, use_container_width=True, help="Logout and clear session")

    st.header("Sessions History")

    # Button to start a new conversation, placed below the logout button
    st.button("New Conversation", key="new_conversation_button", use_container_width=True)

    

    # Display the conversation history and allow review of past conversations
    if st.session_state.conversation_history:
        for idx, conversation in enumerate(st.session_state.conversation_history):
            col1, col2 = st.columns([8, 1])  # Create two columns: one for the title and one for the button

            with col1:
                if st.button(f"Conversation {idx + 1}", key=f"conversation_{idx}"):
                    # Load the selected conversation into the current session
                    st.session_state.messages = conversation['messages']
                    st.session_state.current_conversation_index = idx
                    st.session_state.updated = True

            with col2:
                # Bin emoji button to delete the conversation
                if st.button("🗑️", key=f"delete_{idx}"):
                    # Remove the conversation from the history
                    del st.session_state.conversation_history[idx]
                    save_conversation_history(st.session_state.conversation_history)  # Save updated history
                    st.rerun()  # Rerun to refresh the page after deletion
    else:
        st.write("No conversations yet.")

# Allow file upload
uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx", "xlsx", "pptx"])

# If a file is uploaded, extract the text and allow questions based on the file content
if uploaded_file is not None:
    file_text = extract_text_from_file(uploaded_file)
    
    # Ask user if they want to display the extracted content
    display_extracted = st.checkbox("Do you want to display the extracted content?")

    if display_extracted:
        st.write("Extracted content from the uploaded file:")
        st.text(file_text)  # Display the extracted content if the user chooses to

    # Add the extracted file content as context for the chatbot
    context = f"Context: {file_text}\n"

# Display the messages for the current session
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input and response
if prompt := st.chat_input("Posez votre question ici..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Query the API and get the response
    response = query_rag(prompt)
    with st.chat_message("assistant"):
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
