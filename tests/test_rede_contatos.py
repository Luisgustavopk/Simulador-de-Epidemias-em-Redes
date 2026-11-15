"""Cadastro canônico de pessoas e contatos compartilhados na rede."""

import pytest

from simulador import EstadoSIR, Individuo, RedeContatos


@pytest.fixture
def rede() -> RedeContatos:
    rede = RedeContatos()
    for identificador in (-2, 0, 7, 11):
        rede.adicionar_individuo(Individuo(identificador))
    return rede


def test_rede_vazia_possui_contagens_e_colecoes_vazias() -> None:
    rede = RedeContatos()

    assert rede.numero_individuos == 0
    assert rede.numero_contatos == 0
    assert rede.individuos == ()
    assert rede.contatos == ()
    assert rede.buscar_individuo(1) is None


@pytest.mark.parametrize("identificador", [0, -3, 8])
def test_cadastro_preserva_individuo_e_aceita_identificadores_inteiros(
    identificador: int,
) -> None:
    rede = RedeContatos()
    individuo = Individuo(identificador)

    rede.adicionar_individuo(individuo)

    assert rede.obter_individuo(identificador) is individuo
    assert rede.buscar_individuo(identificador) is individuo
    assert rede.individuos == (individuo,)
    assert rede.vizinhos(identificador) == ()
    assert rede.contatos_de(individuo) == frozenset()
    assert rede.grau(individuo) == 0
    assert rede.numero_individuos == 1


@pytest.mark.parametrize("mesma_instancia", [True, False])
def test_identificador_duplicado_nao_substitui_individuo_cadastrado(
    mesma_instancia: bool,
) -> None:
    rede = RedeContatos()
    original = Individuo(1)
    rede.adicionar_individuo(original)
    duplicado = original if mesma_instancia else Individuo(1)

    with pytest.raises(ValueError):
        rede.adicionar_individuo(duplicado)

    assert rede.obter_individuo(1) is original
    assert rede.numero_individuos == 1
    assert rede.numero_contatos == 0


@pytest.mark.parametrize("individuo", [None, 1])
def test_cadastro_rejeita_objeto_que_nao_e_individuo(individuo: object) -> None:
    rede = RedeContatos()

    with pytest.raises(TypeError):
        rede.adicionar_individuo(individuo)

    assert rede.numero_individuos == 0
    assert rede.individuos == ()


@pytest.mark.parametrize("consulta", ["obter_individuo", "vizinhos"])
def test_consultas_obrigatorias_rejeitam_identificador_ausente(
    rede: RedeContatos, consulta: str
) -> None:
    with pytest.raises(KeyError):
        getattr(rede, consulta)(999)

    assert rede.buscar_individuo(999) is None


@pytest.mark.parametrize("consulta", ["obter_individuo", "buscar_individuo", "vizinhos"])
@pytest.mark.parametrize("identificador", [True, "0"])
def test_consultas_rejeitam_identificador_de_tipo_invalido(
    rede: RedeContatos, consulta: str, identificador: object
) -> None:
    with pytest.raises(TypeError):
        getattr(rede, consulta)(identificador)


def test_conectar_compartilha_contato_e_instancias_cadastradas(rede: RedeContatos) -> None:
    origem = rede.obter_individuo(-2)
    destino = rede.obter_individuo(0)

    contato = rede.conectar(origem, destino, peso=0.4)

    assert contato.origem is origem
    assert contato.destino is destino
    assert contato.peso == 0.4
    assert rede.obter_contato(-2, 0) is contato
    assert rede.obter_contato(0, -2) is contato
    assert rede.contatos_de(origem) == frozenset({contato})
    assert rede.contatos_de(destino) == frozenset({contato})
    assert rede.vizinhos(-2) == (destino,)
    assert rede.vizinhos(0) == (origem,)
    assert rede.contatos == (contato,)
    assert rede.numero_contatos == 1


def test_rede_desconexa_conta_cada_contato_uma_vez(rede: RedeContatos) -> None:
    primeira = rede.adicionar_contato(-2, 0)
    segunda = rede.adicionar_contato(0, 7)
    central = rede.obter_individuo(0)
    solitario = rede.obter_individuo(11)

    assert rede.numero_individuos == 4
    assert rede.numero_contatos == 2
    assert set(rede.contatos) == {primeira, segunda}
    assert len(rede.contatos) == 2
    assert rede.contatos_de(central) == frozenset({primeira, segunda})
    assert rede.grau(central) == 2
    assert {vizinho.id for vizinho in rede.vizinhos(0)} == {-2, 7}
    assert rede.contatos_de(solitario) == frozenset()
    assert rede.grau(solitario) == 0


@pytest.mark.parametrize("origem,destino", [(-2, 0), (0, -2)])
def test_contato_duplicado_ou_invertido_nao_altera_rede(
    rede: RedeContatos, origem: int, destino: int
) -> None:
    original = rede.adicionar_contato(-2, 0, peso=0.5)

    with pytest.raises(ValueError):
        rede.conectar(
            rede.obter_individuo(origem), rede.obter_individuo(destino), peso=0.9
        )

    assert rede.obter_contato(origem, destino) is original
    assert original.peso == 0.5
    assert rede.numero_contatos == 1
    assert rede.contatos == (original,)


@pytest.mark.parametrize(
    "origem,destino,peso,erro",
    [
        pytest.param(999, 0, 1.0, KeyError, id="origem-ausente"),
        pytest.param(0, 999, 1.0, KeyError, id="destino-ausente"),
        pytest.param(0, 0, 1.0, ValueError, id="laco"),
        pytest.param(0, 7, -1.0, ValueError, id="peso-negativo"),
        pytest.param(0, 7, 1.1, ValueError, id="peso-acima-do-limite"),
        pytest.param(0, 7, "1", TypeError, id="peso-textual"),
        pytest.param(True, 7, 1.0, TypeError, id="origem-booleana"),
        pytest.param(0, True, 1.0, TypeError, id="destino-booleano"),
    ],
)
def test_falha_ao_adicionar_contato_preserva_toda_a_rede(
    rede: RedeContatos,
    origem: object,
    destino: object,
    peso: object,
    erro: type[Exception],
) -> None:
    original = rede.adicionar_contato(-2, 0)

    with pytest.raises(erro):
        rede.adicionar_contato(origem, destino, peso=peso)

    assert rede.numero_individuos == 4
    assert rede.numero_contatos == 1
    assert rede.contatos == (original,)
    assert {vizinho.id for vizinho in rede.vizinhos(0)} == {-2}
    assert rede.vizinhos(7) == ()


@pytest.mark.parametrize("id_desconhecido", [0, 99])
@pytest.mark.parametrize("lado", [0, 1])
def test_conectar_rejeita_objeto_nao_cadastrado_mesmo_com_id_existente(
    rede: RedeContatos, id_desconhecido: int, lado: int
) -> None:
    argumentos = [rede.obter_individuo(-2), rede.obter_individuo(7)]
    argumentos[lado] = Individuo(id_desconhecido)

    with pytest.raises(KeyError):
        rede.conectar(*argumentos)

    assert rede.numero_contatos == 0
    assert rede.contatos == ()


@pytest.mark.parametrize("consulta", ["contatos_de", "grau"])
@pytest.mark.parametrize("identificador", [0, 99])
def test_consultas_estruturais_exigem_a_instancia_cadastrada(
    rede: RedeContatos, consulta: str, identificador: int
) -> None:
    with pytest.raises(KeyError):
        getattr(rede, consulta)(Individuo(identificador))


@pytest.mark.parametrize("consulta", ["contatos_de", "grau"])
@pytest.mark.parametrize("pessoa", [None, 0])
def test_consultas_estruturais_exigem_individuo(
    rede: RedeContatos, consulta: str, pessoa: object
) -> None:
    with pytest.raises(TypeError):
        getattr(rede, consulta)(pessoa)


@pytest.mark.parametrize("lado", [0, 1])
def test_conectar_rejeita_argumento_que_nao_e_individuo(
    rede: RedeContatos, lado: int
) -> None:
    argumentos = [rede.obter_individuo(-2), rede.obter_individuo(7)]
    argumentos[lado] = None

    with pytest.raises(TypeError):
        rede.conectar(*argumentos)

    assert rede.numero_contatos == 0


@pytest.mark.parametrize("origem,destino", [(0, 7), (999, 0), (0, 999)])
def test_consulta_de_contato_ausente_levanta_erro(
    rede: RedeContatos, origem: int, destino: int
) -> None:
    with pytest.raises(KeyError):
        rede.obter_contato(origem, destino)


@pytest.mark.parametrize("origem,destino", [(True, 0), (0, True), (0, "7")])
def test_consulta_de_contato_rejeita_tipos_invalidos(
    rede: RedeContatos, origem: object, destino: object
) -> None:
    with pytest.raises(TypeError):
        rede.obter_contato(origem, destino)


def test_isolamento_e_recuperacao_preservam_topologia_e_grau(rede: RedeContatos) -> None:
    contato = rede.adicionar_contato(-2, 0)
    individuo = rede.obter_individuo(0)
    grau_original = rede.grau(individuo)

    individuo.infectar(3)
    individuo.isolar()
    individuo.recuperar()

    assert rede.vizinhos(-2)[0] is individuo
    assert individuo.estado is EstadoSIR.RECUPERADO
    assert contato.ativa is True  # Marcar a pessoa não escolhe um mecanismo.
    assert rede.contatos_de(individuo) == frozenset({contato})
    assert rede.grau(individuo) == grau_original
    assert rede.numero_contatos == 1


def test_colecoes_retornadas_nao_mudam_com_novos_cadastros(rede: RedeContatos) -> None:
    primeira = rede.adicionar_contato(-2, 0)
    central = rede.obter_individuo(0)
    individuos_antes = rede.individuos
    contatos_da_rede_antes = rede.contatos
    vizinhos_antes = rede.vizinhos(0)
    contatos_do_individuo_antes = rede.contatos_de(central)
    novo = Individuo(40)

    rede.adicionar_individuo(novo)
    rede.conectar(central, novo)

    assert len(individuos_antes) == 4
    assert all(individuo is not novo for individuo in individuos_antes)
    assert contatos_da_rede_antes == (primeira,)
    assert {vizinho.id for vizinho in vizinhos_antes} == {-2}
    assert contatos_do_individuo_antes == frozenset({primeira})
    assert rede.numero_individuos == 5
    assert rede.numero_contatos == 2
    assert {vizinho.id for vizinho in rede.vizinhos(0)} == {-2, 40}


def test_iteradores_preservam_ordem_e_identidade_sem_expor_colecoes_mutaveis(
    rede: RedeContatos,
) -> None:
    rede.adicionar_contato(7, 0, peso=0)
    rede.adicionar_contato(0, -2)

    assert tuple(rede.iter_individuos()) == rede.individuos
    assert tuple(rede.iter_contatos()) == rede.contatos
    assert tuple(rede.iter_vizinhos(0)) == rede.vizinhos(0)
    assert tuple(rede.iter_vizinhos(11)) == ()
    assert tuple(rede.iter_ids_vizinhos(0)) == (7, -2)
    assert tuple(rede.iter_ids_vizinhos(11)) == ()


@pytest.mark.parametrize("consulta", ["iter_vizinhos", "iter_ids_vizinhos"])
@pytest.mark.parametrize("identificador,erro", [(True, TypeError), ("0", TypeError), (999, KeyError)])
def test_iterador_de_vizinhos_valida_origem_antes_de_ser_consumido(
    rede: RedeContatos, consulta: str, identificador: object, erro: type[Exception]
) -> None:
    with pytest.raises(erro):
        getattr(rede, consulta)(identificador)


def test_copia_de_rede_vazia_e_independente() -> None:
    original = RedeContatos()

    copia = original.copiar()
    copia.adicionar_individuo(Individuo(1))

    assert copia is not original
    assert original.numero_individuos == original.numero_contatos == 0
    assert copia.numero_individuos == 1


def test_copia_preserva_estados_e_compartilha_contato_apenas_entre_extremos_copiados(
    rede: RedeContatos,
) -> None:
    rede.adicionar_contato(7, 0, peso=0)
    rede.adicionar_contato(-2, 0, peso=0.7)
    rede.obter_individuo(-2).infectar(3)
    rede.obter_individuo(-2).isolar()
    rede.obter_individuo(-2).recuperar()
    rede.obter_individuo(0).infectar(5)

    copia = rede.copiar()
    outra = rede.copiar()

    assert copia.numero_individuos == rede.numero_individuos
    assert copia.numero_contatos == rede.numero_contatos
    for pessoa in rede.individuos:
        pessoa_copiada = copia.obter_individuo(pessoa.id)
        assert pessoa_copiada is not pessoa
        assert pessoa_copiada is not outra.obter_individuo(pessoa.id)
        assert pessoa_copiada.estado is pessoa.estado
        assert pessoa_copiada.isolamento is pessoa.isolamento
        assert pessoa_copiada.dia_inicio_infeccao == pessoa.dia_inicio_infeccao
        assert [v.id for v in copia.vizinhos(pessoa.id)] == [v.id for v in rede.vizinhos(pessoa.id)]
    for contato in rede.contatos:
        origem, destino = contato.origem.id, contato.destino.id
        copiado = copia.obter_contato(origem, destino)
        assert copiado is copia.obter_contato(destino, origem)
        assert copiado is not contato
        assert copiado is not outra.obter_contato(origem, destino)
        assert copiado.origem is copia.obter_individuo(origem)
        assert copiado.destino is copia.obter_individuo(destino)
        assert copiado.peso == contato.peso
        assert copiado.ativa == contato.ativa

    copia.obter_individuo(7).infectar(9)
    copia.obter_individuo(0).recuperar()
    copia.adicionar_individuo(Individuo(50))
    copia.adicionar_contato(50, 11)

    assert rede.obter_individuo(7).estado is EstadoSIR.SUSCETIVEL
    assert outra.obter_individuo(7).estado is EstadoSIR.SUSCETIVEL
    assert rede.obter_individuo(0).estado is EstadoSIR.INFECTADO
    assert rede.buscar_individuo(50) is None
    assert outra.buscar_individuo(50) is None
    assert rede.numero_contatos == outra.numero_contatos == 2
