"""Caracteriza uma base preparada com os algoritmos estruturais do simulador.

Uso: PYTHONPATH=src python3 scripts/caracterizar_rede_real.py [--graficos]
O cálculo usa biblioteca padrão; --graficos requer ReportLab no ambiente.
"""

import argparse
from collections import Counter
from collections.abc import Iterable
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
from typing import Any

from simulador import componentes_conexas, importar_rede_csv, resumir_rede


RAIZ = Path(__file__).resolve().parents[1]
PASTA_PADRAO = RAIZ / "dados/dados/redes_reais/escola_suica_2024"


def gravar_csv(caminho: Path, colunas: tuple[str, ...], linhas: Iterable[Iterable[object]]) -> None:
    """Grava dados sem arredondamento, em UTF-8, com vírgula e ponto decimal."""
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo, lineterminator="\n")
        escritor.writerow(colunas)
        escritor.writerows(linhas)


def hash_arquivo(caminho: Path) -> str:
    """Identifica o conteúdo de um arquivo por SHA-256."""
    return sha256(caminho.read_bytes()).hexdigest()


def caracterizar(pasta: Path, saida: Path) -> dict[str, Any]:
    """Confere a preparação, calcula graus/componentes e exporta quatro CSVs.

    A análise considera a topologia cadastrada, incluindo todos os indivíduos.
    O manifesto da preparação deve corresponder aos arquivos de entrada.
    Não modifica a rede nem executa transições epidemiológicas.
    """
    manifesto = json.loads((pasta / "manifesto.json").read_text(encoding="utf-8"))
    hashes_entrada = {"manifesto.json": hash_arquivo(pasta / "manifesto.json")}
    for nome, metadados in manifesto["arquivos_preparados"].items():
        digest = hash_arquivo(pasta / nome)
        if digest != metadados["sha256"]:
            raise ValueError(f"SHA-256 diferente do manifesto: {nome}. Confira a preparação.")
        hashes_entrada[nome] = digest

    rede = importar_rede_csv(pasta / "contatos.csv", arquivo_individuos=pasta / "individuos.csv").rede
    resumo = resumir_rede(rede)
    graus = {pessoa.id: rede.grau(pessoa) for pessoa in rede.iter_individuos()}
    componentes = sorted(componentes_conexas(rede), key=lambda grupo: min(grupo))
    frequencias = Counter(graus.values())
    n, m = resumo.numero_individuos, resumo.numero_contatos
    if sum(graus.values()) != 2 * m or sum(frequencias.values()) != n:
        raise ValueError("As contagens estruturais não conservam graus e população.")
    if sum(map(len, componentes)) != n:
        raise ValueError("As componentes não cobrem a população.")

    indicadores = {
        "numero_individuos": n,
        "numero_contatos": m,
        "grau_medio": resumo.grau_medio,
        "grau_minimo": min(graus.values(), default=0),
        "grau_maximo": max(graus.values(), default=0),
        "densidade": 2 * m / (n * (n - 1)) if n > 1 else 0.0,
        "numero_componentes": len(componentes),
        "maior_componente": max(map(len, componentes), default=0),
        "individuos_sem_contatos": frequencias[0],
        "soma_graus": sum(graus.values()),
    }
    with (pasta / "mapa_ids.csv").open(encoding="utf-8", newline="") as arquivo:
        mapa = {int(linha["id"]): linha["id_original"] for linha in csv.DictReader(arquivo)}
    if set(mapa) != set(graus):
        raise ValueError("O mapa de IDs não corresponde à população importada.")

    saida.mkdir(parents=True, exist_ok=True)
    gravar_csv(saida / "resumo.csv", tuple(indicadores), [indicadores.values()])
    gravar_csv(
        saida / "graus.csv", ("id", "id_original", "grau"),
        ((identificador, mapa[identificador], grau) for identificador, grau in sorted(graus.items())),
    )
    gravar_csv(
        saida / "distribuicao_graus.csv", ("grau", "numero_individuos", "fracao"),
        ((k, frequencias[k], frequencias[k] / n) for k in range(n)),
    )
    gravar_csv(
        saida / "componentes.csv", ("componente", "numero_individuos", "ids"),
        ((indice, len(grupo), " ".join(map(str, sorted(grupo))))
         for indice, grupo in enumerate(componentes, start=1)),
    )
    fontes_codigo = (
        "src/simulador/analise_estrutural.py",
        "src/simulador/rede_contatos.py",
        "src/simulador/importacao.py",
        "scripts/caracterizar_rede_real.py",
    )
    return {
        "base": manifesto["base"],
        "titulo_rede": manifesto["fonte"]["titulo"],
        "coleta": manifesto["fonte"]["coleta"],
        "calculado_em_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "representacao": manifesto["preparacao"]["tratamento"],
        "indicadores": indicadores,
        "ids_grau_maximo": sorted(i for i, grau in graus.items() if grau == indicadores["grau_maximo"]),
        "ids_sem_contatos": sorted(i for i, grau in graus.items() if grau == 0),
        "tamanhos_componentes": [len(grupo) for grupo in componentes],
        "sha256_entradas": hashes_entrada,
        "sha256_codigo": {nome: hash_arquivo(RAIZ / nome) for nome in fontes_codigo},
        "verificacoes": {"soma_graus_igual_2m": True, "populacao_preservada": True},
        "epidemias_executadas": False,
    }


def gerar_graficos(saida: Path, registro: dict[str, Any]) -> None:
    """Exporta a distribuição discreta em PDF/SVG usando ReportLab opcional."""
    from reportlab import Version
    from reportlab.graphics import renderPDF, renderSVG
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.shapes import Drawing, Line, String
    from reportlab.lib.colors import HexColor

    with (saida / "distribuicao_graus.csv").open(encoding="utf-8", newline="") as arquivo:
        frequencias = [int(linha["numero_individuos"]) for linha in csv.DictReader(arquivo)]
    indicadores = registro["indicadores"]
    n, m = indicadores["numero_individuos"], indicadores["numero_contatos"]
    media = indicadores["grau_medio"]
    inicio = datetime.fromisoformat(registro["coleta"]["inicio"]).strftime("%d/%m/%Y")
    fim = datetime.fromisoformat(registro["coleta"]["fim"]).strftime("%d/%m/%Y")
    figura = Drawing(780, 420)
    figura.add(String(62, 389, "Distribuição de graus", fontName="Helvetica-Bold", fontSize=18))
    figura.add(String(62, 365, registro["titulo_rede"], fontName="Helvetica", fontSize=12))
    detalhe = f"União estática de {inicio} a {fim} | {n} indivíduos | {m:,} contatos".replace(",", ".")
    figura.add(String(62, 345, detalhe, fontName="Helvetica", fontSize=10))
    barras = VerticalBarChart()
    barras.x, barras.y, barras.width, barras.height = 62, 104, 684, 208
    barras.data = [frequencias] if frequencias else [[0]]
    barras.categoryAxis.categoryNames = [str(k) if k % 5 == 0 else "" for k in range(n)] or ["0"]
    barras.categoryAxis.labels.fontName = "Helvetica"
    barras.categoryAxis.labels.fontSize = 10
    barras.valueAxis.valueMin = 0
    barras.valueAxis.valueMax = max(frequencias, default=0) + 1
    barras.valueAxis.valueStep = 1
    barras.valueAxis.labels.fontSize = 10
    barras.valueAxis.visibleGrid = True
    barras.valueAxis.gridStrokeColor = HexColor("#e5e7eb")
    barras.valueAxis.gridStrokeWidth = 0.5
    barras.bars[0].fillColor = HexColor("#375a70")
    barras.bars[0].strokeWidth = 0
    barras.groupSpacing = 1
    figura.add(barras)
    if n:
        x_media = barras.x + barras.width * (media + 0.5) / n
        figura.add(Line(
            x_media, barras.y, x_media, barras.y + barras.height,
            strokeColor=HexColor("#a33c23"), strokeDashArray=[4, 3],
        ))
        figura.add(String(
            x_media + 6, 320, f"Média: {media:.2f}".replace(".", ","),
            fillColor=HexColor("#a33c23"), fontName="Helvetica", fontSize=10,
        ))
    figura.add(String(
        404, 65, "Grau k (número de vizinhos distintos)",
        textAnchor="middle", fontName="Helvetica", fontSize=12,
    ))
    figura.add(String(62, 325, "Número de indivíduos", fontName="Helvetica", fontSize=10))
    figura.add(String(
        62, 35, "Uma barra por grau inteiro; frequências zero também integram o CSV. "
        "Fonte: CSVs preparados do projeto.",
        fontName="Helvetica", fontSize=10,
    ))
    figura.add(String(
        62, 18, "Contatos de datas distintas são agregados; o gráfico não representa encontros simultâneos.",
        fontName="Helvetica", fontSize=10,
    ))
    renderPDF.drawToFile(figura, str(saida / "distribuicao_graus.pdf"), invariant=1)
    renderSVG.drawToFile(figura, str(saida / "distribuicao_graus.svg"))
    registro["graficos"] = {"biblioteca": "ReportLab", "versao": Version, "pdf_invariant": True}


def main() -> None:
    """Calcula a caracterização e registra hashes dos arquivos produzidos."""
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument("--pasta", type=Path, default=PASTA_PADRAO, help="Pasta da base preparada.")
    argumentos.add_argument("--saida", type=Path, help="Destino; padrão: <pasta>/caracterizacao.")
    argumentos.add_argument("--graficos", action="store_true", help="Exportar também PDF e SVG; requer ReportLab.")
    opcoes = argumentos.parse_args()
    saida = opcoes.saida or opcoes.pasta / "caracterizacao"
    registro = caracterizar(opcoes.pasta, saida)
    arquivos = ["resumo.csv", "graus.csv", "distribuicao_graus.csv", "componentes.csv"]
    if opcoes.graficos:
        gerar_graficos(saida, registro)
        arquivos.extend(["distribuicao_graus.pdf", "distribuicao_graus.svg"])
    registro["sha256_saidas"] = {nome: hash_arquivo(saida / nome) for nome in arquivos}
    (saida / "caracterizacao.json").write_text(
        json.dumps(registro, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    print(json.dumps(registro["indicadores"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
