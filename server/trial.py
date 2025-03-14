import openai
from fastapi import FastAPI, UploadFile, File, Form
import fitz  # PyMuPDF for PDFs
from docx import Document
import os
import json
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

app = FastAPI()

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_openai_api_key_here")

# OpenAI client instance
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Function to extract text from a DOCX file
def extract_text_from_docx(docx_path):
    doc = Document(docx_path)
    return "\n".join([para.text for para in doc.paragraphs])

# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    return "\n".join([page.get_text("text") for page in doc])

@app.post("/generate-file-structure/")
async def generate_file_structure(
    file: UploadFile = File(None), 
    prd_text: str = Form(None),  
    tech_stack: str = Form(...)
):
    """Reads PRD document and generates a detailed, optimized file structure in JSON format for Django+React or Node.js+React."""
    try:
        # Step 1: Extract PRD text from document or take direct input
        if file:
            file_path = f"temp_{file.filename}"
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())

            if file.filename.endswith(".docx"):
                prd_text = extract_text_from_docx(file_path)
            elif file.filename.endswith(".pdf"):
                prd_text = extract_text_from_pdf(file_path)
            else:
                return {"error": "Unsupported file format. Use DOCX or PDF."}

        if not prd_text:
            return {"error": "No PRD text provided."}

        if tech_stack.lower() not in ["django-react", "nodejs-react"]:
            return {"error": "Invalid tech stack. Choose 'django-react' or 'nodejs-react'."}

        # Step 2: Optimized Prompt for GPT-4o
        prompt = f"""
        You are an expert software architect. Generate a **detailed project directory structure** in **JSON format**.

        **Instructions:**
        - Use a JSON **nested dictionary format**.
        - **Keys represent directories or files**.
        - **Values describe purpose or contain subdirectories**.
        - Ensure **best practices** for the chosen tech stack ({tech_stack.upper()}).

        **PRD Document for Context:**
        ```
        {prd_text}
        ```

        Generate the **final directory structure in JSON format**, ensuring all PRD features are included.
        """

        # Step 3: Call OpenAI GPT-4o
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a highly experienced software architect specializing in full-stack development."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4096
        )

        # Step 4: Check if API Response is Empty
        gpt_response = response.choices[0].message.content.strip()
        if not gpt_response:
            return {"error": "OpenAI API did not return a response"}

        # Step 5: Extract Only the JSON Block
        match = re.search(r"\{.*\}", gpt_response, re.DOTALL)
        if not match:
            return {"error": "No valid JSON found in GPT response", "raw_response": gpt_response}

        gpt_response_cleaned = match.group(0)

        # Step 6: Parse JSON Safely
        try:
            file_structure_json = json.loads(gpt_response_cleaned)
        except json.JSONDecodeError as e:
            return {
                "error": f"GPT response is not valid JSON: {str(e)}",
                "raw_response": gpt_response
            }

        return {"file_structure": file_structure_json}

    except Exception as e:
        return {"error": str(e)}
