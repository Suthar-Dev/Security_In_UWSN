import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.spatial.distance import euclidean
import random
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from cryptography.fernet import Fernet

class UnderwaterChannel:
    def __init__(self, depth=50, salinity=35, temperature=15):
        """
        More localized underwater channel model
        """
        c = 1448.96 + 4.591 * temperature - 0.05304 * (temperature**2) \
            + 2.374 * salinity + 0.0373 * depth + 1.34 * (depth**2 / 1000)
        
        self.sound_speed = c  # m/s
        self.depth = depth
        self.salinity = salinity
        self.temperature = temperature
        
        self.frequency = 25000  # 25 kHz typical for underwater acoustics
        
    def calculate_cir(self, transmitter_pos, receiver_pos):
        """
        More localized Channel Impulse Response (CIR) calculation
        """
        distance = euclidean(transmitter_pos, receiver_pos)
        direct_delay = distance / self.sound_speed
        
        # Direction vector calculations
        direction_vector = receiver_pos - transmitter_pos
        
        # Prevent divide by zero
        azimuth = np.arctan2(direction_vector[1], direction_vector[0] + 1e-10)
        elevation = np.arcsin(direction_vector[2] / (distance + 1e-10))
        
        # Simplified path loss calculation
        spreading_loss = 20 * np.log10(distance + 1)
        
        try:
            absorption_coeff = (0.1 * self.frequency**2 / (1 + self.frequency**2)) + \
                               (40 * self.frequency**2 / (4100 + self.frequency**2)) + \
                               2.75e-4 * self.frequency**2 + 0.003
            
            absorption_loss = max(absorption_coeff * distance / 1000, 0)
            
            total_loss_db = spreading_loss + absorption_loss
            base_amplitude = 10 ** (-total_loss_db / 20)
        except OverflowError:
            base_amplitude = 1e-10
        
        # Simplified multipath components
        num_paths = 3
        amplitudes = []
        delays = []
        phases = []
        
        # Direct path
        amplitudes.append(base_amplitude)
        delays.append(direct_delay)
        phases.append(azimuth)
        
        # Simplified reflection components
        for i in range(1, num_paths):
            reflection_delay = direct_delay + np.random.uniform(0.001, 0.03)
            reflection_distance = distance * (1 + np.random.uniform(0.1, 0.3))
            
            reflection_loss = 20 * np.log10(reflection_distance + 1)
            reflection_amplitude = base_amplitude * (0.5 ** i) * (10 ** (-reflection_loss / 20))
            
            reflection_phase = np.clip(azimuth + np.random.normal(0, 0.1), -np.pi, np.pi)
            
            amplitudes.append(max(reflection_amplitude, 1e-10))
            delays.append(reflection_delay)
            phases.append(reflection_phase)
        
        return np.array([amplitudes, delays, phases])
    

class PUF:
    def __init__(self, unique_id):
        """
        Simplified PUF with more predictable response
        """
        self.unique_id = unique_id
        seed = hash(unique_id) ^ int(unique_id.encode().hex(), 16)
        np.random.seed(seed % (2**32))
        
        # Simpler, more stable coefficients
        self.base_response = np.random.uniform(0.5, 2.0)
        #self.noise_level = 0.01
    
    def generate_response(self, challenge):
        """
        Simplified response generation with minimal noise
        """
        # Very simple transformation to make response more predictable
        transformed_challenge = np.sin(challenge * np.pi)
        
        # Consistent response with minimal noise
        # response = (self.base_response * transformed_challenge + 
        #             np.random.normal(0, self.noise_level))
        
        response = (self.base_response * transformed_challenge)
        
        return response


class Node:
    def __init__(self, node_id, is_legitimate=True, authenticator_pos=None):
        """
        Enhanced Node with constrained positioning
        """
        self.node_id = node_id
        self.is_legitimate = is_legitimate
        
        # Constrained positioning around authenticator
        if authenticator_pos is not None:
            # Small initialization radius (e.g., 10 units)
            initialization_radius = 10
            self.position = authenticator_pos + np.random.uniform(-initialization_radius, 
                                                                  initialization_radius, 3)
            self.position = np.clip(self.position, 0, 100)
        else:
            self.position = np.random.rand(3) * 100
        
        self.puf = PUF(node_id)
        self.shared_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.shared_key)
        
    def move(self, authenticator_pos):
        """
        Constrained movement around authenticator
        """
        # Small movement radius
        movement_radius = 5
        movement = np.random.uniform(-movement_radius, movement_radius, 3)
        new_position = self.position + movement
        
        # Constrain around authenticator's position
        new_position = np.clip(new_position, 
                                authenticator_pos - 20, 
                                authenticator_pos + 20)
        
        self.position = new_position
        
    def get_cir(self, authenticator_pos, channel):
        """
        CIR generation with legitimate/malicious behavior
        """
        if self.is_legitimate:
            return channel.calculate_cir(self.position, authenticator_pos)
        else:
            # Malicious node generates significantly different CIR
            fake_position = self.position + np.random.uniform(10, 20, 3)
            return channel.calculate_cir(fake_position, authenticator_pos)

class Authenticator:
    def __init__(self, cir_threshold=0.85):
        """
        More robust underwater authenticator with dynamic thresholding
        """
        self.position = np.array([50, 50, 50])
        self.channel = UnderwaterChannel()
        self.cir_database = {}
        self.puf_models = {}
        self.shared_keys = {}  # Database to store shared keys for each node
        self.thresholds = {}
        self.static_threshold = cir_threshold
        
        # New tracking for database recreation locations
        self.database_recreation_locations = {}
    
    def calculate_mtrrs(self, cir1, cir2):
        """
        More localized similarity calculation
        """
        amp1, delay1, phase1 = cir1
        amp2, delay2, phase2 = cir2
        
        eps = 1e-10
        
        # More conservative amplitude similarity
        amp1_norm = (amp1 - np.mean(amp1)) / (np.std(amp1) + eps)
        amp2_norm = (amp2 - np.mean(amp2)) / (np.std(amp2) + eps)
        
        amp_similarity = np.dot(amp1_norm, amp2_norm) / (
            (np.linalg.norm(amp1_norm) * np.linalg.norm(amp2_norm)) + eps
        )
        
        # More stringent delay and phase difference calculations
        delay_diff = np.mean(np.abs(delay1 - delay2)) / (np.max(np.concatenate([delay1, delay2])) + eps)
        phase_diff = np.mean(np.abs(phase1 - phase2)) / (2 * np.pi)
        
        # Complex similarity score with penalty for variations
        similarity = (amp_similarity + 1) / 2  # Normalize to [0, 1]
        penalty = (delay_diff + phase_diff) * 0.5  # Penalize temporal and phase variations
        
        # More conservative final score
        final_score = max(similarity - penalty, 0)
        
        return final_score

    def initialize_node(self, node_id, node, num_cir_samples=15):
        """
        More robust initialization with static threshold and shared key generation
        """
        # Initialize tracking for this node
        self.database_recreation_locations[node_id] = []
        
        # Reset database and initialize
        self.cir_database[node_id] = []
        self.shared_keys[node_id] = node.shared_key  # Store the shared key
        positions = []
        
        # Collect CIR samples with more variability
        print("Collecting CIR samples...")
        for i in range(num_cir_samples):
            positions.append(node.position.copy())
            cir = node.get_cir(self.position, self.channel)
            self.cir_database[node_id].append(cir)
            node.move(self.position)
        
        print("\nTraining PUF model...")
        
        # Simplified PUF training with single challenge
        challenges = np.array([0.5])  # Single, simple challenge
        responses = np.array([node.puf.generate_response(c) for c in challenges])

        # More robust model training
        puf_model = RandomForestRegressor(
            n_estimators=100,  # Reduced from previous implementation
            max_depth=10,      # Simplified depth
            random_state=42
        )
        puf_model.fit(challenges.reshape(-1, 1), responses)
        self.puf_models[node_id] = puf_model
        
        # Use static threshold
        self.thresholds[node_id] = self.static_threshold
        
        self.print_cir_database(node_id, "Initial CIR Database")
        
        return positions

    def authenticate_node(self, node_id, node, attempt_num):
        """
        More rigorous authentication process with comprehensive verification
        """
        print(f"\nAuthentication Attempt #{attempt_num}")
        print(f"Node Type: {'Legitimate' if node.is_legitimate else 'Malicious'}")
        print(f"Node Position: {node.position}")
        current_cir = node.get_cir(self.position, self.channel)
        
        print(f"Current CIR Amplitudes (first 3 taps): {current_cir[0][:3]}...")
        
        # CIR Authentication
        scores = []
        for stored_cir in self.cir_database[node_id]:
            score = self.calculate_mtrrs(current_cir, stored_cir)
            scores.append(score)
        
        max_score = max(scores) if scores else 0
        
        print(f"MTRRS Score: {max_score:.4f} (Threshold: {self.thresholds[node_id]:.4f})")
        
        # CIR Authentication Success
        if max_score >= self.thresholds[node_id]:
            print("CIR Authentication: SUCCESS")
            return True, "CIR", None
        
        print("CIR Authentication: FAILED")
        print("Attempting PUF Authentication...")
        
        # Check if node has the correct shared key
        if node_id not in self.shared_keys or node.shared_key != self.shared_keys[node_id]:
            print("PUF Authentication: FAILED - Incorrect Shared Key")
            return False, None, None
        
        # Simplified PUF Authentication
        challenge = 0.5  # Single, simple challenge
        
        # Encrypt challenge with shared key
        cipher_suite = Fernet(self.shared_keys[node_id])
        encrypted_challenge = cipher_suite.encrypt(str(challenge).encode())
        
        try:
            # Decrypt challenge (simulating node's decryption)
            decrypted_challenge = float(cipher_suite.decrypt(encrypted_challenge).decode())
            
            # Generate response
            predicted_response = self.puf_models[node_id].predict([[decrypted_challenge]])[0]
            actual_response = node.puf.generate_response(decrypted_challenge)
            
            # More lenient verification
            relative_error = abs((predicted_response - actual_response) / 
                                  (abs(predicted_response) + 1e-10))
            
            if relative_error < 0.1:  # 10% tolerance
                print("PUF Authentication: SUCCESS")
                return True, "PUF", current_cir
        except Exception as e:
            print(f"PUF Authentication: FAILED - Encryption/Decryption Error: {e}")
        
        print("PUF Authentication: FAILED")
        return False, None, None

    def print_cir_database(self, node_id, title="Current CIR Database"):
        """Print detailed view of CIR database"""
        print(f"\n=== {title} for Node {node_id} ===")
        print(f"Number of CIR samples: {len(self.cir_database[node_id])}")
        print(f"Current threshold: {self.thresholds[node_id]:.4f}")
        print("\nSample CIR values (first 3 taps of each):")
        for i, cir in enumerate(self.cir_database[node_id]):
            print(f"CIR {i+1}: Amplitudes {cir[0][:3]}")

    def update_cir_database(self, node_id, new_cir, failed_position):
        """
        Update CIR database with comprehensive locality-based approach
        """
        print("\n=== Updating CIR Database ===")
        print("Current database state before update:")
        self.print_cir_database(node_id, "Pre-Update CIR Database")
        
        # Track database recreation locations
        # Include both the failed position and nearby positions
        database_locations = [failed_position]
        
        # Collect new CIR samples close to the failed authentication position
        current_node = Node(node_id)  # Create temporary node
        
        for _ in range(4):  # 4 additional samples
            # Constrain new positions to a small range around failed position
            nearby_pos = failed_position + np.random.uniform(-10, 10, 3)
            
            # Ensure position stays within bounds
            nearby_pos = np.clip(nearby_pos, 0, 100)
            
            # Get CIR for this nearby position
            current_node.position = nearby_pos
            cir_sample = current_node.get_cir(self.position, self.channel)
            
            # Add to database
            self.cir_database[node_id].append(cir_sample)
            database_locations.append(nearby_pos)
        
        # Store the locations for visualization
        self.database_recreation_locations[node_id].append(database_locations)
        
        # Retain the static threshold
        self.thresholds[node_id] = self.static_threshold
        
        print("\nUpdated database state:")
        self.print_cir_database(node_id, "Post-Update CIR Database")

def simulate_network(initialization_range=10, authentication_range=50, cir_threshold=0.85):
    # Create authenticator with configurable threshold
    authenticator = Authenticator(cir_threshold=cir_threshold)
    
    # Create nodes with more constrained initial positions
    legitimate_node = Node("node1", is_legitimate=True, authenticator_pos=authenticator.position)
    malicious_node = Node("node2", is_legitimate=False, authenticator_pos=authenticator.position)
    
    # Initialize legitimate node and get positions for visualization
    legitimate_positions = authenticator.initialize_node("legitimate", legitimate_node)
    
    # Visualization of initialization phase
    fig = plt.figure(figsize=(12, 6))
    
    # Initialization Phase Plot
    ax1 = fig.add_subplot(121, projection='3d')
    legitimate_positions = np.array(legitimate_positions)
    ax1.scatter(legitimate_positions[:,0], legitimate_positions[:,1], 
                legitimate_positions[:,2], c='b', label='Legitimate Node Path')
    ax1.scatter(authenticator.position[0], authenticator.position[1], 
                authenticator.position[2], c='r', s=100, label='Authenticator')
    
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    ax1.set_zlabel('Z')
    ax1.set_title('Initialization Phase')
    ax1.legend()
    
    # Authentication Phase Plot
    ax2 = fig.add_subplot(122, projection='3d')
    
    ax2.set_xlim(-100, 200)
    ax2.set_ylim(-100, 200)
    ax2.set_zlim(-100, 200)
    
    # Authentication phase simulation
    print("\n=== Starting Authentication Phase ===")
    num_legitimate_tests = 20
    num_malicious_tests = 80
    results = {
        'legitimate': {'CIR': 0, 'PUF': 0, 'Failed': 0, 'CIR_Updates': 0},
        'malicious': {'CIR': 0, 'PUF': 0, 'Failed': 0}
    }
    
    authentication_positions = {'legitimate': [], 'malicious': []}
    
    print("\n--- Testing Legitimate Node ---")
    np.random.seed()
    for i in range(num_legitimate_tests):
        # Precise positioning for legitimate nodes on one side of authenticator's YZ plane
        legitimate_node.position = authenticator.position + np.array([50, 50, 0]) + \
            np.random.uniform(-authentication_range, authentication_range, 3)
        legitimate_node.position[0] = np.clip(legitimate_node.position[0], 0, 100)
        
        authentication_positions['legitimate'].append(legitimate_node.position.copy())
        
        # First authentication attempt
        success, method, new_cir = authenticator.authenticate_node(
            "legitimate", legitimate_node, i+1
        )
        
        if success:
            results['legitimate'][method] += 1
            if method == "PUF" and new_cir is not None:
                print(f"\nSuccessful PUF Authentication at attempt {i+1}")
                # Pass the failed authentication position for locality-based update
                authenticator.update_cir_database("legitimate", new_cir, authentication_positions['legitimate'][-1])
                results['legitimate']['CIR_Updates'] += 1
        else:
            results['legitimate']['Failed'] += 1
    
    print("\n--- Testing Malicious Node ---")
    for i in range(num_malicious_tests):
        # Precise positioning for malicious nodes on opposite side of authenticator's YZ plane
        malicious_node.position = authenticator.position + np.array([-50, -50, 0]) + \
            np.random.uniform(-authentication_range, authentication_range, 3)
        malicious_node.position[0] = np.clip(malicious_node.position[0], 0, 100)
        
        authentication_positions['malicious'].append(malicious_node.position.copy())
        
        success, method, _ = authenticator.authenticate_node(
            "legitimate", malicious_node, i+1
        )
        
        if success:
            results['malicious'][method] += 1
        else:
            results['malicious']['Failed'] += 1
    
    # Authentication Phase Visualization
    legitimate_pos = np.array(authentication_positions['legitimate'])
    malicious_pos = np.array(authentication_positions['malicious'])
    
    ax2.scatter(legitimate_pos[:,0], legitimate_pos[:,1], legitimate_pos[:,2], 
                c='b', label='Legitimate Node Attempts')
    ax2.scatter(malicious_pos[:,0], malicious_pos[:,1], malicious_pos[:,2], 
                c='r', label='Malicious Node Attempts')
    ax2.scatter(authenticator.position[0], authenticator.position[1], 
                authenticator.position[2], c='g', s=100, label='Authenticator')
    
    ax2.set_xlabel('X')
    ax2.set_ylabel('Y')
    ax2.set_zlabel('Z')
    ax2.set_title('Authentication Phase')
    ax2.legend()
    
    plt.tight_layout()
    plt.show()
    
    
    # Visualization of database recreation locations
    fig = plt.figure(figsize=(12, 6))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot authenticator position
    ax.scatter(authenticator.position[0], authenticator.position[1], authenticator.position[2], 
               c='r', s=200, label='Authenticator')
    
    # Plot database recreation locations
    for node_id, locations_list in authenticator.database_recreation_locations.items():
        for locations in locations_list:
            # Convert to numpy array for easier plotting
            locations = np.array(locations)
            
            # Plot the failed position (first location) in a different color
            ax.scatter(locations[0,0], locations[0,1], locations[0,2], 
                       c='orange', s=150, marker='x', label='Failed Position')
            
            # Plot nearby locations
            ax.scatter(locations[1:,0], locations[1:,1], locations[1:,2], 
                       c='green', s=100, label='Nearby Locations')
    
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('CIR Database Recreation Locations')
    ax.legend()
    
    plt.tight_layout()
    plt.show()
    
    # Print results
    print("\nAuthentication Results:")
    print("\nLegitimate Node:")
    total_legitimate = sum(results['legitimate'].values()) - results['legitimate']['CIR_Updates']
    for method, count in results['legitimate'].items():
        if method != 'CIR_Updates':
            print(f"{method}: {count} ({count/total_legitimate*100:.2f}%)")
    print(f"CIR Database Updates: {results['legitimate']['CIR_Updates']}")
        
    print("\nMalicious Node:")
    total_malicious = sum(results['malicious'].values())
    for method, count in results['malicious'].items():
        print(f"{method}: {count} ({count/total_malicious*100:.2f}%)")
        
    # Calculate overall accuracy
    legitimate_accuracy = (results['legitimate']['CIR'] + 
                         results['legitimate']['PUF']) / num_legitimate_tests
    malicious_rejection = results['malicious']['Failed'] / num_malicious_tests
    
    print(f"\nOverall System Performance:")
    print(f"Legitimate Node Authentication Rate: {legitimate_accuracy*100:.2f}%")
    print(f"Malicious Node Rejection Rate: {malicious_rejection*100:.2f}%")
    print(f"CIR Database Updates: {results['legitimate']['CIR_Updates']}")
    

if __name__ == "__main__":
    simulate_network(cir_threshold=0.9)