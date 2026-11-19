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

export interface FormularioConfiguracao {
  beta: string | null
  gamma: string
  modo_peso: 'intensidade' | 'probabilidade'
  modo_iniciais: 'ids' | 'sorteio'
  ids_infectados_iniciais?: string[]
  quantidade_infectados?: string
  semente_epidemia: string
  semente_iniciais: string
  semente_isolamento: string
  limite_passos: string
  revisao_rede: string
  intervencao?: FormularioIntervencao | null
}

export interface ConfiguracaoValidada {
  populacao: number
  modo_iniciais: 'ids' | 'sorteio'
  configuracao: {
    beta: number | null
    gamma: number
    modo_peso: string
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
  execucao_disponivel: false
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
