"""Produz síntese e figuras vetoriais dos lotes já executados, sem novas simulações.

Uso: PYTHONPATH=src python3 scripts/analisar_topologias.py
Os desenhos requerem ReportLab; o executor epidemiológico usa só a biblioteca padrão.
"""

from collections import defaultdict
import csv
import json
from pathlib import Path
from statistics import mean

from experimentos_topologia import CENARIOS, RESULTADOS, gravar_json, hash_arquivo


MODELOS = ("escola", "erdos_renyi", "barabasi_albert")
NOMES = {"escola": "Escola", "erdos_renyi": "Erdős–Rényi", "barabasi_albert": "Barabási–Albert"}
CORES = {"escola": "#176B70", "erdos_renyi": "#A44B16", "barabasi_albert": "#694AA0"}


def ler_csv(nome: str) -> list[dict[str, str]]:
    """Lê uma das exportações do bloco A."""
    with (RESULTADOS / nome).open(newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def desenhar_curvas() -> None:
    """Exporta três painéis com médias de I, ponderando igualmente cada rede."""
    from reportlab.graphics import renderPDF, renderSVG
    from reportlab.graphics.shapes import Drawing, Line, PolyLine, Rect, String
    from reportlab.lib.colors import HexColor
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # Fonte local com acentos para o PDF e nomes explícitos na saída SVG.
    pdfmetrics.registerFont(TTFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    d = Drawing(900, 370)
    d.add(Rect(0, 0, 900, 370, fillColor=HexColor("#FFFFFF"), strokeColor=None))

    def texto(x: float, y: float, valor: str, tamanho: int = 11, ancora: str = "start") -> None:
        d.add(String(x, y, valor, fontName="DejaVu", fontSize=tamanho,
                     fillColor=HexColor("#20252B"), textAnchor=ancora))

    texto(35, 343, "Propagação simulada nas três famílias de redes", 17)
    texto(35, 321, "N = 67 · β = 0,005 · γ = 0,10 · 3 infectados iniciais · até 200 transições", 11)
    grupos = defaultdict(list)
    for linha in ler_csv("curvas_medias_por_rede.csv"):
        grupos[linha["modelo"], linha["cenario"], int(linha["passo"])].append(float(linha["infectados_media"]))
    titulos = ("Sem intervenção", "Seleção aleatória", "Seleção por grau")
    for painel, (cenario, titulo) in enumerate(zip(CENARIOS, titulos)):
        x0, y0, largura, altura = 45 + painel * 293, 101, 246, 176
        texto(x0 + largura / 2, 294, titulo, 12, "middle")
        for valor in (0, 3, 6, 9, 12):
            y = y0 + valor * altura / 12
            d.add(Line(x0, y, x0 + largura, y, strokeColor=HexColor("#E4E7EB"), strokeWidth=.6))
            texto(x0 - 8, y - 3, str(valor), 9, "end")
        for t in (0, 50, 100, 150, 200):
            x = x0 + t * largura / 200
            texto(x, y0 - 17, str(t), 9, "middle")
        d.add(Line(x0, y0, x0, y0 + altura, strokeColor=HexColor("#56606A"), strokeWidth=.7))
        d.add(Line(x0, y0, x0 + largura, y0, strokeColor=HexColor("#56606A"), strokeWidth=.7))
        if cenario != "sem_intervencao":
            x = x0 + 5 * largura / 200
            d.add(Line(x, y0, x, y0 + altura, strokeColor=HexColor("#89929A"),
                       strokeWidth=.7, strokeDashArray=[3, 3]))
        for modelo in MODELOS:
            pontos = []
            for t in range(201):
                valor = mean(grupos[modelo, cenario, t])
                if valor > 12:
                    raise ValueError("Curva excede o eixo; ajuste a escala antes de exportar.")
                pontos.extend((x0 + t * largura / 200, y0 + valor * altura / 12))
            d.add(PolyLine(pontos, strokeColor=HexColor(CORES[modelo]), strokeWidth=1.8))
        texto(x0 + largura / 2, y0 - 36, "Passo (unidade abstrata)", 10, "middle")
    texto(45, 281, "I médio", 10)
    for i, modelo in enumerate(MODELOS):
        x = 170 + i * 235
        d.add(Line(x, 44, x + 24, 44, strokeColor=HexColor(CORES[modelo]), strokeWidth=2))
        texto(x + 32, 40, NOMES[modelo], 11)
    texto(35, 19, "100 repetições por rede; escola: 1 rede; ER e BA: média das 10 redes. Desativação de 13 pessoas em t = 5.", 10)
    pasta = RESULTADOS / "figuras"
    pasta.mkdir(exist_ok=True)
    renderPDF.drawToFile(d, str(pasta / "curvas-topologias.pdf"), invariant=1)
    renderSVG.drawToFile(d, str(pasta / "curvas-topologias.svg"))


def main() -> None:
    """Calcula contrastes descritivos e conserva a unidade de agregação."""
    resumo = ler_csv("resumo_por_modelo.csv")
    valores = {(x["modelo"], x["cenario"], x["metrica"]): float(x["media"]) for x in resumo}
    contrastes = []
    for modelo in MODELOS:
        for metrica in ("pico_proporcional", "fracao_acumulada"):
            contraste = {"modelo": modelo, "metrica": metrica}
            for a, b in (("sem_intervencao", "aleatoria"), ("sem_intervencao", "grau"), ("aleatoria", "grau")):
                contraste[f"{a}_menos_{b}_pontos_percentuais"] = 100 * (valores[modelo, a, metrica] - valores[modelo, b, metrica])
            contrastes.append(contraste)
    pareadas = ler_csv("diferencas_pareadas.csv")
    grupos = defaultdict(list)
    for x in pareadas:
        grupos[x["modelo"], x["cenario"], x["metrica"]].append(float(x["diferenca"]))
    sinais = [{"modelo": m, "cenario": c, "metrica": k, "n": len(v),
               "diferenca_positiva": sum(x > 0 for x in v),
               "empate": sum(x == 0 for x in v), "diferenca_negativa": sum(x < 0 for x in v)}
              for (m, c, k), v in sorted(grupos.items())]
    met = ler_csv("metricas.csv")
    censura = [x for x in met if x["motivo_termino"] == "limite_passos"]
    desenhar_curvas()
    gravar_json(RESULTADOS / "analise.json", {
        "contrastes_de_medias": contrastes, "sinais_das_diferencas_pareadas": sinais,
        "censuradas": censura,
        "nivel_dispersao_escola": "amostral entre 100 repetições na mesma rede",
        "nivel_dispersao_sinteticas": "amostral entre 10 médias; cada média usa 100 repetições",
        "observacao": "Descrição das condições executadas; não estima significância ou eficácia clínica.",
        "sha256_entradas": {n: hash_arquivo(RESULTADOS / n) for n in (
            "resumo_por_modelo.csv", "diferencas_pareadas.csv", "curvas_medias_por_rede.csv", "metricas.csv")},
        "sha256_figuras": {p.name: hash_arquivo(p) for p in sorted((RESULTADOS / "figuras").glob("*"))},
        "sha256_script": hash_arquivo(Path(__file__)),
    })
    print(json.dumps(contrastes, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
