import { useEffect, useRef, useState } from 'react'
import { AppShell } from '../components/AppShell'
import { Icon } from '../components/Icon'
import { useCargaRede } from '../hooks/useCargaRede'
import {
  NOMES_CENARIOS,
  csvMetricas,
  csvResultado,
  dimensoesPng,
  linhasHistorico,
  maximoHistorico,
  pacoteExportacao,
  serializarGrafico,
} from '../features/resultados/dadosResultados'
import { TabelaHistorico } from '../features/resultados/TabelaHistorico'
import { GraficoTrajetorias } from '../features/resultados/GraficoTrajetorias'
import { filtrosTrajetoriasPadrao } from '../features/resultados/filtrosTrajetorias'
import {
  executarComparacao,
  executarSimulacao,
  listarResultados,
  consultarResultado,
  type ResultadoResumo,
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

export function ResultsPage() {
  const carga = useCargaRede()
  const totalRede = carga.rede?.resumo?.numero_individuos ?? 100
  const [historicoBase, setHistorico] = useState<RegistroResultado[]>([])
  const [resultado, setResultado] = useState<ResultadoSimulacao | null>(null)
  const [comparacao, setComparacao] =
    useState<ResultadoComparacaoExecutada | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState('')
  const [filtrosGrafico, setFiltrosGrafico] = useState(filtrosTrajetoriasPadrao)
  const grafico = useRef<SVGSVGElement | null>(null)
  const consulta = useRef<AbortController | null>(null)
  const [anteriores, setAnteriores] = useState<ResultadoResumo[]>([])
  const [chaveExecucao, setChaveExecucao] = useState('')
  const execucaoSelecionada = comparacao
    ? (comparacao.execucoes.find(
        (execucao) =>
          `${execucao.cenario}-${execucao.repeticao}` === chaveExecucao,
      ) ?? execucaoPrincipal(comparacao))
    : undefined
  const historico = execucaoSelecionada?.historico ?? historicoBase
  const resultadoId = resultado?.resultado_id ?? comparacao?.resultado_id

  useEffect(() => {
    const controlador = new AbortController()
    if (carga.rede) {
      listarResultados(controlador.signal)
        .then((lista) => {
          if (!controlador.signal.aborted)
            setAnteriores(
              lista.resultados.filter(
                (item) =>
                  item.revisao_rede === carga.rede?.revisao &&
                  item.contexto_rede === carga.rede?.contexto_rede,
              ),
            )
        })
        .catch(() => undefined)
    }
    return () => controlador.abort()
  }, [carga.rede, resultadoId])

  useEffect(() => () => consulta.current?.abort(), [])

  async function recuperarResultado(identificador: string) {
    if (!identificador) return
    consulta.current?.abort()
    const controlador = new AbortController()
    consulta.current = controlador
    setCarregando(true)
    setErro('')
    setFiltrosGrafico(filtrosTrajetoriasPadrao())
    setChaveExecucao('')
    try {
      const salvo = await consultarResultado(identificador, controlador.signal)
      if (controlador.signal.aborted) return
      if (
        salvo.contexto_rede !== carga.rede?.contexto_rede ||
        salvo.revisao_rede !== carga.rede?.revisao
      )
        throw new Error('O resultado pertence a outra revisão da rede.')
      if ('execucoes' in salvo) {
        setComparacao(salvo)
        setResultado(null)
        setHistorico(execucaoPrincipal(salvo)?.historico ?? [])
        sessionStorage.setItem(
          CHAVE_RESULTADO,
          JSON.stringify({ tipo: 'comparacao', comparacao: salvo }),
        )
      } else {
        setResultado(salvo)
        setComparacao(null)
        setHistorico(salvo.historico)
        sessionStorage.setItem(
          CHAVE_RESULTADO,
          JSON.stringify({ tipo: 'individual', resultado: salvo }),
        )
      }
    } catch (falha) {
      if (!controlador.signal.aborted)
        setErro(
          falha instanceof Error
            ? falha.message
            : 'Não foi possível consultar o resultado.',
        )
    } finally {
      if (!controlador.signal.aborted) setCarregando(false)
    }
  }

  useEffect(() => {
    if (!carga.rede) return
    const controlador = new AbortController()
    async function carregar() {
      setCarregando(true)
      setErro('')
      try {
        setFiltrosGrafico(filtrosTrajetoriasPadrao())
        setChaveExecucao('')
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
              if (controlador.signal.aborted) return
              sessionStorage.setItem(
                CHAVE_RESULTADO,
                JSON.stringify({ tipo: 'comparacao', comparacao: lote }),
              )
              setComparacao(lote)
              const principal = execucaoPrincipal(lote)
              if (principal) setHistorico(principal.historico)
            } else {
              const ensaio = await executarSimulacao(
                salvo.formulario,
                controlador.signal,
              )
              if (controlador.signal.aborted) return
              sessionStorage.setItem(
                CHAVE_RESULTADO,
                JSON.stringify({ tipo: 'individual', resultado: ensaio }),
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
  const total = resultado?.populacao ?? comparacao?.populacao ?? totalRede
  const pico =
    resultado?.metrica.pico_infectados ??
    execucaoSelecionada?.metrica.pico_infectados ??
    maximoHistorico(historico, 'infectados')
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
    execucaoSelecionada?.metrica.horizonte_observado ??
    passoAtual
  const dadosAtuais = resultado ?? comparacao

  const descricaoCenario = execucaoSelecionada
    ? `${NOMES_CENARIOS[execucaoSelecionada.cenario]} · repetição ${execucaoSelecionada.repeticao}`
    : resultado
      ? 'Execução única'
      : null
  const motivoTermino =
    resultado?.motivo_termino ?? execucaoSelecionada?.motivo_termino ?? null

  function exportarCsv() {
    if (!dadosAtuais) return
    baixar(
      csvResultado(
        dadosAtuais,
        ['cenario', 'repeticao', 'passo', 'S', 'I', 'R', 'Isolados'],
        linhasHistorico(historico).map((linha) => [
          execucaoSelecionada?.cenario ?? 'individual',
          execucaoSelecionada?.repeticao ?? 1,
          ...linha,
        ]),
      ),
      'historico-ensaio.csv',
      'text/csv;charset=utf-8',
    )
  }

  function baixar(conteudo: BlobPart, nome: string, tipo: string) {
    const url = URL.createObjectURL(new Blob([conteudo], { type: tipo }))
    const link = document.createElement('a')
    link.href = url
    link.download = `observatorio-rev${dadosAtuais?.revisao_rede ?? 0}-${new Date().toLocaleDateString('sv-SE')}-${nome}`
    link.click()
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  }

  function exportarCsvAgregado() {
    if (comparacao)
      baixar(
        csvMetricas(comparacao),
        'metricas-agregadas.csv',
        'text/csv;charset=utf-8',
      )
  }

  function exportarTrajetorias() {
    if (!comparacao) return
    const linhas: unknown[][] = []
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
        ])
      }
    }
    baixar(
      csvResultado(
        comparacao,
        ['repeticao', 'cenario', 'passo', 'S', 'I', 'R', 'Isolados'],
        linhas,
      ),
      'trajetorias-comparacao.csv',
      'text/csv;charset=utf-8',
    )
  }

  function exportarJson() {
    if (dadosAtuais)
      baixar(
        JSON.stringify(
          {
            ...pacoteExportacao(dadosAtuais),
            visualizacao: {
              series_visiveis: filtrosGrafico.series,
              filtros_grafico: filtrosGrafico,
              cenario: execucaoSelecionada?.cenario,
              repeticao: execucaoSelecionada?.repeticao,
            },
          },
          null,
          2,
        ),
        'metadados-ensaio.json',
        'application/json',
      )
  }

  function exportarSvg() {
    if (!grafico.current || !dadosAtuais) return
    baixar(
      serializarGrafico(grafico.current, dadosAtuais, opcoesExportacao()).svg,
      'trajetorias-epidemia.svg',
      'image/svg+xml;charset=utf-8',
    )
  }

  function exportarPng() {
    if (!grafico.current || !dadosAtuais) return
    const {
      svg,
      largura: larguraExportada,
      altura: alturaExportada,
    } = serializarGrafico(grafico.current, dadosAtuais, opcoesExportacao())
    const imagem = new Image()
    imagem.onload = () => {
      const canvas = document.createElement('canvas')
      const dimensoes = dimensoesPng(larguraExportada, alturaExportada)
      canvas.width = dimensoes.largura
      canvas.height = dimensoes.altura
      const contexto = canvas.getContext('2d')
      if (!contexto) {
        setErro('Não foi possível preparar a exportação PNG.')
        return
      }
      contexto.scale(
        dimensoes.largura / larguraExportada,
        dimensoes.altura / alturaExportada,
      )
      contexto.drawImage(imagem, 0, 0, larguraExportada, alturaExportada)
      canvas.toBlob((blob) => {
        if (blob) baixar(blob, 'trajetorias-epidemia.png', 'image/png')
        else setErro('Não foi possível gerar o arquivo PNG.')
      }, 'image/png')
    }
    imagem.onerror = () => setErro('Não foi possível gerar o arquivo PNG.')
    imagem.src = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`
  }

  function opcoesExportacao() {
    return {
      filtros: filtrosGrafico,
      descricao: grafico.current
        ?.getAttribute('aria-label')
        ?.replace('Curvas SIR ao longo do tempo. ', ''),
      cenarios: comparacao
        ? (
            Object.keys(
              filtrosGrafico.cenarios,
            ) as (keyof typeof NOMES_CENARIOS)[]
          ).filter((cenario) => filtrosGrafico.cenarios[cenario])
        : [],
      legenda: comparacao
        ? `S: contínua · I: tracejada · R: pontilhada · Q: mista${filtrosGrafico.modo === 'medias' && filtrosGrafico.mostrarDesvio ? ' · faixas: desvio amostral' : ''}`
        : 'S: suscetíveis · I: infectados · R: recuperados · Q: isolados',
    }
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

        <section
          className="results-section-heading"
          aria-label="Consulta de resultados"
        >
          <label htmlFor="resultado-anterior">
            Execuções anteriores desta rede
          </label>
          <select
            id="resultado-anterior"
            value={resultadoId ?? ''}
            disabled={carregando || !anteriores.length}
            onChange={(evento) => void recuperarResultado(evento.target.value)}
          >
            <option value="">Selecione uma execução</option>
            {anteriores.map((item, indice) => (
              <option key={item.id} value={item.id}>
                Execução {indice + 1} · revisão {item.revisao_rede} ·{' '}
                {item.populacao} pessoas
              </option>
            ))}
          </select>
        </section>
        {comparacao && (
          <div className="results-section-heading">
            <label htmlFor="execucao-principal">
              Cenário e repetição do painel e da tabela
            </label>
            <select
              id="execucao-principal"
              value={
                execucaoSelecionada
                  ? `${execucaoSelecionada.cenario}-${execucaoSelecionada.repeticao}`
                  : ''
              }
              onChange={(evento) => setChaveExecucao(evento.target.value)}
            >
              {comparacao.execucoes.map((execucao) => (
                <option
                  key={`${execucao.cenario}-${execucao.repeticao}`}
                  value={`${execucao.cenario}-${execucao.repeticao}`}
                >
                  {NOMES_CENARIOS[execucao.cenario]} · repetição{' '}
                  {execucao.repeticao}
                </option>
              ))}
            </select>
          </div>
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

        <GraficoTrajetorias
          key={resultadoId ?? 'atual'}
          historico={historico}
          comparacao={comparacao}
          populacao={total}
          carregando={carregando}
          filtros={filtrosGrafico}
          onAlterar={setFiltrosGrafico}
          grafico={grafico}
          onExportarSvg={exportarSvg}
          onExportarPng={exportarPng}
        />

        {comparacao && (
          <section className="history-panel" aria-labelledby="statistics-title">
            <div className="results-section-heading">
              <h2 id="statistics-title">Métricas agregadas por estratégia</h2>
            </div>
            <div className="history-table-wrap">
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Cenário</th>
                    <th>Métrica</th>
                    <th>n</th>
                    <th>Ausentes</th>
                    <th>Média</th>
                    <th>Desvio-padrão</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(comparacao.resumo).flatMap(
                    ([cenario, resumo]) =>
                      Object.entries(resumo.metricas).map(
                        ([metrica, estatistica]) => (
                          <tr key={`${cenario}-${metrica}`}>
                            <th scope="row">{cenario}</th>
                            <td>{metrica}</td>
                            <td>{estatistica.n}</td>
                            <td>{estatistica.ausentes}</td>
                            <td>
                              {estatistica.media?.toLocaleString('pt-BR') ??
                                '—'}
                            </td>
                            <td>
                              {estatistica.desvio_padrao?.toLocaleString(
                                'pt-BR',
                              ) ?? '—'}
                            </td>
                          </tr>
                        ),
                      ),
                  )}
                </tbody>
              </table>
            </div>
          </section>
        )}

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
              {comparacao && (
                <button type="button" onClick={exportarCsvAgregado}>
                  CSV agregado
                </button>
              )}
              {comparacao && (
                <button type="button" onClick={exportarTrajetorias}>
                  CSV trajetórias
                </button>
              )}
              <button
                type="button"
                onClick={exportarJson}
                disabled={!dadosAtuais}
              >
                JSON
              </button>
            </div>
          </div>
          <TabelaHistorico
            key={`${resultadoId ?? 'atual'}-${chaveExecucao}`}
            historico={historico}
          />
        </section>
      </main>
    </AppShell>
  )
}
