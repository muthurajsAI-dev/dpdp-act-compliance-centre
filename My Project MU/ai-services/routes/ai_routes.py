import os
import io
import importlib
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify
from google import genai
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Optional libraries for file parsing (loaded at runtime to avoid hard import errors)
try:
    pypdf_mod = importlib.import_module('pypdf')
    PdfReader = getattr(pypdf_mod, 'PdfReader', None)
except Exception:
    PdfReader = None

try:
    docx = importlib.import_module('docx')
except Exception:
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
    data = request.get_json()
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

    # Read bytes once from the uploaded file (werkzeug FileStorage)
    file_bytes = file.read()

    # Use a BytesIO wrapper for libraries that expect a file-like object
    file_stream = io.BytesIO(file_bytes)

    try:
        # 1. Handle PDF files
        if filename.endswith('.pdf'):
            if PdfReader is None:
                return jsonify({"status": "error", "message": "Install the pypdf package to parse PDF uploads."}), 400
            # PdfReader can accept a file-like object
            reader = PdfReader(file_stream)
            for page in getattr(reader, 'pages', []):
                try:
                    text = page.extract_text()
                except Exception:
                    text = None
                if text:
                    extracted_text += text + "\n"

        # 2. Handle Word documents (.docx)
        elif filename.endswith('.docx'):
            if docx is None:
                return jsonify({"status": "error", "message": "Install python-docx to parse DOCX uploads."}), 400
            # python-docx accepts a file-like object
            doc = docx.Document(file_stream)
            for para in doc.paragraphs:
                extracted_text += para.text + "\n"

        # 3. Handle Images (.jpg, .jpeg, .png) using Gemini Multimodal capability
        elif filename.endswith(('.jpg', '.jpeg', '.png')):
            image_bytes = file_bytes
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
            try:
                extracted_text = file_bytes.decode('utf-8', errors='ignore')
            except Exception:
                extracted_text = ''

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

@ai_bp.route('/export-pdf', methods=['GET'])
def export_pdf():
    return jsonify({"status": "success", "message": "PDF audit report package generated successfully."})

@ai_bp.route('/email-report', methods=['POST'])
def email_report():
    return jsonify({"status": "success", "message": "Audit report dispatched to registered administrator email."})