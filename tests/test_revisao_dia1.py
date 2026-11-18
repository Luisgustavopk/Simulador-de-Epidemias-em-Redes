from unittest.mock import patch

from simulador.aleatoriedade import GeradorAleatorio
from simulador.configuracao import ConfiguracaoSimulacao
from simulador.individuo import EstadoSIR, Individuo
from simulador.motor_sir import MotorSIR
from simulador.rede_contatos import RedeContatos


def test_exposicao_positiva_muito_pequena_nao_e_arredondada_para_zero():
    rede = RedeContatos()
    for id_individuo in (1, 2):
        rede.adicionar_individuo(Individuo(id_individuo))
    rede.adicionar_contato(1, 2, 1e-18)
    rede.obter_individuo(2).infectar(0)
    cfg = ConfiguracaoSimulacao(1.0, 0.0, 1, 2, 3, 10, 1, ())
    gerador = GeradorAleatorio(1)
    with patch.object(gerador, 'uniforme', side_effect=[0.0, 0.9]):
        MotorSIR(gerador).avancar(rede, cfg, 0, revisao_rede=1)
    assert rede.obter_individuo(1).estado is EstadoSIR.INFECTADO
    assert rede.obter_individuo(1).dia_inicio_infeccao == 1
