"""Geradores nativos de redes sintéticas com aleatoriedade independente."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from itertools import combinations
import math
from random import Random

from simulador.individuo import Individuo
from simulador.rede_contatos import RedeContatos


class _ParametrosImutaveis(Mapping[str, int | float]):
    """Mapa numérico sem objetos mutáveis, compatível com cópia profunda."""

    __slots__ = ("_itens",)

    def __init__(self, valores: Mapping[str, int | float]) -> None:
        if not isinstance(valores, Mapping):
            raise TypeError("Os parâmetros e detalhes do modelo devem ser mapas.")
        itens = tuple(valores.items())
        for chave, valor in itens:
            if not isinstance(chave, str):
                raise TypeError("As chaves dos parâmetros e detalhes devem ser strings.")
            if isinstance(valor, bool) or not isinstance(valor, (int, float)):
                raise TypeError(f"O valor de {chave!r} deve ser numérico, sem booleanos.")
            if isinstance(valor, float) and not math.isfinite(valor):
                raise ValueError(f"O valor de {chave!r} deve ser finito.")
        self._itens = itens

    def __getitem__(self, chave: str) -> int | float:
        for nome, valor in self._itens:
            if chave == nome:
                return valor
        raise KeyError(chave)

    def __iter__(self) -> Iterator[str]:
        return (chave for chave, _ in self._itens)

    def __len__(self) -> int:
        return len(self._itens)

    def __repr__(self) -> str:
        return repr(dict(self._itens))

    def __deepcopy__(self, memo: dict[int, object]) -> _ParametrosImutaveis:
        memo[id(self)] = self
        return self


@dataclass(frozen=True, slots=True)
class ResultadoGeracaoRede:
    """Rede nova e configuração preservada para reproduzir a geração.

    Os metadados são somente leitura; a rede pode receber as alterações de
    domínio normais. A versão identifica as convenções dos algoritmos locais.
    """

    rede: RedeContatos
    modelo: str
    parametros: Mapping[str, int | float]
    semente: int
    versao_algoritmo: int = 1
    detalhes_modelo: Mapping[str, int | float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Separa e preserva mapas imutáveis de entradas e informações derivadas."""
        if not isinstance(self.modelo, str):
            raise TypeError("modelo deve ser uma string.")
        _validar_inteiro(self.semente, "semente")
        _validar_inteiro(self.versao_algoritmo, "versao_algoritmo")
        object.__setattr__(self, "parametros", _ParametrosImutaveis(self.parametros))
        object.__setattr__(self, "detalhes_modelo", _ParametrosImutaveis(self.detalhes_modelo))

    def exportar_metadados(self) -> dict[str, object]:
        """Devolve dicionários independentes, próprios para conversão em JSON.

        Registra a configuração de origem; estados e alterações posteriores
        na rede não são exportados por esta operação.
        """
        return {
            "modelo": self.modelo,
            "parametros": dict(self.parametros),
            "semente": self.semente,
            "versao_algoritmo": self.versao_algoritmo,
            "detalhes_modelo": dict(self.detalhes_modelo),
        }

    def recriar(self) -> ResultadoGeracaoRede:
        """Gera outra rede inicial usando modelo, parâmetros, semente e versão."""
        return reconstruir_rede(self.exportar_metadados())

    def copiar(self) -> ResultadoGeracaoRede:
        """Copia a condição atual da rede e preserva os metadados de origem."""
        return deepcopy(self)


def _validar_inteiro(valor: int, nome: str) -> None:
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise TypeError(f"{nome} deve ser um inteiro, sem aceitar booleanos.")


def _validar_intervalo_unitario(valor: float, nome: str) -> float:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise TypeError(f"{nome} deve ser um número real, sem aceitar booleanos.")
    if not 0 <= valor <= 1:
        raise ValueError(f"{nome} deve ser finito e estar entre 0 e 1.")
    return float(valor)


def _validar_comuns(numero_individuos: int, semente: int, peso: float) -> float:
    _validar_inteiro(numero_individuos, "numero_individuos")
    if numero_individuos < 1:
        raise ValueError("numero_individuos deve ser positivo.")
    _validar_inteiro(semente, "semente")
    return _validar_intervalo_unitario(peso, "peso")


def _criar_populacao(numero_individuos: int) -> RedeContatos:
    rede = RedeContatos()
    for id_individuo in range(numero_individuos):
        rede.adicionar_individuo(Individuo(id_individuo))
    return rede


def gerar_erdos_renyi(
    numero_individuos: int,
    probabilidade_contato: float,
    *,
    semente: int,
    peso: float = 1.0,
) -> ResultadoGeracaoRede:
    """Gera G(n, p), sorteando cada par distinto uma única vez.

    Args:
        numero_individuos: População inteira positiva, com IDs de 0 a n - 1.
        probabilidade_contato: Probabilidade finita em [0, 1] de criar cada par.
        semente: Inteiro explícito para um gerador aleatório exclusivo da chamada.
        peso: Peso fixo, finito em [0, 1], dos contatos criados; não altera p.

    Returns:
        Rede independente, incluindo pessoas sem contatos, e seus metadados.

    Raises:
        TypeError: Se um parâmetro tiver tipo incompatível, incluindo bool.
        ValueError: Se n não for positivo ou p/peso estiverem fora do domínio.
    """
    peso = _validar_comuns(numero_individuos, semente, peso)
    probabilidade_contato = _validar_intervalo_unitario(
        probabilidade_contato, "probabilidade_contato"
    )
    aleatorio = Random(semente)
    rede = _criar_populacao(numero_individuos)
    pessoas = rede.individuos
    if probabilidade_contato == 1:
        for origem, destino in combinations(range(numero_individuos), 2):
            rede.conectar(pessoas[origem], pessoas[destino], peso)
    elif probabilidade_contato > 0:
        for origem, destino in combinations(range(numero_individuos), 2):
            if aleatorio.random() < probabilidade_contato:
                rede.conectar(pessoas[origem], pessoas[destino], peso)
    return ResultadoGeracaoRede(
        rede=rede,
        modelo="erdos_renyi",
        parametros={
            "numero_individuos": numero_individuos,
            "probabilidade_contato": probabilidade_contato,
            "peso": peso,
        },
        semente=semente,
    )


def gerar_barabasi_albert(
    numero_individuos: int,
    contatos_por_novo_individuo: int,
    *,
    semente: int,
    peso: float = 1.0,
) -> ResultadoGeracaoRede:
    """Gera uma rede por crescimento e ligação preferencial pelo grau estrutural.

    A convenção local começa com o grafo completo de m + 1 pessoas. Cada nova
    pessoa escolhe m alvos distintos entre as anteriores, com probabilidade
    proporcional ao grau; os graus só são atualizados após a escolha dos alvos.

    Args:
        numero_individuos: População inteira positiva, com IDs de 0 a n - 1.
        contatos_por_novo_individuo: Inteiro m, com 1 <= m < n.
        semente: Inteiro explícito para um gerador aleatório exclusivo da chamada.
        peso: Peso fixo, finito em [0, 1], sem efeito na ligação preferencial.

    Returns:
        Rede independente e conectada, com configuração e tamanho do núcleo.

    Raises:
        TypeError: Se um parâmetro tiver tipo incompatível, incluindo bool.
        ValueError: Se n, m ou peso estiverem fora dos respectivos domínios.
    """
    peso = _validar_comuns(numero_individuos, semente, peso)
    _validar_inteiro(contatos_por_novo_individuo, "contatos_por_novo_individuo")
    if not 1 <= contatos_por_novo_individuo < numero_individuos:
        raise ValueError("contatos_por_novo_individuo deve satisfazer 1 <= m < n.")
    aleatorio = Random(semente)
    rede = _criar_populacao(numero_individuos)
    pessoas = rede.individuos
    tamanho_nucleo = contatos_por_novo_individuo + 1
    # Cada ID aparece uma vez por contato incidente: sorteá-lo é ponderar por grau.
    ids_por_grau: list[int] = []
    for origem in range(tamanho_nucleo):
        for destino in range(origem + 1, tamanho_nucleo):
            rede.conectar(pessoas[origem], pessoas[destino], peso)
            ids_por_grau.extend((origem, destino))

    for novo_id in range(tamanho_nucleo, numero_individuos):
        alvos: list[int] = []
        selecionados: set[int] = set()
        while len(alvos) < contatos_por_novo_individuo:
            alvo = aleatorio.choice(ids_por_grau)
            if alvo not in selecionados:
                selecionados.add(alvo)
                alvos.append(alvo)
        for alvo in alvos:
            rede.conectar(pessoas[novo_id], pessoas[alvo], peso)
        ids_por_grau.extend(alvos)
        ids_por_grau.extend([novo_id] * contatos_por_novo_individuo)

    return ResultadoGeracaoRede(
        rede=rede,
        modelo="barabasi_albert",
        parametros={
            "numero_individuos": numero_individuos,
            "contatos_por_novo_individuo": contatos_por_novo_individuo,
            "peso": peso,
        },
        semente=semente,
        detalhes_modelo={"tamanho_nucleo_inicial": tamanho_nucleo},
    )


def reconstruir_rede(metadados: Mapping[str, object]) -> ResultadoGeracaoRede:
    """Reconstrói ER ou BA a partir de metadados, inclusive após ler JSON.

    Args:
        metadados: Modelo, parâmetros de entrada, semente e versão do algoritmo.
            Detalhes derivados são opcionais; se presentes, devem ser coerentes.

    Returns:
        Nova rede inicial com configuração validada pelos próprios geradores.

    Raises:
        TypeError: Se algum campo tiver tipo incompatível.
        ValueError: Se faltarem campos, houver campos desconhecidos, o modelo
            ou a versão não forem suportados, ou a configuração for incoerente.
    """
    if not isinstance(metadados, Mapping):
        raise TypeError("Os metadados devem ser um mapa.")
    if any(not isinstance(chave, str) for chave in metadados):
        raise TypeError("As chaves dos metadados devem ser strings.")
    obrigatorios = {"modelo", "parametros", "semente", "versao_algoritmo"}
    faltantes = obrigatorios - metadados.keys()
    extras = metadados.keys() - obrigatorios - {"detalhes_modelo"}
    if faltantes:
        raise ValueError("Metadados incompletos; campos ausentes: " + ", ".join(sorted(faltantes)))
    if extras:
        raise ValueError("Campos de metadados não suportados: " + ", ".join(sorted(extras)))
    modelo = metadados["modelo"]
    if not isinstance(modelo, str):
        raise TypeError("modelo deve ser uma string.")
    if modelo not in ("erdos_renyi", "barabasi_albert"):
        raise ValueError(f"Modelo não suportado: {modelo!r}.")
    versao = metadados["versao_algoritmo"]
    _validar_inteiro(versao, "versao_algoritmo")
    if versao != 1:
        raise ValueError(f"Versão de algoritmo não suportada: {versao}.")
    parametros = _ParametrosImutaveis(metadados["parametros"])
    segundo_parametro = (
        "probabilidade_contato" if modelo == "erdos_renyi" else "contatos_por_novo_individuo"
    )
    obrigatorios_parametros = {"numero_individuos", segundo_parametro}
    faltantes_parametros = obrigatorios_parametros - parametros.keys()
    extras_parametros = parametros.keys() - obrigatorios_parametros - {"peso"}
    if faltantes_parametros:
        raise ValueError("Parâmetros ausentes: " + ", ".join(sorted(faltantes_parametros)))
    if extras_parametros:
        raise ValueError("Parâmetros não suportados: " + ", ".join(sorted(extras_parametros)))
    if "detalhes_modelo" in metadados:
        detalhes = _ParametrosImutaveis(metadados["detalhes_modelo"])
        esperados = {}
        if modelo == "barabasi_albert":
            m = parametros["contatos_por_novo_individuo"]
            _validar_inteiro(m, "contatos_por_novo_individuo")
            esperados = {"tamanho_nucleo_inicial": m + 1}
        if detalhes != esperados:
            raise ValueError("detalhes_modelo não corresponde aos parâmetros e à versão.")
    semente = metadados["semente"]
    if modelo == "erdos_renyi":
        return gerar_erdos_renyi(**parametros, semente=semente)
    return gerar_barabasi_albert(**parametros, semente=semente)
