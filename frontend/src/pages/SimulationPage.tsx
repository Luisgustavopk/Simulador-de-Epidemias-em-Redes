import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { AppShell } from '../components/AppShell'
import { Icon } from '../components/Icon'
import { NetworkScene } from '../features/rede/visualizacao/NetworkScene'
import { useCargaRede } from '../hooks/useCargaRede'
import type { PreviaRede } from '../types/rede'

type EstadoSIR = 'S' | 'I' | 'R' | 'isolado'

interface RegistroEnsaio {
  passo: number
  suscetiveis: number
  infectados: number
  recuperados: number
  isolados: number
}

const LIMITE_PASSOS = 100
const CHAVE_HISTORICO = 'observatorio-historico-ensaio'

function persistirHistorico(registro: RegistroEnsaio) {
  try {
    const historicoAnterior = JSON.parse(
      sessionStorage.getItem(CHAVE_HISTORICO) ?? '[]',
    ) as RegistroEnsaio[]
    const historico = [
      ...historicoAnterior.filter((item) => item.passo !== registro.passo),
      registro,
    ].sort((a, b) => a.passo - b.passo)
    sessionStorage.setItem(CHAVE_HISTORICO, JSON.stringify(historico))
  } catch {
    sessionStorage.setItem(CHAVE_HISTORICO, JSON.stringify([registro]))
  }
}

function previaDemonstrativa(total: number): PreviaRede {
  const quantidade = Math.min(Math.max(total, 20), 180)
  const individuos = Array.from({ length: quantidade }, (_, indice) => ({
    id: `I${String(indice + 1).padStart(3, '0')}`,
    grau: 2 + ((indice * 7) % 8),
  }))
  const contatos = individuos.flatMap((individuo, indice) => {
    const destino = individuos[(indice * 3 + 11) % quantidade]
    const destinoExtra = individuos[(indice * 5 + 37) % quantidade]
    return destino.id === individuo.id
      ? []
      : [
          { origem: individuo.id, destino: destino.id, peso: 0.5, ativa: true },
          ...(destinoExtra.id !== individuo.id
            ? [{ origem: individuo.id, destino: destinoExtra.id, peso: 0.7, ativa: true }]
            : []),
        ]
  })
  return {
    revisao: 0,
    individuos,
    contatos,
    total_individuos: total,
    total_contatos: contatos.length,
    parcial: quantidade < total,
  }
}

export function SimulationPage({
  onNavegarRede,
}: {
  onNavegarRede: () => void
}) {
  const carga = useCargaRede()
  const total = carga.rede?.resumo?.numero_individuos ?? 100
  const previa = carga.previa ?? previaDemonstrativa(total)
  const [modo, setModo] = useState<'unica' | 'repeticoes'>('unica')
  const [status, setStatus] = useState<'Pausado' | 'Executando' | 'Finalizado'>(
    'Pausado',
  )
  const [passo, setPasso] = useState(0)
  const [suscetiveis, setSuscetiveis] = useState(Math.max(total - 4, 0))
  const [infectados, setInfectados] = useState(total >= 4 ? 4 : total)
  const [recuperados, setRecuperados] =  useState(0)
  const [isolados, setIsolados] = useState(0)
  const [tema, setTema] = useState<'dark' | 'light'>('dark')
  const [visualizacao, setVisualizacao] = useState<'mapa' | '3d'>('mapa')
  const rodando = useRef(false)

  const limparRelogio = useRef<(() => void) | null>(null)
  const avancar = useCallback(() => {
    setPasso((passoAtual) => {
      if (passoAtual >= LIMITE_PASSOS) {
        rodando.current = false
        setStatus('Finalizado')
        return passoAtual
      }
      const novoPasso = passoAtual + 1
      setSuscetiveis((s) => {
        setInfectados((i) => {
          setRecuperados((r) => {
            setIsolados((isoladosAtuais) => {
              const novasInfeccoes =
                s === 0
                  ? 0
                  : Math.min(s, Math.max(1, Math.ceil(i * 0.11)))
              const novasRecuperacoes = Math.min(
                i,
                Math.max(1, Math.ceil(i * 0.09)),
              )
              const novoS = Math.max(0, s - novasInfeccoes)
              const novoI = Math.max(
                0,
                i + novasInfeccoes - novasRecuperacoes,
              )
              const novoR = Math.min(total, r + novasRecuperacoes)
              const novoIsolado =
                modo === 'repeticoes' && novoPasso % 10 === 0
                  ? Math.min(total, isoladosAtuais + 3)
                  : isoladosAtuais

              setSuscetiveis(novoS)
              setInfectados(novoI)
              setRecuperados(novoR)
              setIsolados(novoIsolado)
              persistirHistorico({
                passo: novoPasso,
                suscetiveis: novoS,
                infectados: novoI,
                recuperados: novoR,
                isolados: novoIsolado,
              })
              if (novoI === 0 || novoPasso >= LIMITE_PASSOS) {
                rodando.current = false
                setStatus('Finalizado')
              }
              return novoIsolado
            })
            return r
          })
          return i
        })
        return s
      })
      return novoPasso
    })
  }, [modo, total])

  function iniciar() {
    if (rodando.current || passo >= LIMITE_PASSOS) return
    rodando.current = true
    setStatus('Executando')
  }

  useEffect(() => {
    if (!rodando.current) return
    const temporizador = window.setInterval(avancar, modo === 'repeticoes' ? 550 : 800)
    limparRelogio.current = () => window.clearInterval(temporizador)
    return () => window.clearInterval(temporizador)
  }, [status, modo, avancar])

  useEffect(() => {
    persistirHistorico({
      passo: 0,
      suscetiveis: Math.max(total - 4, 0),
      infectados: total >= 4 ? 4 : total,
      recuperados: 0,
      isolados: 0,
    })
  }, [total])

  function pausar() {
    rodando.current = false
    limparRelogio.current?.()
    setStatus('Pausado')
  }

  function reiniciar() {
    rodando.current = false
    limparRelogio.current?.()
    const inicial = Math.max(total - 4, 0)
    const infectadoInicial = total >= 4 ? 4 : total
    setPasso(0)
    setSuscetiveis(inicial)
    setInfectados(infectadoInicial)
    setRecuperados(0)
    setIsolados(0)
    setStatus('Pausado')
    sessionStorage.removeItem(CHAVE_HISTORICO)
    persistirHistorico({
      passo: 0,
      suscetiveis: inicial,
      infectados: infectadoInicial,
      recuperados: 0,
      isolados: 0,
    })
  }

  const percentual = Math.round((passo / LIMITE_PASSOS) * 100)
  const estadosPorNo = useMemo(() => {
    const estados: Record<string, EstadoSIR> = {}
    const quantidade = previa.individuos.length
    previa.individuos.forEach((no, indice) => {
      const posicao = quantidade ? indice / quantidade : 0
      if (isolados > 0 && indice < Math.round((isolados / total) * quantidade)) {
        estados[no.id] = 'isolado'
      } else if (
        posicao <
        recuperados / Math.max(total, 1)
      ) {
        estados[no.id] = 'R'
      } else if (
        posicao <
        (recuperados + infectados) / Math.max(total, 1)
      ) {
        estados[no.id] = 'I'
      } else {
        estados[no.id] = 'S'
      }
    })
    return estados
  }, [previa.individuos, recuperados, infectados, isolados, total])

  return (
    <AppShell
      conectado={carga.conexao === 'online'}
      etapaAtiva={3}
      onNavegar={(etapa) => {
        if (etapa === 1) onNavegarRede()
      }}
    >
      <main id="conteudo" className="workspace simulation-workspace" tabIndex={-1}>
        <div className="workspace-heading">
          <div>
            <p className="page-eyebrow">03 / Evolução no tempo</p>
            <h1>Ensaio passo a passo</h1>
            <p>
              Execute, pause e acompanhe os estados da população demonstrativa.
            </p>
          </div>
          <div
            className="sir-model"
            role="img"
            aria-label="Modelo SIR"
          >
            <span><b>S</b><small>{suscetiveis}</small></span>
            <i>β<Icon nome="arrow" size={33} /></i>
            <span><b>I</b><small>{infectados}</small></span>
            <i>γ<Icon nome="arrow" size={33} /></i>
            <span><b>R</b><small>{recuperados}</small></span>
          </div>
        </div>

        <div className="simulation-workbench">
          <aside className="simulation-controls" aria-labelledby="controls-title">
            <div className="section-heading">
              <h2 id="controls-title">Controles do ensaio</h2>
              <div className="requirements"><span>RF06</span><span>RF07</span></div>
            </div>
            <fieldset className="experiment-mode">
              <legend>Modo de Experimento</legend>
              <button
                type="button"
                className={modo === 'unica' ? 'experiment-card selected' : 'experiment-card'}
                aria-pressed={modo === 'unica'}
                onClick={() => setModo('unica')}
              >
                <span className="radio-mark" aria-hidden="true" />
                <span><strong>Execução Única</strong><small>Trajetória detalhada (RF06)</small></span>
              </button>
              <button
                type="button"
                className={modo === 'repeticoes' ? 'experiment-card selected' : 'experiment-card'}
                aria-pressed={modo === 'repeticoes'}
                onClick={() => setModo('repeticoes')}
              >
                <span className="radio-mark" aria-hidden="true" />
                <span><strong>Repetições</strong><small>Comparar cenários (RF07)</small></span>
              </button>
            </fieldset>
            <div className="experiment-actions">
              <button
                type="button"
                className="button-primary full-width"
                onClick={iniciar}
                disabled={status === 'Executando' || passo >= LIMITE_PASSOS}
              >
                ▶ Iniciar / Continuar Simulação
              </button>
              <button
                type="button"
                className="button-secondary full-width"
                onClick={avancar}
                disabled={status === 'Executando' || passo >= LIMITE_PASSOS}
              >
                ▷ 1 Passo
              </button>
              <div className="pause-reset">
                <button type="button" className="button-pause" onClick={pausar} disabled={status !== 'Executando'}>
                  ⏸ Pausar
                </button>
                <button type="button" className="button-reset" onClick={reiniciar}>
                  ↺ Reiniciar
                </button>
              </div>
            </div>
          </aside>

          <section className="population-panel" aria-labelledby="population-title">
            <div className="population-heading">
              <h2 id="population-title">População ao longo do tempo</h2>
              <span className={`run-status status-${status.toLowerCase()}`}>
                {status === 'Pausado' ? 'Pausado' : status === 'Executando' ? 'Executando' : 'Finalizado'} - {passo}/{LIMITE_PASSOS}
              </span>
            </div>
            <div className="progress-label">
              <strong>Passo Atual: t = {passo}</strong>
              <span>{percentual}%</span>
            </div>
            <div
              className="simulation-progress"
              role="progressbar"
              aria-label="Progresso da simulação"
              aria-valuemin={0}
              aria-valuemax={LIMITE_PASSOS}
              aria-valuenow={passo}
            >
              <span style={{ width: `${percentual}%` }} />
            </div>
            <div className="progress-ticks" aria-hidden="true">
              <span>0</span><span>25</span><span>50</span><span>75</span><span>100 passos</span>
            </div>

            <section className="sir-network" aria-labelledby="network-title">
              <div className="network-title-row">
                <div>
                  <h3 id="network-title">Estados na rede</h3>
                  <p>Estados individuais do grafo carregado - {previa.total_individuos.toLocaleString('pt-BR')} nós - t = {passo}</p>
                </div>
                <div className="sir-network-controls">
                  <div className="graph-view-switch" role="group" aria-label="Visualização da rede">
                    <button type="button" aria-pressed={visualizacao === 'mapa'} onClick={() => setVisualizacao('mapa')}>Mapa</button>
                    <button type="button" aria-pressed={visualizacao === '3d'} onClick={() => setVisualizacao('3d')}>3D</button>
                  </div>
                  <div className="graph-theme" role="group" aria-label="Tema do grafo">
                    <button type="button" aria-pressed={tema === 'light'} onClick={() => setTema('light')}>Claro</button>
                    <button type="button" aria-pressed={tema === 'dark'} onClick={() => setTema('dark')}>Escuro</button>
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
              <div className="sir-network-legend" aria-label="Legenda dos estados">
                <span><b className="legend-s" />Suscetível</span>
                <span><b className="legend-i" />Infectado</span>
                <span><b className="legend-r" />Recuperado</span>
                <span><b className="legend-isolado" />Isolado</span>
              </div>
            </section>

            <dl className="sir-population-stats">
              <div><dt>Suscetíveis (S)</dt><dd className="stat-s">{suscetiveis}</dd></div>
              <div><dt>Infectados (I)</dt><dd className="stat-i">{infectados}</dd></div>
              <div><dt>Recuperados (R)</dt><dd className="stat-r">{recuperados}</dd></div>
              <div><dt>Isolados</dt><dd className="stat-isolado">{isolados}</dd></div>
            </dl>
            <div className="population-proportion" aria-label="Distribuição proporcional da população">
              <span className="bar-s" style={{ width: `${(suscetiveis / total) * 100}%` }} />
              <span className="bar-i" style={{ width: `${(infectados / total) * 100}%` }} />
              <span className="bar-r" style={{ width: `${(recuperados / total) * 100}%` }} />
              <span className="bar-isolado" style={{ width: `${(isolados / total) * 100}%` }} />
            </div>
          </section>
        </div>
      </main>
    </AppShell>
  )
}
