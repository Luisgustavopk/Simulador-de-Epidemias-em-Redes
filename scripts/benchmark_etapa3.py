"""Mede a receita-base na escola, ER 1000 e BA 2000, sequencialmente.

PYTHONPATH=src python3 scripts/benchmark_etapa3.py
Cinco chamadas sem instrumentação, uma com tracemalloc e uma contando cópias.
"""

import gc
import json
from pathlib import Path
from statistics import median
from time import perf_counter
import tracemalloc
from unittest.mock import patch

from experimentos_intervencoes import ambiente, conferir_referencia, preparar_pedido
from experimentos_topologia import (
    DADOS, PROTOCOLO, RESULTADOS, assinatura_rede, assinatura_resultado, criar_servico,
    gravar_csv, gravar_json, hash_arquivo, ler_lote,
)
from simulador.comparacao_api import executar_comparacao_api
from simulador.rede_contatos import RedeContatos


DESTINO = DADOS / "experimentos/desempenho-v1"


def medir(operacao, esperado: str, numero: int) -> dict:
    """Cronometra só a operação; calcula/verifica assinaturas fora do intervalo."""
    tempos = []
    for i in range(numero):
        inicio = perf_counter()
        resultado = operacao()
        tempos.append(perf_counter() - inicio)
        if assinatura_resultado(resultado) != esperado:
            raise ValueError("Execução cronometrada divergiu do lote científico.")
        del resultado
        print(f"  tempo {i + 1}/{numero}: {tempos[-1]:.6f}s", flush=True)
    gc.collect()
    tracemalloc.start()
    try:
        resultado = operacao()
        _, pico = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    if assinatura_resultado(resultado) != esperado:
        raise ValueError("Instrumentação de memória alterou o resultado.")
    del resultado
    print(f"  pico adicional de alocações Python: {pico} bytes", flush=True)
    contador = 0
    original = RedeContatos.copiar

    def contar_copia(rede):
        nonlocal contador
        contador += 1
        return original(rede)

    with patch.object(RedeContatos, "copiar", contar_copia):
        resultado = operacao()
    if assinatura_resultado(resultado) != esperado:
        raise ValueError("Contagem de cópias alterou o resultado.")
    return {"tempos_segundos": tempos, "mediana_segundos": median(tempos),
            "pico_adicional_python_bytes": pico, "copias_rede": contador,
            "assinatura_resultado": esperado, "assinaturas_identicas_nas_7_execucoes": True}


def main() -> None:
    protocolo = json.loads(PROTOCOLO.read_text())
    plano = protocolo["desempenho_planejado"]
    registro = ambiente()
    registro["sha256_executor_benchmark"] = hash_arquivo(Path(__file__))
    registro.update(escopo=plano, medicoes=[])
    redes = {r["id"]: r for r in protocolo["redes_planejadas"]}
    lotes = {l["rede"]: l for l in protocolo["lotes_planejados"] if l["bloco"] == "A_topologias"}
    DESTINO.mkdir(parents=True, exist_ok=True)
    for nome in plano["redes"]:
        print(f"Benchmark: {nome}", flush=True)
        # Importação, geração, confirmação e leitura da referência ficam fora do cronômetro.
        servico = criar_servico(redes[nome])
        pedido = preparar_pedido(protocolo, lotes[nome], servico)
        referencia = servico.obter_rede_confirmada(servico.inspecionar()["revisao"]).rede
        estrutura = assinatura_rede(referencia)
        baseline = ler_lote(RESULTADOS / "lotes" / f"A_{nome}.json.gz")
        if estrutura != baseline["assinatura_rede"]:
            raise ValueError("Rede diferente da utilizada na campanha.")
        if registro["sha256_codigo_dominio"] != json.loads((RESULTADOS / "execucao.json").read_text())["sha256_codigo_dominio"]:
            raise ValueError("Código do domínio diferente do usado na campanha.")
        resultado = medir(lambda: executar_comparacao_api(servico, pedido),
                          baseline["assinatura_resultado"], plano["medicoes_tempo"])
        conferir_referencia(servico, estrutura)
        registro["medicoes"].append({"rede": nome, "populacao": referencia.numero_individuos,
                                     "contatos": referencia.numero_contatos,
                                     "assinatura_rede": estrutura, "pedido": pedido,
                                     "trajetorias_por_chamada": baseline["validacao"]["execucoes"],
                                     "registros_por_chamada": baseline["validacao"]["registros"], **resultado})
        gravar_json(DESTINO / "medicoes.json", registro)
    registro["concluido"] = True
    gravar_json(DESTINO / "medicoes.json", registro)
    gravar_csv(DESTINO / "resumo.csv", ("rede", "trajetorias", "registros", "mediana_segundos",
                                       "pico_adicional_python_bytes", "copias_rede"),
               ((m["rede"], m["trajetorias_por_chamada"], m["registros_por_chamada"], m["mediana_segundos"],
                 m["pico_adicional_python_bytes"], m["copias_rede"]) for m in registro["medicoes"]))
    gravar_csv(DESTINO / "tempos.csv", ("rede", "medicao", "segundos"),
               ((m["rede"], i, t) for m in registro["medicoes"] for i, t in enumerate(m["tempos_segundos"], 1)))
    gravar_json(DESTINO / "verificacao.json", {"concluida": True, "redes": 3, "cronometragens": 15,
                "execucoes_com_tracemalloc": 3, "execucoes_com_contagem_copias": 3,
                "trajetorias_extras_fora_da_amostra": 6300, "todas_assinaturas_identicas_ao_bloco_A": True,
                "sha256_medicoes": hash_arquivo(DESTINO / "medicoes.json")})
    print("Benchmark concluído nas três redes.", flush=True)


if __name__ == "__main__":
    main()
