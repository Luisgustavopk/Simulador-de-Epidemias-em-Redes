import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'
import ts from 'typescript'

function modulo(fonte) {
  return `data:text/javascript;base64,${Buffer.from(
    ts.transpileModule(fonte, {
      compilerOptions: {
        target: ts.ScriptTarget.ES2023,
        module: ts.ModuleKind.ESNext,
      },
    }).outputText,
  ).toString('base64')}`
}
const rede = modulo(
  await readFile(
    new URL('../src/services/redeApi.ts', import.meta.url),
    'utf8',
  ),
)
const fonte = (
  await readFile(
    new URL('../src/services/configuracaoApi.ts', import.meta.url),
    'utf8',
  )
).replace("'./redeApi'", JSON.stringify(rede))
const api = await import(modulo(fonte))
const campos = {
  ativa: true,
  estrategia: 'aleatoria',
  fracao: '0,58',
  inicio: '0',
  mecanismo: 'desativacao',
  reducao: '.5',
}

test('ausência de intervenção não envia parâmetros ocultos', () => {
  assert.equal(typeof api.prepararFormularioIntervencao, 'function')
  assert.equal(
    api.prepararFormularioIntervencao({ ...campos, ativa: false }),
    null,
  )
})

test('formulário não envia orçamento contraditório nem redução inaplicável', () => {
  assert.equal(typeof api.prepararFormularioIntervencao, 'function')
  assert.deepEqual(api.prepararFormularioIntervencao(campos), {
    estrategia: 'aleatoria',
    fracao: '0,58',
    inicio: '0',
    mecanismo: 'desativacao',
  })
  assert.equal(
    api.prepararFormularioIntervencao({ ...campos, mecanismo: 'reducao' })
      .reducao,
    '.5',
  )
})

test('intervenção, revisão e semente textual chegam ao backend', async () => {
  const anterior = globalThis.fetch
  let recebido
  globalThis.fetch = async (_url, opcoes) => {
    recebido = JSON.parse(opcoes.body)
    return Response.json({
      configuracao: { intervencao: { quantidade_isolados: 29 } },
    })
  }
  try {
    const resultado = await api.validarConfiguracao({
      intervencao: api.prepararFormularioIntervencao(campos),
      revisao_rede: '2',
      semente_isolamento: '900719925474099312345',
    })
    assert.equal(recebido.intervencao.fracao, '0,58')
    assert.equal(recebido.revisao_rede, '2')
    assert.equal(recebido.semente_isolamento, '900719925474099312345')
    assert.equal(resultado.configuracao.intervencao.quantidade_isolados, 29)
  } finally {
    globalThis.fetch = anterior
  }
})
