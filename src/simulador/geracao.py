"""Geradores nativos de redes sintéticas com aleatoriedade independente."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from random import Random
from types import MappingProxyType

from simulador.individuo import Individuo
from simulador.rede_contatos import RedeContatos


@dataclass(frozen=True, slots=True)
class ResultadoGeracaoRede:
    """Rede nova e configuração preservada para reproduzir a geração.

    Os metadados são somente leitura; a rede pode receber as alterações de
    domínio normais. A versão identifica as convenções dos algoritmos locais.
    """

    rede: RedeContatos
    modelo: str
    parametros: Mapping[str, int | float]
    semente: int
    versao_algoritmo: int = 1

    def __post_init__(self) -> None:
        """Preserva uma cópia imutável dos parâmetros, sem reter um dict externo."""
        object.__setattr__(self, "parametros", MappingProxyType(dict(self.parametros)))


def _validar_inteiro(valor: int, nome: str) -> None:
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise TypeError(f"{nome} deve ser um inteiro, sem aceitar booleanos.")


def _validar_intervalo_unitario(valor: float, nome: str) -> float:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise TypeError(f"{nome} deve ser um número real, sem aceitar booleanos.")
    if not 0 <= valor <= 1:
        raise ValueError(f"{nome} deve ser finito e estar entre 0 e 1.")
    return float(valor)


def _validar_comuns(numero_individuos: int, semente: int, peso: float) -> float:
    _validar_inteiro(numero_individuos, "numero_individuos")
    if numero_individuos < 1:
        raise ValueError("numero_individuos deve ser positivo.")
    _validar_inteiro(semente, "semente")
    return _validar_intervalo_unitario(peso, "peso")


def _criar_populacao(numero_individuos: int) -> RedeContatos:
    rede = RedeContatos()
    for id_individuo in range(numero_individuos):
        rede.adicionar_individuo(Individuo(id_individuo))
    return rede


def gerar_erdos_renyi(
    numero_individuos: int,
    probabilidade_contato: float,
    *,
    semente: int,
    peso: float = 1.0,
) -> ResultadoGeracaoRede:
    """Gera G(n, p), sorteando cada par distinto uma única vez.

    Args:
        numero_individuos: População inteira positiva, com IDs de 0 a n - 1.
        probabilidade_contato: Probabilidade finita em [0, 1] de criar cada par.
        semente: Inteiro explícito para um gerador aleatório exclusivo da chamada.
        peso: Peso fixo, finito em [0, 1], dos contatos criados; não altera p.

    Returns:
        Rede independente, incluindo pessoas sem contatos, e seus metadados.

    Raises:
        TypeError: Se um parâmetro tiver tipo incompatível, incluindo bool.
        ValueError: Se n não for positivo ou p/peso estiverem fora do domínio.
    """
    peso = _validar_comuns(numero_individuos, semente, peso)
    probabilidade_contato = _validar_intervalo_unitario(
        probabilidade_contato, "probabilidade_contato"
    )
    aleatorio = Random(semente)
    rede = _criar_populacao(numero_individuos)
    for origem in range(numero_individuos):
        for destino in range(origem + 1, numero_individuos):
            if aleatorio.random() < probabilidade_contato:
                rede.adicionar_contato(origem, destino, peso)
    return ResultadoGeracaoRede(
        rede=rede,
        modelo="erdos_renyi",
        parametros={
            "numero_individuos": numero_individuos,
            "probabilidade_contato": probabilidade_contato,
            "peso": peso,
        },
        semente=semente,
    )


def gerar_barabasi_albert(
    numero_individuos: int,
    contatos_por_novo_individuo: int,
    *,
    semente: int,
    peso: float = 1.0,
) -> ResultadoGeracaoRede:
    """Gera uma rede por crescimento e ligação preferencial pelo grau estrutural.

    A convenção local começa com o grafo completo de m + 1 pessoas. Cada nova
    pessoa escolhe m alvos distintos entre as anteriores, com probabilidade
    proporcional ao grau; os graus só são atualizados após a escolha dos alvos.

    Args:
        numero_individuos: População inteira positiva, com IDs de 0 a n - 1.
        contatos_por_novo_individuo: Inteiro m, com 1 <= m < n.
        semente: Inteiro explícito para um gerador aleatório exclusivo da chamada.
        peso: Peso fixo, finito em [0, 1], sem efeito na ligação preferencial.

    Returns:
        Rede independente e conectada, com configuração e tamanho do núcleo.

    Raises:
        TypeError: Se um parâmetro tiver tipo incompatível, incluindo bool.
        ValueError: Se n, m ou peso estiverem fora dos respectivos domínios.
    """
    peso = _validar_comuns(numero_individuos, semente, peso)
    _validar_inteiro(contatos_por_novo_individuo, "contatos_por_novo_individuo")
    if not 1 <= contatos_por_novo_individuo < numero_individuos:
        raise ValueError("contatos_por_novo_individuo deve satisfazer 1 <= m < n.")
    aleatorio = Random(semente)
    rede = _criar_populacao(numero_individuos)
    tamanho_nucleo = contatos_por_novo_individuo + 1
    # Cada ID aparece uma vez por contato incidente: sorteá-lo é ponderar por grau.
    ids_por_grau: list[int] = []
    for origem in range(tamanho_nucleo):
        for destino in range(origem + 1, tamanho_nucleo):
            rede.adicionar_contato(origem, destino, peso)
            ids_por_grau.extend((origem, destino))

    for novo_id in range(tamanho_nucleo, numero_individuos):
        alvos: list[int] = []
        selecionados: set[int] = set()
        while len(alvos) < contatos_por_novo_individuo:
            alvo = aleatorio.choice(ids_por_grau)
            if alvo not in selecionados:
                selecionados.add(alvo)
                alvos.append(alvo)
        for alvo in alvos:
            rede.adicionar_contato(novo_id, alvo, peso)
        ids_por_grau.extend(alvos)
        ids_por_grau.extend([novo_id] * contatos_por_novo_individuo)

    return ResultadoGeracaoRede(
        rede=rede,
        modelo="barabasi_albert",
        parametros={
            "numero_individuos": numero_individuos,
            "contatos_por_novo_individuo": contatos_por_novo_individuo,
            "tamanho_nucleo_inicial": tamanho_nucleo,
            "peso": peso,
        },
        semente=semente,
    )
