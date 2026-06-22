"""
One-time migration: adds new columns to existing tables.
Safe to run multiple times (checks if column already exists before adding).
"""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "instance", "diu_wise.db")

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH} — will be created fresh on first run, no migration needed.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ── users table: faculty advisor alert columns ─────────────────────────
    new_user_cols = [
        ("faculty_advisor_email",  "TEXT"),
        ("advisor_alert_consent",  "INTEGER NOT NULL DEFAULT 0"),
        ("advisor_alert_sent_at",  "DATETIME"),
    ]
    for col, col_type in new_user_cols:
        if not column_exists(cur, "users", col):
            cur.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
            print(f"  + users.{col}")
        else:
            print(f"  ✓ users.{col} already exists")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
