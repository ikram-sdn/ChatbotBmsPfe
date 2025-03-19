import requests
from langchain_community.llms import Ollama
import ollama
import fitz  # PyMuPDF (for PDFs)
from docx import Document  # For DOCX files
import pandas as pd  # For Excel files
import io
from pptx import Presentation  # For PPTX files


# Function to extract text from PowerPoint files
def extract_text_from_pptx(file):
    # Read the file and extract text from PowerPoint presentation
    byte_data = file.read()
    prs = Presentation(io.BytesIO(byte_data))
    text = ""
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text += shape.text + "\n"
    return text

def extract_text_from_pdf(uploaded_file):
    # Read the uploaded file content as bytes
    byte_data = uploaded_file.read()

    # Use io.BytesIO to convert byte_data to a file-like object
    with io.BytesIO(byte_data) as byte_file:
        doc = fitz.open(stream=byte_file, filetype="pdf")  # Open using the byte stream

        text = ""
        # Iterate over each page in the PDF and extract text
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text += page.get_text()

    return text

# Function to extract text from Word document
def extract_text_from_word(file):
    # Read the file and extract text from Word
    byte_data = file.read()
    doc = Document(io.BytesIO(byte_data))
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

# Function to extract text from Excel document
def extract_text_from_excel(file):
    # Read the file and convert it to a DataFrame
    byte_data = file.read()
    df = pd.read_excel(io.BytesIO(byte_data))
    text = df.to_string()  # You can format the output as needed
    return text

# Generic function to extract text based on file type
def extract_text_from_file(file):
    if file.type == "application/pdf":
        return extract_text_from_pdf(file)
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_word(file)
    elif file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        return extract_text_from_excel(file)
    elif file.type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":  # pptx type
        return extract_text_from_pptx(file)
    else:
        return "Unsupported file type"


# Définir le modèle
model = "llama3.1:8b-instruct-q4_K_M"

system_prompt = '''
You are an expert in Battery Management Systems (BMS), specializing in making complex information easy to understand. 
When provided with a question and relevant context about Battery Management Systems, your task is to deliver a clear, concise, and comprehensive response based on the given information.
Your objective is to ensure the user fully understands the key points and concepts related to BMS.
always answer in the language of the question provided, not the language of the context!
'''

# Fonction pour appeler le modèle Llama3 via Ollama
def talk_to_llama3(actual_prompt, temp):
    print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
    print(actual_prompt)
    print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
    
    response = ollama.chat(
        model=model, 
        messages=[
            { 'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': actual_prompt},
        ]
    )

    return response['message']['content']

# Fonction pour retirer les doublons
def remove_duplicates(l):
    l_without_duplicates = []
    unseen = set()  # Pour optimiser la recherche des doublons
    for element in l:
        if element[0] not in unseen:
            l_without_duplicates.append(element)
            unseen.add(element[0])
    return l_without_duplicates

# Fonction de recherche similaire dans la base de données
def get_similiar(queries, db, n=4):
    results = []
    for query in queries:
        result = db.max_marginal_relevance_search(query, k=n)
        results.extend(result)

    results = [(doc.page_content, 1) for doc in results]  # Formatage des résultats
    return results

# Fonction de reformulation des questions
def reformulate(question, REFORMULATION_TEMP):
    questions = [question]
    for i in range(1):
        q = f"""
        Réformulez cette question,
        Veuillez le reformuler en tenant compte de ce contexte et en ajoutant quelques mots clés en lien avec cela.
        Assurez-vous d'utiliser des mots différents de ceux de la question posée.
        votre réponse doit se composer uniquement des questions formulées et rien d'autre.
        question: {question}
        reformulation:
        """
        questions.append(talk_to_llama3(q, REFORMULATION_TEMP))
        
    return questions
