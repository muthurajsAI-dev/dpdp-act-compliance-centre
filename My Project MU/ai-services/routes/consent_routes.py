from flask import Blueprint, render_template, jsonify, request
import sqlite3

consent_bp = Blueprint('consent', __name__)

def get_db():
    conn = sqlite3.connect('app_data.db')
    conn.row_factory = sqlite3.Row
    return conn

@consent_bp.route('/')
def consent_page():
    return render_template('consent.html')

@consent_bp.route('/data', methods=['GET'])
def get_consent_data():
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS consent_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                principal_email TEXT,
                purpose TEXT,
                status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()
        
        cursor.execute("SELECT * FROM consent_records ORDER BY id DESC")
        consents = [dict(row) for row in cursor.fetchall()]
            
        return jsonify({
            "status": "success",
            "total_records": len(consents),
            "consents": consents
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db.close()

@consent_bp.route('/add', methods=['POST'])
def add_consent():
    data = request.json
    email = data.get('principal_email')
    purpose = data.get('purpose')
    status = data.get('status', 'Granted')
    
    if not email or not purpose:
        return jsonify({"status": "error", "message": "Email and purpose are required"}), 400
        
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO consent_records (principal_email, purpose, status) VALUES (?, ?, ?)",
            (email, purpose, status)
        )
        db.commit()
        return jsonify({"status": "success", "message": "Consent record added successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db.close()

@consent_bp.route('/update/<int:consent_id>', methods=['POST'])
def update_consent(consent_id):
    data = request.json
    new_status = data.get('status')
    
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE consent_records SET status = ? WHERE id = ?",
            (new_status, consent_id)
        )
        db.commit()
        return jsonify({"status": "success", "message": "Consent status updated successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db.close()