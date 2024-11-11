import random

class Node:
    def __init__(self, node_id, is_malicious=False, processing_power=1e6, energy=100):
        self.node_id = node_id
        self.is_malicious = is_malicious
        self.processing_power = processing_power  # in FLOPS
        self.energy = energy  # Energy budget in arbitrary units
        self.cir = None

    def consume_energy(self, amount):
        """Reduces the node's energy budget."""
        self.energy -= amount
        if self.energy <= 0:
            print(f"Node {self.node_id} is out of energy and shutting down.")
            return False
        return True

    def process_task(self, flops_required):
        """Simulate task processing with computational constraints."""
        if flops_required / self.processing_power > 1:
            print(f"Node {self.node_id} is taking longer due to limited processing power.")
        return self.consume_energy(flops_required * 0.01)  # Assume energy cost per FLOP
