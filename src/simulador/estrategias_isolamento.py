from abc import ABC, abstractmethod

from simulador.aleatoriedade import GeradorAleatorio
from simulador.configuracao import ConfiguracaoSimulacao, ErroConfiguracao, ProblemaConfiguracao
from simulador.rede_contatos import RedeContatos


def _validar_rede(rede: RedeContatos) -> None:
    if not isinstance(rede, RedeContatos):
        raise TypeError("A rede deve ser uma instância de RedeContatos.")


def _validar_quantidade(rede: RedeContatos, quantidade: int) -> None:
    _validar_rede(rede)
    if isinstance(quantidade, bool) or not isinstance(quantidade, int):
        raise TypeError("A quantidade de pessoas deve ser inteira.")
    if not 0 <= quantidade <= rede.numero_individuos:
        raise ValueError("A quantidade deve estar entre zero e a população.")


class EstrategiaIsolamento(ABC):
    def __init__(self, nome: str) -> None:
        self._nome = nome

    @property
    def nome(self) -> str:
        return self._nome

    @abstractmethod
    def selecionar(self, rede: RedeContatos, quantidade: int) -> tuple[int, ...]:
        pass


class IsolamentoAleatorio(EstrategiaIsolamento):
    def __init__(self, gerador: GeradorAleatorio) -> None:
        if not isinstance(gerador, GeradorAleatorio):
            raise TypeError("Informe o gerador do fluxo de isolamento.")
        super().__init__("aleatoria")
        self._gerador = gerador

    def selecionar(self, rede: RedeContatos, quantidade: int) -> tuple[int, ...]:
        _validar_quantidade(rede, quantidade)
        if quantidade == 0:
            return ()
        return self._gerador.amostrar_ids(
            [pessoa.id for pessoa in rede.iter_individuos()], quantidade,
        )


class IsolamentoPorGrau(EstrategiaIsolamento):
    def __init__(self, rede_original: RedeContatos) -> None:
        _validar_rede(rede_original)
        if any(p.isolamento for p in rede_original.iter_individuos()):
            raise ValueError("Capture os graus na referência anterior à intervenção.")
        super().__init__("grau")
        self._graus_originais = {
            pessoa.id: rede_original.grau(pessoa)
            for pessoa in rede_original.iter_individuos()
        }

    @property
    def graus_originais(self) -> dict[int, int]:
        return self._graus_originais.copy()

    def selecionar(self, rede: RedeContatos, quantidade: int) -> tuple[int, ...]:
        _validar_quantidade(rede, quantidade)
        if {p.id for p in rede.iter_individuos()} != self._graus_originais.keys():
            raise ValueError("A população mudou. Prepare novamente os graus originais.")
        ids_ordenados = sorted(
            self._graus_originais,
            key=lambda id_individuo: (-self._graus_originais[id_individuo], id_individuo),
        )
        return tuple(ids_ordenados[:quantidade])


def preparar_estrategia(
    rede_original: RedeContatos, configuracao: ConfiguracaoSimulacao,
    *, revisao_rede: int,
) -> EstrategiaIsolamento | None:
    problemas = configuracao.validar(rede_original, revisao_rede)
    if problemas:
        raise ErroConfiguracao(problemas)
    intervencao = configuracao.intervencao
    if intervencao is None or intervencao.quantidade_isolados(rede_original.numero_individuos) == 0:
        return None
    if any(p.isolamento for p in rede_original.iter_individuos()):
        raise ErroConfiguracao([ProblemaConfiguracao(
            "intervencao", "Prepare a estratégia numa rede anterior à intervenção.",
        )])
    if intervencao.estrategia == "grau":
        return IsolamentoPorGrau(rede_original)
    return IsolamentoAleatorio(GeradorAleatorio(configuracao.semente_isolamento))
