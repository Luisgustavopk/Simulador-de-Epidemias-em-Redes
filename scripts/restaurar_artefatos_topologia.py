"""Recria as saídas ignoradas pelo Git a partir do inventário e dos lotes salvos.

Uso: PYTHONPATH=src python3 scripts/restaurar_artefatos_topologia.py
--empacotar-lotes reúne os lotes locais em ZIP determinístico e hash SHA-256.
O modo padrão extrai os lotes e restaura as saídas, sem novas trajetórias SIR.
"""

import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
from tempfile import TemporaryDirectory
from zipfile import ZIP_STORED, ZipFile, ZipInfo

from experimentos_topologia import (
    CONTROLES, RAIZ, RESULTADOS, caracterizar_rede, consolidar,
    hash_arquivo, ler_lote, preparar_controles,
)
from simulador import importar_rede_csv


EXPORTACOES = (
    "metricas.csv", "diferencas_pareadas.csv", "curvas_medias_por_rede.csv",
    "historicos.csv.gz",
)
PACOTE_LOTES = "lotes-topologia-v1.zip"


def _lotes_registrados(resultados: Path) -> dict[str, str]:
    """Obtém nomes e hashes esperados do registro da execução original."""
    registro = json.loads((resultados / "execucao.json").read_text(encoding="utf-8"))
    esperados = {}
    for lote in registro["lotes"]:
        identificador, digest = lote["id"], lote["sha256"]
        if not re.fullmatch(r"[A-Za-z0-9_-]+", identificador) or not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ValueError("Identificador ou hash inválido no registro da execução.")
        nome = f"lotes/{identificador}.json.gz"
        if nome in esperados:
            raise ValueError("Lote repetido no registro da execução.")
        esperados[nome] = digest
    if not esperados:
        raise ValueError("Registro da execução sem lotes.")
    return esperados


def empacotar_lotes(resultados: Path = RESULTADOS) -> dict[str, int]:
    """Preserva os bytes dos lotes e hashes num ZIP com ordem e metadados fixos."""
    esperados = _lotes_registrados(resultados)
    encontrados = {f"lotes/{p.name}" for p in (resultados / "lotes").glob("*.json.gz")}
    if encontrados != set(esperados):
        raise ValueError("Lotes locais ausentes ou extras em relação à execução registrada.")
    dados = {}
    for nome, digest in esperados.items():
        caminho = resultados / nome
        if hash_arquivo(caminho) != digest:
            raise ValueError(f"Lote diverge da execução registrada: {caminho.name}.")
        ler_lote(caminho)
        dados[nome] = caminho.read_bytes()
        dados[nome + ".sha256"] = caminho.with_suffix(".gz.sha256").read_bytes()
    with TemporaryDirectory(prefix="empacotar-lotes-", dir=resultados) as temporario:
        arquivo = Path(temporario) / PACOTE_LOTES
        with ZipFile(arquivo, "w", compression=ZIP_STORED) as pacote:
            for nome in sorted(dados):
                item = ZipInfo(nome, date_time=(1980, 1, 1, 0, 0, 0))
                item.create_system = 3
                item.external_attr = 0o100644 << 16
                # Os membros .gz já estão comprimidos; ZIP_STORED evita recompressão.
                pacote.writestr(item, dados[nome])
        with ZipFile(arquivo) as pacote:
            if any(pacote.read(nome) != conteudo for nome, conteudo in dados.items()):
                raise ValueError("O empacotamento alterou os bytes de um lote.")
        arquivo_hash = Path(temporario) / (PACOTE_LOTES + ".sha256")
        arquivo_hash.write_text(hash_arquivo(arquivo) + "\n", encoding="ascii")
        tamanho = arquivo.stat().st_size
        arquivo.replace(resultados / PACOTE_LOTES)
        arquivo_hash.replace(resultados / arquivo_hash.name)
    return {"lotes": len(esperados), "arquivos_no_pacote": len(dados), "bytes_pacote": tamanho}


def extrair_lotes(resultados: Path, destino: Path) -> int:
    """Confere o pacote completo e extrai somente os nomes previstos, sem extractall."""
    arquivo = resultados / PACOTE_LOTES
    esperado = arquivo.with_suffix(".zip.sha256").read_text(encoding="ascii").strip()
    if hash_arquivo(arquivo) != esperado:
        raise ValueError("Hash do pacote de lotes diferente do registrado.")
    esperados = _lotes_registrados(resultados)
    nomes = set(esperados) | {n + ".sha256" for n in esperados}
    dados = {}
    with ZipFile(arquivo) as pacote:
        if len(pacote.namelist()) != len(nomes) or set(pacote.namelist()) != nomes:
            raise ValueError("Conteúdo do pacote diverge dos lotes registrados.")
        for nome, digest in esperados.items():
            conteudo, checksum = pacote.read(nome), pacote.read(nome + ".sha256")
            if sha256(conteudo).hexdigest() != digest or checksum.strip() != digest.encode("ascii"):
                raise ValueError(f"Hash de lote interno diferente do registrado: {nome}.")
            dados[Path(nome).name] = conteudo
            dados[Path(nome).name + ".sha256"] = checksum
    destino.mkdir(parents=True, exist_ok=True)
    for nome, conteudo in dados.items():
        (destino / nome).write_bytes(conteudo)
    return len(esperados)


def restaurar() -> dict[str, int]:
    """Valida as saídas em pasta temporária antes de repor somente arquivos locais."""
    protocolo = json.loads((RESULTADOS / "protocolo-utilizado.json").read_text(encoding="utf-8"))
    inventario = json.loads((CONTROLES / "inventario.json").read_text(encoding="utf-8"))
    consolidacao = json.loads((RESULTADOS / "consolidacao.json").read_text(encoding="utf-8"))
    with (RESULTADOS / "caracterizacao_redes.csv").open(encoding="utf-8", newline="") as arquivo:
        redes = list(csv.DictReader(arquivo))
    especificacoes = {r["id"]: r for r in protocolo["redes_planejadas"]}
    padroes = [
        (RESULTADOS / "lotes", "*.json.gz"),
        (RESULTADOS / "lotes", "*.json.gz.sha256"),
    ]
    protegidos = [CONTROLES / "inventario.json", *RESULTADOS.glob("*.json"),
                  RESULTADOS / PACOTE_LOTES, RESULTADOS / (PACOTE_LOTES + ".sha256"),
                  *(RESULTADOS / n for n in consolidacao["sha256_saidas"] if n not in EXPORTACOES)]
    for pasta, padrao in padroes:
        protegidos.extend(pasta.glob(padrao))
    hashes_protegidos = {p: hash_arquivo(p) for p in protegidos}

    with TemporaryDirectory(prefix="restaurar-topologias-") as temporario:
        area = Path(temporario)
        saida = area / "resultados"
        saida.mkdir()
        quantidade_lotes = extrair_lotes(RESULTADOS, saida / "lotes")
        for caminho in (saida / "lotes").iterdir():
            local = RESULTADOS / "lotes" / caminho.name
            if local.exists() and hash_arquivo(local) != hash_arquivo(caminho):
                raise ValueError(f"Lote local divergente; arquivo preservado: {local.name}.")
        controles = area / "controles"
        if preparar_controles(protocolo, controles) != inventario["redes"]:
            raise ValueError("Controles regenerados divergem do inventário preservado.")

        # consolidar() lê os lotes extraídos; todas as suas escritas ficam nesta área.
        shutil.copy2(RESULTADOS / "caracterizacao_redes.csv", saida / "caracterizacao_redes.csv")
        if consolidar(saida) != consolidacao:
            raise ValueError("Consolidação regenerada diverge do registro preservado.")

        for linha in redes:
            identificador = linha["rede"]
            especificacao = especificacoes[identificador]
            pasta = (controles / identificador if especificacao["tipo"] == "sintetica"
                     else RAIZ / especificacao["pasta"])
            rede = importar_rede_csv(
                pasta / "contatos.csv", arquivo_individuos=pasta / "individuos.csv",
            ).rede
            indicadores = caracterizar_rede(rede, saida / "caracterizacao" / identificador)
            if any(float(linha[k]) != valor for k, valor in indicadores.items()):
                raise ValueError(f"Caracterização regenerada diverge: {identificador}.")

        # A cópia exclui o inventário e os resumos já versionados.
        shutil.copytree(saida / "lotes", RESULTADOS / "lotes", dirs_exist_ok=True)
        for registro in inventario["redes"]:
            identificador = registro["rede_id"]
            shutil.copytree(controles / identificador, CONTROLES / identificador, dirs_exist_ok=True)
        shutil.copytree(saida / "caracterizacao", RESULTADOS / "caracterizacao", dirs_exist_ok=True)
        for nome in EXPORTACOES:
            shutil.copy2(saida / nome, RESULTADOS / nome)

    if any(hash_arquivo(p) != h for p, h in hashes_protegidos.items()):
        raise ValueError("Um dos arquivos preservados foi alterado durante a restauração.")
    return {"controles": len(inventario["redes"]), "redes_caracterizadas": len(redes),
            "lotes": quantidade_lotes, "exportacoes": len(EXPORTACOES), "novas_trajetorias": 0}


def main() -> None:
    """Restaura controles e CSVs, mantendo o log original somente onde já existe."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--empacotar-lotes", action="store_true")
    args = parser.parse_args()
    resumo = empacotar_lotes() if args.empacotar_lotes else restaurar()
    print(json.dumps(resumo, ensure_ascii=False))


if __name__ == "__main__":
    main()
