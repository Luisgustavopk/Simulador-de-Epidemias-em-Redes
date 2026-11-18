"""Mecanismos distintos, orçamento em pessoas e população preservada."""

from collections import Counter
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from simulador import (
    EstadoSIR, Individuo, MecanismoIsolamento, RedeContatos,
    aplicar_isolamento, bfs, componentes_conexas, gerar_barabasi_albert,
    gerar_erdos_renyi, importar_rede_csv, resumir_rede,
)


@pytest.fixture
def rede() -> RedeContatos:
    rede = RedeContatos()
    for identificador in range(5):
        rede.adicionar_individuo(Individuo(identificador))
    for origem, destino in ((0, 1), (1, 2), (2, 3)):
        rede.adicionar_contato(origem, destino, 0.8)
    rede.obter_individuo(1).infectar(0)
    rede.obter_individuo(2).infectar(0)
    rede.obter_individuo(2).recuperar()
    return rede


@pytest.mark.parametrize("mecanismo", list(MecanismoIsolamento))
def test_mecanismos_aceitam_s_i_r_e_preservam_coorte(
    rede: RedeContatos, mecanismo: MecanismoIsolamento,
) -> None:
    copia = rede.copiar()
    pessoas = rede.individuos
    estados = tuple(pessoa.estado for pessoa in pessoas)
    kwargs = {"reducao": 0.5} if mecanismo is MecanismoIsolamento.REDUCAO else {}

    resultado = aplicar_isolamento(rede, (0, 1, 2), mecanismo, orcamento=3, **kwargs)

    assert resultado.ids_selecionados == (0, 1, 2)
    assert resultado.mecanismo is mecanismo
    assert resultado.numero_contatos_afetados == 3
    assert resultado.orcamento == 3  # Três pessoas, independentemente das arestas.
    assert resultado.reducao == kwargs.get("reducao")
    assert rede.individuos == pessoas
    assert tuple(pessoa.estado for pessoa in pessoas) == estados
    assert sum(Counter(pessoa.estado for pessoa in pessoas).values()) == 5
    assert [pessoa.id for pessoa in pessoas if pessoa.isolamento] == [0, 1, 2]
    assert rede.obter_individuo(2).dia_inicio_infeccao == 0
    assert not any(pessoa.isolamento for pessoa in copia.individuos)
    assert all(contato.ativa and contato.peso == 0.8 for contato in copia.contatos)
    if mecanismo is MecanismoIsolamento.DESATIVACAO:
        assert all(not contato.ativa for contato in rede.contatos)
        assert all(contato.peso == 0.8 for contato in rede.contatos)
        assert resumir_rede(rede) == resumir_rede(copia)
    elif mecanismo is MecanismoIsolamento.REDUCAO:
        assert all(contato.ativa for contato in rede.contatos)
        assert all(contato.peso == 0.4 for contato in rede.contatos)
        assert resumir_rede(rede) == resumir_rede(copia)
    else:
        assert rede.numero_contatos == 0
        assert rede.numero_individuos == 5
        assert len(componentes_conexas(rede)) == 5
    with pytest.raises(FrozenInstanceError):
        resultado.orcamento = 5


@pytest.mark.parametrize("mecanismo", list(MecanismoIsolamento))
def test_recuperacao_preserva_restricao_sem_reposicao_de_alvos(
    rede: RedeContatos, mecanismo: MecanismoIsolamento,
) -> None:
    kwargs = {"reducao": 0.5} if mecanismo is MecanismoIsolamento.REDUCAO else {}
    aplicar_isolamento(rede, [1], mecanismo, orcamento=1, **kwargs)
    contatos = tuple((c, c.peso, c.ativa) for c in rede.contatos)

    rede.obter_individuo(1).recuperar()

    assert rede.obter_individuo(1).estado is EstadoSIR.RECUPERADO
    assert rede.obter_individuo(1).isolamento is True
    assert [pessoa.id for pessoa in rede.individuos if pessoa.isolamento] == [1]
    assert tuple((c, c.peso, c.ativa) for c in rede.contatos) == contatos
    assert rede.numero_individuos == 5


@pytest.mark.parametrize("reducao,peso", [(0, 0.8), (0.5, 0.4), (1, 0)])
def test_reducao_ocorre_uma_vez_com_dois_extremos_selecionados(
    rede: RedeContatos, reducao: float, peso: float,
) -> None:
    rede.desativar_contato(2, 3)  # Uma restrição prévia de contato não é reativada.

    aplicar_isolamento(
        rede, [1, 2], MecanismoIsolamento.REDUCAO, orcamento=2, reducao=reducao,
    )

    assert rede.obter_contato(1, 2).peso == pytest.approx(peso)
    assert rede.obter_contato(0, 1).peso == pytest.approx(peso)
    assert rede.obter_contato(2, 3).peso == pytest.approx(peso)
    assert rede.obter_contato(1, 2).ativa is True
    assert rede.obter_contato(2, 3).ativa is False
    assert bfs(rede, 0) == (0, 1, 2, 3)


@pytest.mark.parametrize("mecanismo", list(MecanismoIsolamento))
@pytest.mark.parametrize("ids,orcamento", [((), 0), ((), 5), ((4,), 1)])
def test_selecao_vazia_ou_sem_contatos_nao_altera_ligacoes(
    rede: RedeContatos, mecanismo: MecanismoIsolamento, ids: tuple[int, ...],
    orcamento: int,
) -> None:
    contatos = rede.contatos
    kwargs = {"reducao": 0.5} if mecanismo is MecanismoIsolamento.REDUCAO else {}

    resultado = aplicar_isolamento(rede, ids, mecanismo, orcamento=orcamento, **kwargs)

    assert resultado.numero_contatos_afetados == 0
    assert resultado.ids_selecionados == ids
    assert rede.contatos == contatos
    assert all(contato.ativa and contato.peso == 0.8 for contato in contatos)
    assert [pessoa.id for pessoa in rede.individuos if pessoa.isolamento] == list(ids)


def test_orcamento_e_limite_de_pessoas_e_nao_de_contatos(rede: RedeContatos) -> None:
    resultado = aplicar_isolamento(
        rede, iter([1]), MecanismoIsolamento.EXCLUSAO, orcamento=1,
    )
    assert resultado.numero_contatos_afetados == 2
    assert rede.numero_contatos == 1
    assert rede.obter_contato(2, 3).ativa is True
    assert rede.grau(rede.obter_individuo(1)) == 0


@pytest.mark.parametrize(
    "ids,mecanismo,orcamento,reducao,erro",
    [
        ([1, 1], MecanismoIsolamento.DESATIVACAO, 2, None, ValueError),
        ([1, 99], MecanismoIsolamento.DESATIVACAO, 2, None, KeyError),
        ([1, True], MecanismoIsolamento.DESATIVACAO, 2, None, TypeError),
        ([1, "2"], MecanismoIsolamento.DESATIVACAO, 2, None, TypeError),
        ([1], MecanismoIsolamento.DESATIVACAO, 0, None, ValueError),
        ([], MecanismoIsolamento.DESATIVACAO, -1, None, ValueError),
        ([], MecanismoIsolamento.DESATIVACAO, 6, None, ValueError),
        ([], MecanismoIsolamento.DESATIVACAO, True, None, TypeError),
        ([], MecanismoIsolamento.DESATIVACAO, 1.5, None, TypeError),
        ([1], "reducao", 1, 0.5, TypeError),
        ([1], MecanismoIsolamento.REDUCAO, 1, None, TypeError),
        ([1], MecanismoIsolamento.REDUCAO, 1, True, TypeError),
        ([1], MecanismoIsolamento.REDUCAO, 1, "0.5", TypeError),
        ([1], MecanismoIsolamento.REDUCAO, 1, -0.1, ValueError),
        ([1], MecanismoIsolamento.REDUCAO, 1, 1.1, ValueError),
        ([1], MecanismoIsolamento.REDUCAO, 1, float("nan"), ValueError),
        ([1], MecanismoIsolamento.REDUCAO, 1, float("inf"), ValueError),
        ([1], MecanismoIsolamento.REDUCAO, 1, 10**1000, ValueError),
        ([1], MecanismoIsolamento.EXCLUSAO, 1, 0.5, ValueError),
        (None, MecanismoIsolamento.EXCLUSAO, 1, None, TypeError),
    ],
)
def test_validacao_completa_ocorre_antes_de_qualquer_mutacao(
    rede: RedeContatos, ids: object, mecanismo: object, orcamento: object,
    reducao: object, erro: type[Exception],
) -> None:
    pessoas = rede.individuos
    contatos = rede.contatos
    estados = tuple(pessoa.estado for pessoa in pessoas)

    with pytest.raises(erro):
        aplicar_isolamento(rede, ids, mecanismo, orcamento=orcamento, reducao=reducao)

    assert rede.individuos == pessoas
    assert tuple(pessoa.estado for pessoa in pessoas) == estados
    assert not any(pessoa.isolamento for pessoa in pessoas)
    assert rede.contatos == contatos
    assert rede.numero_contatos == 3
    assert all(contato.ativa and contato.peso == 0.8 for contato in contatos)


@pytest.mark.parametrize("segunda_selecao", [[1], [3]])
def test_reaplicacao_ou_mistura_de_intervencoes_nao_acumula_reducao(
    rede: RedeContatos, segunda_selecao: list[int],
) -> None:
    aplicar_isolamento(
        rede, [1], MecanismoIsolamento.REDUCAO, orcamento=1, reducao=0.5,
    )
    with pytest.raises(ValueError, match="sem isolamento prévio"):
        aplicar_isolamento(
            rede, segunda_selecao, MecanismoIsolamento.REDUCAO,
            orcamento=1, reducao=0.5,
        )
    assert rede.obter_contato(0, 1).peso == 0.4
    assert rede.obter_contato(2, 3).peso == 0.8
    assert not rede.obter_individuo(3).isolamento


def test_isolamento_rejeita_objeto_que_nao_e_rede() -> None:
    with pytest.raises(TypeError, match="RedeContatos"):
        aplicar_isolamento(None, [], MecanismoIsolamento.EXCLUSAO, orcamento=0)


@pytest.mark.parametrize("modelo", ["er", "ba"])
@pytest.mark.parametrize("mecanismo", list(MecanismoIsolamento))
def test_copiar_resultado_preserva_intervencao_e_recriar_restaura_origem(
    modelo: str, mecanismo: MecanismoIsolamento,
) -> None:
    resultado = (
        gerar_erdos_renyi(6, 1, peso=0.8, semente=42)
        if modelo == "er"
        else gerar_barabasi_albert(6, 2, peso=0.8, semente=42)
    )
    kwargs = {"reducao": 0.5} if mecanismo is MecanismoIsolamento.REDUCAO else {}
    aplicar_isolamento(resultado.rede, [1], mecanismo, orcamento=1, **kwargs)

    copia = resultado.copiar()
    recriada = resultado.recriar()

    assert copia.rede.obter_individuo(1).isolamento is True
    assert recriada.rede.obter_individuo(1).isolamento is False
    assert all(c.peso == 0.8 and c.ativa for c in recriada.rede.contatos)
    assert copia.rede.numero_contatos == resultado.rede.numero_contatos
    for contato in resultado.rede.contatos:
        copiado = copia.rede.obter_contato(contato.origem.id, contato.destino.id)
        assert copiado is not contato
        assert (copiado.peso, copiado.ativa) == (contato.peso, contato.ativa)


def test_csv_preserva_pessoa_sem_contatos_apos_exclusao(tmp_path: Path) -> None:
    contatos = tmp_path / "contatos.csv"
    cadastro = tmp_path / "individuos.csv"
    contatos.write_text("origem,destino,peso\n1,2,0.8\n", encoding="utf-8")
    cadastro.write_text("id\n1\n2\n3\n", encoding="utf-8")
    rede = importar_rede_csv(contatos, arquivo_individuos=cadastro).rede
    rede.obter_individuo(1).infectar(0)

    aplicar_isolamento(rede, [1], MecanismoIsolamento.EXCLUSAO, orcamento=1)

    assert rede.numero_individuos == 3
    assert rede.numero_contatos == 0
    assert len(componentes_conexas(rede)) == 3
    assert rede.obter_individuo(1).estado is EstadoSIR.INFECTADO
