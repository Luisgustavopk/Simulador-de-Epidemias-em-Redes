"""Orquestração temporal básica de uma simulação em rede."""

from dataclasses import dataclass

from simulador.individuo import EstadoSIR
from simulador.rede_contatos import RedeContatos


@dataclass(frozen=True, init=False)
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
    """Avança o relógio temporal e registra o estado da rede."""

    def __init__(
        self,
        rede: RedeContatos,
        limite_passos: int = 100,
        **opcoes: object,
    ) -> None:
        if not isinstance(rede, RedeContatos):
            raise TypeError("rede deve ser uma instância de RedeContatos.")

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

        self.rede = rede
        self.limite_passos = limite_passos
        self.passo_atual = 0
        self.historico: list[RegistroPasso] = []
        self.finalizada = False
        self.inicializar()

    @property
    def passo(self) -> int:
        return self.passo_atual

    @property
    def registros(self) -> tuple[RegistroPasso, ...]:
        return tuple(self.historico)

    def inicializar(self) -> list[RegistroPasso]:
        """Reinicia o relógio e registra o estado inicial em t=0."""
        self.passo_atual = 0
        self.historico.clear()
        self.finalizada = False
        self._atualizar_finalizacao()
        if not self.finalizada:
            self.registrar_estado_atual()
        else:
            self.registrar_estado_atual()
        return list(self.historico)

    def contar_estados(self) -> tuple[int, int, int, int]:
        """Conta S, I, R e isolados percorrendo os indivíduos da rede."""
        suscetiveis = 0
        infectados = 0
        recuperados = 0
        isolados = 0

        for individuo in self.rede.individuos:
            if individuo.estado is EstadoSIR.SUSCETIVEL:
                suscetiveis += 1
            elif individuo.estado is EstadoSIR.INFECTADO:
                infectados += 1
            elif individuo.estado is EstadoSIR.RECUPERADO:
                recuperados += 1

            if individuo.isolamento:
                isolados += 1

        return suscetiveis, infectados, recuperados, isolados

    def registrar_estado_atual(self) -> RegistroPasso:
        """Cria e adiciona o RegistroPasso correspondente ao passo atual."""
        s, i, r, isolados = self.contar_estados()
        registro = RegistroPasso(
            passo=self.passo_atual,
            suscetiveis=s,
            infectados=i,
            recuperados=r,
            isolados=isolados,
        )
        self.historico.append(registro)
        self._atualizar_finalizacao()
        return registro

    def executar_passo(self) -> RegistroPasso:
        """Avança t -> t+1 e registra uma nova fotografia."""
        if self.finalizada:
            return self.historico[-1]
        if self.passo_atual >= self.limite_passos:
            self.finalizada = True
            return self.historico[-1]

        self.passo_atual += 1
        return self.registrar_estado_atual()

    def avancar(self) -> RegistroPasso:
        return self.executar_passo()

    def executar(self) -> list[RegistroPasso]:
        """Executa até extinção dos infectados ou o limite de passos."""
        while not self.finalizada:
            self.executar_passo()
        return list(self.historico)

    def executar_motor(
        self,
        motor: object,
        configuracao: object,
        revisao_rede: int,
        estrategia: object = None,
    ) -> tuple[RegistroPasso, ...]:
        """Executa o ciclo SIR usando a configuração e o motor fornecidos.

        A preparação dos infectados iniciais e da intervenção no passo zero
        ocorre antes da criação desta instância. A partir do registro inicial,
        este método concentra a evolução, a intervenção agendada e a parada.
        """
        from simulador.isolamento import aplicar_isolamento

        intervencao = configuracao.intervencao
        while not self.finalizada:
            if (
                intervencao is not None
                and self.passo == intervencao.inicio
                and self.passo > 0
                and estrategia is not None
            ):
                ids = estrategia.selecionar(
                    self.rede,
                    intervencao.quantidade_isolados(self.rede.numero_individuos),
                )
                aplicar_isolamento(
                    self.rede,
                    ids,
                    intervencao.mecanismo,
                    orcamento=intervencao.quantidade_isolados(
                        self.rede.numero_individuos,
                    ),
                    reducao=intervencao.reducao,
                )
            motor.avancar(
                self.rede,
                configuracao,
                self.passo,
                revisao_rede=revisao_rede,
            )
            self.executar_passo()
        return self.registros

    def getPassoAtual(self) -> int:
        return self.passo_atual

    def isFinalizada(self) -> bool:
        return self.finalizada

    def getHistorico(self) -> tuple[RegistroPasso, ...]:
        return tuple(self.historico)

    def _atualizar_finalizacao(self) -> None:
        _, infectados, _, _ = self.contar_estados()
        if infectados == 0:
            self.finalizada = True
        elif self.passo_atual >= self.limite_passos:
            self.finalizada = True
