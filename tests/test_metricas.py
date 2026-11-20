"""Métricas epidemiológicas derivadas do histórico de passos."""

import pytest

from simulador import MetricasEpidemia, RegistroPasso


@pytest.fixture
def historico() -> tuple[RegistroPasso, ...]:
    return (
        RegistroPasso(passo=0, s=7, i=3, r=0),
        RegistroPasso(passo=1, s=5, i=4, r=1),
        RegistroPasso(passo=2, s=4, i=2, r=4),
        RegistroPasso(passo=3, s=4, i=0, r=6),
    )


def test_calcula_metricas_e_resumo(historico: tuple[RegistroPasso, ...]) -> None:
    metricas = MetricasEpidemia(historico, total_individuos=10)

    assert metricas.pico_infectados == 4
    assert metricas.passo_pico == 1
    assert metricas.total_afetados == 6
    assert metricas.taxa_ataque == 0.6
    assert metricas.taxa_ataque_percentual == 60.0
    assert metricas.duracao_surto == 3
    assert metricas.gerar_resumo() == {
        "pico_infectados": 4,
        "passo_pico": 1,
        "total_afetados": 6,
        "taxa_ataque": 0.6,
        "duracao_surto": 3,
        "fracao_final_recuperados": 0.6,
        "ocorreu_infeccao": True,
    }


def test_pico_empata_no_primeiro_passo() -> None:
    historico = (
        RegistroPasso(passo=0, s=8, i=2, r=0),
        RegistroPasso(passo=1, s=8, i=2, r=0),
        RegistroPasso(passo=2, s=7, i=1, r=2),
    )

    metricas = MetricasEpidemia(historico, 10)

    assert metricas.passo_pico == 0


def test_duracao_usa_horizonte_quando_infectados_nao_zeram() -> None:
    historico = (
        RegistroPasso(passo=0, s=8, i=2, r=0),
        RegistroPasso(passo=1, s=7, i=3, r=0),
    )

    metricas = MetricasEpidemia(historico, 10)

    assert metricas.duracao_surto == 1


@pytest.mark.parametrize("historico", [[], ()])
def test_historico_vazio_lanca_value_error(
    historico: list[RegistroPasso] | tuple[RegistroPasso, ...],
) -> None:
    with pytest.raises(ValueError):
        MetricasEpidemia(historico, 10)


def test_historico_com_tipo_invalido_lanca_type_error() -> None:
    with pytest.raises(TypeError):
        MetricasEpidemia("histórico", 10)


def test_historico_com_objeto_invalido_lanca_type_error() -> None:
    with pytest.raises(TypeError):
        MetricasEpidemia([object()], 10)


def test_validacoes_de_populacao_passos_e_consistencia() -> None:
    historico = (RegistroPasso(passo=0, s=8, i=2, r=0),)

    with pytest.raises(TypeError):
        MetricasEpidemia(historico, True)
    with pytest.raises(ValueError):
        MetricasEpidemia(historico, -1)
    metricas_zero = MetricasEpidemia(
        (RegistroPasso(passo=0, s=0, i=0, r=0),),
        0,
    )
    assert metricas_zero.taxa_ataque == 0
    with pytest.raises(ValueError):
        MetricasEpidemia(historico, 11)
    with pytest.raises(ValueError):
        MetricasEpidemia(
            (
                RegistroPasso(passo=1, s=8, i=2, r=0),
            ),
            10,
        )


def test_populacao_zero_produz_metricas_nulas() -> None:
    metricas = MetricasEpidemia((RegistroPasso(passo=0, s=0, i=0, r=0),), 0)

    assert metricas.pico_infectados == 0
    assert metricas.pico_proporcional == 0.0
    assert metricas.taxa_ataque == 0.0
    assert metricas.duracao_extincao == 0


def test_registros_e_metricas_sao_imutaveis() -> None:
    registro = RegistroPasso(passo=0, s=1, i=0, r=0)
    metricas = MetricasEpidemia((registro,), 1)

    with pytest.raises((AttributeError, TypeError)):
        registro.infectados = 1
    with pytest.raises(AttributeError):
        metricas.pico_infectados = 2
