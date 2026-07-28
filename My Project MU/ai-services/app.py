import os
import jwt
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta, timezone
from routes.ai_routes import ai_bp, limiter
from google import genai

load_dotenv()

app = Flask(__name__)

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("CRITICAL: SECRET_KEY is missing from environment settings!")
app.config['SECRET_KEY'] = SECRET_KEY

ADMIN_USER = os.getenv("ADMIN_USERNAME")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD")

# Initialize Gemini Client (assumes GEMINI_API_KEY is in your environment variables)
client = genai.Client()

limiter.init_app(app)

app.register_blueprint(ai_bp, url_prefix='/ai')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    if data.get('username') == ADMIN_USER and data.get('password') == ADMIN_PASS:
        token = jwt.encode({
            'user': ADMIN_USER,
            'exp': datetime.now(timezone.utc) + timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({"status": "success", "access_token": token})
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401

@app.route('/api/upload', methods=['POST'])
def handle_file_upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file part provided"}), 400
    
    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # Read file bytes in-memory and send straight to Gemini
        file_bytes = uploaded_file.read()
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                "Analyze this uploaded document for compliance under India's DPDP Act 2023. Give a clear risk summary:",
                file_bytes
            ]
        )
        return jsonify({"analysis": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=os.getenv("FLASK_DEBUG", "False") == "True")