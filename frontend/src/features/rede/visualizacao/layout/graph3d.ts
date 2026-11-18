import type { PreviaRede } from '../../../../types/rede'

export interface Vetor3D {
  x: number
  y: number
  z: number
}

export interface No3D extends Vetor3D {
  id: string
  grau: number
}

export interface Camera3D {
  azimute: number
  elevacao: number
  zoom: number
  deslocamentoX: number
  deslocamentoY: number
}

export const ZOOM_MINIMO = 0.6
export const ZOOM_MAXIMO = 2.4
export const CAMERA_INICIAL: Readonly<Camera3D> = {
  azimute: 0.35,
  elevacao: -0.2,
  zoom: 1,
  deslocamentoX: 0,
  deslocamentoY: 0,
}

const limitar = (valor: number, minimo: number, maximo: number) =>
  Math.max(minimo, Math.min(maximo, valor))

export function aproximar(
  camera: Camera3D,
  fator: number,
  maximo = ZOOM_MAXIMO,
): Camera3D {
  return {
    ...camera,
    zoom: limitar(camera.zoom * fator, ZOOM_MINIMO, maximo),
  }
}

export function girar(camera: Camera3D, x: number, y: number): Camera3D {
  return {
    ...camera,
    azimute: (camera.azimute + x) % (2 * Math.PI),
    elevacao: limitar(camera.elevacao + y, -Math.PI / 2, Math.PI / 2),
  }
}

export function deslocar(
  camera: Camera3D,
  x: number,
  y: number,
  limite = 2,
): Camera3D {
  return {
    ...camera,
    deslocamentoX: limitar(camera.deslocamentoX + x, -limite, limite),
    deslocamentoY: limitar(camera.deslocamentoY + y, -limite, limite),
  }
}

export function rotacionar(ponto: Vetor3D, camera: Camera3D): Vetor3D {
  const x =
    ponto.x * Math.cos(camera.azimute) + ponto.z * Math.sin(camera.azimute)
  const z =
    -ponto.x * Math.sin(camera.azimute) + ponto.z * Math.cos(camera.azimute)
  return {
    x,
    y: ponto.y * Math.cos(camera.elevacao) - z * Math.sin(camera.elevacao),
    z: ponto.y * Math.sin(camera.elevacao) + z * Math.cos(camera.elevacao),
  }
}

export function projetar(
  ponto: Vetor3D,
  camera: Camera3D,
  largura: number,
  altura: number,
) {
  return criarProjecao(camera, largura, altura)(ponto)
}

/** Reutiliza os coeficientes da câmera para todos os nós de um quadro. */
export function criarProjecao(
  camera: Camera3D,
  largura: number,
  altura: number,
) {
  const cosA = Math.cos(camera.azimute)
  const sinA = Math.sin(camera.azimute)
  const cosE = Math.cos(camera.elevacao)
  const sinE = Math.sin(camera.elevacao)
  // O limite de zoom mantém a câmera fora da esfera que contém os nós (raio 180).
  const distancia = 520 / camera.zoom
  const foco = Math.min(largura, altura) * 1.2
  const centroX = largura / 2 + camera.deslocamentoX * altura
  const centroY = altura / 2 + camera.deslocamentoY * altura
  return (ponto: Vetor3D) => {
    const x = ponto.x * cosA + ponto.z * sinA
    const z = -ponto.x * sinA + ponto.z * cosA
    const y = ponto.y * cosE - z * sinE
    const profundidade = ponto.y * sinE + z * cosE
    const escala = foco / (distancia - profundidade)
    return {
      x: centroX + x * escala,
      y: centroY + y * escala,
      profundidade,
      escala,
    }
  }
}

/** Escala comum entre redes, com compressão logarítmica e perspectiva discreta. */
export function raioDoNo(grau: number, escala: number) {
  // Não normalizar pelo máximo da prévia: o mesmo grau deve ter a mesma base.
  const base = 2.5 + Math.min(1.5, Math.log2(1 + Math.max(0, grau)) * 0.25)
  return base * limitar(Math.sqrt(escala / 0.95), 0.9, 1.1)
}

export interface NoProjetado {
  id: string
  x: number
  y: number
  raio: number
  profundidade: number
}

/** Pontos ordenados do fundo para a frente; o corpo visível tem prioridade. */
export function encontrarNo(
  pontos: readonly NoProjetado[],
  x: number,
  y: number,
  tolerancia: number,
) {
  let melhor: string | null = null
  let menorDistancia = Infinity
  for (let i = pontos.length - 1; i >= 0; i--) {
    const ponto = pontos[i]
    const distancia = Math.hypot(x - ponto.x, y - ponto.y)
    if (distancia <= ponto.raio + 1) return ponto.id
    if (
      distancia <= Math.max(ponto.raio, tolerancia) &&
      distancia < menorDistancia
    ) {
      melhor = ponto.id
      menorDistancia = distancia
    }
  }
  return melhor
}

/** Layout de apresentação: não altera contatos, graus ou o estado do domínio. */
export function distribuirEm3D(previa: PreviaRede): No3D[] {
  const total = previa.individuos.length
  if (total < 2)
    return previa.individuos.map((no) => ({ ...no, x: 0, y: 0, z: 0 }))

  // Esfera de Fibonacci: inicialização determinística sem consumir a semente SIR.
  const pontos = previa.individuos.map((no, i) => {
    const y = 1 - (2 * (i + 0.5)) / total
    const raio = Math.sqrt(1 - y * y)
    const angulo = i * Math.PI * (3 - Math.sqrt(5))
    return {
      ...no,
      x: 100 * raio * Math.cos(angulo),
      y: 100 * y,
      z: 100 * raio * Math.sin(angulo),
    }
  })
  const indices = new Map(pontos.map((ponto, i) => [ponto.id, i]))
  const ligacoes = previa.contatos.flatMap((contato) => {
    const a = indices.get(contato.origem)
    const b = indices.get(contato.destino)
    return a === undefined || b === undefined ? [] : [[a, b]]
  })
  const forcas = pontos.map(() => ({ x: 0, y: 0, z: 0 }))
  const distanciaIdeal = 65

  // Relaxamento limitado à prévia (até 180 nós), calculado uma vez por carga.
  // Repulsão separa nós; molas aproximam vizinhos. Pesos não viram distâncias.
  for (let passo = 0; passo < 100; passo++) {
    for (const forca of forcas) forca.x = forca.y = forca.z = 0
    for (let i = 0; i < total; i++) {
      for (let j = i + 1; j < total; j++) {
        const dx = pontos[i].x - pontos[j].x
        const dy = pontos[i].y - pontos[j].y
        const dz = pontos[i].z - pontos[j].z
        const distancia2 = Math.max(dx * dx + dy * dy + dz * dz, 0.01)
        const fator = (distanciaIdeal * distanciaIdeal) / distancia2
        forcas[i].x += dx * fator
        forcas[i].y += dy * fator
        forcas[i].z += dz * fator
        forcas[j].x -= dx * fator
        forcas[j].y -= dy * fator
        forcas[j].z -= dz * fator
      }
    }
    for (const [a, b] of ligacoes) {
      const dx = pontos[a].x - pontos[b].x
      const dy = pontos[a].y - pontos[b].y
      const dz = pontos[a].z - pontos[b].z
      const fator = Math.hypot(dx, dy, dz) / distanciaIdeal
      forcas[a].x -= dx * fator
      forcas[a].y -= dy * fator
      forcas[a].z -= dz * fator
      forcas[b].x += dx * fator
      forcas[b].y += dy * fator
      forcas[b].z += dz * fator
    }
    const temperatura = 12 * (1 - passo / 100) + 0.1
    for (let i = 0; i < total; i++) {
      const forca = forcas[i]
      const fator = Math.min(
        1,
        temperatura / Math.max(Math.hypot(forca.x, forca.y, forca.z), 0.01),
      )
      pontos[i].x += forca.x * fator
      pontos[i].y += forca.y * fator
      pontos[i].z += forca.z * fator
    }
  }

  const centro = pontos.reduce(
    (soma, ponto) => ({
      x: soma.x + ponto.x / total,
      y: soma.y + ponto.y / total,
      z: soma.z + ponto.z / total,
    }),
    { x: 0, y: 0, z: 0 },
  )
  const raio = Math.max(
    ...pontos.map((ponto) =>
      Math.hypot(ponto.x - centro.x, ponto.y - centro.y, ponto.z - centro.z),
    ),
    1,
  )
  return pontos.map((ponto) => ({
    ...ponto,
    x: ((ponto.x - centro.x) * 180) / raio,
    y: ((ponto.y - centro.y) * 180) / raio,
    z: ((ponto.z - centro.z) * 180) / raio,
  }))
}
