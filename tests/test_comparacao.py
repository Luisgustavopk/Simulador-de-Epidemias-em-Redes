from dataclasses import replace

import pytest

from simulador.carga_rede import RedeDisponivel
from simulador.comparacao import (
    ErroExecucaoComparacao, PedidoComparacao, ResultadoIndividual, executar_comparacao,
)
from simulador.configuracao import ConfiguracaoIntervencao, ConfiguracaoSimulacao, ErroConfiguracao
from simulador.estrategias_isolamento import preparar_estrategia
from simulador.individuo import EstadoSIR, Individuo
from simulador.isolamento import MecanismoIsolamento, aplicar_isolamento
from simulador.rede_contatos import RedeContatos


@pytest.fixture
def referencia():
    rede = RedeContatos()
    for identificador in (3, 1, 0, 2):
        rede.adicionar_individuo(Individuo(identificador))
    rede.adicionar_contato(0, 1, 0.8)
    rede.adicionar_contato(0, 2, 0.5)
    return RedeDisponivel(rede, 1, {'tipo': 'didatica'})


@pytest.fixture
def pedido():
    return PedidoComparacao(ConfiguracaoSimulacao(
        beta=0.2, gamma=0.1, limite_passos=10, revisao_rede=1,
        semente_epidemia=42, semente_iniciais=43, semente_isolamento=44,
        quantidade_infectados=2,
        intervencao=ConfiguracaoIntervencao('grau', 0.5, 0, MecanismoIsolamento.REDUCAO, 0.5),
    ), repeticoes=2)


def resultado(pico=2, duracao=4):
    return ResultadoIndividual(
        populacao_inicial=4, pico_infectados=pico, passo_pico=0,
        fracao_acumulada=pico / 4, horizonte_observado=10 if duracao is None else duracao,
        duracao_extincao=duracao, motivo_termino='limite_passos' if duracao is None else 'extincao',
        historico=(),
    )


def test_seis_chamadas_preservam_rede_e_condicoes_por_repeticao(referencia, pedido):
    redes = []
    configuracoes = []

    def executar(rede, cfg):
        assert all(p.estado is EstadoSIR.SUSCETIVEL and not p.isolamento for p in rede.individuos)
        assert rede.obter_contato(0, 1).peso == 0.8
        redes.append(rede)
        configuracoes.append(cfg)
        estrategia = preparar_estrategia(rede, cfg, revisao_rede=1)
        if estrategia:
            intervencao = cfg.intervencao
            ids = estrategia.selecionar(rede, 2)
            aplicar_isolamento(rede, ids, intervencao.mecanismo, orcamento=2, reducao=0.5)
        rede.obter_individuo(0).infectar(0)
        return resultado()

    lote = executar_comparacao(referencia, pedido, executar)
    assert [(e.repeticao, e.cenario) for e in lote.execucoes] == [
        (repeticao, cenario) for repeticao in (1, 2)
        for cenario in ('sem_intervencao', 'aleatoria', 'grau')
    ]
    assert len({id(rede) for rede in redes}) == 6
    assert referencia.rede.obter_contato(0, 1).peso == 0.8
    assert all(p.estado is EstadoSIR.SUSCETIVEL for p in referencia.rede.individuos)
    assert [cfg.semente_epidemia for cfg in configuracoes] == [42, 42, 42, 43, 43, 43]
    for indice in (0, 3):
        controle, aleatoria, grau = configuracoes[indice:indice + 3]
        assert controle.ids_infectados_iniciais == aleatoria.ids_infectados_iniciais == grau.ids_infectados_iniciais
        assert len(set(controle.ids_infectados_iniciais)) == 2
        assert controle.intervencao is None
        assert aleatoria.intervencao.estrategia == 'aleatoria'
        assert replace(grau.intervencao, estrategia='aleatoria') == aleatoria.intervencao
    assert lote.pedido.configuracao.quantidade_infectados == 2
    repetido = executar_comparacao(referencia, pedido, lambda rede, cfg: resultado())
    assert repetido == lote


def test_ids_manuais_sao_preservados_entre_repeticoes(referencia, pedido):
    configuracao = replace(pedido.configuracao, quantidade_infectados=None, ids_infectados_iniciais=(0, 1))
    lote = executar_comparacao(referencia, replace(pedido, configuracao=configuracao), lambda rede, cfg: resultado())
    assert all(e.configuracao.ids_infectados_iniciais == (0, 1) for e in lote.execucoes)


@pytest.mark.parametrize('repeticoes', [0, -1, True, 1.5])
def test_lote_invalido_nao_chama_executor(referencia, pedido, repeticoes):
    with pytest.raises(ErroConfiguracao, match='repetições'):
        executar_comparacao(referencia, replace(pedido, repeticoes=repeticoes), lambda *_: pytest.fail('chamada indevida'))


@pytest.mark.parametrize('mudanca', [{'revisao_rede': 2}, {'intervencao': None}])
def test_lote_exige_revisao_atual_e_intervencao(referencia, pedido, mudanca):
    with pytest.raises(ErroConfiguracao):
        executar_comparacao(
            referencia, replace(pedido, configuracao=replace(pedido.configuracao, **mudanca)),
            lambda *_: pytest.fail('chamada indevida'),
        )


def test_falha_individual_identifica_cenario_e_interrompe(referencia, pedido):
    chamadas = []

    def executar(rede, cfg):
        chamadas.append(cfg)
        if len(chamadas) == 2:
            raise ValueError('falha individual')
        return resultado()

    with pytest.raises(ErroExecucaoComparacao) as erro:
        executar_comparacao(referencia, pedido, executar)
    assert (erro.value.repeticao, erro.value.cenario) == (1, 'aleatoria')
    assert str(erro.value.__cause__) == 'falha individual'
    assert len(chamadas) == 2


def test_consolidacao_pareada_trata_zero_aumento_e_censura(referencia, pedido):
    resultados = iter([
        resultado(0, 0), resultado(1, None), resultado(0, 0),
        resultado(4, None), resultado(2, 6), resultado(3, None),
    ])
    lote = executar_comparacao(referencia, pedido, lambda rede, cfg: next(resultados))
    controle = lote.resumo['sem_intervencao']
    aleatoria = lote.resumo['aleatoria']
    assert controle.metricas['pico_infectados'].media == 2
    assert controle.metricas['pico_infectados'].desvio_padrao == pytest.approx(2.8284271247461903)
    assert controle.metricas['pico_proporcional'].media == 0.5
    assert controle.censuradas == 1
    assert controle.proporcao_censuradas == 0.5
    assert controle.motivos_termino == {'extincao': 1, 'limite_passos': 1}
    duracao = controle.metricas['duracao_extincao']
    assert (duracao.n, duracao.ausentes, duracao.media, duracao.desvio_padrao) == (1, 1, 0, None)
    assert aleatoria.diferencas['pico_infectados'].media == 0.5
    assert aleatoria.reducoes['pico_infectados'].n == 1
    assert aleatoria.reducoes['pico_infectados'].media == 0.5
    assert aleatoria.diferencas['duracao_extincao'].n == 0
    assert aleatoria.diferencas['duracao_extincao'].media is None


def test_censura_total_e_uma_observacao(referencia, pedido):
    lote = executar_comparacao(referencia, replace(pedido, repeticoes=1), lambda rede, cfg: resultado(2, None))
    resumo = lote.resumo['grau']
    assert resumo.censuradas == 1
    duracao = resumo.metricas['duracao_extincao']
    assert (duracao.n, duracao.ausentes, duracao.media, duracao.desvio_padrao) == (0, 1, None, None)
    assert resumo.metricas['pico_infectados'].desvio_padrao is None
