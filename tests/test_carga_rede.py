"""Contrato da futura tela e entrega de referências independentes para B/C."""

from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import pytest

import simulador.carga_rede as modulo_carga
from simulador import (
    ArquivoCSV,
    ErroCargaRede,
    EstadoSIR,
    ServicoCargaRede,
)


@pytest.fixture
def servico() -> ServicoCargaRede:
    return ServicoCargaRede()


def parametros_er(**alteracoes: object) -> dict[str, object]:
    return {
        "modelo": "erdos_renyi", "numero_individuos": "4",
        "probabilidade_contato": "1", "peso": "0,5", "semente": "42",
        **alteracoes,
    }


def test_estado_inicial_nao_disponibiliza_rede_para_etapas_seguintes(
    servico: ServicoCargaRede,
) -> None:
    estado = servico.inspecionar()
    assert estado["disponivel"] is estado["confirmada"] is False
    assert estado["resumo"] is estado["origem"] is None
    assert estado["revisao"] == 0
    for operacao in (servico.confirmar, servico.obter_rede_confirmada,
                     servico.listar_individuos, servico.listar_contatos):
        with pytest.raises(ErroCargaRede, match="rede válida"):
            operacao(0)


def test_geracao_reune_resumo_origem_e_reproducao_com_semente(
    servico: ServicoCargaRede,
) -> None:
    resultado = servico.gerar(parametros_er())
    resumo = resultado["resumo"]
    assert resultado["disponivel"] is True
    assert resultado["confirmada"] is False
    assert resultado["revisao"] == 1
    assert resumo == {
        "numero_individuos": 4, "numero_contatos": 6, "grau_medio": 3,
        "grau_maximo": 3, "numero_componentes": 1, "conexa": True,
        "individuos_sem_contatos": 0,
        "distribuicao_graus": [{"grau": 3, "quantidade": 4}],
    }
    assert resultado["origem"]["semente"] == "42"
    assert resultado["origem"]["parametros"]["peso"] == 0.5
    outro = ServicoCargaRede().gerar(parametros_er())
    assert resultado == outro
    assert json.loads(json.dumps(resultado, allow_nan=False)) == resultado


def test_barabasi_albert_usa_contrato_do_gerador_existente(
    servico: ServicoCargaRede,
) -> None:
    estado = servico.gerar({
        "modelo": "barabasi_albert", "numero_individuos": 10,
        "contatos_por_novo_individuo": "2", "semente": "-17",
    })
    assert estado["resumo"]["conexa"] is True
    assert estado["resumo"]["numero_contatos"] == 17
    assert estado["origem"]["detalhes_modelo"] == {"tamanho_nucleo_inicial": 3}
    assert estado["origem"]["parametros"]["peso"] == 1


def test_rede_desconexa_e_rede_unitaria_sao_validas_para_carga(
    servico: ServicoCargaRede,
) -> None:
    estado = servico.gerar(parametros_er(probabilidade_contato=0))
    assert estado["resumo"]["conexa"] is False
    assert estado["resumo"]["numero_componentes"] == 4
    assert estado["resumo"]["individuos_sem_contatos"] == 4
    assert estado["resumo"]["grau_medio"] == 0
    estado = servico.gerar(parametros_er(numero_individuos=1))
    assert estado["resumo"]["conexa"] is True
    assert estado["resumo"]["grau_maximo"] == 0


def test_validacao_retencao_dos_campos_e_erros_estruturados(
    servico: ServicoCargaRede,
) -> None:
    campos = parametros_er(numero_individuos="", probabilidade_contato="nan", semente="3.5")
    with pytest.raises(ErroCargaRede) as capturado:
        servico.gerar(campos)
    assert {p.campo for p in capturado.value.problemas} == {
        "numero_individuos", "probabilidade_contato", "semente",
    }
    assert campos["numero_individuos"] == ""
    assert servico.inspecionar()["disponivel"] is False
    assert json.loads(json.dumps(capturado.value.para_dict())) == capturado.value.para_dict()


@pytest.mark.parametrize(
    "campo,valor",
    [
        ("numero_individuos", 0), ("numero_individuos", -1),
        ("numero_individuos", True), ("numero_individuos", 2.5),
        ("numero_individuos", "１"), ("semente", None),
        ("peso", ""), ("peso", True), ("peso", 10**1000),
        ("peso", float("inf")), ("peso", -0.1), ("peso", 1.1),
        ("probabilidade_contato", None), ("probabilidade_contato", "0,1.2"),
        ("modelo", "watts_strogatz"), ("modelo", None),
        ("contatos_por_novo_individuo", 1), ("desconhecido", 1),
    ],
)
def test_campos_invalidos_nao_substituem_rede_confirmada(
    servico: ServicoCargaRede, campo: str, valor: object,
) -> None:
    servico.gerar(parametros_er())
    anterior = servico.confirmar(1)
    with pytest.raises(ErroCargaRede) as capturado:
        servico.gerar(parametros_er(**{campo: valor}))
    assert campo in {p.campo for p in capturado.value.problemas}
    assert servico.inspecionar() == anterior
    assert servico.obter_rede_confirmada(1).rede.numero_contatos == 6


@pytest.mark.parametrize("m", [0, 4, True, "2.5", ""])
def test_barabasi_rejeita_m_invalido(servico: ServicoCargaRede, m: object) -> None:
    with pytest.raises(ErroCargaRede) as capturado:
        servico.gerar({
            "modelo": "barabasi_albert", "numero_individuos": 4,
            "contatos_por_novo_individuo": m, "semente": 42,
        })
    assert "contatos_por_novo_individuo" in {p.campo for p in capturado.value.problemas}


@pytest.mark.parametrize("entrada", [None, [], "er"])
def test_geracao_exige_mapa_de_campos(servico: ServicoCargaRede, entrada: object) -> None:
    with pytest.raises(ErroCargaRede):
        servico.gerar(entrada)


def test_confirmacao_e_copias_independentes_para_b_e_c(
    servico: ServicoCargaRede,
) -> None:
    servico.gerar(parametros_er())
    with pytest.raises(ErroCargaRede, match="Confirme"):
        servico.obter_rede_confirmada(1)
    confirmado = servico.confirmar(1)
    assert servico.confirmar(1) == confirmado
    b = servico.obter_rede_confirmada(1)
    c = servico.obter_rede_confirmada(1)
    b.rede.obter_individuo(0).infectar(0)
    b.rede.desconectar_individuo(0)
    b.origem["parametros"]["peso"] = 0
    assert c.rede.obter_individuo(0).estado is EstadoSIR.SUSCETIVEL
    assert c.rede.numero_contatos == 6
    assert servico.inspecionar() == confirmado
    assert servico.inspecionar_individuo(1, 0)["estado"] == "S"


def test_nova_rede_invalida_confirmacao_e_revisoes_antigas(
    servico: ServicoCargaRede,
) -> None:
    servico.gerar(parametros_er())
    servico.confirmar(1)
    nova = servico.gerar(parametros_er(numero_individuos=2))
    assert nova["revisao"] == 2
    assert nova["confirmada"] is False
    for operacao in (servico.confirmar, servico.obter_rede_confirmada,
                     servico.listar_individuos, servico.listar_contatos):
        with pytest.raises(ErroCargaRede, match="alterada"):
            operacao(1)
    with pytest.raises(ErroCargaRede):
        servico.inspecionar_individuo(1, 0)
    assert servico.confirmar(2)["confirmada"] is True


@pytest.mark.parametrize("revisao", [True, "1", 0, 1.0])
def test_revisao_exige_inteiro_exato(servico: ServicoCargaRede, revisao: object) -> None:
    servico.gerar(parametros_er())
    with pytest.raises(ErroCargaRede):
        servico.confirmar(revisao)


def test_retorno_serializado_nao_permite_modificar_referencia(
    servico: ServicoCargaRede,
) -> None:
    retorno = servico.gerar(parametros_er())
    retorno["resumo"]["distribuicao_graus"].clear()
    retorno["origem"]["parametros"]["peso"] = 0
    assert servico.inspecionar()["resumo"]["distribuicao_graus"] == [{"grau": 3, "quantidade": 4}]
    assert servico.inspecionar()["origem"]["parametros"]["peso"] == 0.5


def test_csv_com_cadastro_preserva_isolados_e_nomes_sem_caminhos_temporarios(
    servico: ServicoCargaRede,
) -> None:
    arquivo = ArquivoCSV("../../contatos.csv", b"origem;destino;peso\n10;20;0.5\n")
    estado = servico.importar_csv(
        arquivo, arquivo_individuos=ArquivoCSV(r"C:\pasta\pessoas.csv", b"id\n10\n20\n30\n"),
        delimitador=";",
    )
    assert estado["resumo"]["numero_individuos"] == 3
    assert estado["resumo"]["numero_contatos"] == 1
    assert estado["resumo"]["numero_componentes"] == 2
    assert estado["origem"]["arquivo_contatos"] == "contatos.csv"
    assert estado["origem"]["arquivo_individuos"] == "pessoas.csv"
    assert estado["origem"]["sha256_contatos"] == sha256(arquivo.conteudo).hexdigest()
    assert "simulador-rede-" not in json.dumps(estado)


def test_erro_csv_preserva_linha_coluna_e_rede_anterior(
    servico: ServicoCargaRede,
) -> None:
    anterior = servico.gerar(parametros_er())
    with pytest.raises(ErroCargaRede) as capturado:
        servico.importar_csv(ArquivoCSV("dados.csv", b"origem,destino,peso\n1,2,nan\n"))
    problema = capturado.value.problemas[0]
    assert (problema.campo, problema.arquivo, problema.linha, problema.coluna) == (
        "arquivo_contatos", "dados.csv", 2, "peso",
    )
    assert servico.inspecionar() == anterior
    assert "simulador-rede-" not in json.dumps(capturado.value.para_dict())


def test_erro_no_cadastro_e_reportado_no_campo_correto(servico: ServicoCargaRede) -> None:
    with pytest.raises(ErroCargaRede) as capturado:
        servico.importar_csv(
            ArquivoCSV("contatos.csv", b"origem,destino\n1,2\n"),
            arquivo_individuos=ArquivoCSV("pessoas.csv", b"id\n1\n1\n"),
        )
    assert capturado.value.problemas[0].campo == "arquivo_individuos"
    assert capturado.value.problemas[0].arquivo == "pessoas.csv"


def test_id_fora_do_cadastro_nao_expoe_caminho_temporario_na_mensagem(
    servico: ServicoCargaRede,
) -> None:
    with pytest.raises(ErroCargaRede) as capturado:
        servico.importar_csv(
            ArquivoCSV("contatos.csv", b"origem,destino\n1,2\n"),
            arquivo_individuos=ArquivoCSV("pessoas.csv", b"id\n1\n"),
        )
    mensagem = capturado.value.problemas[0].mensagem
    assert "pessoas.csv" in mensagem
    assert "simulador-rede-" not in mensagem
    assert capturado.value.problemas[0].coluna == "destino"


@pytest.mark.parametrize("conteudo", [b"origem,destino\n", b"\xff", b""])
def test_csv_sem_populacao_ou_mal_codificado_nao_fica_disponivel(
    servico: ServicoCargaRede, conteudo: bytes,
) -> None:
    with pytest.raises(ErroCargaRede):
        servico.importar_csv(ArquivoCSV("dados.csv", conteudo))
    assert not servico.inspecionar()["disponivel"]


@pytest.mark.parametrize("delimitador", [None, "", "::", "\n", '"'])
def test_separador_invalido_tem_erro_de_formulario(
    servico: ServicoCargaRede, delimitador: object,
) -> None:
    with pytest.raises(ErroCargaRede) as capturado:
        servico.importar_csv(ArquivoCSV("dados.csv", b""), delimitador=delimitador)
    assert capturado.value.problemas[0].campo == "delimitador"


def test_campos_de_upload_exigem_arquivo_csv(servico: ServicoCargaRede) -> None:
    with pytest.raises(ErroCargaRede):
        servico.importar_csv(None)
    with pytest.raises(ErroCargaRede):
        servico.importar_csv(ArquivoCSV("dados.csv", b""), arquivo_individuos="pessoas.csv")


@pytest.mark.parametrize("nome", ["", "  ", "..", "\0", "/"])
def test_nome_do_arquivo_precisa_ser_valido(nome: str) -> None:
    with pytest.raises(ValueError):
        ArquivoCSV(nome, b"")


def test_arquivo_exige_nome_textual_e_conteudo_bytes() -> None:
    with pytest.raises(TypeError):
        ArquivoCSV(None, b"")
    with pytest.raises(TypeError):
        ArquivoCSV("dados.csv", "origem,destino")


def test_inspecao_paginada_por_grau_e_ids_grandes_sem_perda_no_json(
    servico: ServicoCargaRede,
) -> None:
    grande = 2**64 + 1
    servico.importar_csv(ArquivoCSV("dados.csv", f"origem,destino\n{grande},0\n0,-1\n".encode()))
    pagina = servico.listar_individuos(1, limite=2)
    assert pagina["individuos"] == [{"id": "0", "grau": 2}, {"id": "-1", "grau": 1}]
    assert servico.listar_individuos(1, inicio=2)["individuos"] == [{"id": str(grande), "grau": 1}]
    assert servico.listar_individuos(1, inicio=3)["individuos"] == []
    no = servico.inspecionar_individuo(1, str(grande))
    assert no["id"] == str(grande)
    assert no["grau"] == 1
    assert no["estado"] == "S"
    assert no["isolamento"] is False
    assert json.loads(json.dumps(no)) == no


@pytest.mark.parametrize("inicio,limite", [(-1, 1), (0, 0), (0, 501), (True, 1), (0, "1")])
def test_paginacao_invalida_tem_diagnostico(
    servico: ServicoCargaRede, inicio: object, limite: object,
) -> None:
    servico.gerar(parametros_er())
    for operacao in (servico.listar_individuos, servico.listar_contatos):
        with pytest.raises(ErroCargaRede):
            operacao(1, inicio=inicio, limite=limite)


@pytest.mark.parametrize("identificador", ["999", "nan", True])
def test_inspecao_rejeita_id_invalido(
    servico: ServicoCargaRede, identificador: object,
) -> None:
    servico.gerar(parametros_er())
    with pytest.raises(ErroCargaRede):
        servico.inspecionar_individuo(1, identificador)


def test_semente_grande_e_preservada_como_texto_para_frontend(
    servico: ServicoCargaRede,
) -> None:
    semente = 2**128 + 1
    estado = servico.gerar(parametros_er(semente=str(semente)))
    assert json.loads(json.dumps(estado))["origem"]["semente"] == str(semente)


def test_contatos_paginados_preservam_extremos_pesos_e_unicidade(
    servico: ServicoCargaRede,
) -> None:
    servico.gerar(parametros_er())
    contatos = []
    for inicio in (0, 2, 4):
        pagina = servico.listar_contatos(1, inicio=inicio, limite=2)
        assert pagina["total"] == 6
        assert pagina["revisao"] == 1
        contatos.extend(pagina["contatos"])
    pares = {frozenset((c["origem"], c["destino"])) for c in contatos}
    assert len(pares) == len(contatos) == 6
    assert all(c["peso"] == 0.5 and c["ativa"] for c in contatos)
    assert all(isinstance(c["origem"], str) for c in contatos)
    assert servico.listar_contatos(1, inicio=6)["contatos"] == []
    contatos[0]["peso"] = 0
    assert servico.listar_contatos(1)["contatos"][0]["peso"] == 0.5
    assert json.loads(json.dumps(contatos)) == contatos


def test_listagem_de_contatos_vazia_em_rede_sem_ligacoes(
    servico: ServicoCargaRede,
) -> None:
    servico.gerar(parametros_er(probabilidade_contato=0))
    assert servico.listar_contatos(1) == {
        "revisao": 1, "total": 0, "inicio": 0, "contatos": [],
    }


@pytest.mark.parametrize("falha_na_saida", [False, True])
def test_falha_da_pasta_temporaria_nao_publica_rede_parcial(
    servico: ServicoCargaRede, monkeypatch: pytest.MonkeyPatch,
    falha_na_saida: bool,
) -> None:
    anterior = servico.gerar(parametros_er())

    @contextmanager
    def pasta_com_falha(**kwargs):
        if not falha_na_saida:
            raise OSError("Sem espaço disponível")
        with TemporaryDirectory(**kwargs) as pasta:
            yield pasta
        raise OSError("Falha ao concluir a limpeza")

    monkeypatch.setattr(modulo_carga, "TemporaryDirectory", pasta_com_falha)
    with pytest.raises(ErroCargaRede) as capturado:
        servico.importar_csv(ArquivoCSV("dados.csv", b"origem,destino\n1,2\n"))
    assert capturado.value.problemas[0].campo == "arquivos"
    assert servico.inspecionar() == anterior


@pytest.mark.parametrize("valido", [False, True])
def test_temporarios_sao_removidos_apos_sucesso_ou_erro_csv(
    servico: ServicoCargaRede, monkeypatch: pytest.MonkeyPatch, valido: bool,
) -> None:
    pastas: list[Path] = []

    @contextmanager
    def registrar_pasta(**kwargs):
        with TemporaryDirectory(**kwargs) as pasta:
            pastas.append(Path(pasta))
            yield pasta

    monkeypatch.setattr(modulo_carga, "TemporaryDirectory", registrar_pasta)
    arquivo = ArquivoCSV("dados.csv", b"origem,destino\n1,2\n" if valido else b"invalido\n")
    if valido:
        servico.importar_csv(arquivo)
    else:
        with pytest.raises(ErroCargaRede):
            servico.importar_csv(arquivo)
    assert len(pastas) == 1
    assert not pastas[0].exists()


def test_inteiro_textual_acima_do_limite_do_python_tem_diagnostico(
    servico: ServicoCargaRede,
) -> None:
    limite = sys.get_int_max_str_digits() if hasattr(sys, "get_int_max_str_digits") else 0
    if limite == 0:
        pytest.skip("O ambiente não limita a conversão de inteiros textuais.")
    with pytest.raises(ErroCargaRede) as capturado:
        servico.gerar(parametros_er(semente="1" * (limite + 1)))
    assert capturado.value.problemas[0].campo == "semente"
