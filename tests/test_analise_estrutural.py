"""Percursos, conectividade e métricas estruturais sem modificar o domínio."""

from collections.abc import Callable
from dataclasses import FrozenInstanceError
from itertools import combinations
from pathlib import Path
import sys

import pytest

from simulador import (
    Individuo,
    RedeContatos,
    ResumoEstrutural,
    bfs,
    componentes_conexas,
    dfs,
    esta_conexa,
    gerar_barabasi_albert,
    gerar_erdos_renyi,
    importar_rede_csv,
    resumir_rede,
)


@pytest.fixture
def rede() -> RedeContatos:
    rede = RedeContatos()
    for identificador in (10, -2, 7, 4, 9, 20, 0, 99):
        rede.adicionar_individuo(Individuo(identificador))
    for origem, destino in ((10, 7), (10, -2), (7, 4), (-2, 4), (4, 9), (20, 0)):
        rede.adicionar_contato(origem, destino, peso=0.4)
    return rede


def test_bfs_visita_por_nivel_e_na_ordem_dos_contatos(rede: RedeContatos) -> None:
    assert bfs(rede, 10) == (10, 7, -2, 4, 9)
    assert bfs(rede, 4) == (4, 7, -2, 9, 10)


def test_dfs_explora_cada_ramo_antes_dos_demais_vizinhos(rede: RedeContatos) -> None:
    assert dfs(rede, 10) == (10, 7, 4, -2, 9)
    assert dfs(rede, 4) == (4, 7, 10, -2, 9)


@pytest.mark.parametrize("percurso", [bfs, dfs])
@pytest.mark.parametrize(
    "origem,esperado",
    [(99, (99,)), (20, (20, 0)), (0, (0, 20)), (-2, (-2, 10, 4, 7, 9))],
)
def test_percurso_fica_na_componente_e_aceita_zero_e_negativos(
    rede: RedeContatos,
    percurso: Callable[[RedeContatos, int], tuple[int, ...]],
    origem: int,
    esperado: tuple[int, ...],
) -> None:
    resultado = percurso(rede, origem)

    assert resultado[0] == origem
    assert set(resultado) == set(esperado)
    assert len(resultado) == len(esperado)
    assert len(resultado) == len(set(resultado))


def test_componentes_particionam_cadastro_incluindo_pessoas_sem_contatos(
    rede: RedeContatos,
) -> None:
    assert componentes_conexas(rede) == (
        frozenset({10, -2, 7, 4, 9}),
        frozenset({20, 0}),
        frozenset({99}),
    )
    assert esta_conexa(rede) is False


def test_conectividade_e_componentes_refletem_contatos_adicionados(rede: RedeContatos) -> None:
    anteriores = componentes_conexas(rede)

    rede.adicionar_contato(9, 20)

    assert esta_conexa(rede) is False
    assert componentes_conexas(rede) == (
        frozenset({10, -2, 7, 4, 9, 20, 0}),
        frozenset({99}),
    )

    rede.adicionar_contato(0, 99)

    assert esta_conexa(rede) is True
    assert componentes_conexas(rede) == (frozenset({10, -2, 7, 4, 9, 20, 0, 99}),)
    assert len(anteriores) == 3
    assert anteriores[-1] == frozenset({99})


def test_rede_vazia_tem_resumo_definido_e_nenhuma_componente() -> None:
    rede = RedeContatos()

    assert componentes_conexas(rede) == ()
    assert esta_conexa(rede) is False
    assert resumir_rede(rede) == ResumoEstrutural(0, 0, 0.0)


def test_rede_unitaria_e_conexa_com_grau_zero() -> None:
    rede = RedeContatos()
    rede.adicionar_individuo(Individuo(-7))

    assert bfs(rede, -7) == dfs(rede, -7) == (-7,)
    assert componentes_conexas(rede) == (frozenset({-7}),)
    assert esta_conexa(rede) is True
    assert resumir_rede(rede) == ResumoEstrutural(1, 0, 0.0)


def test_resumo_conta_contatos_uma_vez_e_inclui_grau_zero_na_media(
    rede: RedeContatos,
) -> None:
    resumo = resumir_rede(rede)

    assert resumo == ResumoEstrutural(8, 6, 1.5)
    assert resumo.grau_medio == 2 * resumo.numero_contatos / resumo.numero_individuos


def test_resumo_preserva_precisao_sem_arredondar() -> None:
    rede = RedeContatos()
    for identificador in range(3):
        rede.adicionar_individuo(Individuo(identificador))
    rede.adicionar_contato(0, 1)

    assert resumir_rede(rede).grau_medio == pytest.approx(2 / 3)


def test_resumo_reutiliza_grau_individual_inclusive_de_pessoa_sem_contatos(
    rede: RedeContatos, monkeypatch: pytest.MonkeyPatch
) -> None:
    grau_original = rede.grau
    consultados: list[int] = []

    def grau_observado(pessoa: Individuo) -> int:
        consultados.append(pessoa.id)
        return grau_original(pessoa)

    monkeypatch.setattr(rede, "grau", grau_observado)

    resumo = resumir_rede(rede)

    assert resumo.grau_medio == 1.5
    assert consultados == [pessoa.id for pessoa in rede.individuos]


def test_resumo_e_imutavel_e_preserva_valores_apos_mudanca_na_rede(
    rede: RedeContatos,
) -> None:
    resumo = resumir_rede(rede)

    rede.adicionar_individuo(Individuo(100))
    rede.adicionar_contato(99, 100)

    assert resumo == ResumoEstrutural(8, 6, 1.5)
    assert resumir_rede(rede).numero_individuos == 9
    assert resumir_rede(rede).numero_contatos == 7
    with pytest.raises(FrozenInstanceError):
        resumo.grau_medio = 0.0


def test_peso_zero_e_isolamento_nao_excluem_contatos_da_analise() -> None:
    rede = RedeContatos()
    for identificador in range(3):
        rede.adicionar_individuo(Individuo(identificador))
    rede.adicionar_contato(0, 1, peso=0)
    rede.adicionar_contato(1, 2, peso=0.5)
    rede.obter_individuo(1).isolar()
    rede.desativar_contato(0, 1)
    rede.desativar_contato(1, 2)

    assert all(not contato.ativa for contato in rede.contatos)
    assert bfs(rede, 0) == dfs(rede, 0) == (0, 1, 2)
    assert componentes_conexas(rede) == (frozenset({0, 1, 2}),)
    assert esta_conexa(rede) is True
    assert resumir_rede(rede) == ResumoEstrutural(3, 2, 4 / 3)


def test_analise_nao_altera_cadastro_contatos_ou_estados(rede: RedeContatos) -> None:
    rede.obter_individuo(10).infectar(0)
    rede.obter_individuo(10).isolar()
    rede.obter_individuo(7).infectar(1)
    rede.obter_individuo(7).recuperar()
    pessoas_antes = rede.individuos
    contatos_antes = rede.contatos
    estados_antes = tuple(
        (p.id, p.estado, p.isolamento, p.dia_inicio_infeccao) for p in rede.individuos
    )

    for _ in range(2):
        assert bfs(rede, 10) == (10, 7, -2, 4, 9)
        assert dfs(rede, 10) == (10, 7, 4, -2, 9)
        assert len(componentes_conexas(rede)) == 3
        assert esta_conexa(rede) is False
        assert resumir_rede(rede) == ResumoEstrutural(8, 6, 1.5)

    assert rede.individuos == pessoas_antes
    assert rede.contatos == contatos_antes
    assert tuple(
        (p.id, p.estado, p.isolamento, p.dia_inicio_infeccao) for p in rede.individuos
    ) == estados_antes


@pytest.mark.parametrize("percurso", [bfs, dfs])
def test_percursos_suportam_caminho_maior_que_limite_de_recursao(
    percurso: Callable[[RedeContatos, int], tuple[int, ...]],
) -> None:
    tamanho = sys.getrecursionlimit() + 50
    rede = RedeContatos()
    for identificador in range(tamanho):
        rede.adicionar_individuo(Individuo(identificador))
    for origem in range(tamanho - 1):
        rede.adicionar_contato(origem, origem + 1)

    assert percurso(rede, 0) == tuple(range(tamanho))


@pytest.mark.parametrize("percurso", [bfs, dfs])
def test_percurso_rejeita_origem_ausente_inclusive_em_rede_vazia(
    rede: RedeContatos, percurso: Callable[[RedeContatos, int], tuple[int, ...]]
) -> None:
    with pytest.raises(KeyError, match="não está cadastrado"):
        percurso(rede, 111)
    with pytest.raises(KeyError, match="não está cadastrado"):
        percurso(RedeContatos(), 0)


@pytest.mark.parametrize("percurso", [bfs, dfs])
@pytest.mark.parametrize("origem", [True, False, 10.0, "10", None])
def test_percurso_reutiliza_validacao_de_id(
    rede: RedeContatos,
    percurso: Callable[[RedeContatos, int], tuple[int, ...]],
    origem: object,
) -> None:
    with pytest.raises(TypeError, match="identificador"):
        percurso(rede, origem)


@pytest.mark.parametrize("operacao", [bfs, dfs, componentes_conexas, esta_conexa, resumir_rede])
@pytest.mark.parametrize("valor", [None, {}, 3])
def test_analise_rejeita_objeto_que_nao_e_rede(
    operacao: Callable[..., object], valor: object
) -> None:
    argumentos = (valor, 0) if operacao in (bfs, dfs) else (valor,)
    with pytest.raises(TypeError, match="RedeContatos"):
        operacao(*argumentos)


def test_analise_integra_importacao_com_cadastro_de_pessoas_sem_contatos(
    tmp_path: Path,
) -> None:
    contatos = tmp_path / "contatos.csv"
    contatos.write_text("origem,destino,peso\n10,20,0\n20,30,0.5\n", encoding="utf-8")
    cadastro = tmp_path / "individuos.csv"
    cadastro.write_text("id\n10\n20\n30\n99\n", encoding="utf-8")
    rede = importar_rede_csv(contatos, arquivo_individuos=cadastro).rede

    assert componentes_conexas(rede) == (frozenset({10, 20, 30}), frozenset({99}))
    assert esta_conexa(rede) is False
    assert resumir_rede(rede) == ResumoEstrutural(4, 2, 1.0)


def test_analise_integra_os_dois_geradores() -> None:
    desconexa = gerar_erdos_renyi(4, 0, semente=0).rede
    conexa = gerar_barabasi_albert(10, 1, semente=0).rede

    assert componentes_conexas(desconexa) == tuple(frozenset({i}) for i in range(4))
    assert esta_conexa(desconexa) is False
    assert resumir_rede(desconexa) == ResumoEstrutural(4, 0, 0.0)
    assert esta_conexa(conexa) is True
    assert componentes_conexas(conexa) == (frozenset(range(10)),)
    assert resumir_rede(conexa) == ResumoEstrutural(10, 9, 1.8)


def test_copiar_rede_preserva_ordem_de_cadastro_e_percursos(rede: RedeContatos) -> None:
    copia = rede.copiar()

    assert [p.id for p in copia.individuos] == [p.id for p in rede.individuos]
    assert bfs(copia, 10) == bfs(rede, 10) == (10, 7, -2, 4, 9)
    assert dfs(copia, 10) == dfs(rede, 10) == (10, 7, 4, -2, 9)
    assert componentes_conexas(copia) == componentes_conexas(rede)
    assert resumir_rede(copia) == resumir_rede(rede)


def test_todos_os_grafos_simples_ate_cinco_pessoas_conferem_com_fecho_transitivo() -> None:
    identificadores = (-8, -1, 0, 6, 11)
    for n in range(6):
        pares = tuple(combinations(range(n), 2))
        for mascara in range(1 << len(pares)):
            rede = RedeContatos()
            for identificador in identificadores[:n]:
                rede.adicionar_individuo(Individuo(identificador))
            distancias = [[0 if i == j else float("inf") for j in range(n)] for i in range(n)]
            for posicao, (i, j) in enumerate(pares):
                if mascara & (1 << posicao):
                    rede.adicionar_contato(identificadores[i], identificadores[j])
                    distancias[i][j] = distancias[j][i] = 1
            # Oráculo independente: fecho transitivo/distâncias por Floyd–Warshall.
            for k in range(n):
                for i in range(n):
                    for j in range(n):
                        distancias[i][j] = min(
                            distancias[i][j], distancias[i][k] + distancias[k][j]
                        )
            componentes_esperadas = set()
            for i in range(n):
                alcancaveis = frozenset(
                    identificadores[j] for j in range(n) if distancias[i][j] < float("inf")
                )
                componentes_esperadas.add(alcancaveis)
                largura = bfs(rede, identificadores[i])
                profundidade = dfs(rede, identificadores[i])
                assert len(largura) == len(set(largura)) == len(alcancaveis)
                assert len(profundidade) == len(set(profundidade)) == len(alcancaveis)
                assert set(largura) == set(profundidade) == alcancaveis
                niveis = [distancias[i][identificadores.index(j)] for j in largura]
                assert niveis == sorted(niveis)
            assert set(componentes_conexas(rede)) == componentes_esperadas
            assert esta_conexa(rede) is (len(componentes_esperadas) == 1)
