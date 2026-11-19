from http.client import HTTPConnection
import json
from threading import Thread

import pytest

from simulador.api_local import ServidorCarga


@pytest.fixture
def api():
    servidor = ServidorCarga(0)
    thread = Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    yield servidor
    servidor.shutdown()
    servidor.server_close()
    thread.join(timeout=2)


def enviar(api, rota, dados, cookie=''):
    conexao = HTTPConnection('127.0.0.1', api.server_port, timeout=5)
    conexao.request('POST', rota, json.dumps(dados), {'Content-Type': 'application/json', 'Cookie': cookie})
    resposta = conexao.getresponse()
    resultado = resposta.status, json.loads(resposta.read()), resposta.getheader('Set-Cookie', cookie).split(';')[0]
    conexao.close()
    return resultado


def test_configuracao_http_valida_e_erros_retornam_422_por_campo(api):
    _, rede, cookie = enviar(api, '/api/rede/gerar', {
        'modelo': 'erdos_renyi', 'numero_individuos': '3', 'semente': '1',
        'peso': '1', 'probabilidade_contato': '1',
    })
    enviar(api, '/api/rede/confirmar', {'revisao': rede['revisao']}, cookie)
    campos = {
        'beta': '0.2', 'gamma': '1', 'modo_peso': 'intensidade',
        'modo_iniciais': 'ids', 'ids_infectados_iniciais': ['0'],
        'semente_epidemia': '42', 'semente_iniciais': '43',
        'semente_isolamento': '44', 'limite_passos': '20', 'revisao_rede': '1',
    }
    status, validada, _ = enviar(api, '/api/rede/configuracao', campos, cookie)
    assert status == 200
    assert validada['configuracao']['ids_infectados_iniciais'] == ['0']
    status, invalida, _ = enviar(api, '/api/rede/configuracao', {**campos, 'gamma': 'nan'}, cookie)
    assert status == 422
    assert invalida['problemas'][0]['campo'] == 'gamma'
    status, _, _ = enviar(api, '/api/rede/configuracao', campos)
    assert status == 422
