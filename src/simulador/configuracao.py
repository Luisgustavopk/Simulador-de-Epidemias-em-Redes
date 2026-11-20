from dataclasses import asdict, dataclass, replace
from decimal import Decimal
import math

from simulador.aleatoriedade import GeradorAleatorio
from simulador.individuo import EstadoSIR
from simulador.isolamento import MecanismoIsolamento
from simulador.rede_contatos import RedeContatos


@dataclass(frozen=True, slots=True)
class ProblemaConfiguracao:
    campo: str
    mensagem: str


class ErroConfiguracao(ValueError):
    def __init__(self, problemas: list[ProblemaConfiguracao]) -> None:
        self.problemas = tuple(problemas)
        super().__init__(" ".join(p.mensagem for p in problemas))

    def para_dict(self) -> dict[str, object]:
        return {"problemas": [asdict(p) for p in self.problemas]}


def _inteiro(valor: object) -> bool:
    return isinstance(valor, int) and not isinstance(valor, bool)


def _probabilidade(valor: object) -> bool:
    return (
        not isinstance(valor, bool) and isinstance(valor, (int, float))
        and 0 <= valor <= 1 and math.isfinite(valor)
    )


@dataclass(frozen=True, slots=True)
class ConfiguracaoIntervencao:
    estrategia: str
    fracao: float
    inicio: int
    mecanismo: MecanismoIsolamento
    reducao: float | None = None

    def validar(self, limite_passos: int) -> list[ProblemaConfiguracao]:
        problemas: list[ProblemaConfiguracao] = []
        if self.estrategia not in ("aleatoria", "grau"):
            problemas.append(ProblemaConfiguracao("intervencao.estrategia", "Escolha seleção aleatória ou por grau."))
        if not _probabilidade(self.fracao):
            problemas.append(ProblemaConfiguracao("intervencao.fracao", "Informe uma fração finita entre 0 e 1."))
        if not _inteiro(self.inicio) or self.inicio < 0 or (
            _inteiro(limite_passos) and limite_passos > 0 and self.inicio >= limite_passos
        ):
            problemas.append(ProblemaConfiguracao("intervencao.inicio", "Use um instante inteiro de 0 até limite de passos menos 1."))
        if not isinstance(self.mecanismo, MecanismoIsolamento):
            problemas.append(ProblemaConfiguracao("intervencao.mecanismo", "Escolha desativação, redução ou exclusão de contatos."))
        if self.mecanismo is MecanismoIsolamento.REDUCAO:
            if not _probabilidade(self.reducao):
                problemas.append(ProblemaConfiguracao("intervencao.reducao", "Informe a redução finita entre 0 e 1."))
        elif self.reducao is not None:
            problemas.append(ProblemaConfiguracao("intervencao.reducao", "Informe redução somente no mecanismo de redução."))
        return problemas

    def quantidade_isolados(self, populacao: int) -> int:
        if not _inteiro(populacao):
            raise TypeError("A população deve ser inteira.")
        if populacao <= 0 or not _probabilidade(self.fracao):
            raise ValueError("Use população positiva e fração finita entre 0 e 1.")
        numerador, denominador = Decimal(str(self.fracao)).as_integer_ratio()
        return numerador * populacao // denominador


@dataclass(frozen=True, slots=True)
class ConfiguracaoSimulacao:
    beta: float | None
    gamma: float
    semente_epidemia: int
    semente_iniciais: int
    semente_isolamento: int
    limite_passos: int
    revisao_rede: int
    ids_infectados_iniciais: tuple[int, ...] | None = None
    quantidade_infectados: int | None = None
    modo_peso: str = "intensidade"
    intervencao: ConfiguracaoIntervencao | None = None

    def validar(self, rede: RedeContatos, revisao_rede: int) -> list[ProblemaConfiguracao]:
        problemas: list[ProblemaConfiguracao] = []

        def erro(campo: str, mensagem: str) -> None:
            problemas.append(ProblemaConfiguracao(campo, mensagem))

        if not isinstance(rede, RedeContatos) or rede.numero_individuos == 0:
            erro("rede", "Confirme uma rede com pelo menos um indivíduo.")
        if (
            not _inteiro(self.revisao_rede) or self.revisao_rede <= 0
            or not _inteiro(revisao_rede) or revisao_rede != self.revisao_rede
        ):
            erro("revisao_rede", "A rede mudou ou a revisão é inválida. Valide novamente.")
        if self.modo_peso not in ("intensidade", "probabilidade"):
            erro("modo_peso", "Escolha intensidade ou probabilidade direta.")
        if self.modo_peso == "probabilidade":
            if self.beta is not None:
                erro("beta", "β não se aplica ao modo de probabilidade direta; use None.")
        elif not _probabilidade(self.beta):
            erro("beta", "Informe β finito entre 0 e 1.")
        if not _probabilidade(self.gamma):
            erro("gamma", "Informe γ finito entre 0 e 1.")
        for campo in ("semente_epidemia", "semente_iniciais", "semente_isolamento"):
            if not _inteiro(getattr(self, campo)):
                erro(campo, "Informe uma semente inteira.")
        if not _inteiro(self.limite_passos) or self.limite_passos <= 0:
            erro("limite_passos", "Informe um limite de passos inteiro positivo.")
        problemas.extend(self._validar_condicoes_iniciais(rede))
        if self.intervencao is not None:
            if not isinstance(self.intervencao, ConfiguracaoIntervencao):
                erro("intervencao", "Informe uma configuração de intervenção válida ou None.")
            else:
                problemas.extend(self.intervencao.validar(self.limite_passos))
        return problemas

    def _validar_condicoes_iniciais(self, rede: RedeContatos) -> list[ProblemaConfiguracao]:
        problemas = []

        def erro(campo: str, mensagem: str) -> None:
            problemas.append(ProblemaConfiguracao(campo, mensagem))

        ids_iniciais = self.ids_infectados_iniciais
        quantidade_sorteada = self.quantidade_infectados
        if ids_iniciais is not None:
            if not isinstance(ids_iniciais, tuple) or any(not _inteiro(id) for id in ids_iniciais):
                erro("ids_infectados_iniciais", "Informe uma tupla de IDs inteiros.")
            else:
                if len(set(ids_iniciais)) != len(ids_iniciais):
                    erro("ids_infectados_iniciais", "Não repita os IDs iniciais.")
                if isinstance(rede, RedeContatos):
                    ausentes = [id for id in ids_iniciais if rede.buscar_individuo(id) is None]
                    if ausentes:
                        erro("ids_infectados_iniciais", f"IDs inexistentes: {ausentes}.")
            if quantidade_sorteada is not None:
                erro("quantidade_infectados", "Use IDs ou quantidade para sorteio, não ambos.")
        elif (
            not _inteiro(quantidade_sorteada) or quantidade_sorteada < 0
            or (isinstance(rede, RedeContatos) and quantidade_sorteada > rede.numero_individuos)
        ):
            erro("quantidade_infectados", "Informe uma quantidade inteira entre 0 e a população.")
        return problemas

    def preparar(self, rede: RedeContatos, revisao_rede: int) -> "ConfiguracaoSimulacao":
        problemas = self.validar(rede, revisao_rede)
        if problemas:
            raise ErroConfiguracao(problemas)
        if self.ids_infectados_iniciais is not None:
            return self
        gerador = GeradorAleatorio(self.semente_iniciais)
        ids = gerador.amostrar_ids(
            [p.id for p in rede.iter_individuos()], self.quantidade_infectados,
        )
        return replace(self, ids_infectados_iniciais=ids, quantidade_infectados=None)


def aplicar_condicoes_iniciais(
    rede_execucao: RedeContatos, configuracao: ConfiguracaoSimulacao, revisao_rede: int,
) -> None:
    preparada = configuracao.preparar(rede_execucao, revisao_rede)
    if any(p.estado is not EstadoSIR.SUSCETIVEL for p in rede_execucao.iter_individuos()):
        raise ErroConfiguracao([ProblemaConfiguracao("rede", "Use uma cópia nova, com todos suscetíveis.")])
    for id_individuo in preparada.ids_infectados_iniciais:
        rede_execucao.obter_individuo(id_individuo).infectar(0)
