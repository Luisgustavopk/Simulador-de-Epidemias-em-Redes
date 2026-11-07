"""Representação de um indivíduo e de seu estado epidemiológico."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias

EstadoEpidemiologico: TypeAlias = Literal["S", "I", "R"]


def _validar_dia(dia: int) -> None:
    if isinstance(dia, bool) or not isinstance(dia, int):
        raise TypeError("O dia da infecção deve ser um número inteiro.")
    if dia < 0:
        raise ValueError("O dia da infecção não pode ser negativo.")


@dataclass(slots=True, eq=False)
class Individuo:
    """Indivíduo da rede, com isolamento separado do estado SIR.

    O identificador deve ser inteiro; sua unicidade na rede será controlada
    pelo grafo. O dia da infecção pode ser desconhecido para indivíduos
    inicialmente infectados ou recuperados.
    """

    id: int
    estado: EstadoEpidemiologico = "S"
    isolamento: bool = False
    dia_inicio_infeccao: int | None = None

    def __post_init__(self) -> None:
        if isinstance(self.id, bool) or not isinstance(self.id, int):
            raise TypeError("O identificador do indivíduo deve ser inteiro.")
        if not isinstance(self.estado, str):
            raise TypeError("O estado epidemiológico deve ser uma string.")
        if self.estado not in ("S", "I", "R"):
            raise ValueError("O estado epidemiológico deve ser S, I ou R.")
        if not isinstance(self.isolamento, bool):
            raise TypeError("O atributo isolamento deve ser booleano.")
        if self.dia_inicio_infeccao is not None:
            _validar_dia(self.dia_inicio_infeccao)
            if self.estado == "S":
                raise ValueError("Um indivíduo suscetível não possui dia de infecção.")

    def infectar(self, dia: int) -> None:
        """Altera S para I e registra o dia, sem realizar sorteio de contágio."""
        _validar_dia(dia)
        if self.estado != "S":
            raise ValueError("Somente indivíduos suscetíveis podem ser infectados.")
        self.estado = "I"
        self.dia_inicio_infeccao = dia

    def recuperar(self) -> None:
        """Altera I para R, preservando o dia da infecção e o isolamento."""
        if self.estado != "I":
            raise ValueError("Somente indivíduos infectados podem se recuperar.")
        self.estado = "R"

    def isolar(self) -> None:
        """Marca o indivíduo como isolado, mantendo o estado epidemiológico."""
        self.isolamento = True

    def liberar_isolamento(self) -> None:
        """Retira o isolamento, mantendo o estado epidemiológico."""
        self.isolamento = False
