"""Importação de redes CSV com diagnóstico por arquivo, linha e campo."""

import csv
import math
import re
from collections.abc import Iterator
from dataclasses import dataclass
from os import PathLike
from pathlib import Path

from simulador.individuo import Individuo
from simulador.rede_contatos import RedeContatos


@dataclass(frozen=True, slots=True)
class ProblemaImportacao:
    """Problema localizável no arquivo; linha indica o início do registro CSV."""

    arquivo: Path
    linha: int | None
    campo: str | None
    mensagem: str

    def __str__(self) -> str:
        local = str(self.arquivo)
        if self.linha is not None:
            local += f", linha {self.linha}"
        if self.campo is not None:
            local += f", campo {self.campo!r}"
        return f"{local}: {self.mensagem}"


class ErroImportacaoRede(ValueError):
    """Reúne os problemas encontrados sem disponibilizar uma rede parcial."""

    def __init__(self, problemas: tuple[ProblemaImportacao, ...]) -> None:
        """Preserva os diagnósticos estruturados para exibição pela interface."""
        self.problemas = problemas
        super().__init__(
            "Não foi possível importar a rede:\n"
            + "\n".join(str(problema) for problema in problemas)
        )


@dataclass(frozen=True, slots=True)
class ResultadoImportacaoRede:
    """Rede validada e arquivos de origem, para consulta após a importação."""

    rede: RedeContatos
    arquivo_contatos: Path
    arquivo_individuos: Path | None = None


def _ler_registros(
    arquivo: Path,
    obrigatorias: tuple[str, ...],
    opcionais: tuple[str, ...],
    delimitador: str,
    problemas: list[ProblemaImportacao],
) -> Iterator[tuple[int, dict[str, str]]]:
    inicio_linha = 1
    try:
        with arquivo.open(encoding="utf-8-sig", newline="") as entrada:
            leitor = csv.reader(entrada, delimiter=delimitador, skipinitialspace=True, strict=True)
            cabecalho: list[str] | None = None
            while True:
                inicio_linha = leitor.line_num + 1
                try:
                    valores = next(leitor)
                except StopIteration:
                    break
                if not valores or (len(valores) == 1 and not valores[0].strip()):
                    continue
                if cabecalho is None:
                    cabecalho = [valor.strip().lower() for valor in valores]
                    colunas = set(cabecalho)
                    faltantes = set(obrigatorias) - colunas
                    desconhecidas = colunas - set(obrigatorias + opcionais)
                    mensagens = []
                    if len(colunas) != len(cabecalho):
                        mensagens.append("O cabeçalho contém colunas repetidas.")
                    if faltantes:
                        mensagens.append(
                            "Colunas obrigatórias ausentes: " + ", ".join(sorted(faltantes)) + "."
                        )
                    if desconhecidas:
                        mensagens.append(
                            "Colunas não suportadas: "
                            + ", ".join(repr(coluna) for coluna in sorted(desconhecidas))
                            + "."
                        )
                    if mensagens:
                        problemas.append(
                            ProblemaImportacao(
                                arquivo, inicio_linha, "cabeçalho", " ".join(mensagens)
                            )
                        )
                        return
                    continue
                if len(valores) != len(cabecalho):
                    problemas.append(
                        ProblemaImportacao(
                            arquivo,
                            inicio_linha,
                            None,
                            f"Esperadas {len(cabecalho)} colunas, recebidas {len(valores)}. "
                            "Confira os separadores e os campos vazios.",
                        )
                    )
                    continue
                yield inicio_linha, dict(zip(cabecalho, (valor.strip() for valor in valores)))
            if cabecalho is None:
                problemas.append(
                    ProblemaImportacao(
                        arquivo, None, "cabeçalho", "Arquivo vazio. Informe as colunas: "
                        + ", ".join(obrigatorias) + "."
                    )
                )
    except UnicodeError:
        problemas.append(
            ProblemaImportacao(
                arquivo, None, None, "Codificação inválida. Salve o arquivo como UTF-8."
            )
        )
    except OSError as erro:
        problemas.append(
            ProblemaImportacao(
                arquivo, None, None, f"Não foi possível ler o arquivo: {erro.strerror}."
            )
        )
    except csv.Error as erro:
        problemas.append(
            ProblemaImportacao(
                arquivo, inicio_linha, None,
                f"CSV malformado: {erro}. Confira as aspas e os separadores.",
            )
        )


def _ler_id(
    valor: str,
    arquivo: Path,
    linha: int,
    campo: str,
    problemas: list[ProblemaImportacao],
) -> int | None:
    if re.fullmatch(r"[+-]?[0-9]+", valor) is not None:
        try:
            return int(valor)
        except ValueError:
            pass
    problemas.append(
        ProblemaImportacao(
            arquivo, linha, campo, f"ID inválido {valor!r}. Informe um número inteiro."
        )
    )
    return None


def _ler_peso(
    valor: str, arquivo: Path, linha: int, problemas: list[ProblemaImportacao]
) -> float | None:
    if not valor:
        return 1.0
    try:
        peso = float(valor)
    except ValueError:
        peso = math.nan
    if math.isfinite(peso) and 0 <= peso <= 1:
        return peso
    problemas.append(
        ProblemaImportacao(
            arquivo, linha, "peso",
            f"Peso inválido {valor!r}. Informe um número finito entre 0 e 1, "
            "usando ponto como separador decimal.",
        )
    )
    return None


def importar_rede_csv(
    arquivo_contatos: str | PathLike[str],
    *,
    arquivo_individuos: str | PathLike[str] | None = None,
    delimitador: str = ",",
) -> ResultadoImportacaoRede:
    """Importa contatos e, opcionalmente, um cadastro completo de indivíduos.

    Args:
        arquivo_contatos: CSV UTF-8 com origem, destino e peso opcional.
        arquivo_individuos: CSV UTF-8 com coluna id. Preserva pessoas sem
            contatos e exige que todos os extremos estejam nesse cadastro.
            Sem esse arquivo, os IDs são inferidos dos contatos válidos.
        delimitador: Separador de uma posição, por padrão vírgula.

    Returns:
        Rede não vazia e arquivos de origem. Pesos omitidos assumem 1.

    Raises:
        ErroImportacaoRede: Se houver problemas de leitura, esquema ou dados.
            Todos os problemas recuperáveis são reunidos antes de retornar.
        TypeError: Se o delimitador não for uma string.
        ValueError: Se o delimitador for inválido.
    """
    if not isinstance(delimitador, str):
        raise TypeError("O delimitador deve ser uma string.")
    if len(delimitador) != 1 or delimitador in '\r\n"':
        raise ValueError("Use um delimitador de um caractere, diferente de aspas e quebras de linha.")
    contatos = Path(arquivo_contatos)
    individuos = Path(arquivo_individuos) if arquivo_individuos is not None else None
    rede = RedeContatos()
    problemas: list[ProblemaImportacao] = []

    if individuos is not None:
        linhas_ids: dict[int, int] = {}
        for linha, registro in _ler_registros(individuos, ("id",), (), delimitador, problemas):
            identificador = _ler_id(registro["id"], individuos, linha, "id", problemas)
            if identificador is None:
                continue
            if identificador in linhas_ids:
                problemas.append(
                    ProblemaImportacao(
                        individuos, linha, "id", f"ID {identificador} repetido; "
                        f"primeiro cadastro na linha {linhas_ids[identificador]}.",
                    )
                )
                continue
            rede.adicionar_individuo(Individuo(identificador))
            linhas_ids[identificador] = linha
    cadastro_valido = not problemas

    pares: dict[tuple[int, int], int] = {}
    for linha, registro in _ler_registros(
        contatos, ("origem", "destino"), ("peso",), delimitador, problemas
    ):
        origem = _ler_id(registro["origem"], contatos, linha, "origem", problemas)
        destino = _ler_id(registro["destino"], contatos, linha, "destino", problemas)
        peso = _ler_peso(registro.get("peso", ""), contatos, linha, problemas)
        if origem is None or destino is None or peso is None:
            continue
        if origem == destino:
            problemas.append(
                ProblemaImportacao(
                    contatos, linha, "origem/destino", "Um contato não pode ligar um ID a ele mesmo."
                )
            )
            continue
        par = (min(origem, destino), max(origem, destino))
        if par in pares:
            problemas.append(
                ProblemaImportacao(
                    contatos, linha, "origem/destino", "Contato duplicado, inclusive em sentido "
                    f"invertido; primeira ocorrência na linha {pares[par]}.",
                )
            )
            continue
        pares[par] = linha
        if individuos is not None:
            if not cadastro_valido:
                continue
            faltantes = False
            for campo, identificador in (("origem", origem), ("destino", destino)):
                if rede.buscar_individuo(identificador) is None:
                    problemas.append(
                        ProblemaImportacao(
                            contatos, linha, campo,
                            f"ID {identificador} não consta no arquivo de indivíduos {individuos}.",
                        )
                    )
                    faltantes = True
            if faltantes:
                continue
        else:
            for identificador in (origem, destino):
                if rede.buscar_individuo(identificador) is None:
                    rede.adicionar_individuo(Individuo(identificador))
        rede.adicionar_contato(origem, destino, peso)

    if not problemas and rede.numero_individuos == 0:
        problemas.append(
            ProblemaImportacao(
                contatos, None, None,
                "Nenhum indivíduo encontrado. Informe contatos ou um cadastro de indivíduos.",
            )
        )
    if problemas:
        raise ErroImportacaoRede(tuple(problemas))
    return ResultadoImportacaoRede(rede, contatos, individuos)
