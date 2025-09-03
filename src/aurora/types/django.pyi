from typing import TypeVar

_K = TypeVar("_K")

type _ListOrTuple[_K] = list[_K] | tuple[_K, ...] | tuple[()]
