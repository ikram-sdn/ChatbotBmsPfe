from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import requests
import json
import os
import bcrypt
import time

from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.llms import Ollama

from utils import *

# ----------- CONFIGURATION -----------
EMBEDDING_MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
CHROMA_PATH_BIG_VECTORSTORE = 'db_3'
USERS_FILE = "users.json"

K_TO_RETRIEVE = 5
GENERATION_TEMP = 0.25

# ----------- PROMPT TEMPLATE ----------- 
Prompt = """
You are an expert in Battery Management Systems (BMS), specializing in making complex information easy to understand.

IMPORTANT:
- Answer in the **same language as the user's question**, regardless of the language of the context.
- Do NOT mix languages in your response.
- If the question is in English, the answer must be in English.
- If the question is in French, answer in French.
- If the question is in German, answer in German.

Use ONLY the information provided in the context.
Do NOT guess, assume, or add extra knowledge.
If the context does not contain enough information to answer, reply:
"The context does not contain enough information to answer this question."

Context:
```{context}```

Question:
```{question}```

Answer:
"""
# ----------- MODEL INITIALIZATION -----------
model_kwargs = {"trust_remote_code": True}
embedding_function = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs=model_kwargs)
db = Chroma(persist_directory=CHROMA_PATH_BIG_VECTORSTORE, embedding_function=embedding_function)

print('✅ Model and vector database initialized')

# ----------- CHATBOT FUNCTION -----------
def query_rag(query_text):
    print('📨 Inside query...')
    now = time.time()

    context_results = get_similiar([query_text], db, n=K_TO_RETRIEVE)
    context_text = "\n\n -------------\n\n".join([doc for doc, _ in context_results])
    
    prompt = Prompt.format(context=context_text, question=query_text)
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
@app.get("/chat/")
async def echo_string(question: str):
    result = query_rag(question)
    print(f"🧠 Response to send: {result}")
    return {"reply": result}