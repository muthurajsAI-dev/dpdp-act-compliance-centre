import os   
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify
from middleware.auth import token_required
from google import genai
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

ai_bp = Blueprint('ai', __name__)

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("CRITICAL: GOOGLE_API_KEY is missing from environment settings!")
client = genai.Client(api_key=api_key)

# Rate limiter — shared across routes, keyed by IP address
limiter = Limiter(key_func=get_remote_address)

@ai_bp.route('/chat', methods=['POST'])
@limiter.limit("10 per minute")   # <-- new: caps abuse per IP
@token_required
def chat(current_user):
    data = request.get_json()
    user_query = data.get('message')
    
    if not user_query:
        return jsonify({"status": "error", "message": "No message provided"}), 400

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=f"Explain this DPDP Act part simply for a student: {user_query}"
        )
        return jsonify({"status": "success", "answer": response.text})
    except Exception as e:
        if "429" in str(e):
            return jsonify({"status": "error", "message": "Limit reached. Please wait 60 seconds."}), 429
        return jsonify({"status": "error", "message": str(e)}), 500