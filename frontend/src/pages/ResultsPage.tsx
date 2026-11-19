import { useEffect, useMemo, useRef, useState } from 'react'
import { AppShell } from '../components/AppShell'
import { Icon } from '../components/Icon'
import { useCargaRede } from '../hooks/useCargaRede'
import {
  executarComparacao,
  executarSimulacao,
  type ExecucaoComparadaResultado,
  type RegistroResultado,
  type ResultadoComparacaoExecutada,
  type ResultadoSimulacao,
  type FormularioConfiguracao,
} from '../services/configuracaoApi'
import './ResultsPage.css'

const CHAVE_CONFIGURACAO = 'observatorio-configuracao'
const CHAVE_RESULTADO = 'observatorio-resultado-execucao'

function execucaoPrincipal(
  comparacao: ResultadoComparacaoExecutada,
): ExecucaoComparadaResultado | undefined {
  return (
    comparacao.execucoes.find((execucao) => execucao.cenario === 'grau') ??
    comparacao.execucoes.find((execucao) => execucao.cenario === 'aleatoria') ??
    comparacao.execucoes[0]
  )
}

function formatarPercentual(valor: number) {
  return `${(valor * 100).toLocaleString('pt-BR', {
    maximumFractionDigits: 1,
  })}%`
}

type CampoCurva = 'suscetiveis' | 'infectados' | 'recuperados' | 'isolados'
type RegistroAgregado = Record<CampoCurva, number> & {
  passo: number
  desvios: Record<CampoCurva, number>
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
    isolados: true,
  })
  const grafico = useRef<SVGSVGElement | null>(null)

  useEffect(() => {
    const controlador = new AbortController()
    async function carregar() {
      setCarregando(true)
      setErro('')
      try {
        setResultado(null)
        setComparacao(null)
        setHistorico([])
        const concluido = JSON.parse(
          sessionStorage.getItem(CHAVE_RESULTADO) ?? 'null',
        ) as
          | {
              tipo: 'individual'
              resultado: ResultadoSimulacao
            }
          | {
              tipo: 'comparacao'
              comparacao: ResultadoComparacaoExecutada
            }
          | null

        const contextoAtual = carga.rede?.contexto_rede
        const revisaoAtual = carga.rede?.revisao
        const resultadoRede =
          concluido?.tipo === 'individual'
            ? concluido.resultado
            : concluido?.tipo === 'comparacao'
              ? concluido.comparacao
              : null
        if (
          resultadoRede &&
          contextoAtual &&
          (resultadoRede.contexto_rede !== contextoAtual ||
            resultadoRede.revisao_rede !== revisaoAtual)
        ) {
          sessionStorage.removeItem(CHAVE_RESULTADO)
          sessionStorage.removeItem('observatorio-historico-ensaio')
          throw new Error(
            'O resultado foi invalidado porque a revisão ou o contexto da rede mudou.',
          )
        }

        if (concluido?.tipo === 'individual') {
          setResultado(concluido.resultado)
          setHistorico(concluido.resultado.historico)
        } else if (concluido?.tipo === 'comparacao') {
          setComparacao(concluido.comparacao)
          const principal = execucaoPrincipal(concluido.comparacao)
          if (principal) setHistorico(principal.historico)
        } else {
          const salvo = JSON.parse(
            sessionStorage.getItem(CHAVE_CONFIGURACAO) ?? 'null',
          ) as {
            repeticoes: string | null
            formulario: FormularioConfiguracao
          } | null

          if (salvo?.formulario) {
            if (
              !carga.rede ||
              salvo.formulario.contexto_rede !== carga.rede.contexto_rede ||
              Number(salvo.formulario.revisao_rede) !== carga.rede.revisao
            ) {
              throw new Error(
                'A configuração foi invalidada porque a revisão ou o contexto da rede mudou.',
              )
            }
            if (salvo.repeticoes) {
              const lote = await executarComparacao(
                salvo.repeticoes,
                salvo.formulario,
                controlador.signal,
              )
              setComparacao(lote)
              const principal = execucaoPrincipal(lote)
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
            setErro('Nenhum ensaio concluído. Execute a simulação na Tela 03.')
            setHistorico([])
          }
        }
      } catch (falha) {
        if (!controlador.signal.aborted) {
          setErro(
            falha instanceof Error
              ? falha.message
              : 'Não foi possível carregar os resultados do backend.',
          )
          setHistorico([])
        }
      } finally {
        if (!controlador.signal.aborted) setCarregando(false)
      }
    }
    void carregar()
    return () => controlador.abort()
  }, [carga.rede, totalRede])

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
  const horizonteObservado =
    resultado?.metrica.horizonte_observado ??
    (comparacao
      ? comparacao.execucoes.reduce(
          (maior, execucao) =>
            Math.max(maior, execucao.metrica.horizonte_observado),
          0,
        )
      : passoAtual)
  const trajetoriasComparadas = useMemo(() => {
    if (!comparacao) return []
    return comparacao.execucoes
  }, [comparacao])

  const curvasAgregadas = useMemo(() => {
    if (!comparacao) return []
    return (['sem_intervencao', 'aleatoria', 'grau'] as const).flatMap(
      (cenario) => {
        const execucoes = comparacao.execucoes.filter(
          (execucao) => execucao.cenario === cenario,
        )
        if (!execucoes.length) return []
        const horizonte = Math.max(
          ...execucoes.map((execucao) =>
            Math.max(...execucao.historico.map((registro) => registro.passo)),
          ),
        )
        const registros: RegistroAgregado[] = []
        for (let passo = 0; passo <= horizonte; passo += 1) {
          const observacoes = execucoes
            .map((execucao) => {
              const anteriores = execucao.historico.filter(
                (registro) => registro.passo <= passo,
              )
              return anteriores.at(-1)
            })
            .filter((registro): registro is RegistroResultado => !!registro)
          if (!observacoes.length) continue
          const media = (campo: CampoCurva) =>
            observacoes.reduce((soma, registro) => soma + registro[campo], 0) /
            observacoes.length
          const desvios = {} as Record<CampoCurva, number>
          const valores = {} as Record<CampoCurva, number>
          for (const campo of [
            'suscetiveis',
            'infectados',
            'recuperados',
            'isolados',
          ] as const) {
            valores[campo] = media(campo)
            desvios[campo] = Math.sqrt(
              observacoes.reduce(
                (soma, registro) => soma + (registro[campo] - valores[campo]) ** 2,
                0,
              ) / observacoes.length,
            )
          }
          registros.push({ passo, ...valores, desvios })
        }
        return [{ cenario, registros }]
      },
    )
  }, [comparacao])

  const execucaoSelecionada = comparacao
    ? execucaoPrincipal(comparacao)
    : undefined
  const descricaoCenario = execucaoSelecionada
    ? `${execucaoSelecionada.cenario === 'sem_intervencao' ? 'Sem intervenção' : execucaoSelecionada.cenario === 'aleatoria' ? 'Intervenção aleatória' : 'Intervenção por grau'} · repetição ${execucaoSelecionada.repeticao}`
    : resultado
      ? 'Execução única'
      : null
  const motivoTermino =
    resultado?.motivo_termino ?? execucaoSelecionada?.motivo_termino ?? null

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

  function baixar(conteudo: BlobPart, nome: string, tipo: string) {
    const url = URL.createObjectURL(new Blob([conteudo], { type: tipo }))
    const link = document.createElement('a')
    link.href = url
    link.download = nome
    link.click()
    URL.revokeObjectURL(url)
  }

  function exportarCsvAgregado() {
    if (!comparacao) return
    const linhas = [['repeticao', 'cenario', 'passo', 'S', 'I', 'R', 'Isolados']]
    for (const execucao of comparacao.execucoes) {
      for (const registro of execucao.historico) {
        linhas.push([
          execucao.repeticao,
          execucao.cenario,
          registro.passo,
          registro.suscetiveis,
          registro.infectados,
          registro.recuperados,
          registro.isolados,
        ].map(String))
      }
    }
    baixar(
      `\ufeff${linhas.map((linha) => linha.join(';')).join('\n')}`,
      'trajetorias-comparacao.csv',
      'text/csv;charset=utf-8',
    )
  }

  function exportarJson() {
    const salvo = sessionStorage.getItem(CHAVE_RESULTADO)
    if (salvo) baixar(salvo, 'metadados-ensaio.json', 'application/json')
  }

  function exportarSvg() {
    if (!grafico.current) return
    const clone = grafico.current.cloneNode(true) as SVGSVGElement
    clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
    baixar(
      new XMLSerializer().serializeToString(clone),
      'trajetorias-epidemia.svg',
      'image/svg+xml;charset=utf-8',
    )
  }

  function exportarPng() {
    if (!grafico.current) return
    const svg = new XMLSerializer().serializeToString(grafico.current)
    const imagem = new Image()
    imagem.onload = () => {
      const canvas = document.createElement('canvas')
      canvas.width = largura * 2
      canvas.height = altura * 2
      const contexto = canvas.getContext('2d')
      if (!contexto) {
        setErro('Não foi possível preparar a exportação PNG.')
        return
      }
      contexto.scale(2, 2)
      contexto.drawImage(imagem, 0, 0, largura, altura)
      canvas.toBlob((blob) => {
        if (blob) baixar(blob, 'trajetorias-epidemia.png', 'image/png')
        else setErro('Não foi possível gerar o arquivo PNG.')
      }, 'image/png')
    }
    imagem.onerror = () => setErro('Não foi possível gerar o arquivo PNG.')
    imagem.src = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`
  }

  const largura = 760
  const altura = 280
  const margem = { esquerda: 46, direita: 18, superior: 18, inferior: 32 }
  const ultimoPasso = Math.max(
    1,
    ...historico.map((registro) => registro.passo),
    ...(comparacao?.execucoes.flatMap((execucao) =>
      execucao.historico.map((registro) => registro.passo),
    ) ?? []),
  )
  const maximo = Math.max(total, 1)
  const x = (passo: number) =>
    margem.esquerda +
    (passo / ultimoPasso) * (largura - margem.esquerda - margem.direita)
  const y = (valor: number) =>
    margem.superior +
    (1 - valor / maximo) * (altura - margem.superior - margem.inferior)
  function linha(
    campo: 'suscetiveis' | 'infectados' | 'recuperados' | 'isolados',
  ) {
    return historico
      .map(
        (registro, indice) =>
          `${indice ? 'L' : 'M'} ${x(registro.passo)} ${y(registro[campo])}`,
      )
      .join(' ')
  }

  function linhaComparada(
    execucao: ExecucaoComparadaResultado,
    campo: 'suscetiveis' | 'infectados' | 'recuperados' | 'isolados',
  ) {
    return execucao.historico
      .map((registro, indice) => {
        const passoMaximo = Math.max(
          1,
          ...execucao.historico.map((item) => item.passo),
        )
        const pontoX =
          margem.esquerda +
          (registro.passo / Math.max(ultimoPasso, passoMaximo)) *
            (largura - margem.esquerda - margem.direita)
        return `${indice ? 'L' : 'M'} ${pontoX} ${y(registro[campo])}`
      })
      .join(' ')
  }

  function linhaAgregada(
    registros: RegistroAgregado[],
    campo: CampoCurva,
  ) {
    return registros
      .map(
        (registro, indice) =>
          `${indice ? 'L' : 'M'} ${x(registro.passo)} ${y(registro[campo])}`,
      )
      .join(' ')
  }

  function areaDesvio(registros: RegistroAgregado[], campo: CampoCurva) {
    const superior = registros.map(
      (registro, indice) =>
        `${indice ? 'L' : 'M'} ${x(registro.passo)} ${y(
          Math.min(maximo, registro[campo] + registro.desvios[campo]),
        )}`,
    )
    const inferior = [...registros].reverse().map((registro) =>
      `L ${x(registro.passo)} ${y(
        Math.max(0, registro[campo] - registro.desvios[campo]),
      )}`,
    )
    return `${superior.join(' ')} ${inferior.join(' ')} Z`
  }

  return (
    <AppShell conectado={carga.conexao === 'online'} etapaAtiva={4}>
      <main id="conteudo" className="workspace results-workspace" tabIndex={-1}>
        <div className="workspace-heading">
          <div>
            <p className="page-eyebrow">04 / Evidências do cenário</p>
            <h1>Leitura do experimento</h1>
            <p>
              Compare trajetórias e examine os registros do cenário observado.
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
            <small>
              {descricaoCenario ?? 'Nenhum cenário selecionado'} · Horizonte
              observado: t = {horizonteObservado}
            </small>
          </article>
          <article>
            <span>Motivo do término</span>
            <strong>
              {motivoTermino === 'extincao'
                ? 'Extinção da epidemia'
                : motivoTermino === 'limite_passos'
                  ? 'Limite máximo de passos'
                  : 'Aguardando execução'}
            </strong>
            <small>
              {motivoTermino
                ? `Resultado registrado em t = ${horizonteObservado}`
                : 'Execute o ensaio na Tela 03'}
            </small>
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
            <span>Fração final recuperada</span>
            <strong>
              {formatarPercentual(
                resultado?.metrica.fracao_final_recuperados ??
                  (atual ? atual.recuperados / Math.max(total, 1) : 0),
              )}
            </strong>
            <small>Recuperados no último registro</small>
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
            <button
              type="button"
              className={visiveis.isolados ? 'active' : ''}
              aria-pressed={visiveis.isolados}
              onClick={() =>
                setVisiveis((atual) => ({
                  ...atual,
                  isolados: !atual.isolados,
                }))
              }
            >
              <i className="curve-q" /> Isolados (Q)
            </button>
            {trajetoriasComparadas.map((execucao) => (
              <span
                key={`${execucao.cenario}-${execucao.repeticao}`}
                className="comparison-key"
              >
                {execucao.cenario === 'sem_intervencao'
                  ? `Sem intervenção · r${execucao.repeticao}`
                  : execucao.cenario === 'aleatoria'
                    ? `Aleatória · r${execucao.repeticao}`
                    : `Por grau · r${execucao.repeticao}`}
              </span>
            ))}
            {curvasAgregadas.length > 0 && (
              <span className="comparison-key">
                    Linhas grossas: média · faixas: desvio-padrão
              </span>
            )}
          </div>
          <div className="trajectory-chart">
            {historico.length ? (
              <svg
                ref={grafico}
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
                {visiveis.isolados && (
                  <path d={linha('isolados')} className="chart-q" />
                )}
                {trajetoriasComparadas.map((execucao, indice) => (
                  <g
                    key={`${execucao.cenario}-${execucao.repeticao}`}
                    className={`comparison-series comparison-${execucao.cenario}`}
                    opacity={0.72}
                  >
                    {visiveis.suscetiveis && (
                      <path
                        d={linhaComparada(execucao, 'suscetiveis')}
                        className="comparison-s"
                        strokeDasharray={indice % 2 ? '7 4' : undefined}
                      />
                    )}
                    {visiveis.infectados && (
                      <path
                        d={linhaComparada(execucao, 'infectados')}
                        className="comparison-i"
                        strokeDasharray={indice % 2 ? '7 4' : undefined}
                      />
                    )}
                    {visiveis.recuperados && (
                      <path
                        d={linhaComparada(execucao, 'recuperados')}
                        className="comparison-r"
                        strokeDasharray={indice % 2 ? '7 4' : undefined}
                      />
                    )}
                    {visiveis.isolados && (
                      <path
                        d={linhaComparada(execucao, 'isolados')}
                        className="comparison-q"
                        strokeDasharray={indice % 2 ? '7 4' : undefined}
                      />
                    )}
                  </g>
                ))}
                {curvasAgregadas.map(({ cenario, registros }, indice) => (
                  <g
                    key={`media-${cenario}`}
                    className={`comparison-series comparison-mean comparison-${cenario}`}
                    aria-label={`Média e desvio-padrão do cenário ${cenario}`}
                  >
                    {(
                      ['suscetiveis', 'infectados', 'recuperados', 'isolados'] as const
                    ).map((campo) => (
                      <path
                        key={`${cenario}-${campo}-desvio`}
                        d={areaDesvio(registros, campo)}
                        className={`comparison-band band-${campo}`}
                      />
                    ))}
                    {visiveis.suscetiveis && (
                      <path
                        d={linhaAgregada(registros, 'suscetiveis')}
                        className="comparison-s"
                        strokeDasharray={indice % 2 ? '3 3' : undefined}
                      />
                    )}
                    {visiveis.infectados && (
                      <path
                        d={linhaAgregada(registros, 'infectados')}
                        className="comparison-i"
                        strokeDasharray={indice % 2 ? '3 3' : undefined}
                      />
                    )}
                    {visiveis.recuperados && (
                      <path
                        d={linhaAgregada(registros, 'recuperados')}
                        className="comparison-r"
                        strokeDasharray={indice % 2 ? '3 3' : undefined}
                      />
                    )}
                    {visiveis.isolados && (
                      <path
                        d={linhaAgregada(registros, 'isolados')}
                        className="comparison-q"
                        strokeDasharray={indice % 2 ? '3 3' : undefined}
                      />
                    )}
                  </g>
                ))}
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
            <div className="export-actions">
              <button type="button" onClick={exportarSvg} disabled={!historico.length}>
                SVG
              </button>
              <button type="button" onClick={exportarPng} disabled={!historico.length}>
                PNG
              </button>
              {comparacao && (
                <button type="button" onClick={exportarCsvAgregado}>
                  CSV agregado
                </button>
              )}
              <button type="button" onClick={exportarJson} disabled={!sessionStorage.getItem(CHAVE_RESULTADO)}>
                JSON
              </button>
            </div>
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
