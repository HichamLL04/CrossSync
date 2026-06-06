from src.decision_engine import parse_dtw_path

def test_parse_dtw_path_grouping():
    # Path mapping: A-indices to B-indices
    path = [(0, 0), (0, 1), (1, 2), (2, 3), (3, 3)]
    groups = parse_dtw_path(path)
    # Expected:
    # Group 1: A[0] -> B[0], B[1] (1 to many - Split)
    # Group 2: A[1] -> B[2] (1 to 1 - Keep)
    # Group 3: A[2], A[3] -> B[3] (many to 1 - Join)
    assert groups == [
        {"type": "split", "source_indices": [0], "target_indices": [0, 1]},
        {"type": "keep", "source_indices": [1], "target_indices": [2]},
        {"type": "join", "source_indices": [2, 3], "target_indices": [3]}
    ]
