"""Verificações dos artefatos científicos, sem substituir o motor da aplicação."""

from copy import deepcopy
import json
from pathlib import Path
import runpy
from zipfile import ZipFile

import pytest


EXECUTOR = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/experimentos_topologia.py"))


def lote_minimo():
    """Monta extinção no instante de intervenção para verificar a ausência de isolamento."""
    cfg = {"beta": 0.005, "gamma": 0.1, "modo_peso": "intensidade", "limite_passos": 2,
           "quantidade_infectados": 1, "semente_epidemia": "42", "semente_iniciais": "43",
           "semente_isolamento": "44", "intervencao": {"estrategia": "grau", "fracao": 0.5,
           "inicio": 1, "mecanismo": "desativacao", "reducao": None}}
    pedido = {"configuracao": cfg, "repeticoes": 1}
    execucoes = []
    for cenario in EXECUTOR["CENARIOS"]:
        receita = {k: cfg[k] for k in ("beta", "gamma", "modo_peso", "limite_passos")}
        receita.update(ids_infectados_iniciais=["0"], sementes={"epidemia": "42", "iniciais": "43", "isolamento": "44"},
                       intervencao=None if cenario == "sem_intervencao" else {**cfg["intervencao"], "estrategia": cenario})
        execucoes.append({"cenario": cenario, "repeticao": 1, "historico": [
            {"passo": 0, "suscetiveis": 1, "infectados": 1, "recuperados": 0, "isolados": 0},
            {"passo": 1, "suscetiveis": 1, "infectados": 0, "recuperados": 1, "isolados": 0}],
            "metrica": {"pico_infectados": 1, "passo_pico": 0, "pico_proporcional": 0.5,
                        "fracao_acumulada": 0.5, "fracao_final_recuperados": 0.5, "ocorreu_infeccao": True,
                        "horizonte_observado": 1, "duracao_extincao": 1}, "motivo_termino": "extincao",
            "manifesto": {"configuracao": receita, "criado_em": "data_a", "rede": {"contexto": "a"}}})
    return pedido, {"populacao": 2, "execucoes": execucoes, "resumo": {}}


def test_hierarquia_da_peso_igual_as_redes_e_preserva_ausencias():
    base = {"modelo": "erdos_renyi", "cenario": "grau", "metrica": "fracao_acumulada"}
    dados = [{**base, "rede": "a", "n": 1, "media": 1.0, "desvio_padrao": None},
             {**base, "rede": "b", "n": 3, "media": 0.0, "desvio_padrao": 0.0},
             {**base, "rede": "c", "n": 0, "media": None, "desvio_padrao": None}]
    resumo = EXECUTOR["resumo_hierarquico"](dados)[0]
    assert resumo["media"] == 0.5  # A média das quatro trajetórias seria 0.25.
    assert resumo["desvio_padrao"] == pytest.approx(2 ** -0.5)
    assert resumo["numero_redes"] == 3 and resumo["redes_com_observacoes"] == 2
    assert resumo["n_repeticoes_total"] == 4


def test_extincao_no_inicio_da_intervencao_nao_isola_e_metrica_adulterada_falha():
    pedido, resultado = lote_minimo()
    assert EXECUTOR["validar_resultado"](resultado, pedido) == {
        "execucoes": 3, "registros": 6, "repeticoes_pareadas": 1,
    }
    resultado["execucoes"][1]["metrica"]["fracao_acumulada"] = 0
    with pytest.raises(ValueError, match="Métricas diferentes"):
        EXECUTOR["validar_resultado"](resultado, pedido)


def test_checkpoint_recusa_receita_incompativel_e_bytes_alterados(tmp_path):
    pedido, resultado = lote_minimo()
    arquivo = tmp_path / "lote.json.gz"
    pacote = {"pedido": pedido, "resultado": resultado, "identificador_execucao": "receita_a"}
    EXECUTOR["salvar_lote"](arquivo, pacote)
    assert EXECUTOR["ler_lote"](arquivo, "receita_a") == pacote
    with pytest.raises(ValueError, match="Checkpoint incompatível"):
        EXECUTOR["ler_lote"](arquivo, "receita_b")
    arquivo.write_bytes(arquivo.read_bytes() + b"alteracao")
    with pytest.raises(ValueError, match="Hash do lote diferente"):
        EXECUTOR["ler_lote"](arquivo)


def test_assinatura_ignora_datas_contextos_mas_conserva_sementes():
    _, resultado = lote_minimo()
    copia = deepcopy(resultado)
    copia["execucoes"][0]["manifesto"]["criado_em"] = "data_b"
    copia["execucoes"][0]["manifesto"]["rede"]["contexto"] = "b"
    assert EXECUTOR["assinatura_resultado"](resultado) == EXECUTOR["assinatura_resultado"](copia)
    copia["execucoes"][0]["manifesto"]["configuracao"]["sementes"]["epidemia"] = "99"
    assert EXECUTOR["assinatura_resultado"](resultado) != EXECUTOR["assinatura_resultado"](copia)


def test_exportacao_do_controle_preserva_parametros_populacao_e_csv(tmp_path):
    protocolo = {"id": "teste", "redes_planejadas": [{"id": "completa", "tipo": "sintetica",
        "modelo": "erdos_renyi", "parametros": {"numero_individuos": 4, "probabilidade_contato": 1.0, "peso": 1.0},
        "semente": 123, "versao_algoritmo": 1}]}
    [gerada] = EXECUTOR["preparar_controles"](protocolo, tmp_path)
    assert gerada["metadados_geracao"]["semente"] == 123
    assert gerada["indicadores"]["numero_individuos"] == 4
    assert gerada["indicadores"]["numero_contatos"] == 6
    assert gerada["indicadores"]["grau_minimo"] == gerada["indicadores"]["grau_maximo"] == 3
    assert gerada["indicadores"]["densidade"] == 1.0
    hashes = gerada["sha256_csv"]
    assert EXECUTOR["preparar_controles"](protocolo, tmp_path)[0]["sha256_csv"] == hashes


def test_estatistica_nao_converte_ausencia_em_zero():
    assert EXECUTOR["estatistica"]([None, 4]) == {"n": 1, "ausentes": 1, "media": 4, "desvio_padrao": None}
    assert EXECUTOR["estatistica"]([None]) == {"n": 0, "ausentes": 1, "media": None, "desvio_padrao": None}


@pytest.fixture
def pacote_temporario(tmp_path, monkeypatch):
    """Prepara um lote válido e seu registro sem executar eventos epidemiológicos."""
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    restaurador = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/restaurar_artefatos_topologia.py"))
    pedido, resultado = lote_minimo()
    caminho = tmp_path / "lotes/A_teste.json.gz"
    EXECUTOR["salvar_lote"](caminho, {
        "pedido": pedido, "resultado": resultado, "identificador_execucao": "receita_a",
    })
    registro = {"lotes": [{"id": "A_teste", "sha256": EXECUTOR["hash_arquivo"](caminho)}]}
    (tmp_path / "execucao.json").write_text(json.dumps(registro), encoding="utf-8")
    return restaurador, tmp_path


def test_pacote_deterministico_restaura_os_mesmos_bytes_sem_alterar_lotes(pacote_temporario):
    restaurador, pasta = pacote_temporario
    originais = {p.name: p.read_bytes() for p in (pasta / "lotes").iterdir()}
    resumo = restaurador["empacotar_lotes"](pasta)
    arquivo = pasta / restaurador["PACOTE_LOTES"]
    bytes_pacote = arquivo.read_bytes()
    assert resumo["lotes"] == 1 and resumo["arquivos_no_pacote"] == 2
    restaurador["empacotar_lotes"](pasta)
    assert arquivo.read_bytes() == bytes_pacote
    assert restaurador["extrair_lotes"](pasta, pasta / "extraidos") == 1
    assert {p.name: p.read_bytes() for p in (pasta / "extraidos").iterdir()} == originais
    assert {p.name: p.read_bytes() for p in (pasta / "lotes").iterdir()} == originais


def test_pacote_adulterado_falha_antes_de_extrair(pacote_temporario):
    restaurador, pasta = pacote_temporario
    restaurador["empacotar_lotes"](pasta)
    arquivo = pasta / restaurador["PACOTE_LOTES"]
    arquivo.write_bytes(arquivo.read_bytes() + b"alteracao")
    with pytest.raises(ValueError, match="Hash do pacote"):
        restaurador["extrair_lotes"](pasta, pasta / "extraidos")
    assert not (pasta / "extraidos").exists()


@pytest.mark.parametrize("alteracao", ["ausente", "extra", "duplicado", "caminho_inseguro"])
def test_pacote_recusa_cobertura_incorreta_mesmo_com_hash_externo_atualizado(pacote_temporario, alteracao):
    restaurador, pasta = pacote_temporario
    restaurador["empacotar_lotes"](pasta)
    arquivo = pasta / restaurador["PACOTE_LOTES"]
    with ZipFile(arquivo) as pacote:
        membros = [(n, pacote.read(n)) for n in pacote.namelist()]
    if alteracao == "ausente":
        membros.pop()
    elif alteracao in ("extra", "caminho_inseguro"):
        nome = "lotes/extra.txt" if alteracao == "extra" else "../fora.txt"
        membros.append((nome, b"extra"))
    with ZipFile(arquivo, "w") as pacote:
        for nome, conteudo in membros:
            pacote.writestr(nome, conteudo)
        if alteracao == "duplicado":
            with pytest.warns(UserWarning, match="Duplicate name"):
                pacote.writestr(*membros[0])
    arquivo.with_suffix(".zip.sha256").write_text(EXECUTOR["hash_arquivo"](arquivo) + "\n")
    with pytest.raises(ValueError, match="Conteúdo do pacote"):
        restaurador["extrair_lotes"](pasta, pasta / "extraidos")
    assert not (pasta / "extraidos").exists() and not (pasta / "fora.txt").exists()


def test_pacote_recusa_hash_interno_alterado(pacote_temporario):
    restaurador, pasta = pacote_temporario
    restaurador["empacotar_lotes"](pasta)
    arquivo = pasta / restaurador["PACOTE_LOTES"]
    with ZipFile(arquivo) as pacote:
        membros = [(n, pacote.read(n)) for n in pacote.namelist()]
    with ZipFile(arquivo, "w") as pacote:
        for nome, conteudo in membros:
            pacote.writestr(nome, b"0" * 64 + b"\n" if nome.endswith(".sha256") else conteudo)
    arquivo.with_suffix(".zip.sha256").write_text(EXECUTOR["hash_arquivo"](arquivo) + "\n")
    with pytest.raises(ValueError, match="Hash de lote interno"):
        restaurador["extrair_lotes"](pasta, pasta / "extraidos")
    assert not (pasta / "extraidos").exists()


def test_empacotamento_recusa_lote_local_diferente_do_registro(pacote_temporario):
    restaurador, pasta = pacote_temporario
    caminho = pasta / "lotes/A_teste.json.gz"
    caminho.write_bytes(caminho.read_bytes() + b"alteracao")
    with pytest.raises(ValueError, match="Lote diverge"):
        restaurador["empacotar_lotes"](pasta)
    assert not (pasta / restaurador["PACOTE_LOTES"]).exists()
