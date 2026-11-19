"""Métricas epidemiológicas calculadas a partir do histórico da simulação."""

from simulador.simulacao import RegistroPasso


class MetricasEpidemia:
    """Calcula os principais indicadores finais de uma epidemia."""

    __slots__ = (
        "historico", "total_individuos", "populacao_inicial",
        "pico_infectados", "passo_pico", "total_afetados",
        "taxa_ataque", "fracao_acumulada", "duracao_surto", "_congelada",
    )

    def __init__(
        self,
        historico: list[RegistroPasso] | tuple[RegistroPasso, ...],
        total_individuos: int,
    ) -> None:
        if not isinstance(historico, (list, tuple)):
            raise TypeError("O histórico deve ser uma lista ou tupla de RegistroPasso.")
        if not historico:
            raise ValueError("O histórico da simulação não pode estar vazio.")
        if any(not isinstance(registro, RegistroPasso) for registro in historico):
            raise TypeError("O histórico deve conter apenas instâncias de RegistroPasso.")

        if isinstance(total_individuos, bool) or not isinstance(total_individuos, int):
            raise TypeError("O total de indivíduos deve ser inteiro.")
        if total_individuos < 0:
            raise ValueError("O total de indivíduos não pode ser negativo.")

        registros = tuple(historico)
        passos = tuple(registro.passo for registro in registros)
        if any(passo_a >= passo_b for passo_a, passo_b in zip(passos, passos[1:])):
            raise ValueError("Os passos do histórico devem estar em ordem estritamente crescente.")
        if passos[0] != 0:
            raise ValueError("O histórico deve começar no passo zero.")

        for registro in registros:
            soma_estados = (
                registro.suscetiveis
                + registro.infectados
                + registro.recuperados
            )
            if soma_estados != total_individuos:
                raise ValueError(
                    "A soma dos estados S, I e R deve corresponder ao total "
                    "de indivíduos da população."
                )
            if total_individuos == 0 and registro.infectados != 0:
                raise ValueError("Uma população zero não pode conter infectados.")

        object.__setattr__(self, "historico", registros)
        object.__setattr__(self, "total_individuos", total_individuos)
        object.__setattr__(self, "populacao_inicial", total_individuos)

        pico_infectados = max(registro.infectados for registro in registros)
        passo_pico = next(
            registro.passo
            for registro in registros if registro.infectados == pico_infectados
        )

        registro_final = registros[-1]
        total_afetados = registro_final.infectados + registro_final.recuperados
        taxa_ataque = total_afetados / total_individuos if total_individuos else 0.0

        duracao_surto = next(
            (
                registro.passo
                for registro in registros
                if registro.infectados == 0
            ),
            registro_final.passo,
        )
        for nome, valor in (
            ("pico_infectados", pico_infectados), ("passo_pico", passo_pico),
            ("total_afetados", total_afetados), ("taxa_ataque", taxa_ataque),
            ("fracao_acumulada", taxa_ataque), ("duracao_surto", duracao_surto),
        ):
            object.__setattr__(self, nome, valor)
        object.__setattr__(self, "_congelada", True)

    def __setattr__(self, nome: str, valor: object) -> None:
        if getattr(self, "_congelada", False):
            raise AttributeError("As métricas são imutáveis.")
        object.__setattr__(self, nome, valor)

    @property
    def taxa_ataque_percentual(self) -> float:
        """Taxa de ataque expressa em percentual, no intervalo [0, 100]."""
        return self.taxa_ataque * 100.0

    @property
    def pico_proporcional(self) -> float:
        return self.pico_infectados / self.total_individuos if self.total_individuos else 0.0

    @property
    def horizonte_observado(self) -> int:
        return self.historico[-1].passo

    @property
    def duracao_extincao(self) -> int | None:
        return self.duracao_surto if self.historico[-1].infectados == 0 else None

    @property
    def fracao_final_recuperados(self) -> float:
        """Fração da população recuperada no último registro."""
        return (
            self.historico[-1].recuperados / self.total_individuos
            if self.total_individuos
            else 0.0
        )

    @property
    def ocorreu_infeccao(self) -> bool:
        """Indica se algum registro observou indivíduos infectados."""
        return any(registro.infectados > 0 for registro in self.historico)

    def gerar_resumo(self) -> dict[str, int | float | bool]:
        """Retorna as métricas em formato adequado para envio ao frontend."""
        return {
            "pico_infectados": self.pico_infectados,
            "passo_pico": self.passo_pico,
            "total_afetados": self.total_afetados,
            "taxa_ataque": self.taxa_ataque,
            "duracao_surto": self.duracao_surto,
            "fracao_final_recuperados": self.fracao_final_recuperados,
            "ocorreu_infeccao": self.ocorreu_infeccao,
        }

    def getPicoInfectados(self) -> int:
        return self.pico_infectados

    def getPassoPico(self) -> int:
        return self.passo_pico

    def getTotalAfetados(self) -> int:
        return self.total_afetados

    def getTaxaAtaque(self) -> float:
        return self.taxa_ataque

    def getPopulacaoInicial(self) -> int:
        return self.total_individuos

    def getFracaoAcumulada(self) -> float:
        return self.taxa_ataque

    def getPicoProporcional(self) -> float:
        return self.pico_proporcional

    def getHorizonteObservado(self) -> int:
        return self.horizonte_observado

    def getDuracaoExtincao(self) -> int:
        return self.duracao_surto

    def getDuracaoSurto(self) -> int:
        return self.duracao_surto

