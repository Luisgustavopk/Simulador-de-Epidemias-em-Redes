"""Métricas epidemiológicas calculadas a partir do histórico da simulação."""

from simulador.simulacao import RegistroPasso


class MetricasEpidemia:
    """Calcula os principais indicadores finais de uma epidemia."""

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
        if total_individuos <= 0:
            raise ValueError("O total de indivíduos deve ser maior que zero.")

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

        self.historico: tuple[RegistroPasso, ...] = registros
        self.total_individuos = total_individuos
        self.populacao_inicial = total_individuos

        self.pico_infectados = max(registro.infectados for registro in registros)
        self.passo_pico = next(
            registro.passo
            for registro in registros
            if registro.infectados == self.pico_infectados
        )

        registro_final = registros[-1]
        self.total_afetados = (
            registro_final.infectados + registro_final.recuperados
        )
        self.taxa_ataque = (
            self.total_afetados / total_individuos
        )
        self.fracao_acumulada = self.taxa_ataque

        self.duracao_surto = next(
            (
                registro.passo
                for registro in registros
                if registro.infectados == 0
            ),
            registro_final.passo,
        )

    @property
    def taxa_ataque_percentual(self) -> float:
        """Taxa de ataque expressa em percentual, no intervalo [0, 100]."""
        return self.taxa_ataque * 100.0

    def gerar_resumo(self) -> dict[str, int | float]:
        """Retorna as métricas em formato adequado para envio ao frontend."""
        return {
            "pico_infectados": self.pico_infectados,
            "passo_pico": self.passo_pico,
            "total_afetados": self.total_afetados,
            "taxa_ataque": self.taxa_ataque,
            "duracao_surto": self.duracao_surto,
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

    def getDuracaoExtincao(self) -> int:
        return self.duracao_surto

    def getDuracaoSurto(self) -> int:
        return self.duracao_surto

