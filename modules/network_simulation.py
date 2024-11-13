from modules.constraints import Node
from modules.cir import authenticate_node
from modules.puf import authenticate_puf
from modules.visualization import NetworkVisualizer
from modules.communication import simulate_latency
import random

class Network:
    def __init__(self):
        self.nodes = []

    def add_node(self, node):
        self.nodes.append(node)

    def authenticate_node(self, node):
        """Perform authentication with constraints."""
        print(f"Authenticating node {node.node_id}")
        delay = simulate_latency(distance=1000)
        print(f"Communication delay: {delay:.2f} seconds")

        # Try CIR-based authentication
        cir_valid = authenticate_node(node.node_id, node.cir)
        if cir_valid:
            node.energy -= 5  # Simulate energy consumption
            return True
        else:
            print("CIR Failed")
        
        # Fallback to PUF-based authentication
        challenge = [random.randint(0, 1) for _ in range(64)]
        response = random.choice([0, 1])
        success = authenticate_puf(challenge, response)
        node.energy -= 10 if success else 15  # Higher energy cost if fallback is needed
        return success

def run_simulation():
    network = Network()

    # Add authenticator node
    auth_node = Node("authenticator", processing_power=1e6, energy=200)
    network.add_node(auth_node)

    # Add legitimate and malicious nodes
    network.add_node(Node("legitimate_node", processing_power=5e5, energy=150))
    network.add_node(Node("malicious_node", is_malicious=True, processing_power=3e5, energy=100))

    # Create a visualizer and run the simulation
    visualizer = NetworkVisualizer(network)
    visualizer.run()
