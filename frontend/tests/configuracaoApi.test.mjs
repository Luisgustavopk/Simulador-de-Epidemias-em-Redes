import assert from 'node:assert/strict'
import test from 'node:test'
import { carregarConfiguracaoApi } from './carregarConfiguracaoApi.mjs'

const { validarConfiguracao } = await carregarConfiguracaoApi()

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
