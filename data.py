import sqlite3
import numpy as np

# Define function to generate simulated CIR data
def generate_cir_data(num_paths=5, length=100):
    """Generate random CIR data to simulate a multi-path environment."""
    delays = np.sort(np.random.uniform(0, 1e-3, num_paths))
    gains = np.random.randn(num_paths)
    impulse_response = np.zeros(length)
    for delay, gain in zip(delays, gains):
        index = int(delay * 1e6)  # Convert delay to an index based on sample rate
        if index < length:
            impulse_response[index] += gain
    return impulse_response

# Connect to SQLite database (or create if it doesn't exist)
conn = sqlite3.connect('C:/Coding/fyp/UWSN_Simulation/data/cir_database.db')
c = conn.cursor()

# Create table for CIR data
c.execute('''
    CREATE TABLE IF NOT EXISTS cir_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        node_id TEXT,
        cir BLOB
    )
''')

# Generate and populate CIR data for multiple nodes
def populate_cir_database(num_nodes=10):
    for i in range(num_nodes):
        node_id = f"node_{i+1}"
        cir_data = generate_cir_data()
        # Convert CIR data to binary for storage
        cir_blob = cir_data.tobytes()
        
        # Insert the node's CIR data into the database
        c.execute("INSERT INTO cir_data (node_id, cir) VALUES (?, ?)", (node_id, cir_blob))
        print(f"Inserted CIR data for {node_id}")

# Populate the database with CIR data
populate_cir_database(num_nodes=10)

# Commit the changes and close the connection
conn.commit()
conn.close()
