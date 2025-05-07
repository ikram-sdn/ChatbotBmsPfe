from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import requests
import json
import os
import bcrypt
import time

import traceback

from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.llms import Ollama

from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import AIMessage, HumanMessage


from langchain_core.language_models import BaseLanguageModel
from langchain_core.vectorstores import VectorStoreRetriever

from utils import *

# ----------- CONFIGURATION -----------
EMBEDDING_MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
CHROMA_PATH_BIG_VECTORSTORE = 'db_3'
USERS_FILE = "users.json"
MIN_CONTEXT_LENGTH=100
K_TO_RETRIEVE = 5
GENERATION_TEMP = 0.25

# ----------- ADVANCED PROMPT TEMPLATE FOR DETAILED BMS EXPERTISE ----------- 
Prompt = """
You are a highly knowledgeable and helpful expert in Battery Management Systems (BMS), specializing in BMS architecture, subsystems, and testing phases.
Your role is to provide accurate, structured, and accessible explanations about BMS-related topics. You must reason through the question clearly and helpfully,
even if the answer is not directly available in the provided context.

Instructions:
Language Consistency: The only determining factor for the response language is the user’s question. Ignore the context language when choosing the response language
 - If the question is in **English**, answer in **English**.
 - If the question is in **French**, answer in **French**.
 - If the question is in **German**, answer in **German**.
 - Do NOT mix languages in your response.


Style Guidelines:
- Be clear, concise, and logically structured.
- Break down complex ideas.
- Use examples, test scenarios, or analogies when useful.

Primary Context Rule:
- Prioritize answering using the provided context if relevant and sufficient.
- If context is unclear or incomplete, do not ignore the question. Instead, respond using domain knowledge and explicitly state that you’re doing so.

Fallback Rule – When Context Is Insufficient or Missing:
If you cannot fully answer using only the context, begin your response with:
"Note: This answer is based on general knowledge, as the provided context does not fully cover the topic."

Source Attribution:
If using the context: "Source: Provided context."
If using general knowledge: "Source: General domain knowledge."

Context:
{context}


Question:
{question}


Answer:
"""


# ----------- MODEL INITIALIZATION -----------
model_kwargs = {"trust_remote_code": True}
embedding_function = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs=model_kwargs)
db = Chroma(persist_directory=CHROMA_PATH_BIG_VECTORSTORE, embedding_function=embedding_function)

print('✅ Model and vector database initialized')

#--------------------CONVERSATION MEMORY MANAGEMENT--------------------------

# Initialize LangChain memory for live conversation tracking
chat_memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Setup LLM and conversational chain
llm = Ollama(model="llama3", temperature=GENERATION_TEMP)
retriever = db.as_retriever(search_kwargs={"k": K_TO_RETRIEVE})

conversation_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=retriever,
    memory=chat_memory,
    return_source_documents=False
)



# ----------- CHATBOT FUNCTION -----------
def query_rag(query_text):
    print('📨 Inside query...')
    now = time.time()

    context_results = get_similiar([query_text], db, n=K_TO_RETRIEVE)
    context_text = "\n\n -------------\n\n".join([doc for doc, _ in context_results])
    context_clean = context_text.strip()

    # Check if context is too weak
    if not context_clean or len(context_clean) < MIN_CONTEXT_LENGTH:
        context_clean = "N/A"  # Triggers model to use its own knowledge if question is about BMS

    prompt = Prompt.format(context=context_clean, question=query_text)
    response_text = talk_to_llama3(prompt, GENERATION_TEMP)

    print(f"⏱ Time used: {time.time() - now:.2f}s")
    return response_text




# ----------- FASTAPI SETUP -----------
app = FastAPI()

# ----------- MODELS FOR USERS -----------
class User(BaseModel):
    username: str
    password: str

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

# ----------- AUTH ROUTES -----------
@app.post("/signup")
async def signup(request: Request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    if add_user(username, password):
        return {"success": True, "message": "User registered successfully."}
    else:
        return {"success": False, "message": "Username already exists."}

@app.post("/login")
async def login(request: Request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    if authenticate_user(username, password):
        return {"success": True, "message": "Login successful."}
    else:
        return {"success": False, "message": "Invalid username or password."}
# ----------- CHAT ENDPOINT -----------
@app.get("/chat")
async def echo_string(question: str):
    result = query_rag(question)
    print(f"🧠 Response to send: {result}")

    return {"reply": result}
