"""Grafo de contatos não direcionado, simples e ponderado."""

from __future__ import annotations

from .aresta import Aresta
from .individuo import Individuo


def _validar_id(id_individuo: int) -> None:
    if isinstance(id_individuo, bool) or not isinstance(id_individuo, int):
        raise TypeError("O identificador do indivíduo deve ser inteiro.")


class Grafo:
    """Rede com contatos compartilhados nos dois sentidos e consultas protegidas."""

    def __init__(self) -> None:
        self._individuos: dict[int, Individuo] = {}
        self._adjacencias: dict[int, dict[int, Aresta]] = {}
        self._numero_arestas = 0

    @property
    def numero_individuos(self) -> int:
        """Quantidade de indivíduos em O(1)."""
        return len(self._individuos)

    @property
    def numero_arestas(self) -> int:
        """Quantidade de contatos únicos em O(1)."""
        return self._numero_arestas

    @property
    def individuos(self) -> tuple[Individuo, ...]:
        """Retorna referências aos indivíduos em uma tupla, em O(V)."""
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
        """Cadastra a pessoa e sua vizinhança vazia, rejeitando IDs duplicados."""
        if not isinstance(individuo, Individuo):
            raise TypeError("O vértice deve ser uma instância de Individuo.")
        if individuo.id in self._individuos:
            raise ValueError(f"O indivíduo {individuo.id} já está cadastrado.")
        self._individuos[individuo.id] = individuo
        self._adjacencias[individuo.id] = {}

    def buscar_individuo(self, id_individuo: int) -> Individuo | None:
        """Busca opcional por ID, retornando None quando não há cadastro."""
        _validar_id(id_individuo)
        return self._individuos.get(id_individuo)

    def obter_individuo(self, id_individuo: int) -> Individuo:
        """Consulta por ID; lança KeyError quando o indivíduo não existe."""
        individuo = self.buscar_individuo(id_individuo)
        if individuo is None:
            raise KeyError(f"O indivíduo {id_individuo} não está cadastrado.")
        return individuo

    def _adjacencia_de(self, individuo: Individuo) -> dict[int, Aresta]:
        if not isinstance(individuo, Individuo):
            raise TypeError("O vértice deve ser uma instância de Individuo.")
        if self._individuos.get(individuo.id) is not individuo:
            raise KeyError(f"O indivíduo {individuo.id} não está cadastrado nesta rede.")
        return self._adjacencias[individuo.id]

    def conectar(
        self, origem: Individuo, destino: Individuo, peso: float = 1.0
    ) -> Aresta:
        """Conecta as instâncias cadastradas, validando antes de alterar a rede."""
        adjacencia = self._adjacencia_de(origem)
        adjacencia_destino = self._adjacencia_de(destino)
        if destino.id in adjacencia:
            raise ValueError(f"Já existe uma aresta entre {origem.id} e {destino.id}.")
        aresta = Aresta(origem, destino, peso)
        adjacencia[destino.id] = aresta
        adjacencia_destino[origem.id] = aresta
        self._numero_arestas += 1
        return aresta

    def adicionar_aresta(
        self, id_origem: int, id_destino: int, peso: float = 1.0
    ) -> Aresta:
        """Conecta por IDs, reutilizando a validação da operação por objetos."""
        return self.conectar(
            self.obter_individuo(id_origem), self.obter_individuo(id_destino), peso
        )

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
        """Vizinhos estruturais, inclusive isolados, em O(grau do indivíduo)."""
        self.obter_individuo(id_individuo)
        return tuple(
            self._individuos[id_vizinho]
            for id_vizinho in self._adjacencias[id_individuo]
        )

    def contatos_de(self, individuo: Individuo) -> frozenset[Aresta]:
        """Contatos estruturais em uma coleção protegida, em O(grau)."""
        return frozenset(self._adjacencia_de(individuo).values())

    def grau(self, individuo: Individuo) -> int:
        """Quantidade de vizinhos estruturais de uma pessoa cadastrada, em O(1)."""
        return len(self._adjacencia_de(individuo))
