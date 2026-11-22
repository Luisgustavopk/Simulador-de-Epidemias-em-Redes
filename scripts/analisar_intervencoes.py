"""Produz síntese e figuras vetoriais dos blocos B/C/D e do benchmark, sem SIR.

PYTHONPATH=src python3 scripts/analisar_intervencoes.py
Requer ReportLab (disponível no Python do sistema usado para as figuras).
"""

import json
from pathlib import Path

from reportlab.graphics import renderPDF, renderSVG
from reportlab.graphics.shapes import Circle, Drawing, Line, PolyLine, Rect, String
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from experimentos_intervencoes import DESTINO
from experimentos_topologia import DADOS, RESULTADOS, estatistica, gravar_json, hash_arquivo, ler_lote


FONT = "DejaVu"
pdfmetrics.registerFont(TTFont(FONT, "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
CORES = {"sem_intervencao": "#555555", "aleatoria": "#b36014", "grau": "#006a82"}
NOMES = {"sem_intervencao": "Sem intervenção", "aleatoria": "Aleatória", "grau": "Por grau"}


def texto(d, x, y, valor, tamanho=10, ancora="start", cor="#222222"):
    d.add(String(x, y, str(valor), fontName=FONT, fontSize=tamanho, textAnchor=ancora, fillColor=HexColor(cor)))


def eixos(d, x, y, largura, altura, titulo, categorias, teto=100):
    texto(d, x, y + altura + 19, titulo, 12)
    for t in range(0, teto + 1, 20 if teto == 100 else 10):
        yy = y + t / teto * altura
        d.add(Line(x, yy, x + largura, yy, strokeColor=HexColor("#dddddd"), strokeWidth=.5))
        texto(d, x - 8, yy - 3, t, 9, "end")
    d.add(Line(x, y, x, y + altura, strokeColor=HexColor("#666666"), strokeWidth=.6))
    xs = [x + largura * (i + .5) / len(categorias) for i in range(len(categorias))]
    for xx, c in zip(xs, categorias):
        texto(d, xx, y - 18, c, 10, "middle")
    return xs, lambda v: y + v / teto * altura


def salvar(d, pasta: Path, nome: str):
    pasta.mkdir(parents=True, exist_ok=True)
    renderPDF.drawToFile(d, str(pasta / (nome + ".pdf")), invariant=1)
    renderSVG.drawToFile(d, str(pasta / (nome + ".svg")))


def base(linhas, id_lote, cenario, metrica):
    return next(r for r in linhas if r["lote"] == id_lote and r["cenario"] == cenario and r["metrica"] == metrica)


def pontos(linhas, condicoes, rotulos, nome, titulo):
    d = Drawing(880, 340)
    texto(d, 40, 317, titulo, 15)
    for j, (c, cor) in enumerate(CORES.items()):
        d.add(Circle(52 + 210 * j, 293, 3, fillColor=HexColor(cor), strokeColor=None))
        texto(d, 62 + 210 * j, 290, NOMES[c])
    for i, (m, titulo_painel) in enumerate((("pico_proporcional", "Pico (% da população)"),
                                            ("fracao_acumulada", "Fração acumulada (%)"))):
        xs, y = eixos(d, 55 + 440 * i, 63, 365, 185, titulo_painel, rotulos)
        for xx, lote in zip(xs, condicoes):
            for j, (c, cor) in enumerate(CORES.items()):
                r = base(linhas, lote, c, m)
                centro, sd = r["media"] * 100, r["desvio_padrao"] * 100
                x = xx + (j - 1) * 14
                d.add(Line(x, y(centro - sd), x, y(centro + sd), strokeColor=HexColor(cor), strokeWidth=1))
                d.add(Circle(x, y(centro), 3.2, fillColor=HexColor(cor), strokeColor=white, strokeWidth=.6))
    texto(d, 40, 17, "Pontos: médias de 100 repetições na escola. Barras: ± 1 desvio amostral; não são intervalos de confiança.", 9)
    salvar(d, DESTINO / "figuras", nome)


def orcamento(linhas):
    d = Drawing(880, 555)
    texto(d, 45, 530, "Orçamento e início — desativação na escola", 15)
    cores = {10: "#8b3b87", 20: "#006a82", 30: "#ad5d00"}
    for j, (f, cor) in enumerate(cores.items()):
        texto(d, 60 + 210 * j, 505, f"Fração {f}% (k = { {10:6,20:13,30:20}[f] })", 10, cor=cor)
    for i, (m, label) in enumerate((("pico_proporcional", "Pico (%)"), ("fracao_acumulada", "Acumulada (%)"))):
        for j, c in enumerate(("aleatoria", "grau")):
            xs, y = eixos(d, 55 + 440 * j, 308 - i * 245, 365, 155, label + " — " + NOMES[c], ["t = 0", "t = 5", "t = 10"])
            referencia = base(linhas, "A_escola_suica_2024", "sem_intervencao", m)["media"] * 100
            d.add(Line(xs[0] - 40, y(referencia), xs[-1] + 40, y(referencia),
                       strokeColor=HexColor("#777777"), strokeDashArray=[3, 3], strokeWidth=.7))
            for f, cor in cores.items():
                valores = [base(linhas, "A_escola_suica_2024" if (f, t) == (20, 5) else f"C_f{f}_t{t}", c, m)["media"] * 100
                           for t in (0, 5, 10)]
                d.add(PolyLine([v for xx, val in zip(xs, valores) for v in (xx, y(val))], strokeColor=HexColor(cor), strokeWidth=1.5))
                for xx, val in zip(xs, valores):
                    d.add(Circle(xx, y(val), 3, fillColor=HexColor(cor), strokeColor=None))
    texto(d, 40, 14, "Médias de 100 repetições por condição. Tracejado: referência comum. A condição 20%/t=5 reutiliza o bloco A.", 9)
    salvar(d, DESTINO / "figuras", "orcamento-inicio")


def desempenho():
    pasta = DADOS / "experimentos/desempenho-v1"
    registro = json.loads((pasta / "medicoes.json").read_text())
    d = Drawing(880, 330)
    texto(d, 45, 305, "Lote de 300 trajetórias — medição sequencial", 15)
    medidas = registro["medicoes"]
    rotulos = ["Escola", "ER 1000", "BA 2000"]
    # Tempo e memória têm escalas próprias; o eixo de tempo inclui todos os valores brutos.
    for j, (campo, titulo) in enumerate((("mediana_segundos", "Tempo (s) — cinco chamadas"),
                                        ("pico_adicional_python_bytes", "Pico adicional Python (MiB)"))):
        x, y0, h, w = 55 + 440 * j, 65, 175, 365
        valores = [m[campo] / (2 ** 20 if j else 1) for m in medidas]
        teto = max(max(m["tempos_segundos"]) for m in medidas) * 1.18 if not j else max(valores) * 1.18
        texto(d, x, 262, titulo, 12)
        for k in range(5):
            yy = y0 + h * k / 4
            d.add(Line(x, yy, x + w, yy, strokeColor=HexColor("#dddddd"), strokeWidth=.5))
            texto(d, x - 8, yy - 3, f"{teto * k / 4:.1f}", 9, "end")
        for i, (m, valor) in enumerate(zip(medidas, valores)):
            xx = x + w * (i + .5) / 3
            d.add(Rect(xx - 24, y0, 48, h * valor / teto, fillColor=HexColor("#006a82"), strokeColor=None))
            texto(d, xx, y0 - 18, rotulos[i], 10, "middle")
            texto(d, xx, y0 + h * valor / teto + 9, f"{valor:.2f}", 10, "middle")
            if not j:
                for t in m["tempos_segundos"]:
                    d.add(Circle(xx, y0 + h * t / teto, 2, fillColor=HexColor("#b36014"), strokeColor=white, strokeWidth=.3))
    texto(d, 40, 20, "Tempo sem instrumentação; memória em chamada separada. Preparo, HTTP e navegador excluídos. Não é RSS.", 9)
    salvar(d, pasta / "figuras", "desempenho")


def orcamento_relatorio(linhas):
    """Figura menor, com fontes legíveis na largura de uma página SBC."""
    d = Drawing(450, 222)
    cores = {10: "#8b3b87", 20: "#006a82", 30: "#ad5d00"}
    for j, (f, cor) in enumerate(cores.items()):
        texto(d, 47 + j * 125, 205, f"Fração {f}%", 10, cor=cor)
    for j, c in enumerate(("aleatoria", "grau")):
        xs, y = eixos(d, 34 + j * 225, 38, 177, 137, NOMES[c], ["0", "5", "10"])
        ref = base(linhas, "A_escola_suica_2024", "sem_intervencao", "fracao_acumulada")["media"] * 100
        d.add(Line(34 + j * 225, y(ref), 211 + j * 225, y(ref), strokeColor=HexColor("#555555"),
                   strokeWidth=.6, strokeDashArray=[2, 2]))
        for f, cor in cores.items():
            valores = [base(linhas, "A_escola_suica_2024" if (f, t) == (20, 5) else f"C_f{f}_t{t}", c,
                            "fracao_acumulada")["media"] * 100 for t in (0, 5, 10)]
            d.add(PolyLine([v for xx, val in zip(xs, valores) for v in (xx, y(val))], strokeColor=HexColor(cor), strokeWidth=1.2))
            for xx, val in zip(xs, valores):
                d.add(Circle(xx, y(val), 2.6, fillColor=HexColor(cor), strokeColor=None))
        texto(d, 122 + j * 225, 8, "Instante de início", 9, "middle")
    salvar(d, DESTINO / "figuras", "sintese-orcamento")


def main():
    consolidacao = json.loads((DESTINO / "consolidacao.json").read_text())
    linhas = consolidacao["resumos"]
    pacote = ler_lote(RESULTADOS / "lotes/A_escola_suica_2024.json.gz")
    for c in CORES:
        grupo = [e for e in pacote["resultado"]["execucoes"] if e["cenario"] == c]
        for m in ("pico_proporcional", "fracao_acumulada"):
            linhas.append({"lote": "A_escola_suica_2024", "cenario": c, "metrica": m,
                           **estatistica([e["metrica"][m] for e in grupo])})
    pontos(linhas, ["A_escola_suica_2024", "B_reducao", "B_exclusao"],
           ["Desativação", "Redução 50%", "Exclusão"], "mecanismos", "Mecanismos — fração 20%, início em t = 5")
    pontos(linhas, ["D_beta0.0025", "A_escola_suica_2024", "D_beta0.01"],
           ["β = 0,0025", "β = 0,005", "β = 0,01"], "sensibilidade-beta", "Sensibilidade a β — fração 20%, início em t = 5")
    orcamento(linhas)
    orcamento_relatorio(linhas)
    desempenho()
    gravar_json(DESTINO / "analise.json", {
        "protocolo": "etapa3-base-v1", "lotes_novos": 12, "trajetorias_novas": 3600,
        "registros_novos": consolidacao["registros"], "censuradas_novas": consolidacao["censuradas"],
        "baseline_reutilizado": "A_escola_suica_2024; não soma repetições à amostra por condição",
        "exclusao_desativacao": "Históricos e métricas idênticos nos 300 pares de cenário/repetição; ver verificacao.json.",
        "escopo": "Uma escola estática, 100 repetições por condição. Desvios amostrais; sem testes de significância ou calibração clínica.",
        "figuras_sha256": {p.name: hash_arquivo(p) for p in sorted((DESTINO / "figuras").glob("*"))},
    })
    print("Figuras de mecanismos, orçamento/início, sensibilidade e desempenho geradas.")


if __name__ == "__main__":
    main()
