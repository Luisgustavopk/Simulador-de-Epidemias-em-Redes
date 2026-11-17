"""Fluxos pseudoaleatórios privados, sem usar o estado global de random."""

from random import Random
from collections.abc import Sequence


class GeradorAleatorio:
    """Mantém a semente inicial e uma instância cujo estado avança a cada uso.

    Cada finalidade recebe sua própria instância e semente explícita. Sementes
    iguais não acoplam os objetos: consumir um fluxo não avança os demais.
    """

    def __init__(self, semente: int) -> None:
        if isinstance(semente, bool) or not isinstance(semente, int):
            raise TypeError("A semente deve ser um inteiro.")
        self._semente = semente
        self._gerador = Random(semente)

    @property
    def semente(self) -> int:
        """Condição inicial; o estado evolutivo permanece no gerador privado."""
        return self._semente

    def uniforme(self) -> float:
        """Sorteia em [0, 1), sem reinicializar o estado."""
        return self._gerador.random()

    def amostrar_ids(self, ids: Sequence[int], quantidade: int) -> tuple[int, ...]:
        """Amostra sem reposição; a ordenação elimina a ordem de cadastro."""
        return tuple(sorted(self._gerador.sample(sorted(ids), quantidade)))
