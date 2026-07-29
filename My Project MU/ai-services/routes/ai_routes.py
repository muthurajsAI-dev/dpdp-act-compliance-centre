import os   
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify
from google import genai
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

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
    
    try:
        # Read the content of the uploaded text/policy file safely
        file_content = file.read().decode('utf-8', errors='ignore')
        
        # Use Gemini to analyze the policy document under DPDP Act 2023 guidelines
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"Analyze this uploaded policy document for compliance under India's DPDP Act 2023. Give a concise summary of compliance status and areas to improve:\n\n{file_content[:4000]}"
        )
        
        return jsonify({
            "status": "success", 
            "analysis": response.text
        })
    except Exception as e:
        if "429" in str(e):
            return jsonify({"status": "error", "message": "Limit reached. Please wait 60 seconds."}), 429
        return jsonify({"status": "error", "message": str(e)}), 500