import terras from '../data/world-land.json'
import type { PreviaRede } from '../../../../types/rede'
import type { Camera3D } from './graph3d'

export interface LocalIlustrativo {
  longitude: number
  latitude: number
}
export interface NoMapa extends LocalIlustrativo {
  id: string
  grau: number
}

// Contornos Natural Earth 1:110m incorporados ao protótipo. Ver data/README.md.
export const POLIGONOS = terras.map((aneis) => ({
  aneis,
  limites: aneis[0].reduce(
    (b, [x, y]) => [
      Math.min(b[0], x),
      Math.min(b[1], y),
      Math.max(b[2], x),
      Math.max(b[3], y),
    ],
    [180, 90, -180, -90],
  ),
}))

function dentroDoAnel(x: number, y: number, anel: number[][]) {
  let dentro = false
  for (let i = 0, j = anel.length - 1; i < anel.length; j = i++) {
    const [xi, yi] = anel[i],
      [xj, yj] = anel[j]
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi)
      dentro = !dentro
  }
  return dentro
}

export function emTerra({ longitude: x, latitude: y }: LocalIlustrativo) {
  return POLIGONOS.some(
    ({ aneis, limites: [esq, baixo, dir, cima] }) =>
      x >= esq &&
      x <= dir &&
      y >= baixo &&
      y <= cima &&
      dentroDoAnel(x, y, aneis[0]) &&
      !aneis.slice(1).some((anel) => dentroDoAnel(x, y, anel)),
  )
}

let candidatos: LocalIlustrativo[] | undefined
function locaisEmTerra() {
  if (candidatos) return candidatos
  candidatos = []
  for (let latitude = -54; latitude <= 76; latitude += 3)
    for (let longitude = -171; longitude <= 177; longitude += 3)
      if (emTerra({ longitude, latitude }))
        candidatos.push({ longitude, latitude })
  return candidatos
}

/** Hash de apresentação; não converte IDs em números nem usa a semente do motor. */
function hash(texto: string) {
  let valor = 2166136261
  for (let i = 0; i < texto.length; i++)
    valor = Math.imul(valor ^ texto.charCodeAt(i), 16777619)
  return valor >>> 0
}

/** Localizações fictícias, estáveis por ID na mesma prévia; não são dados geográficos. */
export function distribuirNoMapa(previa: PreviaRede): NoMapa[] {
  const locais = locaisEmTerra()
  const ocupados = new Set<number>()
  const posicoes = new Map<string, LocalIlustrativo>()
  // A ordem recebida e o grau não determinam a posição de um indivíduo.
  for (const { id } of [...previa.individuos].sort((a, b) =>
    a.id < b.id ? -1 : a.id > b.id ? 1 : 0,
  )) {
    let indice = hash(id) % locais.length
    while (ocupados.size < locais.length && ocupados.has(indice))
      indice = (indice + 1) % locais.length
    ocupados.add(indice)
    const centro = locais[indice]
    let local = centro
    for (let tentativa = 0; tentativa < 8; tentativa++) {
      const ponto = {
        longitude:
          centro.longitude + (hash(`${id}:x:${tentativa}`) / 2 ** 32 - 0.5) * 2,
        latitude:
          centro.latitude + (hash(`${id}:y:${tentativa}`) / 2 ** 32 - 0.5) * 2,
      }
      if (emTerra(ponto)) {
        local = ponto
        break
      }
    }
    posicoes.set(id, local)
  }
  return previa.individuos.map((no) => ({ ...no, ...posicoes.get(no.id)! }))
}

/** Mesma transformação para continentes, contatos, indivíduos e seleção. */
export function criarProjecaoMapa(
  camera: Camera3D,
  largura: number,
  altura: number,
) {
  const escala =
    Math.max(0.01, Math.min((largura - 32) / 360, (altura - 32) / 150)) *
    camera.zoom
  const x = largura / 2 + camera.deslocamentoX * altura
  const y = altura / 2 + camera.deslocamentoY * altura
  return {
    escala,
    x,
    y,
    projetar: ({ longitude, latitude }: LocalIlustrativo) => ({
      x: x + longitude * escala,
      y: y + (15 - latitude) * escala,
    }),
  }
}
