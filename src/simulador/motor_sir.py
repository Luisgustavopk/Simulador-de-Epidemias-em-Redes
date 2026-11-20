from simulador.aleatoriedade import GeradorAleatorio
from simulador.configuracao import ConfiguracaoSimulacao, ErroConfiguracao
from simulador.contato import Contato
from simulador.individuo import EstadoSIR, Individuo
from simulador.rede_contatos import RedeContatos


class MotorSIR:
    def __init__(self, gerador: GeradorAleatorio) -> None:
        self._gerador = gerador
        self._rede: RedeContatos | None = None
        self._versao_topologia = -1
        self._configuracao: ConfiguracaoSimulacao | None = None
        self._revisao_rede: int | None = None
        self._ordem: tuple[
            tuple[Individuo, tuple[tuple[int, Contato], ...]], ...
        ] = ()

    def _preparar(
        self, rede: RedeContatos, configuracao: ConfiguracaoSimulacao,
        revisao_rede: int,
    ) -> None:
        estrutura_mudou = (
            not isinstance(rede, RedeContatos)
            or self._rede is not rede
            or self._versao_topologia != rede.versao_topologia
        )
        if (
            estrutura_mudou
            or self._configuracao is not configuracao
            or type(revisao_rede) is not int
            or self._revisao_rede != revisao_rede
        ):
            problemas = configuracao.validar(rede, revisao_rede)
            if problemas:
                raise ErroConfiguracao(problemas)
        if estrutura_mudou:
            pessoas = sorted(rede.iter_individuos(), key=lambda pessoa: pessoa.id)
            self._ordem = tuple(
                (pessoa, tuple(
                    (contato.outro_extremo(pessoa).id, contato)
                    for contato in sorted(
                        rede.contatos_de(pessoa),
                        key=lambda contato: contato.outro_extremo(pessoa).id,
                    )
                ))
                for pessoa in pessoas
            )
            self._rede = rede
            self._versao_topologia = rede.versao_topologia
        self._configuracao = configuracao
        self._revisao_rede = revisao_rede

    def avancar(
        self, rede: RedeContatos, configuracao: ConfiguracaoSimulacao,
        passo_atual: int, *, revisao_rede: int,
    ) -> None:
        if isinstance(passo_atual, bool) or not isinstance(passo_atual, int):
            raise TypeError("O passo atual deve ser inteiro.")
        if passo_atual < 0:
            raise ValueError("O passo atual deve ser não negativo.")
        self._preparar(rede, configuracao, revisao_rede)
        estados_no_inicio = {
            pessoa.id: pessoa.estado for pessoa, _ in self._ordem
        }
        novas_infecoes: list[int] = []
        recuperacoes: list[int] = []
        for pessoa, contatos in self._ordem:
            if estados_no_inicio[pessoa.id] is EstadoSIR.SUSCETIVEL:
                probabilidade_infeccao = 0.0
                for id_vizinho, contato in contatos:
                    if not contato.ativa or estados_no_inicio[id_vizinho] is not EstadoSIR.INFECTADO:
                        continue
                    probabilidade_contato = contato.peso
                    if configuracao.modo_peso == "intensidade":
                        probabilidade_contato *= configuracao.beta
                    probabilidade_infeccao += (1 - probabilidade_infeccao) * probabilidade_contato
                if self._gerador.uniforme() < probabilidade_infeccao:
                    novas_infecoes.append(pessoa.id)
            elif estados_no_inicio[pessoa.id] is EstadoSIR.INFECTADO:
                if self._gerador.uniforme() < configuracao.gamma:
                    recuperacoes.append(pessoa.id)
        for id_individuo in novas_infecoes:
            rede.obter_individuo(id_individuo).infectar(passo_atual + 1)
        for id_individuo in recuperacoes:
            rede.obter_individuo(id_individuo).recuperar()
