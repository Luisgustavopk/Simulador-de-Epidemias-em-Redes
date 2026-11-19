from dataclasses import replace

import pytest

from simulador.configuracao import (
    ConfiguracaoSimulacao, ErroConfiguracao, aplicar_condicoes_iniciais,
)
from simulador.individuo import EstadoSIR, Individuo
from simulador.rede_contatos import RedeContatos


@pytest.fixture
def rede():
    resultado = RedeContatos()
    for id_individuo in (30, 10, 20):
        resultado.adicionar_individuo(Individuo(id_individuo))
    resultado.adicionar_contato(10, 20, 0.5)
    return resultado


def configuracao(**campos):
    return replace(ConfiguracaoSimulacao(0.2, 0.1, 1, 2, 3, 50, 1, (10,)), **campos)


@pytest.mark.parametrize(('campo', 'valor'), [
    ('beta', -0.1), ('beta', float('nan')), ('beta', float('inf')),
    ('beta', True), ('gamma', 1.1), ('gamma', None), ('gamma', '0.2'),
    ('limite_passos', 0), ('limite_passos', True), ('limite_passos', 2.5),
    ('semente_epidemia', False), ('semente_iniciais', '5'),
    ('semente_isolamento', None), ('modo_peso', 'desconhecido'),
    ('ids_infectados_iniciais', (10, 10)), ('ids_infectados_iniciais', (99,)),
    ('ids_infectados_iniciais', (True,)),
    ('quantidade_infectados', 1), ('revisao_rede', True),
])
def test_validacao_identifica_campo_sem_mutar_rede(rede, campo, valor):
    problemas = configuracao(**{campo: valor}).validar(rede, 1)
    assert campo in {p.campo for p in problemas}
    assert all(p.mensagem for p in problemas)
    assert all(p.estado is EstadoSIR.SUSCETIVEL for p in rede.individuos)


def test_validacao_reune_erros_e_rejeita_revisao_antiga(rede):
    problemas = configuracao(beta=-1, gamma=2, limite_passos=0).validar(rede, 2)
    assert {'beta', 'gamma', 'limite_passos', 'revisao_rede'} <= {p.campo for p in problemas}


@pytest.mark.parametrize('quantidade', [-1, 4, True, 1.5])
def test_sorteio_rejeita_quantidade_invalida(rede, quantidade):
    cfg = configuracao(ids_infectados_iniciais=None, quantidade_infectados=quantidade)
    assert 'quantidade_infectados' in {p.campo for p in cfg.validar(rede, 1)}


def test_sorteio_sem_reposicao_estavel_e_sem_mutar_referencia(rede):
    cfg = configuracao(ids_infectados_iniciais=None, quantidade_infectados=2)
    preparada = cfg.preparar(rede, 1)
    outra = RedeContatos()
    for id_individuo in (10, 20, 30):
        outra.adicionar_individuo(Individuo(id_individuo))
    assert preparada.ids_infectados_iniciais == cfg.preparar(outra, 1).ids_infectados_iniciais
    assert len(set(preparada.ids_infectados_iniciais)) == 2
    assert cfg.ids_infectados_iniciais is None
    assert all(p.estado is EstadoSIR.SUSCETIVEL for p in rede.individuos)
    copia = rede.copiar()
    aplicar_condicoes_iniciais(copia, preparada, 1)
    assert {p.id for p in copia.individuos if p.estado is EstadoSIR.INFECTADO} == set(preparada.ids_infectados_iniciais)
    assert all(p.dia_inicio_infeccao == 0 for p in copia.individuos if p.estado is EstadoSIR.INFECTADO)
    assert all(p.estado is EstadoSIR.SUSCETIVEL for p in rede.individuos)
    with pytest.raises(ErroConfiguracao):
        aplicar_condicoes_iniciais(copia, preparada, 1)


def test_falha_na_inicializacao_nao_aplica_parcialmente(rede):
    rede.obter_individuo(30).infectar(0)
    with pytest.raises(ErroConfiguracao):
        aplicar_condicoes_iniciais(rede, configuracao(), 1)
    assert rede.obter_individuo(10).estado is EstadoSIR.SUSCETIVEL


def test_probabilidade_direta_exige_beta_ausente(rede):
    assert not configuracao(modo_peso='probabilidade', beta=None).validar(rede, 1)
    assert 'beta' in {p.campo for p in configuracao(modo_peso='probabilidade').validar(rede, 1)}


def test_populacao_vazia_e_inicializacao_sem_infectados(rede):
    assert 'rede' in {p.campo for p in configuracao().validar(RedeContatos(), 1)}
    preparada = configuracao(ids_infectados_iniciais=()).preparar(rede, 1)
    aplicar_condicoes_iniciais(rede, preparada, 1)
    assert all(p.estado is EstadoSIR.SUSCETIVEL for p in rede.individuos)
