"""Uma transição síncrona SIR; relógio e registro pertencem à orquestração."""

from simulador.aleatoriedade import GeradorAleatorio
from simulador.configuracao import ConfiguracaoSimulacao, ErroConfiguracao
from simulador.individuo import EstadoSIR
from simulador.rede_contatos import RedeContatos


class MotorSIR:
    """Reutiliza o fluxo epidemiológico recebido, inclusive entre passos."""

    def __init__(self, gerador: GeradorAleatorio) -> None:
        self._gerador = gerador

    def avancar(
        self, rede: RedeContatos, configuracao: ConfiguracaoSimulacao,
        passo_atual: int, *, revisao_rede: int,
    ) -> None:
        """Calcula e aplica uma vez as transições de t para t+1, no próprio grafo.

        Args:
            rede: Cópia da execução, após efeitos de intervenção já aplicados.
            configuracao: Parâmetros validados; não executa o limite de passos.
            passo_atual: Relógio fornecido pela orquestração, inteiro >= 0.
            revisao_rede: Revisão da entrada usada na execução.

        Raises:
            ErroConfiguracao: Se a configuração ou a revisão forem inválidas.
            ValueError: Se o instante for negativo.
            TypeError: Se o instante não for inteiro (bool não é aceito).
        """
        if isinstance(passo_atual, bool) or not isinstance(passo_atual, int):
            raise TypeError("O passo atual deve ser inteiro.")
        if passo_atual < 0:
            raise ValueError("O passo atual deve ser não negativo.")
        problemas = configuracao.validar(rede, revisao_rede)
        if problemas:
            raise ErroConfiguracao(problemas)
        # Guardar valores, não apenas referências a pessoas mutáveis. Nenhum
        # recém-infectado participa das decisões desta mesma transição.
        pessoas = sorted(rede.iter_individuos(), key=lambda p: p.id)
        estados = {p.id: p.estado for p in pessoas}
        novas_infecoes: list[int] = []
        recuperacoes: list[int] = []
        for pessoa in pessoas:
            if estados[pessoa.id] is EstadoSIR.SUSCETIVEL:
                nao_transmitir = 1.0
                for contato in sorted(rede.contatos_de(pessoa), key=lambda c: c.outro_extremo(pessoa).id):
                    vizinho = contato.outro_extremo(pessoa)
                    if contato.ativa and estados[vizinho.id] is EstadoSIR.INFECTADO:
                        p = contato.peso
                        if configuracao.modo_peso == "intensidade":
                            p *= configuracao.beta
                        nao_transmitir *= 1 - p
                if self._gerador.uniforme() < 1 - nao_transmitir:
                    novas_infecoes.append(pessoa.id)
            elif estados[pessoa.id] is EstadoSIR.INFECTADO:
                if self._gerador.uniforme() < configuracao.gamma:
                    recuperacoes.append(pessoa.id)
        # Isolamento não é filtro: REDUCAO mantém contatos ativos com peso
        # reduzido; DESATIVACAO/EXCLUSAO já foram materializadas na rede.
        for id_individuo in novas_infecoes:
            rede.obter_individuo(id_individuo).infectar(passo_atual + 1)
        for id_individuo in recuperacoes:
            rede.obter_individuo(id_individuo).recuperar()
