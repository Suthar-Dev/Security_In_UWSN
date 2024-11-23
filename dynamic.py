import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.spatial.distance import euclidean
import random
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import accuracy_score
from cryptography.fernet import Fernet
import time

class UnderwaterChannel:
    def __init__(self):
        self.sound_speed = 1500  # m/s in water
        self.attenuation_coeff = 0.1  # dB/m
        self.reflection_coeff = 0.3
        self.num_taps = 10
        
    def calculate_cir(self, transmitter_pos, receiver_pos):
        distance = euclidean(transmitter_pos, receiver_pos)
        delay = distance / self.sound_speed
        
        # Make CIR more sensitive to position changes
        direction_vector = receiver_pos - transmitter_pos
        angle = np.arctan2(direction_vector[1], direction_vector[0])
        
        # Calculate direct path amplitude with more realistic attenuation
        attenuation = np.exp(-self.attenuation_coeff * distance)
        
        # Add directional sensitivity
        attenuation *= (1 + 0.3 * np.cos(angle))
        
        amplitudes = []
        phases = []
        
        # Direct path
        amplitudes.append(attenuation)
        phases.append(angle + np.random.normal(0, 0.1))
        
        # Multipath components with more variation
        for i in range(1, self.num_taps):
            # Add more realistic multipath based on position
            reflection_distance = distance + np.random.uniform(0, 20)
            reflection_angle = angle + np.random.normal(0, 0.5)
            
            reflection_attenuation = (
                attenuation * self.reflection_coeff * 
                np.exp(-self.attenuation_coeff * (reflection_distance - distance)) *
                (1 + 0.2 * np.cos(reflection_angle))
            )
            
            # Add environmental variations
            reflection_attenuation *= np.random.uniform(0.3, 1.0)
            amplitudes.append(reflection_attenuation)
            phases.append(reflection_angle + np.random.normal(0, 0.2))
            
        return np.array([amplitudes, phases])

class PUF:
    def __init__(self, unique_id):
        self.challenge_bits = 64
        self.unique_id = unique_id
        
    def generate_response(self, challenge):
        np.random.seed(hash(str(self.unique_id)) % 2**32)
        response = np.dot(challenge, np.random.rand(len(challenge)))
        response += np.random.normal(0, 0.01)
        return response

class Node:
    def __init__(self, node_id, is_legitimate=True):
        self.node_id = node_id
        self.is_legitimate = is_legitimate
        self.position = np.random.rand(3) * 100
        self.puf = PUF(node_id)
        self.shared_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.shared_key)
        
    def move(self):
        # More significant movement to ensure CIR changes
        movement = np.random.randn(3) * 5  # Increased movement range
        new_position = self.position + movement
        new_position = np.clip(new_position, 0, 100)
        self.position = new_position
        
    def get_cir(self, authenticator_pos, channel):
        if self.is_legitimate:
            return channel.calculate_cir(self.position, authenticator_pos)
        else:
            # Malicious node tries to generate fake CIR
            fake_position = self.position + np.random.randn(3) * 8
            return channel.calculate_cir(fake_position, authenticator_pos)

class Authenticator:
    def __init__(self):
        self.position = np.array([50, 50, 50])
        self.channel = UnderwaterChannel()
        self.cir_database = {}
        self.puf_models = {}
        self.shared_keys = {}
        self.thresholds = {}
        
    def initialize_node(self, node_id, node, num_cir_samples=15):
        print(f"\nInitializing node {node_id}")
        self.cir_database[node_id] = []
        positions = []
        
        print("Collecting CIR samples...")
        for i in range(num_cir_samples):
            positions.append(node.position.copy())
            cir = node.get_cir(self.position, self.channel)
            self.cir_database[node_id].append(cir)
            print(f"Sample {i+1}: CIR Amplitudes: {cir[0][:3]}... (first 3 taps)")
            node.move()
            
        print("\nTraining PUF model...")
        challenges = np.random.rand(100, node.puf.challenge_bits)
        responses = np.array([node.puf.generate_response(c) for c in challenges])
        
        puf_model = RandomForestRegressor(n_estimators=100)
        puf_model.fit(challenges, responses)
        self.puf_models[node_id] = puf_model
        
        self.shared_keys[node_id] = node.shared_key
        
        # Calculate threshold with more stringent criteria
        scores = []
        for i, cir1 in enumerate(self.cir_database[node_id]):
            for j, cir2 in enumerate(self.cir_database[node_id]):
                if i != j:
                    scores.append(self.calculate_mtrrs(cir1, cir2))
        
        # More stringent threshold
        self.thresholds[node_id] = np.mean(scores) - 0.3 * np.std(scores)
        print(f"Set MTRRS threshold: {self.thresholds[node_id]:.4f}")
        
        return positions
        
    def calculate_mtrrs(self, cir1, cir2):
        amp1, phase1 = cir1
        amp2, phase2 = cir2
        
        amp_correlation = np.corrcoef(amp1, amp2)[0,1]
        phase_diff = np.mean(np.abs(phase1 - phase2))
        
        return amp_correlation * (1 - phase_diff / (2 * np.pi))
    
    def authenticate_node(self, node_id, node, attempt_num):
        print(f"\nAuthentication Attempt #{attempt_num}")
        print(f"Node Type: {'Legitimate' if node.is_legitimate else 'Malicious'}")
        print(f"Node Position: {node.position}")
        
        current_cir = node.get_cir(self.position, self.channel)
        print(f"Current CIR Amplitudes (first 3 taps): {current_cir[0][:3]}...")
        
        max_score = -float('inf')
        for stored_cir in self.cir_database[node_id]:
            score = self.calculate_mtrrs(current_cir, stored_cir)
            max_score = max(max_score, score)
        
        print(f"MTRRS Score: {max_score:.4f} (Threshold: {self.thresholds[node_id]:.4f})")
        
        if max_score >= self.thresholds[node_id]:
            print("CIR Authentication: SUCCESS")
            return True, "CIR"
        
        print("CIR Authentication: FAILED")
        print("Attempting PUF Authentication...")
            
        challenge = np.random.rand(node.puf.challenge_bits)
        
        try:
            actual_response = node.puf.generate_response(challenge)
            predicted_response = self.puf_models[node_id].predict([challenge])[0]
            
            response_diff = abs(actual_response - predicted_response)
            print(f"PUF Response Difference: {response_diff:.4f}")
            
            if response_diff < 0.1:
                print("PUF Authentication: SUCCESS")
                return True, "PUF"
            else:
                print("PUF Authentication: FAILED")
                
        except Exception as e:
            print(f"PUF Authentication Error: {e}")
            
        return False, None

def simulate_network():
    # Create nodes
    legitimate_node = Node("node1", is_legitimate=True)
    malicious_node = Node("node2", is_legitimate=False)
    authenticator = Authenticator()
    
    # Initialize legitimate node and get positions for visualization
    legitimate_positions = authenticator.initialize_node("legitimate", legitimate_node)
    
    # Visualization of initialization phase
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    legitimate_positions = np.array(legitimate_positions)
    ax.scatter(legitimate_positions[:,0], legitimate_positions[:,1], 
              legitimate_positions[:,2], c='b', label='Legitimate Node Path')
    ax.scatter(authenticator.position[0], authenticator.position[1], 
              authenticator.position[2], c='r', s=100, label='Authenticator')
    
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.legend()
    plt.title('Initialization Phase')
    plt.show()
    
    # Authentication phase simulation
    print("\n=== Starting Authentication Phase ===")
    num_tests = 5
    results = {
        'legitimate': {'CIR': 0, 'PUF': 0, 'Failed': 0},
        'malicious': {'CIR': 0, 'PUF': 0, 'Failed': 0}
    }
    
    authentication_positions = {'legitimate': [], 'malicious': []}
    
    print("\n--- Testing Legitimate Node ---")
    for i in range(num_tests):
        legitimate_node.move()
        authentication_positions['legitimate'].append(legitimate_node.position.copy())
        success, method = authenticator.authenticate_node("legitimate", legitimate_node, i+1)
        if success:
            results['legitimate'][method] += 1
        else:
            results['legitimate']['Failed'] += 1
            
    print("\n--- Testing Malicious Node ---")
    for i in range(num_tests):
        malicious_node.move()
        authentication_positions['malicious'].append(malicious_node.position.copy())
        success, method = authenticator.authenticate_node("legitimate", malicious_node, i+1)
        if success:
            results['malicious'][method] += 1
        else:
            results['malicious']['Failed'] += 1
    
    # Visualization of authentication phase
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    legitimate_pos = np.array(authentication_positions['legitimate'])
    malicious_pos = np.array(authentication_positions['malicious'])
    
    ax.scatter(legitimate_pos[:,0], legitimate_pos[:,1], legitimate_pos[:,2], 
              c='b', label='Legitimate Node Attempts')
    ax.scatter(malicious_pos[:,0], malicious_pos[:,1], malicious_pos[:,2], 
              c='r', label='Malicious Node Attempts')
    ax.scatter(authenticator.position[0], authenticator.position[1], 
              authenticator.position[2], c='g', s=100, label='Authenticator')
    
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.legend()
    plt.title('Authentication Phase')
    plt.show()
    
    # Print results
    print("\nAuthentication Results:")
    print("\nLegitimate Node:")
    total_legitimate = sum(results['legitimate'].values())
    for method, count in results['legitimate'].items():
        print(f"{method}: {count} ({count/total_legitimate*100:.2f}%)")
        
    print("\nMalicious Node:")
    total_malicious = sum(results['malicious'].values())
    for method, count in results['malicious'].items():
        print(f"{method}: {count} ({count/total_malicious*100:.2f}%)")
        
    # Calculate overall accuracy
    legitimate_accuracy = (results['legitimate']['CIR'] + 
                         results['legitimate']['PUF']) / num_tests
    malicious_rejection = results['malicious']['Failed'] / num_tests
    
    print(f"\nOverall System Performance:")
    print(f"Legitimate Node Authentication Rate: {legitimate_accuracy*100:.2f}%")
    print(f"Malicious Node Rejection Rate: {malicious_rejection*100:.2f}%")

if __name__ == "__main__":
    simulate_network()