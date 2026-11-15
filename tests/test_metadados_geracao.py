"""Reconstrução por configuração, exportação e cópia dos resultados."""

from collections.abc import Callable
from copy import deepcopy
from dataclasses import asdict
from functools import partial
import json
import sys

import pytest

from simulador import (
    EstadoSIR,
    RedeContatos,
    ResultadoGeracaoRede,
    gerar_barabasi_albert,
    gerar_erdos_renyi,
    reconstruir_rede,
)


@pytest.fixture(params=["erdos_renyi", "barabasi_albert"])
def gerador(request: pytest.FixtureRequest) -> Callable[..., ResultadoGeracaoRede]:
    if request.param == "erdos_renyi":
        return partial(gerar_erdos_renyi, probabilidade_contato=0.3)
    return partial(gerar_barabasi_albert, contatos_por_novo_individuo=2)


def _assinatura(rede: RedeContatos) -> tuple[tuple[int, ...], tuple[tuple[int, int, float], ...]]:
    return (
        tuple(p.id for p in rede.individuos),
        tuple((c.origem.id, c.destino.id, c.peso) for c in rede.contatos),
    )


@pytest.mark.parametrize("semente", [0, -7, 42])
def test_reconstrucao_por_metadados_json_preserva_contatos_ordens_e_configuracao(
    gerador: Callable[..., ResultadoGeracaoRede], semente: int
) -> None:
    original = gerador(numero_individuos=20, semente=semente, peso=0.7)
    metadados = json.loads(json.dumps(original.exportar_metadados(), allow_nan=False))

    reconstruido = reconstruir_rede(metadados)

    assert reconstruido.rede is not original.rede
    assert _assinatura(reconstruido.rede) == _assinatura(original.rede)
    assert reconstruido.exportar_metadados() == original.exportar_metadados()
    for pessoa in original.rede.individuos:
        assert reconstruido.rede.obter_individuo(pessoa.id) is not pessoa
        assert [v.id for v in reconstruido.rede.vizinhos(pessoa.id)] == [
            v.id for v in original.rede.vizinhos(pessoa.id)
        ]


def test_parametros_sao_aceitos_diretamente_pelos_dois_geradores(
    gerador: Callable[..., ResultadoGeracaoRede],
) -> None:
    original = gerador(numero_individuos=10, semente=42)
    funcao = gerar_erdos_renyi if original.modelo == "erdos_renyi" else gerar_barabasi_albert

    reconstruido = funcao(**original.parametros, semente=original.semente)

    assert _assinatura(reconstruido.rede) == _assinatura(original.rede)
    if original.modelo == "barabasi_albert":
        assert "tamanho_nucleo_inicial" not in original.parametros
        assert original.detalhes_modelo == {"tamanho_nucleo_inicial": 3}
    else:
        assert original.detalhes_modelo == {}


def test_exportacao_devolve_dicionarios_independentes(
    gerador: Callable[..., ResultadoGeracaoRede],
) -> None:
    resultado = gerador(numero_individuos=8, semente=42)
    metadados = resultado.exportar_metadados()

    metadados["parametros"]["peso"] = 0.2
    metadados["detalhes_modelo"]["extra"] = 10

    assert resultado.parametros["peso"] == 1
    assert "extra" not in resultado.detalhes_modelo
    assert resultado.exportar_metadados()["parametros"]["peso"] == 1


def test_metadados_imutaveis_nao_retem_dicionarios_externos() -> None:
    parametros = {"numero_individuos": 8, "peso": 0.7}
    detalhes = {"tamanho_nucleo_inicial": 3}
    resultado = ResultadoGeracaoRede(
        RedeContatos(), "exemplo", parametros, 42, detalhes_modelo=detalhes
    )

    parametros["peso"] = 0.1
    detalhes["tamanho_nucleo_inicial"] = 5

    assert resultado.parametros["peso"] == 0.7
    assert resultado.detalhes_modelo["tamanho_nucleo_inicial"] == 3
    with pytest.raises(TypeError):
        resultado.detalhes_modelo["tamanho_nucleo_inicial"] = 4
    with pytest.raises(KeyError):
        resultado.parametros["ausente"]
    assert "peso" in repr(resultado.parametros)


@pytest.mark.parametrize("operacao", [deepcopy, lambda r: r.copiar()])
def test_copia_do_resultado_preserva_condicao_atual_sem_compartilhar_rede(
    gerador: Callable[..., ResultadoGeracaoRede],
    operacao: Callable[[ResultadoGeracaoRede], ResultadoGeracaoRede],
) -> None:
    original = gerador(numero_individuos=8, semente=42)
    original.rede.obter_individuo(0).infectar(3)
    original.rede.obter_individuo(0).isolar()

    copia = operacao(original)

    assert copia is not original
    assert copia.rede is not original.rede
    assert _assinatura(copia.rede) == _assinatura(original.rede)
    assert copia.exportar_metadados() == original.exportar_metadados()
    for pessoa in original.rede.individuos:
        assert copia.rede.obter_individuo(pessoa.id) is not pessoa
    assert copia.rede.obter_individuo(0).dia_inicio_infeccao == 3
    assert copia.rede.obter_individuo(0).isolamento is True
    copia.rede.obter_individuo(0).recuperar()
    assert original.rede.obter_individuo(0).estado is EstadoSIR.INFECTADO
    with pytest.raises(TypeError):
        copia.parametros["peso"] = 0.2
    with pytest.raises(TypeError):
        copia.detalhes_modelo["extra"] = 1


def test_recriar_retorna_condicao_inicial_em_vez_de_copiar_alteracoes_posteriores(
    gerador: Callable[..., ResultadoGeracaoRede],
) -> None:
    resultado = gerador(numero_individuos=8, semente=42)
    assinatura_inicial = _assinatura(resultado.rede)
    resultado.rede.obter_individuo(0).infectar(3)
    resultado.rede.obter_individuo(0).isolar()

    recriado = resultado.recriar()

    assert _assinatura(recriado.rede) == assinatura_inicial
    assert recriado.rede.obter_individuo(0).estado is EstadoSIR.SUSCETIVEL
    assert recriado.rede.obter_individuo(0).isolamento is False
    assert recriado.rede.obter_individuo(0).dia_inicio_infeccao is None
    assert resultado.rede.obter_individuo(0).estado is EstadoSIR.INFECTADO


def test_asdict_funciona_e_copia_a_rede_preservando_parametros_somente_leitura(
    gerador: Callable[..., ResultadoGeracaoRede],
) -> None:
    resultado = gerador(numero_individuos=8, semente=42)

    convertido = asdict(resultado)

    assert isinstance(convertido, dict)
    assert convertido["rede"] is not resultado.rede
    assert _assinatura(convertido["rede"]) == _assinatura(resultado.rede)
    assert dict(convertido["parametros"]) == dict(resultado.parametros)
    assert dict(convertido["detalhes_modelo"]) == dict(resultado.detalhes_modelo)
    with pytest.raises(TypeError):
        convertido["parametros"]["peso"] = 0


@pytest.mark.parametrize("pessoa_primeiro", [False, True])
def test_deepcopy_preserva_referencias_compartilhadas_no_conteiner(
    pessoa_primeiro: bool,
) -> None:
    resultado = gerar_erdos_renyi(3, 1, semente=0)
    pessoa = resultado.rede.obter_individuo(0)
    contato = resultado.rede.obter_contato(0, 1)
    elementos = [pessoa, contato, resultado] if pessoa_primeiro else [resultado, contato, pessoa]

    copiados = deepcopy(elementos)
    copia = copiados[2] if pessoa_primeiro else copiados[0]
    pessoa_copiada = copiados[0] if pessoa_primeiro else copiados[2]

    assert pessoa_copiada is copia.rede.obter_individuo(0)
    assert copiados[1] is copia.rede.obter_contato(0, 1)
    assert copiados[1].origem is pessoa_copiada
    assert copiados[1].destino is copia.rede.obter_individuo(1)


def test_asdict_e_copia_suportam_caminho_maior_que_limite_de_recursao() -> None:
    n = sys.getrecursionlimit() + 50
    resultado = gerar_erdos_renyi(n, 0, semente=0)
    for origem in range(n - 1):
        resultado.rede.adicionar_contato(origem, origem + 1)

    convertido = asdict(resultado)
    copia = deepcopy(resultado)

    assert _assinatura(convertido["rede"]) == _assinatura(resultado.rede)
    assert _assinatura(copia.rede) == _assinatura(resultado.rede)


@pytest.mark.parametrize("campo", ["modelo", "parametros", "semente", "versao_algoritmo"])
def test_reconstrucao_rejeita_metadados_incompletos(campo: str) -> None:
    metadados = gerar_erdos_renyi(3, 0, semente=0).exportar_metadados()
    del metadados[campo]

    with pytest.raises(ValueError, match=campo):
        reconstruir_rede(metadados)


@pytest.mark.parametrize(
    "campo,valor,erro",
    [
        ("modelo", "outro", ValueError),
        ("modelo", 1, TypeError),
        ("parametros", None, TypeError),
        ("parametros", [], TypeError),
        ("semente", True, TypeError),
        ("versao_algoritmo", True, TypeError),
        ("versao_algoritmo", 1.0, TypeError),
        ("versao_algoritmo", "1", TypeError),
        ("versao_algoritmo", 2, ValueError),
        ("detalhes_modelo", None, TypeError),
        ("detalhes_modelo", {"extra": 1}, ValueError),
    ],
)
def test_reconstrucao_rejeita_campos_invalidos(campo: str, valor: object, erro: type[Exception]) -> None:
    metadados = gerar_erdos_renyi(3, 0, semente=0).exportar_metadados()
    metadados[campo] = valor

    with pytest.raises(erro):
        reconstruir_rede(metadados)


@pytest.mark.parametrize("metadados", [None, [], {1: 2}])
def test_reconstrucao_exige_mapa_com_chaves_textuais(metadados: object) -> None:
    with pytest.raises(TypeError):
        reconstruir_rede(metadados)


def test_reconstrucao_nao_descarta_campos_desconhecidos() -> None:
    metadados = gerar_erdos_renyi(3, 0, semente=0).exportar_metadados()
    metadados["sementee"] = 1

    with pytest.raises(ValueError, match="sementee"):
        reconstruir_rede(metadados)


@pytest.mark.parametrize("parametros", [{"numero_individuos": 3}, {"numero_individuos": 3, "p": 0}])
def test_reconstrucao_identifica_parametro_obrigatorio_ausente(parametros: dict[str, int]) -> None:
    metadados = gerar_erdos_renyi(3, 0, semente=0).exportar_metadados()
    metadados["parametros"] = parametros

    with pytest.raises(ValueError, match="probabilidade_contato"):
        reconstruir_rede(metadados)


def test_reconstrucao_rejeita_parametro_extra_e_detalhe_derivado_incoerente() -> None:
    metadados = gerar_barabasi_albert(8, 2, semente=0).exportar_metadados()
    metadados["parametros"]["extra"] = 4
    with pytest.raises(ValueError, match="extra"):
        reconstruir_rede(metadados)
    del metadados["parametros"]["extra"]
    metadados["detalhes_modelo"]["tamanho_nucleo_inicial"] = 4
    with pytest.raises(ValueError, match="detalhes_modelo"):
        reconstruir_rede(metadados)


def test_reconstrucao_aceita_detalhes_omitidos_e_peso_padrao() -> None:
    reconstruido = reconstruir_rede({
        "modelo": "barabasi_albert",
        "parametros": {"numero_individuos": 8, "contatos_por_novo_individuo": 2},
        "semente": 42,
        "versao_algoritmo": 1,
    })

    assert reconstruido.parametros["peso"] == 1
    assert reconstruido.detalhes_modelo == {"tamanho_nucleo_inicial": 3}


@pytest.mark.parametrize(
    "parametros,erro",
    [({1: 2}, TypeError), ({"x": []}, TypeError), ({"x": float("inf")}, ValueError)],
)
def test_resultado_impede_metadados_mutaveis_ou_incompativeis_com_json(
    parametros: dict[object, object], erro: type[Exception]
) -> None:
    with pytest.raises(erro):
        ResultadoGeracaoRede(RedeContatos(), "exemplo", parametros, 0)


@pytest.mark.parametrize("campo", ["modelo", "semente", "versao_algoritmo"])
def test_resultado_valida_tipos_de_identificacao(campo: str) -> None:
    argumentos = {"rede": RedeContatos(), "modelo": "exemplo", "parametros": {}, "semente": 0}
    argumentos[campo] = None
    with pytest.raises(TypeError, match=campo):
        ResultadoGeracaoRede(**argumentos)
