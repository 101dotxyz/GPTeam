import os
import hashlib
from typing import Callable, TypeVar
from uuid import UUID
import socket

T = TypeVar("T")
K = TypeVar("K")


def deduplicate_list(items: list[T], key: Callable[[T], K]) -> list[T]:
    unique_values: dict[K, T] = {}
    for item in items:
        k = key(item)
        if k not in unique_values:
            unique_values[k] = item
    return list(unique_values.values())


def seed_uuid(seed: str) -> str:
    return str(UUID(hashlib.sha1(seed.encode()).hexdigest()[:32]))


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def get_open_port():
    port = os.getenv("PORT", "5000")
    while is_port_in_use(port):
        port += 1
    return port
