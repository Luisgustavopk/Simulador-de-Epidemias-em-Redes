import assert from 'node:assert/strict'
import test from 'node:test'
import { carregarConfiguracaoApi } from './carregarConfiguracaoApi.mjs'

const { validarComparacao, validarConfiguracao, executarComparacao, executarSimulacao } =
  await carregarConfiguracaoApi()

test('configuração conserva IDs e sementes textuais e inclui a revisão', async () => {
  const anterior = globalThis.fetch
  let recebido
  globalThis.fetch = async (caminho, opcoes) => {
    recebido = { caminho, ...opcoes }
    return Response.json({
      configuracao: { ids_infectados_iniciais: ['9007199254740993'] },
    })
  }
  try {
    await validarConfiguracao({
      semente_epidemia: '9007199254740993',
      ids_infectados_iniciais: ['9007199254740993'],
      revisao_rede: '7',
    })
    assert.equal(recebido.caminho, '/api/rede/configuracao')
    assert.equal(recebido.credentials, 'same-origin')
    const corpo = JSON.parse(recebido.body)
    assert.equal(corpo.semente_epidemia, '9007199254740993')
    assert.deepEqual(corpo.ids_infectados_iniciais, ['9007199254740993'])
    assert.equal(corpo.revisao_rede, '7')
  } finally {
    globalThis.fetch = anterior
  }
})

test('mensagens de validação por campo chegam ao consumidor', async () => {
  const anterior = globalThis.fetch
  globalThis.fetch = async () =>
    Response.json(
      { problemas: [{ campo: 'beta', mensagem: 'Corrija o intervalo.' }] },
      { status: 422 },
    )
  try {
    await assert.rejects(
      validarConfiguracao({}),
      (erro) => erro.problemas[0].campo === 'beta',
    )
  } finally {
    globalThis.fetch = anterior
  }
})

test('comparação envia a quantidade original do sorteio e a revisão', async () => {
  const anterior = globalThis.fetch
  globalThis.fetch = async (caminho, opcoes) => {
    assert.equal(caminho, '/api/rede/comparacao/validar')
    assert.equal(opcoes.credentials, 'same-origin')
    assert.deepEqual(JSON.parse(opcoes.body), {
      repeticoes: '2',
      configuracao: {
        modo_iniciais: 'sorteio',
        quantidade_infectados: '3',
        revisao_rede: '7',
        semente_epidemia: '9007199254740993',
      },
    })
    return Response.json({ execucao_disponivel: true })
  }
  try {
    const resultado = await validarComparacao('2', {
      modo_iniciais: 'sorteio',
      quantidade_infectados: '3',
      revisao_rede: '7',
      semente_epidemia: '9007199254740993',
    })
    assert.equal(resultado.execucao_disponivel, true)
  } finally {
    globalThis.fetch = anterior
  }
})

test('execução individual usa a rota do motor SIR', async () => {
  const anterior = globalThis.fetch
  globalThis.fetch = async (caminho, opcoes) => {
    assert.equal(caminho, '/api/rede/simulacao/executar')
    assert.equal(opcoes.method, 'POST')
    assert.deepEqual(JSON.parse(opcoes.body), { limite_passos: '20' })
    return Response.json({
      populacao: 3,
      metrica: {
        pico_infectados: 2,
        passo_pico: 1,
        pico_proporcional: 2 / 3,
        fracao_acumulada: 1,
        horizonte_observado: 2,
        duracao_extincao: 2,
      },
      historico: [
        {
          passo: 0,
          suscetiveis: 1,
          infectados: 2,
          recuperados: 0,
          isolados: 0,
        },
      ],
    })
  }
  try {
    const resultado = await executarSimulacao({ limite_passos: '20' })
    assert.equal(resultado.populacao, 3)
    assert.equal(resultado.historico[0].passo, 0)
  } finally {
    globalThis.fetch = anterior
  }
})

test('execução de comparação preserva lote e cenários separados', async () => {
  const anterior = globalThis.fetch
  globalThis.fetch = async (caminho, opcoes) => {
    assert.equal(caminho, '/api/rede/comparacao/executar')
    assert.equal(opcoes.method, 'POST')
    assert.deepEqual(JSON.parse(opcoes.body), {
      repeticoes: '3',
      configuracao: { revisao_rede: '4', semente_epidemia: '42' },
    })
    return Response.json({
      contexto_rede: 'rede-a',
      revisao_rede: 4,
      populacao: 10,
      execucoes: [
        { cenario: 'grau', repeticao: 1, historico: [{ passo: 0 }] },
        { cenario: 'aleatoria', repeticao: 1, historico: [{ passo: 0 }] },
      ],
      resumo: {},
    })
  }
  try {
    const lote = await executarComparacao('3', {
      revisao_rede: '4',
      semente_epidemia: '42',
    })
    assert.equal(lote.revisao_rede, 4)
    assert.deepEqual(lote.execucoes.map((item) => item.cenario), ['grau', 'aleatoria'])
  } finally {
    globalThis.fetch = anterior
  }
})
