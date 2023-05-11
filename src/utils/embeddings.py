import numpy as np
import openai
import openai.error
import asyncio

from ..utils.cache import json_cache


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    similarity = dot_product / (norm_a * norm_b)
    return similarity


async def get_embedding(text: str, model="text-embedding-ada-002", max_retries=3) -> np.ndarray:
    for attempt in range(max_retries):
        try:
            response: list[float] = await openai.Embedding.acreate(
                input=[text.replace("\n", " ")], model=model
            )

            embedding = response["data"][0]["embedding"]

            return np.array(embedding)
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(1)  # Wait for 1 second before retrying
            else:
                raise e  # If all retries failed, raise the exception
