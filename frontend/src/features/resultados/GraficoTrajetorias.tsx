import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type Dispatch,
  type RefObject,
  type SetStateAction,
} from 'react'
import type {
  RegistroResultado,
  ResultadoComparacaoExecutada,
} from '../../services/configuracaoApi'
import {
  agregarCurvas,
  CAMPOS_CURVA,
  caminhoEscalonado,
  CORES_CENARIOS,
  maximoHistorico,
  NOMES_CENARIOS,
  type CampoCurva,
  type RegistroAgregado,
} from './dadosResultados'

import {
  filtrosTrajetoriasPadrao,
  type CenarioGrafico as Cenario,
  type FiltrosTrajetorias,
  type ModoGrafico,
} from './filtrosTrajetorias'

const CENARIOS = Object.keys(NOMES_CENARIOS) as Cenario[]
const SERIES = {
  suscetiveis: { nome: 'Suscetíveis (S)', classe: 's' },
  infectados: { nome: 'Infectados (I)', classe: 'i' },
  recuperados: { nome: 'Recuperados (R)', classe: 'r' },
  isolados: { nome: 'Isolados (Q)', classe: 'q' },
}

function IntervaloPassos({
  inicio,
  fim,
  horizonte,
  onAplicar,
}: {
  inicio: number
  fim: number
  horizonte: number
  onAplicar: (inicio: number, fim: number) => void
}) {
  const [de, setDe] = useState(String(inicio))
  const [ate, setAte] = useState(String(fim))
  const [erro, setErro] = useState('')
  return (
    <form
      className="trajectory-range"
      noValidate
      onSubmit={(evento) => {
        evento.preventDefault()
        const primeiro = Number(de)
        const ultimo = Number(ate)
        if (
          !de.trim() ||
          !ate.trim() ||
          !Number.isInteger(primeiro) ||
          !Number.isInteger(ultimo) ||
          primeiro < 0 ||
          ultimo > horizonte ||
          primeiro > ultimo
        ) {
          setErro(
            `Use passos inteiros de 0 a ${horizonte}, com o início menor ou igual ao fim.`,
          )
          return
        }
        setErro('')
        onAplicar(primeiro, ultimo)
      }}
    >
      <fieldset>
        <legend>Intervalo de passos</legend>
        <label htmlFor="grafico-inicio">
          De
          <input
            id="grafico-inicio"
            type="number"
            min={0}
            max={horizonte}
            step={1}
            value={de}
            aria-invalid={!!erro}
            aria-describedby={erro ? 'grafico-intervalo-erro' : undefined}
            onChange={(evento) => setDe(evento.target.value)}
          />
        </label>
        <label htmlFor="grafico-fim">
          Até
          <input
            id="grafico-fim"
            type="number"
            min={0}
            max={horizonte}
            step={1}
            value={ate}
            aria-invalid={!!erro}
            aria-describedby={erro ? 'grafico-intervalo-erro' : undefined}
            onChange={(evento) => setAte(evento.target.value)}
          />
        </label>
        <button className="trajectory-apply" type="submit">
          Aplicar
        </button>
      </fieldset>
      {erro && (
        <p
          className="trajectory-range-error"
          id="grafico-intervalo-erro"
          role="alert"
        >
          {erro}
        </p>
      )}
    </form>
  )
}

interface Props {
  historico: RegistroResultado[]
  comparacao: ResultadoComparacaoExecutada | null
  populacao: number
  carregando: boolean
  filtros: FiltrosTrajetorias
  onAlterar: Dispatch<SetStateAction<FiltrosTrajetorias>>
  grafico: RefObject<SVGSVGElement | null>
  onExportarSvg: () => void
  onExportarPng: () => void
}

export function GraficoTrajetorias({
  historico,
  comparacao,
  populacao,
  carregando,
  filtros,
  onAlterar,
  grafico,
  onExportarSvg,
  onExportarPng,
}: Props) {
  const recipiente = useRef<HTMLDivElement | null>(null)
  const [largura, setLargura] = useState(760)
  const [edicaoIntervalo, setEdicaoIntervalo] = useState(0)
  useEffect(() => {
    if (!recipiente.current || typeof ResizeObserver === 'undefined') return
    const observador = new ResizeObserver(([entrada]) => {
      if (entrada)
        setLargura(Math.min(760, Math.max(280, entrada.contentRect.width)))
    })
    observador.observe(recipiente.current)
    return () => observador.disconnect()
  }, [])
  const repeticoes = useMemo(
    () =>
      [...new Set(comparacao?.execucoes.map((item) => item.repeticao))].sort(
        (a, b) => a - b,
      ),
    [comparacao],
  )
  const horizonte = useMemo(
    () =>
      comparacao
        ? comparacao.execucoes.reduce(
            (maior, item) =>
              Math.max(maior, maximoHistorico(item.historico, 'passo')),
            0,
          )
        : maximoHistorico(historico, 'passo'),
    [comparacao, historico],
  )
  const agregadas = useMemo(
    () => (comparacao ? agregarCurvas(comparacao) : []),
    [comparacao],
  )
  const repeticao = repeticoes.includes(filtros.repeticao ?? -1)
    ? filtros.repeticao!
    : (repeticoes[0] ?? 1)
  const fim = Math.min(filtros.fim ?? horizonte, horizonte)
  const inicio = Math.min(filtros.inicio, fim)
  const campos = CAMPOS_CURVA.filter((campo) => filtros.series[campo])
  const cenarios = CENARIOS.filter((cenario) => filtros.cenarios[cenario])
  const trajetorias = useMemo(
    () =>
      comparacao?.execucoes.filter(
        (item) =>
          filtros.cenarios[item.cenario] &&
          (filtros.modo === 'todas' ||
            (filtros.modo === 'repeticao' && item.repeticao === repeticao)),
      ) ?? [],
    [comparacao, filtros.cenarios, filtros.modo, repeticao],
  )
  const medias = agregadas.filter(
    (item) => filtros.modo === 'medias' && filtros.cenarios[item.cenario],
  )
  const altura = 300
  const margem = { esquerda: 46, direita: 18, superior: 18, inferior: 36 }
  const maximo = Math.max(populacao, 1)
  const x = (passo: number) =>
    margem.esquerda +
    ((passo - inicio) / Math.max(fim - inicio, 1)) *
      (largura - margem.esquerda - margem.direita)
  const y = (valor: number) =>
    margem.superior +
    (1 - valor / maximo) * (altura - margem.superior - margem.inferior)
  const noIntervalo = <T extends { passo: number }>(registros: T[]) =>
    registros.filter(
      (registro) => registro.passo >= inicio && registro.passo <= fim,
    )
  const marcas = [
    ...new Set(
      Array.from({ length: 5 }, (_, indice) =>
        Math.round(inicio + ((fim - inicio) * indice) / 4),
      ),
    ),
  ]
  const linhas = comparacao
    ? [
        ...medias.map((item) => ({
          ...item,
          registros: noIntervalo(item.registros),
        })),
        ...trajetorias.map((item) => ({
          ...item,
          registros: noIntervalo(item.historico),
        })),
      ]
    : [{ registros: noIntervalo(historico) }]
  const temCurvas =
    campos.length > 0 && linhas.some((item) => item.registros.length > 0)
  const descricao = comparacao
    ? filtros.modo === 'medias'
      ? `Médias de ${repeticoes.length} ${repeticoes.length === 1 ? 'repetição' : 'repetições'} por cenário`
      : filtros.modo === 'repeticao'
        ? `Repetição ${repeticao} · ${trajetorias.length} ${trajetorias.length === 1 ? 'trajetória' : 'trajetórias'}`
        : `${trajetorias.length} trajetórias · todas as repetições`
    : 'Execução individual'
  const resumo = `${descricao} · passos ${inicio} a ${fim}`

  function curva(
    registros: RegistroResultado[] | RegistroAgregado[],
    campo: CampoCurva,
    classe: string,
  ) {
    const pontos = noIntervalo(registros)
    if (!pontos.length) return null
    if (pontos.length === 1)
      return (
        <circle
          key={campo}
          cx={x(pontos[0].passo)}
          cy={y(pontos[0][campo])}
          r={3}
          className={classe}
        />
      )
    return (
      <path
        key={campo}
        className={classe}
        d={caminhoEscalonado(
          pontos.map((registro) => [x(registro.passo), y(registro[campo])]),
        )}
      />
    )
  }

  function areaDesvio(registros: RegistroAgregado[], campo: CampoCurva) {
    const pontos = noIntervalo(registros)
    if (
      !pontos.length ||
      pontos.some((registro) => registro.desvios[campo] === null)
    )
      return null
    const limites = pontos.map((registro) => ({
      passo: registro.passo,
      superior: Math.min(maximo, registro[campo] + registro.desvios[campo]!),
      inferior: Math.max(0, registro[campo] - registro.desvios[campo]!),
    }))
    const borda = (campo: 'superior' | 'inferior') =>
      limites.flatMap((registro, indice) =>
        indice
          ? [
              [x(registro.passo), y(limites[indice - 1][campo])],
              [x(registro.passo), y(registro[campo])],
            ]
          : [[x(registro.passo), y(registro[campo])]],
      )
    return (
      [...borda('superior'), ...borda('inferior').reverse()]
        .map(([px, py], indice) => `${indice ? 'L' : 'M'} ${px} ${py}`)
        .join(' ') + ' Z'
    )
  }

  return (
    <section className="trajectory-panel" aria-labelledby="trajectory-title">
      <div className="results-section-heading">
        <div>
          <h2 id="trajectory-title">Trajetórias da epidemia</h2>
          <p>Escolha o que comparar e o intervalo de passos.</p>
        </div>
        <div className="trajectory-actions">
          <button
            type="button"
            className="trajectory-reset"
            onClick={() => {
              onAlterar(filtrosTrajetoriasPadrao())
              setEdicaoIntervalo((atual) => atual + 1)
            }}
          >
            Restaurar visualização
          </button>
          <div className="export-actions">
            <button
              type="button"
              onClick={onExportarSvg}
              disabled={carregando || !temCurvas}
            >
              SVG
            </button>
            <button
              type="button"
              onClick={onExportarPng}
              disabled={carregando || !temCurvas}
            >
              PNG
            </button>
          </div>
        </div>
      </div>
      <div className="trajectory-filters" aria-label="Filtros do gráfico">
        <fieldset>
          <legend>Estados</legend>
          <div className="trajectory-legend">
            {CAMPOS_CURVA.map((campo) => (
              <button
                key={campo}
                type="button"
                className={filtros.series[campo] ? 'active' : ''}
                aria-pressed={filtros.series[campo]}
                onClick={() =>
                  onAlterar((atual) => ({
                    ...atual,
                    series: { ...atual.series, [campo]: !atual.series[campo] },
                  }))
                }
              >
                <i
                  className={`curve-${SERIES[campo].classe}`}
                  aria-hidden="true"
                />
                {SERIES[campo].nome}
              </button>
            ))}
          </div>
        </fieldset>
        {comparacao && (
          <fieldset>
            <legend>Cenários</legend>
            <div className="trajectory-scenarios">
              {CENARIOS.map((cenario) => (
                <button
                  key={cenario}
                  type="button"
                  aria-pressed={filtros.cenarios[cenario]}
                  onClick={() =>
                    onAlterar((atual) => ({
                      ...atual,
                      cenarios: {
                        ...atual.cenarios,
                        [cenario]: !atual.cenarios[cenario],
                      },
                    }))
                  }
                >
                  <i
                    style={{ background: CORES_CENARIOS[cenario] }}
                    aria-hidden="true"
                  />
                  {NOMES_CENARIOS[cenario]}
                </button>
              ))}
            </div>
          </fieldset>
        )}
        <div className="trajectory-options">
          {comparacao && (
            <>
              <label className="trajectory-field" htmlFor="grafico-modo">
                Exibição
                <select
                  id="grafico-modo"
                  value={filtros.modo}
                  onChange={(evento) =>
                    onAlterar((atual) => ({
                      ...atual,
                      modo: evento.target.value as ModoGrafico,
                    }))
                  }
                >
                  <option value="medias">Médias por cenário</option>
                  <option value="repeticao">Uma repetição</option>
                  <option value="todas">Todas as repetições</option>
                </select>
              </label>
              {filtros.modo === 'repeticao' && (
                <label className="trajectory-field" htmlFor="grafico-repeticao">
                  Repetição do gráfico
                  <select
                    id="grafico-repeticao"
                    value={repeticao}
                    onChange={(evento) =>
                      onAlterar((atual) => ({
                        ...atual,
                        repeticao: Number(evento.target.value),
                      }))
                    }
                  >
                    {repeticoes.map((numero) => (
                      <option key={numero} value={numero}>
                        Repetição {numero}
                      </option>
                    ))}
                  </select>
                </label>
              )}
              {filtros.modo === 'medias' && (
                <label className="trajectory-deviation">
                  <input
                    type="checkbox"
                    checked={filtros.mostrarDesvio}
                    onChange={(evento) =>
                      onAlterar((atual) => ({
                        ...atual,
                        mostrarDesvio: evento.target.checked,
                      }))
                    }
                  />
                  Mostrar desvio-padrão
                </label>
              )}
            </>
          )}
          <IntervaloPassos
            key={`${edicaoIntervalo}-${horizonte}`}
            inicio={inicio}
            fim={fim}
            horizonte={horizonte}
            onAplicar={(inicio, fim) =>
              onAlterar((atual) => ({ ...atual, inicio, fim }))
            }
          />
        </div>
      </div>
      <p className="trajectory-summary" role="status">
        {carregando ? 'Consultando backend…' : resumo}
      </p>
      <div className="trajectory-chart" ref={recipiente}>
        {temCurvas ? (
          <svg
            ref={grafico}
            viewBox={`0 0 ${largura} ${altura}`}
            role="img"
            aria-label={`Curvas SIR ao longo do tempo. ${resumo}`}
          >
            <desc>
              {comparacao
                ? `Cenários: ${cenarios.map((cenario) => NOMES_CENARIOS[cenario]).join(', ')}. `
                : ''}
              Os filtros alteram somente o gráfico; métricas e histórico mantêm
              a execução selecionada no painel.
              {comparacao && filtros.modo === 'medias'
                ? ' As médias mantêm n constante por cenário e prolongam apenas extinções. O desvio amostral fica ausente com uma repetição.'
                : ''}
            </desc>
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
            {marcas.map((passo) => (
              <text
                key={passo}
                x={x(passo)}
                y={altura - 8}
                textAnchor="middle"
                className="chart-label chart-step"
              >
                {passo}
              </text>
            ))}
            {!comparacao &&
              campos.map((campo) =>
                curva(historico, campo, `chart-${SERIES[campo].classe}`),
              )}
            {trajetorias.map((execucao) => (
              <g
                key={`${execucao.cenario}-${execucao.repeticao}`}
                className={`comparison-series comparison-${execucao.cenario}`}
                style={{ color: CORES_CENARIOS[execucao.cenario] }}
                data-repeticao={execucao.repeticao}
              >
                <title>
                  {NOMES_CENARIOS[execucao.cenario]} · repetição{' '}
                  {execucao.repeticao}
                </title>
                {campos.map((campo) =>
                  curva(
                    execucao.historico,
                    campo,
                    `comparison-${SERIES[campo].classe}`,
                  ),
                )}
              </g>
            ))}
            {medias.map(({ cenario, registros }) => (
              <g
                key={`media-${cenario}`}
                className={`comparison-series comparison-mean comparison-${cenario}`}
                style={{ color: CORES_CENARIOS[cenario] }}
                aria-label={`Média do cenário ${NOMES_CENARIOS[cenario]}`}
              >
                {filtros.mostrarDesvio &&
                  noIntervalo(registros).length > 1 &&
                  campos.map((campo) => {
                    const area = areaDesvio(registros, campo)
                    return area ? (
                      <path
                        key={`${campo}-desvio`}
                        d={area}
                        className={`comparison-band band-${campo}`}
                      />
                    ) : null
                  })}
                {campos.map((campo) =>
                  curva(registros, campo, `comparison-${SERIES[campo].classe}`),
                )}
              </g>
            ))}
          </svg>
        ) : (
          <p className="chart-empty">
            {!historico.length
              ? 'Nenhum registro disponível.'
              : !campos.length
                ? 'Selecione pelo menos um estado para exibir as curvas.'
                : !cenarios.length && comparacao
                  ? 'Selecione pelo menos um cenário para comparar.'
                  : 'Não há registros no intervalo escolhido. Amplie o intervalo de passos.'}
          </p>
        )}
      </div>
      <p className="trajectory-help">
        {comparacao
          ? 'Cores: cenários. Traços: S contínuo · I tracejado · R pontilhado · Q misto. '
          : ''}
        Os filtros afetam o gráfico e suas imagens. O histórico e os arquivos
        CSV/JSON conservam os dados completos.
      </p>
    </section>
  )
}
