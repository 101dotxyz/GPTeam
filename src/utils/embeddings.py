import numpy as np
import openai

from ..utils.cache import json_cache


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    similarity = dot_product / (norm_a * norm_b)
    return similarity


async def get_embedding(text: str, model="text-embedding-ada-002") -> np.ndarray:
    response: list[float] = await openai.Embedding.acreate(
        input=[text.replace("\n", " ")], model=model
    )

    embedding = response["data"][0]["embedding"]

    return np.array(embedding)


def get_embedding_sync(text: str, model="text-embedding-ada-002"):
    response: list[float] = openai.Embedding.create(
        input=[text.replace("\n", " ")], model=model
    )

    embedding = response["data"][0]["embedding"]

    return embedding
