"""Mutações validadas, identidade, simetria e preservação epidemiológica."""

from copy import deepcopy
from random import Random

import pytest

from simulador import EstadoSIR, Individuo, RedeContatos, bfs, resumir_rede


@pytest.fixture
def rede() -> RedeContatos:
    rede = RedeContatos()
    for identificador in (-1, 0, 2, 3, 4):
        rede.adicionar_individuo(Individuo(identificador))
    for origem, destino in ((2, 0), (0, -1), (2, 3)):
        rede.adicionar_contato(origem, destino, 0.8)
    return rede


def test_alterar_peso_preserva_objeto_ordem_atividade_e_contagens(
    rede: RedeContatos,
) -> None:
    contato = rede.obter_contato(2, 0)
    vizinhos = rede.vizinhos(0)
    rede.desativar_contato(0, 2)

    alterado = rede.alterar_peso_contato(0, 2, 0.3)

    assert alterado is contato is rede.obter_contato(2, 0)
    assert contato.peso == 0.3
    assert contato.ativa is False
    assert rede.vizinhos(0) == vizinhos
    assert rede.numero_contatos == 3
    assert rede.numero_individuos == 5


@pytest.mark.parametrize("peso", [-1, 1.1, float("nan"), float("inf"), 10**1000])
def test_peso_invalido_na_atualizacao_nao_modifica_contato(
    rede: RedeContatos, peso: float,
) -> None:
    contato = rede.obter_contato(0, 2)

    with pytest.raises(ValueError):
        rede.alterar_peso_contato(0, 2, peso)

    assert contato.peso == 0.8
    assert contato.ativa is True
    assert rede.numero_contatos == 3


@pytest.mark.parametrize("peso", [None, True, "0.2"])
def test_atualizacao_rejeita_peso_de_tipo_invalido(
    rede: RedeContatos, peso: object,
) -> None:
    with pytest.raises(TypeError):
        rede.alterar_peso_contato(0, 2, peso)
    assert rede.obter_contato(0, 2).peso == 0.8


def test_desativacao_e_idempotente_e_preserva_topologia(rede: RedeContatos) -> None:
    resumo = resumir_rede(rede)
    ordem = bfs(rede, 0)
    contato = rede.obter_contato(0, 2)

    assert rede.desativar_contato(2, 0) is contato
    assert rede.desativar_contato(0, 2) is contato

    assert contato.ativa is False
    assert contato.peso == 0.8
    assert resumir_rede(rede) == resumo
    assert bfs(rede, 0) == ordem
    assert not any(pessoa.isolamento for pessoa in rede.individuos)


@pytest.mark.parametrize("origem,destino", [(0, 2), (2, 0)])
def test_remocao_preserva_pessoas_e_retira_as_duas_direcoes(
    rede: RedeContatos, origem: int, destino: int,
) -> None:
    contato = rede.obter_contato(origem, destino)
    pessoas = rede.individuos

    assert rede.remover_contato(origem, destino) is contato

    assert rede.individuos == pessoas
    assert rede.numero_contatos == 2
    assert rede.vizinhos(0) == (rede.obter_individuo(-1),)
    assert rede.vizinhos(2) == (rede.obter_individuo(3),)
    assert sum(rede.grau(pessoa) for pessoa in pessoas) == 4
    for a, b in ((origem, destino), (destino, origem)):
        with pytest.raises(KeyError):
            rede.obter_contato(a, b)
    with pytest.raises(KeyError):
        rede.remover_contato(origem, destino)
    assert rede.numero_contatos == 2
    novo = rede.adicionar_contato(origem, destino, 0)
    assert novo is not contato
    assert rede.numero_contatos == 3


@pytest.mark.parametrize("estado", list(EstadoSIR))
def test_desconexao_preserva_cadastro_sir_isolamento_e_historico(
    rede: RedeContatos, estado: EstadoSIR,
) -> None:
    pessoa = rede.obter_individuo(2)
    if estado is not EstadoSIR.SUSCETIVEL:
        pessoa.infectar(5)
    if estado is EstadoSIR.RECUPERADO:
        pessoa.recuperar()
    pessoa.isolar()
    anteriores = rede.contatos_de(pessoa)

    removidos = rede.desconectar_individuo(2)

    assert frozenset(removidos) == anteriores
    assert rede.obter_individuo(2) is pessoa
    assert pessoa.estado is estado
    assert pessoa.isolamento is True
    assert pessoa.dia_inicio_infeccao == (None if estado is EstadoSIR.SUSCETIVEL else 5)
    assert rede.numero_individuos == 5
    assert rede.numero_contatos == 1
    assert rede.grau(pessoa) == 0
    assert rede.vizinhos(3) == ()
    assert rede.desconectar_individuo(2) == ()
    assert rede.desconectar_individuo(4) == ()
    if estado is EstadoSIR.INFECTADO:
        pessoa.recuperar()
        assert pessoa.estado is EstadoSIR.RECUPERADO
        assert pessoa.isolamento is True


@pytest.mark.parametrize(
    "operacao", ["alterar_peso_contato", "desativar_contato", "remover_contato"],
)
@pytest.mark.parametrize(
    "origem,destino,erro",
    [(0, 3, KeyError), (99, 0, KeyError), (0, 99, KeyError),
     (True, 0, TypeError), (0, "2", TypeError)],
)
def test_falhas_nas_operacoes_preservam_rede_inteira(
    rede: RedeContatos, operacao: str, origem: object, destino: object,
    erro: type[Exception],
) -> None:
    contatos = rede.contatos
    vizinhos = {pessoa.id: rede.vizinhos(pessoa.id) for pessoa in rede.individuos}
    argumentos = (origem, destino, 0.4) if operacao == "alterar_peso_contato" else (origem, destino)

    with pytest.raises(erro):
        getattr(rede, operacao)(*argumentos)

    assert rede.contatos == contatos
    assert rede.numero_contatos == 3
    assert all(contato.ativa and contato.peso == 0.8 for contato in contatos)
    assert {pessoa.id: rede.vizinhos(pessoa.id) for pessoa in rede.individuos} == vizinhos


@pytest.mark.parametrize("identificador,erro", [(99, KeyError), (True, TypeError)])
def test_desconexao_invalida_preserva_rede(
    rede: RedeContatos, identificador: object, erro: type[Exception],
) -> None:
    contatos = rede.contatos
    with pytest.raises(erro):
        rede.desconectar_individuo(identificador)
    assert rede.contatos == contatos
    assert rede.numero_contatos == 3


def test_copia_preserva_alteracoes_sem_compartilhar_contatos_mutaveis(
    rede: RedeContatos,
) -> None:
    original = rede.copiar()
    contato = rede.alterar_peso_contato(0, 2, 0.4)
    rede.desativar_contato(0, 2)
    rede.desconectar_individuo(3)

    pessoa_copiada, contato_copiado, copia = deepcopy(
        [rede.obter_individuo(2), contato, rede]
    )

    assert contato_copiado is copia.obter_contato(0, 2)
    assert contato_copiado.origem is pessoa_copiada
    assert contato_copiado.peso == 0.4
    assert contato_copiado.ativa is False
    assert copia.numero_contatos == 2
    assert copia.vizinhos(3) == ()
    copia.alterar_peso_contato(0, 2, 0)
    assert contato.peso == 0.4
    assert original.obter_contato(0, 2).peso == 0.8
    assert original.obter_contato(0, 2).ativa is True
    assert original.numero_contatos == 3


@pytest.mark.parametrize("semente", [0, 42, -17])
def test_sequencia_de_operacoes_concorda_com_modelo_de_pares(
    semente: int,
) -> None:
    sorteio = Random(semente)
    rede = RedeContatos()
    ids = (-5, 0, 1, 9, 20, 30)
    for identificador in ids:
        rede.adicionar_individuo(Individuo(identificador))
    pares: dict[tuple[int, int], tuple[float, bool]] = {}

    for _ in range(150):
        a, b = sorted(sorteio.sample(ids, 2))
        operacao = sorteio.choice(("conectar", "peso", "desativar", "remover", "desconectar"))
        if operacao == "desconectar":
            rede.desconectar_individuo(a)
            pares = {par: valor for par, valor in pares.items() if a not in par}
        elif (a, b) not in pares:
            rede.adicionar_contato(b, a, 0.8)
            pares[a, b] = (0.8, True)
        elif operacao == "peso":
            peso = sorteio.choice((0, 0.2, 1))
            rede.alterar_peso_contato(b, a, peso)
            pares[a, b] = (peso, pares[a, b][1])
        elif operacao == "desativar":
            rede.desativar_contato(b, a)
            pares[a, b] = (pares[a, b][0], False)
        elif operacao == "remover":
            rede.remover_contato(b, a)
            del pares[a, b]

        assert rede.numero_individuos == len(ids)
        assert rede.numero_contatos == len(rede.contatos) == len(pares)
        assert sum(rede.grau(pessoa) for pessoa in rede.individuos) == 2 * len(pares)
        for pessoa in rede.individuos:
            esperados = {outro for par in pares if pessoa.id in par for outro in par if outro != pessoa.id}
            assert {p.id for p in rede.vizinhos(pessoa.id)} == esperados
        for (a, b), (peso, ativa) in pares.items():
            contato = rede.obter_contato(a, b)
            assert rede.obter_contato(b, a) is contato
            assert contato.peso == peso
            assert contato.ativa is ativa
