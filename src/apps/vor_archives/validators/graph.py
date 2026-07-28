from typing import Protocol, Iterable, TypeAlias
from itertools import chain
from collections import deque

NodeKeyPair: TypeAlias = tuple[int, int]
class RelationStrategy(Protocol):
    def __call__(self, key: NodeKeyPair) -> Iterable[NodeKeyPair]: 
        ...


class CycleChecker:
    def __init__(self, items_out: RelationStrategy, items_in: RelationStrategy):
        self.__items_out = items_out
        self.__items_in = items_in

    def check(self, source: NodeKeyPair, target: NodeKeyPair):
        """
        Проверяет, существует ли путь от source к target в текущем графе.
        """
        if target == source:
            return True
        visited = set()
        queue = deque([source])

        while queue:
            key = queue.popleft()
            if key in visited:
                continue
            visited.add(key)

            items = chain(self.__items_out(key), self.__items_in(key))
            for item in items:
                if item == target:
                    return True
                if item not in visited:
                    queue.append(item)
        return False
