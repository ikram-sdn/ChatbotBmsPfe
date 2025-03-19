from fastapi import FastAPI
import requests
import json
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.llms import Ollama

import time
from utils import *

# Définir les modèles et chemins d'accès
EMBEDDING_MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
CHROMA_PATH_BIG_VECTORSTORE = 'db_3'

K_TO_RETRIEVE = 5
GENERATION_TEMP = 0.25

Prompt = """
You are an expert in Battery Management Systems (BMS), specializing in making complex information easy to understand. 
When provided with a question and relevant context about Battery Management Systems, your task is to deliver a clear, concise, and comprehensive response based on the given information.
Your objective is to ensure the user fully understands the key points and concepts related to BMS.
always answer in the language of the question provided, not the language of the context!

answer the following question based on the facts present in the context provided

Context: ```{context}```
 - -

question: ```{question}```

give you answer directly without mentioning the source of the facts.
if the context is not related to the question, do not provide an answer.
"""

# Initialisation du modèle et du vecteur
model_kwargs = {"trust_remote_code": True}
embedding_function = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs=model_kwargs)

db = Chroma(persist_directory=CHROMA_PATH_BIG_VECTORSTORE, embedding_function=embedding_function)
print('done initializing the model and vectordb')

# Fonction principale de la requête
def query_rag(query_text):
    print('inside query')
    now = time.time()

    # Recherche dans la base de données
    context_everything_db = get_similiar([query_text], db, n=K_TO_RETRIEVE)
    print(len(context_everything_db))
    
    later = time.time()
    print(f'time used = {later-now}')
    
    context_everything = []
    context_everything.extend(context_everything_db)

    context_text = "\n\n -------------\n\n".join([doc for doc, _score in context_everything])
    print('================================')
    for element in context_everything:
        print(element)
        print('********************************')
    print('================================')
 
    # Remplissage du prompt
    prompt = Prompt.format(context=context_text, question=query_text)
    response_text = talk_to_llama3(prompt, GENERATION_TEMP)
  
    return response_text

#### API CODE ####
app = FastAPI()

@app.get("/chat/")
async def echo_string(question: str):
    result = query_rag(question)
    print(f"Response to send: {result}")
    return {"reply": result}
