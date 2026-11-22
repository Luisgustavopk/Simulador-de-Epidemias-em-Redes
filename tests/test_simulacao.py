"""Orquestração temporal e registros SIR."""

import pytest

from simulador import (
    EstadoSIR,
    Individuo,
    RedeContatos,
    RegistroPasso,
    Simulacao,
)
from simulador.configuracao import ConfiguracaoIntervencao, ConfiguracaoSimulacao
from simulador.isolamento import MecanismoIsolamento


@pytest.fixture
def rede() -> RedeContatos:
    rede = RedeContatos()
    rede.adicionar_individuo(Individuo(0))
    rede.adicionar_individuo(Individuo(1))
    rede.adicionar_individuo(Individuo(2))
    rede.obter_individuo(1).infectar(passo=0)
    rede.obter_individuo(2).isolar()
    return rede


def test_registro_passo_aceita_sir_e_expoe_aliases() -> None:
    registro = RegistroPasso(passo=2, s=4, i=3, r=1, isolados=2)

    assert registro.passo == 2
    assert registro.suscetiveis == registro.s == 4
    assert registro.infectados == registro.i == 3
    assert registro.recuperados == registro.r == 1
    assert registro.isolados == 2


def test_execucao_registra_estado_inicial_isolados_e_limite(
    rede: RedeContatos,
) -> None:
    simulacao = Simulacao(rede, limite_passos=2)

    assert simulacao.passo_atual == 0
    assert simulacao.historico[0].suscetiveis == 2
    assert simulacao.historico[0].infectados == 1
    assert simulacao.historico[0].recuperados == 0
    assert simulacao.historico[0].isolados == 1

    historico = simulacao.executar()

    assert [registro.passo for registro in historico] == [0, 1, 2]
    assert simulacao.finalizada is True
    assert simulacao.passo_atual == 2


def test_extincao_finaliza_sem_avancar_o_relogio() -> None:
    rede = RedeContatos()
    rede.adicionar_individuo(Individuo(0))

    simulacao = Simulacao(rede)
    registro = simulacao.avancar()

    assert simulacao.isFinalizada()
    assert registro.passo == 0
    assert registro.infectados == 0
    assert len(simulacao.historico) == 1


def test_executar_motor_concentra_evolucao_e_parada(rede: RedeContatos) -> None:
    class MotorFalso:
        def avancar(self, rede, configuracao, passo_atual, *, revisao_rede):
            rede.obter_individuo(1).recuperar()

    class ConfiguracaoFalsa:
        intervencao = None

    simulacao = Simulacao(rede, limite_passos=2)
    historico = simulacao.executar_motor(
        MotorFalso(),
        ConfiguracaoFalsa(),
        revisao_rede=1,
    )

    assert historico[-1].infectados == 0


def test_configuracao_executa_motor_e_entrega_resultado_independente():
    from dataclasses import FrozenInstanceError
    from simulador import ResultadoSimulacao
    from simulador.configuracao import ConfiguracaoSimulacao

    rede = RedeContatos()
    for identificador in (1, 2, 3):
        rede.adicionar_individuo(Individuo(identificador))
    rede.adicionar_contato(1, 2)
    rede.adicionar_contato(2, 3)
    configuracao = ConfiguracaoSimulacao(1.0, 1.0, 42, 43, 44, 10, 1, (1,))
    simulacao = Simulacao(rede, configuracao)

    resultado = simulacao.executar()

    assert isinstance(resultado, ResultadoSimulacao)
    assert resultado.motivo_termino == 'extincao'
    assert [registro.infectados for registro in resultado.historico] == [1, 1, 1, 0]
    assert resultado.metricas.fracao_final_recuperados == 1.0
    assert resultado.configuracao == configuracao
    assert simulacao.executar() is resultado
    assert all(pessoa.estado is EstadoSIR.SUSCETIVEL for pessoa in rede.individuos)
    with pytest.raises(FrozenInstanceError):
        resultado.populacao_inicial = 4


@pytest.mark.parametrize('inicio', [0, 1, 2])
def test_configuracao_respeita_agendamento_e_extincao(inicio):
    from simulador.configuracao import ConfiguracaoSimulacao, ConfiguracaoIntervencao
    from simulador.isolamento import MecanismoIsolamento

    rede = RedeContatos()
    rede.adicionar_individuo(Individuo(1))
    configuracao = ConfiguracaoSimulacao(0.0, 1.0, 42, 43, 44, 3, 1, (1,),
        intervencao=ConfiguracaoIntervencao('grau', 1.0, inicio, MecanismoIsolamento.DESATIVACAO))

    resultado = Simulacao(rede, configuracao).executar()

    assert resultado.historico[0].isolados == (1 if inicio == 0 else 0)
    assert resultado.historico[-1].isolados == (1 if inicio == 0 else 0)
    assert resultado.horizonte_observado == 1
    assert not rede.obter_individuo(1).isolamento


def test_intervencao_futura_nao_antecipa_isolamento_nem_recupera_no_limite():
    from simulador.configuracao import ConfiguracaoSimulacao, ConfiguracaoIntervencao
    from simulador.isolamento import MecanismoIsolamento

    rede = RedeContatos()
    rede.adicionar_individuo(Individuo(1))
    configuracao = ConfiguracaoSimulacao(0.0, 0.0, 42, 43, 44, 3, 1, (1,),
        intervencao=ConfiguracaoIntervencao('grau', 1.0, 1, MecanismoIsolamento.DESATIVACAO))

    resultado = Simulacao(rede, configuracao).executar()

    assert [registro.isolados for registro in resultado.historico] == [0, 1, 1, 1]
    assert resultado.motivo_termino == 'limite_passos'
    assert resultado.historico[-1].infectados == 1
    assert resultado.historico[-1].recuperados == 0


@pytest.mark.parametrize("mecanismo", list(MecanismoIsolamento))
@pytest.mark.parametrize("legada", [False, True])
def test_intervencao_em_um_consta_no_registro_e_bloqueia_proxima_transicao(
    mecanismo: MecanismoIsolamento, legada: bool,
) -> None:
    from simulador.aleatoriedade import GeradorAleatorio
    from simulador.configuracao import aplicar_condicoes_iniciais
    from simulador.estrategias_isolamento import preparar_estrategia
    from simulador.motor_sir import MotorSIR

    rede = RedeContatos()
    for identificador in range(3):
        rede.adicionar_individuo(Individuo(identificador))
    rede.adicionar_contato(0, 1)
    rede.adicionar_contato(1, 2)
    configuracao = ConfiguracaoSimulacao(
        1.0, 0.0, 42, 43, 44, 3, 1, (0,),
        intervencao=ConfiguracaoIntervencao(
            "grau", 0.34, 1, mecanismo,
            reducao=1.0 if mecanismo is MecanismoIsolamento.REDUCAO else None,
        ),
    )
    if legada:
        aplicar_condicoes_iniciais(rede, configuracao, 1)
        estrategia = preparar_estrategia(rede, configuracao, revisao_rede=1)
        simulacao = Simulacao(rede, limite_passos=3)
    else:
        simulacao = Simulacao(rede, configuracao)
    registro_inicial = simulacao.registros[0]

    if legada:
        historico = simulacao.executar_motor(
            MotorSIR(GeradorAleatorio(42)), configuracao, 1, estrategia,
        )
    else:
        historico = simulacao.executar().historico

    assert historico == (
        RegistroPasso(0, 2, 1, 0, 0),
        RegistroPasso(1, 1, 2, 0, 1),
        RegistroPasso(2, 1, 2, 0, 1),
        RegistroPasso(3, 1, 2, 0, 1),
    )
    assert historico[0] is registro_inicial
    assert [p.id for p in simulacao.rede.individuos if p.isolamento] == [1]


@pytest.mark.parametrize("mecanismo", list(MecanismoIsolamento))
@pytest.mark.parametrize("estrategia", ["grau", "aleatoria"])
def test_sem_infectados_nao_aplica_intervencao_em_zero(
    mecanismo: MecanismoIsolamento, estrategia: str,
) -> None:
    rede = RedeContatos()
    rede.adicionar_individuo(Individuo(0))
    rede.adicionar_individuo(Individuo(1))
    rede.adicionar_contato(0, 1, peso=0.8)
    configuracao = ConfiguracaoSimulacao(
        1.0, 0.0, 42, 43, 44, 3, 1, (),
        intervencao=ConfiguracaoIntervencao(
            estrategia, 1.0, 0, mecanismo,
            reducao=0.5 if mecanismo is MecanismoIsolamento.REDUCAO else None,
        ),
    )
    simulacao = Simulacao(rede, configuracao)

    resultado = simulacao.executar()

    assert resultado.historico == (RegistroPasso(0, 2, 0, 0, 0),)
    assert resultado.motivo_termino == "extincao"
    assert simulacao.executar_passo() is resultado.historico[0]
    assert not any(p.isolamento for p in simulacao.rede.individuos)
    contato = simulacao.rede.obter_contato(0, 1)
    assert contato.ativa and contato.peso == 0.8
    assert simulacao.inicializar() == list(resultado.historico)
    assert simulacao.executar().historico == resultado.historico


@pytest.fixture
def rede_suscetivel() -> RedeContatos:
    rede = RedeContatos()
    for identificador in range(8):
        rede.adicionar_individuo(Individuo(identificador))
    for identificador in range(8):
        rede.adicionar_contato(identificador, (identificador + 1) % 8, peso=0.8)
    rede.adicionar_contato(0, 4, peso=0.6)
    return rede


def retrato_rede(rede: RedeContatos) -> tuple[tuple, tuple]:
    pessoas = tuple(
        (pessoa.id, pessoa.estado, pessoa.isolamento, pessoa.dia_inicio_infeccao)
        for pessoa in rede.individuos
    )
    contatos = tuple(sorted(
        (contato.origem.id, contato.destino.id, contato.peso, contato.ativa)
        for contato in rede.contatos
    ))
    return pessoas, contatos


@pytest.mark.parametrize("metodo", ["avancar", "executar_passo"])
def test_avanco_configurado_atualiza_sir_uma_vez_por_passo(metodo: str) -> None:
    rede = RedeContatos()
    for identificador in (1, 2, 3):
        rede.adicionar_individuo(Individuo(identificador))
    rede.adicionar_contato(1, 2)
    rede.adicionar_contato(2, 3)
    configuracao = ConfiguracaoSimulacao(1.0, 1.0, 42, 43, 44, 10, 1, (1,))
    simulacao = Simulacao(rede, configuracao)
    avancar = getattr(simulacao, metodo)

    assert avancar() == RegistroPasso(1, 1, 1, 1)
    assert avancar() == RegistroPasso(2, 0, 1, 2)
    assert avancar() == RegistroPasso(3, 0, 0, 3)
    assert simulacao.finalizada
    assert avancar() is simulacao.registros[-1]
    assert len(simulacao.registros) == 4
    assert all(pessoa.estado is EstadoSIR.SUSCETIVEL for pessoa in rede.individuos)


@pytest.mark.parametrize("semente", [7, 42, 1337])
@pytest.mark.parametrize("passos_manuais", [1, 3])
def test_execucao_apos_passos_preserva_sorteios_e_agendamento(
    rede_suscetivel: RedeContatos, semente: int, passos_manuais: int,
) -> None:
    configuracao = ConfiguracaoSimulacao(
        0.55, 0.25, semente, 43, 44, 12, 1, (0, 3),
        intervencao=ConfiguracaoIntervencao(
            "aleatoria", 0.5, 2, MecanismoIsolamento.REDUCAO, reducao=0.5,
        ),
    )
    referencia = Simulacao(rede_suscetivel, configuracao).executar()
    simulacao = Simulacao(rede_suscetivel, configuracao)

    for _ in range(passos_manuais):
        simulacao.avancar()
    resultado = simulacao.executar()

    assert resultado.historico == referencia.historico
    assert resultado.metricas.gerar_resumo() == referencia.metricas.gerar_resumo()
    assert resultado.motivo_termino == referencia.motivo_termino
    assert simulacao.executar() is resultado


@pytest.mark.parametrize("inicio", [0, 1, 2])
def test_avanco_manual_aplica_intervencao_no_inicio_do_passo(inicio: int) -> None:
    rede = RedeContatos()
    rede.adicionar_individuo(Individuo(1))
    configuracao = ConfiguracaoSimulacao(
        0.0, 0.0, 42, 43, 44, 4, 1, (1,),
        intervencao=ConfiguracaoIntervencao(
            "grau", 1.0, inicio, MecanismoIsolamento.DESATIVACAO,
        ),
    )
    simulacao = Simulacao(rede, configuracao)

    for _ in range(5):
        simulacao.executar_passo()

    assert [registro.isolados for registro in simulacao.registros] == [
        int(passo >= inicio) for passo in range(5)
    ]
    assert simulacao.passo == 4
    assert all(registro.infectados == 1 for registro in simulacao.registros)


@pytest.mark.parametrize("mecanismo", list(MecanismoIsolamento))
@pytest.mark.parametrize("inicio", [0, 2])
@pytest.mark.parametrize("concluir", [False, True])
def test_reinicializacao_restaura_rede_e_sorteios_da_intervencao(
    rede_suscetivel: RedeContatos,
    mecanismo: MecanismoIsolamento,
    inicio: int,
    concluir: bool,
) -> None:
    configuracao = ConfiguracaoSimulacao(
        0.6, 0.0, 42, 43, 44, 6, 1, quantidade_infectados=2,
        intervencao=ConfiguracaoIntervencao(
            "aleatoria", 0.5, inicio, mecanismo,
            reducao=0.5 if mecanismo is MecanismoIsolamento.REDUCAO else None,
        ),
    )
    retrato_original = retrato_rede(rede_suscetivel)
    simulacao = Simulacao(rede_suscetivel, configuracao)
    registro_inicial = simulacao.registros[0]
    retrato_inicial = retrato_rede(simulacao.rede)
    controle = Simulacao(rede_suscetivel, configuracao)
    esperado = controle.executar()
    if concluir:
        resultado_anterior = simulacao.executar()
    else:
        for _ in range(3):
            simulacao.avancar()
        resultado_anterior = None
    rede_anterior = simulacao.rede
    historico_anterior = simulacao.registros

    historico_reiniciado = simulacao.inicializar()

    assert historico_reiniciado == [registro_inicial]
    assert simulacao.passo == 0
    assert not simulacao.finalizada
    assert simulacao.rede is not rede_anterior
    assert retrato_rede(simulacao.rede) == retrato_inicial
    resultado = simulacao.executar()
    assert resultado is not resultado_anterior
    assert resultado.configuracao == esperado.configuracao
    assert resultado.historico == esperado.historico
    assert resultado.metricas.gerar_resumo() == esperado.metricas.gerar_resumo()
    assert retrato_rede(simulacao.rede) == retrato_rede(controle.rede)
    assert retrato_rede(rede_suscetivel) == retrato_original
    if resultado_anterior is not None:
        assert resultado_anterior.historico == historico_anterior


def test_reinicializacao_apos_extincao_reaplica_infectados_iniciais() -> None:
    rede = RedeContatos()
    rede.adicionar_individuo(Individuo(1))
    configuracao = ConfiguracaoSimulacao(0.0, 1.0, 42, 43, 44, 3, 1, (1,))
    simulacao = Simulacao(rede, configuracao)
    resultado_anterior = simulacao.executar()

    assert simulacao.inicializar() == [RegistroPasso(0, 0, 1, 0)]
    assert not simulacao.finalizada
    resultado = simulacao.executar()

    assert resultado is not resultado_anterior
    assert resultado.historico == resultado_anterior.historico
    assert resultado.motivo_termino == "extincao"


def test_reinicializacao_usa_retrato_independente_da_rede_recebida() -> None:
    rede = RedeContatos()
    rede.adicionar_individuo(Individuo(1))
    rede.adicionar_individuo(Individuo(2))
    rede.adicionar_contato(1, 2)
    configuracao = ConfiguracaoSimulacao(1.0, 1.0, 42, 43, 44, 3, 1, (1,))
    simulacao = Simulacao(rede, configuracao)
    esperado = simulacao.executar()
    rede.remover_contato(1, 2)
    rede.obter_individuo(2).infectar(0)

    simulacao.inicializar()
    resultado = simulacao.executar()

    assert resultado.historico == esperado.historico
    assert simulacao.rede.numero_contatos == 1
    assert rede.numero_contatos == 0
    assert rede.obter_individuo(2).estado is EstadoSIR.INFECTADO


def test_reinicializacao_do_registrador_restaura_estados_e_contatos(
    rede: RedeContatos,
) -> None:
    rede.adicionar_contato(0, 1, peso=0.8)
    simulacao = Simulacao(rede, limite_passos=2)
    retrato_inicial = retrato_rede(simulacao.rede)
    rede.obter_individuo(1).recuperar()
    rede.desativar_contato(0, 1)
    rede.alterar_peso_contato(0, 1, 0.2)
    simulacao.avancar()

    assert simulacao.inicializar() == [RegistroPasso(0, 2, 1, 0, 1)]
    assert retrato_rede(simulacao.rede) == retrato_inicial
    assert not simulacao.finalizada
    assert simulacao.rede is not rede
