"""Indivíduo com identidade estável e transições epidemiológicas controladas."""

from enum import Enum


class EstadoSIR(str, Enum):
    SUSCETIVEL = "S"
    INFECTADO = "I"
    RECUPERADO = "R"


class Individuo:
    """Começa suscetível; estado e isolamento mudam apenas pelas operações."""

    __slots__ = ("_id", "_estado", "_isolamento", "_dia_inicio_infeccao")

    def __init__(self, id: int) -> None:
        if isinstance(id, bool) or not isinstance(id, int):
            raise TypeError("O identificador do indivíduo deve ser inteiro.")
        self._id = id
        self._estado = EstadoSIR.SUSCETIVEL
        self._isolamento = False
        self._dia_inicio_infeccao: int | None = None

    @property
    def id(self) -> int:
        return self._id

    @property
    def estado(self) -> EstadoSIR:
        return self._estado

    @property
    def isolamento(self) -> bool:
        return self._isolamento

    @property
    def dia_inicio_infeccao(self) -> int | None:
        return self._dia_inicio_infeccao

    def infectar(self, passo: int) -> None:
        """Aplica S → I e registra o passo, inclusive zero."""
        if isinstance(passo, bool) or not isinstance(passo, int):
            raise TypeError("O passo da infecção deve ser inteiro.")
        if passo < 0:
            raise ValueError("O passo da infecção não pode ser negativo.")
        if self._estado is not EstadoSIR.SUSCETIVEL:
            raise ValueError("Somente indivíduos suscetíveis podem ser infectados.")
        self._estado = EstadoSIR.INFECTADO
        self._dia_inicio_infeccao = passo

    def recuperar(self) -> None:
        """Aplica I → R, preservando o histórico e o isolamento."""
        if self._estado is not EstadoSIR.INFECTADO:
            raise ValueError("Somente indivíduos infectados podem se recuperar.")
        self._estado = EstadoSIR.RECUPERADO

    def isolar(self) -> None:
        """Isola em qualquer estado; chamadas repetidas mantêm a condição."""
        self._isolamento = True
