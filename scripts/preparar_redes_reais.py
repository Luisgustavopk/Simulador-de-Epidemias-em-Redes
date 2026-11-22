"""Prepara a base escolar selecionada e confere a importação, sem executar epidemias."""

import argparse
from collections import Counter
from collections.abc import Iterable
from datetime import date, datetime, timezone
import csv
from hashlib import sha256
import json
import math
from pathlib import Path
import platform
from typing import Any
from urllib.request import urlopen

from simulador import ArquivoCSV, ServicoCargaRede, importar_rede_csv


PASTA_PADRAO = Path(__file__).resolve().parents[1] / "dados" / "dados" / "redes_reais"


def gravar_csv(caminho: Path, colunas: tuple[str, ...], linhas: Iterable[Iterable[object]]) -> None:
    """Grava CSV em UTF-8 com vírgula, ponto decimal e quebras Unix."""
    with caminho.open("w", encoding="utf-8", newline="") as saida:
        escritor = csv.writer(saida, lineterminator="\n")
        escritor.writerow(colunas)
        escritor.writerows(linhas)


def obter_fontes(pasta: Path, fonte: dict[str, Any], baixar: bool) -> list[dict[str, Any]]:
    """Verifica hashes e baixa fontes ausentes somente com --baixar."""
    pasta.mkdir(parents=True, exist_ok=True)
    registros = []
    for arquivo in fonte["arquivos"]:
        destino = pasta / arquivo["nome"]
        if destino.exists():
            conteudo = destino.read_bytes()
        elif baixar:
            with urlopen(arquivo["url"], timeout=45) as resposta:
                conteudo = resposta.read()
        else:
            raise FileNotFoundError(f"Fonte ausente: {destino}. Use --baixar.")
        digest = sha256(conteudo).hexdigest()
        if digest != arquivo["sha256"]:
            raise ValueError(f"SHA-256 diferente para {destino}; confira a versão da fonte.")
        if not destino.exists():
            destino.write_bytes(conteudo)
        registros.append({"arquivo": arquivo["nome"], "bytes": len(conteudo), "sha256": digest})
    return registros


def preparar_escola(originais: Path, destino: Path) -> dict[str, Any]:
    """Une contatos diários positivos, preservando IDs e duração para auditoria."""
    identificadores: set[str] = set()
    observacoes: dict[tuple[str, str], list[int]] = {}
    dias: set[str] = set()
    vistos: set[tuple[str, str, str]] = set()
    contagens: Counter[str] = Counter()
    caminho = originais / "contact-duration-acc-based-att-65.csv"
    with caminho.open(encoding="utf-8-sig", newline="") as entrada:
        leitor = csv.DictReader(entrada)
        obrigatorias = {
            "date", "student_id_left", "student_id_right", "contact_duration",
            "absent_left", "absent_right", "motion_left", "motion_right",
        }
        if not obrigatorias.issubset(leitor.fieldnames or []):
            raise ValueError("Colunas esperadas não encontradas na base escolar.")
        for linha in leitor:
            contagens["linhas_lidas"] += 1
            esquerda, direita = linha["student_id_left"], linha["student_id_right"]
            if not esquerda or not direita or esquerda == direita:
                raise ValueError("Identificador vazio ou laço na base escolar.")
            identificadores.update((esquerda, direita))
            dia = date.fromisoformat(linha["date"]).isoformat()
            dias.add(dia)
            par = tuple(sorted((esquerda, direita)))
            chave = (dia, *par)
            if chave in vistos:
                raise ValueError(f"Par diário repetido na fonte: {chave}.")
            vistos.add(chave)
            if linha["absent_left"] not in ("TRUE", "FALSE") or linha["absent_right"] not in ("TRUE", "FALSE"):
                raise ValueError("Indicador de ausência desconhecido.")
            texto = linha["contact_duration"]
            if texto == "NA":
                contagens["duracao_ausente"] += 1
                continue
            duracao = float(texto)
            if not math.isfinite(duracao) or duracao < 0 or not duracao.is_integer():
                raise ValueError("Duração inválida na base escolar.")
            movimentos = (float(linha["motion_left"]), float(linha["motion_right"]))
            if any(not math.isfinite(valor) or valor < 0 for valor in movimentos):
                raise ValueError("Movimento inválido na base escolar.")
            if linha["absent_left"] == "TRUE" or linha["absent_right"] == "TRUE" or min(movimentos) == 0:
                contagens["fora_filtro_presenca_movimento"] += 1
                continue
            if duracao == 0:
                contagens["duracao_zero_valida"] += 1
                continue
            contagens["contatos_diarios_positivos"] += 1
            acumulado = observacoes.setdefault(par, [0, 0])
            acumulado[0] += int(duracao)
            acumulado[1] += 1
    mapa = {original: indice for indice, original in enumerate(sorted(identificadores))}
    if not mapa or not observacoes:
        raise ValueError("Base escolar sem população ou contatos válidos.")
    pares = sorted((min(mapa[a], mapa[b]), max(mapa[a], mapa[b]), a, b) for a, b in observacoes)
    gravar_csv(destino / "individuos.csv", ("id",), ((indice,) for indice in mapa.values()))
    gravar_csv(destino / "mapa_ids.csv", ("id", "id_original"), ((indice, original) for original, indice in mapa.items()))
    gravar_csv(destino / "contatos.csv", ("origem", "destino", "peso"), ((a, b, 1) for a, b, _, _ in pares))
    gravar_csv(
        destino / "duracoes_observadas.csv",
        ("origem", "destino", "duracao_total_segundos", "dias_com_contato"),
        ((a, b, *observacoes[(original_a, original_b)]) for a, b, original_a, original_b in pares),
    )
    return {
        **dict(contagens), "primeira_data": min(dias), "ultima_data": max(dias),
        "datas_na_fonte": len(dias), "pares_positivos_unicos": len(observacoes),
        "duracao_total_segundos": sum(valor[0] for valor in observacoes.values()),
        "tratamento": "União estática dos pares com duração > 0, ambos presentes e com movimento > 0; sem imputação. Peso 1.",
    }


def verificar_importacao(pasta: Path, fonte: dict[str, Any]) -> dict[str, Any]:
    """Confere o importador e o serviço de carga usado pela interface."""
    contatos, individuos = pasta / "contatos.csv", pasta / "individuos.csv"
    rede = importar_rede_csv(contatos, arquivo_individuos=individuos).rede
    if rede.numero_individuos != fonte["numero_individuos_esperado"]:
        raise ValueError("População preparada diverge da fonte documentada.")
    esperado = fonte.get("numero_contatos_esperado")
    if esperado is not None and rede.numero_contatos != esperado:
        raise ValueError("Quantidade de contatos diverge da fonte documentada.")
    servico = ServicoCargaRede()
    estado = servico.importar_csv(
        ArquivoCSV(contatos.name, contatos.read_bytes()),
        arquivo_individuos=ArquivoCSV(individuos.name, individuos.read_bytes()),
    )
    confirmado = servico.confirmar(estado["revisao"])
    resumo = confirmado["resumo"]
    if resumo["numero_individuos"] != rede.numero_individuos or resumo["numero_contatos"] != rede.numero_contatos:
        raise ValueError("Importador e serviço de carga divergiram.")
    if any(pessoa.estado.value != "S" or pessoa.isolamento for pessoa in rede.iter_individuos()):
        raise ValueError("A importação alterou condições epidemiológicas iniciais.")
    return {
        "importador": "aprovado", "servico_carga": "aprovado", "confirmada": confirmado["confirmada"],
        "numero_individuos": rede.numero_individuos, "numero_contatos": rede.numero_contatos,
        "todos_suscetiveis_e_nao_isolados": True,
    }


def main() -> None:
    """Reproduz a preparação e grava manifesto de fontes, saídas e verificações."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baixar", action="store_true", help="Baixa somente fontes ausentes e verifica SHA-256.")
    parser.add_argument("--pasta", type=Path, default=PASTA_PADRAO)
    parser.add_argument("--base", choices=("escola_suica_2024",), default="escola_suica_2024")
    argumentos = parser.parse_args()
    catalogo = json.loads((argumentos.pasta / "fontes.json").read_text(encoding="utf-8"))
    for nome, fonte in catalogo["bases"].items():
        if argumentos.base != nome:
            continue
        originais = argumentos.pasta / "originais" / nome
        arquivos = obter_fontes(originais, fonte, argumentos.baixar)
        destino = argumentos.pasta / nome
        destino.mkdir(parents=True, exist_ok=True)
        tratamento = preparar_escola(originais, destino)
        verificacao = verificar_importacao(destino, fonte)
        manifesto = {
            "base": nome, "preparado_em_utc": datetime.now(timezone.utc).isoformat(),
            "python": platform.python_version(), "fonte": fonte, "arquivos_originais": arquivos,
            "sha256_catalogo": sha256((argumentos.pasta / "fontes.json").read_bytes()).hexdigest(),
            "sha256_preparador": sha256(Path(__file__).read_bytes()).hexdigest(),
            "preparacao": tratamento, "verificacao": verificacao,
            "arquivos_preparados": {
                arquivo.name: {"bytes": arquivo.stat().st_size, "sha256": sha256(arquivo.read_bytes()).hexdigest()}
                for arquivo in sorted(destino.glob("*.csv"))
            },
            "epidemias_executadas": False,
        }
        (destino / "manifesto.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"base": nome, **verificacao}, ensure_ascii=False))


if __name__ == "__main__":
    main()
