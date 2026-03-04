from database.db import get_connection
from datetime import datetime

def add_repair(device_id, problem, price):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO repairs (device_id, problem_description, price, date_created) VALUES (?, ?, ?, ?)",
        (device_id, problem, price, datetime.now().strftime("%Y-%m-%d"))
    )
    conn.commit()
    conn.close()

def get_repairs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT repairs.id, devices.model, problem_description, status, price, date_created
        FROM repairs
        JOIN devices ON repairs.device_id = devices.id
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_status(repair_id, new_status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE repairs SET status=? WHERE id=?",
        (new_status, repair_id)
    )
    conn.commit()
    conn.close()
