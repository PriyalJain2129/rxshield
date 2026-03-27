# app.py - RxShield (Stable & Safe Version for Railway)

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

app.config['SESSION_COOKIE_SECURE']   = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_NAME']     = 'rxshield_session'

from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

from dotenv import load_dotenv
load_dotenv()
SENDER_EMAIL    = os.getenv('SENDER_EMAIL', '')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', '')

conn_global = None

# ====================== EMAIL ======================
def send_welcome_email(to_email, name, role):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Welcome to RxShield!'
        msg['From'] = f'RxShield <{SENDER_EMAIL}>'
        msg['To'] = to_email
        html = f"<h2>Welcome, {name}!</h2><p>Account created successfully as {role}.</p>"
        msg.attach(MIMEText(html, 'html'))
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=5)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Email failed: {e}")

def send_welcome_email_async(to_email, name, role):
    threading.Thread(target=send_welcome_email, args=(to_email, name, role), daemon=True).start()

# ====================== DATABASE ======================
DATABASE_URL = os.getenv('DATABASE_URL', '').strip()
USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

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

    if USE_POSTGRES:
        conn_global = psycopg2.connect(DATABASE_URL, connect_timeout=15, sslmode='require')
        conn_global.autocommit = True
        print("✅ Connected to Supabase")
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

# ====================== INIT DB ======================
def init_db():
    conn = get_db()
    cur = conn.cursor()

    # Create tables (Postgres version)
    if USE_POSTGRES:
        cur.execute('''CREATE TABLE IF NOT EXISTS users (user_id SERIAL PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL, role TEXT DEFAULT 'Doctor', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS patients (patient_id TEXT PRIMARY KEY, age INTEGER, gender TEXT, condition TEXT, current_drug TEXT, dosage_mg INTEGER, side_effects TEXT, allergy_class TEXT, max_safe_dose INTEGER, interacts_with TEXT, clinical_warning TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS drugs (drug_id SERIAL PRIMARY KEY, drug_name TEXT UNIQUE, allergy_class TEXT, max_safe_dose INTEGER, interacts_with TEXT, clinical_warning TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS orders (order_id SERIAL PRIMARY KEY, patient_id TEXT, ordered_drug TEXT, ordered_dose INTEGER, status TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS alerts (alert_id SERIAL PRIMARY KEY, patient_id TEXT, ordered_drug TEXT, alert_type TEXT, alert_message TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    else:
        # SQLite version (keep your original if you prefer)
        pass  # add your SQLite CREATE statements if needed

    # Load patients CSV
    cur.execute('SELECT COUNT(*) FROM patients')
    count = cur.fetchone()[0] if not USE_POSTGRES else list(cur.fetchone().values())[0]
    if count == 0:
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'real_drug_dataset_updated.csv')
        if os.path.exists(csv_path):
            with open(csv_path, encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                rows = [(row['Patient_ID'], int(row['Age']), row['Gender'], row['Condition'], row['Drug_Name'],
                         int(row['Dosage_mg']), row['Side_Effects'], row['Allergy_Class'],
                         int(row['Max_Safe_Dose_mg']), row['Interacts_With'], row['Clinical_Warning']) for row in reader]
            ph = ','.join(['%s']*11) if USE_POSTGRES else ','.join(['?']*11)
            cur.executemany(f'INSERT INTO patients VALUES ({ph})', rows)
            print(f"✅ Loaded {len(rows)} patients")
    conn.commit()
    print("✅ Database ready")

try:
    init_db()
except Exception as e:
    print(f"DB Init Warning: {e}")

# ====================== ROUTES ======================

@app.route('/')
def home():
    if not is_logged_in(): return redirect(url_for('login_page'))
    try:
        conn = get_db()
        patients = db_execute(conn, 'SELECT patient_id, age, gender, condition, current_drug, allergy_class FROM patients', fetchall=True)
        drugs = db_execute(conn, 'SELECT DISTINCT current_drug FROM patients ORDER BY current_drug', fetchall=True)
        all_drugs = sorted(set([d['current_drug'] for d in drugs if d.get('current_drug')]))
        return render_template('index.html', patients=patients, drugs=all_drugs, page='home')
    except Exception as e:
        print("Home error:", e)
        return "Error loading dashboard", 500

@app.route('/patients')
def patients_page():
    if not is_logged_in(): return redirect(url_for('login_page'))
    try:
        conn = get_db()
        patients = db_execute(conn, 'SELECT * FROM patients', fetchall=True)
        return render_template('patients.html', patients=patients, page='patients')
    except Exception as e:
        print("Patients error:", e)
        return "Error loading patients", 500

@app.route('/alerts')
def alerts_page():
    if not is_logged_in(): return redirect(url_for('login_page'))
    try:
        conn = get_db()
        alerts = db_execute(conn, 'SELECT * FROM alerts ORDER BY timestamp DESC', fetchall=True)
        return render_template('alerts.html', alerts=alerts, page='alerts')
    except Exception as e:
        print("Alerts error:", e)
        return "Error loading alerts", 500

@app.route('/orders')
def orders_page():
    if not is_logged_in(): return redirect(url_for('login_page'))
    try:
        conn = get_db()
        orders = db_execute(conn, 'SELECT * FROM orders ORDER BY timestamp DESC', fetchall=True)
        return render_template('orders.html', orders=orders, page='orders')
    except Exception as e:
        print("Orders error:", e)
        return "Error loading orders", 500

# Order Entry Page - FIXED (Drug list + Patient list)
@app.route('/order-entry')
def order_entry_page():
    if not is_logged_in(): return redirect(url_for('login_page'))
    try:
        conn = get_db()
        patients = db_execute(conn, 'SELECT patient_id, age, gender, condition, current_drug FROM patients', fetchall=True)
        drugs = db_execute(conn, 'SELECT DISTINCT current_drug FROM patients ORDER BY current_drug', fetchall=True)
        all_drugs = sorted(set([d['current_drug'] for d in drugs if d.get('current_drug')]))
        
        return render_template('order_entry.html', patients=patients, drugs=all_drugs)
    except Exception as e:
        print("Order Entry error:", e)
        return "Error loading order entry", 500

# Keep your existing /api/signup, /api/login, /check-order, /save-patient etc. routes as they were.

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)