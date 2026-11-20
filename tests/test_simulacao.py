"""Orquestração temporal e registros SIR."""

import pytest

from simulador import (
    EstadoSIR,
    Individuo,
    RedeContatos,
    RegistroPasso,
    Simulacao,
)


@pytest.fixture
def rede() -> RedeContatos:
    rede = RedeContatos()
    rede.adicionar_individuo(Individuo(0))
    rede.adicionar_individuo(Individuo(1))
    rede.adicionar_individuo(Individuo(2))
    rede.obter_individuo(1).infectar(passo=0)
    rede.obter_individuo(2).isolar()
    return rede


def test_registro_passo_aceita_sir_e_expoe_aliases() -> None:
    registro = RegistroPasso(passo=2, s=4, i=3, r=1, isolados=2)

    assert registro.passo == 2
    assert registro.suscetiveis == registro.s == 4
    assert registro.infectados == registro.i == 3
    assert registro.recuperados == registro.r == 1
    assert registro.isolados == 2


def test_execucao_registra_estado_inicial_isolados_e_limite(
    rede: RedeContatos,
) -> None:
    simulacao = Simulacao(rede, limite_passos=2)

    assert simulacao.passo_atual == 0
    assert simulacao.historico[0].suscetiveis == 2
    assert simulacao.historico[0].infectados == 1
    assert simulacao.historico[0].recuperados == 0
    assert simulacao.historico[0].isolados == 1

    historico = simulacao.executar()

    assert [registro.passo for registro in historico] == [0, 1, 2]
    assert simulacao.finalizada is True
    assert simulacao.passo_atual == 2


def test_extincao_finaliza_sem_avancar_o_relogio() -> None:
    rede = RedeContatos()
    rede.adicionar_individuo(Individuo(0))

    simulacao = Simulacao(rede)
    registro = simulacao.avancar()

    assert simulacao.isFinalizada()
    assert registro.passo == 0
    assert registro.infectados == 0
    assert len(simulacao.historico) == 1


def test_executar_motor_concentra_evolucao_e_parada(rede: RedeContatos) -> None:
    class MotorFalso:
        def avancar(self, rede, configuracao, passo_atual, *, revisao_rede):
            rede.obter_individuo(1).recuperar()

    class ConfiguracaoFalsa:
        intervencao = None

    simulacao = Simulacao(rede, limite_passos=2)
    historico = simulacao.executar_motor(
        MotorFalso(),
        ConfiguracaoFalsa(),
        revisao_rede=1,
    )

    assert historico[-1].infectados == 0
