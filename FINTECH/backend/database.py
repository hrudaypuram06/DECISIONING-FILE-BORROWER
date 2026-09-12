import sqlite3
import json
import hashlib
from datetime import datetime

DB_FILE = "credifair.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Rules table
    c.execute('''
        CREATE TABLE IF NOT EXISTS rules (
            version INTEGER PRIMARY KEY AUTOINCREMENT,
            risk_threshold REAL,
            min_income REAL,
            watchlist_enabled BOOLEAN,
            created_at TEXT
        )
    ''')
    
    # Insert default rule if empty
    c.execute("SELECT COUNT(*) FROM rules")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO rules (risk_threshold, min_income, watchlist_enabled, created_at) VALUES (?, ?, ?, ?)",
                  (0.40, 15000.0, True, datetime.now().isoformat()))
        
    # Decisions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS decisions (
            application_id TEXT PRIMARY KEY,
            applicant_name TEXT,
            input_data TEXT,
            model_version TEXT,
            rule_version INTEGER,
            risk_score REAL,
            risk_prob REAL,
            decision TEXT,
            reasons TEXT,
            watchlist_result TEXT,
            timestamp TEXT,
            hash TEXT
        )
    ''')

    # Cryptographic Hash Chain Audit Logs
    c.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id TEXT,
            decision TEXT,
            version_info TEXT,
            hash TEXT,
            prev_hash TEXT,
            timestamp TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

    # Seed initial data if empty
    seed_initial_data()

def seed_initial_data():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM decisions")
    if c.fetchone()[0] == 0:
        conn.close()
        sample_applicants = [
            {"app_id": "APP-52425", "name": "Rahul Sharma", "income": 45000, "expense": 18000, "rent": 95, "util": 90, "telecom": 92, "cf": 0.85, "gig": 15000, "rating": 4.8, "decision": "APPROVE", "score": 92, "prob": 0.08, "watchlist": "CLEAR"},
            {"app_id": "APP-52426", "name": "Priya Verma", "income": 28000, "expense": 14000, "rent": 88, "util": 85, "telecom": 87, "cf": 0.70, "gig": 8000, "rating": 4.5, "decision": "APPROVE", "score": 85, "prob": 0.15, "watchlist": "CLEAR"},
            {"app_id": "APP-52427", "name": "Amit Kumar", "income": 12000, "expense": 11000, "rent": 65, "util": 60, "telecom": 70, "cf": 0.40, "gig": 2000, "rating": 3.2, "decision": "REJECT", "score": 35, "prob": 0.65, "watchlist": "CLEAR"},
            {"app_id": "APP-52428", "name": "Sneha Patel", "income": 65000, "expense": 25000, "rent": 98, "util": 95, "telecom": 96, "cf": 0.92, "gig": 22000, "rating": 4.9, "decision": "APPROVE", "score": 96, "prob": 0.04, "watchlist": "CLEAR"},
            {"app_id": "APP-52429", "name": "SANCTIONS_USER_01", "income": 50000, "expense": 20000, "rent": 90, "util": 90, "telecom": 90, "cf": 0.80, "gig": 10000, "rating": 4.0, "decision": "REJECT", "score": 40, "prob": 0.60, "watchlist": "MATCH (FLAGGED)"}
        ]
        for app in sample_applicants:
            input_data = {
                "applicant_name": app["name"],
                "monthly_income": app["income"],
                "monthly_expense": app["expense"],
                "rent_payment_ratio": app["rent"],
                "utility_payment_ratio": app["util"],
                "telecom_payment_ratio": app["telecom"],
                "cash_flow_stability": app["cf"],
                "gig_income": app["gig"],
                "platform_rating": app["rating"]
            }
            reasons = ["Satisfactory credit profile."] if app["decision"] == "APPROVE" else ["High default risk probability / Regulatory flag."]
            save_decision(
                app_id=app["app_id"],
                applicant_name=app["name"],
                input_data=input_data,
                model_version="v1.2.0",
                rule_version=1,
                risk_score=app["score"],
                risk_prob=app["prob"],
                decision=app["decision"],
                reasons=reasons,
                watchlist_result=app["watchlist"]
            )
    else:
        conn.close()

def get_current_rule():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT version, risk_threshold, min_income, watchlist_enabled FROM rules ORDER BY version DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    if row:
        return {"version": row[0], "risk_threshold": row[1], "min_income": row[2], "watchlist_enabled": bool(row[3])}
    return {"version": 1, "risk_threshold": 0.40, "min_income": 15000.0, "watchlist_enabled": True}

def get_all_rules():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM rules ORDER BY version DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(ix) for ix in rows]

def update_rule(risk_threshold, min_income, watchlist_enabled):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO rules (risk_threshold, min_income, watchlist_enabled, created_at) VALUES (?, ?, ?, ?)",
              (risk_threshold, min_income, watchlist_enabled, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return get_current_rule()

def get_last_hash():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT hash FROM audit_logs ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    return row[0] if row else "0000000000000000000000000000000000000000000000000000000000000000"

def save_decision(app_id, applicant_name, input_data, model_version, rule_version, risk_score, risk_prob, decision, reasons, watchlist_result):
    timestamp = datetime.now().isoformat()
    prev_hash = get_last_hash()
    
    record_string = f"{app_id}|{json.dumps(input_data, sort_keys=True)}|{model_version}|{rule_version}|{risk_score}|{decision}|{json.dumps(reasons)}|{watchlist_result}|{timestamp}|{prev_hash}"
    record_hash = hashlib.sha256(record_string.encode('utf-8')).hexdigest()
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO decisions (application_id, applicant_name, input_data, model_version, rule_version, risk_score, risk_prob, decision, reasons, watchlist_result, timestamp, hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (app_id, applicant_name, json.dumps(input_data), model_version, rule_version, risk_score, risk_prob, decision, json.dumps(reasons), watchlist_result, timestamp, record_hash))
    
    c.execute('''
        INSERT INTO audit_logs (application_id, decision, version_info, hash, prev_hash, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (app_id, decision, f"M:{model_version} R:{rule_version}", record_hash, prev_hash, timestamp))
    
    conn.commit()
    conn.close()
    return record_hash

def get_decision(app_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM decisions WHERE application_id = ?", (app_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "application_id": row[0],
            "applicant_name": row[1],
            "input_data": json.loads(row[2]),
            "model_version": row[3],
            "rule_version": row[4],
            "risk_score": row[5],
            "risk_prob": row[6],
            "decision": row[7],
            "reasons": json.loads(row[8]),
            "watchlist_result": row[9],
            "timestamp": row[10],
            "hash": row[11]
        }
    return None

def get_all_decisions():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM decisions ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()
    result = []
    for r in rows:
        item = dict(r)
        item['input_data'] = json.loads(item['input_data'])
        item['reasons'] = json.loads(item['reasons'])
        result.append(item)
    return result

def get_all_audit_logs():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM audit_logs ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()
    return [dict(ix) for ix in rows]
