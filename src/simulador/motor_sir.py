from simulador.aleatoriedade import GeradorAleatorio
from simulador.configuracao import ConfiguracaoSimulacao, ErroConfiguracao
from simulador.individuo import EstadoSIR
from simulador.rede_contatos import RedeContatos


class MotorSIR:
    def __init__(self, gerador: GeradorAleatorio) -> None:
        self._gerador = gerador

    def avancar(
        self, rede: RedeContatos, configuracao: ConfiguracaoSimulacao,
        passo_atual: int, *, revisao_rede: int,
    ) -> None:
        if isinstance(passo_atual, bool) or not isinstance(passo_atual, int):
            raise TypeError("O passo atual deve ser inteiro.")
        if passo_atual < 0:
            raise ValueError("O passo atual deve ser não negativo.")
        problemas = configuracao.validar(rede, revisao_rede)
        if problemas:
            raise ErroConfiguracao(problemas)
        pessoas = sorted(rede.iter_individuos(), key=lambda p: p.id)
        estados = {p.id: p.estado for p in pessoas}
        novas_infecoes: list[int] = []
        recuperacoes: list[int] = []
        for pessoa in pessoas:
            if estados[pessoa.id] is EstadoSIR.SUSCETIVEL:
                probabilidade = 0.0
                for contato in sorted(rede.contatos_de(pessoa), key=lambda c: c.outro_extremo(pessoa).id):
                    vizinho = contato.outro_extremo(pessoa)
                    if contato.ativa and estados[vizinho.id] is EstadoSIR.INFECTADO:
                        p = contato.peso
                        if configuracao.modo_peso == "intensidade":
                            p *= configuracao.beta
                        probabilidade += (1 - probabilidade) * p
                if self._gerador.uniforme() < probabilidade:
                    novas_infecoes.append(pessoa.id)
            elif estados[pessoa.id] is EstadoSIR.INFECTADO:
                if self._gerador.uniforme() < configuracao.gamma:
                    recuperacoes.append(pessoa.id)
        for id_individuo in novas_infecoes:
            rede.obter_individuo(id_individuo).infectar(passo_atual + 1)
        for id_individuo in recuperacoes:
            rede.obter_individuo(id_individuo).recuperar()
