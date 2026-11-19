from dataclasses import replace
from unittest.mock import patch

import pytest

from simulador.aleatoriedade import GeradorAleatorio
from simulador.configuracao import ConfiguracaoSimulacao, ErroConfiguracao
from simulador.individuo import EstadoSIR, Individuo
from simulador.isolamento import aplicar_isolamento, MecanismoIsolamento
from simulador.motor_sir import MotorSIR
from simulador.rede_contatos import RedeContatos


def rede_com_contatos(pesos=(0.2, 0.4)):
    rede = RedeContatos()
    for id_individuo in reversed(range(1, len(pesos) + 2)):
        rede.adicionar_individuo(Individuo(id_individuo))
    for outro, peso in enumerate(pesos, 2):
        rede.adicionar_contato(1, outro, peso)
        rede.obter_individuo(outro).infectar(0)
    return rede


def avancar(rede, sorteios, **campos):
    cfg = replace(ConfiguracaoSimulacao(1.0, 0.0, 1, 2, 3, 10, 1, ()), **campos)
    gerador = GeradorAleatorio(cfg.semente_epidemia)
    with patch.object(gerador, 'uniforme', side_effect=sorteios):
        return MotorSIR(gerador).avancar(rede, cfg, 0, revisao_rede=1)


@pytest.mark.parametrize(('sorteio', 'infectado'), [(0.519, True), (0.52, False), (0.521, False)])
def test_multiplas_exposicoes_combinam_em_052_e_limiar_estrito(sorteio, infectado):
    rede = rede_com_contatos()
    assert avancar(rede, [sorteio, 0.8, 0.8]) is None
    assert (rede.obter_individuo(1).estado is EstadoSIR.INFECTADO) is infectado


@pytest.mark.parametrize('gamma', [0.0, 1.0])
def test_beta_zero_impede_contagio_e_recuperacao_respeita_gamma(gamma):
    rede = rede_com_contatos((1.0,))
    avancar(rede, [0.0, 0.0], beta=0.0, gamma=gamma)
    assert rede.obter_individuo(1).estado is EstadoSIR.SUSCETIVEL
    assert rede.obter_individuo(2).estado is (EstadoSIR.RECUPERADO if gamma else EstadoSIR.INFECTADO)


@pytest.mark.parametrize('bloqueio', ['zero', 'desativado', 'excluido'])
def test_contato_sem_exposicao_nao_transmite(bloqueio):
    rede = rede_com_contatos((1.0,))
    if bloqueio == 'zero':
        rede.alterar_peso_contato(1, 2, 0)
    elif bloqueio == 'desativado':
        rede.desativar_contato(1, 2)
    else:
        rede.remover_contato(1, 2)
    avancar(rede, [0.0, 0.9])
    assert rede.obter_individuo(1).estado is EstadoSIR.SUSCETIVEL


def test_cadeia_nao_transmite_em_cascata_e_novo_infectado_nao_recupera():
    rede = RedeContatos()
    for id_individuo in (1, 2, 3):
        rede.adicionar_individuo(Individuo(id_individuo))
    rede.adicionar_contato(1, 2)
    rede.adicionar_contato(2, 3)
    rede.obter_individuo(1).infectar(0)
    avancar(rede, [0.1, 0.0, 0.1], gamma=1.0)
    assert [p.estado for p in rede.individuos] == [EstadoSIR.RECUPERADO, EstadoSIR.INFECTADO, EstadoSIR.SUSCETIVEL]
    assert rede.obter_individuo(2).dia_inicio_infeccao == 1


def test_reducao_parcial_nao_e_anulada_pela_marca_de_isolamento():
    rede = rede_com_contatos((1.0,))
    aplicar_isolamento(rede, [2], mecanismo=MecanismoIsolamento.REDUCAO, orcamento=1, reducao=0.5)
    avancar(rede, [0.49, 0.0], gamma=1.0)
    assert rede.obter_individuo(1).estado is EstadoSIR.INFECTADO
    assert rede.obter_individuo(2).estado is EstadoSIR.RECUPERADO
    assert rede.obter_individuo(2).isolamento
    assert rede.obter_contato(1, 2).peso == 0.5
    assert rede.obter_contato(1, 2).ativa


def test_modo_direto_nao_reaplica_beta():
    rede = rede_com_contatos((0.4,))
    avancar(rede, [0.39, 0.9], modo_peso='probabilidade', beta=None)
    assert rede.obter_individuo(1).estado is EstadoSIR.INFECTADO


def test_motor_preserva_gerador_entre_passos():
    rede = rede_com_contatos((1.0,))
    cfg = ConfiguracaoSimulacao(0.0, 0.0, 42, 2, 3, 10, 1, ())
    gerador = GeradorAleatorio(42)
    controle = GeradorAleatorio(42)
    motor = MotorSIR(gerador)
    for t in range(2):
        motor.avancar(rede, cfg, t, revisao_rede=1)
    for _ in range(4):
        controle.uniforme()
    assert gerador.uniforme() == controle.uniforme()


def test_revisao_invalida_nao_consume_sorteios_nem_aplica_transicoes():
    rede = rede_com_contatos((1.0,))
    gerador = GeradorAleatorio(42)
    cfg = ConfiguracaoSimulacao(1.0, 1.0, 42, 2, 3, 10, 1, ())
    with pytest.raises(ErroConfiguracao):
        MotorSIR(gerador).avancar(rede, cfg, 0, revisao_rede=2)
    assert rede.obter_individuo(1).estado is EstadoSIR.SUSCETIVEL
    assert gerador.uniforme() == GeradorAleatorio(42).uniforme()


@pytest.mark.parametrize('passo', [-1, True, 0.5])
def test_instante_invalido_rejeitado_antes_de_mutar(passo):
    rede = rede_com_contatos((1.0,))
    cfg = ConfiguracaoSimulacao(1.0, 1.0, 1, 2, 3, 10, 1, ())
    with pytest.raises((TypeError, ValueError)):
        MotorSIR(GeradorAleatorio(1)).avancar(rede, cfg, passo, revisao_rede=1)
    assert rede.obter_individuo(1).estado is EstadoSIR.SUSCETIVEL


def test_mesmos_dados_e_semente_independem_da_ordem_de_cadastro():
    primeira = rede_com_contatos()
    segunda = RedeContatos()
    for id_individuo in (1, 2, 3):
        segunda.adicionar_individuo(Individuo(id_individuo))
    for outro, peso in ((3, 0.4), (2, 0.2)):
        segunda.adicionar_contato(1, outro, peso)
        segunda.obter_individuo(outro).infectar(0)
    cfg = ConfiguracaoSimulacao(1.0, 0.5, 42, 2, 3, 10, 1, ())
    for rede in (primeira, segunda):
        MotorSIR(GeradorAleatorio(42)).avancar(rede, cfg, 0, revisao_rede=1)
    assert {p.id: p.estado for p in primeira.individuos} == {p.id: p.estado for p in segunda.individuos}
