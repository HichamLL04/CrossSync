import numpy as np
from sentence_transformers import SentenceTransformer

class SemanticAligner:
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        self.model = SentenceTransformer(model_name)

    def get_embeddings(self, sentences: list[str]) -> np.ndarray:
        if not sentences:
            return np.array([])
        return self.model.encode(sentences, show_progress_bar=False)

    def compute_cost_matrix(self, embs_a: np.ndarray, embs_b: np.ndarray) -> np.ndarray:
        # Compute cosine similarity
        norm_a = embs_a / np.linalg.norm(embs_a, axis=1, keepdims=True)
        norm_b = embs_b / np.linalg.norm(embs_b, axis=1, keepdims=True)
        similarity = np.dot(norm_a, norm_b.T)
        # Cost is 1.0 - similarity (bounded between 0 and 2)
        return 1.0 - similarity

def align_sequences(cost_matrix: np.ndarray) -> list[tuple[int, int]]:
    n, m = cost_matrix.shape
    dp = np.full((n, m), np.inf)
    dp[0, 0] = cost_matrix[0, 0]

    # DP Table computation
    for i in range(n):
        for j in range(m):
            if i == 0 and j == 0:
                continue
            costs = []
            if i > 0:
                costs.append(dp[i - 1, j])
            if j > 0:
                costs.append(dp[i, j - 1])
            if i > 0 and j > 0:
                costs.append(dp[i - 1, j - 1])
            dp[i, j] = cost_matrix[i, j] + min(costs)

    # Backtracking
    path = []
    i, j = n - 1, m - 1
    while i > 0 or j > 0:
        path.append((i, j))
        options = []
        if i > 0 and j > 0:
            options.append((dp[i - 1, j - 1], (i - 1, j - 1)))
        if i > 0:
            options.append((dp[i - 1, j], (i - 1, j)))
        if j > 0:
            options.append((dp[i, j - 1], (i, j - 1)))
        
        # Pick option with minimum cost
        _, next_step = min(options, key=lambda x: x[0])
        i, j = next_step
    path.append((0, 0))
    path.reverse()
    return path
