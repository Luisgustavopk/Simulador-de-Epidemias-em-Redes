"""Fluxos reais do adaptador HTTP e isolamento das sessões de carga."""

import base64
from http.client import HTTPConnection
import json
from threading import Thread

import pytest

from simulador.api_local import ServidorCarga, VALIDADE_SESSAO


@pytest.fixture
def api():
    servidor = ServidorCarga(0)
    thread = Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    yield servidor
    servidor.shutdown()
    servidor.server_close()
    thread.join(timeout=2)


def solicitar(api, caminho="/api/rede", dados=None, cookie="", headers=None):
    conexao = HTTPConnection("127.0.0.1", api.server_port, timeout=5)
    cabecalhos = {"Cookie": cookie, **(headers or {})}
    if dados is not None:
        cabecalhos.setdefault("Content-Type", "application/json")
    corpo = dados if isinstance(dados, str) else json.dumps(dados) if dados is not None else None
    conexao.request("POST" if dados is not None else "GET", caminho, corpo, cabecalhos)
    resposta = conexao.getresponse()
    novo_cookie = resposta.getheader("Set-Cookie", cookie).split(";", 1)[0]
    status = resposta.status
    resultado = json.loads(resposta.read())
    conexao.close()
    return status, resultado, novo_cookie


def parametros(modelo="barabasi_albert"):
    return {
        "modelo": modelo, "numero_individuos": "30", "semente": "42", "peso": "0,8",
        **({"contatos_por_novo_individuo": "2"} if modelo == "barabasi_albert" else {"probabilidade_contato": "0"}),
    }


def arquivo(nome, conteudo):
    return {"nome": nome, "conteudo_base64": base64.b64encode(conteudo).decode("ascii")}


@pytest.mark.parametrize("modelo", ["barabasi_albert", "erdos_renyi"])
def test_geracao_inspecao_confirmacao_e_copia_para_proximas_etapas(api, modelo):
    status, inicial, cookie = solicitar(api)
    assert status == 200 and not inicial["disponivel"]
    status, rede, _ = solicitar(api, "/api/rede/gerar", parametros(modelo), cookie)
    assert status == 200 and rede["resumo"]["numero_individuos"] == 30
    assert not rede["confirmada"]
    status, previa, _ = solicitar(api, "/api/rede/previa?revisao=1", cookie=cookie)
    assert status == 200 and len(previa["individuos"]) == 30
    assert not previa["parcial"]
    assert len(previa["contatos"]) == rede["resumo"]["numero_contatos"]
    for rota, campo in (("individuos", "individuos"), ("contatos", "contatos")):
        status, pagina, _ = solicitar(api, f"/api/rede/{rota}?revisao=1&limite=10", cookie=cookie)
        assert status == 200 and len(pagina[campo]) <= 10
    status, pessoa, _ = solicitar(api, "/api/rede/individuo?revisao=1&id=0", cookie=cookie)
    assert status == 200 and pessoa["estado"] == "S" and not pessoa["isolamento"]
    status, confirmada, _ = solicitar(api, "/api/rede/confirmar", {"revisao": 1}, cookie)
    assert status == 200 and confirmada["confirmada"]
    sessao = api.sessao(cookie)[1]
    copia = sessao.servico.obter_rede_confirmada(1)
    copia.rede.obter_individuo(0).infectar(0)
    assert solicitar(api, "/api/rede/individuo?revisao=1&id=0", cookie=cookie)[1]["estado"] == "S"


def test_sessoes_independentes_e_persistencia_apos_recarregar(api):
    _, rede, cookie = solicitar(api, "/api/rede/gerar", parametros())
    assert solicitar(api, cookie=cookie)[1] == rede
    _, outra, outro_cookie = solicitar(api)
    assert not outra["disponivel"] and outro_cookie != cookie


def test_importacao_preserva_ids_grandes_pessoas_sem_contatos_e_bytes(api):
    id_grande = "900719925474099312345"
    dados = {
        "arquivo_contatos": arquivo("rede.csv", f"origem,destino,peso\n{id_grande},2,0.5\n".encode()),
        "arquivo_individuos": arquivo("pessoas.csv", f"id\n{id_grande}\n2\n-1\n".encode()),
    }
    status, rede, cookie = solicitar(api, "/api/rede/importar", dados)
    assert status == 200 and rede["resumo"]["individuos_sem_contatos"] == 1
    status, pessoa, _ = solicitar(api, f"/api/rede/individuo?revisao=1&id={id_grande}", cookie=cookie)
    assert status == 200 and pessoa["id"] == id_grande
    status, previa, _ = solicitar(api, "/api/rede/previa?revisao=1", cookie=cookie)
    assert status == 200 and id_grande in [p["id"] for p in previa["individuos"]]


def test_falha_de_importacao_nao_substitui_rede_confirmada(api):
    _, _, cookie = solicitar(api, "/api/rede/gerar", parametros())
    _, confirmada, _ = solicitar(api, "/api/rede/confirmar", {"revisao": 1}, cookie)
    status, erro, _ = solicitar(api, "/api/rede/importar", {
        "arquivo_contatos": arquivo("erros.csv", b"origem,destino,peso\n1,2,nan\n"),
    }, cookie)
    assert status == 422
    assert erro["problemas"][0]["linha"] == 2
    assert erro["problemas"][0]["arquivo"] == "erros.csv"
    assert solicitar(api, cookie=cookie)[1] == confirmada


def test_nova_rede_exige_nova_confirmacao_e_revisao_atual(api):
    _, _, cookie = solicitar(api, "/api/rede/gerar", parametros())
    solicitar(api, "/api/rede/confirmar", {"revisao": 1}, cookie)
    _, nova, _ = solicitar(api, "/api/rede/gerar", parametros("erdos_renyi"), cookie)
    assert nova["revisao"] == 2 and not nova["confirmada"]
    assert solicitar(api, "/api/rede/confirmar", {"revisao": 1}, cookie)[0] == 409


def test_previa_parcial_e_metricas_completas(api):
    dados = {**parametros(), "numero_individuos": "200"}
    _, rede, cookie = solicitar(api, "/api/rede/gerar", dados)
    _, previa, _ = solicitar(api, "/api/rede/previa?revisao=1", cookie=cookie)
    assert previa["parcial"] and len(previa["individuos"]) == 180
    assert previa["total_individuos"] == rede["resumo"]["numero_individuos"] == 200
    ids = {p["id"] for p in previa["individuos"]}
    assert all(c["origem"] in ids and c["destino"] in ids for c in previa["contatos"])


@pytest.mark.parametrize("dados", ["{", "[]", '"texto"'])
def test_corpo_json_invalido_recebe_diagnostico(api, dados):
    status, erro, _ = solicitar(api, "/api/rede/gerar", dados)
    assert status in (400, 422) and erro["problemas"][0]["campo"] == "formulario"


@pytest.mark.parametrize("dados", [{}, {"arquivo_contatos": {}}, {"arquivo_contatos": {"nome": "x", "conteudo_base64": "???"}}])
def test_upload_invalido_nao_escapa_como_excecao_interna(api, dados):
    status, erro, _ = solicitar(api, "/api/rede/importar", dados)
    assert status == 422 and erro["problemas"][0]["campo"] == "arquivo_contatos"


@pytest.mark.parametrize("headers,status", [
    ({"Origin": "https://outro-site.example"}, 403),
    ({"Host": "outro-site.example"}, 403),
    ({"Content-Type": "text/plain"}, 415),
    ({"Content-Length": "9000000"}, 413),
])
def test_adaptador_recusa_origem_formato_e_corpo_inadequados(api, headers, status):
    assert solicitar(api, "/api/rede/gerar", parametros(), headers=headers)[0] == status


def test_id_inexistente_e_paginacao_invalida_tem_diagnostico(api):
    _, _, cookie = solicitar(api, "/api/rede/gerar", parametros())
    assert solicitar(api, "/api/rede/individuo?revisao=1&id=999", cookie=cookie)[0] == 422
    assert solicitar(api, "/api/rede/individuos?revisao=1&limite=0", cookie=cookie)[0] == 422
    assert solicitar(api, "/api/rede/contatos?revisao=1&inicio=abc", cookie=cookie)[0] == 422


@pytest.mark.parametrize("caminho", ["/api/inexistente", "/api/rede/inexistente?revisao=1"])
def test_rota_inexistente_nao_e_confundida_com_revisao_antiga(api, caminho):
    status, erro, _ = solicitar(api, caminho)
    assert status == 404
    assert erro["problemas"][0]["campo"] == "rota"


def test_metodo_incorreto_informa_metodo_permitido_e_nao_cria_rede(api):
    conexao = HTTPConnection("127.0.0.1", api.server_port, timeout=5)
    try:
        conexao.request("GET", "/api/rede/gerar")
        resposta = conexao.getresponse()
        assert resposta.status == 405
        assert resposta.getheader("Allow") == "POST"
        assert json.loads(resposta.read())["problemas"][0]["campo"] == "metodo"
    finally:
        conexao.close()
    assert not solicitar(api)[1]["disponivel"]


def test_sessao_expirada_perde_rede_e_confirma_antiga_e_recusada(api):
    _, _, cookie = solicitar(api, "/api/rede/gerar", parametros())
    solicitar(api, "/api/rede/confirmar", {"revisao": 1}, cookie)
    api.sessao(cookie)[1].ultimo_acesso -= VALIDADE_SESSAO + 1

    status, atual, novo_cookie = solicitar(api, cookie=cookie)
    assert status == 200
    assert novo_cookie != cookie
    assert atual["revisao"] == 0
    assert not atual["disponivel"] and not atual["confirmada"]
    status, erro, _ = solicitar(api, "/api/rede/confirmar", {"revisao": 1}, novo_cookie)
    assert status == 422
    assert erro["problemas"][0]["campo"] == "rede"


def test_limite_de_sessoes_mantem_sessao_existente_e_recupera_apos_expiracao(api, monkeypatch):
    monkeypatch.setattr("simulador.api_local.MAX_SESSOES", 1)
    _, rede, cookie = solicitar(api, "/api/rede/gerar", parametros())
    status, erro, _ = solicitar(api)
    assert status == 503 and erro["problemas"][0]["campo"] == "sessao"
    assert solicitar(api, cookie=cookie)[1] == rede

    api.sessao(cookie)[1].ultimo_acesso -= VALIDADE_SESSAO + 1
    assert solicitar(api)[0] == 200


def test_nome_unicode_do_upload_nao_causa_falha_ao_publicar_resposta(api):
    nome = "rede_acentuação_\ud800.csv"
    status, rede, cookie = solicitar(api, "/api/rede/importar", {
        "arquivo_contatos": arquivo(nome, b"origem,destino,peso\n1,2,1\n"),
    })
    assert status == 200
    assert rede["origem"]["arquivo_contatos"] == nome
    assert solicitar(api, cookie=cookie)[1] == rede
