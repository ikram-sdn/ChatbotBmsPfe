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

K_TO_RETRIEVE = 5
GENERATION_TEMP = 0.25

# ----------- ADVANCED PROMPT TEMPLATE FOR DETAILED BMS EXPERTISE ----------- 
Prompt = """
You are a highly specialized expert in Battery Management Systems (BMS) with a deep understanding of the BMS architecture, its various functionalities, subsystems, and testing phases. Your role is to provide **detailed and accurate information** to users while helping them understand complex concepts about BMS, including the **test phases** and the **ECU BMS subsystems**.

**IMPORTANT INSTRUCTIONS:**
- **Language Consistency:** The only determining factor for the response language is the user’s question. Ignore the context language when choosing the response language
    - If the question is in **English**, answer in **English**.
    - If the question is in **French**, answer in **French**.
    - If the question is in **German**, answer in **German**.
    - Do NOT mix languages in your response.
  
- **Detailed and Structured Responses:** Provide **thorough, clear, and concise explanations** of each concept. Ensure that the user can fully understand the BMS functionalities and subsystems, as well as the different **testing phases** (e.g., simulation, validation, etc.).
  
- **Context-Dependent Answers:** Only use the information provided in the context. Do not make guesses or add knowledge that is not included in the context.
  
- **Inadequate Context:** If the context does not provide enough information to answer the question, respond with:
  `"The context does not contain enough information to answer this question."`

- **Provide Examples When Relevant:** If relevant, provide real-world examples, diagrams, or test scenarios to help the user understand the concepts more easily.

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

    # 👉 Add user message to memory
    chat_memory.chat_memory.add_user_message(query_text)

    # Original RAG logic (kept intact)
    context_results = get_similiar([query_text], db, n=K_TO_RETRIEVE)
    context_text = "\n\n -------------\n\n".join([doc for doc, _ in context_results])
    
    prompt = Prompt.format(context=context_text, question=query_text)

    # ❌ Old manual model call (bypasses memory)
    # response_text = talk_to_llama3(prompt, GENERATION_TEMP)

    # ✅ New memory-aware call using LangChain
    response_text = conversation_chain.run(query_text)

    # 👉 Add AI message to memory
    chat_memory.chat_memory.add_ai_message(response_text)

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