from flask import Blueprint, render_template, jsonify
from middleware.auth import token_required
from database import get_user_audits

audit_bp = Blueprint('audit', __name__)

@audit_bp.route('/compliance-audit')
def compliance_audit():
    return render_template('compliance_audit.html')

@audit_bp.route('/logs', methods=['GET'])
@token_required
def get_audit_logs(current_user_email):
    logs = get_user_audits(current_user_email)
    return jsonify({"status": "success", "logs": logs})