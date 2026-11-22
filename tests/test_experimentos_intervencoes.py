"""Regressões da separação das condições, restauração e instrumentação do protocolo."""

from pathlib import Path
from zipfile import ZipFile

import pytest


@pytest.fixture
def executor(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    import experimentos_intervencoes
    return experimentos_intervencoes


def test_mesma_rede_nao_mescla_condicoes_e_duracao_censurada_fica_ausente(executor, tmp_path):
    from simulador import ServicoCargaRede
    from simulador.comparacao_api import executar_comparacao_api

    servico = ServicoCargaRede()
    estado = servico.gerar({"modelo": "erdos_renyi", "numero_individuos": 4,
                            "probabilidade_contato": 1, "peso": 1, "semente": 10})
    servico.confirmar(estado["revisao"])
    protocolo = {"configuracao_api_base": {"modo_peso": "intensidade", "beta": 0, "gamma": 0,
        "modo_iniciais": "sorteio", "quantidade_infectados": 1, "limite_passos": 2,
        "semente_iniciais": "10", "semente_epidemia": "20", "semente_isolamento": "30",
        "intervencao": {"estrategia": "grau", "fracao": .25, "inicio": 0,
                        "mecanismo": "desativacao", "reducao": None}}, "repeticoes_por_lote": 3}
    for nome, beta in (("baixa", 0), ("alta", 1)):
        lote = {"id": nome, "bloco": "D", "rede": "mesma", "beta": beta, "fracao": .25,
                "inicio": 0, "mecanismo": "desativacao", "reducao": None}
        pedido = executor.preparar_pedido(protocolo, lote, servico)
        resultado = executar_comparacao_api(servico, pedido)
        executor.salvar_lote(tmp_path / "lotes" / f"{nome}.json.gz", {
            "lote": lote, "pedido": pedido, "resultado": resultado,
            "validacao": executor.validar_resultado(resultado, pedido)})
    resumo = executor.consolidar(tmp_path)
    linhas = [r for r in resumo["resumos"] if r["metrica"] == "pico_proporcional" and r["cenario"] == "sem_intervencao"]
    assert {r["lote"]: r["media"] for r in linhas} == {"baixa": .25, "alta": 1.0}
    assert all(r["n"] == 3 for r in linhas)
    duracoes = [r for r in resumo["resumos"] if r["metrica"] == "duracao_extincao"]
    assert all(r["media"] is None and r["n"] == 0 and r["ausentes"] == 3 for r in duracoes)
    assert resumo["trajetorias"] == 18 and resumo["censuradas"] == 18
    assert protocolo["configuracao_api_base"]["beta"] == 0


def test_zip_aceita_id_decimal_e_recusa_membro_extra_antes_de_extrair(executor, tmp_path):
    lote = {"id": "D_beta0.0025", "bloco": "D_sensibilidade_beta"}
    arquivo = tmp_path / "lotes/D_beta0.0025.json.gz"
    arquivo.parent.mkdir()
    arquivo.write_bytes(b"bytes preservados")
    digest = executor.hash_arquivo(arquivo)
    arquivo.with_suffix(".gz.sha256").write_text(digest + "\n")
    executor.gravar_json(tmp_path / "execucao.json", {"lotes": [{"id": lote["id"], "sha256": digest}]})
    executor.gravar_json(tmp_path / "protocolo-utilizado.json", {"lotes_planejados": [lote]})
    executor.arquivo_pacote(tmp_path)
    executor.arquivo_pacote(tmp_path, tmp_path / "restaurado")
    assert (tmp_path / "restaurado/lotes" / arquivo.name).read_bytes() == arquivo.read_bytes()
    zip_path = tmp_path / executor.PACOTE
    with ZipFile(zip_path, "a") as pacote:
        pacote.writestr("../extra.txt", b"extra")
    zip_path.with_suffix(".zip.sha256").write_text(executor.hash_arquivo(zip_path))
    with pytest.raises(ValueError, match="Membros inesperados"):
        executor.arquivo_pacote(tmp_path, tmp_path / "recusado")
    assert not (tmp_path / "recusado").exists()


def test_benchmark_separa_cinco_tempos_e_conta_so_a_chamada_instrumentada(executor, monkeypatch):
    import benchmark_etapa3 as benchmark
    from simulador.rede_contatos import RedeContatos

    chamadas = []
    rede = RedeContatos()

    def operacao():
        chamadas.append(rede.copiar())
        return {"assinatura": "igual"}

    valores = iter([0, .2, 1, 1.4, 2, 2.8, 3, 4, 5, 6.2])
    monkeypatch.setattr(benchmark, "perf_counter", lambda: next(valores))
    monkeypatch.setattr(benchmark, "assinatura_resultado", lambda r: r["assinatura"])
    resultado = benchmark.medir(operacao, "igual", 5)
    assert resultado["tempos_segundos"] == pytest.approx([.2, .4, .8, 1, 1.2])
    assert resultado["mediana_segundos"] == pytest.approx(.8)
    assert resultado["copias_rede"] == 1 and len(chamadas) == 7
    assert RedeContatos.copiar.__name__ == "copiar"


def test_benchmark_recusa_divergencia_na_execucao_cronometrada(executor, monkeypatch):
    import benchmark_etapa3 as benchmark
    monkeypatch.setattr(benchmark, "assinatura_resultado", lambda r: r["assinatura"])
    with pytest.raises(ValueError, match="cronometrada divergiu"):
        benchmark.medir(lambda: {"assinatura": "outra"}, "esperada", 5)
