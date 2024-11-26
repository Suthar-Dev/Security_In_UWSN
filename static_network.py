import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report
from mpl_toolkits.mplot3d import Axes3D
import scipy.signal as signal
from scipy.spatial.distance import euclidean

class UnderwaterAuthenticationSystem:
    def __init__(self, n_legitimate_nodes=5, water_depth=50, temp=10, salinity=35):
        np.random.seed(42)
        # Network parameters
        self.n_legitimate_nodes = n_legitimate_nodes
        self.water_depth = water_depth
        self.temperature = temp
        self.salinity = salinity
        
        # Underwater environment parameters
        self.current_drift_max = 0.3     # Minimal drift for static case
        self.temperature_variation = 0.1  # Minimal temperature variation
        self.salinity_variation = 0.1    # Minimal salinity variation
        self.multipath_effect = 0.15     # Reduced multipath effect
        self.sound_speed = self.calculate_sound_speed()
        self.attenuation_coefficient = self.calculate_attenuation()
        
        # Network structure
        self.authenticator_pos = np.array([50, 50, 10])
        self.legitimate_positions = self.generate_random_node_positions(n_legitimate_nodes)
        self.cir_database = {}
        self.authentication_threshold = 0.1 # Stricter threshold for static case

    def calculate_sound_speed(self):
        """Calculate underwater sound speed using Del Grosso equation"""
        return (1492.9 + (4.591 * self.temperature) 
                - (0.05 * self.temperature**2) 
                + (0.0002 * self.temperature**3)
                + (1.33 - (0.011 * self.temperature)) * (self.salinity - 35)
                + (0.016 * self.water_depth / 1000))
    
    def calculate_attenuation(self):
        """Calculate acoustic attenuation in underwater channel"""
        base_freq = 10000  # 10 kHz typical underwater communication
        return (0.1 * np.exp(0.02 * self.temperature) 
                * (1 + (base_freq**2 / (base_freq**2 + 1000**2)))
                * (1 / (1 + self.water_depth/100)))

    def generate_random_node_positions(self, num_nodes, x_bounds = [0,100], y_bounds = [0,100], z_bounds = [0,100]):
        
        np.random.seed(None)
        positions = []
        for _ in range(num_nodes):
            x = np.random.uniform(*x_bounds)
            y = np.random.uniform(*y_bounds)
            z = np.random.uniform(*z_bounds)
            positions.append(np.array([x, y, z]))
        return np.array(positions)


    def apply_underwater_effects(self, cir):
        """Apply minimal underwater effects for static case"""
        temperature_effect = np.random.normal(0, self.temperature_variation, cir.shape)
        salinity_effect = np.random.normal(0, self.salinity_variation, cir.shape)
        multipath_effect = np.random.normal(0, self.multipath_effect, cir.shape)
        return cir + (temperature_effect + salinity_effect + multipath_effect) * np.abs(cir)

    def generate_channel_impulse_response(self, source_pos, dest_pos):
        """Generate CIR based on position and underwater effects"""
        distance = np.linalg.norm(source_pos - dest_pos)
        path_loss = (distance * self.attenuation_coefficient) / self.sound_speed
        
        num_taps = 10
        cir = np.zeros(num_taps, dtype=complex)
        
        # Generate more deterministic CIR for static nodes
        for i in range(num_taps):
            amplitude = np.exp(-path_loss) * (1 / (i + 1))  # Decreasing amplitude with tap
            phase = 2 * np.pi * distance * i / self.sound_speed
            cir[i] = amplitude * np.exp(1j * phase)
        
        return self.apply_underwater_effects(cir)

    def calculate_cir_similarity(self, cir1, cir2):
        """Enhanced CIR similarity calculation"""
        # Magnitude comparison
        magnitude_diff = np.abs(np.abs(cir1) - np.abs(cir2))
        normalized_mag_diff = magnitude_diff / (np.max(np.abs(cir1)) + 1e-10)
    
        # Phase comparison
        phase_diff = np.abs(np.angle(cir1 * np.conj(cir2)))
        normalized_phase_diff = phase_diff / (2 * np.pi)
    
        # Weighted combination
        similarity = (0.7 * np.mean(normalized_mag_diff) + 
                     0.3 * np.mean(normalized_phase_diff))
        # print(cir1,cir2,similarity)
        return similarity

    def generate_malicious_positions(self, num_nodes):
        """Generate malicious node positions far from legitimate nodes"""
        positions = []
        while len(positions) < num_nodes:
            # Generate positions in corners of the network
            corner = np.random.randint(0, 4)
            if corner == 0:
                pos = np.array([10, 10, np.random.uniform(5, 45)])
            elif corner == 1:
                pos = np.array([90, 10, np.random.uniform(5, 45)])
            elif corner == 2:
                pos = np.array([10, 90, np.random.uniform(5, 45)])
            else:
                pos = np.array([90, 90, np.random.uniform(5, 45)])
            
            # Add small random variation
            pos += np.random.uniform(-5, 5, size=3)
            positions.append(pos)
        return np.array(positions)

    def print_cir_database(self):
        """Print CIR values stored in the database"""
        print("\n=== CIR Database Contents ===")
        for node_id, node_data in self.cir_database.items():
            print(f"\nNode {node_id} at position {node_data['position']}")
            print("Reference CIR signatures:")
            for i, signature in enumerate(node_data['signatures']):
                print(f"Signature {i + 1}:")
                print(f"Magnitude: {np.abs(signature)}")
                print(f"Phase: {np.angle(signature)}")
                print("---")

    def initialize_network(self, num_references=5):
        """Initialize network CIR database"""
        self.cir_database.clear()
        for node_id in range(self.n_legitimate_nodes):
            node_position = self.legitimate_positions[node_id]
            signatures = []
            for _ in range(num_references):
                drifted_pos = self.apply_node_drift(node_position)
                cir = self.generate_channel_impulse_response(drifted_pos, self.authenticator_pos)
                signatures.append(cir)
            
            self.cir_database[node_id] = {
                'position': node_position,
                'signatures': signatures,
                'original_position': node_position.copy()
            }
        return self.cir_database
    
    def apply_node_drift(self, position):
        """Apply minimal drift for static nodes"""
        drift = np.random.normal(0, self.current_drift_max/4, size=3)  # Reduced drift for static case
        drift[2] *= 0.2  # Even smaller vertical drift
        return position + drift

    def generate_test_nodes(self, m_test_nodes):
        """Generate mix of legitimate and malicious test nodes"""
        test_nodes = []
        true_labels = []
        
        # Add legitimate nodes
        for node_id in range(min(self.n_legitimate_nodes, m_test_nodes // 2)):
            test_nodes.append({
                'position': self.legitimate_positions[node_id],
                'true_id': node_id,
                'is_legitimate': True
            })
            true_labels.append(1)
        
        # Add malicious nodes
        malicious_count = m_test_nodes - len(test_nodes)
        malicious_positions = self.generate_malicious_positions(malicious_count)
        for pos in malicious_positions:
            test_nodes.append({
                'position': pos,
                'true_id': None,
                'is_legitimate': False
            })
            true_labels.append(0)
            
        return test_nodes, true_labels

    def generate_malicious_positions(self, num_nodes):
        """Generate random positions for malicious nodes"""
        positions = []
        while len(positions) < num_nodes:
            candidate = np.random.uniform(
                low=[0, 0, 0],
                high=[100, 100, self.water_depth],
                size=3
            )
            if not any(np.linalg.norm(candidate - pos) < 20 for pos in self.legitimate_positions):
                positions.append(candidate)
        return np.array(positions)

    def calculate_cir_similarity(self, cir1, cir2):
        # print(cir1,cir2)
        """Calculate similarity between two CIRs"""
        magnitude_diff = np.abs(np.abs(cir1) - np.abs(cir2))
        phase_diff = np.angle(cir1 * np.conj(cir2))
        return np.mean(np.sqrt(magnitude_diff**2 + phase_diff**2))

    def authenticate_node(self, test_position):
        """Enhanced authentication with weighted distance metrics"""
        test_cir = self.generate_channel_impulse_response(test_position, self.authenticator_pos)
        min_distance = float('inf')
        matched_node_id = None
    
        for node_id, node_data in self.cir_database.items():
            node_signatures = node_data['signatures']
        
            # Calculate position-based weight
            position_distance = np.linalg.norm(test_position - node_data['position'])
            position_weight = np.exp(-position_distance / 50)  # Decay factor of 50
        
            # Calculate CIR-based distances with position weight
            distances = []
            for ref_sig in node_signatures:
                # Separate magnitude and phase differences
                magnitude_diff = np.abs(np.abs(test_cir) - np.abs(ref_sig))
                phase_diff = np.abs(np.angle(test_cir * np.conj(ref_sig)))
            
                # Weight the differences
                weighted_mag_diff = np.mean(magnitude_diff) * 0.7  # 70% weight to magnitude
                weighted_phase_diff = np.mean(phase_diff) * 0.3    # 30% weight to phase
            
                # Combine with position weight
                total_distance = (weighted_mag_diff + weighted_phase_diff) * (1 + (1 - position_weight))
                distances.append(total_distance)
            
            # print(node_id, distances,test_position)
            avg_distance = np.mean(distances)
        
            if avg_distance < min_distance:
                min_distance = avg_distance
                matched_node_id = node_id
    
        # Dynamic threshold based on distance
        dynamic_threshold = self.authentication_threshold * (1 + min_distance/5)
    
        return {
            'authenticated': min_distance <= dynamic_threshold,
            'distance': min_distance,
            'matched_node': matched_node_id,
            'test_cir': test_cir
        }

    def authenticate_nodes(self, test_nodes):
        """Authenticate multiple test nodes"""
        predictions = []
        authentication_details = []
        
        for node in test_nodes:
            auth_result = self.authenticate_node(node['position'])
            predictions.append(1 if auth_result['authenticated'] else 0)
            authentication_details.append({
                'is_legitimate': node['is_legitimate'],
                'authenticated': auth_result['authenticated'],
                'distance': auth_result['distance'],
                'matched_node': auth_result['matched_node'],
                'test_cir': auth_result['test_cir']
            })
        return predictions, authentication_details

    def plot_network_structure(self, test_nodes=None, auth_details=None):
        """
        Visualize network structure with optional test results
        
        This 3D plot shows:
        1. Red triangle: Authenticator node position
        2. Blue dots: Original legitimate node positions
        3. Green dotted lines: Communication links between legitimate nodes and authenticator
        4. Colored markers for test results (if provided):
           - Green circles: True Positives (correctly authenticated legitimate nodes)
           - Red X's: False Positives (incorrectly authenticated malicious nodes)
           - Orange squares: False Negatives (incorrectly rejected legitimate nodes)
           - Purple diamonds: True Negatives (correctly rejected malicious nodes)
        """
        """Visualize network structure with optional test results"""
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        # Plot authenticator
        ax.scatter(*self.authenticator_pos, color='red', s=200, marker='^',
                  label='Authenticator Node')
        
        # Plot legitimate nodes
        ax.scatter(self.legitimate_positions[:, 0],
                  self.legitimate_positions[:, 1],
                  self.legitimate_positions[:, 2],
                  color='blue', s=100, label='Legitimate Nodes')
        
        # Connect legitimate nodes to authenticator
        for pos in self.legitimate_positions:
            ax.plot([self.authenticator_pos[0], pos[0]],
                   [self.authenticator_pos[1], pos[1]],
                   [self.authenticator_pos[2], pos[2]],
                   'g--', alpha=0.3)
        
        # Plot test nodes if provided
        if test_nodes is not None and auth_details is not None:
            for node, detail in zip(test_nodes, auth_details):
                pos = node['position']
                if detail['authenticated'] and node['is_legitimate']:
                    color, marker, label = 'green', 'o', 'True Positive'
                elif detail['authenticated'] and not node['is_legitimate']:
                    color, marker, label = 'red', 'x', 'False Positive'
                elif not detail['authenticated'] and node['is_legitimate']:
                    color, marker, label = 'orange', 's', 'False Negative'
                else:
                    color, marker, label = 'purple', 'D', 'True Negative'
                
                ax.scatter(pos[0], pos[1], pos[2],
                          color=color, marker=marker, s=100, label=label)
        
        # Remove duplicate labels
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys())
        
        ax.set_xlabel('X Position (m)')
        ax.set_ylabel('Y Position (m)')
        ax.set_zlabel('Depth (m)')
        ax.set_title('Underwater Network Structure')
        plt.show()

    def plot_cir_visualization(self, auth_details, node_idx):
        """
        Visualize CIR comparison for a specific node
        
        Left Plot - CIR Magnitude Comparison:
        - Red solid line: Test node's CIR magnitude
        - Blue dashed lines: Reference CIR magnitudes from database
        - Higher magnitude indicates stronger signal at that delay tap
        - Similar patterns between test and reference suggest legitimate node
        
        Right Plot - CIR Phase Comparison:
        - Red solid line: Test node's CIR phase
        - Blue dashed lines: Reference CIR phases from database
        - Phase shows signal delay characteristics
        - Similar phase patterns indicate similar multipath characteristics
        """
        detail = auth_details[node_idx]
        test_cir = detail['test_cir']
        ref_node = detail['matched_node']
        
        if ref_node is not None:
            ref_cirs = self.cir_database[ref_node]['signatures']
            
            plt.figure(figsize=(15, 5))
            
            # Plot magnitude
            plt.subplot(121)
            plt.title('CIR Magnitude Comparison')
            plt.plot(np.abs(test_cir), 'r-', linewidth=2, label='Test Node')
            for i, ref_cir in enumerate(ref_cirs):
                plt.plot(np.abs(ref_cir), 'b--', alpha=0.5, 
                        label=f'Reference {i+1}' if i == 0 else None)
            plt.xlabel('Tap Index (Time Delay)')
            plt.ylabel('Magnitude (Signal Strength)')
            plt.legend()
            
            # Plot phase
            plt.subplot(122)
            plt.title('CIR Phase Comparison')
            plt.plot(np.angle(test_cir), 'r-', linewidth=2, label='Test Node')
            for i, ref_cir in enumerate(ref_cirs):
                plt.plot(np.angle(ref_cir), 'b--', alpha=0.5,
                        label=f'Reference {i+1}' if i == 0 else None)
            plt.xlabel('Tap Index (Time Delay)')
            plt.ylabel('Phase (radians)')
            plt.legend()
            
            # Add authentication result as text
            plt.figtext(0.5, 0.02, 
                       f"Authentication Result: {'Authenticated' if detail['authenticated'] else 'Rejected'}\n" +
                       f"Distance Metric: {detail['distance']:.4f} (Threshold: {self.authentication_threshold})",
                       ha='center', bbox=dict(facecolor='white', alpha=0.8))
            
            plt.tight_layout()
            plt.show()

    def plot_authentication_metrics(self, true_labels, predictions):
        """
        Plot authentication performance metrics
        
        Confusion Matrix Shows:
        - True Negatives: Correctly identified malicious nodes (top-left)
        - False Positives: Incorrectly authenticated malicious nodes (top-right)
        - False Negatives: Incorrectly rejected legitimate nodes (bottom-left)
        - True Positives: Correctly authenticated legitimate nodes (bottom-right)
        
        Classification Report Shows:
        - Precision: Ratio of correct authentications to total authentications
        - Recall: Ratio of correct authentications to total legitimate nodes
        - F1-score: Harmonic mean of precision and recall
        - Support: Number of instances for each class
        """
        plt.figure(figsize=(8, 6))
        cm = confusion_matrix(true_labels, predictions)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                   xticklabels=['Malicious', 'Legitimate'],
                   yticklabels=['Malicious', 'Legitimate'])
        plt.title('Authentication Confusion Matrix')
        plt.xlabel('Predicted')
        plt.ylabel('True')
        plt.show()
        
        print("\nClassification Report:")
        print(classification_report(true_labels, predictions,
                                 target_names=['Malicious', 'Legitimate']))

def run_simulation(n_legitimate=5, m_test=20):
    """Run comprehensive underwater network authentication simulation"""
    print("\n=== Underwater Network Authentication Simulation ===")
    print(f"Initializing network with {n_legitimate} legitimate nodes...")
    print(f"Testing with {m_test} nodes ({m_test//2} legitimate, {m_test - m_test//2} malicious)")
    
    # Create and initialize network
    network = UnderwaterAuthenticationSystem(n_legitimate_nodes=n_legitimate)
    network.initialize_network()
    
    # Plot initial network structure
    print("\n=== Initial Network Structure ===")
    network.plot_network_structure()
    
    # Generate and authenticate test nodes
    test_nodes, true_labels = network.generate_test_nodes(m_test)
    predictions, auth_details = network.authenticate_nodes(test_nodes)
    
    # Plot authentication results
    print("\n=== Authentication Test Results ===")
    network.plot_network_structure(test_nodes, auth_details)
    
    # Print detailed results
    print("\n=== Detailed Authentication Results ===")
    for i, (node, detail) in enumerate(zip(test_nodes, auth_details)):
        print(f"\nNode {i}:")
        print(f" Type: {'Legitimate' if node['is_legitimate'] else 'Malicious'}")
        print(f" Position: {node['position']}")
        print(f" Authentication Result: {detail['authenticated']}")
        print(f" Authentication Distance: {detail['distance']:.4f}")
        print(f" Matched with Node: {detail['matched_node']}")
        
        # Visualize CIR comparison for a few nodes
        if i < 3:  # Show first 3 nodes as examples
            network.plot_cir_visualization(auth_details, i)
    
    # Plot authentication metrics
    print("\n=== Authentication Performance Metrics ===")
    network.plot_authentication_metrics(true_labels, predictions)

if __name__ == "__main__":
    run_simulation(n_legitimate=10, m_test=50)