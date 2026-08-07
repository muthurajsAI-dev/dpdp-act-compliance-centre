from flask import Blueprint, render_template, session, redirect, url_for
from database import SessionLocal

audit_bp = Blueprint('audit', __name__)

@audit_bp.route('/compliance-audit')
def compliance_audit():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    db = SessionLocal()
    try:
        return render_template('compliance_audit.html')
    finally:
        db.close()