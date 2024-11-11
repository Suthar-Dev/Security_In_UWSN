import numpy as np
import random
import time

def simulate_latency(distance=1000, bandwidth=1000):
    """
    Simulate underwater communication latency.
    - distance: distance between nodes in meters
    - bandwidth: channel bandwidth in bps
    """
    speed_of_sound = 1500  # Speed of sound in water (m/s)
    propagation_delay = distance / speed_of_sound  # Time for signal to travel
    transmission_delay = random.uniform(0.05, 0.1) / bandwidth  # Bandwidth constraint
    total_delay = propagation_delay + transmission_delay
    time.sleep(total_delay)  # Simulate the delay
    return total_delay
