import re

from simulador.carga_rede import ServicoCargaRede
from simulador.comparacao import CENARIOS, PedidoComparacao
from simulador.configuracao import ErroConfiguracao, ProblemaConfiguracao
from simulador.configuracao_api import ler_configuracao


def _ler_repeticoes(valor: object) -> int:
    if type(valor) is int and valor > 0:
        return valor
    if isinstance(valor, str) and re.fullmatch(r'[0-9]+', valor.strip()):
        try:
            repeticoes = int(valor)
        except ValueError:
            repeticoes = 0
        if repeticoes > 0:
            return repeticoes
    raise ErroConfiguracao([ProblemaConfiguracao('repeticoes', 'Informe um número inteiro positivo de repetições.')])


def validar_comparacao(servico: ServicoCargaRede, campos: dict[str, object]) -> dict[str, object]:
    problemas = [
        ProblemaConfiguracao(campo, 'Este campo não faz parte da comparação.')
        for campo in campos if campo not in ('configuracao', 'repeticoes')
    ]
    if problemas:
        raise ErroConfiguracao(problemas)
    entrada = campos.get('configuracao')
    if not isinstance(entrada, dict):
        raise ErroConfiguracao([ProblemaConfiguracao('configuracao', 'Informe os parâmetros da comparação.')])
    repeticoes = _ler_repeticoes(campos.get('repeticoes'))
    configuracao, referencia, modo = ler_configuracao(servico, entrada)
    intervencao = PedidoComparacao(configuracao, repeticoes).validar(referencia)
    ids_manuais = configuracao.ids_infectados_iniciais
    populacao = referencia.rede.numero_individuos
    return {
        'repeticoes': str(repeticoes),
        'cenarios': list(CENARIOS),
        'revisao_rede': referencia.revisao,
        'contexto_rede': servico.contexto_rede,
        'limite_passos': configuracao.limite_passos,
        'populacao': populacao,
        'modo_iniciais': modo,
        'quantidade_infectados': (
            len(ids_manuais) if ids_manuais is not None else configuracao.quantidade_infectados
        ),
        'quantidade_isolados': intervencao.quantidade_isolados(populacao),
        'intervencao': {
            'fracao': intervencao.fracao,
            'inicio': intervencao.inicio,
            'mecanismo': intervencao.mecanismo.value,
            'reducao': intervencao.reducao,
        },
        'sementes_base': {
            'epidemia': str(configuracao.semente_epidemia),
            'iniciais': str(configuracao.semente_iniciais),
            'isolamento': str(configuracao.semente_isolamento),
        },
        'execucao_disponivel': False,
    }
