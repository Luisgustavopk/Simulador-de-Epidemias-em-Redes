"""Invariantes de uma rede simples, ponderada e não direcionada."""

import pytest

from simulador import Grafo, Individuo


@pytest.fixture
def grafo() -> Grafo:
    rede = Grafo()
    for identificador in (-2, 0, 7, 11):
        rede.adicionar_individuo(Individuo(identificador))
    return rede


def test_grafo_vazio_possui_contagens_e_colecoes_vazias() -> None:
    grafo = Grafo()

    assert grafo.numero_individuos == 0
    assert grafo.numero_arestas == 0
    assert grafo.individuos == ()
    assert grafo.arestas == ()


@pytest.mark.parametrize("identificador", [0, -3, 8])
def test_cadastro_preserva_individuo_e_aceita_identificadores_inteiros(
    identificador: int,
) -> None:
    grafo = Grafo()
    individuo = Individuo(identificador)

    grafo.adicionar_individuo(individuo)

    assert grafo.obter_individuo(identificador) is individuo
    assert grafo.individuos == (individuo,)
    assert grafo.vizinhos(identificador) == ()
    assert grafo.numero_individuos == 1


@pytest.mark.parametrize("mesma_instancia", [True, False])
def test_identificador_duplicado_nao_substitui_individuo_cadastrado(
    mesma_instancia: bool,
) -> None:
    grafo = Grafo()
    original = Individuo(1)
    grafo.adicionar_individuo(original)
    duplicado = original if mesma_instancia else Individuo(1)

    with pytest.raises(ValueError):
        grafo.adicionar_individuo(duplicado)

    assert grafo.obter_individuo(1) is original
    assert grafo.numero_individuos == 1
    assert grafo.numero_arestas == 0


@pytest.mark.parametrize("individuo", [None, 1])
def test_cadastro_rejeita_objeto_que_nao_e_individuo(individuo: object) -> None:
    grafo = Grafo()

    with pytest.raises(TypeError):
        grafo.adicionar_individuo(individuo)

    assert grafo.numero_individuos == 0
    assert grafo.individuos == ()


@pytest.mark.parametrize("consulta", ["obter_individuo", "vizinhos"])
def test_consultas_rejeitam_identificador_ausente(
    grafo: Grafo, consulta: str
) -> None:
    with pytest.raises(KeyError):
        getattr(grafo, consulta)(999)


@pytest.mark.parametrize("consulta", ["obter_individuo", "vizinhos"])
@pytest.mark.parametrize("identificador", [True, "0"])
def test_consultas_rejeitam_identificador_de_tipo_invalido(
    grafo: Grafo, consulta: str, identificador: object
) -> None:
    with pytest.raises(TypeError):
        getattr(grafo, consulta)(identificador)


def test_contato_compartilha_aresta_e_individuos_nos_dois_sentidos(
    grafo: Grafo,
) -> None:
    origem = grafo.obter_individuo(-2)
    destino = grafo.obter_individuo(0)

    aresta = grafo.adicionar_aresta(-2, 0, peso=2.4, ativa=False)

    assert aresta.origem is origem
    assert aresta.destino is destino
    assert aresta.peso == 2.4
    assert aresta.ativa is False
    assert grafo.obter_aresta(-2, 0) is aresta
    assert grafo.obter_aresta(0, -2) is aresta
    assert grafo.vizinhos(-2) == (destino,)
    assert grafo.vizinhos(0) == (origem,)
    assert grafo.arestas == (aresta,)
    assert grafo.numero_arestas == 1


def test_rede_desconexa_conta_cada_aresta_uma_vez(grafo: Grafo) -> None:
    primeira = grafo.adicionar_aresta(-2, 0)
    segunda = grafo.adicionar_aresta(0, 7)

    assert grafo.numero_individuos == 4
    assert grafo.numero_arestas == 2
    assert set(grafo.arestas) == {primeira, segunda}
    assert len(grafo.arestas) == 2
    assert {vizinho.id for vizinho in grafo.vizinhos(0)} == {-2, 7}
    assert {vizinho.id for vizinho in grafo.vizinhos(7)} == {0}
    assert grafo.vizinhos(11) == ()


@pytest.mark.parametrize("origem,destino", [(-2, 0), (0, -2)])
def test_contato_duplicado_ou_invertido_nao_altera_aresta_existente(
    grafo: Grafo, origem: int, destino: int
) -> None:
    original = grafo.adicionar_aresta(-2, 0, peso=0.5)

    with pytest.raises(ValueError):
        grafo.adicionar_aresta(origem, destino, peso=9)

    assert grafo.obter_aresta(origem, destino) is original
    assert original.peso == 0.5
    assert grafo.numero_arestas == 1
    assert grafo.arestas == (original,)


@pytest.mark.parametrize(
    "origem,destino,peso,ativa,erro",
    [
        pytest.param(999, 0, 1.0, True, KeyError, id="origem-ausente"),
        pytest.param(0, 999, 1.0, True, KeyError, id="destino-ausente"),
        pytest.param(0, 0, 1.0, True, ValueError, id="laco"),
        pytest.param(0, 7, -1.0, True, ValueError, id="peso-invalido"),
        pytest.param(0, 7, "1", True, TypeError, id="peso-textual"),
        pytest.param(0, 7, 1.0, 1, TypeError, id="ativa-nao-booleana"),
        pytest.param(True, 7, 1.0, True, TypeError, id="origem-booleana"),
        pytest.param(0, True, 1.0, True, TypeError, id="destino-booleano"),
    ],
)
def test_falha_ao_adicionar_aresta_preserva_toda_a_rede(
    grafo: Grafo,
    origem: object,
    destino: object,
    peso: object,
    ativa: object,
    erro: type[Exception],
) -> None:
    original = grafo.adicionar_aresta(-2, 0)

    with pytest.raises(erro):
        grafo.adicionar_aresta(origem, destino, peso=peso, ativa=ativa)

    assert grafo.numero_individuos == 4
    assert grafo.numero_arestas == 1
    assert grafo.arestas == (original,)
    assert {vizinho.id for vizinho in grafo.vizinhos(0)} == {-2}
    assert grafo.vizinhos(7) == ()


@pytest.mark.parametrize("origem,destino", [(0, 7), (999, 0), (0, 999)])
def test_consulta_de_aresta_ausente_levanta_erro(
    grafo: Grafo, origem: int, destino: int
) -> None:
    with pytest.raises(KeyError):
        grafo.obter_aresta(origem, destino)


@pytest.mark.parametrize("origem,destino", [(True, 0), (0, True), (0, "7")])
def test_consulta_de_aresta_rejeita_tipos_invalidos(
    grafo: Grafo, origem: object, destino: object
) -> None:
    with pytest.raises(TypeError):
        grafo.obter_aresta(origem, destino)


def test_alteracoes_epidemiologicas_preservam_a_topologia(grafo: Grafo) -> None:
    aresta = grafo.adicionar_aresta(-2, 0)
    individuo = grafo.obter_individuo(0)

    individuo.infectar(3)
    individuo.isolar()
    aresta.ativa = False

    vizinho = grafo.vizinhos(-2)[0]
    assert vizinho is individuo
    assert vizinho.estado == "I"
    assert vizinho.dia_inicio_infeccao == 3
    assert vizinho.isolamento is True
    assert grafo.obter_aresta(0, -2) is aresta
    assert grafo.obter_aresta(0, -2).ativa is False
    assert grafo.numero_arestas == 1


def test_colecoes_retornadas_sao_retratos_da_topologia(grafo: Grafo) -> None:
    primeira = grafo.adicionar_aresta(-2, 0)
    individuos_antes = grafo.individuos
    arestas_antes = grafo.arestas
    vizinhos_antes = grafo.vizinhos(0)
    novo = Individuo(40)

    grafo.adicionar_individuo(novo)
    grafo.adicionar_aresta(0, 40)

    assert len(individuos_antes) == 4
    assert all(individuo is not novo for individuo in individuos_antes)
    assert arestas_antes == (primeira,)
    assert {vizinho.id for vizinho in vizinhos_antes} == {-2}
    assert grafo.numero_individuos == 5
    assert grafo.numero_arestas == 2
    assert {vizinho.id for vizinho in grafo.vizinhos(0)} == {-2, 40}
