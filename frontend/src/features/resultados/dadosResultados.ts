import type {
  RegistroResultado,
  ResultadoComparacaoExecutada,
  ResultadoSimulacao,
} from '../../services/configuracaoApi'

export const CAMPOS_CURVA = [
  'suscetiveis',
  'infectados',
  'recuperados',
  'isolados',
] as const
export type CampoCurva = (typeof CAMPOS_CURVA)[number]
export type RegistroAgregado = Record<CampoCurva, number> & {
  passo: number
  n: number
  prolongadas: number
  desvios: Record<CampoCurva, number | null>
}
export type DadosResultado = ResultadoSimulacao | ResultadoComparacaoExecutada
export const CORES_CENARIOS = {
  sem_intervencao: '#4c78a8',
  aleatoria: '#c94d4d',
  grau: '#4c9a72',
}
export const NOMES_CENARIOS = {
  sem_intervencao: 'Sem intervenção',
  aleatoria: 'Aleatório',
  grau: 'Por grau',
}

export function maximoHistorico(
  historico: readonly RegistroResultado[],
  campo: CampoCurva | 'passo',
) {
  let maior = 0
  for (const registro of historico) {
    if (registro[campo] > maior) maior = registro[campo]
  }
  return maior
}

export function agregarCurvas(comparacao: ResultadoComparacaoExecutada) {
  const horizonte = comparacao.execucoes.reduce(
    (maior, execucao) => Math.max(maior, execucao.historico.at(-1)?.passo ?? 0),
    0,
  )
  return (['sem_intervencao', 'aleatoria', 'grau'] as const).flatMap(
    (cenario) => {
      const execucoes = comparacao.execucoes.filter(
        (execucao) => execucao.cenario === cenario,
      )
      if (!execucoes.length) return []
      const indices = execucoes.map(() => 0)
      const registros: RegistroAgregado[] = []
      for (let passo = 0; passo <= horizonte; passo += 1) {
        const observacoes = execucoes.flatMap((execucao, indice) => {
          while (
            (execucao.historico[indices[indice] + 1]?.passo ?? Infinity) <=
            passo
          )
            indices[indice]++
          const registro = execucao.historico[indices[indice]]
          if (!registro) return []
          if (registro.passo === passo) return [registro]
          return execucao.motivo_termino === 'extincao' &&
            registro.infectados === 0 &&
            indices[indice] === execucao.historico.length - 1 &&
            registro.passo < passo
            ? [registro]
            : []
        })
        if (observacoes.length !== execucoes.length) break
        const valores = {} as Record<CampoCurva, number>
        const desvios = {} as Record<CampoCurva, number | null>
        for (const campo of CAMPOS_CURVA) {
          valores[campo] =
            observacoes.reduce((soma, registro) => soma + registro[campo], 0) /
            observacoes.length
          desvios[campo] =
            observacoes.length > 1
              ? Math.sqrt(
                  observacoes.reduce(
                    (soma, registro) =>
                      soma + (registro[campo] - valores[campo]) ** 2,
                    0,
                  ) /
                    (observacoes.length - 1),
                )
              : null
        }
        registros.push({
          passo,
          ...valores,
          n: observacoes.length,
          prolongadas: observacoes.filter((registro) => registro.passo < passo)
            .length,
          desvios,
        })
      }
      return [{ cenario, registros }]
    },
  )
}

export function escalaContagem(
  maximo: number,
  populacao: number,
  ajustar: boolean,
) {
  const limite = Math.max(1, populacao)
  const alvo = ajustar ? Math.min(limite, Math.max(1, maximo * 1.05)) : limite
  const ordem = 10 ** Math.floor(Math.log10(alvo / 5))
  const intervalo = Math.max(
    1,
    ([1, 2, 5, 10].find((fator) => fator * ordem >= alvo / 5) ?? 10) * ordem,
  )
  const teto = Math.min(limite, Math.ceil(alvo / intervalo) * intervalo)
  const valores = [0]
  for (let valor = intervalo; valor < teto; valor += intervalo)
    valores.push(valor)
  valores.push(teto)
  return { maximo: teto, valores }
}

export function registroNoPasso<T extends { passo: number }>(
  registros: readonly T[],
  passo: number,
): T | null {
  let inicio = 0
  let fim = registros.length - 1
  while (inicio <= fim) {
    const meio = Math.floor((inicio + fim) / 2)
    const registro = registros[meio]
    if (registro.passo === passo) return registro
    if (registro.passo < passo) inicio = meio + 1
    else fim = meio - 1
  }
  return null
}

export function caminhoEscalonado(
  pontos: readonly (readonly [number, number])[],
) {
  return pontos
    .map(([x, y], indice) => (indice ? `H ${x} V ${y}` : `M ${x} ${y}`))
    .join(' ')
}

export function dimensoesPng(largura: number, altura: number) {
  if (
    !Number.isFinite(largura) ||
    !Number.isFinite(altura) ||
    largura <= 0 ||
    altura <= 0
  )
    throw new Error('As dimensões do gráfico devem ser positivas e finitas.')
  const escala = Math.max(1, 2400 / largura)
  return {
    largura: Math.ceil(largura * escala),
    altura: Math.ceil(altura * escala),
  }
}

export function pacoteExportacao(resultado: DadosResultado) {
  return {
    projeto: 'Observatório — Simulador de Epidemias em Redes',
    data_local: new Date().toLocaleString('sv-SE'),
    fuso_horario: Intl.DateTimeFormat().resolvedOptions().timeZone,
    revisao_rede: resultado.revisao_rede,
    resultado,
  }
}

export function csvResultado(
  dados: DadosResultado,
  cabecalho: string[],
  linhas: unknown[][],
) {
  const pacote = pacoteExportacao(dados)
  const metadados = [
    pacote.projeto,
    pacote.data_local,
    pacote.fuso_horario,
    dados.revisao_rede,
    JSON.stringify(dados.manifesto ?? {}),
  ]
  const celula = (valor: unknown) =>
    `"${String(valor ?? '').replaceAll('"', '""')}"`
  return (
    '\ufeff' +
    [
      [
        'projeto',
        'data_local',
        'fuso_horario',
        'revisao_rede',
        'manifesto',
        ...cabecalho,
      ],
      ...linhas.map((linha) => [...metadados, ...linha]),
    ]
      .map((linha) => linha.map(celula).join(';'))
      .join('\n')
  )
}

export function csvMetricas(comparacao: ResultadoComparacaoExecutada) {
  return csvResultado(
    comparacao,
    ['cenario', 'metrica', 'n', 'ausentes', 'media', 'desvio_padrao'],
    Object.entries(comparacao.resumo).flatMap(([cenario, resumo]) =>
      Object.entries(resumo.metricas).map(([metrica, estatistica]) => [
        cenario,
        metrica,
        estatistica.n,
        estatistica.ausentes,
        estatistica.media,
        estatistica.desvio_padrao,
      ]),
    ),
  )
}

export function serializarGrafico(
  elemento: SVGSVGElement,
  dados: DadosResultado,
  visualizacao?: {
    filtros: unknown
    descricao?: string
    cenarios: (keyof typeof NOMES_CENARIOS)[]
    legenda: string
  },
) {
  const clone = elemento.cloneNode(true) as SVGSVGElement
  const originais = [elemento, ...elemento.querySelectorAll('*')]
  const copias = [clone, ...clone.querySelectorAll('*')]
  const propriedades = [
    'fill',
    'fill-opacity',
    'stroke',
    'stroke-width',
    'stroke-dasharray',
    'stroke-opacity',
    'opacity',
    'font-family',
    'font-size',
    'font-weight',
    'text-anchor',
    'visibility',
    'display',
  ]
  originais.forEach((original, indice) => {
    const estilo = getComputedStyle(original)
    for (const propriedade of propriedades) {
      copias[indice].setAttribute(
        propriedade,
        estilo.getPropertyValue(propriedade),
      )
    }
  })
  clone
    .querySelectorAll('[data-consulta]')
    .forEach((elemento) => elemento.remove())
  clone
    .querySelectorAll('.chart-label')
    .forEach((elemento) => elemento.setAttribute('fill', '#374151'))
  const { width: largura, height: altura } = elemento.viewBox.baseVal
  const namespace = 'http://www.w3.org/2000/svg'
  clone.setAttribute('xmlns', namespace)
  const cabecalho = visualizacao ? 152 : 128
  const deslocamento = cabecalho - 128
  clone.setAttribute(
    'viewBox',
    `0 -${cabecalho} ${largura} ${altura + cabecalho}`,
  )
  clone.setAttribute('width', String(largura))
  clone.setAttribute('height', String(altura + cabecalho))
  const metadados = document.createElementNS(namespace, 'metadata')
  metadados.textContent = JSON.stringify({
    ...pacoteExportacao(dados),
    ...(visualizacao ? { visualizacao } : {}),
  })
  clone.prepend(metadados)
  const fundo = document.createElementNS(namespace, 'rect')
  fundo.setAttribute('x', '0')
  fundo.setAttribute('y', String(-cabecalho))
  fundo.setAttribute('width', String(largura))
  fundo.setAttribute('height', String(altura + cabecalho))
  fundo.setAttribute('fill', '#ffffff')
  clone.prepend(fundo)
  const titulo = document.createElementNS(namespace, 'text')
  titulo.setAttribute('x', '16')
  titulo.setAttribute('y', String(-104 - deslocamento))
  titulo.setAttribute('fill', '#161616')
  titulo.setAttribute('font-size', '14')
  titulo.textContent = `Observatório · revisão ${dados.revisao_rede} · ${new Date().toLocaleString()}`
  clone.append(titulo)
  const configuracao = dados.manifesto?.configuracao ?? {}
  const sementes = (configuracao.sementes ?? {}) as Record<string, string>
  const intervencao = configuracao.intervencao as Record<string, unknown> | null
  for (const [indice, texto] of [
    `β: ${configuracao.beta ?? 'direto'} · γ: ${configuracao.gamma} · pessoas: ${dados.populacao} · repetições: ${'execucoes' in dados ? dados.manifesto?.repeticoes : 1}`,
    `Sementes ${'execucoes' in dados ? 'base' : ''}: epidemia ${sementes.epidemia} · iniciais ${sementes.iniciais} · isolamento ${sementes.isolamento}`,
    intervencao
      ? `Isolamento: ${intervencao.mecanismo} · fração ${intervencao.fracao} · início ${intervencao.inicio}`
      : 'Sem intervenção',
  ].entries()) {
    const linha = document.createElementNS(namespace, 'text')
    linha.setAttribute('x', '16')
    linha.setAttribute('y', String(-84 - deslocamento + indice * 16))
    linha.setAttribute('fill', '#161616')
    linha.setAttribute('font-size', '11')
    linha.textContent = texto
    clone.append(linha)
  }
  if (visualizacao?.descricao) {
    const escopo = document.createElementNS(namespace, 'text')
    escopo.setAttribute('x', '16')
    escopo.setAttribute('y', '-56')
    escopo.setAttribute('fill', '#161616')
    escopo.setAttribute('font-size', '11')
    escopo.textContent = visualizacao.descricao
    clone.append(escopo)
  }
  const legenda = document.createElementNS(namespace, 'text')
  legenda.setAttribute('x', '16')
  legenda.setAttribute('y', '-32')
  legenda.setAttribute('fill', '#161616')
  legenda.setAttribute('font-size', '11')
  legenda.textContent =
    visualizacao?.legenda ??
    ('execucoes' in dados
      ? 'S: contínua · I: tracejada · R: pontilhada · Q: mista · médias ± desvio amostral'
      : 'S: suscetíveis · I: infectados · R: recuperados · Q: isolados')
  clone.append(legenda)
  if ('execucoes' in dados) {
    Object.entries(CORES_CENARIOS)
      .filter(
        ([cenario]) =>
          !visualizacao ||
          visualizacao.cenarios.includes(
            cenario as keyof typeof NOMES_CENARIOS,
          ),
      )
      .forEach(([cenario, cor], indice) => {
        const rotulo = document.createElementNS(namespace, 'text')
        rotulo.setAttribute('x', String(16 + indice * 240))
        rotulo.setAttribute('y', '-14')
        rotulo.setAttribute('fill', cor)
        rotulo.setAttribute('font-size', '12')
        rotulo.textContent =
          NOMES_CENARIOS[cenario as keyof typeof NOMES_CENARIOS]
        clone.append(rotulo)
      })
  }
  return {
    svg: new XMLSerializer().serializeToString(clone),
    largura,
    altura: altura + cabecalho,
  }
}

export function linhasHistorico(historico: RegistroResultado[]) {
  return historico.map((registro) => [
    registro.passo,
    ...CAMPOS_CURVA.map((campo) => registro[campo]),
  ])
}
