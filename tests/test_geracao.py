"""Propriedades dos modelos sintéticos e reprodução por configuração."""

from collections import Counter
from collections.abc import Callable
from dataclasses import FrozenInstanceError
from functools import partial
import random

import pytest

from simulador import (
    EstadoSIR,
    RedeContatos,
    ResultadoGeracaoRede,
    gerar_barabasi_albert,
    gerar_erdos_renyi,
)


@pytest.fixture(params=["erdos_renyi", "barabasi_albert"])
def gerador(request: pytest.FixtureRequest) -> Callable[..., ResultadoGeracaoRede]:
    if request.param == "erdos_renyi":
        return partial(gerar_erdos_renyi, probabilidade_contato=0.35)
    return partial(gerar_barabasi_albert, contatos_por_novo_individuo=2)


def _contatos(rede: RedeContatos) -> set[tuple[int, int, float]]:
    return {
        (min(c.origem.id, c.destino.id), max(c.origem.id, c.destino.id), c.peso)
        for c in rede.contatos
    }


def test_erdos_renyi_p_zero_preserva_todos_sem_contatos() -> None:
    resultado = gerar_erdos_renyi(9, 0, semente=0)

    assert resultado.rede.numero_individuos == 9
    assert resultado.rede.numero_contatos == 0
    assert all(resultado.rede.vizinhos(i) == () for i in range(9))


def test_erdos_renyi_p_um_cria_grafo_completo() -> None:
    rede = gerar_erdos_renyi(8, 1, semente=21).rede

    assert rede.numero_contatos == 28
    assert all(rede.grau(pessoa) == 7 for pessoa in rede.individuos)


def test_erdos_renyi_aceita_uma_pessoa() -> None:
    rede = gerar_erdos_renyi(1, 0.5, semente=8).rede

    assert rede.numero_individuos == 1
    assert rede.numero_contatos == 0


def test_erdos_renyi_configuracao_conhecida_reproduz_contatos() -> None:
    resultado = gerar_erdos_renyi(4, 0.5, semente=0, peso=0.8)

    assert _contatos(resultado.rede) == {(0, 3, 0.8), (1, 2, 0.8), (2, 3, 0.8)}
    assert resultado.modelo == "erdos_renyi"
    assert dict(resultado.parametros) == {
        "numero_individuos": 4,
        "probabilidade_contato": 0.5,
        "peso": 0.8,
    }


def test_barabasi_albert_versao_um_preserva_rede_conhecida() -> None:
    resultado = gerar_barabasi_albert(6, 2, semente=42)

    assert resultado.versao_algoritmo == 1
    assert _contatos(resultado.rede) == {
        (0, 1, 1.0), (0, 2, 1.0), (0, 3, 1.0), (0, 4, 1.0), (0, 5, 1.0),
        (1, 2, 1.0), (1, 4, 1.0), (2, 3, 1.0), (2, 5, 1.0),
    }


@pytest.mark.parametrize("n,m", [(2, 1), (8, 1), (8, 2), (15, 4), (8, 7)])
@pytest.mark.parametrize("semente", [0, 19])
def test_barabasi_albert_nucleo_crescimento_e_conectividade(
    n: int, m: int, semente: int
) -> None:
    resultado = gerar_barabasi_albert(n, m, semente=semente)
    rede = resultado.rede

    assert resultado.modelo == "barabasi_albert"
    assert resultado.detalhes_modelo["tamanho_nucleo_inicial"] == m + 1
    assert resultado.parametros["contatos_por_novo_individuo"] == m
    assert rede.numero_individuos == n
    assert rede.numero_contatos == m * n - m * (m + 1) // 2
    for origem in range(m + 1):
        for destino in range(origem + 1, m + 1):
            assert rede.obter_contato(origem, destino).peso == 1
    for novo_id in range(m + 1, n):
        anteriores = [vizinho.id for vizinho in rede.vizinhos(novo_id) if vizinho.id < novo_id]
        assert len(anteriores) == m

    visitados = {0}
    pendentes = [0]
    while pendentes:
        for vizinho in rede.vizinhos(pendentes.pop()):
            if vizinho.id not in visitados:
                visitados.add(vizinho.id)
                pendentes.append(vizinho.id)
    assert visitados == set(range(n))


def test_barabasi_albert_pondera_escolhas_por_grau_antes_de_cada_inclusao(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    amostras: list[tuple[int, ...]] = []

    class AleatorioObservado(random.Random):
        def choice(self, sequencia: list[int]) -> int:
            amostras.append(tuple(sequencia))
            return super().choice(sequencia)

    monkeypatch.setattr("simulador.geracao.Random", AleatorioObservado)

    rede = gerar_barabasi_albert(12, 3, semente=15).rede

    assert amostras
    for amostra in amostras:
        novo_id = max(amostra) + 1
        # Desconsidera contatos com as pessoas que ainda não haviam chegado.
        graus_anteriores = {
            i: sum(vizinho.id < novo_id for vizinho in rede.vizinhos(i))
            for i in range(novo_id)
        }
        assert Counter(amostra) == graus_anteriores


@pytest.mark.parametrize("semente", [0, -17, 999, 10**80])
def test_mesma_configuracao_reproduz_rede_independente(
    gerador: Callable[..., ResultadoGeracaoRede], semente: int
) -> None:
    primeiro = gerador(numero_individuos=30, semente=semente, peso=0.7)
    gerador(numero_individuos=12, semente=semente + 1)
    segundo = gerador(numero_individuos=30, semente=semente, peso=0.7)

    assert primeiro.semente == segundo.semente == semente
    assert primeiro.parametros == segundo.parametros
    assert primeiro.versao_algoritmo == segundo.versao_algoritmo == 1
    assert _contatos(primeiro.rede) == _contatos(segundo.rede)
    assert primeiro.rede is not segundo.rede
    assert primeiro.rede.obter_individuo(0) is not segundo.rede.obter_individuo(0)
    primeiro.rede.obter_individuo(0).infectar(0)
    primeiro.rede.obter_individuo(0).isolar()
    assert segundo.rede.obter_individuo(0).estado is EstadoSIR.SUSCETIVEL
    assert segundo.rede.obter_individuo(0).isolamento is False


def test_semente_influencia_um_caso_nao_deterministico(
    gerador: Callable[..., ResultadoGeracaoRede],
) -> None:
    primeiro = gerador(numero_individuos=30, semente=5)
    segundo = gerador(numero_individuos=30, semente=11)

    assert _contatos(primeiro.rede) != _contatos(segundo.rede)


def test_geracao_nao_consume_aleatoriedade_global(
    gerador: Callable[..., ResultadoGeracaoRede],
) -> None:
    estado_anterior = random.getstate()

    gerador(numero_individuos=20, semente=50)

    assert random.getstate() == estado_anterior


@pytest.mark.parametrize("peso", [0, 0.4, 1])
def test_peso_uniforme_nao_altera_topologia_e_rede_e_simples_simetrica(
    gerador: Callable[..., ResultadoGeracaoRede], peso: float
) -> None:
    rede = gerador(numero_individuos=20, semente=2, peso=peso).rede
    referencia = gerador(numero_individuos=20, semente=2).rede

    assert {(u, v) for u, v, _ in _contatos(rede)} == {
        (u, v) for u, v, _ in _contatos(referencia)
    }
    assert {pessoa.id for pessoa in rede.individuos} == set(range(20))
    assert len(_contatos(rede)) == rede.numero_contatos
    assert sum(rede.grau(pessoa) for pessoa in rede.individuos) == 2 * rede.numero_contatos
    for contato in rede.contatos:
        u, v = contato.origem.id, contato.destino.id
        assert u != v
        assert rede.obter_contato(u, v) is rede.obter_contato(v, u)
        assert contato.peso == peso
    for pessoa in rede.individuos:
        assert pessoa.estado is EstadoSIR.SUSCETIVEL
        assert pessoa.isolamento is False
        assert pessoa.dia_inicio_infeccao is None


def test_metadados_nao_podem_ser_sobrescritos(
    gerador: Callable[..., ResultadoGeracaoRede],
) -> None:
    resultado = gerador(numero_individuos=6, semente=42)

    with pytest.raises(TypeError):
        resultado.parametros["peso"] = 0.1
    with pytest.raises(FrozenInstanceError):
        resultado.semente = 7


def test_resultado_copia_parametros_recebidos() -> None:
    parametros = {"numero_individuos": 8, "peso": 1.0}
    resultado = ResultadoGeracaoRede(RedeContatos(), "exemplo", parametros, 0)

    parametros["peso"] = 0.4

    assert resultado.parametros["peso"] == 1


@pytest.mark.parametrize("valor", [True, False, 3.0, "8", None])
def test_rejeita_populacao_com_tipo_invalido(
    gerador: Callable[..., ResultadoGeracaoRede], valor: object
) -> None:
    with pytest.raises(TypeError, match="numero_individuos"):
        gerador(numero_individuos=valor, semente=0)


@pytest.mark.parametrize("valor", [0, -1])
def test_rejeita_populacao_nao_positiva(
    gerador: Callable[..., ResultadoGeracaoRede], valor: int
) -> None:
    with pytest.raises(ValueError, match="numero_individuos"):
        gerador(numero_individuos=valor, semente=0)


@pytest.mark.parametrize("valor", [True, 0.0, "7", None])
def test_rejeita_semente_com_tipo_invalido(
    gerador: Callable[..., ResultadoGeracaoRede], valor: object
) -> None:
    with pytest.raises(TypeError, match="semente"):
        gerador(numero_individuos=8, semente=valor)


def test_exige_semente_explicita(gerador: Callable[..., ResultadoGeracaoRede]) -> None:
    with pytest.raises(TypeError, match="semente"):
        gerador(numero_individuos=8)


@pytest.mark.parametrize("valor", [True, "0.5", None, 1 + 0j])
def test_rejeita_peso_com_tipo_invalido(
    gerador: Callable[..., ResultadoGeracaoRede], valor: object
) -> None:
    with pytest.raises(TypeError, match="peso"):
        gerador(numero_individuos=8, semente=0, peso=valor)


@pytest.mark.parametrize("valor", [-0.1, 1.1, float("inf"), float("-inf"), float("nan"), 10**400])
def test_rejeita_peso_fora_do_dominio(
    gerador: Callable[..., ResultadoGeracaoRede], valor: float
) -> None:
    with pytest.raises(ValueError, match="peso"):
        gerador(numero_individuos=8, semente=0, peso=valor)


@pytest.mark.parametrize("valor", [True, "0.5", None, 0.5j])
def test_erdos_renyi_rejeita_probabilidade_com_tipo_invalido(valor: object) -> None:
    with pytest.raises(TypeError, match="probabilidade_contato"):
        gerar_erdos_renyi(8, valor, semente=0)


@pytest.mark.parametrize("valor", [-0.1, 1.1, float("inf"), float("nan"), 10**400])
def test_erdos_renyi_rejeita_probabilidade_fora_do_dominio(valor: float) -> None:
    with pytest.raises(ValueError, match="probabilidade_contato"):
        gerar_erdos_renyi(8, valor, semente=0)


@pytest.mark.parametrize("valor", [True, False, 2.0, "2", None])
def test_barabasi_albert_rejeita_m_com_tipo_invalido(valor: object) -> None:
    with pytest.raises(TypeError, match="contatos_por_novo_individuo"):
        gerar_barabasi_albert(8, valor, semente=0)


@pytest.mark.parametrize("n,m", [(1, 1), (8, 0), (8, -2), (8, 8), (8, 9)])
def test_barabasi_albert_rejeita_m_fora_do_dominio(n: int, m: int) -> None:
    with pytest.raises(ValueError, match="contatos_por_novo_individuo"):
        gerar_barabasi_albert(n, m, semente=0)
