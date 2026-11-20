import { useEffect, useMemo, useState } from 'react'
import { AppShell } from '../components/AppShell'
import { Icon } from '../components/Icon'
import { NetworkScene } from '../features/rede/visualizacao/NetworkScene'
import { useCargaRede } from '../hooks/useCargaRede'
import {
  executarComparacao,
  executarSimulacao,
  type ExecucaoComparadaResultado,
  type FormularioConfiguracao,
  type RegistroResultado,
  type ResultadoSimulacao,
} from '../services/configuracaoApi'
import type { PreviaRede } from '../types/rede'

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

function lerConfiguracao(): {
  repeticoes: string | null
  formulario: FormularioConfiguracao
} | null {
  try {
    const valor = JSON.parse(
      sessionStorage.getItem(CHAVE_CONFIGURACAO) ?? 'null',
    ) as {
      repeticoes: string | null
      formulario: FormularioConfiguracao
    } | null
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
  const total = carga.rede?.resumo?.numero_individuos ?? 100
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
  const [resultadoIndividual, setResultadoIndividual] =
    useState<ResultadoSimulacao | null>(null)
  const [passo, setPasso] = useState(0)
  const [tema, setTema] = useState<'dark' | 'light'>('dark')
  const [visualizacao, setVisualizacao] = useState<'mapa' | '3d'>('mapa')

  useEffect(() => {
    if (!carga.rede || !historico.length) return
    const configuracao = lerConfiguracao()
    const resultadoContextualizado =
      resultadoIndividual?.contexto_rede === carga.rede.contexto_rede &&
      resultadoIndividual.revisao_rede === carga.rede.revisao
    const configuracaoAtual =
      configuracao?.formulario.contexto_rede === carga.rede.contexto_rede &&
      Number(configuracao?.formulario.revisao_rede) === carga.rede.revisao
    if (!resultadoContextualizado && !configuracaoAtual) {
      const tarefa = window.setTimeout(() => {
        setHistorico([])
        setResultadoIndividual(null)
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
  }, [carga.rede, historico.length, resultadoIndividual])

  const atual = historico.at(-1) ?? {
    passo: 0,
    suscetiveis: Math.max(total - 4, 0),
    infectados: Math.min(4, total),
    recuperados: 0,
    isolados: 0,
  }
  const registroAtual = historico.find((item) => item.passo === passo) ?? atual
  const suscetiveis = registroAtual.suscetiveis
  const infectados = registroAtual.infectados
  const recuperados = registroAtual.recuperados
  const isolados = registroAtual.isolados
  const limitePassos =
    resultadoIndividual?.metrica.horizonte_observado ??
    historico.at(-1)?.passo ??
    100

  const estadosPorNo = useMemo(() => {
    const estados: Record<string, EstadoSIR> = {}
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
  }, [previa.individuos, recuperados, infectados, isolados, total])

  async function executarBackend(): Promise<boolean> {
    setErro('')
    const configuracao = lerConfiguracao()
    if (!configuracao) {
      setErro('Valide uma configuração na Tela 02 antes de executar o ensaio.')
      setRequisicao('falhou')
      return false
    }
    if (
      !carga.rede ||
      configuracao.formulario.contexto_rede !== carga.rede.contexto_rede ||
      Number(configuracao.formulario.revisao_rede) !== carga.rede.revisao
    ) {
      setErro(
        'A rede mudou desde a validação. Volte à Tela 02 e valide a configuração novamente.',
      )
      setRequisicao('falhou')
      return false
    }

    setRequisicao('carregando')
    try {
      if (modo === 'repeticoes') {
        const lote = await executarComparacao(
          configuracao.repeticoes ?? '2',
          configuracao.formulario,
        )
        const principal: ExecucaoComparadaResultado =
          lote.execucoes.find((item) => item.cenario === 'grau') ??
          lote.execucoes.find((item) => item.cenario === 'aleatoria') ??
          lote.execucoes[0]
        const registros = principal?.historico ?? []
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

      const resultado = await executarSimulacao(configuracao.formulario)
      setResultadoIndividual(resultado)
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
      if (falha instanceof DOMException && falha.name === 'AbortError')
        return false
      setErro(
        falha instanceof Error
          ? falha.message
          : 'Não foi possível executar o ensaio no backend.',
      )
      setRequisicao('falhou')
      return false
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
    setPasso(0)
    setStatus('Pausado')
    setRequisicao('ociosa')
    sessionStorage.removeItem(CHAVE_HISTORICO)
    sessionStorage.removeItem(CHAVE_RESULTADO)
    setHistorico([])
    setResultadoIndividual(null)
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
    limitePassos > 0 ? Math.round((passo / limitePassos) * 100) : 0

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
          <div className="sir-model" role="img" aria-label="Modelo SIR">
            <span>
              <b>S</b>
              <small>{suscetiveis}</small>
            </span>
            <i>
              β<Icon nome="arrow" size={33} />
            </i>
            <span>
              <b>I</b>
              <small>{infectados}</small>
            </span>
            <i>
              γ<Icon nome="arrow" size={33} />
            </i>
            <span>
              <b>R</b>
              <small>{recuperados}</small>
            </span>
          </div>
        </div>

        {erro && (
          <p className="results-warning" role="alert">
            {erro}
          </p>
        )}

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
                  status === 'Executando' || requisicao === 'carregando'
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
                  status === 'Executando' ||
                  (historico.length > 0 &&
                    passo >= Math.max(...historico.map((item) => item.passo)))
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
          </aside>

          <section
            className="population-panel"
            aria-labelledby="population-title"
          >
            <div className="population-heading">
              <h2 id="population-title">População ao longo do tempo</h2>
              <span className={`run-status status-${status.toLowerCase()}`}>
                {status} - {passo}/{limitePassos}
              </span>
            </div>
            <div className="progress-label">
              <strong>Passo Atual: t = {passo}</strong>
              <span>{percentual}%</span>
            </div>
            <div
              className="simulation-progress"
              role="progressbar"
              aria-valuemin={0}
              aria-valuemax={limitePassos}
              aria-valuenow={passo}
            >
              <span style={{ width: `${percentual}%` }} />
            </div>
            <div className="progress-ticks" aria-hidden="true">
              <span>0</span>
              <span>25</span>
              <span>50</span>
              <span>75</span>
              <span>{limitePassos} passos</span>
            </div>

            <section className="sir-network" aria-labelledby="network-title">
              <div className="network-title-row">
                <div>
                  <h3 id="network-title">Estados na rede</h3>
                  <p>
                    Estado individual inferido a partir das contagens do
                    histórico (o backend não fornece snapshots por ID) -{' '}
                    {previa.total_individuos.toLocaleString('pt-BR')} nós - t ={' '}
                    {passo}
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
            </section>

            <dl className="sir-population-stats">
              <div>
                <dt>Suscetíveis (S)</dt>
                <dd className="stat-s">{suscetiveis}</dd>
              </div>
              <div>
                <dt>Infectados (I)</dt>
                <dd className="stat-i">{infectados}</dd>
              </div>
              <div>
                <dt>Recuperados (R)</dt>
                <dd className="stat-r">{recuperados}</dd>
              </div>
              <div>
                <dt>Isolados</dt>
                <dd className="stat-isolado">{isolados}</dd>
              </div>
            </dl>
            <div
              className="population-proportion"
              aria-label="Distribuição proporcional da população"
            >
              <span
                className="bar-s"
                style={{ width: `${(suscetiveis / total) * 100}%` }}
              />
              <span
                className="bar-i"
                style={{ width: `${(infectados / total) * 100}%` }}
              />
              <span
                className="bar-r"
                style={{ width: `${(recuperados / total) * 100}%` }}
              />
              <span
                className="bar-isolado"
                style={{ width: `${(isolados / total) * 100}%` }}
              />
            </div>
          </section>
        </div>
      </main>
    </AppShell>
  )
}
