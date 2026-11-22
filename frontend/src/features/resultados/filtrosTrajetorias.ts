import type { CampoCurva, NOMES_CENARIOS } from './dadosResultados'

export type CenarioGrafico = keyof typeof NOMES_CENARIOS
export type ModoGrafico = 'medias' | 'repeticao' | 'todas'

export interface FiltrosTrajetorias {
  series: Record<CampoCurva, boolean>
  cenarios: Record<CenarioGrafico, boolean>
  modo: ModoGrafico
  repeticao: number | null
  mostrarDesvio: boolean
  inicio: number
  fim: number | null
}

export function filtrosTrajetoriasPadrao(): FiltrosTrajetorias {
  return {
    series: {
      suscetiveis: false,
      infectados: true,
      recuperados: false,
      isolados: false,
    },
    cenarios: { sem_intervencao: true, aleatoria: true, grau: true },
    modo: 'medias',
    repeticao: null,
    mostrarDesvio: true,
    inicio: 0,
    fim: null,
  }
}
