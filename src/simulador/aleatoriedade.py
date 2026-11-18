from random import Random
from collections.abc import Sequence


class GeradorAleatorio:
    def __init__(self, semente: int) -> None:
        if isinstance(semente, bool) or not isinstance(semente, int):
            raise TypeError("A semente deve ser um inteiro.")
        self._semente = semente
        self._gerador = Random(semente)

    @property
    def semente(self) -> int:
        return self._semente

    def uniforme(self) -> float:
        return self._gerador.random()

    def amostrar_ids(self, ids: Sequence[int], quantidade: int) -> tuple[int, ...]:
        return tuple(sorted(self._gerador.sample(sorted(ids), quantidade)))
