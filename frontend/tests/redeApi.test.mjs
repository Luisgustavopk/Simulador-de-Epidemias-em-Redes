import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'
import ts from 'typescript'

// O cliente só importa tipos. Compilá-lo aqui permite usar node:test com o
// TypeScript já instalado, sem acrescentar um framework de testes ao projeto.
const fonte = await readFile(
  new URL('../src/services/redeApi.ts', import.meta.url),
  'utf8',
)
const { outputText } = ts.transpileModule(fonte, {
  compilerOptions: {
    target: ts.ScriptTarget.ES2023,
    module: ts.ModuleKind.ESNext,
  },
})
const { redeApi, ErroApi, problemasDoErro, redeDesatualizada } = await import(
  `data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`
)

function responder(contexto, dados, status = 200) {
  return contexto.mock.method(globalThis, 'fetch', async () =>
    Response.json(dados, { status }),
  )
}

test('consulta encaminha cookie de sessão e sinal de cancelamento', async (contexto) => {
  const dados = { revisao: 0, disponivel: false, confirmada: false }
  const fetch = responder(contexto, dados)
  const controlador = new AbortController()

  assert.deepEqual(await redeApi.inspecionar(controlador.signal), dados)
  const [url, opcoes] = fetch.mock.calls[0].arguments
  assert.equal(url, '/api/rede')
  assert.equal(opcoes.credentials, 'same-origin')
  assert.equal(opcoes.signal, controlador.signal)
})

test('geração mantém a semente textual e envia JSON', async (contexto) => {
  const fetch = responder(contexto, { revisao: 1 })
  const campos = {
    modelo: 'erdos_renyi',
    numero_individuos: '3',
    semente: '900719925474099312345',
    probabilidade_contato: '0,5',
    peso: '0,8',
  }
  await redeApi.gerar(campos)

  const [url, opcoes] = fetch.mock.calls[0].arguments
  assert.equal(url, '/api/rede/gerar')
  assert.equal(opcoes.method, 'POST')
  assert.equal(opcoes.headers['Content-Type'], 'application/json')
  assert.deepEqual(JSON.parse(opcoes.body), campos)
})

test('diagnóstico CSV conserva arquivo, linha e coluna', async (contexto) => {
  const problema = {
    campo: 'arquivo_contatos',
    mensagem: 'Peso inválido.',
    arquivo: 'rede.csv',
    linha: 3,
    coluna: 'peso',
  }
  responder(contexto, { problemas: [problema] }, 422)
  await assert.rejects(redeApi.inspecionar(), (erro) => {
    assert(erro instanceof ErroApi)
    assert.deepEqual(problemasDoErro(erro), [problema])
    assert.equal(redeDesatualizada(erro), false)
    return true
  })
})

for (const problemas of [[], [null, {}, { campo: 3, mensagem: false }]]) {
  test(`diagnóstico malformado não provoca lista vazia: ${JSON.stringify(problemas)}`, async (contexto) => {
    responder(contexto, { problemas }, 500)
    await assert.rejects(redeApi.inspecionar(), (erro) => {
      assert.equal(problemasDoErro(erro)[0].campo, 'conexao')
      assert(problemasDoErro(erro)[0].mensagem.length > 0)
      return true
    })
  })
}

test('itens inválidos não ocultam um diagnóstico utilizável', async (contexto) => {
  const problema = { campo: 'revisao', mensagem: 'Atualize a rede.' }
  responder(contexto, { problemas: [null, {}, problema] }, 409)
  await assert.rejects(redeApi.inspecionar(), (erro) => {
    assert.deepEqual(problemasDoErro(erro), [problema])
    assert.equal(redeDesatualizada(erro), true)
    return true
  })
})

test('resposta HTML do proxy recebe diagnóstico de conexão', async (contexto) => {
  contexto.mock.method(
    globalThis,
    'fetch',
    async () => new Response('<html>Erro</html>', { status: 502 }),
  )
  await assert.rejects(redeApi.inspecionar(), (erro) => {
    assert.equal(problemasDoErro(erro)[0].campo, 'conexao')
    return true
  })
})

test('falha de rede é distinguida de cancelamento voluntário', async (contexto) => {
  const fetch = contexto.mock.method(globalThis, 'fetch', async () => {
    throw new TypeError('Failed to fetch')
  })
  await assert.rejects(redeApi.inspecionar(), (erro) => {
    assert.equal(problemasDoErro(erro)[0].campo, 'conexao')
    return true
  })
  const cancelamento = new DOMException('Cancelado', 'AbortError')
  fetch.mock.mockImplementation(async () => {
    throw cancelamento
  })
  await assert.rejects(redeApi.inspecionar(), (erro) => erro === cancelamento)
})

test('consulta de indivíduo preserva um ID maior que o inteiro seguro do JavaScript', async (contexto) => {
  const fetch = responder(contexto, { id: '900719925474099312345' })
  await redeApi.individuo(3, '+900719925474099312345')
  const [caminho] = fetch.mock.calls[0].arguments
  const url = new URL(caminho, 'http://localhost')
  assert.equal(url.searchParams.get('id'), '+900719925474099312345')
  assert.equal(url.searchParams.get('revisao'), '3')
})

test('arquivo acima de 5 MiB é recusado antes do envio', async (contexto) => {
  const fetch = responder(contexto, {})
  const arquivo = new File([new Uint8Array(5 * 1024 * 1024 + 1)], 'grande.csv')
  await assert.rejects(redeApi.importar(arquivo, null, ','), (erro) => {
    assert.equal(problemasDoErro(erro)[0].campo, 'arquivos')
    return true
  })
  assert.equal(fetch.mock.callCount(), 0)
})

test('rede ausente requer sincronização e falha desconhecida tem mensagem utilizável', () => {
  assert(
    redeDesatualizada(
      new ErroApi([{ campo: 'rede', mensagem: 'Carregue novamente.' }]),
    ),
  )
  assert.equal(redeDesatualizada(new Error('Erro inesperado')), false)
  assert(problemasDoErro(new Error('Erro inesperado'))[0].mensagem)
  assert(problemasDoErro(new ErroApi([]))[0].mensagem)
})
