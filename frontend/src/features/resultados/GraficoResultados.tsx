import { useMemo, useState, type RefObject } from 'react'
import type {
  RegistroResultado,
  ResultadoComparacaoExecutada,
} from '../../services/configuracaoApi'
import {
  agregarCurvas,
  CAMPOS_CURVA,
  caminhoEscalonado,
  escalaContagem,
  registroNoPasso,
  CORES_CENARIOS,
  NOMES_CENARIOS,
  type CampoCurva,
  type RegistroAgregado,
} from './dadosResultados'

const CAMPOS = {
  suscetiveis: { nome: 'Suscetíveis (S)', cor: '#4c78a8' },
  infectados: { nome: 'Infectados (I)', cor: '#c94d4d' },
  recuperados: { nome: 'Recuperados (R)', cor: '#4c9a72' },
  isolados: { nome: 'Isolados (Q)', cor: '#8c6bb1' },
}
const TRACOS = { sem_intervencao: '', aleatoria: '9 5', grau: '2 4' }
type Cenario = keyof typeof NOMES_CENARIOS
type Registro = RegistroResultado | RegistroAgregado
type Serie = {
  id: string
  nome: string
  campo: CampoCurva
  cor: string
  traco: string
  registros: Registro[]
  media: boolean
  censuradas: number
}
type Props = {
  historico: RegistroResultado[]
  comparacao: ResultadoComparacaoExecutada | null
  populacao: number
  grafico: RefObject<SVGSVGElement | null>
}

export function GraficoResultados({
  historico,
  comparacao,
  populacao,
  grafico,
}: Props) {
  const [campo, setCampo] = useState<CampoCurva | 'todos'>(
    comparacao ? 'infectados' : 'todos',
  )
  const [modo, setModo] = useState('medias')
  const [repeticao, setRepeticao] = useState(1)
  const [desvios, setDesvios] = useState(false)
  const [escala, setEscala] = useState('ajustada')
  const [passoConsultado, setPassoConsultado] = useState(0)
  const [cenarios, setCenarios] = useState<Cenario[]>([
    'sem_intervencao',
    'aleatoria',
    'grau',
  ])
  const [tabelaAberta, setTabelaAberta] = useState(false)
  const [pagina, setPagina] = useState(0)
  const agregadas = useMemo(
    () => (comparacao ? agregarCurvas(comparacao) : []),
    [comparacao],
  )
  const repeticoes = useMemo(
    () =>
      [...new Set(comparacao?.execucoes.map((e) => e.repeticao) ?? [])].sort(
        (a, b) => a - b,
      ),
    [comparacao],
  )
  const series = useMemo(() => {
    const campos = campo === 'todos' ? CAMPOS_CURVA : [campo]
    if (!comparacao)
      return campos.map((c) => ({
        id: c,
        nome: CAMPOS[c].nome,
        campo: c,
        cor: CAMPOS[c].cor,
        traco: '',
        registros: historico,
        media: false,
        censuradas: 0,
      }))
    const bases =
      modo === 'medias'
        ? agregadas.map((g) => ({
            cenario: g.cenario,
            registros: g.registros as Registro[],
            censuradas: comparacao.execucoes.filter(
              (e) =>
                e.cenario === g.cenario && e.motivo_termino === 'limite_passos',
            ).length,
          }))
        : comparacao.execucoes
            .filter((e) => e.repeticao === repeticao)
            .map((e) => ({
              cenario: e.cenario,
              registros: e.historico as Registro[],
              censuradas: Number(e.motivo_termino === 'limite_passos'),
            }))
    return bases
      .filter((b) => cenarios.includes(b.cenario))
      .flatMap((b) =>
        campos.map((c) => ({
          id: `${b.cenario}-${c}`,
          nome: `${NOMES_CENARIOS[b.cenario]}${campo === 'todos' ? ` · ${CAMPOS[c].nome}` : ''}`,
          campo: c,
          cor: campo === 'todos' ? CAMPOS[c].cor : CORES_CENARIOS[b.cenario],
          traco: TRACOS[b.cenario],
          registros: b.registros,
          media: modo === 'medias',
          censuradas: b.censuradas,
        })),
      )
  }, [campo, comparacao, historico, modo, repeticao, agregadas, cenarios])
  const largura = 1000
  const altura = 390 + Math.ceil(series.length / 3) * 22
  const margem = {
    esquerda: 64,
    direita: 28,
    superior: 42 + Math.ceil(series.length / 3) * 22,
    inferior: 64,
  }
  const horizonte = Math.max(
    1,
    comparacao
      ? comparacao.execucoes.reduce(
          (maior, e) => Math.max(maior, e.historico.at(-1)?.passo ?? 0),
          0,
        )
      : (historico.at(-1)?.passo ?? 0),
  )
  const x = (passo: number) =>
    margem.esquerda +
    (passo / horizonte) * (largura - margem.esquerda - margem.direita)
  const maiorValor = useMemo(
    () =>
      series.reduce(
        (maior, serie) =>
          serie.registros.reduce((atual, registro) => {
            const desvio =
              desvios && serie.media && 'desvios' in registro
                ? (registro.desvios[serie.campo] ?? 0)
                : 0
            return Math.max(
              atual,
              Math.min(populacao, registro[serie.campo] + desvio),
            )
          }, maior),
        0,
      ),
    [series, desvios, populacao],
  )
  const eixo = escalaContagem(maiorValor, populacao, escala === 'ajustada')
  const y = (valor: number) =>
    margem.superior +
    (1 - valor / eixo.maximo) * (altura - margem.superior - margem.inferior)
  const passos = [
    ...new Set(
      [0, 1, 2, 3, 4, 5, 6].map((i) => Math.round((horizonte * i) / 6)),
    ),
  ]
  const valores = eixo.valores
  const ultimoPasso = series.reduce(
    (maior, serie) => Math.max(maior, serie.registros.at(-1)?.passo ?? 0),
    0,
  )
  const passoAtual = Math.min(passoConsultado, ultimoPasso)
  const quantidadeLinhas = series.reduce(
    (total, s) => total + s.registros.length,
    0,
  )
  const ultimaPagina = Math.max(0, Math.ceil(quantidadeLinhas / 25) - 1)
  const paginaAtual = Math.min(pagina, ultimaPagina)
  let inicioSerie = 0
  const linhasTabela = tabelaAberta
    ? series.flatMap((s) => {
        const inicio = Math.max(0, paginaAtual * 25 - inicioSerie)
        const fim = Math.max(0, (paginaAtual + 1) * 25 - inicioSerie)
        inicioSerie += s.registros.length
        return s.registros
          .slice(inicio, fim)
          .map((r) => ({ serie: s, registro: r }))
      })
    : []

  function faixa(serie: Serie) {
    if (!serie.media || serie.registros.length === 0) return ''
    const pontos = serie.registros.map((r) => {
      const desvio = 'desvios' in r ? r.desvios[serie.campo] : null
      return desvio === null
        ? null
        : {
            passo: r.passo,
            superior: Math.min(populacao, r[serie.campo] + desvio),
            inferior: Math.max(0, r[serie.campo] - desvio),
          }
    })
    if (pontos.some((p) => p === null)) return ''
    const validos = pontos.filter((p) => p !== null)
    const superior = validos.flatMap((p, i) =>
      i
        ? [
            [x(p.passo), y(validos[i - 1].superior)],
            [x(p.passo), y(p.superior)],
          ]
        : [[x(p.passo), y(p.superior)]],
    )
    const inferior = validos
      .flatMap((p, i) =>
        i
          ? [
              [x(p.passo), y(validos[i - 1].inferior)],
              [x(p.passo), y(p.inferior)],
            ]
          : [[x(p.passo), y(p.inferior)]],
      )
      .reverse()
    return (
      [...superior, ...inferior]
        .map(([px, py], i) => `${i ? 'L' : 'M'} ${px} ${py}`)
        .join(' ') + ' Z'
    )
  }

  return (
    <section className="trajectory-panel" aria-labelledby="trajectory-title">
      <div className="results-section-heading">
        <div>
          <h2 id="trajectory-title">Trajetórias da epidemia</h2>
          <p>
            {comparacao
              ? 'Compare as estratégias sob a mesma configuração'
              : 'Contagens observadas ao longo dos passos'}
          </p>
        </div>
      </div>
      <div className="chart-controls">
        <label>
          Indicador
          <select
            aria-label="Indicador"
            value={campo}
            onChange={(e) => {
              setCampo(e.target.value as CampoCurva | 'todos')
              setPagina(0)
            }}
          >
            <option value="todos">Todos os estados</option>
            {CAMPOS_CURVA.map((c) => (
              <option key={c} value={c}>
                {CAMPOS[c].nome}
              </option>
            ))}
          </select>
        </label>
        {comparacao && (
          <>
            <label>
              Visualização
              <select
                aria-label="Visualização"
                value={modo}
                onChange={(e) => {
                  setModo(e.target.value)
                  setPagina(0)
                }}
              >
                <option value="medias">Médias por estratégia</option>
                <option value="repeticao">Trajetórias de uma repetição</option>
              </select>
            </label>
            {modo === 'repeticao' && (
              <label>
                Repetição
                <select
                  aria-label="Repetição"
                  value={repeticao}
                  onChange={(e) => {
                    setRepeticao(Number(e.target.value))
                    setPagina(0)
                  }}
                >
                  {repeticoes.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </label>
            )}
            {modo === 'medias' && (
              <label className="chart-check">
                <input
                  type="checkbox"
                  checked={desvios}
                  onChange={(e) => setDesvios(e.target.checked)}
                />
                Mostrar ± desvio-padrão
              </label>
            )}
          </>
        )}
        <label>
          Escala vertical
          <select
            aria-label="Escala vertical"
            value={escala}
            onChange={(e) => setEscala(e.target.value)}
          >
            <option value="ajustada">Ajustar às curvas</option>
            <option value="populacao">População total</option>
          </select>
        </label>
      </div>
      {comparacao && (
        <fieldset className="chart-scenarios">
          <legend>Estratégias exibidas</legend>
          {(Object.keys(NOMES_CENARIOS) as Cenario[]).map((c) => (
            <label key={c}>
              <input
                type="checkbox"
                checked={cenarios.includes(c)}
                onChange={(e) => {
                  setCenarios((atual) =>
                    e.target.checked
                      ? [...atual, c]
                      : atual.filter((item) => item !== c),
                  )
                  setPagina(0)
                }}
              />
              {NOMES_CENARIOS[c]}
            </label>
          ))}
        </fieldset>
      )}
      <div className="chart-context">
        <span>
          {populacao.toLocaleString('pt-BR')} pessoas ·{' '}
          {comparacao
            ? `${repeticoes.length} repetição(ões) por estratégia`
            : 'execução individual'}
        </span>
        <span>
          Eixo vertical: 0–{eixo.maximo.toLocaleString('pt-BR')} pessoas ·{' '}
          {escala === 'ajustada' ? 'escala ajustada' : 'população total'}
        </span>
      </div>
      <div
        className="trajectory-chart"
        tabIndex={0}
        role="region"
        aria-label="Gráfico; use a rolagem horizontal em telas estreitas"
      >
        {historico.length > 0 && series.length > 0 ? (
          <svg
            ref={grafico}
            viewBox={`0 0 ${largura} ${altura}`}
            role="img"
            aria-labelledby="titulo-svg descricao-svg"
            data-escala={escala}
            data-limite-vertical={eixo.maximo}
            data-indicador={campo}
            data-modo={comparacao ? modo : 'individual'}
            data-repeticao={comparacao && modo === 'repeticao' ? repeticao : ''}
            data-cenarios={cenarios.join(',')}
            onClick={(e) => {
              const area = e.currentTarget.getBoundingClientRect()
              const posicao = ((e.clientX - area.left) / area.width) * largura
              const posicaoVertical =
                ((e.clientY - area.top) / area.height) * altura
              if (
                posicaoVertical >= margem.superior &&
                posicaoVertical <= altura - margem.inferior &&
                posicao >= margem.esquerda &&
                posicao <= largura - margem.direita
              ) {
                const passo = Math.round(
                  ((posicao - margem.esquerda) /
                    (largura - margem.esquerda - margem.direita)) *
                    horizonte,
                )
                setPassoConsultado(Math.min(ultimoPasso, Math.max(0, passo)))
              }
            }}
          >
            <title id="titulo-svg">
              {campo === 'todos'
                ? 'Contagens SIR e isolamento'
                : CAMPOS[campo].nome}{' '}
              ·{' '}
              {comparacao
                ? modo === 'medias'
                  ? 'médias por estratégia'
                  : `repetição ${repeticao}`
                : 'execução individual'}
            </title>
            <desc id="descricao-svg">
              Contagem de pessoas por passo. Consulte os dados das curvas na
              tabela abaixo. Traçados distinguem estratégias; não há suavização
              entre passos. Eixo vertical de zero a {eixo.maximo} pessoas;{' '}
              {escala === 'ajustada'
                ? 'ajustado às curvas exibidas'
                : 'população total'}
              .
            </desc>
            {series.map((s, i) => (
              <g
                key={`legenda-${s.id}`}
                transform={`translate(${64 + (i % 3) * 304},${24 + Math.floor(i / 3) * 22})`}
              >
                <line
                  x1="0"
                  x2="28"
                  y1="0"
                  y2="0"
                  stroke={s.cor}
                  strokeWidth="3"
                  strokeDasharray={s.traco}
                />
                <text x="36" y="4" className="chart-label chart-legend-label">
                  {s.nome}
                </text>
              </g>
            ))}
            {valores.map((v) => (
              <g key={v}>
                <line
                  x1={margem.esquerda}
                  x2={largura - margem.direita}
                  y1={y(v)}
                  y2={y(v)}
                  className="chart-grid"
                />
                <text
                  x={margem.esquerda - 12}
                  y={y(v) + 4}
                  textAnchor="end"
                  className="chart-label"
                >
                  {v}
                </text>
              </g>
            ))}
            {passos.map((p) => (
              <text
                key={p}
                x={x(p)}
                y={altura - 42}
                textAnchor="middle"
                className="chart-label"
              >
                {p}
              </text>
            ))}
            <text
              x={largura / 2}
              y={altura - 15}
              textAnchor="middle"
              className="chart-axis-title"
            >
              Passos (dias do modelo)
            </text>
            <text
              x="17"
              y={(margem.superior + altura - margem.inferior) / 2}
              textAnchor="middle"
              transform={`rotate(-90 17 ${(margem.superior + altura - margem.inferior) / 2})`}
              className="chart-axis-title"
            >
              Pessoas
            </text>
            <line
              data-consulta="true"
              x1={x(passoAtual)}
              x2={x(passoAtual)}
              y1={margem.superior}
              y2={altura - margem.inferior}
              className="chart-cursor"
            />
            {series.map((s) => (
              <g key={s.id} data-serie={s.id}>
                <title>
                  {s.nome} ·{' '}
                  {s.media
                    ? `n = ${'n' in (s.registros[0] ?? {}) ? (s.registros[0] as RegistroAgregado).n : 0}`
                    : 'trajetória individual'}{' '}
                  · {s.censuradas} censurada(s)
                </title>
                {desvios && faixa(s) && (
                  <path
                    d={faixa(s)}
                    fill={s.cor}
                    fillOpacity="0.12"
                    stroke="none"
                  />
                )}
                <path
                  data-curva={s.id}
                  d={caminhoEscalonado(
                    s.registros.map((r) => [x(r.passo), y(r[s.campo])]),
                  )}
                  fill="none"
                  stroke={s.cor}
                  strokeWidth="2.5"
                  strokeDasharray={s.traco}
                />
                {s.registros.length === 1 && (
                  <circle
                    cx={x(s.registros[0].passo)}
                    cy={y(s.registros[0][s.campo])}
                    r="4"
                    fill={s.cor}
                  />
                )}
              </g>
            ))}
          </svg>
        ) : (
          <p className="chart-empty" role="status">
            {historico.length
              ? 'Selecione pelo menos uma estratégia para exibir o gráfico.'
              : 'Nenhum registro disponível.'}
          </p>
        )}
      </div>
      {series.length > 0 && historico.length > 0 && (
        <div className="chart-inspector">
          <div className="chart-inspector-heading">
            <label htmlFor="consulta-passo">
              Consultar passo <b>{passoAtual}</b>
            </label>
            <span>Clique no gráfico ou use as setas no controle</span>
          </div>
          <input
            id="consulta-passo"
            type="range"
            min="0"
            max={ultimoPasso}
            step="1"
            value={passoAtual}
            disabled={ultimoPasso === 0}
            onChange={(e) => setPassoConsultado(Number(e.target.value))}
          />
          <ul className="chart-values" aria-live="polite" aria-atomic="true">
            {series.map((serie) => {
              const registro = registroNoPasso(serie.registros, passoAtual)
              return (
                <li key={serie.id}>
                  <span className="chart-value-name">
                    <svg width="26" height="8" aria-hidden="true">
                      <line
                        x1="0"
                        x2="26"
                        y1="4"
                        y2="4"
                        stroke={serie.cor}
                        strokeWidth="3"
                        strokeDasharray={serie.traco}
                      />
                    </svg>
                    {serie.nome}
                  </span>
                  <strong>
                    {registro
                      ? registro[serie.campo].toLocaleString('pt-BR', {
                          maximumFractionDigits: 2,
                        })
                      : 'Sem registro'}
                  </strong>
                  <span>
                    {registro
                      ? `${serie.media ? 'Média · ' : ''}pessoas${'n' in registro ? ` · n = ${registro.n}` : ''}`
                      : 'Fora dos dados disponíveis'}
                  </span>
                </li>
              )
            })}
          </ul>
        </div>
      )}
      <details className="chart-reading">
        <summary>Como ler este gráfico</summary>
        <p id="descricao-curvas" className="chart-description">
          {comparacao
            ? modo === 'medias'
              ? 'Médias com n constante por estratégia, limitadas ao horizonte comum disponível. Apenas extinções preservam o estado final; não há prolongamento após censura. Desvio amostral indisponível para n = 1.'
              : `Trajetórias observadas da repetição ${repeticao}; cada linha termina no seu último registro.`
            : 'Estados atualizados em passos discretos. Isolados também pertencem a S, I ou R.'}
        </p>
        {comparacao && (
          <ul className="chart-sample-info">
            {agregadas
              .filter((g) => cenarios.includes(g.cenario))
              .map((g) => (
                <li key={g.cenario}>
                  <b>{NOMES_CENARIOS[g.cenario]}</b>: n ={' '}
                  {g.registros[0]?.n ?? 0}; horizonte da média{' '}
                  {g.registros.at(-1)?.passo ?? '—'};{' '}
                  {
                    comparacao.execucoes.filter(
                      (e) =>
                        e.cenario === g.cenario &&
                        e.motivo_termino === 'limite_passos',
                    ).length
                  }{' '}
                  censurada(s).
                </li>
              ))}
          </ul>
        )}
      </details>
      <details
        className="chart-data"
        onToggle={(e) => setTabelaAberta(e.currentTarget.open)}
      >
        <summary>
          Dados das curvas exibidas ({quantidadeLinhas} valores)
        </summary>
        {tabelaAberta && (
          <>
            <div className="history-table-wrap">
              <table className="history-table">
                <caption>
                  Mesmos valores do gráfico; traço significa dado não aplicável.
                </caption>
                <thead>
                  <tr>
                    <th scope="col">Série</th>
                    <th scope="col">Passo</th>
                    <th scope="col">Pessoas</th>
                    <th scope="col">n</th>
                    <th scope="col">Desvio amostral</th>
                    <th scope="col">Extinções prolongadas</th>
                  </tr>
                </thead>
                <tbody>
                  {linhasTabela.map(({ serie: s, registro: r }) => (
                    <tr key={`${s.id}-${r.passo}`}>
                      <th scope="row">{s.nome}</th>
                      <td>{r.passo}</td>
                      <td>
                        {r[s.campo].toLocaleString('pt-BR', {
                          maximumFractionDigits: 2,
                        })}
                      </td>
                      <td>{'n' in r ? r.n : 1}</td>
                      <td>
                        {'desvios' in r
                          ? (r.desvios[s.campo]?.toLocaleString('pt-BR', {
                              maximumFractionDigits: 3,
                            }) ?? '—')
                          : '—'}
                      </td>
                      <td>{'prolongadas' in r ? r.prolongadas : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="chart-pagination">
              <button
                type="button"
                disabled={paginaAtual === 0}
                onClick={() => setPagina(paginaAtual - 1)}
              >
                Anterior
              </button>
              <span role="status">
                Página {paginaAtual + 1} de {ultimaPagina + 1}
              </span>
              <button
                type="button"
                disabled={paginaAtual === ultimaPagina}
                onClick={() => setPagina(paginaAtual + 1)}
              >
                Próxima
              </button>
            </div>
          </>
        )}
      </details>
    </section>
  )
}
