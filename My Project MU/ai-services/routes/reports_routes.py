from flask import Blueprint, render_template, jsonify
from middleware.auth import token_required
from database import get_user_audits

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
def reports_page():
    return render_template('reports.html')

@reports_bp.route('/data', methods=['GET'])
@token_required
def get_reports_data(current_user_email):
    logs = get_user_audits(current_user_email)
    return jsonify({
        "status": "success",
        "total_records": len(logs),
        "reports": logs
    })