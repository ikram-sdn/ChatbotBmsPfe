import streamlit as st
import requests
from utils import extract_text_from_file  # Assurez-vous que cette fonction est définie dans utils.py
import datetime
import json
import os

# Fichier pour stocker l’historique des conversations
CONVERSATION_FILE = "conversation_history.json"

# Fonction pour interroger l'API
def query_rag(prompt):
    url = f'http://localhost:8000/chat?question={prompt}'
    response = requests.get(url)
    data = response.json()
    return data.get('reply', "❌ Erreur lors de la récupération de la réponse.")

# Charger l’historique des conversations depuis un fichier
def load_conversation_history():
    if os.path.exists(CONVERSATION_FILE):
        with open(CONVERSATION_FILE, 'r') as f:
            try:
                return json.load(f)  # Doit être un dictionnaire
            except json.JSONDecodeError:
                return {}  # Si fichier corrompu, retourne un dictionnaire vide
    return {}

# Sauvegarder l’historique des conversations
def save_conversation_history(conversations):
    with open(CONVERSATION_FILE, 'w') as f:
        json.dump(conversations, f, indent=4)

# Fonction de déconnexion
def logout():
    st.session_state.clear()
    st.rerun()

# Charger l’historique dans la session
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = load_conversation_history()

if not isinstance(st.session_state.conversation_history, dict):
    st.session_state.conversation_history = {}  # S'assurer que c'est un dictionnaire

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sauvegarder la conversation actuelle avant d’en démarrer une nouvelle
def save_current_conversation():
    if st.session_state.messages:
        date_key = datetime.datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        if date_key not in st.session_state.conversation_history:
            st.session_state.conversation_history[date_key] = []
        
        conversation = {"timestamp": timestamp, "messages": st.session_state.messages.copy()}
        st.session_state.conversation_history[date_key].append(conversation)
        
        save_conversation_history(st.session_state.conversation_history)
        st.session_state.messages = []  # Réinitialiser pour la nouvelle conversation

# Interface principale
st.title("Chatbot Battery Management System")

# Barre latérale avec historique et actions
with st.sidebar:
    st.button("🔒 Logout", key="logout_button", on_click=logout, use_container_width=True)

    if st.button("➕ New Conversation", key="new_conversation_button", use_container_width=True):
        save_current_conversation()

    st.header("📅 Historique des Conversations")

    # Trier les dates du plus récent au plus ancien
    sorted_dates = sorted(st.session_state.conversation_history.keys(), reverse=True)

    if sorted_dates:
        for date in sorted_dates:
            st.subheader(f"📆 {date}")  # Affichage de la date
            
            for idx, conversation in enumerate(reversed(st.session_state.conversation_history.get(date, []))):  # Trier les conversations dans chaque date
                col1, col2 = st.columns([8, 1])  # Deux colonnes : titre et bouton
                with col1:
                    if st.button(f"🗂️ Conversation {len(st.session_state.conversation_history[date]) - idx}", key=f"conversation_{date}_{idx}"):
                        st.session_state.messages = conversation["messages"]
                        st.session_state.updated = True
                
                with col2:
                    if st.button("🗑️", key=f"delete_{date}_{idx}"):
                        del st.session_state.conversation_history[date][idx]
                        if not st.session_state.conversation_history[date]:  # Supprimer la date si vide
                            del st.session_state.conversation_history[date]
                        save_conversation_history(st.session_state.conversation_history)
                        st.rerun()
    else:
        st.write("Aucune conversation enregistrée.")

# Upload de fichier
uploaded_file = st.file_uploader("Choisissez un fichier", type=["pdf", "docx", "xlsx", "pptx"])

if uploaded_file is not None:
    file_text = extract_text_from_file(uploaded_file)
    
    display_extracted = st.checkbox("Afficher le contenu extrait ?")
    if display_extracted:
        st.write("Contenu extrait :")
        st.text(file_text)

    context = f"Context: {file_text}\n"

# Affichage des messages de la conversation actuelle
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Gestion des nouvelles questions
if prompt := st.chat_input("Posez votre question ici..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    response = query_rag(prompt)
    with st.chat_message("assistant"):
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
