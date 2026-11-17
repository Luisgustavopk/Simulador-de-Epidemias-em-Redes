import { solicitar } from './redeApi'

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
