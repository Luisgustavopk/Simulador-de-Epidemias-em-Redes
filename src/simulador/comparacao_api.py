import re

from simulador.aleatoriedade import GeradorAleatorio
from simulador.comparacao import (
    CENARIOS,
    PedidoComparacao,
    ResultadoIndividual,
    executar_comparacao,
)
from simulador.configuracao import aplicar_condicoes_iniciais
from simulador.estrategias_isolamento import preparar_estrategia
from simulador.isolamento import aplicar_isolamento
from simulador.metricas import MetricasEpidemia
from simulador.motor_sir import MotorSIR
from simulador.simulacao import Simulacao

from simulador.carga_rede import ServicoCargaRede
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


def _serializar_historico(historico):
    return [
        {
            'passo': registro.passo,
            'suscetiveis': registro.suscetiveis,
            'infectados': registro.infectados,
            'recuperados': registro.recuperados,
            'isolados': registro.isolados,
        }
        for registro in historico
    ]


def _executar_individual(referencia, configuracao) -> ResultadoIndividual:
    rede = referencia.copiar()
    preparada = configuracao.preparar(rede, referencia.revisao)
    aplicar_condicoes_iniciais(rede, preparada, referencia.revisao)

    estrategia = preparar_estrategia(rede, preparada, revisao_rede=referencia.revisao)
    intervencao = preparada.intervencao
    if intervencao is not None and intervencao.inicio == 0:
        if estrategia is not None:
            ids = estrategia.selecionar(rede, intervencao.quantidade_isolados(rede.numero_individuos))
            aplicar_isolamento(
                rede, ids, intervencao.mecanismo,
                orcamento=intervencao.quantidade_isolados(rede.numero_individuos),
                reducao=intervencao.reducao,
            )

    simulado = Simulacao(rede, configuracao.limite_passos)
    motor = MotorSIR(GeradorAleatorio(configuracao.semente_epidemia))
    while not simulado.finalizada:
        passo = simulado.passo + 1
        if intervencao is not None and passo == intervencao.inicio and passo > 0:
            if estrategia is not None:
                ids = estrategia.selecionar(rede, intervencao.quantidade_isolados(rede.numero_individuos))
                aplicar_isolamento(
                    rede, ids, intervencao.mecanismo,
                    orcamento=intervencao.quantidade_isolados(rede.numero_individuos),
                    reducao=intervencao.reducao,
                )
        motor.avancar(rede, configuracao, passo - 1, revisao_rede=referencia.revisao)
        simulado.executar_passo()
        if simulado.passo >= configuracao.limite_passos:
            break

    historico = simulado.registros
    metricas = MetricasEpidemia(list(historico), rede.numero_individuos)
    registro_final = historico[-1]
    return ResultadoIndividual(
        populacao_inicial=referencia.rede.numero_individuos,
        pico_infectados=metricas.pico_infectados,
        passo_pico=metricas.passo_pico,
        fracao_acumulada=metricas.taxa_ataque,
        horizonte_observado=registro_final.passo,
        duracao_extincao=(
            metricas.duracao_surto if registro_final.infectados == 0 else None
        ),
        motivo_termino='extincao' if registro_final.infectados == 0 else 'limite_passos',
        historico=historico,
    )


def executar_simulacao_api(servico: ServicoCargaRede, campos: dict[str, object]) -> dict[str, object]:
    configuracao, referencia, _ = ler_configuracao(servico, campos)
    resultado = _executar_individual(referencia, configuracao)
    historico = _serializar_historico(resultado.historico)
    return {
        'contexto_rede': servico.contexto_rede,
        'revisao_rede': referencia.revisao,
        'populacao': resultado.populacao_inicial,
        'metrica': {
            'pico_infectados': resultado.pico_infectados,
            'passo_pico': resultado.passo_pico,
            'pico_proporcional': resultado.pico_proporcional,
            'fracao_acumulada': resultado.fracao_acumulada,
            'horizonte_observado': resultado.horizonte_observado,
            'duracao_extincao': resultado.duracao_extincao,
        },
        'historico': historico,
    }


def executar_comparacao_api(servico: ServicoCargaRede, campos: dict[str, object]) -> dict[str, object]:
    if set(campos) != {'repeticoes', 'configuracao'}:
        raise ErroConfiguracao([
            ProblemaConfiguracao(campo, 'Este campo não faz parte da comparação.')
            for campo in campos if campo not in ('configuracao', 'repeticoes')
        ])
    entrada = campos.get('configuracao')
    if not isinstance(entrada, dict):
        raise ErroConfiguracao([ProblemaConfiguracao('configuracao', 'Informe os parâmetros da comparação.')])
    repeticoes = _ler_repeticoes(campos.get('repeticoes'))
    configuracao, referencia, _ = ler_configuracao(servico, entrada)
    resultado = executar_comparacao(
        referencia,
        PedidoComparacao(configuracao, repeticoes),
        lambda rede, cfg: _executar_individual(
            type('ReferenciaExecucao', (), {
                'rede': rede,
                'revisao': referencia.revisao,
                'copiar': lambda self: rede.copiar(),
                'origem': referencia.origem,
            })(),
            cfg,
        ),
    )
    execucoes = [
        {
            'repeticao': execucao.repeticao,
            'cenario': execucao.cenario,
            'metrica': {
                'pico_infectados': execucao.resultado.pico_infectados,
                'passo_pico': execucao.resultado.passo_pico,
                'pico_proporcional': execucao.resultado.pico_proporcional,
                'fracao_acumulada': execucao.resultado.fracao_acumulada,
                'horizonte_observado': execucao.resultado.horizonte_observado,
                'duracao_extincao': execucao.resultado.duracao_extincao,
            },
            'historico': _serializar_historico(execucao.resultado.historico),
        }
        for execucao in resultado.execucoes
    ]
    return {
        'contexto_rede': servico.contexto_rede,
        'revisao_rede': referencia.revisao,
        'populacao': referencia.rede.numero_individuos,
        'execucoes': execucoes,
        'resumo': {
            cenario: {
                'censuradas': resumo.censuradas,
                'proporcao_censuradas': resumo.proporcao_censuradas,
            }
            for cenario, resumo in resultado.resumo.items()
        },
    }
