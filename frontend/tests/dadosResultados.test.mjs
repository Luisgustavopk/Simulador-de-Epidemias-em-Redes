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
const {
  agregarCurvas,
  csvMetricas,
  pacoteExportacao,
  maximoHistorico,
  caminhoEscalonado,
  dimensoesPng,
  escalaContagem,
  registroNoPasso,
} = await import(
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
      {
        cenario: 'grau',
        motivo_termino: 'extincao',
        historico: [registro(0, 1), registro(1, 0)],
      },
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
      {
        cenario: 'grau',
        motivo_termino: 'extincao',
        historico: [registro(0, 1), registro(1, 0)],
      },
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

test('curva censurada não é prolongada nem muda silenciosamente o denominador', () => {
  const comparacao = {
    execucoes: [
      {
        cenario: 'grau',
        motivo_termino: 'limite_passos',
        historico: [registro(0, 2), registro(1, 2)],
      },
      {
        cenario: 'grau',
        motivo_termino: 'limite_passos',
        historico: [registro(0, 4), registro(1, 3), registro(2, 2)],
      },
    ],
  }
  const copia = JSON.stringify(comparacao)
  const { registros } = agregarCurvas(comparacao)[0]
  assert.equal(registros.at(-1).passo, 1)
  assert.equal(registros.at(-1).infectados, 2.5)
  assert.equal(registros.at(-1).n, 2)
  assert.equal(JSON.stringify(comparacao), copia)
})

test('desvio de uma observação é ausente, enquanto desvio zero de duas é válido', () => {
  const comparacao = {
    execucoes: [
      { cenario: 'grau', historico: [registro(0, 2)] },
      { cenario: 'aleatoria', historico: [registro(0, 2)] },
      { cenario: 'aleatoria', historico: [registro(0, 2)] },
    ],
  }
  const grupos = agregarCurvas(comparacao)
  assert.equal(
    grupos.find((g) => g.cenario === 'grau').registros[0].desvios.infectados,
    null,
  )
  assert.equal(
    grupos.find((g) => g.cenario === 'aleatoria').registros[0].desvios
      .infectados,
    0,
  )
})

test('lacuna observada não é interpolada nem preenchida como um novo registro', () => {
  const comparacao = {
    execucoes: [
      {
        cenario: 'grau',
        motivo_termino: 'limite_passos',
        historico: [registro(0, 2), registro(2, 1)],
      },
    ],
  }
  assert.deepEqual(
    agregarCurvas(comparacao)[0].registros.map((r) => r.passo),
    [0],
  )
})

test('traçado discreto mantém o valor até o próximo instante sem diagonais', () => {
  assert.equal(
    caminhoEscalonado([
      [0, 4],
      [10, 2],
      [20, 3],
    ]),
    'M 0 4 H 10 V 2 H 20 V 3',
  )
  assert.equal(caminhoEscalonado([]), '')
  assert.equal(caminhoEscalonado([[0, 0]]), 'M 0 0')
})

test('PNG tem largura mínima de 2400 pixels e preserva a proporção', () => {
  assert.deepEqual(dimensoesPng(1000, 500), { largura: 2400, altura: 1200 })
  assert.deepEqual(dimensoesPng(3000, 1500), { largura: 3000, altura: 1500 })
  assert.throws(() => dimensoesPng(0, 500), /dimensões/i)
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

test('escala ajustada parte de zero e contém o maior valor sem ultrapassar a população', () => {
  assert.deepEqual(escalaContagem(21, 48, true), {
    maximo: 25,
    valores: [0, 5, 10, 15, 20, 25],
  })
  assert.deepEqual(escalaContagem(21, 48, false), {
    maximo: 48,
    valores: [0, 10, 20, 30, 40, 48],
  })
  assert.deepEqual(escalaContagem(0, 48, true), { maximo: 1, valores: [0, 1] })
  assert.deepEqual(escalaContagem(2.8, 3, true), {
    maximo: 3,
    valores: [0, 1, 2, 3],
  })
  assert.deepEqual(escalaContagem(0, 0, true), { maximo: 1, valores: [0, 1] })
  const escala = escalaContagem(133333, 200000, true)
  assert.ok(escala.maximo >= 133333 && escala.maximo <= 200000)
  assert.ok(escala.valores.length <= 7)
})

test('consulta por passo encontra somente registros observados sem interpolar lacunas ou prolongar o fim', () => {
  const historico = [registro(0, 3), registro(2, 1), registro(4, 0)]
  assert.equal(registroNoPasso(historico, 0), historico[0])
  assert.equal(registroNoPasso(historico, 2), historico[1])
  assert.equal(registroNoPasso(historico, 4), historico[2])
  assert.equal(registroNoPasso(historico, 1), null)
  assert.equal(registroNoPasso(historico, 5), null)
  assert.equal(registroNoPasso([], 0), null)
})
