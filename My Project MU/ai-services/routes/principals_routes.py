from flask import Blueprint, render_template, jsonify, request
import sqlite3

principals_bp = Blueprint('principals', __name__)

def get_db():
    conn = sqlite3.connect('app_data.db')
    conn.row_factory = sqlite3.Row
    return conn

@principals_bp.route('/')
def principals_page():
    return render_template('principals.html')

@principals_bp.route('/data', methods=['GET'])
def get_principals_data():
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_principals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT,
                consent_status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()
        
        cursor.execute("SELECT * FROM data_principals ORDER BY id DESC")
        principals = [dict(row) for row in cursor.fetchall()]
            
        return jsonify({
            "status": "success",
            "total_records": len(principals),
            "principals": principals
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db.close()

@principals_bp.route('/add', methods=['POST'])
def add_principal():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    consent_status = data.get('consent_status', 'Granted')
    
    if not name or not email:
        return jsonify({"status": "error", "message": "Name and email are required"}), 400
        
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO data_principals (name, email, consent_status) VALUES (?, ?, ?)",
            (name, email, consent_status)
        )
        db.commit()
        return jsonify({"status": "success", "message": "Data principal added successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db.close()