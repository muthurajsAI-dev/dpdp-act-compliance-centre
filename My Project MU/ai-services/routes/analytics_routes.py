from flask import Blueprint, render_template, jsonify
import sqlite3

analytics_bp = Blueprint('analytics', __name__)

def get_db():
    conn = sqlite3.connect('app_data.db')
    conn.row_factory = sqlite3.Row
    return conn

@analytics_bp.route('/')
def analytics_page():
    return render_template('analytics.html')

@analytics_bp.route('/data', methods=['GET'])
def get_analytics_metrics():
    db = get_db()
    cursor = db.cursor()
    try:
        # Fetch counts from respective tables if they exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row['name'] for row in cursor.fetchall()]
        
        total_principals = 0
        if 'data_principals' in tables:
            cursor.execute("SELECT COUNT(*) as count FROM data_principals")
            total_principals = cursor.fetchone()['count']
            
        total_consents = 0
        granted_consents = 0
        withdrawn_consents = 0
        if 'consent_records' in tables:
            cursor.execute("SELECT COUNT(*) as count FROM consent_records")
            total_consents = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM consent_records WHERE status = 'Granted'")
            granted_consents = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM consent_records WHERE status = 'Withdrawn'")
            withdrawn_consents = cursor.fetchone()['count']
            
        total_risks = 0
        critical_risks = 0
        if 'risk_logs' in tables:
            cursor.execute("SELECT COUNT(*) as count FROM risk_logs")
            total_risks = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM risk_logs WHERE risk_level IN ('High', 'Critical')")
            critical_risks = cursor.fetchone()['count']

        return jsonify({
            "status": "success",
            "metrics": {
                "total_principals": total_principals,
                "total_consents": total_consents,
                "granted_consents": granted_consents,
                "withdrawn_consents": withdrawn_consents,
                "total_risks": total_risks,
                "critical_risks": critical_risks
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db.close()