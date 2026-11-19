from dataclasses import asdict
import re

from simulador.carga_rede import ErroCargaRede, ProblemaCargaRede, RedeDisponivel, ServicoCargaRede
from simulador.configuracao import (
    ConfiguracaoIntervencao, ConfiguracaoSimulacao, ErroConfiguracao, ProblemaConfiguracao,
)
from simulador.isolamento import MecanismoIsolamento


def ler_configuracao(
    servico: ServicoCargaRede, campos: dict[str, object],
) -> tuple[ConfiguracaoSimulacao, RedeDisponivel, str]:
    problemas: list[ProblemaConfiguracao] = []
    falhas_conversao: set[str] = set()

    def erro(campo: str, mensagem: str) -> None:
        problemas.append(ProblemaConfiguracao(campo, mensagem))

    def falha_conversao(campo: str, mensagem: str) -> None:
        falhas_conversao.add(campo)
        erro(campo, mensagem)

    def inteiro(campo: str, valor: object, *, textual: bool = False) -> int | None:
        if not textual and isinstance(valor, int) and not isinstance(valor, bool):
            return valor
        if isinstance(valor, str) and re.fullmatch(r'[+-]?[0-9]+', valor.strip()):
            try:
                return int(valor)
            except ValueError:
                pass
        falha_conversao(campo, "Informe um inteiro válido em texto, sem casas decimais.")
        return None

    def decimal(campo: str, valor: object) -> float | None:
        if not isinstance(valor, bool) and isinstance(valor, (str, int, float)):
            try:
                return float(valor.replace(',', '.') if isinstance(valor, str) else valor)
            except (ValueError, OverflowError):
                pass
        falha_conversao(campo, "Informe um número válido; use ponto ou vírgula para as casas decimais.")
        return None

    def ler_intervencao(entrada: object) -> ConfiguracaoIntervencao | None:
        if entrada is None:
            return None
        if not isinstance(entrada, dict):
            erro('intervencao', 'Informe os campos da intervenção ou null para nenhuma.')
            return None
        for campo in entrada:
            if campo not in ('estrategia', 'fracao', 'inicio', 'mecanismo', 'reducao'):
                erro(f'intervencao.{campo}', 'Este campo não faz parte da configuração; a quantidade é derivada da fração.')
        try:
            mecanismo = MecanismoIsolamento(entrada.get('mecanismo'))
        except (TypeError, ValueError):
            mecanismo = None
            falha_conversao('intervencao.mecanismo', 'Escolha desativação, redução ou exclusão de contatos.')
        reducao = entrada.get('reducao')
        if reducao is not None:
            reducao = decimal('intervencao.reducao', reducao)
        return ConfiguracaoIntervencao(
            estrategia=entrada.get('estrategia'),
            fracao=decimal('intervencao.fracao', entrada.get('fracao')),
            inicio=inteiro('intervencao.inicio', entrada.get('inicio')),
            mecanismo=mecanismo,
            reducao=reducao,
        )

    modo = campos.get('modo_iniciais')
    permitidos = {
        'beta', 'gamma', 'modo_peso', 'modo_iniciais', 'semente_epidemia',
        'semente_iniciais', 'semente_isolamento', 'limite_passos', 'revisao_rede', 'contexto_rede', 'intervencao',
    }
    ids = None
    quantidade = None
    if modo == 'ids':
        permitidos.add('ids_infectados_iniciais')
        entrada = campos.get('ids_infectados_iniciais')
        if not isinstance(entrada, list):
            falha_conversao('ids_infectados_iniciais', 'Informe uma lista de IDs em texto.')
        else:
            ids = tuple(inteiro('ids_infectados_iniciais', id, textual=True) for id in entrada)
    elif modo == 'sorteio':
        permitidos.add('quantidade_infectados')
        quantidade = inteiro('quantidade_infectados', campos.get('quantidade_infectados'))
    else:
        erro('modo_iniciais', 'Escolha IDs ou sorteio sem reposição.')
    for campo in campos:
        if campo not in permitidos:
            erro(campo, 'Este campo não se aplica ao modo escolhido.')
    modo_peso = campos.get('modo_peso')
    beta = campos.get('beta')
    if modo_peso != 'probabilidade' or beta is not None:
        beta = decimal('beta', beta)
    intervencao = ler_intervencao(campos.get('intervencao'))
    cfg = ConfiguracaoSimulacao(
        beta=beta, gamma=decimal('gamma', campos.get('gamma')),
        semente_epidemia=inteiro('semente_epidemia', campos.get('semente_epidemia'), textual=True),
        semente_iniciais=inteiro('semente_iniciais', campos.get('semente_iniciais'), textual=True),
        semente_isolamento=inteiro('semente_isolamento', campos.get('semente_isolamento'), textual=True),
        limite_passos=inteiro('limite_passos', campos.get('limite_passos')),
        revisao_rede=inteiro('revisao_rede', campos.get('revisao_rede')),
        ids_infectados_iniciais=ids, quantidade_infectados=quantidade, modo_peso=modo_peso,
        intervencao=intervencao,
    )
    if cfg.revisao_rede is None:
        raise ErroConfiguracao(problemas)
    if 'contexto_rede' in campos and campos['contexto_rede'] != servico.contexto_rede:
        raise ErroCargaRede((ProblemaCargaRede(
            'revisao', 'A rede mudou. Atualize a inspeção e valide novamente.',
        ),))
    disponivel = servico.obter_rede_confirmada(cfg.revisao_rede)
    problemas.extend(
        problema for problema in cfg.validar(disponivel.rede, disponivel.revisao)
        if problema.campo not in falhas_conversao
    )
    if problemas:
        raise ErroConfiguracao(list(dict.fromkeys(problemas)))
    return cfg, disponivel, modo


def validar_formulario(servico: ServicoCargaRede, campos: dict[str, object]) -> dict[str, object]:
    cfg, disponivel, modo = ler_configuracao(servico, campos)
    preparada = cfg.preparar(disponivel.rede, disponivel.revisao)
    resumo = asdict(preparada)
    resumo['ids_infectados_iniciais'] = [str(id) for id in preparada.ids_infectados_iniciais]
    for campo in ('semente_epidemia', 'semente_iniciais', 'semente_isolamento'):
        resumo[campo] = str(resumo[campo])
    if preparada.intervencao is not None:
        resumo['intervencao']['mecanismo'] = preparada.intervencao.mecanismo.value
        resumo['intervencao']['quantidade_isolados'] = preparada.intervencao.quantidade_isolados(disponivel.rede.numero_individuos)
    return {
        'configuracao': resumo, 'populacao': disponivel.rede.numero_individuos,
        'modo_iniciais': modo, 'origem_rede': disponivel.origem, 'contexto_rede': servico.contexto_rede,
    }
