import sqlite3

DB_NAME = "service_center.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_connection()
    with open("database/schema.sql", "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.close()
