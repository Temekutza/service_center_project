from database.db import get_connection

def add_device(client_id, device_type, brand, model):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO devices (client_id, device_type, brand, model) VALUES (?, ?, ?, ?)",
        (client_id, device_type, brand, model)
    )
    conn.commit()
    conn.close()

def get_devices():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT devices.id, clients.name, device_type, brand, model
        FROM devices
        JOIN clients ON devices.client_id = clients.id
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows
