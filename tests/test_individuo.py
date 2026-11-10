"""Estados SIR encapsulados e isolamento independente do estado."""

import pytest

from simulador import EstadoSIR, Individuo


def _no_estado(estado: EstadoSIR) -> Individuo:
    individuo = Individuo(1)
    if estado is not EstadoSIR.SUSCETIVEL:
        individuo.infectar(2)
    if estado is EstadoSIR.RECUPERADO:
        individuo.recuperar()
    return individuo


@pytest.mark.parametrize("identificador", [0, -1, 7])
def test_individuo_inicia_suscetivel_sem_historico(identificador: int) -> None:
    individuo = Individuo(identificador)

    assert individuo.id == identificador
    assert individuo.estado is EstadoSIR.SUSCETIVEL
    assert individuo.isolamento is False
    assert individuo.dia_inicio_infeccao is None


@pytest.mark.parametrize("identificador", [True, 1.5, "1", None])
def test_identificador_precisa_ser_inteiro(identificador: object) -> None:
    with pytest.raises(TypeError):
        Individuo(identificador)


@pytest.mark.parametrize("passo", [0, 12])
def test_infectar_registra_passo_e_preserva_isolamento(passo: int) -> None:
    individuo = Individuo(1)
    individuo.isolar()

    individuo.infectar(passo)

    assert individuo.estado is EstadoSIR.INFECTADO
    assert individuo.dia_inicio_infeccao == passo
    assert individuo.isolamento is True


def test_recuperar_preserva_inicio_da_infeccao_e_isolamento() -> None:
    individuo = Individuo(1)
    individuo.infectar(3)
    individuo.isolar()

    individuo.recuperar()

    assert individuo.estado is EstadoSIR.RECUPERADO
    assert individuo.dia_inicio_infeccao == 3
    assert individuo.isolamento is True


@pytest.mark.parametrize("estado", list(EstadoSIR))
def test_isolar_e_idempotente_sem_mudar_estado_ou_historico(
    estado: EstadoSIR,
) -> None:
    individuo = _no_estado(estado)
    inicio = individuo.dia_inicio_infeccao

    individuo.isolar()
    individuo.isolar()

    assert individuo.isolamento is True
    assert individuo.estado is estado
    assert individuo.dia_inicio_infeccao == inicio


@pytest.mark.parametrize("estado", [EstadoSIR.INFECTADO, EstadoSIR.RECUPERADO])
def test_apenas_suscetiveis_podem_ser_infectados(estado: EstadoSIR) -> None:
    individuo = _no_estado(estado)

    with pytest.raises(ValueError):
        individuo.infectar(9)

    assert individuo.estado is estado
    assert individuo.dia_inicio_infeccao == 2


@pytest.mark.parametrize("estado", [EstadoSIR.SUSCETIVEL, EstadoSIR.RECUPERADO])
def test_apenas_infectados_podem_se_recuperar(estado: EstadoSIR) -> None:
    individuo = _no_estado(estado)
    inicio = individuo.dia_inicio_infeccao

    with pytest.raises(ValueError):
        individuo.recuperar()

    assert individuo.estado is estado
    assert individuo.dia_inicio_infeccao == inicio


@pytest.mark.parametrize(
    "passo,erro",
    [(-1, ValueError), (True, TypeError), (1.5, TypeError), (None, TypeError)],
)
def test_infeccao_invalida_nao_modifica_individuo(
    passo: object, erro: type[Exception]
) -> None:
    individuo = Individuo(1)
    individuo.isolar()

    with pytest.raises(erro):
        individuo.infectar(passo)

    assert individuo.estado is EstadoSIR.SUSCETIVEL
    assert individuo.dia_inicio_infeccao is None
    assert individuo.isolamento is True


@pytest.mark.parametrize(
    "atributo,valor",
    [
        ("id", 2),
        ("estado", EstadoSIR.RECUPERADO),
        ("isolamento", True),
        ("dia_inicio_infeccao", 4),
    ],
)
def test_consultas_nao_permitem_contornar_as_transicoes(
    atributo: str, valor: object
) -> None:
    individuo = Individuo(1)

    with pytest.raises(AttributeError):
        setattr(individuo, atributo, valor)

    assert individuo.id == 1
    assert individuo.estado is EstadoSIR.SUSCETIVEL
    assert individuo.isolamento is False
    assert individuo.dia_inicio_infeccao is None


def test_identidade_em_conjuntos_e_mapas_permanece_apos_transicoes() -> None:
    individuo = Individuo(1)
    participantes = {individuo}
    indicadores = {individuo: "original"}
    identidade_hash = hash(individuo)

    individuo.infectar(0)
    individuo.isolar()
    individuo.recuperar()

    assert individuo in participantes
    assert indicadores[individuo] == "original"
    assert hash(individuo) == identidade_hash
