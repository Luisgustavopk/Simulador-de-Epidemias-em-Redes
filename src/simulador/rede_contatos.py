"""Grafo de contatos não direcionado, simples e ponderado."""

from __future__ import annotations

from simulador.contato import Contato
from simulador.individuo import Individuo


def _validar_id(id_individuo: int) -> None:
    if isinstance(id_individuo, bool) or not isinstance(id_individuo, int):
        raise TypeError("O identificador do indivíduo deve ser inteiro.")


class RedeContatos:
    """Grafo simples não direcionado, com cadastro por ID e listas de adjacência.

    Cada contato é compartilhado pelas vizinhanças dos seus dois extremos e
    contado uma única vez. As consultas devolvem coleções imutáveis contendo
    os mesmos objetos de domínio, não cópias dos estados epidemiológicos.
    """

    def __init__(self) -> None:
        """Cria uma rede vazia, permitindo cadastrar pessoas sem contatos."""
        self._individuos: dict[int, Individuo] = {}
        self._adjacencias: dict[int, dict[int, Contato]] = {}
        self._numero_contatos = 0

    @property
    def numero_individuos(self) -> int:
        """Quantidade de indivíduos em O(1)."""
        return len(self._individuos)

    @property
    def numero_contatos(self) -> int:
        """Quantidade de contatos únicos em O(1)."""
        return self._numero_contatos

    @property
    def individuos(self) -> tuple[Individuo, ...]:
        """Retorna referências aos indivíduos em uma tupla, em O(V)."""
        return tuple(self._individuos.values())

    @property
    def contatos(self) -> tuple[Contato, ...]:
        """Retorna cada contato uma única vez, em O(V + E)."""
        return tuple(
            contato
            for id_origem, vizinhanca in self._adjacencias.items()
            for id_destino, contato in vizinhanca.items()
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

    def _adjacencia_de(self, individuo: Individuo) -> dict[int, Contato]:
        if not isinstance(individuo, Individuo):
            raise TypeError("O vértice deve ser uma instância de Individuo.")
        if self._individuos.get(individuo.id) is not individuo:
            raise KeyError(f"O indivíduo {individuo.id} não está cadastrado nesta rede.")
        return self._adjacencias[individuo.id]

    def conectar(
        self, origem: Individuo, destino: Individuo, peso: float = 1.0
    ) -> Contato:
        """Conecta duas pessoas cadastradas, sem alterar a rede em caso de erro.

        Args:
            origem: Instância cadastrada de um extremo do contato.
            destino: Instância cadastrada do outro extremo.
            peso: Intensidade normalizada em [0, 1].

        Returns:
            O mesmo contato registrado nas duas listas de adjacência.

        Raises:
            TypeError: Se um extremo ou o peso tiver tipo incompatível.
            KeyError: Se algum objeto não for a pessoa cadastrada nesta rede.
            ValueError: Se houver laço, contato repetido ou peso inválido.
        """
        adjacencia = self._adjacencia_de(origem)
        adjacencia_destino = self._adjacencia_de(destino)
        if destino.id in adjacencia:
            raise ValueError(f"Já existe um contato entre {origem.id} e {destino.id}.")
        contato = Contato(origem, destino, peso)
        adjacencia[destino.id] = contato
        adjacencia_destino[origem.id] = contato
        self._numero_contatos += 1
        return contato

    def adicionar_contato(
        self, id_origem: int, id_destino: int, peso: float = 1.0
    ) -> Contato:
        """Conecta por IDs, reutilizando a validação da operação por objetos."""
        return self.conectar(
            self.obter_individuo(id_origem), self.obter_individuo(id_destino), peso
        )

    def obter_contato(self, id_origem: int, id_destino: int) -> Contato:
        """Consulta o contato em qualquer sentido; ausências lançam KeyError."""
        self.obter_individuo(id_origem)
        self.obter_individuo(id_destino)
        try:
            return self._adjacencias[id_origem][id_destino]
        except KeyError:
            raise KeyError(
                f"Não existe contato entre {id_origem} e {id_destino}."
            ) from None

    def vizinhos(self, id_individuo: int) -> tuple[Individuo, ...]:
        """Vizinhos estruturais, inclusive isolados, em O(grau do indivíduo)."""
        self.obter_individuo(id_individuo)
        return tuple(
            self._individuos[id_vizinho]
            for id_vizinho in self._adjacencias[id_individuo]
        )

    def contatos_de(self, individuo: Individuo) -> frozenset[Contato]:
        """Contatos estruturais em uma coleção protegida, em O(grau)."""
        return frozenset(self._adjacencia_de(individuo).values())

    def grau(self, individuo: Individuo) -> int:
        """Quantidade de vizinhos estruturais de uma pessoa cadastrada, em O(1)."""
        return len(self._adjacencia_de(individuo))
