"""Regras de uma conexão ponderada entre dois indivíduos distintos."""

import pytest

from simulador import Aresta, Individuo


@pytest.fixture
def extremos() -> tuple[Individuo, Individuo]:
    return Individuo(1), Individuo(2)


@pytest.mark.parametrize("identificador,indice_esperado", [(1, 1), (2, 0)])
def test_outro_extremo_funciona_nos_dois_sentidos(
    extremos: tuple[Individuo, Individuo],
    identificador: int,
    indice_esperado: int,
) -> None:
    aresta = Aresta(*extremos)

    assert aresta.outro_extremo(identificador) is extremos[indice_esperado]


def test_extremos_mantem_referencia_aos_individuos(
    extremos: tuple[Individuo, Individuo],
) -> None:
    aresta = Aresta(*extremos)

    extremos[1].infectar(4)

    vizinho = aresta.outro_extremo(1)
    assert vizinho.estado == "I"
    assert vizinho.dia_inicio_infeccao == 4


def test_outro_extremo_rejeita_individuo_fora_da_conexao(
    extremos: tuple[Individuo, Individuo],
) -> None:
    aresta = Aresta(*extremos)

    with pytest.raises(ValueError):
        aresta.outro_extremo(3)


@pytest.mark.parametrize("identificador", [True, "1"])
def test_outro_extremo_rejeita_identificador_de_tipo_invalido(
    extremos: tuple[Individuo, Individuo], identificador: object
) -> None:
    aresta = Aresta(*extremos)

    with pytest.raises(TypeError):
        aresta.outro_extremo(identificador)


@pytest.mark.parametrize("lado_invalido", ["origem", "destino"])
def test_extremos_precisam_ser_individuos(
    extremos: tuple[Individuo, Individuo], lado_invalido: str
) -> None:
    origem, destino = extremos

    with pytest.raises(TypeError):
        if lado_invalido == "origem":
            Aresta(None, destino)
        else:
            Aresta(origem, None)


@pytest.mark.parametrize("mesma_instancia", [True, False])
def test_grafo_simples_rejeita_lacos_pelo_identificador(
    mesma_instancia: bool,
) -> None:
    origem = Individuo(1)
    destino = origem if mesma_instancia else Individuo(1)

    with pytest.raises(ValueError):
        Aresta(origem, destino)


@pytest.mark.parametrize("peso", [0, 3.5])
def test_peso_admite_zero_e_intensidade_maior_que_um(
    extremos: tuple[Individuo, Individuo], peso: float
) -> None:
    aresta = Aresta(*extremos, peso=peso)

    assert aresta.peso == peso


@pytest.mark.parametrize(
    "peso",
    [
        pytest.param(-0.1, id="negativo"),
        pytest.param(float("nan"), id="nan"),
        pytest.param(float("inf"), id="infinito-positivo"),
        pytest.param(float("-inf"), id="infinito-negativo"),
        pytest.param(10**1000, id="inteiro-fora-da-faixa-float"),
    ],
)
def test_peso_precisa_ser_finito_e_nao_negativo(
    extremos: tuple[Individuo, Individuo], peso: float
) -> None:
    with pytest.raises(ValueError):
        Aresta(*extremos, peso=peso)


@pytest.mark.parametrize("peso", [True, "0.5", None])
def test_peso_precisa_ser_numerico(
    extremos: tuple[Individuo, Individuo], peso: object
) -> None:
    with pytest.raises(TypeError):
        Aresta(*extremos, peso=peso)


@pytest.mark.parametrize("ativa", [1, "sim"])
def test_ativa_precisa_ser_booleana(
    extremos: tuple[Individuo, Individuo], ativa: object
) -> None:
    with pytest.raises(TypeError):
        Aresta(*extremos, ativa=ativa)
