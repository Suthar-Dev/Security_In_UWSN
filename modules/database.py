import sqlite3
import numpy as np

conn = sqlite3.connect('data/cir_database.db')
c = conn.cursor()

def save_cir_to_db(node_id, cir):
    cir_blob = np.array(cir).tobytes()
    c.execute("INSERT INTO cir_data (node_id, cir) VALUES (?, ?)", (node_id, cir_blob))
    conn.commit()

def load_cir_from_db(node_id):
    c.execute("SELECT cir FROM cir_data WHERE node_id = ?", (node_id,))
    result = c.fetchone()
    return np.frombuffer(result[0], dtype=float) if result else None
