import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'
import ts from 'typescript'

const raiz = new URL(
  '../src/features/rede/visualizacao/layout/',
  import.meta.url,
)
const terras = JSON.parse(
  await readFile(new URL('../data/world-land.json', raiz), 'utf8'),
)
const fonte = (await readFile(new URL('graphMap.ts', raiz), 'utf8')).replace(
  "import terras from '../data/world-land.json'",
  `const terras = ${JSON.stringify(terras)}`,
)
const { outputText } = ts.transpileModule(fonte, {
  compilerOptions: {
    target: ts.ScriptTarget.ES2023,
    module: ts.ModuleKind.ESNext,
  },
})
const { distribuirNoMapa, criarProjecaoMapa, emTerra } = await import(
  `data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`
)
const camera = {
  azimute: 0,
  elevacao: 0,
  zoom: 1,
  deslocamentoX: 0,
  deslocamentoY: 0,
}
const rede = {
  revisao: 1,
  parcial: false,
  total_individuos: 180,
  total_contatos: 1,
  individuos: Array.from({ length: 180 }, (_, i) => ({
    id: String(i),
    grau: i < 2 ? 1 : 0,
  })),
  contatos: [{ origem: '0', destino: '1', peso: 0.3, ativa: true }],
}

test('contornos distinguem terras e oceanos em diferentes continentes', () => {
  for (const [longitude, latitude] of [
    [-47.9, -15.8],
    [-100, 40],
    [13, 23],
    [90, 45],
    [135, -25],
  ])
    assert(emTerra({ longitude, latitude }))
  for (const [longitude, latitude] of [
    [0, 0],
    [-140, 0],
    [80, -30],
  ])
    assert.equal(emTerra({ longitude, latitude }), false)
})

test('posições ilustrativas são determinísticas, distintas e em terra; domínio preservado', () => {
  const original = structuredClone(rede)
  const pontos = distribuirNoMapa(rede)
  assert.deepEqual(pontos, distribuirNoMapa(rede))
  assert.deepEqual(rede, original)
  assert.deepEqual(
    pontos.map(({ id, grau }) => ({ id, grau })),
    rede.individuos,
  )
  assert.equal(
    new Set(pontos.map((p) => `${p.longitude}:${p.latitude}`)).size,
    180,
  )
  assert(pontos.every(emTerra))
  assert(new Set(pontos.map((p) => Math.sign(p.longitude))).size > 1)
})

test('alterar ordem, grau ou contatos não muda a posição de um ID', () => {
  const original = distribuirNoMapa(rede).sort((a, b) =>
    a.id.localeCompare(b.id),
  )
  const outra = distribuirNoMapa({
    ...rede,
    contatos: [],
    individuos: [...rede.individuos]
      .reverse()
      .map((no) => ({ ...no, grau: 99 })),
  }).sort((a, b) => a.id.localeCompare(b.id))
  assert.deepEqual(
    outra.map(({ id, longitude, latitude }) => ({ id, longitude, latitude })),
    original.map(({ id, longitude, latitude }) => ({
      id,
      longitude,
      latitude,
    })),
  )
})

test('população vazia, pessoa isolada, IDs grandes e negativos são preservados', () => {
  assert.deepEqual(distribuirNoMapa({ ...rede, individuos: [] }), [])
  const individuos = [
    { id: '900719925474099312345678', grau: 0 },
    { id: '-2', grau: 0 },
  ]
  const pontos = distribuirNoMapa({ ...rede, individuos, contatos: [] })
  assert(pontos.every(emTerra))
  assert.deepEqual(
    pontos.map(({ id, grau }) => ({ id, grau })),
    individuos,
  )
  assert(
    emTerra(
      distribuirNoMapa({
        ...rede,
        individuos: [individuos[0]],
        contatos: [],
      })[0],
    ),
  )
})

test('projeção enquadra o mapa e os nós em desktop e mobile; pan e zoom são coerentes', () => {
  for (const [largura, altura] of [
    [1440, 650],
    [320, 320],
    [812, 160],
  ]) {
    const projecao = criarProjecaoMapa(camera, largura, altura)
    for (const ponto of distribuirNoMapa(rede)) {
      const p = projecao.projetar(ponto)
      assert(p.x >= 0 && p.x <= largura)
      assert(p.y >= 0 && p.y <= altura)
    }
    const centro = { longitude: 0, latitude: 15 }
    assert.deepEqual(projecao.projetar(centro), {
      x: largura / 2,
      y: altura / 2,
    })
    const ampliada = criarProjecaoMapa(
      { ...camera, zoom: 8, deslocamentoX: 0.2, deslocamentoY: -0.1 },
      largura,
      altura,
    )
    const p = { longitude: 10, latitude: 5 }
    const base = projecao.projetar(p),
      zoom = ampliada.projetar(p)
    assert(
      Math.abs(
        zoom.x - (largura / 2 + altura * 0.2 + 8 * (base.x - largura / 2)),
      ) < 1e-8,
    )
    assert(
      Math.abs(
        zoom.y - (altura / 2 - altura * 0.1 + 8 * (base.y - altura / 2)),
      ) < 1e-8,
    )
  }
})
