import { solicitar } from './redeApi'

export interface EntradaIntervencao {
  ativa: boolean
  estrategia: 'aleatoria' | 'grau'
  fracao: string
  inicio: string
  mecanismo: 'desativacao' | 'reducao' | 'exclusao'
  reducao: string
}

export interface FormularioIntervencao {
  estrategia: EntradaIntervencao['estrategia']
  fracao: string
  inicio: string
  mecanismo: EntradaIntervencao['mecanismo']
  reducao?: string
}

export function prepararFormularioIntervencao(
  campos: EntradaIntervencao,
): FormularioIntervencao | null {
  if (!campos.ativa) return null
  return {
    estrategia: campos.estrategia,
    fracao: campos.fracao,
    inicio: campos.inicio,
    mecanismo: campos.mecanismo,
    ...(campos.mecanismo === 'reducao' ? { reducao: campos.reducao } : {}),
  }
}

export type ModoPeso = 'intensidade' | 'probabilidade'

export type FormularioConfiguracao = {
  beta: string | null
  gamma: string
  modo_peso: ModoPeso
  semente_epidemia: string
  semente_iniciais: string
  semente_isolamento: string
  limite_passos: string
  revisao_rede: string
  contexto_rede?: string
  intervencao?: FormularioIntervencao | null
} & (
  | {
      modo_iniciais: 'ids'
      ids_infectados_iniciais: string[]
      quantidade_infectados?: never
    }
  | {
      modo_iniciais: 'sorteio'
      quantidade_infectados: string
      ids_infectados_iniciais?: never
    }
)

export interface ConfiguracaoValidada {
  contexto_rede: string
  populacao: number
  modo_iniciais: 'ids' | 'sorteio'
  configuracao: {
    beta: number | null
    gamma: number
    modo_peso: ModoPeso
    ids_infectados_iniciais: string[]
    semente_epidemia: string
    semente_iniciais: string
    semente_isolamento: string
    limite_passos: number
    revisao_rede: number
    intervencao: {
      estrategia: EntradaIntervencao['estrategia']
      fracao: number
      quantidade_isolados: number
      inicio: number
      mecanismo: EntradaIntervencao['mecanismo']
      reducao: number | null
    } | null
  }
}

export function validarConfiguracao(
  campos: FormularioConfiguracao,
  signal?: AbortSignal,
): Promise<ConfiguracaoValidada> {
  return solicitar<ConfiguracaoValidada>('/configuracao', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(campos),
    signal,
  })
}

export interface ComparacaoValidada {
  repeticoes: string
  contexto_rede: string
  limite_passos: number
  cenarios: ('sem_intervencao' | 'aleatoria' | 'grau')[]
  revisao_rede: number
  populacao: number
  modo_iniciais: 'ids' | 'sorteio'
  quantidade_infectados: number
  quantidade_isolados: number
  intervencao: {
    fracao: number
    inicio: number
    mecanismo: EntradaIntervencao['mecanismo']
    reducao: number | null
  }
  sementes_base: {
    epidemia: string
    iniciais: string
    isolamento: string
  }
  execucao_disponivel: boolean
}

export function validarComparacao(
  repeticoes: string,
  configuracao: FormularioConfiguracao,
  signal?: AbortSignal,
): Promise<ComparacaoValidada> {
  return solicitar<ComparacaoValidada>('/comparacao/validar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repeticoes, configuracao }),
    signal,
  })
}

export interface RegistroResultado {
  passo: number
  suscetiveis: number
  infectados: number
  recuperados: number
  isolados: number
}

export interface ResultadoSimulacao {
  contexto_rede: string
  revisao_rede: number
  populacao: number
  metrica: {
    pico_infectados: number
    passo_pico: number
    pico_proporcional: number
    fracao_acumulada: number
    horizonte_observado: number
    duracao_extincao: number | null
  }
  motivo_termino: 'extincao' | 'limite_passos'
  historico: RegistroResultado[]
}

export interface ExecucaoComparadaResultado {
  repeticao: number
  cenario: 'sem_intervencao' | 'aleatoria' | 'grau'
  metrica: ResultadoSimulacao['metrica']
  motivo_termino: ResultadoSimulacao['motivo_termino']
  historico: RegistroResultado[]
}

export interface ResultadoComparacaoExecutada {
  contexto_rede: string
  revisao_rede: number
  populacao: number
  execucoes: ExecucaoComparadaResultado[]
  resumo: Record<string, { censuradas: number; proporcao_censuradas: number }>
}

export function executarSimulacao(
  campos: FormularioConfiguracao,
  signal?: AbortSignal,
): Promise<ResultadoSimulacao> {
  return solicitar<ResultadoSimulacao>('/simulacao/executar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(campos),
    signal,
  })
}

export function executarComparacao(
  repeticoes: string,
  configuracao: FormularioConfiguracao,
  signal?: AbortSignal,
): Promise<ResultadoComparacaoExecutada> {
  return solicitar<ResultadoComparacaoExecutada>('/comparacao/executar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repeticoes, configuracao }),
    signal,
  })
}
