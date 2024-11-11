import numpy as np

def generate_puf_response(challenge, weights):
    return 1 if np.dot(challenge, weights) > 0 else 0

def authenticate_puf(challenge, stored_response):
    weights = np.random.randn(64)
    response = generate_puf_response(challenge, weights)
    return response == stored_response
