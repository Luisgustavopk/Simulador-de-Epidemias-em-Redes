"""Aplicação única dos mecanismos, preservando a coorte epidemiológica.

A seleção das pessoas e o agendamento pertencem ao controlador. Este módulo
recebe os IDs selecionados e aplica o mecanismo no instante da intervenção.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

from simulador.individuo import Individuo
from simulador.rede_contatos import RedeContatos


class MecanismoIsolamento(str, Enum):
    """Efeito sobre os contatos das pessoas selecionadas."""

    DESATIVACAO = "desativacao"
    REDUCAO = "reducao"
    EXCLUSAO = "exclusao"


@dataclass(frozen=True, slots=True)
class ResultadoIsolamento:
    """Registro da aplicação; duração adotada até o fim da execução.

    O controlador deve associar estratégia, semente e passo a esse registro.
    Contatos afetados são únicos, mesmo com ambos os extremos selecionados.
    """

    ids_selecionados: tuple[int, ...]
    mecanismo: MecanismoIsolamento
    orcamento: int
    reducao: float | None
    numero_contatos_afetados: int


def aplicar_isolamento(
    rede: RedeContatos,
    ids_selecionados: Iterable[int],
    mecanismo: MecanismoIsolamento,
    *,
    orcamento: int,
    reducao: float | None = None,
) -> ResultadoIsolamento:
    """Valida a seleção completa e aplica o mecanismo, sem sorteios.

    A política desta versão tem uma intervenção por cenário, sem liberação
    ou substituição de alvos. Não aceita isolamento prévio, evitando misturar
    mecanismos ou acumular reduções por reaplicação. Use uma cópia da rede
    de referência para cada cenário. O cadastro e os estados SIR não mudam.

    Args:
        rede: Rede do cenário, ainda sem pessoas isoladas.
        ids_selecionados: IDs únicos já escolhidos pela estratégia, em S, I ou R.
        mecanismo: Desativação, redução ou exclusão dos contatos incidentes.
        orcamento: Limite inteiro de pessoas, entre zero e a população.
        reducao: Fração retirada do peso, em [0, 1], exigida somente na redução.
            Por exemplo, 0.5 transforma 0.8 em 0.4. Aplica uma vez por contato,
            mesmo quando seus dois extremos estão selecionados.

    Returns:
        Registro imutável da seleção e da quantidade de contatos abrangidos.

    Raises:
        TypeError: Se rede, mecanismo, IDs, orçamento ou redução tiverem tipo
            incompatível. Texto não substitui MecanismoIsolamento.
        ValueError: Se houver duplicatas, orçamento excedido, isolamento prévio
            ou parâmetros fora do domínio. Nenhuma validação altera a rede.
        KeyError: Se algum ID não pertencer à rede.
    """
    if not isinstance(rede, RedeContatos):
        raise TypeError("A rede deve ser uma instância de RedeContatos.")
    if not isinstance(mecanismo, MecanismoIsolamento):
        raise TypeError("O mecanismo deve ser um MecanismoIsolamento.")
    if isinstance(orcamento, bool) or not isinstance(orcamento, int):
        raise TypeError("O orçamento deve ser inteiro.")
    if not 0 <= orcamento <= rede.numero_individuos:
        raise ValueError("O orçamento deve estar entre zero e a população.")
    if mecanismo is MecanismoIsolamento.REDUCAO:
        if isinstance(reducao, bool) or not isinstance(reducao, (int, float)):
            raise TypeError("A redução deve ser uma fração numérica em [0, 1].")
        if not 0 <= reducao <= 1:
            raise ValueError("A redução deve ser finita e estar entre 0 e 1.")
        reducao = float(reducao)
    elif reducao is not None:
        raise ValueError("Informe redução somente para o mecanismo de redução.")

    ids = tuple(ids_selecionados)
    selecionados: set[int] = set()
    pessoas: list[Individuo] = []
    for identificador in ids:
        pessoa = rede.obter_individuo(identificador)
        if identificador in selecionados:
            raise ValueError(f"O indivíduo {identificador} foi selecionado duas vezes.")
        selecionados.add(identificador)
        pessoas.append(pessoa)
    if len(ids) > orcamento:
        raise ValueError("A seleção excede o orçamento de pessoas.")
    if any(pessoa.isolamento for pessoa in rede.iter_individuos()):
        raise ValueError("A intervenção exige uma rede sem isolamento prévio.")

    # Materializar os contatos antes de removê-los evita invalidar iteradores.
    # A enumeração única também evita reduzir duas vezes um contato compartilhado.
    afetados = tuple(
        contato for contato in rede.iter_contatos()
        if contato.origem.id in selecionados or contato.destino.id in selecionados
    )
    for contato in afetados:
        origem, destino = contato.origem.id, contato.destino.id
        if mecanismo is MecanismoIsolamento.DESATIVACAO:
            rede.desativar_contato(origem, destino)
        elif mecanismo is MecanismoIsolamento.EXCLUSAO:
            rede.remover_contato(origem, destino)
        else:
            # O ramo REDUCAO validou a fração antes de qualquer mutação.
            assert reducao is not None
            rede.alterar_peso_contato(origem, destino, contato.peso * (1 - reducao))
    for pessoa in pessoas:
        pessoa.isolar()
    return ResultadoIsolamento(ids, mecanismo, orcamento, reducao, len(afetados))
