import os
import jwt
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from routes.ai_routes import ai_bp, limiter
from database import init_db, create_user, get_user_by_email
from routes.audit_routes import audit_bp  
from routes.settings_routes import settings_bp    
from routes.reports_routes import reports_bp      
load_dotenv()

app = Flask(__name__)

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("CRITICAL: SECRET_KEY is missing from environment settings!")
app.config['SECRET_KEY'] = SECRET_KEY

limiter.init_app(app)
app.register_blueprint(ai_bp, url_prefix='/ai')
app.register_blueprint(audit_bp, url_prefix='/audit')
app.register_blueprint(settings_bp, url_prefix='/account')
app.register_blueprint(reports_bp, url_prefix='/reports')
init_db()  # creates users table if it doesn't exist yet

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/signup', methods=['POST'])
@limiter.limit("5 per minute")
def signup():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or '@' not in email:
        return jsonify({"status": "error", "message": "Please enter a valid email"}), 400
    if len(password) < 8:
        return jsonify({"status": "error", "message": "Password must be at least 8 characters"}), 400

    password_hash = generate_password_hash(password)
    created = create_user(email, password_hash)

    if not created:
        return jsonify({"status": "error", "message": "An account with this email already exists"}), 409

    return jsonify({"status": "success", "message": "Account created. Please sign in."})

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    user = get_user_by_email(email)

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({"status": "error", "message": "Invalid email or password"}), 401

    token = jwt.encode({
        'email': user['email'],
        'exp': datetime.now(timezone.utc) + timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({"status": "success", "access_token": token})

if __name__ == '__main__':
    app.run(debug=os.getenv("FLASK_DEBUG", "False") == "True")