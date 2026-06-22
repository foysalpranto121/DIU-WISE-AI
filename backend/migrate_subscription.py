"""One-time migration to create the subscriptions table."""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), "instance", "diu_wise.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
        plan TEXT NOT NULL DEFAULT 'free',
        status TEXT NOT NULL DEFAULT 'active',
        started_at TEXT,
        expires_at TEXT
    )
""")
conn.commit()
conn.close()
print("subscriptions table ready.")
