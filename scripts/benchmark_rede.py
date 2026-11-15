"""Mede geração sem contatos e memória dos percursos, sem limites de aprovação."""

import argparse
from collections.abc import Callable
import json
import platform
from statistics import median
from time import perf_counter
import tracemalloc

from simulador import bfs, dfs, gerar_erdos_renyi


def medir(operacao: Callable[[], object], repeticoes: int) -> dict[str, float | int]:
    """Separa tempo sem rastreamento da medição de pico de memória Python."""
    tempos = []
    for _ in range(repeticoes):
        inicio = perf_counter()
        resultado = operacao()
        tempos.append(perf_counter() - inicio)
        del resultado
    tracemalloc.start()
    resultado = operacao()
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    del resultado
    return {"mediana_segundos": median(tempos), "pico_bytes": pico}


def inteiro_positivo(texto: str) -> int:
    """Valida os tamanhos e a quantidade de medições da linha de comando."""
    valor = int(texto)
    if valor < 1:
        raise argparse.ArgumentTypeError("Informe um inteiro positivo.")
    return valor


def main() -> None:
    """Imprime JSON com ambiente, parâmetros e medições locais reproduzíveis."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-er", type=inteiro_positivo, default=6000)
    parser.add_argument("--n-dfs", type=inteiro_positivo, default=700)
    parser.add_argument("--repeticoes", type=inteiro_positivo, default=3)
    argumentos = parser.parse_args()
    rede_densa = gerar_erdos_renyi(argumentos.n_dfs, 1, semente=42).rede
    operacoes: dict[str, Callable[[], object]] = {
        "er_p_zero": lambda: gerar_erdos_renyi(argumentos.n_er, 0, semente=42),
        "bfs_completa": lambda: bfs(rede_densa, 0),
        "dfs_completa": lambda: dfs(rede_densa, 0),
    }
    print(json.dumps({
        "python": platform.python_version(),
        "n_er": argumentos.n_er,
        "n_dfs": argumentos.n_dfs,
        "repeticoes": argumentos.repeticoes,
        "semente": 42,
        "medicoes": {
            nome: medir(operacao, argumentos.repeticoes)
            for nome, operacao in operacoes.items()
        },
    }, indent=2))


if __name__ == "__main__":
    main()
