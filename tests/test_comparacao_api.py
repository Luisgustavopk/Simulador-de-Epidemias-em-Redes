import pytest

from simulador.api_local import atender
from simulador.carga_rede import ErroCargaRede, ServicoCargaRede
from simulador.configuracao import ErroConfiguracao


@pytest.fixture
def servico():
    carga = ServicoCargaRede()
    carga.gerar({
        'modelo': 'erdos_renyi', 'numero_individuos': '3', 'semente': '1',
        'peso': '1', 'probabilidade_contato': '1',
    })
    carga.confirmar(1)
    return carga


@pytest.fixture
def campos():
    return {
        'beta': '0.2', 'gamma': '0.1', 'modo_peso': 'intensidade',
        'modo_iniciais': 'sorteio', 'quantidade_infectados': '2',
        'semente_epidemia': '900719925474099312345', 'semente_iniciais': '43',
        'semente_isolamento': '44', 'limite_passos': '20', 'revisao_rede': '1',
        'intervencao': {'estrategia': 'grau', 'fracao': '0.5', 'inicio': '0', 'mecanismo': 'desativacao'},
    }


def validar(servico, campos, repeticoes='2'):
    return atender(servico, 'POST', '/api/rede/comparacao/validar', {}, {
        'configuracao': campos, 'repeticoes': repeticoes,
    })


def test_preparo_preserva_sorteio_e_nao_publica_resultados(servico, campos):
    resposta = validar(servico, campos)
    assert resposta['revisao_rede'] == 1
    assert resposta['repeticoes'] == '2'
    assert resposta['cenarios'] == ['sem_intervencao', 'aleatoria', 'grau']
    assert resposta['quantidade_isolados'] == 1
    assert resposta['intervencao'] == {
        'fracao': 0.5, 'inicio': 0, 'mecanismo': 'desativacao', 'reducao': None,
    }
    assert resposta['quantidade_infectados'] == 2
    assert resposta['modo_iniciais'] == 'sorteio'
    assert resposta['sementes_base']['epidemia'] == '900719925474099312345'
    assert resposta['execucao_disponivel'] is False
    assert 'resultados' not in resposta
    assert all(p.estado.value == 'S' and not p.isolamento for p in servico.obter_rede_confirmada(1).rede.individuos)


@pytest.mark.parametrize('repeticoes', [True, '0', '-1', '1.5', 2.0, '9' * 5000])
def test_api_rejeita_repeticoes_invalidas(servico, campos, repeticoes):
    with pytest.raises(ErroConfiguracao) as erro:
        validar(servico, campos, repeticoes)
    assert [p.campo for p in erro.value.problemas] == ['repeticoes']


def test_api_revalida_revisao_e_intervencao(servico, campos):
    with pytest.raises(ErroCargaRede):
        validar(servico, {**campos, 'revisao_rede': '2'})
    with pytest.raises(ErroConfiguracao) as erro:
        validar(servico, {**campos, 'intervencao': None})
    assert erro.value.problemas[0].campo == 'intervencao'


def test_fracao_nao_numerica_gera_um_diagnostico_da_causa(servico, campos):
    campos['intervencao']['fracao'] = 'abc'
    with pytest.raises(ErroConfiguracao) as erro:
        atender(servico, 'POST', '/api/rede/configuracao', {}, campos)
    assert [p.campo for p in erro.value.problemas] == ['intervencao.fracao']
