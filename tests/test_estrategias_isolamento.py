from dataclasses import replace

import pytest

from simulador.aleatoriedade import GeradorAleatorio
from simulador.configuracao import ConfiguracaoIntervencao, ConfiguracaoSimulacao, ErroConfiguracao
from simulador.estrategias_isolamento import IsolamentoAleatorio, IsolamentoPorGrau, preparar_estrategia
from simulador.individuo import Individuo
from simulador.isolamento import MecanismoIsolamento, aplicar_isolamento
from simulador.rede_contatos import RedeContatos


@pytest.fixture
def rede():
    rede = RedeContatos()
    for id_individuo in (6, 3, 5, 1, 4, 2):
        rede.adicionar_individuo(Individuo(id_individuo))
    for origem, destino, peso in ((1, 2, .1), (1, 3, .1), (1, 4, .1), (2, 3, 1)):
        rede.adicionar_contato(origem, destino, peso)
    rede.obter_individuo(2).infectar(0)
    rede.obter_individuo(3).infectar(0)
    rede.obter_individuo(3).recuperar()
    return rede


def retrato(rede):
    return (
        {p.id: (p.estado, p.isolamento, p.dia_inicio_infeccao) for p in rede.individuos},
        {(min(c.origem.id, c.destino.id), max(c.origem.id, c.destino.id)): (c.peso, c.ativa) for c in rede.contatos},
    )


def cfg(**campos):
    return replace(ConfiguracaoSimulacao(.2, .1, 42, 43, 44, 20, 1, ()), **campos)


@pytest.mark.parametrize('fracao, populacao, esperado', [(0, 6, 0), (1, 6, 6), (.25, 6, 1), (.58, 50, 29)])
def test_orcamento_e_derivado_da_fracao_com_piso(fracao, populacao, esperado):
    intervencao = ConfiguracaoIntervencao('grau', fracao, 0, MecanismoIsolamento.DESATIVACAO)
    assert intervencao.quantidade_isolados(populacao) == esperado


def test_grau_original_nao_ponderado_desempata_por_id_e_inclui_grau_zero(rede):
    antes = retrato(rede)
    estrategia = IsolamentoPorGrau(rede)
    assert estrategia.selecionar(rede, 1) == (1,)
    assert estrategia.selecionar(rede, 6) == (1, 2, 3, 4, 5, 6)
    assert retrato(rede) == antes


def test_graus_sao_capturados_antes_e_nao_recalculados_depois(rede):
    estrategia = IsolamentoPorGrau(rede)
    copia = rede.copiar()
    aplicar_isolamento(copia, (1,), MecanismoIsolamento.EXCLUSAO, orcamento=1)
    assert copia.grau(copia.obter_individuo(1)) == 0
    assert estrategia.selecionar(copia, 2) == (1, 2)
    graus = estrategia.graus_originais
    graus[1] = 0
    assert estrategia.graus_originais[1] == 3
    with pytest.raises(ValueError):
        IsolamentoPorGrau(copia)


def test_aleatoria_sem_reposicao_reproduz_e_nao_muda_estados_ou_contatos(rede):
    antes = retrato(rede)
    a = IsolamentoAleatorio(GeradorAleatorio(44))
    b = IsolamentoAleatorio(GeradorAleatorio(44))
    ids = a.selecionar(rede, 4)
    assert len(ids) == len(set(ids)) == 4
    assert set(ids) <= {1, 2, 3, 4, 5, 6}
    assert ids == b.selecionar(rede, 4)
    assert set(a.selecionar(rede, 6)) == {1, 2, 3, 4, 5, 6}
    assert retrato(rede) == antes


def test_sorteio_zero_e_entrada_invalida_nao_consumem_fluxo(rede):
    gerador = GeradorAleatorio(44)
    estrategia = IsolamentoAleatorio(gerador)
    assert estrategia.selecionar(rede, 0) == ()
    for quantidade in (-1, 7, True, .5):
        with pytest.raises((ValueError, TypeError)):
            estrategia.selecionar(rede, quantidade)
    assert gerador.uniforme() == GeradorAleatorio(44).uniforme()


def test_fluxo_epidemiologico_nao_e_consumido_pela_selecao(rede):
    epidemia = GeradorAleatorio(42)
    isolamento = GeradorAleatorio(44)
    estrategia = IsolamentoAleatorio(isolamento)
    primeira = estrategia.selecionar(rede, 3)
    segunda = estrategia.selecionar(rede, 3)
    controle = IsolamentoAleatorio(GeradorAleatorio(44))
    assert (primeira, segunda) == (controle.selecionar(rede, 3), controle.selecionar(rede, 3))
    assert epidemia.uniforme() == GeradorAleatorio(42).uniforme()


def test_sem_intervencao_ou_orcamento_zero_nao_prepara_estrategia(rede):
    assert preparar_estrategia(rede, cfg(), revisao_rede=1) is None
    vazia = ConfiguracaoIntervencao('aleatoria', 0, 0, MecanismoIsolamento.DESATIVACAO)
    assert preparar_estrategia(rede, cfg(intervencao=vazia), revisao_rede=1) is None


def test_preparo_exige_revisao_atual_e_referencia_anterior_ao_mecanismo(rede):
    intervencao = ConfiguracaoIntervencao('grau', .5, 0, MecanismoIsolamento.DESATIVACAO)
    with pytest.raises(ErroConfiguracao):
        preparar_estrategia(rede, cfg(intervencao=intervencao), revisao_rede=2)
    aplicar_isolamento(rede, (1,), MecanismoIsolamento.DESATIVACAO, orcamento=1)
    with pytest.raises(ErroConfiguracao):
        preparar_estrategia(rede, cfg(intervencao=intervencao), revisao_rede=1)


@pytest.mark.parametrize('mecanismo', list(MecanismoIsolamento))
def test_selecao_e_mecanismo_preservam_coorte_e_sir(rede, mecanismo):
    referencia = retrato(rede)
    copia = rede.copiar()
    estrategia = IsolamentoPorGrau(rede)
    ids = estrategia.selecionar(copia, 2)
    resultado = aplicar_isolamento(copia, ids, mecanismo, orcamento=2, reducao=.5 if mecanismo is MecanismoIsolamento.REDUCAO else None)
    assert resultado.ids_selecionados == (1, 2)
    assert resultado.numero_contatos_afetados == 4
    assert {p.id: p.estado for p in copia.individuos} == {p.id: p.estado for p in rede.individuos}
    assert copia.numero_individuos == 6
    assert {p.id for p in copia.individuos if p.isolamento} == {1, 2}
    if mecanismo is MecanismoIsolamento.REDUCAO:
        assert copia.obter_contato(1, 2).peso == .05  # compartilhado, reduz uma vez
    elif mecanismo is MecanismoIsolamento.DESATIVACAO:
        assert all(not c.ativa for c in copia.contatos)
    else:
        assert copia.numero_contatos == 0
    assert retrato(rede) == referencia


@pytest.mark.parametrize('ids', [(1, 1), (1, 99), (1, 2, 3)])
def test_mecanismo_rejeita_selecao_invalida_antes_de_mutar(rede, ids):
    antes = retrato(rede)
    with pytest.raises((ValueError, KeyError)):
        aplicar_isolamento(rede, ids, MecanismoIsolamento.DESATIVACAO, orcamento=2)
    assert retrato(rede) == antes


@pytest.mark.parametrize('campo, valor', [
    ('fracao', -1), ('fracao', 1.1), ('fracao', float('nan')),
    ('fracao', float('inf')), ('fracao', True), ('inicio', -1),
    ('inicio', 20), ('inicio', True), ('inicio', .5),
    ('estrategia', 'outra'), ('mecanismo', 'desativacao'), ('reducao', .5),
])
def test_configuracao_intervencao_invalida_identifica_campo(rede, campo, valor):
    intervencao = replace(ConfiguracaoIntervencao('grau', .5, 0, MecanismoIsolamento.DESATIVACAO), **{campo: valor})
    problemas = cfg(intervencao=intervencao).validar(rede, 1)
    assert f'intervencao.{campo}' in {p.campo for p in problemas}


@pytest.mark.parametrize('valor', [None, -1, 2, True, float('nan'), float('inf')])
def test_reducao_exige_fracao_finita_aplicavel(rede, valor):
    intervencao = ConfiguracaoIntervencao('aleatoria', .5, 0, MecanismoIsolamento.REDUCAO, valor)
    assert 'intervencao.reducao' in {p.campo for p in cfg(intervencao=intervencao).validar(rede, 1)}


@pytest.mark.parametrize('mecanismo', list(MecanismoIsolamento))
def test_mecanismo_preserva_contato_que_nao_incide_nos_selecionados(rede, mecanismo):
    rede.adicionar_contato(5, 6, .8)
    copia = rede.copiar()
    ids = IsolamentoPorGrau(rede).selecionar(copia, 2)
    assert ids == (1, 2)
    aplicar_isolamento(copia, ids, mecanismo, orcamento=2, reducao=.5 if mecanismo is MecanismoIsolamento.REDUCAO else None)
    assert copia.obter_contato(5, 6).ativa
    assert copia.obter_contato(5, 6).peso == .8
    assert not copia.obter_individuo(5).isolamento


def test_grau_inclui_contatos_inativos_e_rejeita_populacao_diferente(rede):
    rede.desativar_contato(1, 2)
    estrategia = IsolamentoPorGrau(rede)
    assert estrategia.graus_originais[1] == 3
    assert estrategia.selecionar(rede, 1) == (1,)
    outra = rede.copiar()
    outra.adicionar_individuo(Individuo(99))
    with pytest.raises(ValueError):
        estrategia.selecionar(outra, 1)


@pytest.mark.parametrize('quantidade', [-1, 7, True, .5])
def test_grau_rejeita_quantidade_invalida(rede, quantidade):
    with pytest.raises((ValueError, TypeError)):
        IsolamentoPorGrau(rede).selecionar(rede, quantidade)


def test_invalidez_na_configuracao_nao_muta_rede(rede):
    antes = retrato(rede)
    invalida = ConfiguracaoIntervencao('grau', float('nan'), 0, MecanismoIsolamento.REDUCAO, .5)
    with pytest.raises(ErroConfiguracao):
        preparar_estrategia(rede, cfg(intervencao=invalida), revisao_rede=1)
    assert retrato(rede) == antes
