"""Gera os controles e executa o bloco A do protocolo, com saídas reproduzíveis.

Uso na raiz: PYTHONPATH=src python3 scripts/experimentos_topologia.py
--somente-controles gera e caracteriza; --somente-consolidar relê os lotes salvos.
As redes e o SIR usam a implementação nativa. Não executa os blocos B, C ou D.
"""

import argparse
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from copy import deepcopy
import csv
from datetime import datetime, timezone
import gzip
from hashlib import sha256
from io import TextIOWrapper
import json
import os
from pathlib import Path
import platform
from statistics import mean, pstdev, stdev
import subprocess
from time import perf_counter
from typing import Any

from simulador import ArquivoCSV, ServicoCargaRede, componentes_conexas, importar_rede_csv
from simulador.comparacao_api import executar_comparacao_api
from simulador.geracao import reconstruir_rede
from simulador.rede_contatos import RedeContatos


RAIZ = Path(__file__).resolve().parents[1]
DADOS = RAIZ / "dados/dados"
PROTOCOLO = DADOS / "experimentos/protocolo-etapa3-v1.json"
CONTROLES = DADOS / "redes_sinteticas/controles-etapa3-v1"
RESULTADOS = DADOS / "experimentos/topologia-v1"
INDICADORES = (
    "pico_infectados", "pico_proporcional", "passo_pico", "fracao_acumulada",
    "fracao_final_recuperados", "horizonte_observado", "duracao_extincao",
)
PRIMARIOS = ("pico_proporcional", "fracao_acumulada")
CENARIOS = ("sem_intervencao", "aleatoria", "grau")


def hash_arquivo(caminho: Path) -> str:
    """Calcula SHA-256 dos bytes de um arquivo."""
    return sha256(caminho.read_bytes()).hexdigest()


def hash_json(valor: object) -> str:
    """Identifica conteúdo JSON sem depender da ordem das chaves."""
    return sha256(json.dumps(valor, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def gravar_json(caminho: Path, valor: object) -> None:
    """Substitui JSON completo de forma atômica, mantendo legibilidade."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(caminho.suffix + ".tmp")
    temporario.write_text(json.dumps(valor, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporario.replace(caminho)


def gravar_csv(caminho: Path, colunas: tuple[str, ...], linhas: Iterable[Iterable[object]]) -> None:
    """Grava CSV com valores completos, sem arredondamento de apresentação."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo, lineterminator="\n")
        escritor.writerow(colunas)
        escritor.writerows(linhas)


@contextmanager
def texto_gzip(caminho: Path) -> Iterator[TextIOWrapper]:
    """Abre CSV gzip sem nome ou data no cabeçalho para conservar seu hash."""
    with caminho.open("wb") as binario:
        with gzip.GzipFile(filename="", mode="wb", fileobj=binario, mtime=0) as comprimido:
            with TextIOWrapper(comprimido, encoding="utf-8", newline="") as texto:
                yield texto


def assinatura_rede(rede: RedeContatos) -> str:
    """Identifica cadastro, pares, pesos e disponibilidade sem objetos mutáveis."""
    return hash_json({
        "ids": sorted(p.id for p in rede.iter_individuos()),
        "contatos": sorted(
            (min(c.origem.id, c.destino.id), max(c.origem.id, c.destino.id), c.peso, c.ativa)
            for c in rede.iter_contatos()
        ),
    })


def caracterizar_rede(rede: RedeContatos, pasta: Path) -> dict[str, int | float]:
    """Exporta graus, frequências e componentes, incluindo indivíduos de grau zero."""
    graus = {p.id: rede.grau(p) for p in rede.iter_individuos()}
    frequencias = Counter(graus.values())
    grupos = sorted(componentes_conexas(rede), key=lambda g: min(g))
    n, m = rede.numero_individuos, rede.numero_contatos
    indicadores = {
        "numero_individuos": n, "numero_contatos": m,
        "grau_medio": mean(graus.values()) if n else 0.0,
        "grau_minimo": min(graus.values(), default=0), "grau_maximo": max(graus.values(), default=0),
        "desvio_graus_populacional": pstdev(graus.values()) if n else 0.0,
        "densidade": 2 * m / (n * (n - 1)) if n > 1 else 0.0,
        "numero_componentes": len(grupos), "maior_componente": max(map(len, grupos), default=0),
        "individuos_sem_contatos": frequencias[0],
    }
    if sum(graus.values()) != 2 * m or sum(map(len, grupos)) != n:
        raise ValueError("Contagem estrutural inconsistente.")
    gravar_csv(pasta / "graus.csv", ("id", "grau"), sorted(graus.items()))
    gravar_csv(pasta / "distribuicao_graus.csv", ("grau", "numero_individuos", "fracao"), (
        (k, frequencias[k], frequencias[k] / n) for k in range(n)
    ))
    gravar_csv(pasta / "componentes.csv", ("componente", "numero_individuos", "ids"), (
        (i, len(g), " ".join(map(str, sorted(g)))) for i, g in enumerate(grupos, 1)
    ))
    return indicadores


def preparar_controles(protocolo: dict[str, Any], destino: Path = CONTROLES) -> list[dict[str, Any]]:
    """Gera ER/BA pelas sementes do protocolo e verifica a reimportação dos CSVs."""
    inventario = []
    for especificacao in protocolo["redes_planejadas"]:
        if especificacao["tipo"] != "sintetica":
            continue
        metadados = {k: especificacao[k] for k in ("modelo", "parametros", "semente", "versao_algoritmo")}
        gerada = reconstruir_rede(metadados)
        rede = gerada.rede
        pasta = destino / especificacao["id"]
        gravar_csv(pasta / "individuos.csv", ("id",), ((p.id,) for p in rede.iter_individuos()))
        gravar_csv(pasta / "contatos.csv", ("origem", "destino", "peso"), sorted(
            (min(c.origem.id, c.destino.id), max(c.origem.id, c.destino.id), c.peso)
            for c in rede.iter_contatos()
        ))
        indicadores = caracterizar_rede(rede, pasta)
        importada = importar_rede_csv(pasta / "contatos.csv", arquivo_individuos=pasta / "individuos.csv").rede
        if assinatura_rede(importada) != assinatura_rede(rede):
            raise ValueError(f"Exportação divergiu da rede gerada: {especificacao['id']}")
        registro = {
            "rede_id": especificacao["id"], "metadados_geracao": gerada.exportar_metadados(),
            "indicadores": indicadores, "assinatura_rede": assinatura_rede(rede),
            "sha256_csv": {p.name: hash_arquivo(p) for p in sorted(pasta.glob("*.csv"))},
            "sha256_gerador": hash_arquivo(RAIZ / "src/simulador/geracao.py"),
            "biblioteca_grafos": "implementacao_nativa_simulador", "reimportacao_identica": True,
        }
        gravar_json(pasta / "manifesto.json", registro)
        inventario.append(registro)
    gravar_json(destino / "inventario.json", {"protocolo": protocolo["id"], "redes": inventario})
    return inventario


def criar_servico(especificacao: dict[str, Any], controles: Path = CONTROLES) -> ServicoCargaRede:
    """Carrega a escola ou gera um controle e confere a identidade com o CSV salvo."""
    servico = ServicoCargaRede()
    if especificacao["tipo"] == "observada":
        pasta = RAIZ / especificacao["pasta"]
        estado = servico.importar_csv(
            ArquivoCSV("contatos.csv", (pasta / "contatos.csv").read_bytes()),
            arquivo_individuos=ArquivoCSV("individuos.csv", (pasta / "individuos.csv").read_bytes()),
        )
    else:
        pasta = controles / especificacao["id"]
        estado = servico.gerar({
            "modelo": especificacao["modelo"], "semente": especificacao["semente"],
            **especificacao["parametros"],
        })
    servico.confirmar(estado["revisao"])
    referencia = servico.obter_rede_confirmada(estado["revisao"])
    importada = importar_rede_csv(pasta / "contatos.csv", arquivo_individuos=pasta / "individuos.csv").rede
    if assinatura_rede(importada) != assinatura_rede(referencia.rede):
        raise ValueError(f"A rede da execução diverge do CSV: {especificacao['id']}")
    return servico


def assinatura_resultado(resultado: dict[str, Any]) -> str:
    """Compara todas as trajetórias, métricas e receitas efetivas, sem datas/contextos."""
    return hash_json({
        "execucoes": [{
            **{k: e[k] for k in ("repeticao", "cenario", "metrica", "motivo_termino", "historico")},
            "configuracao": e["manifesto"]["configuracao"],
        } for e in resultado["execucoes"]],
        "resumo": resultado["resumo"],
    })


def validar_resultado(resultado: dict[str, Any], pedido: dict[str, Any]) -> dict[str, int]:
    """Recalcula indicadores e verifica conservação, pareamento, sementes e censura."""
    cfg = pedido["configuracao"]
    repeticoes, n = pedido["repeticoes"], resultado["populacao"]
    esperadas = {(r, c) for r in range(1, repeticoes + 1) for c in CENARIOS}
    encontradas = {(e["repeticao"], e["cenario"]) for e in resultado["execucoes"]}
    if encontradas != esperadas or len(resultado["execucoes"]) != len(esperadas):
        raise ValueError("Execuções ausentes ou repetidas no lote.")
    iniciais: dict[int, list[str]] = {}
    registros = 0
    for e in resultado["execucoes"]:
        h = e["historico"]
        receita = e["manifesto"]["configuracao"]
        r = e["repeticao"]
        if any(receita[k] != cfg[k] for k in ("beta", "gamma", "modo_peso", "limite_passos")):
            raise ValueError("Parâmetros efetivos diferentes do pedido.")
        inter_esperada = None if e["cenario"] == "sem_intervencao" else {
            **cfg["intervencao"], "estrategia": e["cenario"],
        }
        if receita["intervencao"] != inter_esperada:
            raise ValueError("Intervenção efetiva diferente do cenário.")
        if [p["passo"] for p in h] != list(range(len(h))):
            raise ValueError("Histórico com lacunas ou instantes repetidos.")
        if h[0]["infectados"] != cfg["quantidade_infectados"] or h[0]["recuperados"] != 0:
            raise ValueError("Condições iniciais diferentes da receita.")
        ids = receita["ids_infectados_iniciais"]
        if len(set(ids)) != cfg["quantidade_infectados"] or iniciais.setdefault(r, ids) != ids:
            raise ValueError("Iniciais diferentes entre os cenários pareados.")
        for fluxo in ("epidemia", "iniciais", "isolamento"):
            if int(receita["sementes"][fluxo]) != int(cfg[f"semente_{fluxo}"]) + r - 1:
                raise ValueError("Derivação de semente diferente do protocolo.")
        inicio, k = cfg["intervencao"]["inicio"], int(n * cfg["intervencao"]["fracao"])
        aplicada = e["cenario"] != "sem_intervencao" and any(
            p["passo"] == inicio and p["infectados"] > 0 and p["passo"] < cfg["limite_passos"] for p in h
        )
        for i, p in enumerate(h):
            if any(type(p[c]) is not int or p[c] < 0 for c in ("suscetiveis", "infectados", "recuperados", "isolados")):
                raise ValueError("Contagem inválida no histórico.")
            if p["suscetiveis"] + p["infectados"] + p["recuperados"] != n:
                raise ValueError("População não conservada.")
            if p["isolados"] != (k if aplicada and p["passo"] >= inicio else 0):
                raise ValueError("Orçamento ou instante da intervenção incorreto.")
            if i and (p["suscetiveis"] > h[i - 1]["suscetiveis"] or p["recuperados"] < h[i - 1]["recuperados"]):
                raise ValueError("Transição incompatível com SIR sem reinfecção.")
            if i < len(h) - 1 and p["infectados"] == 0:
                raise ValueError("Execução continuou depois da extinção.")
        final = h[-1]
        pico = max(p["infectados"] for p in h)
        metricas = {
            "pico_infectados": pico,
            "passo_pico": next(p["passo"] for p in h if p["infectados"] == pico),
            "pico_proporcional": pico / n,
            "fracao_acumulada": (final["infectados"] + final["recuperados"]) / n,
            "fracao_final_recuperados": final["recuperados"] / n,
            "horizonte_observado": final["passo"],
            "duracao_extincao": final["passo"] if final["infectados"] == 0 else None,
            "ocorreu_infeccao": any(p["infectados"] > 0 for p in h),
        }
        if e["metrica"] != metricas:
            raise ValueError("Métricas diferentes do recálculo independente do histórico.")
        motivo = "extincao" if final["infectados"] == 0 else "limite_passos"
        if e["motivo_termino"] != motivo or (motivo == "limite_passos" and final["passo"] != cfg["limite_passos"]):
            raise ValueError("Parada ou censura incorreta.")
        registros += len(h)
    return {"execucoes": len(esperadas), "registros": registros, "repeticoes_pareadas": len(iniciais)}


def salvar_lote(caminho: Path, pacote: dict[str, Any]) -> None:
    """Salva JSON integral gzip determinístico e seu hash, sem depender da sessão HTTP."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(".tmp")
    dados = json.dumps(pacote, ensure_ascii=False, separators=(",", ":")).encode()
    temporario.write_bytes(gzip.compress(dados, mtime=0))
    temporario.replace(caminho)
    caminho.with_suffix(caminho.suffix + ".sha256").write_text(hash_arquivo(caminho) + "\n")


def ler_lote(caminho: Path, identificador: str | None = None) -> dict[str, Any]:
    """Recusa alterações de conteúdo ou checkpoint de outra receita/código/entrada."""
    esperado = caminho.with_suffix(caminho.suffix + ".sha256").read_text().strip()
    if hash_arquivo(caminho) != esperado:
        raise ValueError(f"Hash do lote diferente: {caminho.name}")
    pacote = json.loads(gzip.decompress(caminho.read_bytes()))
    if identificador is not None and pacote["identificador_execucao"] != identificador:
        raise ValueError(f"Checkpoint incompatível: {caminho.name}")
    validar_resultado(pacote["resultado"], pacote["pedido"])
    return pacote


def estatistica(valores: list[float | int | None]) -> dict[str, int | float | None]:
    """Separa valores ausentes e usa desvio amostral somente com duas observações."""
    presentes = [v for v in valores if v is not None]
    return {"n": len(presentes), "ausentes": len(valores) - len(presentes),
            "media": mean(presentes) if presentes else None,
            "desvio_padrao": stdev(presentes) if len(presentes) > 1 else None}


def resumo_hierarquico(por_rede: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Dá peso igual às médias das redes, sem tratar repetições como topologias."""
    grupos: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for linha in por_rede:
        grupos[linha["modelo"], linha["cenario"], linha["metrica"]].append(linha)
    saida = []
    for (modelo, cenario, metrica), grupo in sorted(grupos.items()):
        medias = [g["media"] for g in grupo if g["media"] is not None]
        desvio = stdev(medias) if len(medias) > 1 else None
        if len(grupo) == 1:
            desvio = grupo[0]["desvio_padrao"]
        saida.append({
            "modelo": modelo, "cenario": cenario, "metrica": metrica,
            "nivel_desvio": "entre_medias_das_redes" if len(grupo) > 1 else "repeticoes_na_rede",
            "numero_redes": len(grupo), "redes_com_observacoes": len(medias),
            "n_repeticoes_total": sum(g["n"] for g in grupo),
            "media": mean(medias) if medias else None, "desvio_padrao": desvio,
        })
    return saida


def consolidar(destino: Path = RESULTADOS) -> dict[str, Any]:
    """Relê os lotes e exporta métricas, diferenças pareadas, curvas e resumos."""
    por_rede, metricas, diferencas, curvas = [], [], [], []
    campos_h = ("passo", "suscetiveis", "infectados", "recuperados", "isolados")
    trajetorias = destino / "historicos.csv.gz"
    with texto_gzip(trajetorias) as arquivo:
        escritor = csv.writer(arquivo, lineterminator="\n")
        escritor.writerow(("rede", "modelo", "cenario", "repeticao", *campos_h))
        for caminho in sorted((destino / "lotes").glob("*.json.gz")):
            pacote = ler_lote(caminho)
            rede, modelo = pacote["rede_id"], pacote["modelo"]
            execucoes = pacote["resultado"]["execucoes"]
            referencias = {e["repeticao"]: e for e in execucoes if e["cenario"] == "sem_intervencao"}
            for e in execucoes:
                c, r = e["cenario"], e["repeticao"]
                sementes = e["manifesto"]["configuracao"]["sementes"]
                metricas.append({"rede": rede, "modelo": modelo, "cenario": c, "repeticao": r,
                                 **e["metrica"], "motivo_termino": e["motivo_termino"], **sementes})
                for h in e["historico"]:
                    escritor.writerow((rede, modelo, c, r, *(h[k] for k in campos_h)))
                if c != "sem_intervencao":
                    for nome in PRIMARIOS:
                        referencia, valor = referencias[r]["metrica"][nome], e["metrica"][nome]
                        diferencas.append({"rede": rede, "modelo": modelo, "cenario": c, "repeticao": r,
                                           "metrica": nome, "diferenca": referencia - valor,
                                           "reducao_relativa": (referencia - valor) / referencia if referencia else None})
            for c in CENARIOS:
                grupo = [e for e in execucoes if e["cenario"] == c]
                for nome in INDICADORES:
                    por_rede.append({"rede": rede, "modelo": modelo, "cenario": c, "metrica": nome,
                                     **estatistica([e["metrica"][nome] for e in grupo])})
                for t in range(pacote["pedido"]["configuracao"]["limite_passos"] + 1):
                    # Só mantém o último estado quando houve extinção; não inventa evolução após censura.
                    pontos = [e["historico"][min(t, len(e["historico"]) - 1)] for e in grupo
                              if t < len(e["historico"]) or e["motivo_termino"] == "extincao"]
                    if pontos:
                        curvas.append({"rede": rede, "modelo": modelo, "cenario": c, "passo": t,
                                       "n": len(pontos), "infectados_media": mean(p["infectados"] for p in pontos)})
    for nome, linhas in [("metricas.csv", metricas), ("resumo_por_rede.csv", por_rede),
                          ("diferencas_pareadas.csv", diferencas), ("curvas_medias_por_rede.csv", curvas)]:
        if linhas:
            gravar_csv(destino / nome, tuple(linhas[0]), (l.values() for l in linhas))
    hierarquia = resumo_hierarquico(por_rede)
    gravar_csv(destino / "resumo_por_modelo.csv", tuple(hierarquia[0]), (l.values() for l in hierarquia))
    resumo = {"execucoes": len(metricas), "lotes": len({l["rede"] for l in metricas}),
              "censuradas": sum(l["motivo_termino"] == "limite_passos" for l in metricas),
              "resumo_modelos": hierarquia,
              "sha256_saidas": {p.name: hash_arquivo(p) for p in sorted(destino.glob("*.csv*"))}}
    gravar_json(destino / "consolidacao.json", resumo)
    return resumo


def executar(protocolo: dict[str, Any], destino: Path = RESULTADOS) -> None:
    """Executa sequencialmente os lotes A, conservando checkpoints e dados efetivos."""
    destino.mkdir(parents=True, exist_ok=True)
    gravar_json(destino / "protocolo-utilizado.json", protocolo)
    codigo = {str(p.relative_to(RAIZ)): hash_arquivo(p) for p in sorted((RAIZ / "src/simulador").glob("*.py"))}
    cientifico = {k: protocolo[k] for k in (
        "id", "redes_planejadas", "configuracao_api_base", "lotes_planejados", "repeticoes_por_lote", "cenarios",
    )}
    cpu = next((l.split(":", 1)[1].strip() for l in Path("/proc/cpuinfo").read_text().splitlines()
                if l.startswith("model name")), platform.processor())
    ambiente = {"data_local": "2026-11-22", "iniciado_em_utc": datetime.now(timezone.utc).isoformat(),
                "python": platform.python_version(), "plataforma": platform.platform(), "cpu": cpu,
                "ram_bytes": os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"),
                "revisao_git": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=RAIZ, text=True).strip(),
                "inclui_alteracoes_locais": True, "sha256_codigo_dominio": codigo,
                "sha256_executor": hash_arquivo(Path(__file__)), "protocolo_cientifico_sha256": hash_json(cientifico),
                "escopo": "bloco A; B/C/D e benchmark não executados", "lotes": []}
    estrutural = []
    redes = {r["id"]: r for r in protocolo["redes_planejadas"]}
    lotes = [l for l in protocolo["lotes_planejados"] if l["bloco"] == "A_topologias"]
    for indice, lote in enumerate(lotes, 1):
        especificacao = redes[lote["rede"]]
        modelo = especificacao.get("modelo", "escola")
        servico = criar_servico(especificacao)
        estado = servico.inspecionar()
        referencia = servico.obter_rede_confirmada(estado["revisao"])
        estrutura = assinatura_rede(referencia.rede)
        medidas = caracterizar_rede(referencia.rede, destino / "caracterizacao" / lote["rede"])
        estrutural.append({"rede": lote["rede"], "modelo": modelo,
                           "semente_topologia": especificacao.get("semente"), **medidas})
        configuracao = deepcopy(protocolo["configuracao_api_base"])
        configuracao.update(beta=lote["beta"], contexto_rede=servico.contexto_rede, revisao_rede=estado["revisao"])
        configuracao["intervencao"].update({k: lote[k] for k in ("fracao", "inicio", "mecanismo", "reducao")})
        pedido = {"configuracao": configuracao, "repeticoes": protocolo["repeticoes_por_lote"]}
        identificador = hash_json({"protocolo": cientifico, "codigo": codigo, "python": platform.python_version(),
                                   "estrutura": estrutura, "lote": lote, "versao_executor": 1})
        caminho = destino / "lotes" / f"{lote['id']}.json.gz"
        inicio = perf_counter()
        if caminho.exists():
            pacote = ler_lote(caminho, identificador)
            origem = "checkpoint_verificado"
        else:
            resultado = executar_comparacao_api(servico, pedido)
            validacao = validar_resultado(resultado, pedido)
            pacote = {"rede_id": lote["rede"], "modelo": modelo,
                      "identificador_execucao": identificador, "assinatura_rede": estrutura,
                      "pedido": pedido, "resultado": resultado, "validacao": validacao,
                      "assinatura_resultado": assinatura_resultado(resultado)}
            salvar_lote(caminho, pacote)
            origem = "execucao_nova"
        if assinatura_rede(referencia.rede) != estrutura or any(
            p.estado.value != "S" or p.isolamento for p in referencia.rede.iter_individuos()
        ):
            raise ValueError("A referência foi alterada pela execução.")
        ambiente["lotes"].append({"id": lote["id"], "origem": origem,
                                  "sha256": hash_arquivo(caminho), **pacote["validacao"]})
        gravar_json(destino / "execucao.json", ambiente)
        print(f"[{indice}/{len(lotes)}] {lote['rede']}: {pacote['validacao']['execucoes']} trajetórias; "
              f"{perf_counter() - inicio:.2f}s; {origem}", flush=True)
    gravar_csv(destino / "caracterizacao_redes.csv", tuple(estrutural[0]), (l.values() for l in estrutural))
    ambiente["concluido_em_utc"] = datetime.now(timezone.utc).isoformat()
    ambiente["concluido"] = True
    gravar_json(destino / "execucao.json", ambiente)


def main() -> None:
    """Coordena geração, execução ou consolidação sem alterar os parâmetros definidos."""
    parser = argparse.ArgumentParser(description=__doc__)
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument("--somente-controles", action="store_true")
    grupo.add_argument("--somente-consolidar", action="store_true")
    args = parser.parse_args()
    protocolo = json.loads(PROTOCOLO.read_text())
    if not args.somente_consolidar:
        controles = preparar_controles(protocolo)
        print(f"{len(controles)} controles gerados, caracterizados e reimportados.", flush=True)
    if args.somente_controles:
        return
    if not args.somente_consolidar:
        executar(protocolo)
    resumo = consolidar()
    print(json.dumps({k: resumo[k] for k in ("execucoes", "lotes", "censuradas")}), flush=True)


if __name__ == "__main__":
    main()
