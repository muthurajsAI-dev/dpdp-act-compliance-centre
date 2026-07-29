import os   
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify
from google import genai
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Optional libraries for file parsing (install via pip if needed)
PdfReader = None
docx = None
try:
    import importlib
    PdfReader = importlib.import_module('pypdf').PdfReader
except ImportError:
    PdfReader = None

try:
    import importlib
    docx = importlib.import_module('docx')
except ImportError:
    docx = None

ai_bp = Blueprint('ai_bp', __name__)

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("CRITICAL: GOOGLE_API_KEY is missing from environment settings!")
client = genai.Client(api_key=api_key)

# Rate limiter — shared across routes, keyed by IP address
limiter = Limiter(key_func=get_remote_address)

@ai_bp.route('/chat', methods=['POST'])
@limiter.limit("10 per minute")
def chat():
    data = request.get_json(silent=True) or {}
    user_message = data.get('message')
    
    if not user_message:
        return jsonify({"status": "error", "message": "No message provided"}), 400

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"You are a legal compliance AI assistant specialized in India's DPDP Act 2023. Answer this query professionally: {user_message}"
        )
        return jsonify({"status": "success", "response": response.text})
    except Exception as e:
        if "429" in str(e):
            return jsonify({"status": "error", "message": "Limit reached. Please wait 60 seconds."}), 429
        return jsonify({"status": "error", "message": str(e)}), 500

@ai_bp.route('/upload', methods=['POST'])
@limiter.limit("5 per minute")
def upload_file():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part in the request"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
    
    filename = file.filename.lower()
    extracted_text = ""

    try:
        # 1. Handle PDF files
        if filename.endswith('.pdf'):
            if PdfReader is None:
                return jsonify({"status": "error", "message": "Install the pypdf package to parse PDF uploads."}), 400
            reader = PdfReader(file)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
        
        # 2. Handle Word documents (.docx)
        elif filename.endswith('.docx'):
            if docx is None:
                return jsonify({"status": "error", "message": "Install python-docx to parse DOCX uploads."}), 400
            doc = docx.Document(file)
            for para in doc.paragraphs:
                extracted_text += para.text + "\n"
                
        # 3. Handle Images (.jpg, .jpeg, .png)
        elif filename.endswith(('.jpg', '.jpeg', '.png')):
            image_bytes = file.read()
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    image_bytes,
                    "Analyze this uploaded policy document or image for compliance under India's DPDP Act 2023. Give a concise summary of compliance status and areas to improve:"
                ]
            )
            return jsonify({"status": "success", "analysis": response.text})

        # 4. Handle Text files (.txt) and fallback
        else:
            extracted_text = file.read().decode('utf-8', errors='ignore')

        if not extracted_text.strip():
            return jsonify({"status": "error", "message": "Could not extract text from the uploaded file."}), 400

        # Send extracted text to Gemini
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"Analyze this uploaded policy document for compliance under India's DPDP Act 2023. Give a concise summary of compliance status and areas to improve:\n\n{extracted_text[:4000]}"
        )
        
        return jsonify({
            "status": "success", 
            "analysis": response.text
        })
    except Exception as e:
        if "429" in str(e):
            return jsonify({"status": "error", "message": "Limit reached. Please wait 60 seconds."}), 429
        return jsonify({"status": "error", "message": str(e)}), 500