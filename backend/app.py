import os
import re
from datetime import datetime

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash

from database import db_execute

app = Flask(__name__)
app.secret_key = "rxshield_secret_key_2026"


# CORS: target ONLY API routes and explicitly allow the Vercel origin.
CORS(
    app,
    supports_credentials=True,
    resources={
        r"/api/*": {
            "origins": [
                "https://rx-shield.vercel.app",
                "http://localhost:8080",
            ]
        }
    },
)

# --- 1. AUTHENTICATION ---

@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    try:
        if request.method == "OPTIONS":
            return "", 200
        data = request.get_json(force=True)
        email = data.get('email', '').lower().strip()
        users = db_execute("SELECT * FROM users WHERE email = %s", (email,))
        if users:
            user = users[0]
            session['user_id'] = user.get('user_id') or user.get('id')
            return jsonify({"status": "success", "user": {"name": user['name']}})
        return jsonify({"status": "error"}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/signup', methods=['POST', 'OPTIONS'])
def signup():
    try:
        if request.method == "OPTIONS":
            return "", 200
        data = request.get_json(force=True)
        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).lower().strip()
        password = str(data.get("password", "")).strip()

        if not name or not email or not password:
            return jsonify({"status": "error", "message": "Missing name/email/password"}), 400

        existing = db_execute("SELECT * FROM users WHERE email = %s", (email,))
        if existing:
            return jsonify({"status": "error", "message": "Email already exists"}), 409

        password_hash = generate_password_hash(password)
        db_execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (name, email, password_hash, "Doctor"),
            is_select=False,
        )

        user = db_execute("SELECT * FROM users WHERE email = %s", (email,))
        if not user:
            return jsonify({"status": "error", "message": "User not found after signup"}), 500

        u = user[0]
        session["user_id"] = u.get("user_id") or u.get("id")
        return jsonify({"status": "success", "user": {"name": u["name"], "email": u.get("email")}})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"status": "success"})


@app.route('/api/me', methods=['GET'])
def get_me():
    uid = session.get('user_id')
    if not uid:
        return jsonify({"error": "Unauthorized"}), 401
    user = db_execute(
        "SELECT name, email FROM users WHERE user_id = %s", (uid,)
    )
    return jsonify(user[0]) if user else (jsonify({"error": "Not found"}), 404)

# --- 2. DATA RETRIEVAL ---

@app.route('/api/patients', methods=['GET'])
def get_patients():
    # Newest / highest patient_id first (e.g. demo IDs P1005, P2000 at top); cap at 150 rows.
    query = (
        "SELECT patient_id AS id, patient_id AS name, age, gender, condition, "
        "allergy_class AS allergy, allergy_class AS allergy_class, current_drug "
        "FROM patients ORDER BY patient_id DESC LIMIT 150"
    )
    try:
        raw_data = db_execute(query)
        if not raw_data:
            return jsonify([])
        clean_data = []
        for r in raw_data:
            try:
                if isinstance(r, dict):
                    clean_data.append(dict(r))
                else:
                    clean_data.append({
                        "id": r[0],
                        "name": r[1],
                        "age": r[2],
                        "gender": r[3],
                        "condition": r[4],
                        "allergy": r[5],
                        "allergy_class": r[6],
                        "current_drug": r[7],
                    })
            except (KeyError, IndexError, TypeError):
                continue
        return jsonify(clean_data)
    except Exception:
        return jsonify([])


@app.route('/api/add-patient', methods=['POST'])
def add_patient():
    try:
        data = request.get_json(force=True)
        patient_id = str(data.get('patient_id', '')).strip()
        age = int(data.get('age'))
        gender = str(data.get('gender', '')).strip()
        condition = str(data.get('condition', '')).strip()
        allergy_class = str(
            data.get('allergy_class') or data.get('allergy') or ''
        ).strip()
        current_drug = str(data.get('current_drug', '')).strip() or 'None'
        max_safe_dose_mg = int(data.get('max_safe_dose_mg'))
        dosage_mg = int(data['dosage_mg']) if data.get('dosage_mg') is not None else 0
        interacts_with = str(data.get('interacts_with', '') or '').strip()
        clinical_warning = str(data.get('clinical_warning', '') or '').strip()

        if not patient_id:
            return jsonify({"status": "error", "message": "patient_id required"}), 400

        db_execute(
            """
            INSERT INTO patients (
                patient_id, age, gender, condition, current_drug,
                dosage_mg, allergy_class, max_safe_dose_mg,
                interacts_with, clinical_warning
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                patient_id,
                age,
                gender,
                condition,
                current_drug,
                dosage_mg,
                allergy_class,
                max_safe_dose_mg,
                interacts_with,
                clinical_warning,
            ),
            is_select=False,
        )
        return jsonify({"status": "success"})
    except (TypeError, ValueError) as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/drugs', methods=['GET'])
def get_drugs():
    query = "SELECT DISTINCT current_drug, max_safe_dose_mg FROM patients WHERE current_drug IS NOT NULL"
    try:
        data = db_execute(query)
        return jsonify([{"id": d[0], "name": d[0], "max_safe_dose": d[1]} for d in data])
    except:
        # Fallback if db_execute returns dicts
        raw = db_execute(query)
        return jsonify([{"id": d['current_drug'], "name": d['current_drug']} for d in raw])

# --- 3. SAFETY ENGINE & ORDERS ---

@app.route('/api/check-order', methods=['POST'])
def check_order():
    data = request.get_json(force=True)
    patient_results = db_execute("SELECT max_safe_dose_mg FROM patients WHERE patient_id = %s", (data['patient_id'],))
    if not patient_results: return jsonify({"alerts": []})
    
    # Check if data is tuple or dict
    p_limit = patient_results[0][0] if isinstance(patient_results[0], (tuple, list)) else patient_results[0]['max_safe_dose_mg']
    
    alerts = []
    if int(data['dosage']) > p_limit:
        alerts.append({
            "rule": "Dose Exceeded", 
            "status": "danger", 
            "type": "DANGER",
            "msg": f"Limit: {p_limit}mg",
            "message": f"Dose {data['dosage']}mg exceeds limit."
        })
    return jsonify({"alerts": alerts})

@app.route('/api/create-order', methods=['POST'])
def create_order():
    try:
        data = request.get_json(force=True)
        # We perform a quick safety check to set the status
        status = 'APPROVED'
        res = db_execute("SELECT max_safe_dose_mg FROM patients WHERE patient_id = %s", (data['patient_id'],))
        if res:
            limit = res[0][0] if isinstance(res[0], (tuple, list)) else res[0]['max_safe_dose_mg']
            if int(data['dosage']) > limit: status = 'FLAGGED'

        db_execute(
            "INSERT INTO orders (patient_id, ordered_drug, ordered_dose, status) VALUES (%s, %s, %s, %s)", 
            (data['patient_id'], data['drug_name'], data['dosage'], status), 
            is_select=False
        )
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/orders', methods=['GET'])
def get_orders():
    # POSITION IS KEY: 0:id, 1:pid, 2:drug, 3:dose, 4:date, 5:status
    query = "SELECT order_id, patient_id, ordered_drug, ordered_dose, created_at, status FROM orders ORDER BY order_id DESC"
    try:
        raw_rows = db_execute(query)
        clean_orders = []
        for r in raw_rows:
            # We extract by index to ensure 'patient_id' is never missed
            is_tuple = isinstance(r, (tuple, list))
            p_id = r[1] if is_tuple else r['patient_id']
            
            clean_orders.append({
                "id": r[0] if is_tuple else r['order_id'],
                "patient": str(p_id), # 👈 This fills the blank column
                "drug": r[2] if is_tuple else r['ordered_drug'],
                "dose": r[3] if is_tuple else r['ordered_dose'],
                "date": (r[4] if is_tuple else r['created_at']).strftime('%b %d, %H:%M') if (r[4] if is_tuple else r['created_at']) else "Recent",
                "status": r[5] if is_tuple else r['status']
            })
        return jsonify(clean_orders)
    except Exception as e:
        print(f"Mapping Error: {e}")
        return jsonify([])

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    query = "SELECT order_id, patient_id, ordered_drug, ordered_dose, created_at, status FROM orders WHERE status = 'FLAGGED' ORDER BY order_id DESC"
    try:
        raw_rows = db_execute(query)
        clean_alerts = []
        for r in raw_rows:
            is_tuple = isinstance(r, (tuple, list))
            clean_alerts.append({
                "id": r[0] if is_tuple else r['order_id'],
                "patient": str(r[1] if is_tuple else r['patient_id']),
                "drug": r[2] if is_tuple else r['ordered_drug'],
                "dose": r[3] if is_tuple else r['ordered_dose'],
                "date": (r[4] if is_tuple else r['created_at']).strftime('%b %d, %H:%M') if (r[4] if is_tuple else r['created_at']) else "Recent",
                "status": r[5] if is_tuple else r['status']
            })
        return jsonify(clean_alerts)
    except:
        return jsonify([])

if __name__ == '__main__':
    app.run(debug=True, port=5000)