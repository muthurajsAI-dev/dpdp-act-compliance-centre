from flask import Blueprint, render_template, jsonify, request
import sqlite3

risk_bp = Blueprint('risk', __name__)

def get_db():
    conn = sqlite3.connect('app_data.db')
    conn.row_factory = sqlite3.Row
    return conn

@risk_bp.route('/')
def risk_page():
    return render_template('risk_monitor.html')

@risk_bp.route('/data', methods=['GET'])
def get_risk_data():
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT,
                risk_level TEXT,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()
        
        cursor.execute("SELECT * FROM risk_logs ORDER BY id DESC")
        risks = [dict(row) for row in cursor.fetchall()]
            
        return jsonify({
            "status": "success",
            "total_records": len(risks),
            "risks": risks
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db.close()

@risk_bp.route('/add', methods=['POST'])
def add_risk():
    data = request.json
    user_email = data.get('user_email')
    risk_level = data.get('risk_level', 'Medium')
    description = data.get('description')
    
    if not user_email or not description:
        return jsonify({"status": "error", "message": "User email and description are required"}), 400
        
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO risk_logs (user_email, risk_level, description) VALUES (?, ?, ?)",
            (user_email, risk_level, description)
        )
        db.commit()
        return jsonify({"status": "success", "message": "Risk log added successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db.close()