import os   
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify
from middleware.auth import token_required
from google import genai 

ai_bp = Blueprint('ai', __name__)

# --- LATEST AI INITIALIZATION ---
# Replace with your actual key starting with AIzaSy...
load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
@ai_bp.route('/chat', methods=['POST'])
@token_required
def chat(current_user):
    data = request.get_json()
    user_query = data.get('message')
    
    if not user_query:
        return jsonify({"status": "error", "message": "No message provided"}), 400

    try:
        # 'gemini-2.5-flash' is the current best for free-tier student projects
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=f"Explain this DPDP Act part simply for a student: {user_query}"
        )
        
        return jsonify({
            "status": "success", 
            "answer": response.text 
        })
        
    except Exception as e:
        # If it still shows 429, this message will tell you to wait
        if "429" in str(e):
            return jsonify({"status": "error", "message": "Limit reached. Please wait 60 seconds."}), 429
        return jsonify({"status": "error", "message": str(e)}), 500