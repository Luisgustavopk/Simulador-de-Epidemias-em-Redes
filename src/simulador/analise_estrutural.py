"""Percursos e métricas da topologia cadastrada na rede de contatos."""

from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass

from simulador.rede_contatos import RedeContatos


@dataclass(frozen=True, slots=True)
class ResumoEstrutural:
    """Contagens e grau médio no instante da análise, incluindo grau zero."""

    numero_individuos: int
    numero_contatos: int
    grau_medio: float


def _validar_rede(rede: RedeContatos) -> None:
    if not isinstance(rede, RedeContatos):
        raise TypeError("A rede deve ser uma instância de RedeContatos.")


def bfs(rede: RedeContatos, id_origem: int) -> tuple[int, ...]:
    """Percorre a componente da origem em largura, sem alterar a rede.

    Args:
        rede: Rede cujos contatos estruturais serão percorridos.
        id_origem: ID inteiro de uma pessoa cadastrada.

    Returns:
        IDs na ordem de visita, começando pela origem. Vizinhos são examinados
        na ordem de cadastro dos contatos, sem considerar peso ou isolamento.

    Raises:
        TypeError: Se a rede ou o ID tiverem tipo incompatível, incluindo bool.
        KeyError: Se a origem não estiver cadastrada, inclusive na rede vazia.
    """
    _validar_rede(rede)
    rede.obter_individuo(id_origem)
    visitados = {id_origem}
    fila = deque([id_origem])
    ordem: list[int] = []
    while fila:
        atual = fila.popleft()
        ordem.append(atual)
        for id_vizinho in rede.iter_ids_vizinhos(atual):
            if id_vizinho not in visitados:
                visitados.add(id_vizinho)
                fila.append(id_vizinho)
    return tuple(ordem)


def dfs(rede: RedeContatos, id_origem: int) -> tuple[int, ...]:
    """Percorre a componente da origem em profundidade, sem recursão.

    Args:
        rede: Rede cujos contatos estruturais serão percorridos.
        id_origem: ID inteiro de uma pessoa cadastrada.

    Returns:
        IDs na ordem da primeira visita. Cada ramo é explorado antes de voltar
        ao próximo vizinho, seguindo a ordem de cadastro dos contatos.

    Raises:
        TypeError: Se a rede ou o ID tiverem tipo incompatível, incluindo bool.
        KeyError: Se a origem não estiver cadastrada, inclusive na rede vazia.
    """
    _validar_rede(rede)
    rede.obter_individuo(id_origem)
    visitados = {id_origem}
    ordem = [id_origem]
    pilha: list[Iterator[int]] = [rede.iter_ids_vizinhos(id_origem)]
    while pilha:
        id_vizinho = next(pilha[-1], None)
        if id_vizinho is None:
            pilha.pop()
        elif id_vizinho not in visitados:
            visitados.add(id_vizinho)
            ordem.append(id_vizinho)
            pilha.append(rede.iter_ids_vizinhos(id_vizinho))
    return tuple(ordem)


def componentes_conexas(rede: RedeContatos) -> tuple[frozenset[int], ...]:
    """Particiona todos os IDs em componentes, incluindo pessoas sem contatos.

    Reutiliza BFS e inicia cada componente pela primeira pessoa ainda não
    visitada na ordem de cadastro. A rede vazia devolve uma tupla vazia.
    """
    _validar_rede(rede)
    visitados: set[int] = set()
    componentes: list[frozenset[int]] = []
    for pessoa in rede.iter_individuos():
        if pessoa.id not in visitados:
            componente = frozenset(bfs(rede, pessoa.id))
            visitados.update(componente)
            componentes.append(componente)
    return tuple(componentes)


def esta_conexa(rede: RedeContatos) -> bool:
    """Indica se uma origem alcança toda a população cadastrada.

    Por convenção desta API, a rede vazia retorna False; uma pessoa sozinha
    forma uma rede conexa. Contatos de peso zero e indisponíveis são incluídos.
    """
    _validar_rede(rede)
    origem = next(rede.iter_individuos(), None)
    if origem is None:
        return False
    return len(bfs(rede, origem.id)) == rede.numero_individuos


def resumir_rede(rede: RedeContatos) -> ResumoEstrutural:
    """Resume população, contatos únicos e média aritmética dos graus.

    Usa RedeContatos.grau() para cada pessoa, incluindo as sem contatos.
    Na rede vazia, o grau médio é 0.0. O resultado preserva os valores do
    instante da consulta mesmo que a rede receba novas pessoas ou contatos.
    """
    _validar_rede(rede)
    numero_individuos = rede.numero_individuos
    soma_graus = sum(rede.grau(pessoa) for pessoa in rede.iter_individuos())
    grau_medio = soma_graus / numero_individuos if numero_individuos else 0.0
    return ResumoEstrutural(
        numero_individuos=numero_individuos,
        numero_contatos=rede.numero_contatos,
        grau_medio=grau_medio,
    )
