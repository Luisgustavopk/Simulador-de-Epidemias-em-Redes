"""Contrato de carga e inspeção para uma futura interface, sem framework web.

O serviço mantém uma referência privada da rede. A interface recebe dados
serializáveis; B e C recebem cópias independentes após a confirmação explícita.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path, PureWindowsPath
import re
from tempfile import TemporaryDirectory
from threading import RLock
from typing import NoReturn

from simulador.analise_estrutural import componentes_conexas, resumir_rede
from simulador.contato import Contato
from simulador.geracao import gerar_barabasi_albert, gerar_erdos_renyi
from simulador.importacao import ErroImportacaoRede, importar_rede_csv
from simulador.rede_contatos import RedeContatos


@dataclass(frozen=True, slots=True)
class ArquivoCSV:
    """Arquivo recebido da interface; nome é apenas identificação para exibição.

    O conteúdo deve ser bytes UTF-8, como o importador exige. O nome original
    nunca determina o caminho temporário usado para processar o arquivo.
    """

    nome: str
    conteudo: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.nome, str):
            raise TypeError("O nome do arquivo deve ser texto.")
        if not self.nome.strip() or "\0" in self.nome:
            raise ValueError("Informe um nome de arquivo válido.")
        if not isinstance(self.conteudo, bytes):
            raise TypeError("O conteúdo do arquivo deve ser bytes.")
        nome = PureWindowsPath(self.nome).name
        if nome in ("", ".", ".."):
            raise ValueError("Informe um nome de arquivo válido.")
        object.__setattr__(self, "nome", nome)


@dataclass(frozen=True, slots=True)
class ProblemaCargaRede:
    """Erro vinculado ao campo do formulário e, em CSV, à posição do dado."""

    campo: str
    mensagem: str
    arquivo: str | None = None
    linha: int | None = None
    coluna: str | None = None


class ErroCargaRede(ValueError):
    """Problemas de entrada, sem substituir a última rede válida."""

    def __init__(self, problemas: tuple[ProblemaCargaRede, ...]) -> None:
        self.problemas = problemas
        super().__init__("\n".join(p.mensagem for p in problemas))

    def para_dict(self) -> dict[str, object]:
        """Retorna dados independentes para erros inline e resumo do formulário."""
        return {"problemas": [asdict(problema) for problema in self.problemas]}


@dataclass(frozen=True, slots=True)
class RedeDisponivel:
    """Cópia de trabalho para B/C, identificada pela revisão da rede confirmada.

    A rede e os metadados desta entrega podem ser usados pelo consumidor sem
    alterar a referência privada do serviço ou entregas a outros consumidores.
    """

    rede: RedeContatos
    revisao: int
    origem: dict[str, object]


def _falhar(campo: str, mensagem: str) -> NoReturn:
    raise ErroCargaRede((ProblemaCargaRede(campo, mensagem),))


def _inteiro(valor: object, campo: str) -> int:
    if isinstance(valor, int) and not isinstance(valor, bool):
        try:
            str(valor)
        except ValueError:
            _falhar(campo, "O inteiro excede o limite de representação do ambiente.")
        return valor
    if isinstance(valor, str) and re.fullmatch(r"[+-]?[0-9]+", valor.strip()):
        try:
            return int(valor)
        except ValueError:
            pass
    _falhar(campo, "Informe um número inteiro válido.")


def _fracao(valor: object, campo: str) -> float:
    if isinstance(valor, bool) or not isinstance(valor, (str, int, float)):
        _falhar(campo, "Informe um número finito entre 0 e 1.")
    try:
        numero = float(valor.replace(",", ".") if isinstance(valor, str) else valor)
    except (ValueError, OverflowError):
        _falhar(campo, "Informe um número finito entre 0 e 1.")
    if not 0 <= numero <= 1:
        _falhar(campo, "Informe um número finito entre 0 e 1.")
    return numero


def _validar_paginacao(inicio: int, limite: int) -> None:
    for campo, valor in (("inicio", inicio), ("limite", limite)):
        if isinstance(valor, bool) or not isinstance(valor, int):
            _falhar(campo, "Informe um inteiro para a paginação.")
    if inicio < 0 or not 1 <= limite <= 500:
        _falhar("paginacao", "Use início não negativo e limite entre 1 e 500.")


def _parametros_geracao(campos: Mapping[str, object]) -> dict[str, object]:
    """Converte campos da futura tela e reúne os erros antes da geração."""
    if not isinstance(campos, Mapping):
        _falhar("formulario", "Informe os parâmetros como um mapa de campos.")
    problemas: list[ProblemaCargaRede] = []
    modelo = campos.get("modelo")
    if modelo not in ("erdos_renyi", "barabasi_albert"):
        problemas.append(ProblemaCargaRede("modelo", "Escolha Erdős–Rényi ou Barabási–Albert."))
    permitidos = {"modelo", "numero_individuos", "semente", "peso"}
    if modelo == "erdos_renyi":
        permitidos.add("probabilidade_contato")
    elif modelo == "barabasi_albert":
        permitidos.add("contatos_por_novo_individuo")
    for campo in campos:
        if campo not in permitidos:
            problemas.append(ProblemaCargaRede(str(campo), "Este campo não se aplica ao modelo selecionado."))
    valores: dict[str, object] = {"modelo": modelo}
    inteiros = ["numero_individuos", "semente"]
    if modelo == "barabasi_albert":
        inteiros.append("contatos_por_novo_individuo")
    for campo in inteiros:
        try:
            valores[campo] = _inteiro(campos.get(campo), campo)
        except ErroCargaRede as erro:
            problemas.extend(erro.problemas)
    for campo in ("peso", "probabilidade_contato"):
        if campo == "probabilidade_contato" and modelo != "erdos_renyi":
            continue
        try:
            valores[campo] = _fracao(campos.get(campo, 1) if campo == "peso" else campos.get(campo), campo)
        except ErroCargaRede as erro:
            problemas.extend(erro.problemas)
    n = valores.get("numero_individuos")
    m = valores.get("contatos_por_novo_individuo")
    if isinstance(n, int) and n <= 0:
        problemas.append(ProblemaCargaRede("numero_individuos", "O número de indivíduos deve ser positivo."))
    if isinstance(m, int) and (m < 1 or isinstance(n, int) and m >= n):
        problemas.append(ProblemaCargaRede("contatos_por_novo_individuo", "Use m inteiro com 1 ≤ m < número de indivíduos."))
    if problemas:
        raise ErroCargaRede(tuple(problemas))
    return valores


class ServicoCargaRede:
    """Estado da etapa de carga, com publicação atômica e confirmação por revisão.

    Use uma instância por sessão de trabalho, compartilhada com os adaptadores
    de B e C. Não é um singleton global nem uma camada de persistência. As
    operações são síncronas e serializadas; o adaptador gráfico decide como
    executar trabalho demorado sem bloquear sua interface.
    """

    def __init__(self) -> None:
        self._rede: RedeContatos | None = None
        self._contatos: tuple[Contato, ...] = ()
        self._origem: dict[str, object] | None = None
        self._resumo: dict[str, object] | None = None
        self._ordenacao: tuple[int, ...] = ()
        self._revisao = 0
        self._confirmada = False
        self._lock = RLock()

    def gerar(self, campos: Mapping[str, object]) -> dict[str, object]:
        """Gera ER/BA com parâmetros de formulário, preservando a origem e a semente.

        Aceita inteiros textuais e frações com ponto ou vírgula decimal. Campos
        desconhecidos ou de outro modelo são recusados. Uma falha preserva a
        rede anterior e sua confirmação; uma nova rede exige nova confirmação.
        """
        with self._lock:
            parametros = _parametros_geracao(campos)
            modelo = parametros.pop("modelo")
            gerador = gerar_erdos_renyi if modelo == "erdos_renyi" else gerar_barabasi_albert
            resultado = gerador(**parametros)
            origem = {"tipo": "sintetica", **resultado.exportar_metadados()}
            # JS não representa todo inteiro Python sem perda de precisão.
            origem["semente"] = str(resultado.semente)
            return self._publicar(resultado.rede, origem)

    def importar_csv(
        self, arquivo_contatos: ArquivoCSV,
        *, arquivo_individuos: ArquivoCSV | None = None,
        delimitador: str = ",",
    ) -> dict[str, object]:
        """Recebe arquivos enviados pela interface e reutiliza o importador nativo.

        Os temporários são apagados inclusive em caso de erro. Os diagnósticos
        mostram nomes enviados, linha e coluna, sem expor caminhos temporários.
        O cadastro opcional preserva pessoas sem contatos.
        """
        if not isinstance(arquivo_contatos, ArquivoCSV):
            _falhar("arquivo_contatos", "Escolha um arquivo CSV de contatos.")
        if arquivo_individuos is not None and not isinstance(arquivo_individuos, ArquivoCSV):
            _falhar("arquivo_individuos", "Escolha um arquivo CSV de indivíduos válido.")
        if not isinstance(delimitador, str) or len(delimitador) != 1 or delimitador in '\r\n"':
            _falhar("delimitador", "Use um separador de um caractere, diferente de aspas e quebras de linha.")
        with self._lock:
            try:
                with TemporaryDirectory(prefix="simulador-rede-") as pasta:
                    contatos = Path(pasta) / "contatos.csv"
                    individuos = Path(pasta) / "individuos.csv" if arquivo_individuos else None
                    enviados = {contatos: ("arquivo_contatos", arquivo_contatos.nome)}
                    contatos.write_bytes(arquivo_contatos.conteudo)
                    if individuos is not None:
                        individuos.write_bytes(arquivo_individuos.conteudo)
                        enviados[individuos] = ("arquivo_individuos", arquivo_individuos.nome)
                    try:
                        resultado = importar_rede_csv(
                            contatos, arquivo_individuos=individuos, delimitador=delimitador,
                        )
                    except ErroImportacaoRede as erro:
                        problemas = []
                        for problema in erro.problemas:
                            campo, nome = enviados[problema.arquivo]
                            mensagem = problema.mensagem
                            for caminho, (_, nome_enviado) in enviados.items():
                                mensagem = mensagem.replace(str(caminho), nome_enviado)
                            problemas.append(ProblemaCargaRede(
                                campo=campo, mensagem=mensagem, arquivo=nome,
                                linha=problema.linha, coluna=problema.campo,
                            ))
                        raise ErroCargaRede(tuple(problemas)) from erro
            except OSError:
                _falhar("arquivos", "Não foi possível preparar os arquivos. Verifique o espaço e as permissões da pasta temporária.")
            origem = {
                "tipo": "observada",
                "arquivo_contatos": arquivo_contatos.nome,
                "arquivo_individuos": arquivo_individuos.nome if arquivo_individuos else None,
                "delimitador": delimitador,
                "sha256_contatos": sha256(arquivo_contatos.conteudo).hexdigest(),
                "sha256_individuos": sha256(arquivo_individuos.conteudo).hexdigest() if arquivo_individuos else None,
            }
            # Só publicar depois de concluir a leitura e remover os temporários.
            return self._publicar(resultado.rede, origem)

    def _publicar(self, rede: RedeContatos, origem: dict[str, object]) -> dict[str, object]:
        resumo = asdict(resumir_rede(rede))
        graus = {pessoa.id: rede.grau(pessoa) for pessoa in rede.iter_individuos()}
        distribuicao = Counter(graus.values())
        componentes = componentes_conexas(rede)
        resumo.update(
            numero_componentes=len(componentes),
            conexa=len(componentes) == 1,
            grau_maximo=max(graus.values(), default=0),
            individuos_sem_contatos=distribuicao.get(0, 0),
            distribuicao_graus=[{"grau": grau, "quantidade": quantidade} for grau, quantidade in sorted(distribuicao.items())],
        )
        ordenacao = tuple(sorted(graus, key=lambda identificador: (-graus[identificador], identificador)))
        # A referência fica privada e estável até a próxima carga. Guardar apenas
        # referências evita percorrer todas as páginas anteriores em cada consulta.
        contatos = rede.contatos
        # Publicar somente depois de finalizar todas as análises da candidata.
        self._rede, self._origem, self._resumo = rede, origem, resumo
        self._ordenacao = ordenacao
        self._contatos = contatos
        self._revisao += 1
        self._confirmada = False
        return self.inspecionar()

    def inspecionar(self) -> dict[str, object]:
        """Retorna um retrato JSON independente, inclusive antes da primeira carga."""
        with self._lock:
            return deepcopy({
                "revisao": self._revisao,
                "disponivel": self._rede is not None,
                "confirmada": self._confirmada,
                "origem": self._origem,
                "resumo": self._resumo,
                "interpretacao_pesos": "intensidade_normalizada_em_0_1",
            })

    def _exigir_revisao(self, revisao: int) -> RedeContatos:
        if self._rede is None:
            _falhar("rede", "Importe ou gere uma rede válida primeiro.")
        if isinstance(revisao, bool) or not isinstance(revisao, int) or revisao != self._revisao:
            _falhar("revisao", "A rede foi alterada. Atualize a inspeção antes de continuar.")
        return self._rede

    def confirmar(self, revisao: int) -> dict[str, object]:
        """Confirma a rede inspecionada para as etapas seguintes; repetir é permitido."""
        with self._lock:
            self._exigir_revisao(revisao)
            self._confirmada = True
            return self.inspecionar()

    def exportar_metadados_geracao(self, revisao: int) -> dict[str, object]:
        """Exporta a configuração nativa aceita por reconstruir_rede().

        O retrato de origem da tela inclui o tipo da rede e uma semente textual.
        Esta operação separa o formato de reprodução: devolve somente os campos
        do gerador e restaura a semente inteira. Recusa redes observadas, cuja
        reprodução exige conservar os arquivos de origem.
        """
        with self._lock:
            self._exigir_revisao(revisao)
            if self._origem["tipo"] != "sintetica":
                _falhar("origem", "A rede observada deve ser reproduzida pelos arquivos de origem.")
            metadados = deepcopy({
                campo: self._origem[campo]
                for campo in ("modelo", "parametros", "semente", "versao_algoritmo", "detalhes_modelo")
            })
            metadados["semente"] = int(metadados["semente"])
            return metadados

    def obter_rede_confirmada(self, revisao: int) -> RedeDisponivel:
        """Entrega uma cópia independente para configurar ou executar um cenário.

        Recusa ausência de rede, falta de confirmação e revisão antiga. Cada
        chamada entrega outra cópia; alterações de B/C não afetam a referência.
        """
        with self._lock:
            rede = self._exigir_revisao(revisao)
            if not self._confirmada:
                _falhar("rede", "Confirme a rede inspecionada antes de continuar.")
            return RedeDisponivel(rede.copiar(), self._revisao, deepcopy(self._origem))

    def listar_individuos(
        self, revisao: int, *, inicio: int = 0, limite: int = 50,
    ) -> dict[str, object]:
        """Pagina IDs por grau decrescente, com desempate por ID crescente.

        A ordenação é apenas de inspeção, sem implementar uma estratégia de
        intervenção. IDs são texto para preservar inteiros grandes no frontend.
        """
        with self._lock:
            rede = self._exigir_revisao(revisao)
            _validar_paginacao(inicio, limite)
            ids = self._ordenacao[inicio:inicio + limite]
            return {
                "revisao": self._revisao,
                "total": rede.numero_individuos,
                "inicio": inicio,
                "individuos": [{"id": str(i), "grau": rede.grau(rede.obter_individuo(i))} for i in ids],
            }

    def listar_contatos(
        self, revisao: int, *, inicio: int = 0, limite: int = 50,
    ) -> dict[str, object]:
        """Pagina contatos únicos para tabela ou visualização da rede real.

        Preserva a ordem de enumeração da referência. Extremos são IDs textuais;
        peso e atividade vêm do domínio, sem recalcular regras no frontend.
        O índice privado de contatos permite consultar em O(limite), sem copiar
        a rede inteira. Uma página além do fim devolve contatos vazios.
        """
        with self._lock:
            rede = self._exigir_revisao(revisao)
            _validar_paginacao(inicio, limite)
            return {
                "revisao": self._revisao,
                "total": rede.numero_contatos,
                "inicio": inicio,
                "contatos": [{
                    "origem": str(c.origem.id), "destino": str(c.destino.id),
                    "peso": c.peso, "ativa": c.ativa,
                } for c in self._contatos[inicio:inicio + limite]],
            }

    def inspecionar_individuo(self, revisao: int, identificador: int | str) -> dict[str, object]:
        """Consulta um ID exato sem expor os objetos mutáveis da rede."""
        with self._lock:
            rede = self._exigir_revisao(revisao)
            identificador = _inteiro(identificador, "id")
            pessoa = rede.buscar_individuo(identificador)
            if pessoa is None:
                _falhar("id", "O ID informado não pertence à rede carregada.")
            return {
                "revisao": self._revisao,
                "id": str(pessoa.id),
                "grau": rede.grau(pessoa),
                "estado": pessoa.estado.value,
                "isolamento": pessoa.isolamento,
                "dia_inicio_infeccao": pessoa.dia_inicio_infeccao,
            }
