// Execute na raiz: node scripts/verificar_base_escola_interface.mjs
// Usa Chrome, Vite e a API reais, com processos e perfil temporários próprios.
import assert from 'node:assert/strict'
import { spawn, execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { once } from 'node:events'
import { mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import { tmpdir } from 'node:os'
import path from 'node:path'
import { pathToFileURL } from 'node:url'

const raiz = process.cwd()
const pasta = path.join(raiz, 'dados/dados/redes_reais/escola_suica_2024')
const evidencias = path.join(raiz, 'dados/dados/redes_reais/evidencias/interface-escola')
const perfil = await mkdtemp(path.join(tmpdir(), 'conferencia-escola-'))
const require = createRequire(path.join(raiz, 'frontend/package.json'))
const { createServer } = await import(pathToFileURL(require.resolve('vite')))
const erros = [], redeHttp = [], capturas = []
let api, vite, navegador, socket
await mkdir(evidencias, { recursive: true })

function aguardarSaida(fluxo, expressao) {
  return new Promise((resolve, reject) => {
    let texto = ''
    const limite = setTimeout(() => reject(new Error(texto)), 15000)
    fluxo.on('data', (parte) => {
      texto += parte.toString()
      const resultado = texto.match(expressao)
      if (resultado) { clearTimeout(limite); resolve(resultado[1]) }
    })
  })
}

try {
  api = spawn(path.join(raiz, '.venv/bin/python'), ['-u', '-m', 'simulador.api_local', '--porta', '0'], {
    cwd: raiz, env: { ...process.env, PYTHONPATH: path.join(raiz, 'src') },
    stdio: ['ignore', 'pipe', 'pipe'],
  })
  const porta = await aguardarSaida(api.stdout, /127\.0\.0\.1:(\d+)/)
  vite = await createServer({ root: path.join(raiz, 'frontend'), logLevel: 'silent',
    server: { host: '127.0.0.1', port: 0, proxy: { '/api': `http://127.0.0.1:${porta}` } } })
  await vite.listen()
  navegador = spawn('/usr/bin/google-chrome', [
    '--headless', '--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu',
    '--remote-debugging-port=0', `--user-data-dir=${perfil}`, 'about:blank',
  ], { stdio: ['ignore', 'ignore', 'pipe'] })
  const depuracao = await aguardarSaida(navegador.stderr, /DevTools listening on (ws:\/\/\S+)/)
  const alvos = await (await fetch(`http://${new URL(depuracao).host}/json/list`)).json()
  socket = new WebSocket(alvos.find((a) => a.type === 'page').webSocketDebuggerUrl)
  await once(socket, 'open')
  let id = 0
  const pendentes = new Map()
  socket.addEventListener('message', ({ data }) => {
    const mensagem = JSON.parse(data)
    if (mensagem.method === 'Runtime.exceptionThrown') erros.push(mensagem.params)
    if (mensagem.method === 'Network.responseReceived' && mensagem.params.response.url.includes('/api/')) {
      const { url, status } = mensagem.params.response
      redeHttp.push({ caminho: new URL(url).pathname + new URL(url).search, status })
    }
    if (mensagem.method === 'Network.requestWillBeSent' && mensagem.params.request.method === 'POST') {
      redeHttp.push({ caminho: new URL(mensagem.params.request.url).pathname, metodo: 'POST' })
    }
    if (pendentes.has(mensagem.id)) {
      pendentes.get(mensagem.id)(mensagem)
      pendentes.delete(mensagem.id)
    }
  })
  async function comando(method, params = {}) {
    const numero = ++id
    const resposta = new Promise((resolve, reject) => {
      const timeout = setTimeout(() => { pendentes.delete(numero); reject(new Error(`Timeout: ${method}`)) }, 15000)
      pendentes.set(numero, (r) => { clearTimeout(timeout); resolve(r) })
    })
    socket.send(JSON.stringify({ id: numero, method, params }))
    const resultado = await resposta
    assert.equal(resultado.error, undefined, JSON.stringify(resultado.error))
    return resultado.result
  }
  async function avaliar(expression) {
    const retorno = await comando('Runtime.evaluate', {
      expression, awaitPromise: true, returnByValue: true, userGesture: true,
    })
    assert.equal(retorno.exceptionDetails, undefined, JSON.stringify(retorno.exceptionDetails))
    return retorno.result.value
  }
  async function ate(expression) {
    const limite = Date.now() + 15000
    while (Date.now() < limite) {
      if (await avaliar(`Boolean(${expression})`)) return
      await new Promise((r) => setTimeout(r, 50))
    }
    throw new Error(`Condição não alcançada: ${expression}`)
  }
  async function clicar(seletor) {
    await avaliar(`(()=>{const e=document.querySelector(${JSON.stringify(seletor)});if(!e||e.disabled)throw Error('Controle indisponível');e.click()})()`)
    await avaliar('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
  }
  async function arquivo(seletor, nome) {
    const { root } = await comando('DOM.getDocument')
    const { nodeId } = await comando('DOM.querySelector', { nodeId: root.nodeId, selector: seletor })
    assert.notEqual(nodeId, 0)
    await comando('DOM.setFileInputFiles', { nodeId, files: [path.join(pasta, nome)] })
  }
  async function captura(nome, seletor = null) {
    await avaliar('scrollTo(0,0)')
    const clip = await avaliar(`(()=>{
      if(!${JSON.stringify(seletor)})return {x:0,y:0,width:innerWidth,height:document.documentElement.scrollHeight,scale:1};
      const e=document.querySelector(${JSON.stringify(seletor)}),r=e.getBoundingClientRect();
      const caixas=[r,...[...e.querySelectorAll('*')].map(n=>n.getBoundingClientRect()).filter(b=>b.width>1&&b.height>1)];
      const direita=Math.max(...caixas.map(b=>b.right)),base=Math.max(...caixas.map(b=>b.bottom));
      return {x:r.x,y:r.y+scrollY,width:Math.min(innerWidth-r.x,direita-r.x+32),height:base-r.y,scale:1};
    })()`)
    const { data } = await comando('Page.captureScreenshot', { format: 'png', clip, captureBeyondViewport: true })
    const bytes = Buffer.from(data, 'base64')
    await writeFile(path.join(evidencias, nome), bytes)
    capturas.push({ arquivo: nome, escopo: seletor ?? 'pagina-completa', area_css:clip, sha256: createHash('sha256').update(bytes).digest('hex') })
  }
  await comando('Page.enable')
  await comando('Runtime.enable')
  await comando('Network.enable')
  await comando('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1100, deviceScaleFactor: 1, mobile: false })
  await comando('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }] })
  await comando('Page.navigate', { url: `http://127.0.0.1:${vite.httpServer.address().port}/#rede` })
  await ate("document.querySelector('.connection-dot.online') && document.querySelector('.source-modes button:last-child')")
  await clicar('.source-modes button:last-child')
  await arquivo('#arquivo_contatos', 'contatos.csv')
  await arquivo('#arquivo_individuos', 'individuos.csv')
  await ate("document.querySelector('#arquivo_contatos-status').textContent.includes('contatos.csv') && document.querySelector('#arquivo_individuos-status').textContent.includes('individuos.csv')")
  await clicar('.network-source button.full-width')
  await ate("document.querySelector('.confirmation-bar strong')?.textContent.includes('Estrutura pronta') && document.querySelector('canvas.network-canvas')?.width>0")
  const inspecao = await avaliar("fetch('/api/rede').then(r=>r.json())")
  assert.equal(inspecao.resumo.numero_individuos, 67)
  assert.equal(inspecao.resumo.numero_contatos, 1325)
  assert.equal(inspecao.resumo.grau_maximo, 54)
  assert.equal(inspecao.resumo.numero_componentes, 1)
  assert.equal(inspecao.resumo.individuos_sem_contatos, 0)
  assert.equal(inspecao.resumo.grau_medio, 2650 / 67)
  const medidas = await avaliar("[...document.querySelectorAll('.network-stats dd')].map(e=>({texto:e.textContent,valor:e.title}))")
  assert.deepEqual(medidas.map(m=>Number(m.valor)), [67,1325,2650/67,54])
  await avaliar(`(()=>{const e=document.querySelector('#id-individuo');Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(e,'25');e.dispatchEvent(new Event('input',{bubbles:true}));})()`)
  await clicar('.node-search button')
  await ate("document.querySelector('.node-degree strong')?.textContent==='54'")
  const inspecaoNo = await avaliar("document.querySelector('.node-result').innerText")
  assert.match(inspecaoNo, /Suscetível \(S\)/)
  assert.match(inspecaoNo, /Não isolado/)
  async function conferirCanvas() {
    return avaliar(`(()=>{const c=document.querySelector('canvas.network-canvas'),d=c.getContext('2d').getImageData(0,0,c.width,c.height).data,cores=new Set();for(let i=0;i<d.length;i+=128)cores.add(d.slice(i,i+3).join(','));return {largura:c.width,altura:c.height,cores:cores.size,rotulo:c.getAttribute('aria-label')};})()`)
  }
  const vista3d = await conferirCanvas()
  assert.ok(vista3d.cores > 20)
  await captura('rede-escolar-3d.png', '.network-workbench')
  await captura('rede-escolar-medidas.png', '.network-analytics')
  await clicar('[aria-label="Visualização da rede"] button:first-child')
  await ate("document.querySelector('.graph-viewport').getAttribute('aria-label')==='Visualização da rede no mapa'")
  const mapa = await conferirCanvas()
  assert.ok(mapa.cores > 20)
  await captura('rede-escolar-mapa.png', '.network-workbench')
  await clicar('[aria-label="Dados a consultar"] button:last-child')
  await ate("document.querySelector('.network-records').textContent.includes('1.325 contatos')")
  await clicar('.confirmation-bar button')
  await ate("document.querySelector('.confirmation-bar').classList.contains('is-confirmed')")
  await captura('rede-escolar-confirmacao.png', '.confirmation-bar')
  await captura('rede-escolar-pagina-completa.png')
  const confirmada = await avaliar("fetch('/api/rede').then(r=>r.json())")
  assert.equal(confirmada.confirmada, true)
  const previa = await avaliar(`fetch('/api/rede/previa?revisao=${confirmada.revisao}').then(r=>r.json())`)
  assert.equal(previa.total_individuos, 67)
  assert.equal(previa.total_contatos, 1325)
  assert.equal(previa.individuos.length, 67)
  assert.equal(previa.contatos.length, 1200)
  assert.equal(previa.parcial, true)
  assert.equal(erros.length, 0)
  assert.ok(redeHttp.some(r=>r.metodo==='POST' && r.caminho.includes('importar')))
  assert.ok(redeHttp.some(r=>r.metodo==='POST' && r.caminho.includes('confirmar')))
  assert.ok(redeHttp.filter(r=>r.status).every(r=>r.status===200))
  assert.ok(!redeHttp.some(r=>r.caminho.includes('/executar')))
  assert.equal(await avaliar('document.documentElement.scrollWidth>innerWidth'), false)
  const hashEntradas = {}
  for (const nome of ['contatos.csv','individuos.csv'])
    hashEntradas[nome] = createHash('sha256').update(await readFile(path.join(pasta,nome))).digest('hex')
  await writeFile(path.join(evidencias,'verificacao.json'), JSON.stringify({
    conferido_em_utc:new Date().toISOString(), resultado:'aprovado',
    navegador:await comando('Browser.getVersion'),node:process.version,
    revisao_codigo:execFileSync('git',['rev-parse','HEAD'],{cwd:raiz,encoding:'utf8'}).trim(),inclui_alteracoes_locais:true,
    viewport:{largura:1440,altura:1100,escala:1},sha256_entradas:hashEntradas,
    medidas_exibidas:medidas,individuo_25:inspecaoNo,vista3d,mapa,
    previa:{individuos:previa.individuos.length,contatos:previa.contatos.length,total_contatos:previa.total_contatos,parcial:previa.parcial},
    rede_confirmada:confirmada,requisicoes:redeHttp,capturas,erros_javascript:erros,
    ajuste_necessario:false,epidemias_executadas:false,inspecao_visual_concluida:false,
  },null,2)+'\n')
  console.log('Importação e confirmação: 67 indivíduos / 1.325 contatos. Mapa, 3D, medidas e inspeção aprovados; prévia parcial de 1.200 contatos.')
} catch (erro) {
  console.error(erro)
  process.exitCode=1
} finally {
  socket?.close()
  navegador?.kill()
  await vite?.close()
  api?.kill()
  await rm(perfil,{recursive:true,force:true,maxRetries:5,retryDelay:100})
}
