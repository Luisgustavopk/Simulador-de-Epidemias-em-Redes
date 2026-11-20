"""Equivalência estocástica e trabalho evitado pelas otimizações do ciclo."""

from dataclasses import replace

import pytest

from simulador.aleatoriedade import GeradorAleatorio
from simulador.carga_rede import ServicoCargaRede
from simulador.comparacao_api import executar_comparacao_api, executar_simulacao_api
from simulador.configuracao import ConfiguracaoSimulacao, ErroConfiguracao
from simulador.individuo import EstadoSIR, Individuo
from simulador.isolamento import MecanismoIsolamento, aplicar_isolamento
from simulador.motor_sir import MotorSIR
from simulador.rede_contatos import RedeContatos
from simulador.simulacao import Simulacao


def rede_exemplo() -> RedeContatos:
    rede = RedeContatos()
    for identificador in (9007199254740993, 8, -7, 2, 14, 0):
        rede.adicionar_individuo(Individuo(identificador))
    for origem, destino, peso in (
        (0, -7, 0.2), (0, 8, 0.8), (0, 2, 1.0), (2, 14, 0.5),
        (8, 14, 0.3), (14, 9007199254740993, 0.6),
    ):
        rede.adicionar_contato(origem, destino, peso)
    return rede


def avancar_referencia(rede, configuracao, passo, gerador) -> None:
    """Mantém o algoritmo anterior sem cache como oráculo de compatibilidade."""
    pessoas = sorted(rede.iter_individuos(), key=lambda pessoa: pessoa.id)
    estados = {pessoa.id: pessoa.estado for pessoa in pessoas}
    infectados = []
    recuperados = []
    for pessoa in pessoas:
        if estados[pessoa.id] is EstadoSIR.SUSCETIVEL:
            probabilidade = 0.0
            contatos = sorted(
                rede.contatos_de(pessoa),
                key=lambda contato: contato.outro_extremo(pessoa).id,
            )
            for contato in contatos:
                vizinho = contato.outro_extremo(pessoa)
                if not contato.ativa or estados[vizinho.id] is not EstadoSIR.INFECTADO:
                    continue
                transmissao = contato.peso
                if configuracao.modo_peso == "intensidade":
                    transmissao *= configuracao.beta
                probabilidade += (1 - probabilidade) * transmissao
            if gerador.uniforme() < probabilidade:
                infectados.append(pessoa.id)
        elif estados[pessoa.id] is EstadoSIR.INFECTADO:
            if gerador.uniforme() < configuracao.gamma:
                recuperados.append(pessoa.id)
    for identificador in infectados:
        rede.obter_individuo(identificador).infectar(passo + 1)
    for identificador in recuperados:
        rede.obter_individuo(identificador).recuperar()


@pytest.mark.parametrize("semente", [42, 1337])
@pytest.mark.parametrize("modo", ["intensidade", "probabilidade"])
@pytest.mark.parametrize("mecanismo", list(MecanismoIsolamento))
def test_motor_preparado_preserva_trajetoria_e_consumo_de_sorteios(
    semente: int, modo: str, mecanismo: MecanismoIsolamento,
) -> None:
    rede = rede_exemplo()
    rede.obter_individuo(0).infectar(0)
    rede.obter_individuo(14).infectar(0)
    referencia = rede.copiar()
    configuracao = ConfiguracaoSimulacao(
        0.4 if modo == "intensidade" else None,
        0.2, semente, 43, 44, 12, 1, (), modo_peso=modo,
    )
    gerador = GeradorAleatorio(semente)
    controle = GeradorAleatorio(semente)
    motor = MotorSIR(gerador)

    for passo in range(12):
        if passo == 2:
            for atual in (rede, referencia):
                aplicar_isolamento(
                    atual, (8,), mecanismo, orcamento=1,
                    reducao=0.4 if mecanismo is MecanismoIsolamento.REDUCAO else None,
                )
        motor.avancar(rede, configuracao, passo, revisao_rede=1)
        avancar_referencia(referencia, configuracao, passo, controle)
        assert [
            (pessoa.id, pessoa.estado, pessoa.dia_inicio_infeccao)
            for pessoa in rede.individuos
        ] == [
            (pessoa.id, pessoa.estado, pessoa.dia_inicio_infeccao)
            for pessoa in referencia.individuos
        ]
    assert gerador.uniforme() == controle.uniforme()


def test_motor_reutiliza_ordenacoes_e_validacao_na_rede_estavel(monkeypatch) -> None:
    rede = rede_exemplo()
    rede.obter_individuo(0).infectar(0)
    configuracao = ConfiguracaoSimulacao(0.0, 0.0, 42, 43, 44, 10, 1, ())
    motor = MotorSIR(GeradorAleatorio(42))
    motor.avancar(rede, configuracao, 0, revisao_rede=1)
    monkeypatch.setattr(rede, "contatos_de", lambda *_: pytest.fail("Ordenação repetida."))
    monkeypatch.setattr(
        ConfiguracaoSimulacao, "validar",
        lambda *_: pytest.fail("Validação integral repetida."),
    )

    motor.avancar(rede, configuracao, 1, revisao_rede=1)

    assert rede.obter_individuo(0).estado is EstadoSIR.INFECTADO


@pytest.mark.parametrize("alteracao", ["substituir", "desconectar", "adicionar"])
def test_motor_invalida_cache_apos_mudanca_estrutural(alteracao: str) -> None:
    rede = rede_exemplo()
    rede.obter_individuo(0).infectar(0)
    referencia = rede.copiar()
    configuracao = ConfiguracaoSimulacao(0.8, 0.0, 42, 43, 44, 10, 1, ())
    gerador = GeradorAleatorio(42)
    controle = GeradorAleatorio(42)
    motor = MotorSIR(gerador)
    motor.avancar(rede, configuracao, 0, revisao_rede=1)
    avancar_referencia(referencia, configuracao, 0, controle)
    for atual in (rede, referencia):
        if alteracao == "substituir":
            atual.remover_contato(0, -7)
            atual.adicionar_contato(0, 9007199254740993)
        elif alteracao == "desconectar":
            atual.desconectar_individuo(0)
        else:
            atual.adicionar_individuo(Individuo(99))
            atual.adicionar_contato(0, 99)

    motor.avancar(rede, configuracao, 1, revisao_rede=1)
    avancar_referencia(referencia, configuracao, 1, controle)

    assert [pessoa.estado for pessoa in rede.individuos] == [
        pessoa.estado for pessoa in referencia.individuos
    ]
    assert gerador.uniforme() == controle.uniforme()


def test_motor_preparado_revalida_configuracao_revisao_e_rede() -> None:
    rede = rede_exemplo()
    configuracao = ConfiguracaoSimulacao(0.0, 0.0, 42, 43, 44, 10, 1, ())
    gerador = GeradorAleatorio(42)
    motor = MotorSIR(gerador)
    motor.avancar(rede, configuracao, 0, revisao_rede=1)
    for revisao_invalida in (2, True, 1.0):
        with pytest.raises(ErroConfiguracao):
            motor.avancar(rede, configuracao, 1, revisao_rede=revisao_invalida)
    with pytest.raises(ErroConfiguracao):
        motor.avancar(rede, replace(configuracao, gamma=2.0), 1, revisao_rede=1)
    outra = rede_exemplo()
    outra.obter_individuo(0).infectar(0)
    motor.avancar(outra, replace(configuracao, gamma=1.0), 1, revisao_rede=1)
    assert outra.obter_individuo(0).estado is EstadoSIR.RECUPERADO
    assert all(pessoa.estado is EstadoSIR.SUSCETIVEL for pessoa in rede.individuos)
    controle = GeradorAleatorio(42)
    for _ in range(12):
        controle.uniforme()
    assert gerador.uniforme() == controle.uniforme()


def test_historico_conta_populacao_apenas_uma_vez_por_registro(monkeypatch) -> None:
    chamadas = []
    contar_original = Simulacao.contar_estados

    def contar(simulacao):
        chamadas.append(simulacao.passo)
        return contar_original(simulacao)

    monkeypatch.setattr(Simulacao, "contar_estados", contar)
    configuracao = ConfiguracaoSimulacao(0.0, 0.0, 42, 43, 44, 4, 1, (0,))

    resultado = Simulacao(rede_exemplo(), configuracao).executar()

    assert chamadas == [registro.passo for registro in resultado.historico]


@pytest.mark.parametrize("comparar,esperadas", [(False, 2), (True, 7)])
def test_api_evita_copias_redundantes_sem_modificar_rede(
    monkeypatch, comparar: bool, esperadas: int,
) -> None:
    servico = ServicoCargaRede()
    estado = servico.gerar({
        "modelo": "barabasi_albert", "numero_individuos": 8,
        "contatos_por_novo_individuo": 2, "semente": 42,
    })
    servico.confirmar(estado["revisao"])
    formulario = {
        "beta": "0.2", "gamma": "0", "modo_peso": "intensidade",
        "modo_iniciais": "ids", "ids_infectados_iniciais": ["0"],
        "semente_epidemia": "42", "semente_iniciais": "43", "semente_isolamento": "44",
        "limite_passos": 5, "revisao_rede": estado["revisao"],
        "intervencao": {
            "estrategia": "grau", "fracao": "0.5", "inicio": 1,
            "mecanismo": "exclusao",
        },
    }
    chamadas = []
    copiar_original = RedeContatos.copiar

    def copiar(rede):
        chamadas.append(rede.numero_individuos)
        return copiar_original(rede)

    monkeypatch.setattr(RedeContatos, "copiar", copiar)

    if comparar:
        resultado = executar_comparacao_api(servico, {
            "configuracao": formulario, "repeticoes": 2,
        })
        assert len(resultado["execucoes"]) == 6
    else:
        executar_simulacao_api(servico, formulario)

    assert len(chamadas) == esperadas
    assert servico.inspecionar()["resumo"] == estado["resumo"]
    referencia = servico.obter_rede_confirmada(estado["revisao"])
    assert all(
        pessoa.estado is EstadoSIR.SUSCETIVEL and not pessoa.isolamento
        for pessoa in referencia.rede.individuos
    )
