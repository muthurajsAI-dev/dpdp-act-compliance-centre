# auth.py (or your middleware file)
from functools import wraps
from flask import request, jsonify
import jwt
import os

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Check if Authorization header is present
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                # Expecting format: "Bearer <token>"
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({"status": "error", "message": "Invalid token format. Use 'Bearer <token>'"}), 401
        
        if not token:
            return jsonify({"status": "error", "message": "Token is missing!"}), 401

        try:
            # Decode the token using the app's secret key
            data = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
            # You can attach current user to request if needed
            current_user = data.get('user')
        except jwt.ExpiredSignatureError:
            return jsonify({"status": "error", "message": "Token has expired!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"status": "error", "message": "Invalid token!"}), 401

        return f(*args, **kwargs)
    return decorated