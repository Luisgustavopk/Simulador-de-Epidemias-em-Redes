"""Importação de arquivos reais e diagnóstico de entradas inválidas."""

from pathlib import Path

import pytest

from simulador import ErroImportacaoRede, EstadoSIR, importar_rede_csv


@pytest.fixture
def contatos(tmp_path: Path) -> Path:
    arquivo = tmp_path / "contatos.csv"
    arquivo.write_text("origem,destino,peso\n1,2,0.5\n2,3,1\n3,1,0\n", encoding="utf-8")
    return arquivo


def test_importacao_cria_uma_pessoa_por_id_e_contatos_compartilhados(contatos: Path) -> None:
    resultado = importar_rede_csv(contatos)
    rede = resultado.rede

    assert resultado.arquivo_contatos == contatos
    assert resultado.arquivo_individuos is None
    assert rede.numero_individuos == 3
    assert rede.numero_contatos == 3
    assert {pessoa.id for pessoa in rede.individuos} == {1, 2, 3}
    assert rede.obter_contato(1, 2) is rede.obter_contato(2, 1)
    assert rede.obter_contato(1, 2).peso == 0.5
    assert rede.obter_contato(1, 3).peso == 0
    assert rede.obter_contato(1, 3).ativa is True
    assert rede.grau(rede.obter_individuo(2)) == 2
    assert all(pessoa.estado is EstadoSIR.SUSCETIVEL for pessoa in rede.individuos)
    assert all(not pessoa.isolamento for pessoa in rede.individuos)


@pytest.mark.parametrize("conteudo", ["origem,destino\n1,2\n", "origem,destino,peso\n1,2,\n"])
def test_peso_omitido_assume_um(tmp_path: Path, conteudo: str) -> None:
    arquivo = tmp_path / "sem_peso.csv"
    arquivo.write_text(conteudo, encoding="utf-8")

    rede = importar_rede_csv(arquivo).rede

    assert rede.obter_contato(1, 2).peso == 1


def test_cadastro_explicito_preserva_pessoas_sem_contatos(tmp_path: Path, contatos: Path) -> None:
    individuos = tmp_path / "individuos.csv"
    individuos.write_text("id\n1\n2\n3\n-7\n0\n", encoding="utf-8")

    resultado = importar_rede_csv(str(contatos), arquivo_individuos=str(individuos))

    assert resultado.arquivo_individuos == individuos
    assert resultado.rede.numero_individuos == 5
    assert resultado.rede.numero_contatos == 3
    assert resultado.rede.vizinhos(-7) == ()
    assert resultado.rede.grau(resultado.rede.obter_individuo(0)) == 0


def test_rede_sem_contatos_e_valida_quando_existe_cadastro_de_pessoas(tmp_path: Path) -> None:
    contatos = tmp_path / "contatos.csv"
    contatos.write_text("origem,destino,peso\n", encoding="utf-8")
    individuos = tmp_path / "individuos.csv"
    individuos.write_text("id\n1\n2\n", encoding="utf-8")

    rede = importar_rede_csv(contatos, arquivo_individuos=individuos).rede

    assert rede.numero_individuos == 2
    assert rede.numero_contatos == 0


def test_id_nao_cadastrado_indica_linha_campo_e_arquivo_de_origem(tmp_path: Path) -> None:
    contatos = tmp_path / "contatos.csv"
    contatos.write_text("origem,destino,peso\n10,20,0.5\n", encoding="utf-8")
    individuos = tmp_path / "individuos.csv"
    individuos.write_text("id\n1\n", encoding="utf-8")

    with pytest.raises(ErroImportacaoRede) as captura:
        importar_rede_csv(contatos, arquivo_individuos=individuos)

    problemas = captura.value.problemas
    assert [(problema.linha, problema.campo) for problema in problemas] == [
        (2, "origem"), (2, "destino")
    ]
    assert all(problema.arquivo == contatos for problema in problemas)
    assert all(str(individuos) in problema.mensagem for problema in problemas)


def test_ids_repetidos_no_cadastro_identificam_primeira_ocorrencia(tmp_path: Path) -> None:
    contatos = tmp_path / "contatos.csv"
    contatos.write_text("origem,destino\n", encoding="utf-8")
    individuos = tmp_path / "individuos.csv"
    individuos.write_text("id\n1\n+01\n", encoding="utf-8")

    with pytest.raises(ErroImportacaoRede) as captura:
        importar_rede_csv(contatos, arquivo_individuos=individuos)

    problema, = captura.value.problemas
    assert problema.arquivo == individuos
    assert problema.linha == 3
    assert problema.campo == "id"
    assert "linha 2" in problema.mensagem


def test_reune_erros_recuperaveis_sem_retornar_rede_parcial(tmp_path: Path) -> None:
    arquivo = tmp_path / "invalido.csv"
    arquivo.write_text(
        "origem,destino,peso\nx,2,0.5\n1,1,0.3\n1,2,nan\n3,,2\n1,2,0.3\n2,1,0.4\n",
        encoding="utf-8",
    )

    with pytest.raises(ErroImportacaoRede) as captura:
        importar_rede_csv(arquivo)

    problemas = captura.value.problemas
    assert [(problema.linha, problema.campo) for problema in problemas] == [
        (2, "origem"), (3, "origem/destino"), (4, "peso"),
        (5, "destino"), (5, "peso"), (7, "origem/destino"),
    ]
    assert "linha 6" in problemas[-1].mensagem
    assert "linha 2, campo 'origem'" in str(captura.value)
    assert str(arquivo) in str(captura.value)


@pytest.mark.parametrize("valor", ["-0.1", "1.1", "nan", "inf", "-inf", "True", "texto", "1e999"])
def test_pesos_invalidos_explicam_intervalo_e_separador_decimal(tmp_path: Path, valor: str) -> None:
    arquivo = tmp_path / "peso.csv"
    arquivo.write_text(f"origem,destino,peso\n1,2,{valor}\n", encoding="utf-8")

    with pytest.raises(ErroImportacaoRede) as captura:
        importar_rede_csv(arquivo)

    problema, = captura.value.problemas
    assert problema.linha == 2
    assert problema.campo == "peso"
    assert "entre 0 e 1" in problema.mensagem
    assert "ponto" in problema.mensagem


@pytest.mark.parametrize("valor", ["", "1.0", "True", "1e2", "1_000"])
def test_ids_exigem_representacao_decimal_inteira(tmp_path: Path, valor: str) -> None:
    arquivo = tmp_path / "id.csv"
    arquivo.write_text(f"origem,destino\n{valor},2\n", encoding="utf-8")

    with pytest.raises(ErroImportacaoRede) as captura:
        importar_rede_csv(arquivo)

    problema, = captura.value.problemas
    assert problema.linha == 2
    assert problema.campo == "origem"
    assert "inteiro" in problema.mensagem


@pytest.mark.parametrize(
    "conteudo",
    ["", "\n  \n", "origem,peso\n1,0.5\n", "origem,destino,peso,peso\n", "origem,destino,id\n"],
)
def test_cabecalho_invalido_e_localizado_no_arquivo(tmp_path: Path, conteudo: str) -> None:
    arquivo = tmp_path / "cabecalho.csv"
    arquivo.write_text(conteudo, encoding="utf-8")

    with pytest.raises(ErroImportacaoRede) as captura:
        importar_rede_csv(arquivo)

    problema, = captura.value.problemas
    assert problema.arquivo == arquivo
    assert problema.campo == "cabeçalho"


@pytest.mark.parametrize("registro", ["1,2", "1,2,0.5,extra"])
def test_quantidade_incorreta_de_colunas_nao_e_ignorada(tmp_path: Path, registro: str) -> None:
    arquivo = tmp_path / "colunas.csv"
    arquivo.write_text(f"origem,destino,peso\n{registro}\n", encoding="utf-8")

    with pytest.raises(ErroImportacaoRede) as captura:
        importar_rede_csv(arquivo)

    problema, = captura.value.problemas
    assert problema.linha == 2
    assert "Esperadas 3 colunas" in problema.mensagem


def test_peso_zero_ids_negativos_bom_e_crlf_sao_preservados(tmp_path: Path) -> None:
    arquivo = tmp_path / "planilha.csv"
    arquivo.write_bytes('\ufeff Origem , Destino , Peso \r\n "-2", 0, 0\r\n'.encode("utf-8"))

    rede = importar_rede_csv(arquivo).rede

    assert rede.obter_contato(-2, 0).peso == 0
    assert rede.numero_individuos == 2


def test_ordem_das_colunas_e_delimitador_explicito(tmp_path: Path) -> None:
    arquivo = tmp_path / "ponto_e_virgula.csv"
    arquivo.write_text("Peso;Destino;Origem\n0.25;2;1\n", encoding="utf-8")

    rede = importar_rede_csv(arquivo, delimitador=";").rede

    assert rede.obter_contato(1, 2).peso == 0.25


def test_linhas_em_branco_nao_deslocam_o_diagnostico(tmp_path: Path) -> None:
    arquivo = tmp_path / "linhas.csv"
    arquivo.write_text("\norigem,destino,peso\n\n1,x,0.5\n", encoding="utf-8")

    with pytest.raises(ErroImportacaoRede) as captura:
        importar_rede_csv(arquivo)

    problema, = captura.value.problemas
    assert problema.linha == 4


def test_registro_com_multiplas_linhas_informa_seu_inicio(tmp_path: Path) -> None:
    arquivo = tmp_path / "multilinha.csv"
    arquivo.write_text('origem,destino,peso\n"1\n2",3,1\n4,5,nan\n', encoding="utf-8")

    with pytest.raises(ErroImportacaoRede) as captura:
        importar_rede_csv(arquivo)

    assert [problema.linha for problema in captura.value.problemas] == [2, 4]


def test_aspas_nao_fechadas_informam_erro_csv(tmp_path: Path) -> None:
    arquivo = tmp_path / "aspas.csv"
    arquivo.write_text('origem,destino,peso\n1,2,"0.5\n', encoding="utf-8")

    with pytest.raises(ErroImportacaoRede) as captura:
        importar_rede_csv(arquivo)

    problema, = captura.value.problemas
    assert problema.linha == 2
    assert "CSV malformado" in problema.mensagem


@pytest.mark.parametrize("diretorio", [False, True])
def test_arquivo_ausente_ou_diretorio_gera_diagnostico_de_leitura(tmp_path: Path, diretorio: bool) -> None:
    arquivo = tmp_path if diretorio else tmp_path / "ausente.csv"

    with pytest.raises(ErroImportacaoRede) as captura:
        importar_rede_csv(arquivo)

    problema, = captura.value.problemas
    assert problema.arquivo == arquivo
    assert problema.linha is None
    assert "ler o arquivo" in problema.mensagem


def test_codificacao_invalida_informa_como_corrigir(tmp_path: Path) -> None:
    arquivo = tmp_path / "codificacao.csv"
    arquivo.write_bytes(b"origem,destino,peso\n\xff,2,1\n")

    with pytest.raises(ErroImportacaoRede) as captura:
        importar_rede_csv(arquivo)

    problema, = captura.value.problemas
    assert "UTF-8" in problema.mensagem


def test_cabecalho_sem_dados_nao_disponibiliza_rede_vazia(tmp_path: Path) -> None:
    arquivo = tmp_path / "vazio.csv"
    arquivo.write_text("origem,destino,peso\n", encoding="utf-8")

    with pytest.raises(ErroImportacaoRede, match="Nenhum indivíduo"):
        importar_rede_csv(arquivo)


def test_erros_no_cadastro_nao_impedem_diagnostico_dos_contatos(tmp_path: Path) -> None:
    individuos = tmp_path / "individuos.csv"
    individuos.write_text("id\nincorreto\n", encoding="utf-8")
    contatos = tmp_path / "contatos.csv"
    contatos.write_text("origem,destino,peso\n1,2,0.5\n3,4,nan\n", encoding="utf-8")

    with pytest.raises(ErroImportacaoRede) as captura:
        importar_rede_csv(contatos, arquivo_individuos=individuos)

    assert [(problema.arquivo, problema.campo) for problema in captura.value.problemas] == [
        (individuos, "id"), (contatos, "peso")
    ]


@pytest.mark.parametrize("delimitador", ["", "::", "\n", '"'])
def test_delimitador_invalido_e_rejeitado(contatos: Path, delimitador: str) -> None:
    with pytest.raises(ValueError, match="delimitador"):
        importar_rede_csv(contatos, delimitador=delimitador)


@pytest.mark.parametrize("delimitador", [None, 1, False])
def test_delimitador_exige_string(contatos: Path, delimitador: object) -> None:
    with pytest.raises(TypeError, match="string"):
        importar_rede_csv(contatos, delimitador=delimitador)


def test_importacoes_sao_independentes_e_falha_nao_altera_rede_anterior(contatos: Path) -> None:
    primeira = importar_rede_csv(contatos).rede
    segunda = importar_rede_csv(contatos).rede
    primeira.obter_individuo(1).infectar(0)
    contatos.write_text("origem,destino,peso\n4,5,1\n5,6,nan\n", encoding="utf-8")

    with pytest.raises(ErroImportacaoRede):
        importar_rede_csv(contatos)

    assert primeira.numero_individuos == segunda.numero_individuos == 3
    assert primeira.numero_contatos == segunda.numero_contatos == 3
    assert primeira.obter_individuo(1).estado is EstadoSIR.INFECTADO
    assert segunda.obter_individuo(1).estado is EstadoSIR.SUSCETIVEL
    assert primeira.buscar_individuo(4) is None


def test_arquivos_de_exemplo_preservam_pessoa_sem_contatos() -> None:
    exemplos = Path(__file__).resolve().parents[1] / "exemplos" / "redes"

    rede = importar_rede_csv(
        exemplos / "contatos.csv", arquivo_individuos=exemplos / "individuos.csv"
    ).rede

    assert rede.numero_individuos == 4
    assert rede.numero_contatos == 3
    assert rede.vizinhos(4) == ()
