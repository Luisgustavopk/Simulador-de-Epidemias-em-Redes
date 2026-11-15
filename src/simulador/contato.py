"""Contato não direcionado com intensidade normalizada e extremos estáveis."""

from simulador.individuo import Individuo


class Contato:
    """Ligação entre duas pessoas distintas, com peso normalizado em [0, 1].

    Os extremos e o peso são somente leitura. A disponibilidade é consultada
    a partir do isolamento dos extremos, sem alterar a intensidade original.
    A rede valida o cadastro das pessoas e a unicidade do par ao conectar.
    """

    __slots__ = ("_origem", "_destino", "_peso")

    def __init__(
        self, origem: Individuo, destino: Individuo, peso: float = 1.0
    ) -> None:
        """Valida os extremos e um peso numérico finito antes de criar o contato.

        Args:
            origem: Um dos indivíduos do contato, sem indicar direção.
            destino: O outro indivíduo, com identificador diferente.
            peso: Intensidade normalizada entre zero e um, inclusive.

        Raises:
            TypeError: Se os extremos ou o peso tiverem tipos incompatíveis.
            ValueError: Se houver laço ou o peso estiver fora de [0, 1].
        """
        if not isinstance(origem, Individuo) or not isinstance(destino, Individuo):
            raise TypeError("Os extremos do contato devem ser indivíduos.")
        if origem.id == destino.id:
            raise ValueError("Um contato não pode ligar um indivíduo a ele mesmo.")
        if isinstance(peso, bool) or not isinstance(peso, (int, float)):
            raise TypeError("O peso do contato deve ser um número real.")
        if not 0 <= peso <= 1:
            raise ValueError("O peso deve ser finito e estar entre 0 e 1.")
        self._origem, self._destino, self._peso = origem, destino, float(peso)

    @property
    def origem(self) -> Individuo:
        """Uma das pessoas do contato, preservando sua identidade."""
        return self._origem

    @property
    def destino(self) -> Individuo:
        """A outra pessoa do contato, sem atribuir orientação à ligação."""
        return self._destino

    @property
    def extremos(self) -> frozenset[Individuo]:
        """Os dois extremos em uma coleção que não permite troca de pessoas."""
        return frozenset((self._origem, self._destino))

    @property
    def peso(self) -> float:
        """Intensidade finita normalizada, inclusive zero e um."""
        return self._peso

    @property
    def ativa(self) -> bool:
        """Indica se nenhum extremo está isolado, independentemente do peso."""
        return not (self._origem.isolamento or self._destino.isolamento)

    def outro_extremo(self, individuo: Individuo) -> Individuo:
        """Consulta pelo próprio objeto, rejeitando cópias com o mesmo ID."""
        if not isinstance(individuo, Individuo):
            raise TypeError("O extremo deve ser uma instância de Individuo.")
        if individuo is self._origem:
            return self._destino
        if individuo is self._destino:
            return self._origem
        raise ValueError("O indivíduo informado não pertence a este contato.")
