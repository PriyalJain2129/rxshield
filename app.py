# app.py - RxShield CPOE System (Stable Version for Railway)

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

# Production session config
app.config['SESSION_COOKIE_SECURE']   = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_NAME']     = 'rxshield_session'

from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Email config
from dotenv import load_dotenv
load_dotenv()
SENDER_EMAIL    = os.getenv('SENDER_EMAIL', '')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', '')

# Global DB Connection
conn_global = None

# ── Send Welcome Email ─────────────────────────────────
def send_welcome_email(to_email, name, role):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = '👋 Welcome to RxShield!'
        msg['From']    = f'RxShield <{SENDER_EMAIL}>'
        msg['To']      = to_email

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background:#EAF7FB; padding:20px;">
            <h2>Welcome aboard, {name}! 👋</h2>
            <p>Your account has been successfully created.</p>
            <p><strong>Role:</strong> {role}</p>
            <p>Thank you for joining RxShield - Smart Prescription Safety System.</p>
        </body>
        </html>
        """

        msg.attach(MIMEText(html, 'html'))

        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=5)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        print(f"✅ Welcome email sent to {to_email}")
    except Exception as e:
        print(f"⚠️ Email failed: {e}")

def send_welcome_email_async(to_email, name, role):
    thread = threading.Thread(target=send_welcome_email, args=(to_email, name, role))
    thread.daemon = True
    thread.start()

# ── Database Setup ─────────────────────────────────────
DATABASE_URL = os.getenv('DATABASE_URL', '').strip()
USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Robust Global DB Connection
def get_db():
    global conn_global

    if conn_global is not None:
        try:
            if USE_POSTGRES:
                conn_global.cursor().execute("SELECT 1")
            else:
                conn_global.execute("SELECT 1")
            return conn_global
        except:
            conn_global = None

    print("🔌 Connecting to database...")

    if USE_POSTGRES:
        try:
            conn_global = psycopg2.connect(
                DATABASE_URL,
                connect_timeout=15,
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5,
                sslmode='require'
            )
            conn_global.autocommit = True
            print("✅ Connected to Supabase PostgreSQL")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise
    else:
        DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hospital.db')
        conn_global = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn_global.row_factory = sqlite3.Row
        print("✅ Connected to SQLite")

    return conn_global

def db_execute(conn, query, params=(), fetchone=False, fetchall=False):
    if USE_POSTGRES:
        query = query.replace('?', '%s')
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        cur = conn.cursor()

    cur.execute(query, params)

    if fetchone:
        row = cur.fetchone()
        return dict(row) if USE_POSTGRES and row else row
    if fetchall:
        rows = cur.fetchall()
        return [dict(r) for r in rows] if USE_POSTGRES else rows
    return cur

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def is_logged_in():
    return 'user_id' in session

def get_current_user():
    if not is_logged_in():
        return None
    conn = get_db()
    user = db_execute(conn, 'SELECT * FROM users WHERE user_id = ?', (session['user_id'],), fetchone=True)
    return user

# ── Init Database ─────────────────────────────────────
def init_db():
    conn = get_db()
    cur = conn.cursor()

    if USE_POSTGRES:
        cur.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL, role TEXT DEFAULT 'Doctor',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS patients (
            patient_id TEXT PRIMARY KEY, age INTEGER, gender TEXT, condition TEXT,
            current_drug TEXT, dosage_mg INTEGER, side_effects TEXT, allergy_class TEXT,
            max_safe_dose INTEGER, interacts_with TEXT, clinical_warning TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS drugs (
            drug_id SERIAL PRIMARY KEY, drug_name TEXT UNIQUE, allergy_class TEXT,
            max_safe_dose INTEGER, interacts_with TEXT, clinical_warning TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS orders (
            order_id SERIAL PRIMARY KEY, patient_id TEXT, ordered_drug TEXT,
            ordered_dose INTEGER, status TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS alerts (
            alert_id SERIAL PRIMARY KEY, patient_id TEXT, ordered_drug TEXT,
            alert_type TEXT, alert_message TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    else:
        cur.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL, role TEXT DEFAULT 'Doctor', created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS patients (
            patient_id TEXT PRIMARY KEY, age INTEGER, gender TEXT, condition TEXT,
            current_drug TEXT, dosage_mg INTEGER, side_effects TEXT, allergy_class TEXT,
            max_safe_dose INTEGER, interacts_with TEXT, clinical_warning TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS drugs (
            drug_id INTEGER PRIMARY KEY AUTOINCREMENT, drug_name TEXT UNIQUE, allergy_class TEXT,
            max_safe_dose INTEGER, interacts_with TEXT, clinical_warning TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id TEXT, ordered_drug TEXT,
            ordered_dose INTEGER, status TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS alerts (
            alert_id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id TEXT, ordered_drug TEXT,
            alert_type TEXT, alert_message TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    # Load CSV if patients table is empty
    cur.execute('SELECT COUNT(*) FROM patients')
    count = cur.fetchone()
    count = count[0] if isinstance(count, tuple) else (list(count.values())[0] if count else 0)

    if count == 0:
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'real_drug_dataset_updated.csv')
        if os.path.exists(csv_path):
            with open(csv_path, encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                rows = [(row['Patient_ID'], int(row['Age']), row['Gender'], row['Condition'], 
                        row['Drug_Name'], int(row['Dosage_mg']), row['Side_Effects'], 
                        row['Allergy_Class'], int(row['Max_Safe_Dose_mg']), row['Interacts_With'], 
                        row['Clinical_Warning']) for row in reader]
            ph = ','.join(['%s'] * 11) if USE_POSTGRES else ','.join(['?'] * 11)
            cur.executemany(f'INSERT INTO patients VALUES ({ph})', rows)
            print(f"✅ Loaded {len(rows)} patients into DB")

    conn.commit()
    print("✅ Database ready")

# Run init on startup with error handling
try:
    init_db()
except Exception as e:
    print(f"⚠️ Database initialization warning: {e}")

# ── Auth Routes ─────────────────────────────────────
@app.route('/api/signup', methods=['POST'])
def signup():
    print("SIGNUP HIT:", request.get_json().get('email') if request.get_json() else None)
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    role = data.get('role', 'Doctor')

    if not name or not email or not password:
        return jsonify({'status': 'error', 'message': 'All fields are required.'}), 400
    if len(password) < 6:
        return jsonify({'status': 'error', 'message': 'Password must be at least 6 characters.'}), 400

    conn = get_db()
    try:
        existing = db_execute(conn, 'SELECT * FROM users WHERE email = ?', (email,), fetchone=True)
        if existing:
            return jsonify({'status': 'error', 'message': 'An account with this email already exists.'}), 400

        hashed = hash_password(password)
        db_execute(conn, 'INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
                   (name, email, hashed, role))
        conn.commit()

        user = db_execute(conn, 'SELECT * FROM users WHERE email = ?', (email,), fetchone=True)
        session['user_id'] = user['user_id']
        session['user_name'] = user['name']
        session['user_role'] = user['role']

        send_welcome_email_async(email, name, role)
        return jsonify({'status': 'success', 'message': 'Account created successfully!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'status': 'error', 'message': 'Email and password are required.'}), 400

    conn = get_db()
    hashed = hash_password(password)
    user = db_execute(conn, 'SELECT * FROM users WHERE email = ? AND password = ?',
                      (email, hashed), fetchone=True)

    if not user:
        return jsonify({'status': 'error', 'message': 'Invalid email or password.'}), 400

    session['user_id'] = user['user_id']
    session['user_name'] = user['name']
    session['user_role'] = user['role']
    return jsonify({'status': 'success', 'message': f'Welcome back, {user["name"]}!'})

# Protected Pages with better error handling
@app.route('/')
def home():
    if not is_logged_in():
        return redirect(url_for('login_page'))
    try:
        conn = get_db()
        patients = db_execute(conn, 'SELECT patient_id, age, gender, condition, current_drug, allergy_class FROM patients', fetchall=True)
        patients = [dict(p) if not isinstance(p, dict) else p for p in patients]
        return render_template('index.html', patients=patients, page='home')
    except Exception as e:
        print(f"Home page error: {e}")
        return "Error loading dashboard", 500

@app.route('/patients')
def patients_page():
    if not is_logged_in():
        return redirect(url_for('login_page'))
    try:
        conn = get_db()
        patients = db_execute(conn, 'SELECT * FROM patients', fetchall=True)
        patients = [dict(p) if not isinstance(p, dict) else p for p in patients]
        return render_template('patients.html', patients=patients, page='patients')
    except Exception as e:
        print(f"Patients page error: {e}")
        return f"Error loading patients: {str(e)}", 500

@app.route('/alerts')
def alerts_page():
    if not is_logged_in():
        return redirect(url_for('login_page'))
    try:
        conn = get_db()
        alerts = db_execute(conn, 'SELECT * FROM alerts ORDER BY timestamp DESC', fetchall=True)
        alerts = [dict(a) if not isinstance(a, dict) else a for a in alerts]
        return render_template('alerts.html', alerts=alerts, page='alerts')
    except Exception as e:
        print(f"Alerts page error: {e}")
        return f"Error loading alerts: {str(e)}", 500

@app.route('/orders')
def orders_page():
    if not is_logged_in():
        return redirect(url_for('login_page'))
    try:
        conn = get_db()
        orders = db_execute(conn, 'SELECT * FROM orders ORDER BY timestamp DESC', fetchall=True)
        orders = [dict(o) if not isinstance(o, dict) else o for o in orders]
        return render_template('orders.html', orders=orders, page='orders')
    except Exception as e:
        print(f"Orders page error: {e}")
        return f"Error loading orders: {str(e)}", 500

# Keep your other routes (add-patient, save-patient, check-order, etc.) as they were before.
# For brevity, I'm not repeating all of them here. You can keep them from your previous version.

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)