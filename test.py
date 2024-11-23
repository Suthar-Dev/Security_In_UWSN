import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report
from mpl_toolkits.mplot3d import Axes3D
import scipy.signal as signal
from scipy.spatial.distance import euclidean
import random

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
        self.authenticator_pos = np.array([50, 50, 25])
        self.legitimate_positions = self.generate_fixed_node_positions(n_legitimate_nodes)
        self.cir_database = {}
        self.authentication_threshold = 0.1  # Increased threshold for mobile case

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
        """Generate initial positions for nodes with assigned path types and random radii"""
        positions = []
        for i in range(num_nodes):
            # Random radius between 15-40 meters
            radius = np.random.uniform(15, 40)
            angle = 2 * np.pi * i / num_nodes
            x = self.authenticator_pos[0] + radius * np.cos(angle)
            y = self.authenticator_pos[1] + radius * np.sin(angle)
            z = random.uniform(10, 40)  # Random depth between 10-40m
            positions.append(np.array([x, y, z]))
        
            # Assign path type and store path information
            path_type = self.path_types[i % len(self.path_types)]
            self.node_paths[i] = {
                'type': path_type,
                'phase': 0,  # Start at consistent phase
                'center': np.array([x, y, z]),
                'radius': radius  # Store the random radius
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
        """
        Enhanced CIR generation that better accounts for underwater acoustic properties
        and physical position relationships.
        """
        # Distance vector and scalar distance
        distance_vector = dest_pos - source_pos
        distance = np.linalg.norm(distance_vector)
        
        # Enhanced path loss model
        spreading_loss = 20 * np.log10(distance)  # Geometric spreading loss
        absorption_loss = self.attenuation_coefficient * distance
        path_loss = np.exp(-(spreading_loss + absorption_loss) / 20)
        
        # Angle-dependent components
        elevation_angle = np.arctan2(distance_vector[2], 
                                np.sqrt(distance_vector[0]**2 + distance_vector[1]**2))
        azimuth_angle = np.arctan2(distance_vector[1], distance_vector[0])
        
        # Initialize CIR array
        num_taps = 15
        cir = np.zeros(num_taps, dtype=complex)
        
        # Direct path component with angle-dependent phase
        direct_delay = distance / self.sound_speed
        tap_index = int(direct_delay * 1e4) % num_taps
        phase = 2 * np.pi * (distance + elevation_angle + azimuth_angle) / self.sound_speed
        cir[tap_index] = path_loss * np.exp(1j * phase)
        
        # Enhanced multipath modeling
        n_paths = min(5, int(2 + distance/40))  # Fewer but more significant paths
        
        for i in range(n_paths):
            # Surface reflection
            surface_reflection = np.array([source_pos[0], source_pos[1], -source_pos[2]])
            surface_distance = np.linalg.norm(surface_reflection - dest_pos)
            surface_loss = path_loss * 0.6 * np.exp(-i/2)  # Decay with each bounce
            surface_delay = surface_distance / self.sound_speed
            tap_index = int(surface_delay * 1e4) % num_taps
            surface_phase = 2 * np.pi * surface_distance / self.sound_speed
            cir[tap_index] += surface_loss * np.exp(1j * surface_phase)
            
            # Bottom reflection
            bottom_reflection = np.array([source_pos[0], source_pos[1], 
                                        2*self.water_depth - source_pos[2]])
            bottom_distance = np.linalg.norm(bottom_reflection - dest_pos)
            bottom_loss = path_loss * 0.4 * np.exp(-i/2)  # More loss from bottom
            bottom_delay = bottom_distance / self.sound_speed
            tap_index = int(bottom_delay * 1e4) % num_taps
            bottom_phase = 2 * np.pi * bottom_distance / self.sound_speed
            cir[tap_index] += bottom_loss * np.exp(1j * bottom_phase)
        
        # Apply underwater effects with position-dependent variations
        cir = self.apply_underwater_effects(cir)
        
        return cir


    def initialize_network(self, num_references=20):
        """Initialize network CIR database with evenly distributed points along complete paths"""
        self.cir_database.clear()
        # Evenly distributed points along complete path
        time_steps = np.linspace(0, 2*np.pi, num_references, endpoint=False)
    
        print("\n=== Initialization Phase Database ===")
    
        for node_id in range(self.n_legitimate_nodes):
            signatures = []
            positions = []
            path_info = self.node_paths[node_id]
        
            print(f"\nLegitimate Node {node_id}:")
            print(f"Path Type: {path_info['type']}")
            print(f"Path Radius: {path_info['radius']:.2f}m")
        
            for t in time_steps:
                node_position = self.update_node_position(node_id, t)
                cir = self.generate_channel_impulse_response(node_position, self.authenticator_pos)
                signatures.append(cir)
                positions.append(node_position)
            
                print(f"\nReference Point {int(t/2/np.pi*num_references)}:")
                print(f"Position: [{node_position[0]:.2f}, {node_position[1]:.2f}, {node_position[2]:.2f}]")
                print(f"CIR Magnitude: {np.abs(cir)[:5]}")
        
            self.cir_database[node_id] = {
                'signatures': signatures,
                'positions': positions,
                'path_type': path_info['type'],
                'radius': path_info['radius']
            }
    
        return self.cir_database

    def calculate_cir_similarity(self, cir1, cir2, pos1, pos2):
        """
        Enhanced CIR similarity calculation that considers both signal characteristics 
        and physical distance between positions.
        """
        # Calculate physical distance between positions
        physical_distance = np.linalg.norm(pos1 - pos2)
        
        # Distance weight factor - similarity decreases with distance
        distance_weight = np.exp(-physical_distance / 20)  # 20m characteristic length
        
        # Normalize CIRs
        cir1_norm = cir1 / (np.linalg.norm(cir1) + 1e-10)
        cir2_norm = cir2 / (np.linalg.norm(cir2) + 1e-10)
        
        # Calculate correlation coefficient
        correlation = np.abs(np.sum(cir1_norm * np.conj(cir2_norm)))
        
        # Calculate phase difference
        phase_diff = np.mean(np.abs(np.angle(cir1_norm) - np.angle(cir2_norm)))
        
        # Calculate magnitude difference
        mag_diff = np.mean(np.abs(np.abs(cir1_norm) - np.abs(cir2_norm)))
        
        # Combined MTRRS score weighted by distance (lower is better)
        mtrrs = ((1 - correlation) * 0.4 + phase_diff * 0.3 + mag_diff * 0.3) / distance_weight
        
        return mtrrs

    def authenticate_node(self, test_position, is_legitimate=None, true_id=None):
        """Modified authentication with distance-aware similarity checking"""
        test_cir = self.generate_channel_impulse_response(test_position, self.authenticator_pos)
        
        min_similarity = float('inf')
        matched_node_id = None
        matched_ref_cir = None
        matched_ref_pos = None
        
        # Find best matching reference CIR considering position
        for node_id, node_data in self.cir_database.items():
            for ref_sig, ref_pos in zip(node_data['signatures'], node_data['positions']):
                # Enhanced similarity calculation that considers position
                similarity = self.calculate_cir_similarity(test_cir, ref_sig, 
                                                        test_position, ref_pos)
                if similarity < min_similarity:
                    min_similarity = similarity
                    matched_node_id = node_id
                    matched_ref_cir = ref_sig
                    matched_ref_pos = ref_pos
        
        # Stricter authentication threshold based on distance
        distance_to_matched = np.linalg.norm(test_position - matched_ref_pos) if matched_ref_pos is not None else float('inf')
        adjusted_threshold = self.authentication_threshold * (1 + distance_to_matched/50)
        
        # Authentication decision
        is_authenticated = min_similarity <= adjusted_threshold
        
        # Debug output remains the same as before
        print("\n=== Authentication Test ===")
        print(f"Test Node ID: {'Unknown' if true_id is None else true_id}")
        print(f"Node Type: {'LEGITIMATE' if is_legitimate else 'MALICIOUS'}")
        print(f"Authentication Result: {'AUTHENTICATED' if is_authenticated else 'REJECTED'}")
        print(f"Similarity Score: {min_similarity:.4f} (Adjusted Threshold: {adjusted_threshold:.4f})")
        print(f"Distance to Matched Position: {distance_to_matched:.2f}m")
        print(f"Best Matched Legitimate Node: {matched_node_id}")
        
        result = {
            'authenticated': is_authenticated,
            'similarity': min_similarity,
            'matched_node': matched_node_id,
            'test_cir': test_cir,
            'matched_ref_cir': matched_ref_cir if is_authenticated else None,
            'matched_ref_pos': matched_ref_pos if is_authenticated else None
        }
        
        return result

    def authenticate_nodes(self, test_nodes):
        """Authenticate multiple test nodes with complete debug information"""
        self.time_step += 1
        predictions = []
        authentication_details = []
        
        print("\n=== Starting Authentication Tests ===")
        print(f"Total nodes to test: {len(test_nodes)}")
        print("----------------------------------------")
        
        for i, node in enumerate(test_nodes):
            print(f"\nTesting Node {i+1} of {len(test_nodes)}")
            auth_result = self.authenticate_node(
                node['position'], 
                is_legitimate=node['is_legitimate'],
                true_id=node.get('true_id')
            )
            predictions.append(1 if auth_result['authenticated'] else 0)
            authentication_details.append({
                'is_legitimate': node['is_legitimate'],
                'authenticated': auth_result['authenticated'],
                'similarity': auth_result['similarity'],
                'matched_node': auth_result['matched_node'],
                'test_cir': auth_result['test_cir'],
                'matched_ref_cir': auth_result.get('matched_ref_cir'),
                'matched_ref_pos': auth_result.get('matched_ref_pos')
            })
        
        # Summary of results
        print("\n=== Authentication Summary ===")
        total_nodes = len(test_nodes)
        legitimate_nodes = sum(1 for node in test_nodes if node['is_legitimate'])
        malicious_nodes = total_nodes - legitimate_nodes
        authenticated_nodes = sum(predictions)
        false_positives = sum(1 for i, pred in enumerate(predictions) 
                            if pred == 1 and not test_nodes[i]['is_legitimate'])
        
        print(f"Total Nodes Tested: {total_nodes}")
        print(f"Legitimate Nodes: {legitimate_nodes}")
        print(f"Malicious Nodes: {malicious_nodes}")
        print(f"Total Authenticated: {authenticated_nodes}")
        print(f"False Positives: {false_positives}")
        
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
        """Enhanced visualization showing node paths and reference points"""
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
    
        # Plot authenticator
        ax.scatter(*self.authenticator_pos, color='red', s=200, marker='^',
                  label='Authenticator Node')
    
        # Plot legitimate nodes and their paths
        colors = plt.cm.rainbow(np.linspace(0, 1, self.n_legitimate_nodes))
        for node_id in range(self.n_legitimate_nodes):
            # Plot complete path trajectory
            t = np.linspace(0, 2*np.pi, 100)
            path_points = np.array([self.update_node_position(node_id, ti) for ti in t])
        
            # Plot path
            ax.plot(path_points[:, 0], path_points[:, 1], path_points[:, 2],
                   '--', color=colors[node_id], alpha=0.3,
                    label=f'Node {node_id} Path ({self.node_paths[node_id]["type"]})')
        
            # Plot reference points
            if node_id in self.cir_database:
                ref_positions = np.array(self.cir_database[node_id]['positions'])
                ax.scatter(ref_positions[:, 0], ref_positions[:, 1], ref_positions[:, 2],
                          color=colors[node_id], marker='o', s=50,
                          label=f'Node {node_id} Reference Points')
        
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
        ax.set_title('Underwater Network Structure with Node Paths and Reference Points')
        plt.tight_layout()
        plt.show()
        
    def plot_cir_visualization(self, auth_details, node_idx):
        """Fixed CIR visualization without distance metric"""
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
            plt.xlabel('Tap Index')
            plt.ylabel('Magnitude')
            plt.legend()
            
            # Plot phase
            plt.subplot(122)
            plt.title('CIR Phase Comparison')
            plt.plot(np.angle(test_cir), 'r-', linewidth=2, label='Test Node')
            for i, ref_cir in enumerate(ref_cirs):
                plt.plot(np.angle(ref_cir), 'b--', alpha=0.5,
                        label=f'Reference {i+1}' if i == 0 else None)
            plt.xlabel('Tap Index')
            plt.ylabel('Phase (radians)')
            plt.legend()
            
            # Add authentication result text
            plt.figtext(0.5, 0.02, 
                    f"Authentication Result: {'Authenticated' if detail['authenticated'] else 'Rejected'}\n" +
                    f"Similarity Score: {detail['similarity']:.4f}",
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
    run_simulation(n_legitimate=5, m_test=30)