import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'
import ts from 'typescript'

const fonte = await readFile(
  new URL(
    '../src/features/rede/visualizacao/layout/graph3d.ts',
    import.meta.url,
  ),
  'utf8',
)
const { outputText } = ts.transpileModule(fonte, {
  compilerOptions: {
    target: ts.ScriptTarget.ES2023,
    module: ts.ModuleKind.ESNext,
  },
})
const {
  distribuirEm3D,
  raioDoNo,
  encontrarNo,
  projetar,
  rotacionar,
  girar,
  aproximar,
  deslocar,
  CAMERA_INICIAL,
  ZOOM_MINIMO,
  ZOOM_MAXIMO,
} = await import(
  `data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`
)

function previa(n, contatos = []) {
  return {
    revisao: 1,
    individuos: Array.from({ length: n }, (_, i) => ({
      id: String(i),
      grau: contatos.filter(
        (c) => c.origem === String(i) || c.destino === String(i),
      ).length,
    })),
    contatos,
    total_individuos: n,
    total_contatos: contatos.length,
    parcial: false,
  }
}
const contato = (a, b) => ({
  origem: String(a),
  destino: String(b),
  peso: 0.5,
  ativa: true,
})

test('layout determinístico preserva IDs, graus, contatos e pesos do domínio', () => {
  const rede = previa(
    12,
    Array.from({ length: 11 }, (_, i) => contato(i, i + 1)),
  )
  rede.individuos[0].id = '900719925474099312345'
  rede.contatos[0].origem = rede.individuos[0].id
  const original = structuredClone(rede)
  const pontos = distribuirEm3D(rede)
  assert.deepEqual(pontos, distribuirEm3D(rede))
  assert.deepEqual(rede, original)
  assert.deepEqual(
    pontos.map(({ id, grau }) => ({ id, grau })),
    rede.individuos,
  )
  assert(new Set(pontos.map((p) => p.z.toFixed(4))).size > 2)
  assert.notDeepEqual(pontos, distribuirEm3D({ ...rede, contatos: [] }))
  assert.deepEqual(
    pontos,
    distribuirEm3D({
      ...rede,
      contatos: rede.contatos.map((c) => ({ ...c, peso: 0.1 })),
    }),
  )
})

test('prévia vazia, pessoa única e população sem contatos têm posições finitas', () => {
  assert.deepEqual(distribuirEm3D(previa(0)), [])
  assert.deepEqual(distribuirEm3D(previa(1)), [
    { id: '0', grau: 0, x: 0, y: 0, z: 0 },
  ])
  for (const no of distribuirEm3D(previa(180))) {
    assert(
      Number.isFinite(no.x) && Number.isFinite(no.y) && Number.isFinite(no.z),
    )
    assert(Math.hypot(no.x, no.y, no.z) <= 180.000001)
  }
})

test('rede densa mantém câmera fora dos nós mesmo no zoom máximo', () => {
  const contatos = []
  for (let a = 0; a < 24; a++)
    for (let b = a + 1; b < 24; b++) contatos.push(contato(a, b))
  for (const no of distribuirEm3D(previa(24, contatos))) {
    for (const zoom of [ZOOM_MINIMO, 1, ZOOM_MAXIMO]) {
      const ponto = projetar(no, { ...CAMERA_INICIAL, zoom }, 240, 320)
      assert(Number.isFinite(ponto.x) && Number.isFinite(ponto.y))
      assert(ponto.escala > 0)
    }
  }
})

test('perspectiva distingue pontos de mesma posição XY em profundidades diferentes', () => {
  const camera = { ...CAMERA_INICIAL, azimute: 0, elevacao: 0 }
  const longe = projetar({ x: 50, y: 30, z: -100 }, camera, 720, 420)
  const perto = projetar({ x: 50, y: 30, z: 100 }, camera, 720, 420)
  assert(perto.escala > longe.escala)
  assert(perto.x > longe.x)
  assert(perto.y > longe.y)
  assert.deepEqual(rotacionar({ x: 10, y: 20, z: 30 }, camera), {
    x: 10,
    y: 20,
    z: 30,
  })
  const giro = projetar(
    { x: 50, y: 30, z: 100 },
    girar(camera, Math.PI / 2, 0),
    720,
    420,
  )
  assert.notEqual(giro.profundidade, perto.profundidade)
  assert.notEqual(giro.x, perto.x)
})

test('limites de órbita, zoom e deslocamento evitam inversões e mantêm restauração independente', () => {
  const original = { ...CAMERA_INICIAL }
  assert.equal(aproximar(original, 100).zoom, ZOOM_MAXIMO)
  assert.equal(aproximar(original, 0.001).zoom, ZOOM_MINIMO)
  assert.equal(girar(original, 10000, 10000).elevacao, Math.PI / 2)
  assert.equal(girar(original, -10000, -10000).elevacao, -Math.PI / 2)
  assert(Math.abs(girar(original, 10000, 0).azimute) < 2 * Math.PI)
  assert.equal(deslocar(original, 100, -100).deslocamentoX, 2)
  assert.equal(deslocar(original, 100, -100).deslocamentoY, -2)
  assert.deepEqual(CAMERA_INICIAL, original)
})

test('escala comum de grau mantém os vértices pequenos e a perspectiva limitada', () => {
  for (const grau of [0, 1, 20, 100, 1000000]) {
    for (const escala of [0.01, 0.3, 1, 3, 100]) {
      const raio = raioDoNo(grau, escala)
      assert(raio >= 2.25 && raio <= 4.4)
    }
  }
  assert(raioDoNo(100, 1) > raioDoNo(1, 1))
  assert(Number.isFinite(raioDoNo(0, 1)))
  assert(raioDoNo(1000000, 1) <= 4.4)
  const graus = [0, 1, 2, 8, 16, 32, 64, 128, 10000]
  const tamanhos = graus.map((grau) => raioDoNo(grau, 0.95))
  assert(tamanhos.every((raio, i) => i === 0 || raio >= tamanhos[i - 1]))
  assert(tamanhos.at(-1) - tamanhos[0] <= 1.5)
})

test('seleção prioriza o corpo visível mais próximo da câmera e preserva IDs textuais', () => {
  const pontos = [
    { id: '-2', x: 10, y: 20, raio: 5, profundidade: -30 },
    { id: '900719925474099312345', x: 10, y: 20, raio: 3, profundidade: 30 },
  ]
  assert.equal(encontrarNo(pontos, 10, 20, 10), '900719925474099312345')
  assert.equal(encontrarNo(pontos, 15, 20, 10), '-2')
  assert.equal(encontrarNo(pontos, 80, 20, 10), null)
})

test('alvo de toque é maior que o desenho sem selecionar pontos distantes', () => {
  const pontos = [{ id: '0', x: 100, y: 100, raio: 3, profundidade: 0 }]
  assert.equal(encontrarNo(pontos, 115, 100, 10), null)
  assert.equal(encontrarNo(pontos, 115, 100, 20), '0')
  assert.equal(encontrarNo(pontos, 125, 100, 20), null)
  assert.equal(encontrarNo([], 100, 100, 20), null)
})
