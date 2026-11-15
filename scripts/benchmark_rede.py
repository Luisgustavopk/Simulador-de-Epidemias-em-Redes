"""Mede geração, percursos e paginação opcional, sem limites de aprovação."""

import argparse
from collections.abc import Callable
import json
import platform
from statistics import median
from time import perf_counter
import tracemalloc

from simulador import ServicoCargaRede, bfs, dfs, gerar_erdos_renyi


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


def percorrer_paginas(
    servico: ServicoCargaRede, revisao: int, numero_contatos: int,
) -> int:
    """Consulta todas as páginas sem acumular os contatos em outra coleção."""
    return sum(
        len(servico.listar_contatos(revisao, inicio=inicio, limite=50)["contatos"])
        for inicio in range(0, numero_contatos, 50)
    )


def main() -> None:
    """Imprime JSON com ambiente, parâmetros e medições locais reproduzíveis."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-er", type=inteiro_positivo, default=6000)
    parser.add_argument("--n-dfs", type=inteiro_positivo, default=700)
    parser.add_argument("--repeticoes", type=inteiro_positivo, default=3)
    parser.add_argument(
        "--n-carga", type=inteiro_positivo,
        help="Inclui a paginação de uma rede BA com esta população (mínimo 2).",
    )
    argumentos = parser.parse_args()
    if argumentos.n_carga is not None and argumentos.n_carga < 2:
        parser.error("--n-carga deve ser pelo menos 2.")
    rede_densa = gerar_erdos_renyi(argumentos.n_dfs, 1, semente=42).rede
    operacoes: dict[str, Callable[[], object]] = {
        "er_p_zero": lambda: gerar_erdos_renyi(argumentos.n_er, 0, semente=42),
        "bfs_completa": lambda: bfs(rede_densa, 0),
        "dfs_completa": lambda: dfs(rede_densa, 0),
    }
    if argumentos.n_carga is not None:
        servico = ServicoCargaRede()
        estado = servico.gerar({
            "modelo": "barabasi_albert",
            "numero_individuos": argumentos.n_carga,
            "contatos_por_novo_individuo": min(4, argumentos.n_carga - 1),
            "semente": 42,
        })
        operacoes["paginas_contatos"] = lambda: percorrer_paginas(
            servico, estado["revisao"], estado["resumo"]["numero_contatos"],
        )
    print(json.dumps({
        "python": platform.python_version(),
        "n_er": argumentos.n_er,
        "n_dfs": argumentos.n_dfs,
        "n_carga": argumentos.n_carga,
        "repeticoes": argumentos.repeticoes,
        "semente": 42,
        "medicoes": {
            nome: medir(operacao, argumentos.repeticoes)
            for nome, operacao in operacoes.items()
        },
    }, indent=2))


if __name__ == "__main__":
    main()
