import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'
import ts from 'typescript'

const fonte = await readFile(
  new URL('../src/features/resultados/dadosResultados.ts', import.meta.url),
  'utf8',
)
const { outputText } = ts.transpileModule(fonte, {
  compilerOptions: {
    target: ts.ScriptTarget.ES2023,
    module: ts.ModuleKind.ESNext,
  },
})
const { agregarCurvas, csvMetricas, pacoteExportacao, maximoHistorico } =
  await import(
    `data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`
  )
const registro = (passo, infectados) => ({
  passo,
  infectados,
  suscetiveis: 4 - infectados,
  recuperados: 0,
  isolados: 0,
})

test('máximos de históricos grandes não expandem argumentos nem alteram dados', () => {
  const historico = Array.from({ length: 200000 }, (_, passo) => ({
    passo,
    infectados: passo === 123456 ? 42 : 0,
  }))
  assert.equal(maximoHistorico(historico, 'passo'), 199999)
  assert.equal(maximoHistorico(historico, 'infectados'), 42)
  assert.equal(maximoHistorico([], 'passo'), 0)
  assert.equal(historico[123456].infectados, 42)
})

test('médias usam repetições do mesmo cenário e desvio amostral', () => {
  const comparacao = {
    execucoes: [
      { cenario: 'grau', historico: [registro(0, 1), registro(1, 0)] },
      { cenario: 'grau', historico: [registro(0, 3), registro(1, 2)] },
      { cenario: 'aleatoria', historico: [registro(0, 4), registro(1, 4)] },
    ],
  }
  const grupos = agregarCurvas(comparacao)
  const grau = grupos.find((grupo) => grupo.cenario === 'grau')
  assert.equal(grau.registros[0].infectados, 2)
  assert.equal(grau.registros[0].desvios.infectados, Math.sqrt(2))
  assert.equal(
    grupos.find((grupo) => grupo.cenario === 'aleatoria').registros[0]
      .infectados,
    4,
  )
})

test('extinções mantêm estado final no horizonte comum sem alterar históricos', () => {
  const comparacao = {
    execucoes: [
      { cenario: 'grau', historico: [registro(0, 1), registro(1, 0)] },
      {
        cenario: 'aleatoria',
        historico: [registro(0, 2), registro(1, 1), registro(2, 0)],
      },
    ],
  }
  const original = JSON.stringify(comparacao)
  const grau = agregarCurvas(comparacao).find(
    (grupo) => grupo.cenario === 'grau',
  )
  assert.equal(grau.registros.at(-1).passo, 2)
  assert.equal(grau.registros.at(-1).infectados, 0)
  assert.equal(JSON.stringify(comparacao), original)
})

test('CSV agregado exporta estatísticas e manifesto com IDs textuais', () => {
  const resultado = {
    revisao_rede: 3,
    manifesto: { ids: ['9007199254740993'], sementes: ['42'] },
    resumo: {
      grau: {
        metricas: {
          pico_infectados: {
            n: 2,
            ausentes: 0,
            media: 2.5,
            desvio_padrao: 0.5,
          },
        },
      },
    },
  }
  const csv = csvMetricas(resultado)
  assert.match(
    csv,
    /"cenario";"metrica";"n";"ausentes";"media";"desvio_padrao"/,
  )
  assert.match(csv, /"grau";"pico_infectados";"2";"0";"2.5";"0.5"/)
  assert.match(csv, /9007199254740993/)
  assert.equal(pacoteExportacao(resultado).resultado, resultado)
})
