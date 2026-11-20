from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass, replace
from statistics import mean, stdev
from typing import Literal

from simulador.carga_rede import RedeDisponivel
from simulador.configuracao import (
    ConfiguracaoIntervencao, ConfiguracaoSimulacao, ErroConfiguracao, ProblemaConfiguracao,
)
from simulador.rede_contatos import RedeContatos

Cenario = Literal['sem_intervencao', 'aleatoria', 'grau']
Motivo = Literal['extincao', 'limite_passos']
CENARIOS: tuple[Cenario, ...] = ('sem_intervencao', 'aleatoria', 'grau')
INDICADORES = (
    'pico_infectados', 'pico_proporcional', 'passo_pico', 'fracao_acumulada',
    'horizonte_observado', 'duracao_extincao', 'fracao_final_recuperados',
)
INDICADORES_REDUCAO = ('pico_infectados', 'pico_proporcional', 'fracao_acumulada')


@dataclass(frozen=True, slots=True)
class PedidoComparacao:
    configuracao: ConfiguracaoSimulacao
    repeticoes: int

    def validar(self, referencia: RedeDisponivel) -> ConfiguracaoIntervencao:
        problemas = self.configuracao.validar(referencia.rede, referencia.revisao)
        if type(self.repeticoes) is not int or self.repeticoes <= 0:
            problemas.append(ProblemaConfiguracao('repeticoes', 'Informe um número inteiro positivo de repetições.'))
        intervencao = self.configuracao.intervencao
        if intervencao is None:
            problemas.append(ProblemaConfiguracao('intervencao', 'Ative e configure a intervenção para comparar as estratégias.'))
        if problemas or intervencao is None:
            raise ErroConfiguracao(problemas)
        return intervencao


@dataclass(frozen=True, slots=True)
class ResultadoIndividual:
    populacao_inicial: int
    pico_infectados: int
    passo_pico: int
    fracao_acumulada: float
    horizonte_observado: int
    duracao_extincao: int | None
    motivo_termino: Motivo
    historico: tuple[object, ...]

    @property
    def pico_proporcional(self) -> float:
        return (
            self.pico_infectados / self.populacao_inicial
            if self.populacao_inicial else 0.0
        )

    @property
    def censurada(self) -> bool:
        return self.motivo_termino == 'limite_passos'

    @property
    def fracao_final_recuperados(self) -> float:
        if not self.populacao_inicial or not self.historico:
            return 0.0
        registro = self.historico[-1]
        return registro.recuperados / self.populacao_inicial

    @property
    def ocorreu_infeccao(self) -> bool:
        return any(registro.infectados > 0 for registro in self.historico)


@dataclass(frozen=True, slots=True)
class ExecucaoComparada:
    repeticao: int
    cenario: Cenario
    configuracao: ConfiguracaoSimulacao
    resultado: ResultadoIndividual


@dataclass(frozen=True, slots=True)
class Estatistica:
    n: int
    ausentes: int
    media: float | None
    desvio_padrao: float | None


@dataclass(frozen=True, slots=True)
class ResumoCenario:
    metricas: dict[str, Estatistica]
    diferencas: dict[str, Estatistica]
    reducoes: dict[str, Estatistica]
    censuradas: int
    proporcao_censuradas: float
    motivos_termino: dict[Motivo, int]


@dataclass(frozen=True, slots=True)
class ResultadoComparacao:
    pedido: PedidoComparacao
    revisao_rede: int
    origem_rede: dict[str, object]
    execucoes: tuple[ExecucaoComparada, ...]
    resumo: dict[Cenario, ResumoCenario]


class ErroExecucaoComparacao(RuntimeError):
    def __init__(self, repeticao: int, cenario: Cenario) -> None:
        self.repeticao = repeticao
        self.cenario = cenario
        super().__init__(f'Falha na repetição {repeticao}, cenário {cenario}.')


def _estatistica(valores: list[int | float | None]) -> Estatistica:
    presentes = [valor for valor in valores if valor is not None]
    n = len(presentes)
    return Estatistica(
        n, len(valores) - n,
        float(mean(presentes)) if n else None,
        stdev(presentes) if n >= 2 else None,
    )


def _diferenca(referencia: int | float | None, comparada: int | float | None) -> int | float | None:
    if referencia is None or comparada is None:
        return None
    return referencia - comparada


def _reducao(referencia: int | float | None, comparada: int | float | None) -> float | None:
    if referencia is None or referencia <= 0 or comparada is None:
        return None
    return (referencia - comparada) / referencia


def _consolidar(execucoes: list[ExecucaoComparada]) -> dict[Cenario, ResumoCenario]:
    referencia = {e.repeticao: e.resultado for e in execucoes if e.cenario == 'sem_intervencao'}
    resumos: dict[Cenario, ResumoCenario] = {}
    for cenario in CENARIOS:
        grupo = [e for e in execucoes if e.cenario == cenario]
        censuradas = sum(e.resultado.censurada for e in grupo)
        pares = [(referencia[e.repeticao], e.resultado) for e in grupo] if cenario != 'sem_intervencao' else []
        resumos[cenario] = ResumoCenario(
            metricas={
                nome: _estatistica([getattr(e.resultado, nome) for e in grupo])
                for nome in INDICADORES
            },
            diferencas={
                nome: _estatistica([_diferenca(getattr(a, nome), getattr(b, nome)) for a, b in pares])
                for nome in INDICADORES
            } if pares else {},
            reducoes={
                nome: _estatistica([_reducao(getattr(a, nome), getattr(b, nome)) for a, b in pares])
                for nome in INDICADORES_REDUCAO
            } if pares else {},
            censuradas=censuradas,
            proporcao_censuradas=censuradas / len(grupo),
            motivos_termino={'extincao': len(grupo) - censuradas, 'limite_passos': censuradas},
        )
    return resumos


def _conferir_resultado(resultado: ResultadoIndividual, populacao: int, limite: int) -> None:
    if type(resultado.populacao_inicial) is not int or resultado.populacao_inicial != populacao:
        raise ValueError('O resultado deve corresponder à população inicial da comparação.')
    campos_inteiros = (resultado.pico_infectados, resultado.passo_pico, resultado.horizonte_observado)
    if any(type(valor) is not int for valor in campos_inteiros):
        raise ValueError('O pico de infectados e os passos observados devem ser inteiros.')
    if not (
        0 <= resultado.pico_infectados <= populacao
        and type(resultado.fracao_acumulada) in (int, float)
        and 0 <= resultado.fracao_acumulada <= 1
        and 0 <= resultado.passo_pico <= resultado.horizonte_observado <= limite
    ):
        raise ValueError('O resultado contém indicadores fora do domínio.')
    if resultado.motivo_termino == 'extincao':
        if type(resultado.duracao_extincao) is not int or resultado.duracao_extincao != resultado.horizonte_observado:
            raise ValueError('A extinção deve estar registrada no último passo observado.')
    elif resultado.motivo_termino == 'limite_passos':
        if resultado.duracao_extincao is not None or resultado.horizonte_observado != limite:
            raise ValueError('O resultado censurado deve chegar ao limite sem duração de extinção.')
    else:
        raise ValueError('O resultado não informa um motivo de término reconhecido.')


def executar_comparacao(
    referencia: RedeDisponivel,
    pedido: PedidoComparacao,
    executar_individual: Callable[[RedeContatos, ConfiguracaoSimulacao], ResultadoIndividual],
) -> ResultadoComparacao:
    intervencao_validada = pedido.validar(referencia)
    configuracao = pedido.configuracao
    populacao = referencia.rede.numero_individuos
    execucoes: list[ExecucaoComparada] = []
    for indice in range(pedido.repeticoes):
        configuracao_repeticao = replace(
            configuracao,
            semente_epidemia=configuracao.semente_epidemia + indice,
            semente_iniciais=configuracao.semente_iniciais + indice,
            semente_isolamento=configuracao.semente_isolamento + indice,
        ).preparar(referencia.rede, referencia.revisao)
        for cenario in CENARIOS:
            intervencao_cenario = (
                None if cenario == 'sem_intervencao' else replace(intervencao_validada, estrategia=cenario)
            )
            configuracao_cenario = replace(configuracao_repeticao, intervencao=intervencao_cenario)
            try:
                resultado = executar_individual(referencia.rede.copiar(), configuracao_cenario)
                _conferir_resultado(resultado, populacao, configuracao_cenario.limite_passos)
            except Exception as erro:
                raise ErroExecucaoComparacao(indice + 1, cenario) from erro
            execucoes.append(ExecucaoComparada(indice + 1, cenario, configuracao_cenario, resultado))
    return ResultadoComparacao(
        pedido, referencia.revisao, deepcopy(referencia.origem), tuple(execucoes), _consolidar(execucoes),
    )
