"""Executa B/C/D; consolida por condição e restaura exportações sem executar SIR.

Uso: PYTHONPATH=src python3 scripts/experimentos_intervencoes.py
--restaurar valida o ZIP e recria as exportações; --verificar repete seis lotes.
"""

import argparse
from copy import deepcopy
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from math import isclose
import os
from pathlib import Path
import platform
import shutil
from statistics import mean
import subprocess
from tempfile import TemporaryDirectory
from time import perf_counter
from zipfile import ZIP_STORED, ZipFile, ZipInfo

from experimentos_topologia import (
    CENARIOS, DADOS, INDICADORES, PRIMARIOS, PROTOCOLO, RAIZ, RESULTADOS,
    assinatura_rede, assinatura_resultado, criar_servico, estatistica,
    gravar_csv, gravar_json, hash_arquivo, hash_json, ler_lote, salvar_lote,
    texto_gzip, validar_resultado,
)
from simulador.comparacao_api import executar_comparacao_api


DESTINO = DADOS / "experimentos/intervencoes-v1"
PACOTE = "lotes-intervencoes-v1.zip"
REPRODUZIR = ("B_reducao", "B_exclusao", "C_f30_t0", "C_f10_t10", "D_beta0.0025", "D_beta0.01")


def ambiente() -> dict:
    """Registra versões e hashes efetivos, inclusive em uma árvore com alterações."""
    cpu = next((l.split(":", 1)[1].strip() for l in Path("/proc/cpuinfo").read_text().splitlines()
                if l.startswith("model name")), platform.processor())
    return {
        "iniciado_em_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(), "plataforma": platform.platform(), "cpu": cpu,
        "ram_bytes": os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"),
        "revisao_git": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=RAIZ, text=True).strip(),
        "arvore_com_alteracoes": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=RAIZ)),
        "sha256_codigo_dominio": {str(p.relative_to(RAIZ)): hash_arquivo(p)
                                  for p in sorted((RAIZ / "src/simulador").glob("*.py"))},
        "sha256_protocolo": hash_arquivo(PROTOCOLO),
        "sha256_executor": hash_arquivo(Path(__file__)),
    }


def preparar_pedido(protocolo: dict, lote: dict, servico) -> dict:
    """Preenche somente a condição planejada e a identificação da rede carregada."""
    cfg = deepcopy(protocolo["configuracao_api_base"])
    cfg.update(beta=lote["beta"], contexto_rede=servico.contexto_rede,
               revisao_rede=servico.inspecionar()["revisao"])
    cfg["intervencao"].update({k: lote[k] for k in ("fracao", "inicio", "mecanismo", "reducao")})
    return {"configuracao": cfg, "repeticoes": protocolo["repeticoes_por_lote"]}


def conferir_referencia(servico, estrutura: str) -> None:
    """Recusa contaminação da rede de referência entre condições."""
    rede = servico.obter_rede_confirmada(servico.inspecionar()["revisao"]).rede
    if assinatura_rede(rede) != estrutura or any(p.estado.value != "S" or p.isolamento for p in rede.iter_individuos()):
        raise ValueError("Referência alterada pela execução.")


def executar(protocolo: dict, destino: Path = DESTINO) -> None:
    """Salva cada lote validado antes de seguir; checkpoints exigem a mesma receita."""
    destino.mkdir(parents=True, exist_ok=True)
    gravar_json(destino / "protocolo-utilizado.json", protocolo)
    registro = ambiente()
    registro.update(escopo="B/C/D na escola; condições fixadas no protocolo etapa3-base-v1", lotes=[])
    anterior = json.loads((RESULTADOS / "execucao.json").read_text())
    if registro["sha256_codigo_dominio"] != anterior["sha256_codigo_dominio"]:
        raise ValueError("O domínio mudou desde A; revisar compatibilidade antes de combinar resultados.")
    redes = {r["id"]: r for r in protocolo["redes_planejadas"]}
    lotes = [l for l in protocolo["lotes_planejados"] if l["bloco"] != "A_topologias"]
    for i, lote in enumerate(lotes, 1):
        servico = criar_servico(redes[lote["rede"]])
        referencia = servico.obter_rede_confirmada(servico.inspecionar()["revisao"]).rede
        estrutura = assinatura_rede(referencia)
        pedido = preparar_pedido(protocolo, lote, servico)
        identificador = hash_json({"protocolo": registro["sha256_protocolo"], "lote": lote,
                                   "codigo": registro["sha256_codigo_dominio"],
                                   "python": registro["python"], "estrutura": estrutura, "versao": 1})
        arquivo = destino / "lotes" / f"{lote['id']}.json.gz"
        inicio = perf_counter()
        if arquivo.exists():
            pacote = ler_lote(arquivo, identificador)
            origem = "checkpoint_verificado"
        else:
            resultado = executar_comparacao_api(servico, pedido)
            pacote = {"lote": lote, "rede_id": lote["rede"], "modelo": "escola",
                      "identificador_execucao": identificador, "assinatura_rede": estrutura,
                      "pedido": pedido, "resultado": resultado,
                      "validacao": validar_resultado(resultado, pedido),
                      "assinatura_resultado": assinatura_resultado(resultado)}
            salvar_lote(arquivo, pacote)
            origem = "execucao_nova"
        conferir_referencia(servico, estrutura)
        registro["lotes"].append({"id": lote["id"], "bloco": lote["bloco"], "sha256": hash_arquivo(arquivo),
                                   "origem": origem, **pacote["validacao"]})
        gravar_json(destino / "execucao.json", registro)
        print(f"[{i}/{len(lotes)}] {lote['id']}: {pacote['validacao']}; {perf_counter() - inicio:.2f}s", flush=True)
    registro.update(concluido=True, concluido_em_utc=datetime.now(timezone.utc).isoformat())
    gravar_json(destino / "execucao.json", registro)


def consolidar(destino: Path = DESTINO) -> dict:
    """Mantém condições separadas; calcula contrastes pareados e ausências explícitas."""
    resumos, pares, metricas, curvas, contagens = [], [], [], [], []
    registros = 0
    campos = ("passo", "suscetiveis", "infectados", "recuperados", "isolados")
    with texto_gzip(destino / "historicos.csv.gz") as arquivo:
        escritor = csv.writer(arquivo, lineterminator="\n")
        escritor.writerow(("lote", "cenario", "repeticao", *campos))
        for caminho in sorted((destino / "lotes").glob("*.json.gz")):
            pacote = ler_lote(caminho)
            registros += pacote["validacao"]["registros"]
            lote, execucoes = pacote["lote"], pacote["resultado"]["execucoes"]
            refs = {e["repeticao"]: e for e in execucoes if e["cenario"] == "sem_intervencao"}
            for e in execucoes:
                c, r = e["cenario"], e["repeticao"]
                metricas.append({"lote": lote["id"], "cenario": c, "repeticao": r,
                                 "motivo_termino": e["motivo_termino"], **e["metrica"]})
                escritor.writerows((lote["id"], c, r, *(p[k] for k in campos)) for p in e["historico"])
                if c != "sem_intervencao":
                    for m in PRIMARIOS:
                        base, valor = refs[r]["metrica"][m], e["metrica"][m]
                        pares.append({"lote": lote["id"], "cenario": c, "repeticao": r, "metrica": m,
                                      "referencia": base, "valor": valor, "diferenca": valor - base,
                                      "reducao_relativa": (base - valor) / base if base else None})
            for c in CENARIOS:
                grupo = [e for e in execucoes if e["cenario"] == c]
                contagens.append({"lote": lote["id"], "cenario": c, "trajetorias": len(grupo),
                                  "censuradas": sum(e["motivo_termino"] == "limite_passos" for e in grupo),
                                  "sem_aplicacao": sum(not any(p["isolados"] for p in e["historico"]) for e in grupo)
                                  if c != "sem_intervencao" else None})
                for m in INDICADORES:
                    resumo = {"lote": lote["id"], "bloco": lote["bloco"], "cenario": c,
                              **{k: lote[k] for k in ("beta", "fracao", "inicio", "mecanismo", "reducao")},
                              "metrica": m, **estatistica([e["metrica"][m] for e in grupo])}
                    backend = pacote["resultado"]["resumo"][c]["metricas"][m]
                    for chave in ("n", "ausentes", "media", "desvio_padrao"):
                        a, b = resumo[chave], backend[chave]
                        if (a is None) != (b is None) or (a is not None and not isclose(a, b, abs_tol=1e-12)):
                            raise ValueError(f"Agregação diferente do backend: {lote['id']}/{c}/{m}/{chave}")
                    if c != "sem_intervencao" and m in PRIMARIOS:
                        deltas = [p for p in pares if p["lote"] == lote["id"] and p["cenario"] == c and p["metrica"] == m]
                        resumo.update(diferenca_pareada=estatistica([p["diferenca"] for p in deltas]),
                                      reducao_relativa_pareada=estatistica([p["reducao_relativa"] for p in deltas]),
                                      pares_menor=sum(p["diferenca"] < 0 for p in deltas),
                                      pares_igual=sum(p["diferenca"] == 0 for p in deltas),
                                      pares_maior=sum(p["diferenca"] > 0 for p in deltas))
                    resumos.append(resumo)
                for t in range(pacote["pedido"]["configuracao"]["limite_passos"] + 1):
                    # Trajetórias extintas mantêm seu último estado apenas para o desenho.
                    estados = [e["historico"][min(t, len(e["historico"]) - 1)] for e in grupo]
                    curvas.append({"lote": lote["id"], "cenario": c, "passo": t,
                                   **{k: mean(p[k] for p in estados) for k in campos[1:]}})
    for nome, linhas in (("metricas.csv", metricas), ("diferencas_pareadas.csv", pares),
                         ("curvas_medias.csv", curvas), ("censura_aplicacao.csv", contagens)):
        gravar_csv(destino / nome, tuple(linhas[0]), (l.values() for l in linhas))
    colunas = tuple(k for k in resumos[0] if k not in ("diferenca_pareada", "reducao_relativa_pareada"))
    gravar_csv(destino / "resumo_por_condicao.csv", colunas, ([r[k] for k in colunas] for r in resumos))
    saida = {"lotes": len({m["lote"] for m in metricas}), "trajetorias": len(metricas),
             "registros": registros,
             "censuradas": sum(c["censuradas"] for c in contagens), "resumos": resumos,
             "contagens": contagens,
             "unidade": "100 repetições na mesma escola por condição; referências repetidas não independentes",
             "sha256_saidas": {p.name: hash_arquivo(p) for p in sorted(destino.glob("*.csv*"))}}
    gravar_json(destino / "consolidacao.json", saida)
    return saida


def arquivo_pacote(destino: Path, extrair: Path | None = None) -> None:
    """Empacota ou extrai apenas membros previstos; valida ZIP, nomes e cada hash."""
    registro = json.loads((destino / "execucao.json").read_text())
    protocolo = json.loads((destino / "protocolo-utilizado.json").read_text())
    permitidos = {l["id"] for l in protocolo["lotes_planejados"] if l["bloco"] != "A_topologias"}
    if {l["id"] for l in registro["lotes"]} != permitidos or len(registro["lotes"]) != len(permitidos):
        raise ValueError("Lotes registrados diferentes do protocolo.")
    dados = {}
    arquivo = destino / PACOTE
    fonte = ZipFile(arquivo) if extrair is not None else None
    try:
        if fonte and hash_arquivo(arquivo) != arquivo.with_suffix(".zip.sha256").read_text().strip():
            raise ValueError("Hash do ZIP divergente.")
        for lote in registro["lotes"]:
            nome, digest = f"lotes/{lote['id']}.json.gz", lote["sha256"]
            for membro in (nome, nome + ".sha256"):
                dados[membro] = fonte.read(membro) if fonte else (destino / membro).read_bytes()
            if sha256(dados[nome]).hexdigest() != digest or dados[nome + ".sha256"].strip() != digest.encode():
                raise ValueError(f"Hash divergente: {nome}")
        if fonte:
            if len(fonte.namelist()) != len(dados) or set(fonte.namelist()) != set(dados):
                raise ValueError("Membros inesperados no pacote.")
            for nome, conteudo in dados.items():
                alvo = extrair / nome
                if alvo.exists() and alvo.read_bytes() != conteudo:
                    raise ValueError(f"Arquivo local divergente preservado: {alvo}")
                alvo.parent.mkdir(parents=True, exist_ok=True)
                alvo.write_bytes(conteudo)
        else:
            with ZipFile(arquivo.with_suffix(".tmp"), "w", ZIP_STORED) as pacote:
                for nome, conteudo in sorted(dados.items()):
                    item = ZipInfo(nome, (1980, 1, 1, 0, 0, 0))
                    item.create_system, item.external_attr = 3, 0o100644 << 16
                    pacote.writestr(item, conteudo)
            arquivo.with_suffix(".tmp").replace(arquivo)
            arquivo.with_suffix(".zip.sha256").write_text(hash_arquivo(arquivo) + "\n")
    finally:
        if fonte:
            fonte.close()


def assinatura_trajetorias(resultado: dict) -> str:
    """Compara efeitos, desconsiderando a receita distinta dos mecanismos."""
    return hash_json([{k: e[k] for k in ("cenario", "repeticao", "historico", "metrica", "motivo_termino")}
                      for e in resultado["execucoes"]])


def restaurar(destino: Path = DESTINO) -> None:
    """Compara em área temporária antes de repor apenas as exportações extensas."""
    esperado = json.loads((destino / "consolidacao.json").read_text())
    with TemporaryDirectory(prefix="restaurar-intervencoes-") as temporario:
        area = Path(temporario)
        arquivo_pacote(destino, area)
        if consolidar(area) != esperado:
            raise ValueError("Exportações restauradas divergentes; originais preservados.")
        arquivo_pacote(destino, destino)
        for nome in ("metricas.csv", "diferencas_pareadas.csv", "curvas_medias.csv", "historicos.csv.gz"):
            shutil.copy2(area / nome, destino / nome)


def verificar(protocolo: dict, destino: Path = DESTINO) -> dict:
    """Audita todos os artefatos e reproduz seis condições cobrindo B, C e D."""
    baseline = ler_lote(RESULTADOS / "lotes/A_escola_suica_2024.json.gz")
    redes = {r["id"]: r for r in protocolo["redes_planejadas"]}
    reproducoes = []
    for caminho in sorted((destino / "lotes").glob("*.json.gz")):
        pacote = ler_lote(caminho)
        if pacote["assinatura_resultado"] != assinatura_resultado(pacote["resultado"]):
            raise ValueError("Assinatura interna divergente.")
        lote = pacote["lote"]
        if lote["beta"] == .005:
            refs = lambda resultado: [e["historico"] for e in resultado["execucoes"] if e["cenario"] == "sem_intervencao"]
            if refs(pacote["resultado"]) != refs(baseline["resultado"]):
                raise ValueError("Referência comum divergente entre os lotes.")
        if lote["id"] == "B_exclusao" and assinatura_trajetorias(pacote["resultado"]) != assinatura_trajetorias(baseline["resultado"]):
            raise ValueError("Exclusão e desativação divergiram sob seleção fixa.")
        if lote["id"] in REPRODUZIR:
            servico = criar_servico(redes[lote["rede"]])
            pedido = preparar_pedido(protocolo, lote, servico)
            novo = executar_comparacao_api(servico, pedido)
            validar_resultado(novo, pedido)
            if assinatura_resultado(novo) != pacote["assinatura_resultado"]:
                raise ValueError(f"Reprodução divergente: {lote['id']}")
            conferir_referencia(servico, pacote["assinatura_rede"])
            reproducoes.append(lote["id"])
            print(f"Reproduzido: {lote['id']}", flush=True)
    original = json.loads((destino / "consolidacao.json").read_text())
    with TemporaryDirectory(prefix="conferir-intervencoes-") as temporario:
        area = Path(temporario)
        arquivo_pacote(destino, area)
        if consolidar(area) != original:
            raise ValueError("A consolidação regenerada diverge.")
    verificacao = {"concluida": True, "data_utc": datetime.now(timezone.utc).isoformat(),
                   "lotes_auditados": original["lotes"], "trajetorias_auditadas": original["trajetorias"],
                   "registros_auditados": original["registros"], "reproducoes": reproducoes,
                   "trajetorias_extras_verificacao": len(reproducoes) * 300,
                   "referencias_comuns_identicas": True, "exclusao_desativacao_identicas": True,
                   "restauracao_zip_e_exportacoes_identicas": True,
                   "sha256_zip": hash_arquivo(destino / PACOTE)}
    gravar_json(destino / "verificacao.json", verificacao)
    return verificacao


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument("--restaurar", action="store_true")
    grupo.add_argument("--verificar", action="store_true")
    args = parser.parse_args()
    protocolo = json.loads(PROTOCOLO.read_text())
    if args.verificar:
        print(json.dumps(verificar(protocolo), ensure_ascii=False))
        return
    if args.restaurar:
        restaurar()
    else:
        executar(protocolo)
        consolidar()
        arquivo_pacote(DESTINO)
    print("12 lotes consolidados; arquivo ZIP e hashes disponíveis.", flush=True)


if __name__ == "__main__":
    main()
