"""Mede simulações reais, cópias e memória sem impor limites de aprovação."""

import argparse
from collections.abc import Callable
import gc
from hashlib import sha256
import json
import platform
from statistics import median
from time import perf_counter
import tracemalloc
from unittest.mock import patch

from simulador.carga_rede import ServicoCargaRede
from simulador.comparacao_api import executar_comparacao_api, executar_simulacao_api
from simulador.rede_contatos import RedeContatos


def inteiro_positivo(texto: str) -> int:
    """Valida os tamanhos do experimento."""
    valor = int(texto)
    if valor < 1:
        raise argparse.ArgumentTypeError("Informe um inteiro positivo.")
    return valor


def assinatura(resultado: dict[str, object]) -> str:
    """Identifica trajetórias e métricas sem os timestamps dos manifestos."""
    if "execucoes" in resultado:
        dados = {
            "execucoes": [
                {campo: execucao[campo] for campo in (
                    "cenario", "repeticao", "historico", "metrica", "motivo_termino",
                )}
                for execucao in resultado["execucoes"]
            ],
            "resumo": resultado["resumo"],
        }
    else:
        dados = {campo: resultado[campo] for campo in (
            "historico", "metrica", "motivo_termino",
        )}
    return sha256(json.dumps(dados, sort_keys=True).encode()).hexdigest()


def medir(operacao: Callable[[], dict[str, object]], medicoes: int) -> dict[str, object]:
    """Separa tempo, alocações Python e contagem de cópias da rede."""
    tempos = []
    for _ in range(medicoes):
        inicio = perf_counter()
        resultado = operacao()
        tempos.append(perf_counter() - inicio)
        del resultado
    gc.collect()
    tracemalloc.start()
    resultado = operacao()
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    identificador = assinatura(resultado)
    del resultado
    numero_copias = 0
    copiar_original = RedeContatos.copiar

    def contar_copia(rede: RedeContatos) -> RedeContatos:
        nonlocal numero_copias
        numero_copias += 1
        return copiar_original(rede)

    with patch.object(RedeContatos, "copiar", contar_copia):
        resultado = operacao()
    assert assinatura(resultado) == identificador
    return {
        "mediana_segundos": median(tempos),
        "pico_adicional_python_bytes": pico,
        "copias_rede": numero_copias,
        "assinatura": identificador,
    }


def main() -> None:
    """Executa o cenário BA documentado com sementes fixas."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--populacoes", type=inteiro_positivo, nargs="+", default=[1000, 4000])
    parser.add_argument("--passos", type=inteiro_positivo, default=60)
    parser.add_argument("--repeticoes", type=inteiro_positivo, default=3)
    parser.add_argument("--medicoes", type=inteiro_positivo, default=3)
    argumentos = parser.parse_args()
    if min(argumentos.populacoes) < 5:
        parser.error("Use populações de pelo menos cinco pessoas para BA com m=4.")
    medicoes = []
    for populacao in argumentos.populacoes:
        servico = ServicoCargaRede()
        estado = servico.gerar({
            "modelo": "barabasi_albert", "numero_individuos": populacao,
            "contatos_por_novo_individuo": 4, "semente": 42,
        })
        servico.confirmar(estado["revisao"])
        formulario = {
            "beta": "0.02", "gamma": "0", "modo_peso": "intensidade",
            "modo_iniciais": "ids", "ids_infectados_iniciais": ["0"],
            "semente_epidemia": "42", "semente_iniciais": "43", "semente_isolamento": "44",
            "limite_passos": argumentos.passos, "revisao_rede": estado["revisao"],
            "contexto_rede": servico.contexto_rede, "intervencao": None,
        }
        medicoes.append({
            "cenario": "individual", "populacao": populacao,
            "contatos": estado["resumo"]["numero_contatos"],
            **medir(lambda: executar_simulacao_api(servico, formulario), argumentos.medicoes),
        })
        if populacao == argumentos.populacoes[0]:
            comparada = {**formulario, "intervencao": {
                "estrategia": "grau", "fracao": "0.1", "inicio": 2,
                "mecanismo": "desativacao",
            }}
            pedido = {"configuracao": comparada, "repeticoes": argumentos.repeticoes}
            medicoes.append({
                "cenario": "comparacao", "populacao": populacao,
                "contatos": estado["resumo"]["numero_contatos"],
                "repeticoes": argumentos.repeticoes,
                **medir(lambda: executar_comparacao_api(servico, pedido), argumentos.medicoes),
            })
    print(json.dumps({
        "python": platform.python_version(), "passos": argumentos.passos,
        "medicoes_por_cenario": argumentos.medicoes, "resultados": medicoes,
    }, indent=2))


if __name__ == "__main__":
    main()
