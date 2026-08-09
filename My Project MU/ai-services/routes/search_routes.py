from flask import Blueprint, request, jsonify
from middleware.auth import token_required
from database import get_user_audits, search_dpdp_sections

search_bp = Blueprint('search_bp', __name__)

NAV_ITEMS = [
    {"label": "Dashboard", "url": "/profile"},
    {"label": "Compliance Audit", "url": "/audit/compliance-audit"},
    {"label": "AI Assistant", "url": "/profile#assistant"},
    {"label": "Reports", "url": "/reports/"},
    {"label": "Data Principals", "url": "/principals/"},
    {"label": "Consent Manager", "url": "/consent/"},
    {"label": "Risk Monitor", "url": "/risk/"},
    {"label": "Analytics Dashboard", "url": "/analytics/"},
    {"label": "Settings", "url": "/account/settings"},
]

@search_bp.route('', methods=['GET'])
@token_required
def global_search(current_user_email):
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"status": "success", "documents": [], "clauses": [], "nav": []})

    q_lower = query.lower()

    all_audits = get_user_audits(current_user_email)
    documents = [a for a in all_audits if q_lower in a['filename'].lower()][:5]

    clauses = search_dpdp_sections(query, limit=5)

    nav = [n for n in NAV_ITEMS if q_lower in n['label'].lower()]

    return jsonify({
        "status": "success",
        "documents": documents,
        "clauses": clauses,
        "nav": nav
    })