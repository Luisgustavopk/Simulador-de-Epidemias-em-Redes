"""Contato não direcionado com intensidade normalizada e extremos estáveis."""

from .individuo import Individuo


class Aresta:
    """Consulta o isolamento dos extremos sem armazenar disponibilidade redundante."""

    __slots__ = ("_origem", "_destino", "_peso")

    def __init__(
        self, origem: Individuo, destino: Individuo, peso: float = 1.0
    ) -> None:
        if not isinstance(origem, Individuo) or not isinstance(destino, Individuo):
            raise TypeError("As extremidades da aresta devem ser indivíduos.")
        if origem.id == destino.id:
            raise ValueError("Uma aresta não pode ligar um indivíduo a ele mesmo.")
        if isinstance(peso, bool) or not isinstance(peso, (int, float)):
            raise TypeError("O peso da aresta deve ser um número real.")
        if not 0 <= peso <= 1:
            raise ValueError("O peso deve ser finito e estar entre 0 e 1.")
        self._origem, self._destino, self._peso = origem, destino, float(peso)

    @property
    def origem(self) -> Individuo:
        return self._origem

    @property
    def destino(self) -> Individuo:
        return self._destino

    @property
    def extremos(self) -> frozenset[Individuo]:
        return frozenset((self._origem, self._destino))

    @property
    def peso(self) -> float:
        return self._peso

    @property
    def ativa(self) -> bool:
        return not (self._origem.isolamento or self._destino.isolamento)

    def outro_extremo(self, individuo: Individuo) -> Individuo:
        """Consulta pelo próprio objeto, rejeitando cópias com o mesmo ID."""
        if not isinstance(individuo, Individuo):
            raise TypeError("O extremo deve ser uma instância de Individuo.")
        if individuo is self._origem:
            return self._destino
        if individuo is self._destino:
            return self._origem
        raise ValueError("O indivíduo informado não pertence a esta aresta.")
