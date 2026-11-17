import type { PreviaRede } from '../../../../types/rede'
import { encontrarNo, raioDoNo } from '../layout/graph3d'
import type { Camera3D, NoProjetado } from '../layout/graph3d'
import { criarProjecaoMapa, POLIGONOS } from '../layout/graphMap'
import type { NoMapa } from '../layout/graphMap'
import type { RenderizadorRede } from './networkRenderer'

interface Ponto extends NoProjetado {
  grau: number
}

/** Canvas nativo: contornos geográficos em cache, contatos reais em dois lotes. */
export class RenderizadorRedeMapa implements RenderizadorRede {
  private readonly canvas: HTMLCanvasElement
  private readonly contexto: CanvasRenderingContext2D
  private readonly nos: NoMapa[]
  private readonly contatos: [number, number][]
  private readonly terra = new Path2D()
  private readonly maiorGrau: number
  private readonly vizinhos = new Set<string>()
  private pontos: Ponto[] = []
  private selecionado: string | null = null
  private filtrar = false
  private sobre: string | null = null
  private paleta = {
    fundo: '',
    texto: '',
    linha: '',
    no: '',
    destaque: '',
    terra: '',
    costa: '',
    fonte: '',
  }

  constructor(
    canvas: HTMLCanvasElement,
    contexto: CanvasRenderingContext2D,
    nos: NoMapa[],
    previa: PreviaRede,
  ) {
    this.canvas = canvas
    this.contexto = contexto
    this.nos = nos
    this.maiorGrau = Math.max(1, ...nos.map((no) => no.grau))
    const indices = new Map(nos.map((no, i) => [no.id, i]))
    this.contatos = previa.contatos.flatMap((contato) => {
      const a = indices.get(contato.origem),
        b = indices.get(contato.destino)
      return a === undefined || b === undefined
        ? []
        : [[a, b] as [number, number]]
    })
    for (const { aneis } of POLIGONOS)
      for (const anel of aneis) {
        anel.forEach(([x, y], i) =>
          i ? this.terra.lineTo(x, 15 - y) : this.terra.moveTo(x, 15 - y),
        )
        this.terra.closePath()
      }
    this.atualizarPaleta()
  }

  atualizarPaleta() {
    const css = getComputedStyle(this.canvas)
    const cor = (nome: string) => css.getPropertyValue(`--plot-${nome}`).trim()
    this.paleta = {
      fundo: cor('background'),
      texto: cor('text'),
      linha: cor('line'),
      no: cor('node'),
      destaque: cor('hub'),
      terra: cor('land'),
      costa: cor('coast'),
      fonte: css.getPropertyValue('--font-sans').trim(),
    }
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
      ? `Indivíduo ${ponto.id} · grau ${ponto.grau} · posição ilustrativa`
      : ''
    this.canvas.dataset.nodeHover = String(id !== null)
  }

  desenhar(
    camera: Camera3D,
    { largura, altura }: { largura: number; altura: number },
  ) {
    const ctx = this.contexto
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    const w = Math.round(largura * dpr),
      h = Math.round(altura * dpr)
    if (this.canvas.width !== w || this.canvas.height !== h) {
      this.canvas.width = w
      this.canvas.height = h
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    ctx.globalAlpha = 1
    ctx.fillStyle = this.paleta.fundo
    ctx.fillRect(0, 0, largura, altura)
    const projecao = criarProjecaoMapa(camera, largura, altura)
    ctx.save()
    ctx.translate(projecao.x, projecao.y)
    ctx.scale(projecao.escala, projecao.escala)
    ctx.fillStyle = this.paleta.terra
    ctx.fill(this.terra, 'evenodd')
    ctx.strokeStyle = this.paleta.costa
    ctx.lineWidth = 0.65 / projecao.escala
    ctx.stroke(this.terra)
    ctx.restore()
    const pontos = this.nos.map((no) => ({
      ...no,
      ...projecao.projetar(no),
      raio: raioDoNo(no.grau, this.maiorGrau, 0.95),
      profundidade: 0,
    }))
    for (const diretos of [false, true]) {
      if (!diretos && this.filtrar) continue
      ctx.beginPath()
      for (const [a, b] of this.contatos) {
        const selecionado =
          pontos[a].id === this.selecionado || pontos[b].id === this.selecionado
        if (selecionado !== diretos) continue
        ctx.moveTo(pontos[a].x, pontos[a].y)
        ctx.lineTo(pontos[b].x, pontos[b].y)
      }
      ctx.strokeStyle = diretos ? this.paleta.destaque : this.paleta.linha
      ctx.globalAlpha = diretos ? 0.85 : 0.18
      ctx.lineWidth = diretos ? 1.2 : 0.65
      ctx.stroke()
    }
    // O selecionado é desenhado por último e tem prioridade na seleção.
    this.pontos = pontos
      .filter(
        (no) =>
          no.x >= -20 &&
          no.x <= largura + 20 &&
          no.y >= -20 &&
          no.y <= altura + 20,
      )
      .sort(
        (a, b) =>
          Number(a.id === this.selecionado) - Number(b.id === this.selecionado),
      )
    for (const no of this.pontos) {
      ctx.globalAlpha = this.filtrar && !this.vizinhos.has(no.id) ? 0.15 : 1
      ctx.fillStyle =
        no.grau > this.maiorGrau * 0.55 ? this.paleta.destaque : this.paleta.no
      ctx.beginPath()
      ctx.arc(no.x, no.y, no.raio, 0, 2 * Math.PI)
      ctx.fill()
    }
    ctx.globalAlpha = 1
    const no = this.pontos.find((ponto) => ponto.id === this.selecionado)
    if (no) {
      ctx.strokeStyle = this.paleta.destaque
      ctx.lineWidth = 1.5
      ctx.beginPath()
      ctx.arc(no.x, no.y, no.raio + 4, 0, Math.PI * 2)
      ctx.stroke()
      const id = no.id.length > 18 ? `${no.id.slice(0, 16)}…` : no.id
      ctx.font = `12px ${this.paleta.fonte}`
      ctx.lineWidth = 3
      ctx.strokeStyle = this.paleta.fundo
      ctx.strokeText(id, no.x + no.raio + 9, no.y + 4)
      ctx.fillStyle = this.paleta.texto
      ctx.fillText(id, no.x + no.raio + 9, no.y + 4)
    }
  }
}
