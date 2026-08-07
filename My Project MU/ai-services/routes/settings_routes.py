from flask import Blueprint, render_template, request, jsonify, Response
import json
from werkzeug.security import generate_password_hash, check_password_hash
from middleware.auth import token_required
from database import get_user_by_email, update_password, delete_user_account, get_user_conversations, get_conversation_messages, get_user_audits

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings')
def settings_page():
    return render_template('settings.html')

@settings_bp.route('/change-password', methods=['POST'])
@token_required
def change_password(current_user_email):
    data = request.get_json()
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')

    if len(new_password) < 8:
        return jsonify({"status": "error", "message": "New password must be at least 8 characters"}), 400

    user = get_user_by_email(current_user_email)
    if not user or not check_password_hash(user['password_hash'], current_password):
        return jsonify({"status": "error", "message": "Current password is incorrect"}), 401

    update_password(current_user_email, generate_password_hash(new_password))
    return jsonify({"status": "success", "message": "Password updated successfully"})

@settings_bp.route('/export-data', methods=['GET'])
@token_required
def export_data(current_user_email):
    conversations = get_user_conversations(current_user_email)
    for conv in conversations:
        conv['messages'] = get_conversation_messages(conv['id'])
    audits = get_user_audits(current_user_email)

    export = {
        "email": current_user_email,
        "conversations": conversations,
        "audit_logs": audits
    }

    return Response(
        json.dumps(export, indent=2),
        mimetype='application/json',
        headers={'Content-Disposition': 'attachment; filename=dpdp_sahayak_my_data.json'}
    )

@settings_bp.route('/delete-account', methods=['POST'])
@token_required
def delete_account(current_user_email):
    delete_user_account(current_user_email)
    return jsonify({"status": "success", "message": "Account deleted"})