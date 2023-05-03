from typing import Callable, TypeVar

T = TypeVar("T")
K = TypeVar("K")


def deduplicate_list(items: list[T], key: Callable[[T], K]) -> list[T]:
    unique_values: dict[K, T] = {}
    for item in items:
        k = key(item)
        if k not in unique_values:
            unique_values[k] = item
    return list(unique_values.values())
