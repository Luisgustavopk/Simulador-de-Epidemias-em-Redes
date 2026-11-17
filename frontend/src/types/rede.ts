export type ModeloRede = 'barabasi_albert' | 'erdos_renyi'

export interface ProblemaCarga {
  campo: string
  mensagem: string
  arquivo?: string | null
  linha?: number | null
  coluna?: string | null
}

export interface ResumoEstrutural {
  numero_individuos: number
  numero_contatos: number
  grau_medio: number
  grau_maximo: number
  numero_componentes: number
  conexa: boolean
  individuos_sem_contatos: number
  distribuicao_graus: { grau: number; quantidade: number }[]
}

export interface OrigemRede {
  tipo: 'sintetica' | 'observada'
  modelo?: ModeloRede
  semente?: string
  parametros?: Record<string, number>
  arquivo_contatos?: string
  arquivo_individuos?: string | null
}

export interface InspecaoRede {
  revisao: number
  disponivel: boolean
  confirmada: boolean
  origem: OrigemRede | null
  resumo: ResumoEstrutural | null
  interpretacao_pesos: string
}

export interface NoRede {
  id: string
  grau: number
}

export interface ContatoRede {
  origem: string
  destino: string
  peso: number
  ativa: boolean
}

export interface PreviaRede {
  revisao: number
  individuos: NoRede[]
  contatos: ContatoRede[]
  total_individuos: number
  total_contatos: number
  parcial: boolean
}

export interface IndividuoInspecionado extends NoRede {
  revisao: number
  estado: 'S' | 'I' | 'R'
  isolamento: boolean
  dia_inicio_infeccao: number | null
}

export interface PaginaIndividuos {
  revisao: number
  total: number
  inicio: number
  individuos: NoRede[]
}

export interface PaginaContatos {
  revisao: number
  total: number
  inicio: number
  contatos: ContatoRede[]
}

export interface FormularioGeracao {
  modelo: ModeloRede
  numero_individuos: string
  semente: string
  peso: string
  probabilidade_contato?: string
  contatos_por_novo_individuo?: string
}

export const nomesModelos: Record<ModeloRede, string> = {
  barabasi_albert: 'Barabási–Albert',
  erdos_renyi: 'Erdős–Rényi',
}

export function descreverOrigem(rede: InspecaoRede | null): string {
  const origem = rede?.origem
  if (!origem) return 'Nenhuma rede carregada'
  return origem.tipo === 'sintetica' && origem.modelo
    ? `${nomesModelos[origem.modelo]} · semente ${origem.semente}`
    : (origem.arquivo_contatos ?? 'Rede importada')
}
