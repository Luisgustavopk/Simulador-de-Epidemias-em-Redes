"""Representação de um contato não direcionado entre dois indivíduos."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .individuo import Individuo


@dataclass(slots=True, eq=False)
class Aresta:
    """Contato ponderado, sem laços, com referências aos dois indivíduos.

    O peso deve ser finito e não negativo. Valores acima de um são aceitos
    para representar intensidade de contato; sua conversão em probabilidade
    será responsabilidade do motor de simulação.

    Os nomes origem e destino identificam apenas as extremidades da conexão.
    O atributo ativa é independente dos indicadores de isolamento individuais.
    """

    origem: Individuo
    destino: Individuo
    peso: float = 1.0
    ativa: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.origem, Individuo) or not isinstance(
            self.destino, Individuo
        ):
            raise TypeError("As extremidades da aresta devem ser indivíduos.")
        if self.origem.id == self.destino.id:
            raise ValueError("Uma aresta não pode ligar um indivíduo a ele mesmo.")
        if isinstance(self.peso, bool) or not isinstance(self.peso, (int, float)):
            raise TypeError("O peso da aresta deve ser um número real.")
        try:
            peso = float(self.peso)
        except OverflowError as exc:
            raise ValueError("O peso da aresta deve ser finito.") from exc
        if not isfinite(peso) or peso < 0:
            raise ValueError("O peso da aresta deve ser finito e não negativo.")
        if not isinstance(self.ativa, bool):
            raise TypeError("O atributo ativa deve ser booleano.")
        self.peso = peso

    def outro_extremo(self, id_individuo: int) -> Individuo:
        """Retorna o vizinho de um dos extremos, consultado pelo identificador."""
        if isinstance(id_individuo, bool) or not isinstance(id_individuo, int):
            raise TypeError("O identificador do indivíduo deve ser inteiro.")
        if id_individuo == self.origem.id:
            return self.destino
        if id_individuo == self.destino.id:
            return self.origem
        raise ValueError("O indivíduo informado não pertence a esta aresta.")
