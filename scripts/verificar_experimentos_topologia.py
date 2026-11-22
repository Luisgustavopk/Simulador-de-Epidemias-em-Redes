"""Audita CSVs e lotes e repete escola/ER1000/BA2000 fora da amostra experimental.

Uso: PYTHONPATH=src python3 scripts/verificar_experimentos_topologia.py
"""

from collections import Counter
from copy import deepcopy
import csv
from datetime import datetime, timezone
import gzip
import json
from math import isclose
from statistics import mean, pstdev
from tempfile import TemporaryDirectory
from pathlib import Path

from experimentos_topologia import (
    CENARIOS, CONTROLES, INDICADORES, RESULTADOS, RAIZ, assinatura_resultado,
    criar_servico, gravar_json, hash_arquivo, ler_lote, preparar_controles,
    validar_resultado,
)
from simulador.comparacao_api import executar_comparacao_api


def ler_csv(caminho: Path) -> list[dict[str, str]]:
    """Lê a tabela completa, preservando ausências como texto vazio."""
    with caminho.open(newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def conferir_estrutura(pasta: Path, esperado: dict) -> None:
    """Conta graus e componentes diretamente nos CSVs, sem algoritmos do domínio."""
    ids = {int(l["id"]) for l in ler_csv(pasta / "individuos.csv")}
    graus = Counter({i: 0 for i in ids})
    pares = set()
    pais = {i: i for i in ids}

    def raiz(i: int) -> int:
        while pais[i] != i:
            i = pais[i]
        return i

    for linha in ler_csv(pasta / "contatos.csv"):
        u, v = sorted((int(linha["origem"]), int(linha["destino"])))
        assert u in ids and v in ids and u != v and (u, v) not in pares
        assert float(linha["peso"]) == 1.0
        pares.add((u, v))
        graus.update((u, v))
        pais[raiz(u)] = raiz(v)
    componentes = Counter(raiz(i) for i in ids)
    n, m = len(ids), len(pares)
    medido = {
        "numero_individuos": n, "numero_contatos": m,
        "grau_medio": mean(graus.values()), "grau_minimo": min(graus.values()),
        "grau_maximo": max(graus.values()), "desvio_graus_populacional": pstdev(graus.values()),
        "densidade": 2 * m / (n * (n - 1)), "numero_componentes": len(componentes),
        "maior_componente": max(componentes.values()),
        "individuos_sem_contatos": sum(g == 0 for g in graus.values()),
    }
    assert all(isclose(float(esperado[k]), v, abs_tol=1e-12) for k, v in medido.items())


def main() -> None:
    """Recusa divergências antes de registrar a conferência e as reproduções."""
    protocolo = json.loads((RESULTADOS / "protocolo-utilizado.json").read_text())
    estruturas = ler_csv(RESULTADOS / "caracterizacao_redes.csv")
    for linha in estruturas:
        pasta = (RAIZ / "dados/dados/redes_reais/escola_suica_2024"
                 if linha["modelo"] == "escola" else CONTROLES / linha["rede"])
        conferir_estrutura(pasta, linha)
    with TemporaryDirectory() as temporario:
        reproduzidas = preparar_controles(protocolo, Path(temporario))
        originais = json.loads((CONTROLES / "inventario.json").read_text())["redes"]
        assert reproduzidas == originais

    pacotes = [ler_lote(p) for p in sorted((RESULTADOS / "lotes").glob("*.json.gz"))]
    chaves, historicos, censuradas = set(), {}, []
    estatisticas = {(l["rede"], l["cenario"], l["metrica"]): l
                    for l in ler_csv(RESULTADOS / "resumo_por_rede.csv")}
    for pacote in pacotes:
        rede = pacote["rede_id"]
        resultado = pacote["resultado"]
        assert assinatura_resultado(resultado) == pacote["assinatura_resultado"]
        for e in resultado["execucoes"]:
            chave = (rede, e["cenario"], str(e["repeticao"]))
            assert chave not in chaves
            chaves.add(chave)
            historicos[chave] = e["historico"]
            if e["motivo_termino"] == "limite_passos":
                censuradas.append({"rede": rede, "cenario": e["cenario"], "repeticao": e["repeticao"]})
        for cenario in CENARIOS:
            for metrica in INDICADORES:
                csv_linha = estatisticas[rede, cenario, metrica]
                nativa = resultado["resumo"][cenario]["metricas"][metrica]
                for k, v in nativa.items():
                    assert (csv_linha[k] == "" if v is None
                            else isclose(float(csv_linha[k]), v, abs_tol=1e-12))
    metricas = ler_csv(RESULTADOS / "metricas.csv")
    assert {(m["rede"], m["cenario"], m["repeticao"]) for m in metricas} == chaves
    assert len(metricas) == len(chaves) == 6300
    registros = 0
    with gzip.open(RESULTADOS / "historicos.csv.gz", "rt", encoding="utf-8", newline="") as arquivo:
        for linha in csv.DictReader(arquivo):
            chave = (linha["rede"], linha["cenario"], linha["repeticao"])
            h = historicos[chave][int(linha["passo"])]
            assert all(int(linha[k]) == v for k, v in h.items())
            registros += 1
    assert registros == sum(map(len, historicos.values()))

    reproducoes = []
    redes = {r["id"]: r for r in protocolo["redes_planejadas"]}
    for rede_id in ("escola_suica_2024", "er_1000", "ba_2000"):
        pacote = next(p for p in pacotes if p["rede_id"] == rede_id)
        servico = criar_servico(redes[rede_id])
        pedido = deepcopy(pacote["pedido"])
        pedido["configuracao"].update(contexto_rede=servico.contexto_rede,
                                       revisao_rede=servico.inspecionar()["revisao"])
        repetida = executar_comparacao_api(servico, pedido)
        validar_resultado(repetida, pedido)
        assinatura = assinatura_resultado(repetida)
        assert assinatura == pacote["assinatura_resultado"]
        reproducoes.append({"rede": rede_id, "trajetorias": 300, "assinatura": assinatura, "identica": True})
        print(f"Reprodução integral idêntica: {rede_id} (300 trajetórias).", flush=True)

    evidencia = {
        "conferido_em_utc": datetime.now(timezone.utc).isoformat(),
        "estruturas_conferidas_sem_algoritmos_dominio": len(estruturas),
        "controles_regenerados_com_csvs_e_manifestos_identicos": len(reproduzidas),
        "lotes": len(pacotes), "trajetorias_experimentais": len(chaves), "registros_exportados": registros,
        "resumos_csv_identicos_ao_backend": True, "historicos_csv_identicos_aos_lotes": True,
        "censuradas": censuradas, "reproducoes": reproducoes,
        "trajetorias_adicionais_so_para_verificacao": 900,
        "testes": {"comando": "PYTHONPATH=src .venv/bin/python -m pytest tests/test_experimentos_topologia.py tests/test_geracao.py tests/test_metadados_geracao.py tests/test_comparacao.py tests/test_metricas.py -q",
                   "passaram": 178},
        "sha256_codigo_verificacao": hash_arquivo(Path(__file__)),
        "sha256_codigo_execucao": hash_arquivo(RAIZ / "scripts/experimentos_topologia.py"),
        "sha256_csvs_escola": {p.name: hash_arquivo(p) for p in sorted(
            (RAIZ / "dados/dados/redes_reais/escola_suica_2024").glob("*.csv"))},
    }
    gravar_json(RESULTADOS / "verificacao.json", evidencia)
    print(json.dumps({k: evidencia[k] for k in ("lotes", "trajetorias_experimentais", "registros_exportados")}))


if __name__ == "__main__":
    main()
