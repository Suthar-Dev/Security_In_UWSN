import matplotlib.pyplot as plt
import networkx as nx
import random
from matplotlib.animation import FuncAnimation

class NetworkVisualizer:
    def __init__(self, network):
        self.network = network
        self.G = nx.DiGraph()
        self.pos = nx.spring_layout(self.G)
        self.fig, self.ax = plt.subplots()
        self.node_colors = {}
        self.node_labels = {}

    def setup_network(self):
        """Initialize the network graph with nodes and edges."""
        for node in self.network.nodes:
            self.G.add_node(node.node_id)
            self.node_colors[node.node_id] = 'green' if not node.is_malicious else 'red'
            self.node_labels[node.node_id] = f"{node.node_id}\nEnergy: {node.energy}"

        # Add edges from the authenticator to other nodes
        for node in self.network.nodes[1:]:
            self.G.add_edge("authenticator", node.node_id)

        self.pos = nx.spring_layout(self.G)

    def update_network(self, i):
        """Update the visualization based on the current state of the network."""
        self.ax.clear()
        colors = [self.node_colors[n] for n in self.G.nodes]
        labels = {n: self.node_labels[n] for n in self.G.nodes}

        nx.draw(self.G, self.pos, with_labels=True, labels=labels, node_color=colors, node_size=800, ax=self.ax)

        # Randomly select a node to attempt authentication
        if i % 10 == 0:
            node = random.choice(self.network.nodes[1:])
            self.authenticate_node(node)

    def authenticate_node(self, node):
        """Simulate node authentication and update visualization."""
        success = self.network.authenticate_node(node)
        self.node_labels[node.node_id] = f"{node.node_id}\nEnergy: {node.energy}"
        self.node_colors[node.node_id] = 'blue' if success else 'orange'

    def run(self):
        """Start the animation."""
        self.setup_network()
        ani = FuncAnimation(self.fig, self.update_network, frames=100, interval=1000, repeat=False)
        plt.title("Underwater Sensor Network Authentication")
        plt.show()
