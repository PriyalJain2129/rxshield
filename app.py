# app.py - Full CPOE System with Authentication + All Features

from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import sqlite3
import hashlib
import os
import csv
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'cpoe_secret_key_rknec_2024')

# ── Email config — loaded from .env ──────────────────────────────
from dotenv import load_dotenv
load_dotenv()
SENDER_EMAIL    = os.getenv('SENDER_EMAIL', '')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', '')

# ── Helper: send welcome email ────────────────────────────────────
def send_welcome_email(to_email, name, role):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = '👋 Welcome to RxShield!'
        msg['From']    = f'RxShield <{SENDER_EMAIL}>'
        msg['To']      = to_email

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin:0; padding:0; background:#EAF7FB; font-family: Arial, sans-serif;">

            <!-- Wrapper -->
            <table width="100%" cellpadding="0" cellspacing="0" style="background:#EAF7FB; padding: 40px 20px;">
                <tr><td align="center">

                    <!-- Card -->
                    <table width="600" cellpadding="0" cellspacing="0"
                           style="background:#ffffff; border-radius:16px; overflow:hidden;
                                  box-shadow: 0 4px 24px rgba(30,127,140,0.12); max-width:600px; width:100%;">

                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #20343A 0%, #1E7F8C 100%);
                                       padding: 40px 40px 32px; text-align:center;">
                                <!-- Caduceus icon -->
                                <div style="width:64px; height:64px; background:#1E7F8C;
                                            border-radius:18px; margin:0 auto 16px;
                                            border: 3px solid rgba(99,201,214,0.5);
                                            display:flex; align-items:center; justify-content:center;
                                            font-size:32px; line-height:64px; text-align:center;">
                                    ⚕️
                                </div>
                                <h1 style="color:#ffffff; margin:0; font-size:28px;
                                           font-weight:700; letter-spacing:-0.5px;">
                                    RxShield
                                </h1>
                                <p style="color:#BFEAF2; margin:6px 0 0; font-size:14px;">
                                    Smart Prescription Safety System
                                </p>
                            </td>
                        </tr>

                        <!-- Body -->
                        <tr>
                            <td style="padding: 40px;">

                                <h2 style="color:#20343A; font-size:22px; margin:0 0 8px;">
                                    Welcome aboard, {name}! 👋
                                </h2>
                                <p style="color:#6b8a91; font-size:15px; margin:0 0 24px; line-height:1.6;">
                                    Your account has been successfully created.
                                    You're now part of the RxShield family.
                                </p>

                                <!-- Info Box -->
                                <table width="100%" cellpadding="0" cellspacing="0"
                                       style="background:#EAF7FB; border-radius:10px;
                                              border-left: 4px solid #1E7F8C; margin-bottom:28px;">
                                    <tr>
                                        <td style="padding: 18px 20px;">
                                            <p style="margin:4px 0; color:#20343A; font-size:14px;">
                                                <strong style="color:#1E7F8C;">Name:</strong> &nbsp;{name}
                                            </p>
                                            <p style="margin:4px 0; color:#20343A; font-size:14px;">
                                                <strong style="color:#1E7F8C;">Email:</strong> &nbsp;{to_email}
                                            </p>
                                            <p style="margin:4px 0; color:#20343A; font-size:14px;">
                                                <strong style="color:#1E7F8C;">Role:</strong> &nbsp;{role}
                                            </p>
                                        </td>
                                    </tr>
                                </table>

                                <!-- What you can do -->
                                <h3 style="color:#20343A; font-size:16px; margin:0 0 14px;">
                                    What you can do with RxShield:
                                </h3>

                                <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
                                    <tr>
                                        <td style="padding:8px 0; border-bottom:1px solid #EAF7FB; font-size:14px; color:#20343A;">
                                            🔍 &nbsp; Check medication orders for safety in real-time
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding:8px 0; border-bottom:1px solid #EAF7FB; font-size:14px; color:#20343A;">
                                            🚨 &nbsp; Get instant alerts for drug interactions and allergies
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding:8px 0; border-bottom:1px solid #EAF7FB; font-size:14px; color:#20343A;">
                                            👥 &nbsp; Manage patient records and medication history
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding:8px 0; font-size:14px; color:#20343A;">
                                            📋 &nbsp; Track all orders and audit trail
                                        </td>
                                    </tr>
                                </table>

                                <!-- CTA Button -->
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td align="center">
                                            <a href="https://rxshield.onrender.com"
                                               style="display:inline-block; background:#1E7F8C;
                                                      color:#ffffff; text-decoration:none;
                                                      padding:14px 36px; border-radius:9px;
                                                      font-size:15px; font-weight:600;
                                                      letter-spacing:0.3px;">
                                                🚀 &nbsp; Open RxShield
                                            </a>
                                        </td>
                                    </tr>
                                </table>

                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="background:#EAF7FB; padding:24px 40px; text-align:center;
                                       border-top: 1px solid #BFEAF2;">
                                <p style="color:#6b8a91; font-size:12px; margin:0; line-height:1.6;">
                                    This email was sent by RxShield — Smart Prescription Safety System.<br>
                                    RKNEC B.Tech Final Year Project · Nagpur, Maharashtra
                                </p>
                                <p style="color:#BFEAF2; font-size:11px; margin:8px 0 0;">
                                    © 2025 RxShield. All rights reserved.
                                </p>
                            </td>
                        </tr>

                    </table>
                    <!-- End Card -->

                </td></tr>
            </table>

        </body>
        </html>
        """

        msg.attach(MIMEText(html, 'html'))

        # Connect to Gmail and send
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        print(f"✅ Welcome email sent to {to_email}")

    except Exception as e:
        # Email failing should NOT break signup — just log it
        print(f"⚠️ Email failed: {e}")

def send_welcome_email_async(to_email, name, role):
    """Send email in background thread so signup is never blocked"""
    thread = threading.Thread(target=send_welcome_email, args=(to_email, name, role))
    thread.daemon = True
    thread.start()

# ── Database setup — PostgreSQL on Render, SQLite locally ─────────
DATABASE_URL = os.getenv('DATABASE_URL', '')
USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras
    # Render sometimes gives 'postgres://' but psycopg2 needs 'postgresql://'
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

def get_db():
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        import sqlite3
        DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hospital.db')
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def db_execute(conn, query, params=(), fetchone=False, fetchall=False):
    """Universal query executor for both PostgreSQL and SQLite"""
    if USE_POSTGRES:
        # PostgreSQL uses %s placeholders, SQLite uses ?
        query = query.replace('?', '%s')
        # PostgreSQL uses SERIAL instead of AUTOINCREMENT
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        cur = conn.cursor()

    cur.execute(query, params)

    if fetchone:
        row = cur.fetchone()
        if USE_POSTGRES and row:
            return dict(row)
        return row
    if fetchall:
        rows = cur.fetchall()
        if USE_POSTGRES:
            return [dict(r) for r in rows]
        return rows
    return cur

# ── Helper: hash password ─────────────────────────────────────────
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ── Helper: check if logged in ────────────────────────────────────
def is_logged_in():
    return 'user_id' in session

# ── Helper: get current user ──────────────────────────────────────
def get_current_user():
    if not is_logged_in():
        return None
    conn = get_db()
    user = db_execute(conn,
        'SELECT * FROM users WHERE user_id = ?', (session['user_id'],), fetchone=True)
    conn.close()
    return user

# ── Init DB — runs once on startup ───────────────────────────────
def init_db():
    conn = get_db()
    cur  = conn.cursor()

    if USE_POSTGRES:
        cur.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL, role TEXT DEFAULT 'Doctor',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS patients (
            patient_id TEXT PRIMARY KEY, age INTEGER, gender TEXT,
            condition TEXT, current_drug TEXT, dosage_mg INTEGER,
            side_effects TEXT, allergy_class TEXT, max_safe_dose INTEGER,
            interacts_with TEXT, clinical_warning TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS drugs (
            drug_id SERIAL PRIMARY KEY,
            drug_name TEXT UNIQUE, allergy_class TEXT,
            max_safe_dose INTEGER, interacts_with TEXT, clinical_warning TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS orders (
            order_id SERIAL PRIMARY KEY,
            patient_id TEXT, ordered_drug TEXT, ordered_dose INTEGER,
            status TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS alerts (
            alert_id SERIAL PRIMARY KEY,
            patient_id TEXT, ordered_drug TEXT, alert_type TEXT,
            alert_message TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    else:
        cur.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL, role TEXT DEFAULT 'Doctor',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS patients (
            patient_id TEXT PRIMARY KEY, age INTEGER, gender TEXT,
            condition TEXT, current_drug TEXT, dosage_mg INTEGER,
            side_effects TEXT, allergy_class TEXT, max_safe_dose INTEGER,
            interacts_with TEXT, clinical_warning TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS drugs (
            drug_id INTEGER PRIMARY KEY AUTOINCREMENT,
            drug_name TEXT UNIQUE, allergy_class TEXT,
            max_safe_dose INTEGER, interacts_with TEXT, clinical_warning TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT, ordered_drug TEXT, ordered_dose INTEGER,
            status TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS alerts (
            alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT, ordered_drug TEXT, alert_type TEXT,
            alert_message TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    # Load CSV if patients table is empty
    cur.execute('SELECT COUNT(*) FROM patients')
    count = cur.fetchone()
    count = count[0] if isinstance(count, tuple) else list(count.values())[0]

    if count == 0:
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'real_drug_dataset_updated.csv')
        if os.path.exists(csv_path):
            with open(csv_path, encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                rows = [(
                    row['Patient_ID'], int(row['Age']), row['Gender'],
                    row['Condition'], row['Drug_Name'], int(row['Dosage_mg']),
                    row['Side_Effects'], row['Allergy_Class'],
                    int(row['Max_Safe_Dose_mg']), row['Interacts_With'],
                    row['Clinical_Warning']
                ) for row in reader]

            ph = ','.join(['%s'] * 11) if USE_POSTGRES else ','.join(['?'] * 11)
            cur.executemany(f'INSERT INTO patients VALUES ({ph})', rows)
            print(f"✅ Loaded {len(rows)} patients into DB")
        else:
            print("⚠️ CSV not found")

    conn.commit()
    conn.close()
    print("✅ Database ready")

# ── Lazy init — runs on first request only ────────────────────────
@app.route('/health')
def health():
    init_db()
    return 'OK', 200

# ═════════════════════════════════════════════════════════════════
# AUTH ROUTES
# ═════════════════════════════════════════════════════════════════

@app.route('/login')
def login_page():
    if is_logged_in():
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    if is_logged_in():
        return redirect(url_for('home'))
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
    try:
        existing = db_execute(conn, 'SELECT * FROM users WHERE email = ?', (email,), fetchone=True)
        if existing:
            conn.close()
            return jsonify({'status': 'error', 'message': 'An account with this email already exists.'})

        hashed = hash_password(password)
        db_execute(conn, 'INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
                   (name, email, hashed, role))
        conn.commit()

        user = db_execute(conn, 'SELECT * FROM users WHERE email = ?', (email,), fetchone=True)
        session['user_id']   = user['user_id']
        session['user_name'] = user['name']
        session['user_role'] = user['role']
        conn.close()

        send_welcome_email_async(email, name, role)
        return jsonify({'status': 'success', 'message': f'Welcome, {name}!'})
    except Exception as e:
        conn.close()
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/login', methods=['POST'])
def login():
    data     = request.get_json()
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'status': 'error', 'message': 'Email and password are required.'})

    conn   = get_db()
    hashed = hash_password(password)
    user   = db_execute(conn, 'SELECT * FROM users WHERE email = ? AND password = ?',
                        (email, hashed), fetchone=True)
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
    if not is_logged_in():
        return redirect(url_for('login_page'))
    user = get_current_user()
    conn = get_db()
    order_count = db_execute(conn, 'SELECT COUNT(*) FROM orders', fetchone=True)
    alert_count = db_execute(conn, 'SELECT COUNT(*) FROM alerts', fetchone=True)
    conn.close()
    order_count = list(order_count.values())[0] if isinstance(order_count, dict) else order_count[0]
    alert_count = list(alert_count.values())[0] if isinstance(alert_count, dict) else alert_count[0]
    return render_template('profile.html', user=user,
                           order_count=order_count,
                           alert_count=alert_count,
                           page='profile')

# ═════════════════════════════════════════════════════════════════
# PAGE ROUTES (all protected — must be logged in)
# ═════════════════════════════════════════════════════════════════

@app.route('/')
def home():
    if not is_logged_in():
        return redirect(url_for('login_page'))
    conn = get_db()

    def val(row, key):
        return row[key] if isinstance(row, dict) else row[key]

    patients         = db_execute(conn, 'SELECT patient_id, age, gender, condition, current_drug, allergy_class FROM patients', fetchall=True)
    drugs_patients   = db_execute(conn, 'SELECT DISTINCT current_drug FROM patients ORDER BY current_drug', fetchall=True)
    drugs_table      = db_execute(conn, 'SELECT drug_name FROM drugs ORDER BY drug_name', fetchall=True)
    all_drugs        = sorted(set(
        [r['current_drug'] for r in drugs_patients] +
        [r['drug_name']    for r in drugs_table]
    ))
    def get_count(query):
        row = db_execute(conn, query, fetchone=True)
        return list(row.values())[0] if isinstance(row, dict) else row[0]

    total_patients = get_count('SELECT COUNT(*) FROM patients')
    total_orders   = get_count('SELECT COUNT(*) FROM orders')
    total_alerts   = get_count('SELECT COUNT(*) FROM alerts')
    approved       = get_count("SELECT COUNT(*) FROM orders WHERE status='APPROVED'")
    conn.close()
    return render_template('index.html',
                           patients=patients, drugs=all_drugs,
                           total_patients=total_patients,
                           total_orders=total_orders,
                           total_alerts=total_alerts,
                           approved=approved, page='home')

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
    orders = db_execute(conn, 'SELECT * FROM orders ORDER BY timestamp DESC', fetchall=True)
    conn.close()
    return render_template('orders.html', orders=orders, page='orders')

@app.route('/alerts')
def alerts_page():
    if not is_logged_in(): return redirect(url_for('login_page'))
    conn   = get_db()
    alerts = db_execute(conn, 'SELECT * FROM alerts ORDER BY timestamp DESC', fetchall=True)
    conn.close()
    return render_template('alerts.html', alerts=alerts, page='alerts')

@app.route('/patients')
def patients_page():
    if not is_logged_in(): return redirect(url_for('login_page'))
    conn     = get_db()
    patients = db_execute(conn, 'SELECT * FROM patients', fetchall=True)
    conn.close()
    return render_template('patients.html', patients=patients, page='patients')

# ═════════════════════════════════════════════════════════════════
# ACTION ROUTES
# ═════════════════════════════════════════════════════════════════

@app.route('/save-patient', methods=['POST'])
def save_patient():
    if not is_logged_in():
        return jsonify({'status': 'error', 'message': 'Not logged in'})
    data = request.get_json()
    conn = get_db()
    try:
        row    = db_execute(conn, 'SELECT COUNT(*) FROM patients', fetchone=True)
        count  = list(row.values())[0] if isinstance(row, dict) else row[0]
        new_id = f"P{str(count + 1).zfill(4)}"
        db_execute(conn, '''INSERT INTO patients
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
    if not is_logged_in():
        return jsonify({'status': 'error', 'message': 'Not logged in'})
    data = request.get_json()
    conn = get_db()
    try:
        db_execute(conn, '''INSERT INTO drugs
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
    if not is_logged_in():
        return jsonify({'status': 'error', 'message': 'Not logged in'})
    data         = request.get_json()
    patient_id   = data.get('patient_id')
    ordered_drug = data.get('ordered_drug', '').strip()
    ordered_dose = int(data.get('ordered_dose', 0))

    conn    = get_db()
    patient = db_execute(conn,
        'SELECT * FROM patients WHERE patient_id = ?', (patient_id,), fetchone=True)

    if not patient:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Patient not found'})

    drug_info = db_execute(conn,
        'SELECT * FROM patients WHERE LOWER(current_drug) = LOWER(?) LIMIT 1',
        (ordered_drug,), fetchone=True)
    if not drug_info:
        drug_info = db_execute(conn,
            'SELECT * FROM drugs WHERE LOWER(drug_name) = LOWER(?) LIMIT 1',
            (ordered_drug,), fetchone=True)

    if not drug_info:
        conn.close()
        return jsonify({
            'status' : 'warning',
            'message': f'⚠️ Drug "{ordered_drug}" not found in database.',
            'alerts' : [{'type': '⚠️ UNKNOWN DRUG',
                         'message': f'Cannot verify safety of "{ordered_drug}". Check spelling or add via Add Drug page.'}]
        })

    alerts      = []
    alert_level = 'safe'

    # Rule 1: Dose limit
    if ordered_dose > drug_info['max_safe_dose']:
        alerts.append({'type': '🚨 DOSE EXCEEDED',
                       'message': f"Max safe dose is {drug_info['max_safe_dose']}mg. You ordered {ordered_dose}mg!"})
        alert_level = 'danger'

    # Rule 2: Allergy
    if drug_info['allergy_class'] and patient['allergy_class']:
        if drug_info['allergy_class'].lower() == patient['allergy_class'].lower() \
                and ordered_drug.lower() != patient['current_drug'].lower():
            alerts.append({'type': '🚨 ALLERGY ALERT',
                           'message': f"Patient sensitive to {patient['allergy_class']} class. {ordered_drug} is same class!"})
            alert_level = 'danger'

    # Rule 3: Interaction
    interactions = [i.strip().lower() for i in drug_info['interacts_with'].split('|')]
    if patient['current_drug'].strip().lower() in interactions:
        alerts.append({'type': '⚠️ DRUG INTERACTION',
                       'message': f"{ordered_drug} interacts with {patient['current_drug']}. {drug_info['clinical_warning']}"})
        if alert_level != 'danger': alert_level = 'warning'

    # Rule 4: Elderly
    risky_elderly = ['ibuprofen','tramadol','ciprofloxacin','glipizide','metoprolol','amlodipine']
    if patient['age'] > 65 and ordered_drug.lower() in risky_elderly:
        alerts.append({'type': '⚠️ ELDERLY RISK',
                       'message': f"Patient is {patient['age']} yrs. {ordered_drug} has higher risk for 65+ patients."})
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
    db_execute(conn,
        'INSERT INTO orders (patient_id, ordered_drug, ordered_dose, status) VALUES (?, ?, ?, ?)',
        (patient_id, ordered_drug, ordered_dose, status))
    for alert in alerts:
        db_execute(conn,
            'INSERT INTO alerts (patient_id, ordered_drug, alert_type, alert_message) VALUES (?, ?, ?, ?)',
            (patient_id, ordered_drug, alert['type'], alert['message']))
    conn.commit()
    conn.close()

    if alert_level == 'safe':
        return jsonify({'status': 'safe',
                        'message': f'✅ Order APPROVED — {ordered_drug} {ordered_dose}mg is safe.',
                        'alerts': []})
    else:
        return jsonify({'status': alert_level,
                        'message': f'Order flagged — {len(alerts)} issue(s) found.',
                        'alerts': alerts})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)