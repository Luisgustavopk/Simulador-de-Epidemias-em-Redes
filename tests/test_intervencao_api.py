import pytest

from simulador.api_local import atender
from simulador.carga_rede import ErroCargaRede, ServicoCargaRede
from simulador.configuracao import ErroConfiguracao


def gerar(servico, n):
    resposta = servico.gerar({
        'modelo': 'erdos_renyi', 'numero_individuos': str(n), 'semente': '1',
        'peso': '1', 'probabilidade_contato': '0',
    })
    servico.confirmar(resposta['revisao'])
    return resposta['revisao']


@pytest.fixture
def servico():
    servico = ServicoCargaRede()
    gerar(servico, 50)
    return servico


def formulario(**intervencao):
    return {
        'beta': '.2', 'gamma': '.1', 'modo_peso': 'intensidade',
        'modo_iniciais': 'ids', 'ids_infectados_iniciais': [],
        'semente_epidemia': '1', 'semente_iniciais': '2',
        'semente_isolamento': '900719925474099312345', 'limite_passos': '10',
        'revisao_rede': '1', 'intervencao': {
            'estrategia': 'grau', 'fracao': '0,58', 'inicio': '0',
            'mecanismo': 'desativacao', **intervencao,
        },
    }


def validar(servico, campos):
    return atender(servico, 'POST', '/api/rede/configuracao', {}, campos)


def test_api_deriva_quantidade_da_fracao_e_nao_muda_referencia(servico):
    resultado = validar(servico, formulario())
    assert resultado['configuracao']['intervencao']['quantidade_isolados'] == 29
    assert resultado['configuracao']['intervencao']['mecanismo'] == 'desativacao'
    assert resultado['configuracao']['semente_isolamento'] == '900719925474099312345'
    assert all(not p.isolamento for p in servico.obter_rede_confirmada(1).rede.individuos)


@pytest.mark.parametrize('campo, valor', [
    ('fracao', 'nan'), ('fracao', '-0.1'), ('fracao', True),
    ('inicio', '10'), ('inicio', '1.5'), ('inicio', True),
    ('estrategia', 'inexistente'), ('mecanismo', 'inexistente'),
    ('quantidade_isolados', '5'), ('reducao', '.5'),
])
def test_api_intervencao_rejeita_parametro_invalido_por_campo(servico, campo, valor):
    with pytest.raises(ErroConfiguracao) as erro:
        validar(servico, formulario(**{campo: valor}))
    assert f'intervencao.{campo}' in {p.campo for p in erro.value.problemas}


def test_api_reducao_requer_parametro_e_aceita_limites(servico):
    with pytest.raises(ErroConfiguracao):
        validar(servico, formulario(mecanismo='reducao'))
    for reducao in ('0', '1'):
        resultado = validar(servico, formulario(mecanismo='reducao', reducao=reducao))
        assert resultado['configuracao']['intervencao']['reducao'] == float(reducao)


def test_ausencia_de_intervencao_e_explicita_e_rejeita_objeto_invalido(servico):
    campos = formulario()
    campos['intervencao'] = None
    assert validar(servico, campos)['configuracao']['intervencao'] is None
    for invalido in (False, [], 'nenhuma'):
        with pytest.raises(ErroConfiguracao):
            validar(servico, {**campos, 'intervencao': invalido})


def test_revisao_nova_invalida_orcamento_anterior_e_recalcula(servico):
    assert validar(servico, formulario())['configuracao']['intervencao']['quantidade_isolados'] == 29
    gerar(servico, 3)
    with pytest.raises(ErroCargaRede):
        validar(servico, formulario())
    atual = formulario()
    atual['revisao_rede'] = '2'
    assert validar(servico, atual)['configuracao']['intervencao']['quantidade_isolados'] == 1
