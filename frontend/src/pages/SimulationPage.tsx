import { useEffect, useMemo, useRef, useState } from 'react'
import { AppShell } from '../components/AppShell'
import { Icon } from '../components/Icon'
import { NetworkScene } from '../features/rede/visualizacao/NetworkScene'
import { ResumoEnsaio } from '../features/resultados/ResumoEnsaio'
import { useCargaRede } from '../hooks/useCargaRede'
import {
  executarComparacao,
  executarSimulacao,
  validarConfiguracao,
  type ConfiguracaoSalva,
  type ConfiguracaoValidada,
  type ExecucaoComparadaResultado,
  type RegistroResultado,
  type ResultadoSimulacao,
} from '../services/configuracaoApi'
import type { PreviaRede } from '../types/rede'
import './SimulationPage.css'

type EstadoSIR = 'S' | 'I' | 'R' | 'isolado'

const CHAVE_HISTORICO = 'observatorio-historico-ensaio'
const CHAVE_CONFIGURACAO = 'observatorio-configuracao'
const CHAVE_RESULTADO = 'observatorio-resultado-execucao'

function previaVazia(total: number): PreviaRede {
  return {
    revisao: 0,
    individuos: [],
    contatos: [],
    total_individuos: total,
    total_contatos: 0,
    parcial: false,
  }
}

function lerConfiguracao(): ConfiguracaoSalva | null {
  try {
    const valor = JSON.parse(
      sessionStorage.getItem(CHAVE_CONFIGURACAO) ?? 'null',
    ) as ConfiguracaoSalva | null
    return valor?.formulario ? valor : null
  } catch {
    return null
  }
}

export function SimulationPage({
  onNavegarRede,
}: {
  onNavegarRede: () => void
}) {
  const carga = useCargaRede()
  const total = carga.rede?.resumo?.numero_individuos ?? 0
  const previa = carga.previa ?? previaVazia(total)
  const [modo, setModo] = useState<'unica' | 'repeticoes'>('unica')
  const [status, setStatus] = useState<'Pausado' | 'Executando' | 'Finalizado'>(
    'Pausado',
  )
  const [erro, setErro] = useState('')
  const [requisicao, setRequisicao] = useState<
    'ociosa' | 'carregando' | 'concluida' | 'falhou'
  >('ociosa')
  const [historico, setHistorico] = useState<RegistroResultado[]>([])
  const [resultadoEnsaio, setResultadoEnsaio] =
    useState<ResultadoSimulacao | null>(null)
  const [passo, setPasso] = useState(0)
  const [tema, setTema] = useState<'dark' | 'light'>('dark')
  const [visualizacao, setVisualizacao] = useState<'mapa' | '3d'>('mapa')
  const pedido = useRef<AbortController | null>(null)
  const [configuracaoSalva] = useState(lerConfiguracao)
  const [validacao, setValidacao] = useState<ConfiguracaoValidada | null>(
    () => configuracaoSalva?.validacao ?? null,
  )
  const [falhaResumo, setFalhaResumo] = useState('')
  const [tentativaResumo, setTentativaResumo] = useState(0)
  const contextoAtual = carga.rede?.contexto_rede
  const revisaoAtual = carga.rede?.revisao
  const podeValidar = Boolean(
    carga.rede?.confirmada &&
    configuracaoSalva?.formulario.contexto_rede === carga.rede.contexto_rede &&
    Number(configuracaoSalva?.formulario.revisao_rede) === carga.rede.revisao,
  )
  const validacaoAtual =
    podeValidar &&
    validacao?.contexto_rede === contextoAtual &&
    validacao?.configuracao?.revisao_rede === revisaoAtual
      ? validacao
      : null
  const podeExecutar = Boolean(
    validacaoAtual &&
    (modo === 'unica' || validacaoAtual.configuracao.intervencao),
  )
  const repeticoes = configuracaoSalva?.repeticoes ?? '2'

  useEffect(() => {
    if (!podeValidar || !configuracaoSalva || validacaoAtual) return
    const controlador = new AbortController()
    validarConfiguracao(configuracaoSalva.formulario, controlador.signal)
      .then((resultado) => {
        if (controlador.signal.aborted) return
        if (
          resultado.contexto_rede !== contextoAtual ||
          resultado.configuracao.revisao_rede !== revisaoAtual
        )
          throw new Error(
            'A rede mudou. Valide a configuração novamente na Tela 02.',
          )
        setValidacao(resultado)
      })
      .catch((falha: unknown) => {
        if (!controlador.signal.aborted)
          setFalhaResumo(
            falha instanceof Error
              ? falha.message
              : 'Não foi possível consultar a configuração.',
          )
      })
    return () => controlador.abort()
  }, [
    podeValidar,
    configuracaoSalva,
    contextoAtual,
    revisaoAtual,
    validacaoAtual,
    tentativaResumo,
  ])

  useEffect(() => {
    return () => {
      pedido.current?.abort()
      pedido.current = null
    }
  }, [carga.rede?.contexto_rede, carga.rede?.revisao])

  useEffect(() => {
    if (!carga.rede || !historico.length) return
    const configuracao = configuracaoSalva
    const resultadoContextualizado =
      resultadoEnsaio?.contexto_rede === carga.rede.contexto_rede &&
      resultadoEnsaio.revisao_rede === carga.rede.revisao
    const configuracaoAtual =
      configuracao?.formulario.contexto_rede === carga.rede.contexto_rede &&
      Number(configuracao?.formulario.revisao_rede) === carga.rede.revisao
    if (!resultadoContextualizado && !configuracaoAtual) {
      const tarefa = window.setTimeout(() => {
        setHistorico([])
        setResultadoEnsaio(null)
        setPasso(0)
        setStatus('Pausado')
        setErro(
          'O resultado foi invalidado porque a revisão ou o contexto da rede mudou.',
        )
        sessionStorage.removeItem(CHAVE_HISTORICO)
        sessionStorage.removeItem(CHAVE_RESULTADO)
      }, 0)
      return () => window.clearTimeout(tarefa)
    }
  }, [carga.rede, historico.length, resultadoEnsaio, configuracaoSalva])

  const resultadoAtual =
    resultadoEnsaio?.contexto_rede === contextoAtual &&
    resultadoEnsaio?.revisao_rede === revisaoAtual
      ? resultadoEnsaio
      : null
  const registroAtual = resultadoAtual
    ? (historico.find((item) => item.passo === passo) ?? null)
    : null
  const suscetiveis = registroAtual?.suscetiveis
  const infectados = registroAtual?.infectados
  const recuperados = registroAtual?.recuperados
  const isolados = registroAtual?.isolados
  const limitePassos =
    resultadoAtual?.metrica.horizonte_observado ?? historico.at(-1)?.passo ?? 0

  const estadosPorNo = useMemo(() => {
    if (!registroAtual || total === 0) return undefined
    const estados: Record<string, EstadoSIR> = {}
    const { recuperados, infectados, isolados } = registroAtual
    const quantidade = previa.individuos.length
    previa.individuos.forEach((no, indice) => {
      const posicao = quantidade ? indice / quantidade : 0
      if (
        isolados > 0 &&
        indice < Math.round((isolados / total) * quantidade)
      ) {
        estados[no.id] = 'isolado'
      } else if (posicao < recuperados / Math.max(total, 1)) {
        estados[no.id] = 'R'
      } else if (posicao < (recuperados + infectados) / Math.max(total, 1)) {
        estados[no.id] = 'I'
      } else {
        estados[no.id] = 'S'
      }
    })
    return estados
  }, [previa.individuos, registroAtual, total])

  async function executarBackend(): Promise<boolean> {
    if (pedido.current) return false
    setErro('')
    const configuracao = configuracaoSalva
    if (!configuracao) {
      setErro('Valide uma configuração na Tela 02 antes de executar o ensaio.')
      setRequisicao('falhou')
      return false
    }
    if (
      !carga.rede?.confirmada ||
      configuracao.formulario.contexto_rede !== carga.rede.contexto_rede ||
      Number(configuracao.formulario.revisao_rede) !== carga.rede.revisao
    ) {
      setErro(
        'A rede mudou desde a validação. Volte à Tela 02 e valide a configuração novamente.',
      )
      setRequisicao('falhou')
      return false
    }

    const controlador = new AbortController()
    pedido.current = controlador
    setRequisicao('carregando')
    try {
      if (modo === 'repeticoes') {
        const lote = await executarComparacao(
          configuracao.repeticoes ?? '2',
          configuracao.formulario,
          controlador.signal,
        )
        if (controlador.signal.aborted || pedido.current !== controlador)
          return false
        const principal: ExecucaoComparadaResultado =
          lote.execucoes.find((item) => item.cenario === 'grau') ??
          lote.execucoes.find((item) => item.cenario === 'aleatoria') ??
          lote.execucoes[0]
        const registros = principal?.historico ?? []
        setResultadoEnsaio(
          principal
            ? {
                ...principal,
                contexto_rede: lote.contexto_rede,
                revisao_rede: lote.revisao_rede,
                populacao: lote.populacao,
              }
            : null,
        )
        setHistorico(registros)
        setPasso(0)
        sessionStorage.setItem(CHAVE_HISTORICO, JSON.stringify(registros))
        sessionStorage.setItem(
          CHAVE_RESULTADO,
          JSON.stringify({
            tipo: 'comparacao',
            comparacao: lote,
            principal,
          }),
        )
        setStatus('Pausado')
        setRequisicao('concluida')
        return registros.length > 0
      }

      const resultado = await executarSimulacao(
        configuracao.formulario,
        controlador.signal,
      )
      if (controlador.signal.aborted || pedido.current !== controlador)
        return false
      setResultadoEnsaio(resultado)
      setHistorico(resultado.historico)
      setPasso(0)
      sessionStorage.setItem(
        CHAVE_HISTORICO,
        JSON.stringify(resultado.historico),
      )
      sessionStorage.setItem(
        CHAVE_RESULTADO,
        JSON.stringify({ tipo: 'individual', resultado }),
      )
      setStatus('Pausado')
      setRequisicao('concluida')
      return resultado.historico.length > 0
    } catch (falha) {
      if (controlador.signal.aborted) return false
      setErro(
        falha instanceof Error
          ? falha.message
          : 'Não foi possível executar o ensaio no backend.',
      )
      setRequisicao('falhou')
      return false
    } finally {
      if (pedido.current === controlador) pedido.current = null
    }
  }

  async function iniciar() {
    if (!historico.length) {
      const executado = await executarBackend()
      if (!executado) return
    }
    setStatus('Executando')
  }

  function pausar() {
    setStatus('Pausado')
  }

  async function avancarUmPasso() {
    if (!historico.length) {
      await executarBackend()
      return
    }
    const proximo = Math.min(historico.length - 1, Math.max(passo + 1, 0))
    const registro = historico[proximo]
    setPasso(registro.passo)
    setStatus(
      proximo === historico.length - 1 || registro.infectados === 0
        ? 'Finalizado'
        : 'Pausado',
    )
  }

  async function reiniciar() {
    pedido.current?.abort()
    pedido.current = null
    setPasso(0)
    setStatus('Pausado')
    setRequisicao('ociosa')
    sessionStorage.removeItem(CHAVE_HISTORICO)
    sessionStorage.removeItem(CHAVE_RESULTADO)
    setHistorico([])
    setResultadoEnsaio(null)
  }

  useEffect(() => {
    if (status !== 'Executando' || !historico.length) return
    const temporizador = window.setInterval(
      () => {
        setPasso((passoAtual) => {
          const indice = historico.findIndex(
            (item) => item.passo === passoAtual,
          )
          const proximo = indice >= 0 ? indice + 1 : 1
          if (proximo >= historico.length) {
            setStatus('Finalizado')
            return historico.at(-1)?.passo ?? passoAtual
          }
          const registro = historico[proximo]
          if (registro.infectados === 0) setStatus('Finalizado')
          return registro.passo
        })
      },
      modo === 'repeticoes' ? 550 : 800,
    )
    return () => window.clearInterval(temporizador)
  }, [status, historico, modo])

  const percentual =
    limitePassos > 0
      ? Math.round((passo / limitePassos) * 100)
      : registroAtual
        ? 100
        : 0

  return (
    <AppShell
      conectado={carga.conexao === 'online'}
      etapaAtiva={3}
      onNavegar={(etapa) => {
        if (etapa === 1) onNavegarRede()
      }}
    >
      <main
        id="conteudo"
        className="workspace simulation-workspace"
        tabIndex={-1}
      >
        <div className="workspace-heading">
          <div>
            <p className="page-eyebrow">03 / Evolução no tempo</p>
            <h1>Ensaio passo a passo</h1>
            <p>
              Execute o motor real e acompanhe o histórico obtido pelo backend.
            </p>
          </div>
          <div
            className="sir-model"
            role="img"
            aria-label={
              registroAtual
                ? `Modelo SIR: ${suscetiveis} suscetíveis, ${infectados} infectados e ${recuperados} recuperados`
                : 'Modelo SIR: contagens indisponíveis antes da execução'
            }
          >
            <span>
              <b>S</b>
              <small>{suscetiveis ?? '—'}</small>
            </span>
            <i>
              β<Icon nome="arrow" size={33} />
            </i>
            <span>
              <b>I</b>
              <small>{infectados ?? '—'}</small>
            </span>
            <i>
              γ<Icon nome="arrow" size={33} />
            </i>
            <span>
              <b>R</b>
              <small>{recuperados ?? '—'}</small>
            </span>
          </div>
        </div>

        {erro && (
          <p className="results-warning" role="alert">
            {erro}
          </p>
        )}

        <ResumoEnsaio
          rede={carga.rede}
          validacao={validacaoAtual}
          modo={modo}
          repeticoes={repeticoes}
          carregando={podeValidar && !validacaoAtual && !falhaResumo}
          erro={podeValidar ? falhaResumo : ''}
          onRepetir={() => {
            setFalhaResumo('')
            setTentativaResumo((atual) => atual + 1)
          }}
        />

        <div className="simulation-workbench">
          <aside
            className="simulation-controls"
            aria-labelledby="controls-title"
          >
            <div className="section-heading">
              <h2 id="controls-title">Controles do ensaio</h2>
              <div className="requirements">
                <span>RF06</span>
                <span>RF07</span>
              </div>
            </div>
            <fieldset className="experiment-mode">
              <legend>Modo de Experimento</legend>
              <button
                type="button"
                className={
                  modo === 'unica'
                    ? 'experiment-card selected'
                    : 'experiment-card'
                }
                aria-pressed={modo === 'unica'}
                onClick={() => {
                  setModo('unica')
                  void reiniciar()
                }}
              >
                <span className="radio-mark" aria-hidden="true" />
                <span>
                  <strong>Execução Única</strong>
                  <small>Trajetória detalhada (RF06)</small>
                </span>
              </button>
              <button
                type="button"
                className={
                  modo === 'repeticoes'
                    ? 'experiment-card selected'
                    : 'experiment-card'
                }
                aria-pressed={modo === 'repeticoes'}
                onClick={() => {
                  setModo('repeticoes')
                  void reiniciar()
                }}
              >
                <span className="radio-mark" aria-hidden="true" />
                <span>
                  <strong>Repetições</strong>
                  <small>Comparar cenários (RF07)</small>
                </span>
              </button>
            </fieldset>
            <div className="experiment-actions">
              <button
                type="button"
                className="button-primary full-width"
                onClick={() => void iniciar()}
                disabled={
                  !podeExecutar ||
                  status === 'Executando' ||
                  requisicao === 'carregando'
                }
              >
                {requisicao === 'carregando'
                  ? 'Consultando backend…'
                  : '▶ Iniciar / Continuar Simulação'}
              </button>
              <button
                type="button"
                className="button-secondary full-width"
                onClick={() => void avancarUmPasso()}
                disabled={
                  !podeExecutar ||
                  requisicao === 'carregando' ||
                  status === 'Executando' ||
                  (historico.length > 0 && passo >= limitePassos)
                }
              >
                ▷ 1 Passo
              </button>
              <div className="pause-reset">
                <button
                  type="button"
                  className="button-pause"
                  onClick={pausar}
                  disabled={status !== 'Executando'}
                >
                  ⏸ Pausar
                </button>
                <button
                  type="button"
                  className="button-reset"
                  onClick={() => void reiniciar()}
                >
                  ↺ Reiniciar
                </button>
              </div>
              {status === 'Finalizado' && (
                <a
                  className="button-primary full-width"
                  href="#resultados"
                  aria-label="Abrir resultados do ensaio concluído"
                >
                  Abrir resultados →
                </a>
              )}
            </div>
            {!podeExecutar && (
              <p role="status">
                {validacaoAtual && modo === 'repeticoes'
                  ? 'Configure uma intervenção na Tela 02 para comparar estratégias.'
                  : 'Confirme a rede e aguarde a configuração validada da Tela 02 para executar.'}
              </p>
            )}
          </aside>

          <section
            className="population-panel"
            aria-labelledby="population-title"
          >
            <div className="population-heading">
              <h2 id="population-title">População ao longo do tempo</h2>
              <span className={`run-status status-${status.toLowerCase()}`}>
                {registroAtual
                  ? `${status} - ${passo}/${limitePassos}`
                  : `${status} · aguardando execução`}
              </span>
            </div>
            {registroAtual ? (
              <>
                <div className="progress-label">
                  <strong>Passo Atual: t = {passo}</strong>
                  <span>{percentual}%</span>
                </div>
                <div
                  className="simulation-progress"
                  role="progressbar"
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={percentual}
                  aria-valuetext={`Passo ${passo} de ${limitePassos} passos registrados`}
                >
                  <span style={{ width: `${percentual}%` }} />
                </div>
                <div className="progress-ticks" aria-hidden="true">
                  {[
                    ...new Set(
                      [0, 0.25, 0.5, 0.75, 1].map((fracao) =>
                        Math.round(limitePassos * fracao),
                      ),
                    ),
                  ].map((instante) => (
                    <span key={instante}>{instante}</span>
                  ))}
                </div>
              </>
            ) : (
              <p role="status" className="simulation-empty">
                {requisicao === 'carregando'
                  ? 'Calculando o ensaio. As contagens aparecerão após a resposta do backend.'
                  : 'Nenhuma simulação executada. As contagens aparecerão após a resposta do backend.'}
              </p>
            )}
            {resultadoAtual && (
              <p className="simulation-outcome">
                Histórico recebido:{' '}
                {resultadoAtual.motivo_termino === 'extincao'
                  ? 'extinção da epidemia'
                  : 'limite máximo de passos'}{' '}
                em t = {limitePassos} ({limitePassos} passos realizados).
              </p>
            )}

            <section className="sir-network" aria-labelledby="network-title">
              <div className="network-title-row">
                <div>
                  <h3 id="network-title">
                    {registroAtual ? 'Estados na rede' : 'Estrutura da rede'}
                  </h3>
                  <p>
                    {registroAtual
                      ? `Estado individual inferido das contagens (não são snapshots por ID) · ${previa.total_individuos.toLocaleString('pt-BR')} nós · t = ${passo}`
                      : 'Prévia estrutural; os estados epidemiológicos ainda não foram calculados.'}
                  </p>
                </div>
                <div className="sir-network-controls">
                  <div
                    className="graph-view-switch"
                    role="group"
                    aria-label="Visualização da rede"
                  >
                    <button
                      type="button"
                      aria-pressed={visualizacao === 'mapa'}
                      onClick={() => setVisualizacao('mapa')}
                    >
                      Mapa
                    </button>
                    <button
                      type="button"
                      aria-pressed={visualizacao === '3d'}
                      onClick={() => setVisualizacao('3d')}
                    >
                      3D
                    </button>
                  </div>
                  <div
                    className="graph-theme"
                    role="group"
                    aria-label="Tema do grafo"
                  >
                    <button
                      type="button"
                      aria-pressed={tema === 'light'}
                      onClick={() => setTema('light')}
                    >
                      Claro
                    </button>
                    <button
                      type="button"
                      aria-pressed={tema === 'dark'}
                      onClick={() => setTema('dark')}
                    >
                      Escuro
                    </button>
                  </div>
                </div>
              </div>
              <div className={`graph-panel graph-${tema} sir-network-canvas`}>
                <NetworkScene
                  previa={previa}
                  selecionado={null}
                  onSelecionar={() => undefined}
                  ocupado={false}
                  visualizacao={visualizacao}
                  estadosPorNo={estadosPorNo}
                  compacto
                />
              </div>
              {registroAtual && (
                <div
                  className="sir-network-legend"
                  aria-label="Legenda dos estados"
                >
                  <span>
                    <b className="legend-s" />
                    Suscetível
                  </span>
                  <span>
                    <b className="legend-i" />
                    Infectado
                  </span>
                  <span>
                    <b className="legend-r" />
                    Recuperado
                  </span>
                  <span>
                    <b className="legend-isolado" />
                    Isolado
                  </span>
                </div>
              )}
            </section>

            <dl className="sir-population-stats">
              <div>
                <dt>Suscetíveis (S)</dt>
                <dd className="stat-s">{suscetiveis ?? '—'}</dd>
              </div>
              <div>
                <dt>Infectados (I)</dt>
                <dd className="stat-i">{infectados ?? '—'}</dd>
              </div>
              <div>
                <dt>Recuperados (R)</dt>
                <dd className="stat-r">{recuperados ?? '—'}</dd>
              </div>
              <div>
                <dt>Isolados</dt>
                <dd className="stat-isolado">{isolados ?? '—'}</dd>
              </div>
            </dl>
            {registroAtual && total > 0 && (
              <div
                className="population-proportion"
                aria-label="Distribuição proporcional da população"
              >
                <span
                  className="bar-s"
                  style={{
                    width: `${(registroAtual.suscetiveis / total) * 100}%`,
                  }}
                />
                <span
                  className="bar-i"
                  style={{
                    width: `${(registroAtual.infectados / total) * 100}%`,
                  }}
                />
                <span
                  className="bar-r"
                  style={{
                    width: `${(registroAtual.recuperados / total) * 100}%`,
                  }}
                />
                <span
                  className="bar-isolado"
                  style={{
                    width: `${(registroAtual.isolados / total) * 100}%`,
                  }}
                />
              </div>
            )}
          </section>
        </div>
      </main>
    </AppShell>
  )
}
