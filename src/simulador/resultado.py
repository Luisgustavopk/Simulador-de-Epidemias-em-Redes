from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from simulador.configuracao import ConfiguracaoSimulacao
    from simulador.metricas import MetricasEpidemia
    from simulador.simulacao import RegistroPasso


@dataclass(frozen=True, slots=True)
class ResultadoSimulacao:
    configuracao: ConfiguracaoSimulacao
    historico: tuple[RegistroPasso, ...]
    metricas: MetricasEpidemia
    motivo_termino: str
    populacao_inicial: int
    repeticao: int | None = None

    @property
    def revisao_rede(self) -> int:
        return self.configuracao.revisao_rede

    @property
    def semente_epidemia(self) -> int:
        return self.configuracao.semente_epidemia

    @property
    def semente_isolamento(self) -> int:
        return self.configuracao.semente_isolamento

    @property
    def pico_infectados(self) -> int:
        return self.metricas.pico_infectados

    @property
    def passo_pico(self) -> int:
        return self.metricas.passo_pico

    @property
    def pico_proporcional(self) -> float:
        return self.metricas.pico_proporcional

    @property
    def fracao_acumulada(self) -> float:
        return self.metricas.fracao_acumulada

    @property
    def fracao_final_recuperados(self) -> float:
        return self.metricas.fracao_final_recuperados

    @property
    def ocorreu_infeccao(self) -> bool:
        return self.metricas.ocorreu_infeccao

    @property
    def horizonte_observado(self) -> int:
        return self.historico[-1].passo

    @property
    def duracao_extincao(self) -> int | None:
        return self.metricas.duracao_extincao

    @property
    def censurada(self) -> bool:
        return self.motivo_termino == 'limite_passos'
