import numpy as np
from scipy.signal import correlate
from modules.database import save_cir_to_db, load_cir_from_db

def generate_cir(num_paths=5, noise_level=0.05):
    """Simulate a multipath CIR with random delays, gains, and noise."""
    delays = np.sort(np.random.uniform(0, 1e-3, num_paths))
    gains = np.random.randn(num_paths)
    impulse_response = np.zeros(100)
    for delay, gain in zip(delays, gains):
        index = int(delay * 1e6)
        impulse_response[index] += gain
    # Add noise
    noise = np.random.normal(0, noise_level, impulse_response.shape)
    return impulse_response + noise

def authenticate_node(node_id, received_cir):
    """Authenticate using stored CIR data."""
    stored_cir = load_cir_from_db(node_id)
    if stored_cir is None:
        return False
    correlation = correlate(stored_cir, received_cir)
    score = max(abs(correlation))
    return score >= 0.75  # Threshold can be adjusted dynamically
