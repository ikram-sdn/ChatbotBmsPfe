import streamlit as st
import requests
from utils import extract_text_from_file  # Assuming you create this function in utils.py


# Helper function pour appeler l'API
def query_rag(prompt):
    url = 'http://localhost:8000/chat?question=' + prompt
    response = requests.get(url)
    data = response.json()
    return data['reply']

# Frontend Streamlit
st.title("Chatbot Battery Management System")

if "messages" not in st.session_state:
    st.session_state.messages = []


# Initialize session state for feedback if not already present
if "feedback" not in st.session_state:
    st.session_state.feedback = None


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



# Afficher les messages précédents
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

     # Handle feedback interaction (set default to None)
    feedback = st.radio("Rate this response:", ("👍 Good", "👎 Bad"), key="feedback_radio", index=None)

    # Store the feedback message only when the user selects an option
    if feedback == "👍 Good":
        st.session_state.feedback = "Thanks for your feedback! 👍"

    elif feedback == "👎 Bad":
        st.session_state.feedback = "Sorry to hear that! 👎 We'll try to improve."

# Display feedback message if available
if st.session_state.feedback:
    st.write(st.session_state.feedback)