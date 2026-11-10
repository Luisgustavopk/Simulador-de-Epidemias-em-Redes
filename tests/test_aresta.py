"""Contatos normalizados e disponibilidade derivada dos dois extremos."""

import pytest

from simulador import Aresta, EstadoSIR, Individuo


@pytest.fixture
def extremos() -> tuple[Individuo, Individuo]:
    return Individuo(1), Individuo(2)


@pytest.mark.parametrize("indice", [0, 1])
def test_outro_extremo_usa_as_instancias_nos_dois_sentidos(
    extremos: tuple[Individuo, Individuo], indice: int
) -> None:
    aresta = Aresta(*extremos)

    assert aresta.outro_extremo(extremos[indice]) is extremos[1 - indice]


@pytest.mark.parametrize("identificador", [1, 3])
def test_outro_extremo_rejeita_pessoa_estranha_mesmo_com_id_igual(
    extremos: tuple[Individuo, Individuo], identificador: int
) -> None:
    aresta = Aresta(*extremos)

    with pytest.raises(ValueError):
        aresta.outro_extremo(Individuo(identificador))


@pytest.mark.parametrize("pessoa", [None, 1, "1"])
def test_outro_extremo_exige_um_individuo(
    extremos: tuple[Individuo, Individuo], pessoa: object
) -> None:
    with pytest.raises(TypeError):
        Aresta(*extremos).outro_extremo(pessoa)


@pytest.mark.parametrize("lado", [0, 1])
def test_extremos_precisam_ser_individuos(
    extremos: tuple[Individuo, Individuo], lado: int
) -> None:
    argumentos = list(extremos)
    argumentos[lado] = None

    with pytest.raises(TypeError):
        Aresta(*argumentos)


@pytest.mark.parametrize("mesma_instancia", [True, False])
def test_contato_rejeita_lacos_pelo_identificador(mesma_instancia: bool) -> None:
    origem = Individuo(1)
    destino = origem if mesma_instancia else Individuo(1)

    with pytest.raises(ValueError):
        Aresta(origem, destino)


@pytest.mark.parametrize("peso", [0, 0.5, 1])
def test_peso_normalizado_e_valido_e_nao_define_disponibilidade(
    extremos: tuple[Individuo, Individuo], peso: float
) -> None:
    aresta = Aresta(*extremos, peso=peso)

    assert aresta.peso == peso
    assert aresta.ativa is True


@pytest.mark.parametrize(
    "peso",
    [-0.1, 1.1, float("nan"), float("inf"), float("-inf"), 10**1000],
)
def test_peso_deve_ser_finito_e_estar_entre_zero_e_um(
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


@pytest.mark.parametrize("indices", [(0,), (1,), (0, 1)])
def test_isolamento_de_qualquer_extremo_bloqueia_contato_imediatamente(
    extremos: tuple[Individuo, Individuo], indices: tuple[int, ...]
) -> None:
    aresta = Aresta(*extremos, peso=0.5)

    for indice in indices:
        extremos[indice].isolar()

    assert aresta.ativa is False
    assert aresta.peso == 0.5


def test_recuperacao_nao_libera_o_contato_isolado(
    extremos: tuple[Individuo, Individuo],
) -> None:
    aresta = Aresta(*extremos)
    individuo = extremos[0]
    individuo.infectar(0)
    individuo.isolar()

    individuo.recuperar()

    assert individuo.estado is EstadoSIR.RECUPERADO
    assert aresta.ativa is False


def test_colecao_de_extremos_nao_expoe_estrutura_mutavel(
    extremos: tuple[Individuo, Individuo],
) -> None:
    aresta = Aresta(*extremos)
    copia = set(aresta.extremos)

    copia.clear()

    assert aresta.extremos == frozenset(extremos)
    assert aresta.origem is extremos[0]
    assert aresta.destino is extremos[1]


@pytest.mark.parametrize("atributo", ["origem", "destino", "extremos", "peso", "ativa"])
def test_identidade_e_valores_do_contato_sao_somente_leitura(
    extremos: tuple[Individuo, Individuo], atributo: str
) -> None:
    aresta = Aresta(*extremos, peso=0.5)

    with pytest.raises(AttributeError):
        setattr(aresta, atributo, None)

    assert aresta.extremos == frozenset(extremos)
    assert aresta.peso == 0.5
    assert aresta.ativa is True


def test_contato_permanece_no_conjunto_apos_mudanca_dos_individuos(
    extremos: tuple[Individuo, Individuo],
) -> None:
    aresta = Aresta(*extremos)
    incidentes = {aresta}
    extremos[1].infectar(4)
    extremos[1].isolar()

    assert aresta in incidentes
    assert aresta.outro_extremo(extremos[0]).estado is EstadoSIR.INFECTADO
    assert aresta.outro_extremo(extremos[0]).dia_inicio_infeccao == 4
