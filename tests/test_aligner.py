import numpy as np
from src.aligner import align_sequences

def test_align_sequences_simple():
    # Simple cost matrix where diagonal has lowest cost (highest similarity)
    # cost = 1.0 - similarity
    cost_matrix = np.array([
        [0.1, 0.9, 0.9],
        [0.9, 0.1, 0.9],
        [0.9, 0.9, 0.2]
    ])
    path = align_sequences(cost_matrix)
    # Expected path: (0,0) -> (1,1) -> (2,2)
    assert path == [(0, 0), (1, 1), (2, 2)]

def test_align_sequences_one_to_many():
    cost_matrix = np.array([
        [0.1, 0.2, 0.9],
        [0.9, 0.9, 0.1]
    ])
    path = align_sequences(cost_matrix)
    # Expected path matching indices:
    # A[0] aligns with B[0] and B[1]
    # A[1] aligns with B[2]
    assert path == [(0, 0), (0, 1), (1, 2)]
