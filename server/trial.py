import openai
from fastapi import FastAPI, UploadFile, File, Form
import fitz  # PyMuPDF for PDFs
from docx import Document
import os
from dotenv import load_dotenv

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
    """Reads PRD document and generates a detailed, optimized file structure for Django+React or Node.js+React."""
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

        # Step 2: Define Fixed Base File Structure
        django_react_structure = """
        /project-root
        ├── /client  (Frontend - React)
        │   ├── /public
        │   │   ├── /images        # Static images
        │   ├── /src
        │   │   ├── /components
        │   │   ├── /pages
        │   │   ├── /redux         # Redux store & slices for state management
        │   │   ├── /context       # Context API for lightweight state management
        │   │   ├── /router        # React Router for navigation
        │   │   ├── index.js
        │   │   ├── App.js
        │   ├── /tests             # Unit & integration tests
        │   │   ├── unit
        │   │   ├── integration
        │   ├── package.json
        │   ├── .env
        │   ├── README.md
        ├── /server  (Backend - Django)
        │   ├── /app
        │   │   ├── /models
        │   │   ├── /views
        │   │   ├── /serializers
        │   │   ├── /urls
        │   │   ├── /tests          # Django unit tests
        │   │   │   ├── test_auth.py
        │   │   ├── /permissions
        │   │   ├── settings.py
        │   │   ├── urls.py
        │   │   ├── wsgi.py
        │   ├── /docs                # API documentation
        │   │   ├── API_REFERENCE.md
        │   ├── manage.py
        │   ├── requirements.txt
        │   ├── .env
        │   ├── README.md
        ├── /deployment
        │   ├── Dockerfile
        │   ├── docker-compose.yml
        │   ├── nginx.conf
        """

        node_react_structure = """
        /project-root
        ├── /client  (Frontend - React)
        │   ├── /public
        │   │   ├── /images        # Static images
        │   ├── /src
        │   │   ├── /components
        │   │   ├── /pages
        │   │   ├── /redux         # Redux store & slices for state management
        │   │   ├── /context       # Context API for lightweight state management
        │   │   ├── /router        # React Router for navigation
        │   │   ├── index.js
        │   │   ├── App.js
        │   ├── package.json
        │   ├── .env
        │   ├── README.md
        ├── /server  (Backend - Node.js/Express)
        │   ├── /src
        │   │   ├── /models
        │   │   ├── /routes
        │   │   ├── /controllers
        │   │   ├── /middleware
        │   │   ├── /config
        │   │   ├── /tests          # Mocha/Chai unit tests
        │   │   │   ├── test_auth.js
        │   ├── /docs               # API documentation
        │   │   ├── API_REFERENCE.md
        │   ├── server.js
        │   ├── package.json
        │   ├── .env
        │   ├── README.md
        ├── /deployment
        │   ├── Dockerfile
        │   ├── docker-compose.yml
        │   ├── nginx.conf
        """

        base_structure = django_react_structure if tech_stack.lower() == "django-react" else node_react_structure

        # Step 3: Optimized Prompt for GPT-4o
        prompt = f"""
        You are an expert software architect. Generate a **detailed and structured project directory** based on the provided PRD.

        **Instructions:**
        - Use a **tree format** for the directory.
        - Ensure **best practices** for scalability and maintainability.
        - Include necessary folders such as **tests, documentation, configurations, and state management**.
        - Generate missing files dynamically based on PRD content.

        **Base Structure for {tech_stack.upper()}:**
        ```
        {base_structure}
        ```

        **PRD Document for Context:**
        ```
        {prd_text}
        ```

        Generate the complete directory structure, ensuring that **all PRD features are covered**.
        """

        # Step 4: Call OpenAI GPT-4o
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a highly experienced software architect specializing in full-stack development."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=3000
        )

        generated_structure = response.choices[0].message.content

        return {"file_structure": generated_structure}

    except Exception as e:
        return {"error": str(e)}
