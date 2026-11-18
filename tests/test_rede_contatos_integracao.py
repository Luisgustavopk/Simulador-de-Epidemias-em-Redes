"""Invariantes da rede com múltiplas pessoas e contatos."""

import pytest

from simulador.contato import Contato
from simulador.individuo import Individuo
from simulador.rede_contatos import RedeContatos


@pytest.fixture
def rede() -> RedeContatos:
    rede = RedeContatos()
    for identificador in (-5, 0, 1, 2, 7, 99):
        rede.adicionar_individuo(Individuo(identificador))
    return rede


def test_contatos_preservam_simetria_pesos_e_soma_dos_graus(
    rede: RedeContatos,
) -> None:
    ligacoes = [(7, -5, 0.0), (-5, 0, 0.4), (2, 0, 1.0), (1, 7, 0.75)]
    vizinhancas = {individuo.id: set() for individuo in rede.individuos}
    contatos = []

    for origem, destino, peso in ligacoes:
        contato = rede.adicionar_contato(origem, destino, peso)
        contatos.append(contato)
        vizinhancas[origem].add(destino)
        vizinhancas[destino].add(origem)

        assert isinstance(contato, Contato)
        assert contato.peso == peso
        assert rede.obter_contato(origem, destino) is contato
        assert rede.obter_contato(destino, origem) is contato
        assert contato in rede.contatos_de(rede.obter_individuo(origem))
        assert contato in rede.contatos_de(rede.obter_individuo(destino))

    assert rede.numero_individuos == 6
    assert rede.numero_contatos == len(ligacoes)
    assert len(rede.contatos) == len(ligacoes)
    assert set(rede.contatos) == set(contatos)
    assert sum(rede.grau(pessoa) for pessoa in rede.individuos) == 2 * len(ligacoes)
    for pessoa in rede.individuos:
        assert {vizinho.id for vizinho in rede.vizinhos(pessoa.id)} == vizinhancas[
            pessoa.id
        ]
        assert rede.grau(pessoa) == len(vizinhancas[pessoa.id])
    assert rede.contatos_de(rede.obter_individuo(99)) == frozenset()


@pytest.mark.parametrize(
    "origem,destino,peso,erro",
    [
        pytest.param(-5, 7, float("nan"), ValueError, id="peso-nan"),
        pytest.param(-5, 7, float("inf"), ValueError, id="peso-infinito"),
        pytest.param(-5, 7, True, TypeError, id="peso-booleano"),
        pytest.param(-5, 7, 1.5, ValueError, id="peso-fora-do-intervalo"),
        pytest.param(0, -5, 0.4, ValueError, id="contato-invertido-duplicado"),
        pytest.param(7, 7, 0.3, ValueError, id="laco"),
        pytest.param(7, 999, 0.3, KeyError, id="id-nao-cadastrado"),
        pytest.param(True, 7, 0.3, TypeError, id="id-booleano"),
    ],
)
def test_adicionar_contato_invalido_preserva_cadastro_e_todas_as_vizinhancas(
    rede: RedeContatos,
    origem: object,
    destino: object,
    peso: object,
    erro: type[Exception],
) -> None:
    rede.adicionar_contato(-5, 0, 0.2)
    rede.adicionar_contato(0, 2, 0.8)
    individuos_antes = rede.individuos
    contatos_antes = rede.contatos
    vizinhancas_antes = {
        pessoa.id: rede.vizinhos(pessoa.id) for pessoa in rede.individuos
    }

    with pytest.raises(erro):
        rede.adicionar_contato(origem, destino, peso)

    assert rede.individuos == individuos_antes
    assert rede.contatos == contatos_antes
    assert rede.numero_individuos == 6
    assert rede.numero_contatos == 2
    assert {contato.peso for contato in rede.contatos} == {0.2, 0.8}
    for pessoa in rede.individuos:
        assert rede.vizinhos(pessoa.id) == vizinhancas_antes[pessoa.id]


def test_consulta_de_contatos_preserva_a_colecao_obtida_antes_de_nova_conexao(
    rede: RedeContatos,
) -> None:
    primeiro = rede.conectar(rede.obter_individuo(7), rede.obter_individuo(1), 0.5)
    contatos_antes = rede.contatos

    segundo = rede.adicionar_contato(1, 2, 0.25)

    assert contatos_antes == (primeiro,)
    assert len(rede.contatos) == 2
    assert set(rede.contatos) == {primeiro, segundo}
    assert rede.numero_contatos == 2
