# app.py - Full CPOE System with Authentication + All Features

from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import sqlite3
import hashlib
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = 'cpoe_secret_key_rknec_2024'

# ── Email config — fill these in ─────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

SENDER_EMAIL    = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')

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
                                            <a href="http://127.0.0.1:5000"
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

# ── Helper: connect to database ───────────────────────────────────
def get_db():
    conn = sqlite3.connect('hospital.db')
    conn.row_factory = sqlite3.Row
    return conn

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
    user = conn.execute(
        'SELECT * FROM users WHERE user_id = ?', (session['user_id'],)
    ).fetchone()
    conn.close()
    return user

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
    existing = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    if existing:
        conn.close()
        return jsonify({'status': 'error', 'message': 'An account with this email already exists.'})

    hashed = hash_password(password)
    conn.execute(
        'INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
        (name, email, hashed, role)
    )
    conn.commit()

    # Auto login after signup
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    session['user_id']   = user['user_id']
    session['user_name'] = user['name']
    session['user_role'] = user['role']
    conn.close()

    # Send welcome email in background
    send_welcome_email(email, name, role)

    return jsonify({'status': 'success', 'message': f'Welcome, {name}!'})

@app.route('/api/login', methods=['POST'])
def login():
    data     = request.get_json()
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'status': 'error', 'message': 'Email and password are required.'})

    conn   = get_db()
    hashed = hash_password(password)
    user   = conn.execute(
        'SELECT * FROM users WHERE email = ? AND password = ?', (email, hashed)
    ).fetchone()
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
    order_count = conn.execute(
        'SELECT COUNT(*) FROM orders', ()
    ).fetchone()[0]
    alert_count = conn.execute(
        'SELECT COUNT(*) FROM alerts', ()
    ).fetchone()[0]
    conn.close()
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
        [row['current_drug'] for row in drugs_from_patients] +
        [row['drug_name']    for row in drugs_from_table]
    ))
    # Dashboard stats
    total_patients = conn.execute('SELECT COUNT(*) FROM patients').fetchone()[0]
    total_orders   = conn.execute('SELECT COUNT(*) FROM orders').fetchone()[0]
    total_alerts   = conn.execute('SELECT COUNT(*) FROM alerts').fetchone()[0]
    approved       = conn.execute("SELECT COUNT(*) FROM orders WHERE status='APPROVED'").fetchone()[0]
    conn.close()
    return render_template('index.html',
                           patients=patients,
                           drugs=all_drugs,
                           total_patients=total_patients,
                           total_orders=total_orders,
                           total_alerts=total_alerts,
                           approved=approved,
                           page='home')

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
    if not is_logged_in():
        return jsonify({'status': 'error', 'message': 'Not logged in'})
    data = request.get_json()
    conn = get_db()
    count  = conn.execute('SELECT COUNT(*) FROM patients').fetchone()[0]
    new_id = f"P{str(count + 1).zfill(4)}"
    try:
        conn.execute('''
            INSERT INTO patients
            (patient_id, age, gender, condition, current_drug, dosage_mg,
             side_effects, allergy_class, max_safe_dose, interacts_with, clinical_warning)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            new_id, int(data['age']), data['gender'], data['condition'],
            data['current_drug'], int(data['dosage_mg']),
            data.get('side_effects', 'None'), data['allergy_class'],
            int(data['max_safe_dose']), data['interacts_with'],
            data.get('clinical_warning', 'None')
        ))
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
        conn.execute('''
            INSERT INTO drugs (drug_name, allergy_class, max_safe_dose, interacts_with, clinical_warning)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['drug_name'], data['allergy_class'], int(data['max_safe_dose']),
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
    patient = conn.execute(
        'SELECT * FROM patients WHERE patient_id = ?', (patient_id,)
    ).fetchone()

    if not patient:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Patient not found'})

    drug_info = conn.execute(
        'SELECT * FROM patients WHERE LOWER(current_drug) = LOWER(?) LIMIT 1',
        (ordered_drug,)
    ).fetchone()
    if not drug_info:
        drug_info = conn.execute(
            'SELECT * FROM drugs WHERE LOWER(drug_name) = LOWER(?) LIMIT 1',
            (ordered_drug,)
        ).fetchone()

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
    conn.execute(
        'INSERT INTO orders (patient_id, ordered_drug, ordered_dose, status) VALUES (?, ?, ?, ?)',
        (patient_id, ordered_drug, ordered_dose, status)
    )
    for alert in alerts:
        conn.execute(
            'INSERT INTO alerts (patient_id, ordered_drug, alert_type, alert_message) VALUES (?, ?, ?, ?)',
            (patient_id, ordered_drug, alert['type'], alert['message'])
        )
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
    app.run(debug=True)