"""Regras de estado, isolamento e validação de indivíduos."""

import pytest

from simulador import Individuo


@pytest.mark.parametrize("identificador", [0, -1])
def test_identificadores_inteiros_nao_sao_limitados_a_positivos(
    identificador: int,
) -> None:
    individuo = Individuo(identificador)

    individuo.infectar(0)

    assert individuo.id == identificador
    assert individuo.estado == "I"


@pytest.mark.parametrize("dia", [0, 12])
def test_infectar_registra_o_dia_e_preserva_o_isolamento(dia: int) -> None:
    individuo = Individuo(1, isolamento=True)

    individuo.infectar(dia)

    assert individuo.estado == "I"
    assert individuo.dia_inicio_infeccao == dia
    assert individuo.isolamento is True


def test_recuperar_preserva_historico_e_isolamento() -> None:
    individuo = Individuo(1, estado="I", isolamento=True, dia_inicio_infeccao=3)

    individuo.recuperar()

    assert individuo.estado == "R"
    assert individuo.dia_inicio_infeccao == 3
    assert individuo.isolamento is True


@pytest.mark.parametrize("estado", ["S", "I", "R"])
def test_isolamento_e_liberacao_independem_do_estado_epidemiologico(
    estado: str,
) -> None:
    dia = None if estado == "S" else 4
    individuo = Individuo(1, estado=estado, dia_inicio_infeccao=dia)

    individuo.isolar()

    assert individuo.isolamento is True
    assert individuo.estado == estado
    assert individuo.dia_inicio_infeccao == dia

    individuo.liberar_isolamento()

    assert individuo.isolamento is False
    assert individuo.estado == estado
    assert individuo.dia_inicio_infeccao == dia


@pytest.mark.parametrize("estado", ["I", "R"])
def test_estado_inicial_admite_dia_de_infeccao_desconhecido(estado: str) -> None:
    individuo = Individuo(1, estado=estado, isolamento=True)

    assert individuo.estado == estado
    assert individuo.dia_inicio_infeccao is None
    assert individuo.isolamento is True


@pytest.mark.parametrize(
    "identificador",
    [
        pytest.param(True, id="booleano"),
        pytest.param(1.5, id="decimal"),
        pytest.param("1", id="texto"),
    ],
)
def test_identificador_precisa_ser_inteiro(identificador: object) -> None:
    with pytest.raises(TypeError):
        Individuo(identificador)


@pytest.mark.parametrize("estado", [None, 1])
def test_estado_precisa_ser_texto(estado: object) -> None:
    with pytest.raises(TypeError):
        Individuo(1, estado=estado)


@pytest.mark.parametrize("estado", ["E", ""])
def test_estado_precisa_pertencer_ao_modelo_sir(estado: str) -> None:
    with pytest.raises(ValueError):
        Individuo(1, estado=estado)


@pytest.mark.parametrize("isolamento", [1, "sim"])
def test_isolamento_precisa_ser_booleano(isolamento: object) -> None:
    with pytest.raises(TypeError):
        Individuo(1, isolamento=isolamento)


@pytest.mark.parametrize(
    "dia,erro",
    [
        pytest.param(-1, ValueError, id="negativo"),
        pytest.param(True, TypeError, id="booleano"),
        pytest.param(2.5, TypeError, id="decimal"),
    ],
)
def test_dia_inicial_de_infeccao_precisa_ser_inteiro_nao_negativo(
    dia: object, erro: type[Exception]
) -> None:
    with pytest.raises(erro):
        Individuo(1, estado="I", dia_inicio_infeccao=dia)


def test_suscetivel_nao_pode_iniciar_com_dia_de_infeccao() -> None:
    with pytest.raises(ValueError):
        Individuo(1, dia_inicio_infeccao=0)


@pytest.mark.parametrize("estado", ["I", "R"])
def test_apenas_suscetivel_pode_ser_infectado(estado: str) -> None:
    individuo = Individuo(1, estado=estado, dia_inicio_infeccao=2)

    with pytest.raises(ValueError):
        individuo.infectar(5)

    assert individuo.estado == estado
    assert individuo.dia_inicio_infeccao == 2


@pytest.mark.parametrize("estado", ["S", "R"])
def test_apenas_infectado_pode_se_recuperar(estado: str) -> None:
    individuo = Individuo(1, estado=estado)

    with pytest.raises(ValueError):
        individuo.recuperar()

    assert individuo.estado == estado
    assert individuo.dia_inicio_infeccao is None


@pytest.mark.parametrize(
    "dia,erro",
    [
        pytest.param(-1, ValueError, id="negativo"),
        pytest.param(True, TypeError, id="booleano"),
        pytest.param(1.5, TypeError, id="decimal"),
    ],
)
def test_infectar_com_dia_invalido_preserva_o_individuo(
    dia: object, erro: type[Exception]
) -> None:
    individuo = Individuo(1, isolamento=True)

    with pytest.raises(erro):
        individuo.infectar(dia)

    assert individuo.estado == "S"
    assert individuo.dia_inicio_infeccao is None
    assert individuo.isolamento is True
