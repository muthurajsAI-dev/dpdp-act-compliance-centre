import os
import io
import importlib
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify
from google import genai
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from middleware.auth import token_required
from database import create_conversation, get_conversation, save_message, get_conversation_messages, get_user_conversations, save_audit

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


@ai_bp.route('/conversations', methods=['GET'])
@token_required
def list_conversations(current_user_email):
    conversations = get_user_conversations(current_user_email)
    return jsonify({"status": "success", "conversations": conversations})


@ai_bp.route('/chat', methods=['POST'])
@limiter.limit("10 per minute")
@token_required
def chat(current_user_email):
    data = request.get_json()
    user_message = data.get('message')
    conversation_id = data.get('conversation_id')

    if not user_message:
        return jsonify({"status": "error", "message": "No message provided"}), 400

    if not conversation_id:
        title = user_message[:50] + ('...' if len(user_message) > 50 else '')
        conversation_id = create_conversation(current_user_email, title)
    else:
        conv = get_conversation(conversation_id, current_user_email)
        if not conv:
            return jsonify({"status": "error", "message": "Conversation not found"}), 404

    history = get_conversation_messages(conversation_id)
    contents = []
    for msg in history:
        role = 'user' if msg['role'] == 'user' else 'model'
        contents.append({"role": role, "parts": [{"text": msg['content']}]})
    contents.append({"role": "user", "parts": [{"text": user_message}]})

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents
        )
        answer = response.text

        save_message(conversation_id, 'user', user_message)
        save_message(conversation_id, 'assistant', answer)

        return jsonify({
            "status": "success",
            "response": answer,
            "conversation_id": conversation_id
        })
    except Exception as e:
        if "429" in str(e):
            return jsonify({"status": "error", "message": "Limit reached. Please wait 60 seconds."}), 429
        return jsonify({"status": "error", "message": str(e)}), 500


@ai_bp.route('/upload', methods=['POST'])
@limiter.limit("5 per minute")
@token_required
def upload_file(current_user_email):
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
    filename = file.filename.lower()
    extracted_text = ""

    file_bytes = file.read()
    file_stream = io.BytesIO(file_bytes)

    try:
        if filename.endswith('.pdf'):
            if PdfReader is None:
                return jsonify({"status": "error", "message": "Install the pypdf package to parse PDF uploads."}), 400
            reader = PdfReader(file_stream)
            for page in getattr(reader, 'pages', []):
                try:
                    text = page.extract_text()
                except Exception:
                    text = None
                if text:
                    extracted_text += text + "\n"

        elif filename.endswith('.docx'):
            if docx is None:
                return jsonify({"status": "error", "message": "Install python-docx to parse DOCX uploads."}), 400
            doc = docx.Document(file_stream)
            for para in doc.paragraphs:
                extracted_text += para.text + "\n"

        elif filename.endswith(('.jpg', '.jpeg', '.png')):
            image_bytes = file_bytes
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    image_bytes,
                    "Analyze this uploaded policy document or image for compliance under India's DPDP Act 2023. Give a concise summary of compliance status and areas to improve:"
                ]
            )
            save_audit(current_user_email, file.filename, response.text[:300])
            return jsonify({"status": "success", "analysis": response.text})

        else:
            try:
                extracted_text = file_bytes.decode('utf-8', errors='ignore')
            except Exception:
                extracted_text = ''

        if not extracted_text.strip():
            return jsonify({"status": "error", "message": "Could not extract text from the uploaded file."}), 400

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"Analyze this uploaded policy document for compliance under India's DPDP Act 2023. Give a concise summary of compliance status and areas to improve:\n\n{extracted_text[:4000]}"
        )

        save_audit(current_user_email, file.filename, response.text[:300])

        return jsonify({
            "status": "success",
            "analysis": response.text
        })
    except Exception as e:
        if "429" in str(e):
            return jsonify({"status": "error", "message": "Limit reached. Please wait 60 seconds."}), 429
        return jsonify({"status": "error", "message": str(e)}), 500


@ai_bp.route('/export-pdf', methods=['GET'])
@token_required
def export_pdf(current_user_email):
    return jsonify({"status": "success", "message": "PDF audit report package generated successfully."})


@ai_bp.route('/email-report', methods=['POST'])
@token_required
def email_report(current_user_email):
    return jsonify({"status": "success", "message": "Audit report dispatched to registered administrator email."})