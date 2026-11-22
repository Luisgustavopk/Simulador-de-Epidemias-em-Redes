"""Orquestração temporal de uma simulação SIR em rede."""

from dataclasses import dataclass

from simulador.aleatoriedade import GeradorAleatorio
from simulador.configuracao import ConfiguracaoSimulacao, aplicar_condicoes_iniciais
from simulador.estrategias_isolamento import preparar_estrategia
from simulador.individuo import EstadoSIR
from simulador.isolamento import aplicar_isolamento
from simulador.motor_sir import MotorSIR
from simulador.rede_contatos import RedeContatos
from simulador.resultado import ResultadoSimulacao


@dataclass(frozen=True, slots=True, init=False)
class RegistroPasso:
    """Fotografia dos estados epidemiológicos em um passo."""

    passo: int
    suscetiveis: int
    infectados: int
    recuperados: int
    isolados: int

    def __init__(
        self,
        passo: int,
        suscetiveis: int | None = None,
        infectados: int | None = None,
        recuperados: int | None = None,
        isolados: int = 0,
        *,
        s: int | None = None,
        i: int | None = None,
        r: int | None = None,
    ) -> None:
        if isinstance(passo, bool) or not isinstance(passo, int):
            raise TypeError("O passo deve ser inteiro.")
        if passo < 0:
            raise ValueError("O passo não pode ser negativo.")

        if suscetiveis is None:
            suscetiveis = s
        if infectados is None:
            infectados = i
        if recuperados is None:
            recuperados = r
        if suscetiveis is None or infectados is None or recuperados is None:
            raise TypeError(
                "Informe suscetiveis, infectados e recuperados "
                "(também aceitos como s, i e r)."
            )

        valores = (suscetiveis, infectados, recuperados, isolados)
        if any(isinstance(valor, bool) or not isinstance(valor, int) for valor in valores):
            raise TypeError("As quantidades do registro devem ser inteiras.")
        if any(valor < 0 for valor in valores):
            raise ValueError("As quantidades do registro não podem ser negativas.")

        object.__setattr__(self, "passo", passo)
        object.__setattr__(self, "suscetiveis", suscetiveis)
        object.__setattr__(self, "infectados", infectados)
        object.__setattr__(self, "recuperados", recuperados)
        object.__setattr__(self, "isolados", isolados)

    @property
    def s(self) -> int:
        return self.suscetiveis

    @property
    def i(self) -> int:
        return self.infectados

    @property
    def r(self) -> int:
        return self.recuperados

    def getPasso(self) -> int:
        return self.passo

    def getSuscetiveis(self) -> int:
        return self.suscetiveis

    def getInfectados(self) -> int:
        return self.infectados

    def getRecuperados(self) -> int:
        return self.recuperados

    def getIsolados(self) -> int:
        return self.isolados


class Simulacao:
    """Coordena o motor SIR, as intervenções e o histórico da rede.

    copiar_referencia=False permite reutilizar um retrato privado dos
    controllers. O chamador deve mantê-lo estável durante o uso da instância.
    Com configuração, a rede de trabalho é independente em cada início.
    """

    def __init__(
        self,
        rede: RedeContatos,
        limite_passos: int | ConfiguracaoSimulacao = 100,
        *,
        configuracao: ConfiguracaoSimulacao | None = None,
        revisao_rede: int | None = None,
        repeticao: int | None = None,
        copiar_referencia: bool = True,
        **opcoes: object,
    ) -> None:
        if not isinstance(rede, RedeContatos):
            raise TypeError("rede deve ser uma instância de RedeContatos.")

        if isinstance(limite_passos, ConfiguracaoSimulacao):
            if configuracao is not None:
                raise TypeError('Informe a configuração apenas uma vez.')
            configuracao = limite_passos
        if configuracao is not None:
            limite_passos = configuracao.limite_passos

        if "max_passos" in opcoes:
            if limite_passos != 100:
                raise TypeError("Informe apenas limite_passos ou max_passos.")
            limite_passos = opcoes.pop("max_passos")
        if opcoes:
            nome = next(iter(opcoes))
            raise TypeError(f"Argumento inesperado: {nome}")
        if isinstance(limite_passos, bool) or not isinstance(limite_passos, int):
            raise TypeError("O limite de passos deve ser inteiro.")
        if limite_passos < 0:
            raise ValueError("O limite de passos não pode ser negativo.")

        self._rede_inicial = rede.copiar() if copiar_referencia else rede
        self.rede = rede
        self.configuracao = None
        self.repeticao = repeticao
        self._resultado: ResultadoSimulacao | None = None
        self._motor: MotorSIR | None = None
        self._estrategia = None
        if configuracao is not None:
            revisao = configuracao.revisao_rede if revisao_rede is None else revisao_rede
            self.configuracao = configuracao.preparar(self._rede_inicial, revisao)
        self.limite_passos = limite_passos
        self.passo_atual = 0
        self.historico: list[RegistroPasso] = []
        self.finalizada = False
        if self.configuracao is None:
            self.registrar_estado_atual()
        else:
            self.inicializar()

    @property
    def passo(self) -> int:
        return self.passo_atual

    @property
    def registros(self) -> tuple[RegistroPasso, ...]:
        return tuple(self.historico)

    def inicializar(self) -> list[RegistroPasso]:
        """Restaura a rede inicial, os sorteios e o único registro em t=0."""
        self.rede = self._rede_inicial.copiar()
        self.passo_atual = 0
        self.historico.clear()
        self.finalizada = False
        self._resultado = None
        self._motor = None
        self._estrategia = None
        if self.configuracao is not None:
            revisao = self.configuracao.revisao_rede
            aplicar_condicoes_iniciais(self.rede, self.configuracao, revisao)
            self._motor = MotorSIR(
                GeradorAleatorio(self.configuracao.semente_epidemia),
            )
            self._estrategia = preparar_estrategia(
                self.rede, self.configuracao, revisao_rede=revisao,
            )
        self.registrar_estado_atual(
            configuracao=self.configuracao, estrategia=self._estrategia,
        )
        return list(self.historico)

    def contar_estados(self) -> tuple[int, int, int, int]:
        """Conta S, I, R e isolados percorrendo os indivíduos da rede."""
        suscetiveis = 0
        infectados = 0
        recuperados = 0
        isolados = 0

        for individuo in self.rede.iter_individuos():
            if individuo.estado is EstadoSIR.SUSCETIVEL:
                suscetiveis += 1
            elif individuo.estado is EstadoSIR.INFECTADO:
                infectados += 1
            elif individuo.estado is EstadoSIR.RECUPERADO:
                recuperados += 1

            if individuo.isolamento:
                isolados += 1

        return suscetiveis, infectados, recuperados, isolados

    def registrar_estado_atual(
        self, *, configuracao: object = None, estrategia: object = None,
    ) -> RegistroPasso:
        """Registra o instante, preparando a intervenção se ainda pode avançar.

        Sem os componentes opcionais, apenas registra o estado da rede.
        Com eles, aplica a intervenção antes do registro, salvo em extinção
        ou no limite. Cada instante do fluxo de execução é registrado uma vez.
        """
        s, i, r, isolados = self.contar_estados()
        if configuracao is not None and i > 0 and self.passo < self.limite_passos:
            # O mecanismo preserva SIR; a seleção informa o acréscimo em Q
            # sem exigir uma segunda contagem da população.
            isolados += self._aplicar_intervencao(configuracao, estrategia)
        registro = RegistroPasso(
            passo=self.passo_atual,
            suscetiveis=s,
            infectados=i,
            recuperados=r,
            isolados=isolados,
        )
        self.historico.append(registro)
        self._atualizar_finalizacao(registro)
        return registro

    def executar_passo(self) -> RegistroPasso:
        """Aplica uma transição SIR configurada e registra o próximo instante."""
        if self.finalizada:
            return self.historico[-1]
        if self.passo_atual >= self.limite_passos:
            self.finalizada = True
            return self.historico[-1]

        if self.configuracao is not None:
            return self._executar_passo_motor(
                self._motor,
                self.configuracao,
                self.configuracao.revisao_rede,
                self._estrategia,
            )
        return self._avancar_relogio()

    def _avancar_relogio(
        self, configuracao: object = None, estrategia: object = None,
    ) -> RegistroPasso:
        self._resultado = None
        self.passo_atual += 1
        return self.registrar_estado_atual(
            configuracao=configuracao, estrategia=estrategia,
        )

    def avancar(self) -> RegistroPasso:
        return self.executar_passo()

    def executar(self) -> ResultadoSimulacao | list[RegistroPasso]:
        """Executa até extinção dos infectados ou o limite de passos."""
        while not self.finalizada:
            self.executar_passo()
        if self.configuracao is not None:
            if self._resultado is None:
                from simulador.metricas import MetricasEpidemia

                self._resultado = ResultadoSimulacao(
                    configuracao=self.configuracao, historico=self.registros,
                    metricas=MetricasEpidemia(self.registros, self.rede.numero_individuos),
                    motivo_termino='extincao' if self.registros[-1].infectados == 0 else 'limite_passos',
                    populacao_inicial=self.rede.numero_individuos, repeticao=self.repeticao,
                )
            return self._resultado
        return list(self.historico)

    def executar_motor(
        self,
        motor: object,
        configuracao: object,
        revisao_rede: int,
        estrategia: object = None,
    ) -> tuple[RegistroPasso, ...]:
        """Executa o ciclo SIR usando a configuração e o motor fornecidos.

        Na construção legada, prepare os infectados iniciais e a intervenção
        no passo zero antes de criar a instância. O avanço compartilha a mesma
        transição usada pela execução configurada por passos.
        """
        while not self.finalizada:
            self._executar_passo_motor(
                motor, configuracao, revisao_rede, estrategia,
            )
        return self.registros

    def _executar_passo_motor(
        self,
        motor: object,
        configuracao: object,
        revisao_rede: int,
        estrategia: object,
    ) -> RegistroPasso:
        motor.avancar(
            self.rede, configuracao, self.passo, revisao_rede=revisao_rede,
        )
        return self._avancar_relogio(configuracao, estrategia)

    def _aplicar_intervencao(self, configuracao: object, estrategia: object) -> int:
        """Aplica a intervenção devida e devolve o número de novos isolados."""
        intervencao = configuracao.intervencao
        if (
            intervencao is not None
            and self.passo == intervencao.inicio
            and estrategia is not None
        ):
            quantidade = intervencao.quantidade_isolados(self.rede.numero_individuos)
            resultado = aplicar_isolamento(
                self.rede,
                estrategia.selecionar(self.rede, quantidade),
                intervencao.mecanismo,
                orcamento=quantidade,
                reducao=intervencao.reducao,
            )
            return len(resultado.ids_selecionados)
        return 0

    def getPassoAtual(self) -> int:
        return self.passo_atual

    def isFinalizada(self) -> bool:
        return self.finalizada

    def getHistorico(self) -> tuple[RegistroPasso, ...]:
        return tuple(self.historico)

    def _atualizar_finalizacao(self, registro: RegistroPasso) -> None:
        if registro.infectados == 0 or self.passo_atual >= self.limite_passos:
            self.finalizada = True
