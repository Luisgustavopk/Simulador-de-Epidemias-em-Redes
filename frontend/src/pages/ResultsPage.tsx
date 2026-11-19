import { useEffect, useMemo, useState } from 'react'
import { AppShell } from '../components/AppShell'
import { Icon } from '../components/Icon'
import { useCargaRede } from '../hooks/useCargaRede'
import {
  executarComparacao,
  executarSimulacao,
  type RegistroResultado,
  type ResultadoComparacaoExecutada,
  type ResultadoSimulacao,
  type FormularioConfiguracao,
} from '../services/configuracaoApi'
import './ResultsPage.css'

const CHAVE_HISTORICO = 'observatorio-historico-ensaio'
const CHAVE_CONFIGURACAO = 'observatorio-configuracao'

interface RegistroLocal {
  passo: number
  suscetiveis: number
  infectados: number
  recuperados: number
  isolados: number
}

function lerHistoricoLocal(total: number): RegistroLocal[] {
  try {
    const registros = JSON.parse(
      sessionStorage.getItem(CHAVE_HISTORICO) ?? '[]',
    ) as RegistroLocal[]
    if (Array.isArray(registros) && registros.length) return registros
  } catch {
    // A demonstração permanece disponível mesmo sem histórico persistido.
  }
  return [
    {
      passo: 0,
      suscetiveis: Math.max(total - 4, 0),
      infectados: Math.min(4, total),
      recuperados: 0,
      isolados: 0,
    },
  ]
}

function formatarPercentual(valor: number) {
  return `${(valor * 100).toLocaleString('pt-BR', {
    maximumFractionDigits: 1,
  })}%`
}

export function ResultsPage() {
  const carga = useCargaRede()
  const totalRede = carga.rede?.resumo?.numero_individuos ?? 100
  const [historico, setHistorico] = useState<RegistroResultado[]>([])
  const [resultado, setResultado] = useState<ResultadoSimulacao | null>(null)
  const [comparacao, setComparacao] =
    useState<ResultadoComparacaoExecutada | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState('')
  const [visiveis, setVisiveis] = useState({
    suscetiveis: true,
    infectados: true,
    recuperados: true,
  })

  useEffect(() => {
    const controlador = new AbortController()
    async function carregar() {
      setCarregando(true)
      setErro('')
      try {
        const salvo = JSON.parse(
          sessionStorage.getItem(CHAVE_CONFIGURACAO) ?? 'null',
        ) as {
          repeticoes: string | null
          formulario: FormularioConfiguracao
        } | null

        if (salvo?.formulario) {
          if (salvo.repeticoes) {
            const lote = await executarComparacao(
              salvo.repeticoes,
              salvo.formulario,
              controlador.signal,
            )
            setComparacao(lote)
            const principal =
              lote.execucoes.find((execucao) => execucao.cenario === 'grau') ??
              lote.execucoes.find(
                (execucao) => execucao.cenario === 'aleatoria',
              ) ??
              lote.execucoes[0]
            if (principal) setHistorico(principal.historico)
          } else {
            const ensaio = await executarSimulacao(
              salvo.formulario,
              controlador.signal,
            )
            setResultado(ensaio)
            setHistorico(ensaio.historico)
          }
        } else {
          setHistorico(lerHistoricoLocal(totalRede))
        }
      } catch {
        if (!controlador.signal.aborted) {
          setErro(
            'O backend não pôde executar o resultado. Exibindo o ensaio registrado localmente.',
          )
          setHistorico(lerHistoricoLocal(totalRede))
        }
      } finally {
        if (!controlador.signal.aborted) setCarregando(false)
      }
    }
    void carregar()
    return () => controlador.abort()
  }, [totalRede])

  const atual = historico.at(-1)
  const passoAtual = atual?.passo ?? 0
  const total = resultado?.populacao ?? totalRede
  const pico =
    resultado?.metrica.pico_infectados ??
    Math.max(0, ...historico.map((registro) => registro.infectados))
  const passoPico =
    resultado?.metrica.passo_pico ??
    historico.find((registro) => registro.infectados === pico)?.passo ??
    0
  const fracaoAcumulada =
    resultado?.metrica.fracao_acumulada ??
    (atual ? atual.infectados + atual.recuperados : 0) / Math.max(total, 1)
  const isolados =
    atual?.isolados ??
    historico.reduce((maior, registro) => Math.max(maior, registro.isolados), 0)

  const trajetoriasComparadas = useMemo(() => {
    if (!comparacao) return []
    return (['sem_intervencao', 'aleatoria', 'grau'] as const)
      .map((cenario) => {
        const execucao = comparacao.execucoes.find(
          (item) => item.cenario === cenario,
        )
        return execucao ? { cenario, historico: execucao.historico } : null
      })
      .filter((item): item is NonNullable<typeof item> => item !== null)
  }, [comparacao])

  function exportarCsv() {
    const linhas = [
      ['passo', 'S', 'I', 'R', 'Isolados'],
      ...historico.map((registro) => [
        registro.passo,
        registro.suscetiveis,
        registro.infectados,
        registro.recuperados,
        registro.isolados,
      ]),
    ]
    const csv = linhas.map((linha) => linha.join(';')).join('\n')
    const url = URL.createObjectURL(
      new Blob(['\ufeff', csv], { type: 'text/csv;charset=utf-8' }),
    )
    const link = document.createElement('a')
    link.href = url
    link.download = 'historico-ensaio.csv'
    link.click()
    URL.revokeObjectURL(url)
  }

  const largura = 760
  const altura = 280
  const margem = { esquerda: 46, direita: 18, superior: 18, inferior: 32 }
  const ultimoPasso = Math.max(
    1,
    ...historico.map((registro) => registro.passo),
  )
  const maximo = Math.max(total, 1)
  const x = (passo: number) =>
    margem.esquerda +
    (passo / ultimoPasso) * (largura - margem.esquerda - margem.direita)
  const y = (valor: number) =>
    margem.superior +
    (1 - valor / maximo) * (altura - margem.superior - margem.inferior)
  function linha(campo: 'suscetiveis' | 'infectados' | 'recuperados') {
    return historico
      .map(
        (registro, indice) =>
          `${indice ? 'L' : 'M'} ${x(registro.passo)} ${y(registro[campo])}`,
      )
      .join(' ')
  }

  return (
    <AppShell conectado={carga.conexao === 'online'} etapaAtiva={4}>
      <main id="conteudo" className="workspace results-workspace" tabIndex={-1}>
        <div className="workspace-heading">
          <div>
            <p className="page-eyebrow">04 / Evidências do cenário</p>
            <h1>Leitura do experimento</h1>
            <p>
              Compare trajetórias e examine os registros do cenário
              demonstrativo.
            </p>
          </div>
          <div className="sir-model" role="img" aria-label="Modelo SIR">
            <span>
              <b>S</b>
              <small>{atual?.suscetiveis ?? total}</small>
            </span>
            <i>
              β<Icon nome="arrow" size={33} />
            </i>
            <span>
              <b>I</b>
              <small>{atual?.infectados ?? 0}</small>
            </span>
            <i>
              γ<Icon nome="arrow" size={33} />
            </i>
            <span>
              <b>R</b>
              <small>{atual?.recuperados ?? 0}</small>
            </span>
          </div>
        </div>

        {erro && (
          <p className="results-warning" role="status">
            {erro}
          </p>
        )}

        <section className="result-metrics" aria-label="Métricas consolidadas">
          <article>
            <span>Situação do ensaio</span>
            <strong>
              {carregando ? 'Calculando…' : `Ensaio em t = ${passoAtual}`}
            </strong>
            <small>Estado registrado no passo t = {passoAtual}</small>
          </article>
          <article>
            <span>Pico de infectados</span>
            <strong>{formatarPercentual(pico / Math.max(total, 1))}</strong>
            <small>
              {pico} nós em t = {passoPico}
            </small>
          </article>
          <article>
            <span>Fração acumulada</span>
            <strong>{formatarPercentual(fracaoAcumulada)}</strong>
            <small>
              {Math.round(fracaoAcumulada * total)} nós ao menos uma vez
            </small>
          </article>
          <article>
            <span>Nós sob intervenção</span>
            <strong>{isolados}</strong>
            <small>
              {isolados === 1 ? 'nó isolado' : 'nós isolados'} estruturalmente
            </small>
          </article>
        </section>

        <section
          className="trajectory-panel"
          aria-labelledby="trajectory-title"
        >
          <div className="results-section-heading">
            <div>
              <h2 id="trajectory-title">
                Trajetórias da epidemia <span>RF09</span>
              </h2>
              <p>Evolução temporal dos estados da população</p>
            </div>
            {carregando && (
              <span className="loading-label">Consultando backend…</span>
            )}
          </div>
          <div className="trajectory-legend" aria-label="Legenda das curvas">
            <button
              type="button"
              className={visiveis.suscetiveis ? 'active' : ''}
              aria-pressed={visiveis.suscetiveis}
              onClick={() =>
                setVisiveis((atual) => ({
                  ...atual,
                  suscetiveis: !atual.suscetiveis,
                }))
              }
            >
              <i className="curve-s" /> Suscetíveis (S)
            </button>
            <button
              type="button"
              className={visiveis.infectados ? 'active' : ''}
              aria-pressed={visiveis.infectados}
              onClick={() =>
                setVisiveis((atual) => ({
                  ...atual,
                  infectados: !atual.infectados,
                }))
              }
            >
              <i className="curve-i" /> Infectados (I)
            </button>
            <button
              type="button"
              className={visiveis.recuperados ? 'active' : ''}
              aria-pressed={visiveis.recuperados}
              onClick={() =>
                setVisiveis((atual) => ({
                  ...atual,
                  recuperados: !atual.recuperados,
                }))
              }
            >
              <i className="curve-r" /> Recuperados (R)
            </button>
            {trajetoriasComparadas.map(({ cenario }) => (
              <span key={cenario} className="comparison-key">
                {cenario === 'sem_intervencao'
                  ? 'Sem intervenção'
                  : cenario === 'aleatoria'
                    ? 'Intervenção aleatória'
                    : 'Intervenção por grau'}
              </span>
            ))}
          </div>
          <div className="trajectory-chart">
            {historico.length ? (
              <svg
                viewBox={`0 0 ${largura} ${altura}`}
                role="img"
                aria-label="Curvas SIR ao longo do tempo"
              >
                {[0, 0.25, 0.5, 0.75, 1].map((nivel) => (
                  <g key={nivel}>
                    <line
                      x1={margem.esquerda}
                      x2={largura - margem.direita}
                      y1={y(nivel * maximo)}
                      y2={y(nivel * maximo)}
                      className="chart-grid"
                    />
                    <text
                      x={margem.esquerda - 8}
                      y={y(nivel * maximo) + 4}
                      textAnchor="end"
                      className="chart-label"
                    >
                      {Math.round(nivel * maximo)}
                    </text>
                  </g>
                ))}
                {[
                  0,
                  ultimoPasso / 4,
                  ultimoPasso / 2,
                  (ultimoPasso * 3) / 4,
                  ultimoPasso,
                ].map((passo) => (
                  <text
                    key={passo}
                    x={x(passo)}
                    y={altura - 8}
                    textAnchor="middle"
                    className="chart-label"
                  >
                    {Math.round(passo)}
                  </text>
                ))}
                {visiveis.suscetiveis && (
                  <path d={linha('suscetiveis')} className="chart-s" />
                )}
                {visiveis.infectados && (
                  <path d={linha('infectados')} className="chart-i" />
                )}
                {visiveis.recuperados && (
                  <path d={linha('recuperados')} className="chart-r" />
                )}
              </svg>
            ) : (
              <p className="chart-empty">Nenhum registro disponível.</p>
            )}
          </div>
        </section>

        <section className="history-panel" aria-labelledby="history-title">
          <div className="history-heading">
            <div>
              <h2 id="history-title">
                Histórico por passo <span>RF08</span>
              </h2>
              <p>{historico.length} registros do ensaio</p>
            </div>
            <button
              type="button"
              className="button-primary export-button"
              onClick={exportarCsv}
              disabled={!historico.length}
            >
              ↓ Exportar histórico (.CSV)
            </button>
          </div>
          <div className="history-table-wrap">
            <table className="history-table">
              <thead>
                <tr>
                  <th>t</th>
                  <th>S</th>
                  <th>I</th>
                  <th>R</th>
                  <th>Isolados</th>
                </tr>
              </thead>
              <tbody>
                {historico.map((registro) => (
                  <tr key={registro.passo}>
                    <td>{registro.passo}</td>
                    <td>{registro.suscetiveis}</td>
                    <td>{registro.infectados}</td>
                    <td>{registro.recuperados}</td>
                    <td>{registro.isolados}</td>
                  </tr>
                ))}
                {!historico.length && (
                  <tr>
                    <td colSpan={5} className="history-empty">
                      Nenhum histórico registrado.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </AppShell>
  )
}
