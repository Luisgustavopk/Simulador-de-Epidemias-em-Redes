import type { Camera3D } from '../layout/graph3d'

export type VisualizacaoRede = '3d' | 'mapa'

export interface RenderizadorRede {
  atualizarPaleta(): void
  selecionar(id: string | null, filtrar: boolean): void
  individuoEm(x: number, y: number, tolerancia?: number): string | null
  indicarPonteiro(id: string | null): void
  desenhar(camera: Camera3D, tamanho: { largura: number; altura: number }): void
}
