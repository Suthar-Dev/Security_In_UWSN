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
        
        # Path types and movement parameters
        self.path_types = ['circular', 'figure8', 'square']
        self.path_radius = 15  # Radius of paths
        self.angular_speed = 0.15  # Angular speed in radians per time step
        self.time_step = 0  # Current time step
        self.node_paths = {}  # Store path information for each node
        
        # Underwater environment parameters
        self.current_drift_max = 0.5      # Increased for mobile case
        self.temperature_variation = 0.15  # Slightly increased variation
        self.salinity_variation = 0.15    # Slightly increased variation
        self.multipath_effect = 0.2       # Increased multipath effect
        self.sound_speed = self.calculate_sound_speed()
        self.attenuation_coefficient = self.calculate_attenuation()
        
        # Network structure
        self.authenticator_pos = np.array([50, 50, 10])
        self.legitimate_positions = self.generate_fixed_node_positions(n_legitimate_nodes)
        self.cir_database = {}
        self.authentication_threshold = 0.2  # Increased threshold for mobile case

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

    def generate_fixed_node_positions(self, num_nodes):
        """Generate initial positions for nodes with assigned path types"""
        positions = []
        radius = 30
        for i in range(num_nodes):
            angle = 2 * np.pi * i / num_nodes
            x = self.authenticator_pos[0] + radius * np.cos(angle)
            y = self.authenticator_pos[1] + radius * np.sin(angle)
            z = 15  # Initial depth
            positions.append(np.array([x, y, z]))
            
            # Assign path type and store path information
            path_type = self.path_types[i % len(self.path_types)]
            self.node_paths[i] = {
                'type': path_type,
                'phase': np.random.uniform(0, 2*np.pi),  # Random starting phase
                'center': np.array([x, y, z])  # Center of the path
            }
        
        return np.array(positions)

    def update_node_position(self, node_id, time_step):
        """Update node position based on its assigned path type"""
        path_info = self.node_paths[node_id]
        center = path_info['center']
        path_type = path_info['type']
        phase = path_info['phase']
        
        if path_type == 'circular':
            # Circular path
            angle = self.angular_speed * time_step + phase
            x = center[0] + self.path_radius * np.cos(angle)
            y = center[1] + self.path_radius * np.sin(angle)
            z = center[2] + np.sin(angle) * 2  # Small vertical oscillation
            
        elif path_type == 'figure8':
            # Figure-8 path
            angle = self.angular_speed * time_step + phase
            x = center[0] + self.path_radius * np.cos(angle)
            y = center[1] + self.path_radius * np.sin(2*angle) / 2
            z = center[2] + np.sin(angle) * 2
            
        else:  # square
            # Square path
            angle = self.angular_speed * time_step + phase
            segment = int((angle / (np.pi/2)) % 4)
            progress = (angle % (np.pi/2)) / (np.pi/2)
            
            if segment == 0:
                x = center[0] + self.path_radius * progress
                y = center[1] + self.path_radius
            elif segment == 1:
                x = center[0] + self.path_radius
                y = center[1] + self.path_radius * (1 - progress)
            elif segment == 2:
                x = center[0] + self.path_radius * (1 - progress)
                y = center[1] - self.path_radius
            else:
                x = center[0] - self.path_radius
                y = center[1] - self.path_radius * (1 - progress)
            
            z = center[2] + np.sin(angle) * 2
        
        return np.array([x, y, z])

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
        
        for i in range(num_taps):
            amplitude = np.exp(-path_loss) * (1 / (i + 1))
            phase = 2 * np.pi * distance * i / self.sound_speed
            cir[i] = amplitude * np.exp(1j * phase)
        
        return self.apply_underwater_effects(cir)

    def initialize_network(self, num_references=10):
        """Initialize network CIR database with nodes at different points along their paths"""
        self.cir_database.clear()
        time_steps = np.linspace(0, 2*np.pi, num_references)
    
        print("\n=== Initialization Phase Details ===")
        print(f"Number of reference points per path: {num_references}")
    
        for node_id in range(self.n_legitimate_nodes):
            signatures = []
            positions = []
        
            print(f"\nLegitimate Node {node_id}:")
            print(f"Path Type: {self.node_paths[node_id]['type']}")
        
            for t in time_steps:
                node_position = self.update_node_position(node_id, t)
                cir = self.generate_channel_impulse_response(node_position, self.authenticator_pos)
                signatures.append(cir)
                positions.append(node_position)
            
                print(f"\nTime step {t:.2f}:")
                print(f"Position: [{node_position[0]:.2f}, {node_position[1]:.2f}, {node_position[2]:.2f}]")
                print(f"CIR Magnitude: {np.abs(cir)[:5]}")  # Show first 5 taps
                print(f"CIR Phase: {np.angle(cir)[:5]}")
        
            self.cir_database[node_id] = {
                'signatures': signatures,
                'positions': positions,
                'path_type': self.node_paths[node_id]['type']
            }
    
        print("\n=== Database Summary ===")
        for node_id in self.cir_database:
            node_data = self.cir_database[node_id]
            print(f"\nNode {node_id}:")
            print(f"Path Type: {node_data['path_type']}")
            print(f"Number of reference positions: {len(node_data['positions'])}")
            print(f"Number of CIR signatures: {len(node_data['signatures'])}")
    
        return self.cir_database

    def calculate_cir_similarity(self, cir1, cir2):
        """Calculate similarity between two CIRs with detailed metrics"""
        # Magnitude comparison
        magnitude_diff = np.abs(np.abs(cir1) - np.abs(cir2))
        normalized_mag_diff = magnitude_diff / (np.max(np.abs(cir1)) + 1e-10)
    
        # Phase comparison
        phase_diff = np.abs(np.angle(cir1 * np.conj(cir2)))
        normalized_phase_diff = phase_diff / (2 * np.pi)
    
        # Weighted combination
        mag_weight = 0.7
        phase_weight = 0.3
        similarity = (mag_weight * np.mean(normalized_mag_diff) + 
                     phase_weight * np.mean(normalized_phase_diff))
    
        print("\nCIR Similarity Calculation:")
        print(f"Average Magnitude Difference: {np.mean(normalized_mag_diff):.4f}")
        print(f"Average Phase Difference: {np.mean(normalized_phase_diff):.4f}")
        print(f"Combined Similarity (w={mag_weight:.1f}*mag + {phase_weight:.1f}*phase): {similarity:.4f}")
    
        return similarity

    def authenticate_node(self, test_position):
        """Enhanced authentication with detailed metrics printing"""
        test_cir = self.generate_channel_impulse_response(test_position, self.authenticator_pos)
    
        print("\n=== Authentication Phase Details ===")
        print(f"Test Node Position: [{test_position[0]:.2f}, {test_position[1]:.2f}, {test_position[2]:.2f}]")
        print(f"Test Node CIR Magnitude: {np.abs(test_cir)[:5]}")
        print(f"Test Node CIR Phase: {np.angle(test_cir)[:5]}")
    
        min_distance = float('inf')
        matched_node_id = None
        all_distances = {}
    
        for node_id, node_data in self.cir_database.items():
            path_distances = []
        
            print(f"\nComparing with Legitimate Node {node_id}:")
            print(f"Path Type: {node_data['path_type']}")
        
            for ref_pos, ref_sig in zip(node_data['positions'], node_data['signatures']):
                # Position-based weight
                position_distance = np.linalg.norm(test_position - ref_pos)
                position_weight = np.exp(-position_distance / 20)
            
                # CIR similarity
                cir_similarity = self.calculate_cir_similarity(test_cir, ref_sig)
            
                # Combined metric
                weighted_distance = cir_similarity * (1 + (1 - position_weight))
                path_distances.append(weighted_distance)
            
                print(f"\nReference Point Analysis:")
                print(f"Reference Position: [{ref_pos[0]:.2f}, {ref_pos[1]:.2f}, {ref_pos[2]:.2f}]")
                print(f"Position Distance: {position_distance:.4f}")
                print(f"Position Weight: {position_weight:.4f}")
                print(f"CIR Similarity: {cir_similarity:.4f}")
                print(f"Weighted Distance: {weighted_distance:.4f}")
        
            min_path_distance = np.min(path_distances)
            all_distances[node_id] = min_path_distance
        
            print(f"\nMinimum Distance for Node {node_id}: {min_path_distance:.4f}")
        
            if min_path_distance < min_distance:
                min_distance = min_path_distance
                matched_node_id = node_id
    
        # Dynamic threshold calculation
        dynamic_threshold = self.authentication_threshold * (1 + min_distance/2)
    
        print("\n=== Authentication Decision ===")
        print(f"Matched Node ID: {matched_node_id}")
        print(f"Final Distance Metric: {min_distance:.4f}")
        print(f"Dynamic Threshold: {dynamic_threshold:.4f}")
        print(f"Authentication Result: {'Authenticated' if min_distance <= dynamic_threshold else 'Rejected'}")
        print("\nAll Node Distances:")
        for node_id, distance in all_distances.items():
            print(f"Node {node_id}: {distance:.4f}")
    
        return {
            'authenticated': min_distance <= dynamic_threshold,
            'distance': min_distance,
            'matched_node': matched_node_id,
            'test_cir': test_cir,
            'all_distances': all_distances
        }

    def authenticate_nodes(self, test_nodes):
        """Authenticate multiple test nodes considering movement"""
        self.time_step += 1  # Update current time step
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

    def generate_test_nodes(self, m_test_nodes):
        """Generate mix of legitimate and malicious test nodes"""
        test_nodes = []
        true_labels = []
    
        # Add legitimate nodes at random positions along their paths
        for node_id in range(min(self.n_legitimate_nodes, m_test_nodes // 2)):
            # Random time point for current position
            random_time = np.random.uniform(0, 2*np.pi)
            current_pos = self.update_node_position(node_id, random_time)
        
            test_nodes.append({
                'position': current_pos,
                'true_id': node_id,
                'is_legitimate': True
            })
            true_labels.append(1)
    
        # Add malicious nodes at random positions
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

    def plot_network_structure(self, test_nodes=None, auth_details=None):
        """Enhanced visualization showing node paths"""
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        # Plot authenticator
        ax.scatter(*self.authenticator_pos, color='red', s=200, marker='^',
                  label='Authenticator Node')
        
        # Plot legitimate nodes and their paths
        colors = plt.cm.rainbow(np.linspace(0, 1, self.n_legitimate_nodes))
        for node_id in range(self.n_legitimate_nodes):
            # Plot path trajectory
            t = np.linspace(0, 4*np.pi, 100)
            path_points = np.array([self.update_node_position(node_id, ti) for ti in t])
            
            ax.plot(path_points[:, 0], path_points[:, 1], path_points[:, 2],
                   '--', color=colors[node_id], alpha=0.3,
                   label=f'Node {node_id} Path ({self.node_paths[node_id]["type"]})')
            
            # Plot current position
            current_pos = self.update_node_position(node_id, self.time_step)
            ax.scatter(*current_pos, color=colors[node_id], s=100)
        
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
        ax.legend(by_label.values(), by_label.keys(), bbox_to_anchor=(1.15, 1))
        
        ax.set_xlabel('X Position (m)')
        ax.set_ylabel('Y Position (m)')
        ax.set_zlabel('Depth (m)')
        ax.set_title('Underwater Network Structure with Node Paths')
        plt.tight_layout()
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
        Plot authentication performance metrics with proper handling of edge cases
    
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
        # Convert labels to numpy arrays if they aren't already
        true_labels = np.array(true_labels)
        predictions = np.array(predictions)
    
        # Plot confusion matrix
        plt.figure(figsize=(8, 6))
        cm = confusion_matrix(true_labels, predictions)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Malicious', 'Legitimate'],
                yticklabels=['Malicious', 'Legitimate'])
        plt.title('Authentication Confusion Matrix')
        plt.xlabel('Predicted')
        plt.ylabel('True')
        plt.show()
    
        # Calculate and display basic metrics
        true_pos = cm[1, 1]
        false_pos = cm[0, 1]
        false_neg = cm[1, 0]
        true_neg = cm[0, 0]
    
        total = np.sum(cm)
        accuracy = (true_pos + true_neg) / total if total > 0 else 0
    
        # Calculate precision, recall, and F1 with proper handling of edge cases
        precision = true_pos / (true_pos + false_pos) if (true_pos + false_pos) > 0 else 0
        recall = true_pos / (true_pos + false_neg) if (true_pos + false_neg) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
        print("\nDetailed Authentication Metrics:")
        print(f"Accuracy: {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall: {recall:.4f}")
        print(f"F1-score: {f1:.4f}")
    
        print("\nDetailed counts:")
        print(f"True Positives (correctly authenticated legitimate nodes): {true_pos}")
        print(f"False Positives (incorrectly authenticated malicious nodes): {false_pos}")
        print(f"True Negatives (correctly rejected malicious nodes): {true_neg}")
        print(f"False Negatives (incorrectly rejected legitimate nodes): {false_neg}")
    
        # Classification report with zero_division parameter
        print("\nClassification Report:")
        print(classification_report(true_labels, predictions,
                              target_names=['Malicious', 'Legitimate'],
                              zero_division=0))

def run_simulation(n_legitimate=5, m_test=20):
    """Run simulation with path-based node movement"""
    print("\n=== Underwater Network Authentication Simulation (Fixed Path Motion) ===")
    print(f"Initializing network with {n_legitimate} legitimate nodes...")
    
    # Create and initialize network
    network = UnderwaterAuthenticationSystem(n_legitimate_nodes=n_legitimate)
    network.initialize_network(num_references=15)  # Increased reference points
    
    # Initial visualization of network structure and paths
    print("\n=== Initial Network Structure and Paths ===")
    network.plot_network_structure()
    
    # Run authentication tests
    print("\n=== Running Authentication Tests ===")
    test_nodes, true_labels = network.generate_test_nodes(m_test)
    predictions, auth_details = network.authenticate_nodes(test_nodes)
    
    # Plot authentication results
    print("\n=== Authentication Results ===")
    network.plot_network_structure(test_nodes, auth_details)
    network.plot_authentication_metrics(true_labels, predictions)
    
    # Display example CIR comparisons
    print("\n=== CIR Visualization for Sample Nodes ===")
    for i in range(min(2, len(auth_details))):
        network.plot_cir_visualization(auth_details, i)
        
        
if __name__ == "__main__":
    run_simulation(n_legitimate=5, m_test=10)