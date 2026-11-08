"""Grafo de contatos não direcionado, simples e ponderado."""

from __future__ import annotations

from .aresta import Aresta
from .individuo import Individuo


def _validar_id(id_individuo: int) -> None:
    if isinstance(id_individuo, bool) or not isinstance(id_individuo, int):
        raise TypeError("O identificador do indivíduo deve ser inteiro.")


class Grafo:
    """Rede de indivíduos representada por listas de adjacência.

    Cada contato compartilha a mesma instância de Aresta nas duas direções.
    Os identificadores dos indivíduos e as extremidades das arestas devem
    permanecer inalterados após o cadastro. Estados, isolamento, pesos e
    indicadores de conexão ativa podem ser atualizados pelos seus consumidores.

    As consultas de coleções retornam tuplas com referências aos modelos,
    preservando a estrutura interna do grafo.
    """

    def __init__(self) -> None:
        self._individuos: dict[int, Individuo] = {}
        self._adjacencias: dict[int, dict[int, Aresta]] = {}
        self._numero_arestas = 0

    @property
    def numero_individuos(self) -> int:
        """Quantidade de indivíduos cadastrados, consultada em O(1)."""
        return len(self._individuos)

    @property
    def numero_arestas(self) -> int:
        """Quantidade de contatos, contando cada aresta uma vez, em O(1)."""
        return self._numero_arestas

    @property
    def individuos(self) -> tuple[Individuo, ...]:
        """Retorna uma tupla dos indivíduos cadastrados, em O(V)."""
        return tuple(self._individuos.values())

    @property
    def arestas(self) -> tuple[Aresta, ...]:
        """Retorna cada contato uma única vez, em O(V + E)."""
        return tuple(
            aresta
            for id_origem, vizinhanca in self._adjacencias.items()
            for id_destino, aresta in vizinhanca.items()
            if id_origem < id_destino
        )

    def adicionar_individuo(self, individuo: Individuo) -> None:
        """Cadastra um indivíduo, rejeitando identificadores duplicados."""
        if not isinstance(individuo, Individuo):
            raise TypeError("O vértice deve ser uma instância de Individuo.")
        identificador = individuo.id
        _validar_id(identificador)
        if identificador in self._individuos:
            raise ValueError(f"O indivíduo {identificador} já está cadastrado.")
        self._individuos[identificador] = individuo
        self._adjacencias[identificador] = {}

    def obter_individuo(self, id_individuo: int) -> Individuo:
        """Consulta por ID; lança KeyError quando o indivíduo não existe."""
        _validar_id(id_individuo)
        try:
            return self._individuos[id_individuo]
        except KeyError:
            raise KeyError(f"O indivíduo {id_individuo} não está cadastrado.") from None

    def adicionar_aresta(
        self,
        id_origem: int,
        id_destino: int,
        peso: float = 1.0,
        ativa: bool = True,
    ) -> Aresta:
        """Cria um contato entre indivíduos cadastrados e retorna a aresta.

        Laços, pesos e tipos inválidos são rejeitados pela classe Aresta.
        Contatos repetidos, inclusive na ordem inversa, lançam ValueError.
        A validação ocorre antes de qualquer alteração na rede.
        """
        origem = self.obter_individuo(id_origem)
        destino = self.obter_individuo(id_destino)
        if id_destino in self._adjacencias[id_origem]:
            raise ValueError(
                f"Já existe uma aresta entre {id_origem} e {id_destino}."
            )
        aresta = Aresta(origem=origem, destino=destino, peso=peso, ativa=ativa)
        self._adjacencias[id_origem][id_destino] = aresta
        self._adjacencias[id_destino][id_origem] = aresta
        self._numero_arestas += 1
        return aresta

    def obter_aresta(self, id_origem: int, id_destino: int) -> Aresta:
        """Consulta o contato em qualquer sentido; ausências lançam KeyError."""
        self.obter_individuo(id_origem)
        self.obter_individuo(id_destino)
        try:
            return self._adjacencias[id_origem][id_destino]
        except KeyError:
            raise KeyError(
                f"Não existe aresta entre {id_origem} e {id_destino}."
            ) from None

    def vizinhos(self, id_individuo: int) -> tuple[Individuo, ...]:
        """Consulta os vizinhos estruturais em O(grau do indivíduo).

        Inclui contatos inativos e indivíduos isolados, pois essas condições
        não removem contatos da estrutura da rede.
        """
        self.obter_individuo(id_individuo)
        return tuple(
            self._individuos[id_vizinho]
            for id_vizinho in self._adjacencias[id_individuo]
        )
