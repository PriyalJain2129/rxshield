# app.py - RxShield CPOE System

from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import sqlite3
import hashlib
import os
import csv
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'cpoe_rxshield_2024')

# ── Email config ──────────────────────────────────────────────────
SENDER_EMAIL    = os.getenv('SENDER_EMAIL', '')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', '')

# ── DB Path ───────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hospital.db')

# ── Init DB — only creates tables, no CSV loading ─────────────────
def init_db():
    try:
        conn   = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            email      TEXT UNIQUE NOT NULL,
            password   TEXT NOT NULL,
            role       TEXT DEFAULT 'Doctor',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS patients (
            patient_id    TEXT PRIMARY KEY,
            age           INTEGER,
            gender        TEXT,
            condition     TEXT,
            current_drug  TEXT,
            dosage_mg     INTEGER,
            side_effects  TEXT,
            allergy_class TEXT,
            max_safe_dose INTEGER,
            interacts_with   TEXT,
            clinical_warning TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS drugs (
            drug_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            drug_name     TEXT UNIQUE,
            allergy_class TEXT,
            max_safe_dose INTEGER,
            interacts_with   TEXT,
            clinical_warning TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
            order_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id   TEXT,
            ordered_drug TEXT,
            ordered_dose INTEGER,
            status       TEXT,
            timestamp    DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS alerts (
            alert_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id    TEXT,
            ordered_drug  TEXT,
            alert_type    TEXT,
            alert_message TEXT,
            timestamp     DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()
        print("✅ Database tables ready")
    except Exception as e:
        print(f"⚠️ DB init error: {e}")

init_db()

# ── Helpers ───────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def is_logged_in():
    return 'user_id' in session

def get_current_user():
    if not is_logged_in(): return None
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return user

# ── Email ─────────────────────────────────────────────────────────
def send_welcome_email(to_email, name, role):
    try:
        if not SENDER_EMAIL or not SENDER_PASSWORD:
            print("⚠️ Email credentials not set, skipping email")
            return
        msg = MIMEMultipart('alternative')
        msg['Subject'] = '👋 Welcome to RxShield!'
        msg['From']    = f'RxShield <{SENDER_EMAIL}>'
        msg['To']      = to_email
        html = f"""
        <html><body style="font-family:Arial; background:#EAF7FB; padding:40px;">
        <div style="max-width:500px; margin:0 auto; background:white; border-radius:16px; overflow:hidden;">
            <div style="background:linear-gradient(135deg,#20343A,#1E7F8C); padding:32px; text-align:center;">
                <h1 style="color:white; margin:0;">⚕️ RxShield</h1>
                <p style="color:#BFEAF2; margin:6px 0 0;">Smart Prescription Safety System</p>
            </div>
            <div style="padding:32px;">
                <h2 style="color:#20343A;">Welcome, {name}! 👋</h2>
                <p style="color:#6b8a91;">Your account has been created successfully.</p>
                <div style="background:#EAF7FB; border-left:4px solid #1E7F8C; padding:16px; border-radius:8px; margin:20px 0;">
                    <p style="margin:4px 0;"><strong style="color:#1E7F8C;">Email:</strong> {to_email}</p>
                    <p style="margin:4px 0;"><strong style="color:#1E7F8C;">Role:</strong> {role}</p>
                </div>
                <a href="https://rxshield.onrender.com"
                   style="display:block; background:#1E7F8C; color:white; text-align:center;
                          padding:14px; border-radius:9px; text-decoration:none; font-weight:600;">
                    🚀 Open RxShield
                </a>
            </div>
            <div style="background:#EAF7FB; padding:20px; text-align:center;">
                <p style="color:#6b8a91; font-size:12px; margin:0;">
                    © 2025 RxShield — Smart Prescription Safety System
                </p>
            </div>
        </div>
        </body></html>
        """
        msg.attach(MIMEText(html, 'html'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"⚠️ Email failed: {e}")

def send_email_async(to_email, name, role):
    t = threading.Thread(target=send_welcome_email, args=(to_email, name, role))
    t.daemon = True
    t.start()

# ═════════════════════════════════════════════════════════════════
# AUTH ROUTES
# ═════════════════════════════════════════════════════════════════

@app.route('/login')
def login_page():
    if is_logged_in(): return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    if is_logged_in(): return redirect(url_for('home'))
    return render_template('signup.html')

@app.route('/api/signup', methods=['POST'])
def signup():
    data     = request.get_json()
    name     = data.get('name', '').strip()
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')
    role     = data.get('role', 'Doctor')

    if not name or not email or not password:
        return jsonify({'status': 'error', 'message': 'All fields are required.'})
    if len(password) < 6:
        return jsonify({'status': 'error', 'message': 'Password must be at least 6 characters.'})

    conn = get_db()
    if conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone():
        conn.close()
        return jsonify({'status': 'error', 'message': 'Email already registered.'})

    conn.execute('INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
                 (name, email, hash_password(password), role))
    conn.commit()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    session['user_id']   = user['user_id']
    session['user_name'] = user['name']
    session['user_role'] = user['role']
    conn.close()
    send_email_async(email, name, role)
    return jsonify({'status': 'success', 'message': f'Welcome, {name}!'})

@app.route('/api/login', methods=['POST'])
def login():
    data     = request.get_json()
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')
    if not email or not password:
        return jsonify({'status': 'error', 'message': 'Email and password are required.'})
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ? AND password = ?',
                        (email, hash_password(password))).fetchone()
    conn.close()
    if not user:
        return jsonify({'status': 'error', 'message': 'Invalid email or password.'})
    session['user_id']   = user['user_id']
    session['user_name'] = user['name']
    session['user_role'] = user['role']
    return jsonify({'status': 'success', 'message': f'Welcome back, {user["name"]}!'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/profile')
def profile_page():
    if not is_logged_in(): return redirect(url_for('login_page'))
    user        = get_current_user()
    conn        = get_db()
    order_count = conn.execute('SELECT COUNT(*) FROM orders').fetchone()[0]
    alert_count = conn.execute('SELECT COUNT(*) FROM alerts').fetchone()[0]
    conn.close()
    return render_template('profile.html', user=user,
                           order_count=order_count, alert_count=alert_count, page='profile')

# ═════════════════════════════════════════════════════════════════
# PAGE ROUTES
# ═════════════════════════════════════════════════════════════════

@app.route('/')
def home():
    if not is_logged_in(): return redirect(url_for('login_page'))
    conn = get_db()
    patients = conn.execute(
        'SELECT patient_id, age, gender, condition, current_drug, allergy_class FROM patients'
    ).fetchall()
    drugs_from_patients = conn.execute(
        'SELECT DISTINCT current_drug FROM patients ORDER BY current_drug'
    ).fetchall()
    drugs_from_table = conn.execute(
        'SELECT drug_name FROM drugs ORDER BY drug_name'
    ).fetchall()
    all_drugs = sorted(set(
        [r['current_drug'] for r in drugs_from_patients] +
        [r['drug_name']    for r in drugs_from_table]
    ))
    total_patients = conn.execute('SELECT COUNT(*) FROM patients').fetchone()[0]
    total_orders   = conn.execute('SELECT COUNT(*) FROM orders').fetchone()[0]
    total_alerts   = conn.execute('SELECT COUNT(*) FROM alerts').fetchone()[0]
    approved       = conn.execute("SELECT COUNT(*) FROM orders WHERE status='APPROVED'").fetchone()[0]
    conn.close()
    return render_template('index.html', patients=patients, drugs=all_drugs,
                           total_patients=total_patients, total_orders=total_orders,
                           total_alerts=total_alerts, approved=approved, page='home')

@app.route('/add-patient')
def add_patient_page():
    if not is_logged_in(): return redirect(url_for('login_page'))
    return render_template('add_patient.html', page='add_patient')

@app.route('/add-drug')
def add_drug_page():
    if not is_logged_in(): return redirect(url_for('login_page'))
    return render_template('add_drug.html', page='add_drug')

@app.route('/orders')
def orders_page():
    if not is_logged_in(): return redirect(url_for('login_page'))
    conn   = get_db()
    orders = conn.execute('SELECT * FROM orders ORDER BY timestamp DESC').fetchall()
    conn.close()
    return render_template('orders.html', orders=orders, page='orders')

@app.route('/alerts')
def alerts_page():
    if not is_logged_in(): return redirect(url_for('login_page'))
    conn   = get_db()
    alerts = conn.execute('SELECT * FROM alerts ORDER BY timestamp DESC').fetchall()
    conn.close()
    return render_template('alerts.html', alerts=alerts, page='alerts')

@app.route('/patients')
def patients_page():
    if not is_logged_in(): return redirect(url_for('login_page'))
    conn     = get_db()
    patients = conn.execute('SELECT * FROM patients').fetchall()
    conn.close()
    return render_template('patients.html', patients=patients, page='patients')

# ═════════════════════════════════════════════════════════════════
# ACTION ROUTES
# ═════════════════════════════════════════════════════════════════

@app.route('/save-patient', methods=['POST'])
def save_patient():
    if not is_logged_in(): return jsonify({'status': 'error', 'message': 'Not logged in'})
    data = request.get_json()
    conn = get_db()
    count  = conn.execute('SELECT COUNT(*) FROM patients').fetchone()[0]
    new_id = f"P{str(count + 1).zfill(4)}"
    try:
        conn.execute('''INSERT INTO patients
            (patient_id, age, gender, condition, current_drug, dosage_mg,
             side_effects, allergy_class, max_safe_dose, interacts_with, clinical_warning)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
            new_id, int(data['age']), data['gender'], data['condition'],
            data['current_drug'], int(data['dosage_mg']),
            data.get('side_effects', 'None'), data['allergy_class'],
            int(data['max_safe_dose']), data['interacts_with'],
            data.get('clinical_warning', 'None')))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'patient_id': new_id,
                        'message': f'Patient {new_id} added successfully!'})
    except Exception as e:
        conn.close()
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/save-drug', methods=['POST'])
def save_drug():
    if not is_logged_in(): return jsonify({'status': 'error', 'message': 'Not logged in'})
    data = request.get_json()
    conn = get_db()
    try:
        conn.execute('''INSERT INTO drugs
            (drug_name, allergy_class, max_safe_dose, interacts_with, clinical_warning)
            VALUES (?, ?, ?, ?, ?)''',
            (data['drug_name'], data['allergy_class'], int(data['max_safe_dose']),
             data['interacts_with'], data['clinical_warning']))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'message': f"{data['drug_name']} added!"})
    except Exception as e:
        conn.close()
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/check-order', methods=['POST'])
def check_order():
    if not is_logged_in(): return jsonify({'status': 'error', 'message': 'Not logged in'})
    data         = request.get_json()
    patient_id   = data.get('patient_id')
    ordered_drug = data.get('ordered_drug', '').strip()
    ordered_dose = int(data.get('ordered_dose', 0))

    conn    = get_db()
    patient = conn.execute('SELECT * FROM patients WHERE patient_id = ?', (patient_id,)).fetchone()
    if not patient:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Patient not found'})

    drug_info = conn.execute(
        'SELECT * FROM patients WHERE LOWER(current_drug) = LOWER(?) LIMIT 1', (ordered_drug,)
    ).fetchone()
    if not drug_info:
        drug_info = conn.execute(
            'SELECT * FROM drugs WHERE LOWER(drug_name) = LOWER(?) LIMIT 1', (ordered_drug,)
        ).fetchone()

    if not drug_info:
        conn.close()
        return jsonify({'status': 'warning',
                        'message': f'⚠️ Drug "{ordered_drug}" not found in database.',
                        'alerts': [{'type': '⚠️ UNKNOWN DRUG',
                                    'message': f'Cannot verify safety. Add via Add Drug page.'}]})

    alerts      = []
    alert_level = 'safe'

    # Rule 1: Dose
    if ordered_dose > drug_info['max_safe_dose']:
        alerts.append({'type': '🚨 DOSE EXCEEDED',
                       'message': f"Max safe dose is {drug_info['max_safe_dose']}mg. You ordered {ordered_dose}mg!"})
        alert_level = 'danger'

    # Rule 2: Allergy
    if drug_info['allergy_class'] and patient['allergy_class']:
        if drug_info['allergy_class'].lower() == patient['allergy_class'].lower() \
                and ordered_drug.lower() != patient['current_drug'].lower():
            alerts.append({'type': '🚨 ALLERGY ALERT',
                           'message': f"Patient sensitive to {patient['allergy_class']}. {ordered_drug} is same class!"})
            alert_level = 'danger'

    # Rule 3: Interaction
    interactions = [i.strip().lower() for i in drug_info['interacts_with'].split('|')]
    if patient['current_drug'].strip().lower() in interactions:
        alerts.append({'type': '⚠️ DRUG INTERACTION',
                       'message': f"{ordered_drug} interacts with {patient['current_drug']}. {drug_info['clinical_warning']}"})
        if alert_level != 'danger': alert_level = 'warning'

    # Rule 4: Elderly
    risky = ['ibuprofen','tramadol','ciprofloxacin','glipizide','metoprolol','amlodipine']
    if patient['age'] > 65 and ordered_drug.lower() in risky:
        alerts.append({'type': '⚠️ ELDERLY RISK',
                       'message': f"Patient is {patient['age']} yrs. Higher risk for 65+ patients."})
        if alert_level != 'danger': alert_level = 'warning'

    # Rule 5: Duplicate
    if ordered_drug.lower() == patient['current_drug'].lower():
        alerts.append({'type': '⚠️ DUPLICATE ORDER',
                       'message': f"Patient already on {patient['current_drug']}. Possible duplicate!"})
        if alert_level != 'danger': alert_level = 'warning'

    # Rule 6: Invalid dose
    if ordered_dose <= 0:
        alerts.append({'type': '⚠️ INVALID DOSE', 'message': 'Dose must be greater than 0.'})
        if alert_level != 'danger': alert_level = 'warning'

    status = 'APPROVED' if alert_level == 'safe' else 'FLAGGED'
    conn.execute('INSERT INTO orders (patient_id, ordered_drug, ordered_dose, status) VALUES (?, ?, ?, ?)',
                 (patient_id, ordered_drug, ordered_dose, status))
    for alert in alerts:
        conn.execute('INSERT INTO alerts (patient_id, ordered_drug, alert_type, alert_message) VALUES (?, ?, ?, ?)',
                     (patient_id, ordered_drug, alert['type'], alert['message']))
    conn.commit()
    conn.close()

    if alert_level == 'safe':
        return jsonify({'status': 'safe',
                        'message': f'✅ Order APPROVED — {ordered_drug} {ordered_dose}mg is safe.',
                        'alerts': []})
    return jsonify({'status': alert_level,
                    'message': f'Order flagged — {len(alerts)} issue(s) found.',
                    'alerts': alerts})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)