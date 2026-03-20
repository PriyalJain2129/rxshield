# database.py - Run this once to set up your database
# Now includes users table for authentication

import sqlite3
import csv

conn   = sqlite3.connect('hospital.db')
cursor = conn.cursor()

# ── Users table (for login/signup) ───────────────────────────────
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        name       TEXT NOT NULL,
        email      TEXT UNIQUE NOT NULL,
        password   TEXT NOT NULL,
        role       TEXT DEFAULT 'Doctor',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

# ── Patients table ────────────────────────────────────────────────
cursor.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        patient_id       TEXT PRIMARY KEY,
        age              INTEGER,
        gender           TEXT,
        condition        TEXT,
        current_drug     TEXT,
        dosage_mg        INTEGER,
        side_effects     TEXT,
        allergy_class    TEXT,
        max_safe_dose    INTEGER,
        interacts_with   TEXT,
        clinical_warning TEXT
    )
''')

# ── Drugs table ───────────────────────────────────────────────────
cursor.execute('''
    CREATE TABLE IF NOT EXISTS drugs (
        drug_id          INTEGER PRIMARY KEY AUTOINCREMENT,
        drug_name        TEXT UNIQUE,
        allergy_class    TEXT,
        max_safe_dose    INTEGER,
        interacts_with   TEXT,
        clinical_warning TEXT
    )
''')

# ── Orders table ──────────────────────────────────────────────────
cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        order_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id   TEXT,
        ordered_drug TEXT,
        ordered_dose INTEGER,
        status       TEXT,
        timestamp    DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

# ── Alerts table ──────────────────────────────────────────────────
cursor.execute('''
    CREATE TABLE IF NOT EXISTS alerts (
        alert_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id    TEXT,
        ordered_drug  TEXT,
        alert_type    TEXT,
        alert_message TEXT,
        timestamp     DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

# ── Load CSV into patients (only if empty) ────────────────────────
cursor.execute('SELECT COUNT(*) FROM patients')
if cursor.fetchone()[0] == 0:
    print("Loading patient data from CSV...")
    with open('real_drug_dataset_updated.csv', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute('''
                INSERT INTO patients VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['Patient_ID'], int(row['Age']), row['Gender'],
                row['Condition'], row['Drug_Name'], int(row['Dosage_mg']),
                row['Side_Effects'], row['Allergy_Class'],
                int(row['Max_Safe_Dose_mg']), row['Interacts_With'],
                row['Clinical_Warning']
            ))
    print("✅ 1000 patients loaded!")
else:
    print("✅ Patients already loaded.")

conn.commit()
conn.close()
print("✅ Database ready — hospital.db")