"""Grafo de contatos não direcionado, simples e ponderado."""

from __future__ import annotations

from collections.abc import Iterator
from copy import deepcopy
from typing import cast

from simulador.contato import Contato, _validar_peso
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
        return tuple(self.iter_individuos())

    @property
    def contatos(self) -> tuple[Contato, ...]:
        """Retorna cada contato uma única vez, em O(V + E)."""
        return tuple(self.iter_contatos())

    def iter_individuos(self) -> Iterator[Individuo]:
        """Itera sem copiar a população; não altere o cadastro durante o uso."""
        return iter(self._individuos.values())

    def iter_contatos(self) -> Iterator[Contato]:
        """Itera contatos únicos sem cópia; mantenha a topologia durante o uso."""
        return (
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

    def alterar_peso_contato(
        self, id_origem: int, id_destino: int, peso: float
    ) -> Contato:
        """Altera o peso em O(1), preservando identidade, atividade e topologia.

        Valida o contato e o novo peso antes da alteração. As duas adjacências
        continuam apontando para o mesmo objeto; referências anteriores veem
        o peso atualizado. Falhas não alteram a rede.
        """
        contato = self.obter_contato(id_origem, id_destino)
        peso_validado = _validar_peso(peso)
        contato._peso = peso_validado
        return contato

    def desativar_contato(self, id_origem: int, id_destino: int) -> Contato:
        """Desativa em O(1), sem remover a ligação nem mudar peso ou pessoas.

        A operação é idempotente. A análise estrutural continua incluindo o
        contato; o futuro motor deve consultar sua disponibilidade.
        """
        contato = self.obter_contato(id_origem, id_destino)
        contato._ativa = False
        return contato

    def remover_contato(self, id_origem: int, id_destino: int) -> Contato:
        """Remove das duas adjacências em O(1), preservando o cadastro.

        Devolve o contato removido. IDs ou ligação ausentes geram KeyError
        antes de alterar a rede; remover novamente também gera KeyError.
        """
        contato = self.obter_contato(id_origem, id_destino)
        del self._adjacencias[id_origem][id_destino]
        del self._adjacencias[id_destino][id_origem]
        self._numero_contatos -= 1
        return contato

    def desconectar_individuo(self, id_individuo: int) -> tuple[Contato, ...]:
        """Remove contatos em O(grau), mantendo a pessoa, seu SIR e histórico.

        Devolve os contatos removidos na ordem da vizinhança. Desconectar uma
        pessoa já sem contatos devolve (). Não marca isolamento por si só.
        """
        individuo = self.obter_individuo(id_individuo)
        adjacencia = self._adjacencia_de(individuo)
        removidos = tuple(adjacencia.values())
        for id_vizinho in adjacencia:
            del self._adjacencias[id_vizinho][id_individuo]
        adjacencia.clear()
        self._numero_contatos -= len(removidos)
        return removidos

    def vizinhos(self, id_individuo: int) -> tuple[Individuo, ...]:
        """Vizinhos estruturais, inclusive isolados, em O(grau do indivíduo)."""
        return tuple(self.iter_vizinhos(id_individuo))

    def iter_vizinhos(self, id_individuo: int) -> Iterator[Individuo]:
        """Valida o ID e itera sem cópia; mantenha a topologia durante o uso."""
        ids = self.iter_ids_vizinhos(id_individuo)
        return (
            self._individuos[id_vizinho]
            for id_vizinho in ids
        )

    def iter_ids_vizinhos(self, id_individuo: int) -> Iterator[int]:
        """Itera IDs sem copiar ou buscar pessoas; mantenha a topologia no uso."""
        self.obter_individuo(id_individuo)
        return iter(self._adjacencias[id_individuo])

    def contatos_de(self, individuo: Individuo) -> frozenset[Contato]:
        """Contatos estruturais em uma coleção protegida, em O(grau)."""
        return frozenset(self._adjacencia_de(individuo).values())

    def grau(self, individuo: Individuo) -> int:
        """Quantidade de vizinhos estruturais de uma pessoa cadastrada, em O(1)."""
        return len(self._adjacencia_de(individuo))

    def copiar(self) -> RedeContatos:
        """Copia topologia, pesos, atividade e estados sem compartilhar mutáveis.

        Preserva a ordem de cadastro das pessoas, a orientação armazenada de
        cada contato e a ordem de cada vizinhança para reproduzir percursos.
        Custa O(V + E); a estrutura deve permanecer estável durante a cópia.
        """
        return deepcopy(self)

    def __deepcopy__(self, memo: dict[int, object]) -> RedeContatos:
        """Copia sem recursão pela topologia, preservando referências no memo."""
        copia = RedeContatos()
        memo[id(self)] = copia
        for pessoa in self.iter_individuos():
            copia.adicionar_individuo(deepcopy(pessoa, memo))
        contatos_copiados: dict[Contato, Contato] = {}
        for contato in self.iter_contatos():
            if id(contato) in memo:
                contato_copiado = cast(Contato, memo[id(contato)])
            else:
                contato_copiado = Contato(
                    copia._individuos[contato.origem.id],
                    copia._individuos[contato.destino.id],
                    contato.peso,
                    ativa=contato.ativa,
                )
                memo[id(contato)] = contato_copiado
            contatos_copiados[contato] = contato_copiado
        # Reconstruir cada adjacência preserva sua ordem mesmo quando o cadastro
        # global dos contatos não coincide com a ordem de enumeração por ID.
        copia._adjacencias = {
            identificador: {
                vizinho: contatos_copiados[contato]
                for vizinho, contato in adjacencia.items()
            }
            for identificador, adjacencia in self._adjacencias.items()
        }
        copia._numero_contatos = self._numero_contatos
        return copia
