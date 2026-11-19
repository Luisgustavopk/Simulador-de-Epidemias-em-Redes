import pytest

from simulador.api_local import atender
from simulador.carga_rede import ArquivoCSV, ErroCargaRede, ServicoCargaRede
from simulador.configuracao import ErroConfiguracao


ID_GRANDE = '900719925474099312345'


@pytest.fixture
def servico():
    servico = ServicoCargaRede()
    servico.importar_csv(
        ArquivoCSV('contatos.csv', f'origem,destino,peso\n{ID_GRANDE},2,0.4\n'.encode()),
    )
    servico.confirmar(1)
    return servico


def campos(**mudancas):
    return {
        'beta': '0,2', 'gamma': '0.1', 'modo_peso': 'intensidade',
        'modo_iniciais': 'ids', 'ids_infectados_iniciais': [ID_GRANDE],
        'semente_epidemia': '900719925474099312345', 'semente_iniciais': '2',
        'semente_isolamento': '3', 'limite_passos': '30', 'revisao_rede': '1',
        **mudancas,
    }


def validar(servico, corpo):
    return atender(servico, 'POST', '/api/rede/configuracao', {}, corpo)


def test_api_valida_preserva_inteiros_grandes_e_referencia(servico):
    resultado = validar(servico, campos())
    assert resultado['configuracao']['ids_infectados_iniciais'] == [ID_GRANDE]
    assert resultado['configuracao']['semente_epidemia'] == ID_GRANDE
    assert resultado['configuracao']['beta'] == 0.2
    assert servico.inspecionar_individuo(1, ID_GRANDE)['estado'] == 'S'


def test_api_rejeita_campos_incompativeis_sem_corrigir_silenciosamente(servico):
    with pytest.raises(ErroConfiguracao) as erro:
        validar(servico, campos(beta='nan', gamma='Infinity', quantidade_infectados='1', extra=True))
    assert {'beta', 'gamma', 'quantidade_infectados', 'extra'} <= {p.campo for p in erro.value.problemas}


def test_api_rejeita_ids_repetidos_e_numero_js_inseguro(servico):
    for ids in ([ID_GRANDE, ID_GRANDE], [900719925474099312345]):
        with pytest.raises(ErroConfiguracao):
            validar(servico, campos(ids_infectados_iniciais=ids))


def test_api_sorteio_resolvido_e_probabilidade_direta(servico):
    formulario = campos(modo_iniciais='sorteio', quantidade_infectados='2', modo_peso='probabilidade', beta=None)
    del formulario['ids_infectados_iniciais']
    resultado = validar(servico, formulario)
    assert resultado['configuracao']['ids_infectados_iniciais'] == ['2', ID_GRANDE]
    assert resultado['configuracao']['beta'] is None
    assert resultado == validar(servico, formulario)


def test_rede_alterada_invalida_configuracao_previamente_valida(servico):
    validar(servico, campos())
    servico.gerar({'modelo': 'erdos_renyi', 'numero_individuos': '2', 'semente': '1', 'peso': '1', 'probabilidade_contato': '1'})
    with pytest.raises(ErroCargaRede) as erro:
        validar(servico, campos())
    assert erro.value.problemas[0].campo == 'revisao'


def test_rede_nao_confirmada_nao_permite_configuracao():
    servico = ServicoCargaRede()
    servico.gerar({'modelo': 'erdos_renyi', 'numero_individuos': '2', 'semente': '1', 'peso': '1', 'probabilidade_contato': '1'})
    with pytest.raises(ErroCargaRede):
        validar(servico, campos())
