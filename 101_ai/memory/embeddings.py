import numpy as np
import openai


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    similarity = dot_product / (norm_a * norm_b)
    return similarity


def get_embedding(text: str, model="text-embedding-ada-002") -> np.ndarray:
    embedding: list[float] = openai.Embedding.create(
        input=[text.replace("\n", " ")], model=model
    )["data"][0]["embedding"]

    return np.array(embedding)
