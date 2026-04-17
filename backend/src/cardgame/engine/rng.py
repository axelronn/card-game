import random
from dataclasses import dataclass


@dataclass
class SeededRng:
    # Deterministic RNG wrapper. Every match carries one of these so replays and
    # tests are reproducible.

    seed: int
    _rng: random.Random | None = None

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    def randint(self, *, low: int, high: int) -> int:
        assert self._rng is not None
        return self._rng.randint(low, high)

    def choice[T](self, *, items: list[T]) -> T:
        assert self._rng is not None
        return self._rng.choice(items)

    def shuffle[T](self, *, items: list[T]) -> list[T]:
        assert self._rng is not None
        copy = list(items)
        self._rng.shuffle(copy)
        return copy
