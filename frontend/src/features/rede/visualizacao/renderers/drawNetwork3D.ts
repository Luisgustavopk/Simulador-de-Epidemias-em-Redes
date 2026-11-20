import type { PreviaRede } from '../../../../types/rede'
import {
  criarProjecao,
  encontrarNo,
  raioDoNo,
  rotacionar,
} from '../layout/graph3d'
import type { Camera3D, No3D, NoProjetado } from '../layout/graph3d'
import type { RenderizadorRede } from './networkRenderer'

export interface TamanhoCena {
  largura: number
  altura: number
}
interface Ponto extends NoProjetado {
  grau: number
  escala: number
}
interface Paleta {
  fundo: string
  texto: string
  secundario: string
  linha: string
  no: string
  destaque: string
  fonte: string
}
const eixos = [
  { nome: 'X', x: 23, y: 0, z: 0 },
  { nome: 'Y', x: 0, y: -23, z: 0 },
  { nome: 'Z', x: 0, y: 0, z: 23 },
]

/** Desenho da prévia, independente do ciclo de renderização do React. */
export class RenderizadorRede3D implements RenderizadorRede {
  private readonly canvas: HTMLCanvasElement
  private readonly contexto: CanvasRenderingContext2D
  private readonly nos: No3D[]
  private readonly contatos: [number, number][]
  private readonly vizinhos = new Set<string>()
  private readonly sprites = new Map<string, HTMLCanvasElement>()
  private paleta!: Paleta
  private pontos: Ponto[] = []
  private selecionado: string | null = null
  private filtrar = false
  private sobre: string | null = null
  private estadosPorNo: Record<string, 'S' | 'I' | 'R' | 'isolado'> = {}

  constructor(
    canvas: HTMLCanvasElement,
    contexto: CanvasRenderingContext2D,
    nos: No3D[],
    previa: PreviaRede,
    estadosPorNo?: Record<string, 'S' | 'I' | 'R' | 'isolado'>,
  ) {
    this.canvas = canvas
    this.contexto = contexto
    this.nos = nos
    this.estadosPorNo = estadosPorNo ?? {}
    const indices = new Map(nos.map((no, i) => [no.id, i]))
    this.contatos = previa.contatos.flatMap((contato) => {
      const a = indices.get(contato.origem),
        b = indices.get(contato.destino)
      return a === undefined || b === undefined
        ? []
        : [[a, b] as [number, number]]
    })
    this.atualizarPaleta()
  }

  atualizarPaleta() {
    const css = getComputedStyle(this.canvas)
    const cor = (nome: string) => css.getPropertyValue(`--plot-${nome}`).trim()
    this.paleta = {
      fundo: cor('background'),
      texto: cor('text'),
      secundario: cor('muted'),
      linha: cor('line'),
      no: cor('node'),
      destaque: cor('hub'),
      fonte: css.getPropertyValue('--font-sans').trim(),
    }
    this.sprites.clear()
  }

  selecionar(id: string | null, filtrar: boolean) {
    this.selecionado = id
    this.filtrar = filtrar
    this.vizinhos.clear()
    if (id !== null) this.vizinhos.add(id)
    for (const [a, b] of this.contatos) {
      if (this.nos[a].id === id) this.vizinhos.add(this.nos[b].id)
      if (this.nos[b].id === id) this.vizinhos.add(this.nos[a].id)
    }
  }

  individuoEm(x: number, y: number, tolerancia = 10) {
    return encontrarNo(this.pontos, x, y, tolerancia)
  }

  indicarPonteiro(id: string | null) {
    if (this.sobre === id) return
    this.sobre = id
    const ponto = this.pontos.find((no) => no.id === id)
    this.canvas.title = ponto
      ? `Indivíduo ${ponto.id} · grau ${ponto.grau}`
      : ''
    this.canvas.dataset.nodeHover = String(id !== null)
  }

  private esfera(selecionado: boolean, camada: number, estado: 'S' | 'I' | 'R' | 'isolado' | undefined) {
    const chave = `${selecionado}:${camada}:${estado ?? 'padrao'}`
    const existente = this.sprites.get(chave)
    if (existente) return existente
    const sprite = document.createElement('canvas')
    sprite.width = sprite.height = 40
    const contexto = sprite.getContext('2d')
    if (contexto) {
      // Cada esfera é opaca; a profundidade altera a cor, sem somar transparências.
      contexto.beginPath()
      contexto.arc(20, 20, 19, 0, Math.PI * 2)
      contexto.fillStyle = selecionado
        ? this.paleta.destaque
        : estado === 'I'
          ? '#ac4433'
          : estado === 'R'
            ? '#487751'
            : estado === 'isolado'
              ? '#c79a42'
              : estado === 'S'
                ? '#315d88'
                : this.paleta.no
      contexto.fill()
      const luz = contexto.createRadialGradient(13, 12, 0, 20, 20, 22)
      luz.addColorStop(0, '#ffffff30')
      luz.addColorStop(0.45, '#ffffff00')
      luz.addColorStop(1, '#00000055')
      contexto.fillStyle = luz
      contexto.fill()
      contexto.globalAlpha = (3 - camada) * 0.12
      contexto.fillStyle = this.paleta.fundo
      contexto.fill()
    }
    this.sprites.set(chave, sprite)
    return sprite
  }

  desenhar(camera: Camera3D, { largura, altura }: TamanhoCena) {
    const contexto = this.contexto
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    const larguraFisica = Math.round(largura * dpr),
      alturaFisica = Math.round(altura * dpr)
    if (
      this.canvas.width !== larguraFisica ||
      this.canvas.height !== alturaFisica
    ) {
      this.canvas.width = larguraFisica
      this.canvas.height = alturaFisica
    }
    contexto.setTransform(dpr, 0, 0, dpr, 0, 0)
    contexto.globalAlpha = 1
    contexto.fillStyle = this.paleta.fundo
    contexto.fillRect(0, 0, largura, altura)
    const projetar = criarProjecao(camera, largura, altura)
    const pontos = this.nos.map((no) => {
      const ponto = projetar(no)
      return {
        ...no,
        ...ponto,
        raio: raioDoNo(no.grau, ponto.escala),
      }
    })
    // Arestas em dois lotes; não há um elemento DOM ou stroke por contato.
    for (const diretos of [false, true]) {
      if (!diretos && this.filtrar) continue
      contexto.beginPath()
      for (const [a, b] of this.contatos) {
        const origem = pontos[a],
          destino = pontos[b]
        const direto =
          origem.id === this.selecionado || destino.id === this.selecionado
        if (direto !== diretos) continue
        contexto.moveTo(origem.x, origem.y)
        contexto.lineTo(destino.x, destino.y)
      }
      contexto.strokeStyle = diretos ? this.paleta.destaque : this.paleta.linha
      contexto.globalAlpha = diretos ? 0.85 : 0.23
      contexto.lineWidth = diretos ? 1.2 : 0.65
      contexto.stroke()
    }
    this.pontos = pontos.sort((a, b) => a.profundidade - b.profundidade)
    for (const ponto of this.pontos) {
      if (
        ponto.x < -20 ||
        ponto.x > largura + 20 ||
        ponto.y < -20 ||
        ponto.y > altura + 20
      )
        continue
      contexto.globalAlpha =
        this.filtrar && !this.vizinhos.has(ponto.id) ? 0.15 : 1
      const camada = Math.max(
        0,
        Math.min(3, Math.floor((ponto.profundidade + 180) / 90)),
      )
      const selecionado = ponto.id === this.selecionado
      contexto.drawImage(
        this.esfera(selecionado, selecionado ? 3 : camada, this.estadosPorNo[ponto.id]),
        ponto.x - ponto.raio,
        ponto.y - ponto.raio,
        ponto.raio * 2,
        ponto.raio * 2,
      )
    }
    contexto.globalAlpha = 1
    const selecionado = this.pontos.find(
      (ponto) => ponto.id === this.selecionado,
    )
    if (selecionado) {
      contexto.beginPath()
      contexto.arc(
        selecionado.x,
        selecionado.y,
        selecionado.raio + 4,
        0,
        Math.PI * 2,
      )
      contexto.strokeStyle = this.paleta.destaque
      contexto.lineWidth = 1.5
      contexto.stroke()
      const id =
        selecionado.id.length > 18
          ? `${selecionado.id.slice(0, 16)}…`
          : selecionado.id
      contexto.font = `12px ${this.paleta.fonte}`
      contexto.lineWidth = 3
      contexto.strokeStyle = this.paleta.fundo
      contexto.strokeText(
        id,
        selecionado.x + selecionado.raio + 9,
        selecionado.y + 4,
      )
      contexto.fillStyle = this.paleta.texto
      contexto.fillText(
        id,
        selecionado.x + selecionado.raio + 9,
        selecionado.y + 4,
      )
    }
    contexto.strokeStyle = this.paleta.secundario
    contexto.fillStyle = this.paleta.secundario
    contexto.lineWidth = 1
    contexto.font = `10px ${this.paleta.fonte}`
    contexto.textAlign = 'center'
    for (const eixo of eixos) {
      const ponto = rotacionar(eixo, camera)
      contexto.beginPath()
      contexto.moveTo(42, altura - 46)
      contexto.lineTo(42 + ponto.x, altura - 46 + ponto.y)
      contexto.stroke()
      contexto.fillText(
        eixo.nome,
        42 + ponto.x * 1.35,
        altura - 43 + ponto.y * 1.35,
      )
    }
    contexto.textAlign = 'start'
  }
}
