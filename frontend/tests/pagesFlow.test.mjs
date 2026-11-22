import assert from 'node:assert/strict'
import { spawn } from 'node:child_process'
import {
  access,
  mkdir,
  mkdtemp,
  readdir,
  rm,
  writeFile,
} from 'node:fs/promises'
import { homedir, tmpdir } from 'node:os'
import path from 'node:path'
import { once } from 'node:events'
import { fileURLToPath } from 'node:url'
import test from 'node:test'
import { createServer } from 'vite'

const frontend = fileURLToPath(new URL('..', import.meta.url))
const projeto = path.dirname(frontend)
async function localizarChrome() {
  const candidatos = [
    process.env.CHROME_BIN,
    '/usr/bin/chromium',
    '/usr/bin/google-chrome',
  ]
  const cache = path.join(homedir(), '.cache/ms-playwright')
  for (const pasta of await readdir(cache).catch(() => []))
    candidatos.push(path.join(cache, pasta, 'chrome-linux64/chrome'))
  for (const candidato of candidatos.filter(Boolean)) {
    try {
      await access(candidato)
      return candidato
    } catch {
      continue
    }
  }
}
const chrome = await localizarChrome()
const aguardarSaida = (fluxo, expressao) =>
  new Promise((resolve, reject) => {
    let texto = ''
    const limite = setTimeout(
      () => reject(new Error(`Tempo esgotado: ${texto}`)),
      15000,
    )
    fluxo.on('data', (bloco) => {
      texto += bloco.toString()
      const encontrado = texto.match(expressao)
      if (encontrado) {
        clearTimeout(limite)
        resolve(encontrado[1])
      }
    })
  })

test(
  'fluxos reais de execução, gráficos e exportação',
  {
    skip: !chrome ? 'Defina CHROME_BIN para executar o navegador.' : false,
    timeout: 60000,
  },
  async (contexto) => {
    const perfil = await mkdtemp(path.join(tmpdir(), 'observatorio-test-'))
    const api = spawn(
      process.env.PYTHON_BIN ?? path.join(projeto, '.venv/bin/python'),
      ['-u', '-m', 'simulador.api_local', '--porta', '0'],
      {
        cwd: projeto,
        env: { ...process.env, PYTHONPATH: path.join(projeto, 'src') },
        stdio: ['ignore', 'pipe', 'pipe'],
      },
    )
    let vite, navegador, socket
    contexto.after(async () => {
      socket?.close()
      navegador?.kill()
      await vite?.close()
      api.kill()
      await rm(perfil, {
        recursive: true,
        force: true,
        maxRetries: 5,
        retryDelay: 100,
      })
    })
    const porta = await aguardarSaida(api.stdout, /127\.0\.0\.1:(\d+)/)
    vite = await createServer({
      root: frontend,
      logLevel: 'silent',
      server: {
        host: '127.0.0.1',
        port: 0,
        proxy: { '/api': `http://127.0.0.1:${porta}` },
      },
    })
    await vite.listen()
    navegador = spawn(
      chrome,
      [
        '--headless',
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--remote-debugging-port=0',
        `--user-data-dir=${perfil}`,
        'about:blank',
      ],
      { stdio: ['ignore', 'ignore', 'pipe'] },
    )
    const depuracao = await aguardarSaida(
      navegador.stderr,
      /DevTools listening on (ws:\/\/[^\s]+)/,
    )
    const alvos = await (
      await fetch(`http://${new URL(depuracao).host}/json/list`)
    ).json()
    socket = new WebSocket(
      alvos.find((alvo) => alvo.type === 'page').webSocketDebuggerUrl,
    )
    await once(socket, 'open')
    let contador = 0
    const pendentes = new Map()
    socket.addEventListener('message', (evento) => {
      const mensagem = JSON.parse(evento.data)
      if (pendentes.has(mensagem.id)) {
        pendentes.get(mensagem.id)(mensagem)
        pendentes.delete(mensagem.id)
      }
    })
    async function comando(method, params = {}) {
      const id = ++contador
      const resposta = new Promise((resolve) => pendentes.set(id, resolve))
      socket.send(JSON.stringify({ id, method, params }))
      const mensagem = await resposta
      assert.equal(mensagem.error, undefined)
      return mensagem.result
    }
    async function avaliar(expression) {
      const resposta = await comando('Runtime.evaluate', {
        expression,
        awaitPromise: true,
        returnByValue: true,
      })
      assert.equal(
        resposta.exceptionDetails,
        undefined,
        JSON.stringify(resposta.exceptionDetails),
      )
      return resposta.result.value
    }
    async function ate(expression) {
      const limite = Date.now() + 10000
      while (Date.now() < limite) {
        if (await avaliar(expression)) return
        await new Promise((resolve) => setTimeout(resolve, 30))
      }
      assert.fail(`Condição não alcançada: ${expression}`)
    }
    async function recarregar() {
      await comando('Page.enable')
      let aoCarregar, limite
      const carregamento = new Promise((resolve, reject) => {
        aoCarregar = (evento) => {
          if (JSON.parse(evento.data).method === 'Page.loadEventFired')
            resolve()
        }
        socket.addEventListener('message', aoCarregar)
        limite = setTimeout(
          () => reject(new Error('A página não concluiu a recarga.')),
          15000,
        )
      })
      try {
        await comando('Page.reload')
        await carregamento
      } finally {
        clearTimeout(limite)
        socket.removeEventListener('message', aoCarregar)
      }
    }
    async function capturarArea(nome, seletor = '.simulation-summary') {
      if (!process.env.CAPTURAS_DIR) return
      await mkdir(process.env.CAPTURAS_DIR, { recursive: true })
      const area = await avaliar(
        `(()=>{const area=document.querySelector(${JSON.stringify(seletor)}).getBoundingClientRect();return {x:area.x+scrollX,y:area.y+scrollY,width:area.width,height:area.height,scale:1}})()`,
      )
      const captura = await comando('Page.captureScreenshot', {
        format: 'png',
        clip: area,
        captureBeyondViewport: true,
      })
      await writeFile(
        path.join(process.env.CAPTURAS_DIR, `${nome}.png`),
        Buffer.from(captura.data, 'base64'),
      )
    }
    await comando('Page.navigate', {
      url: `http://127.0.0.1:${vite.httpServer.address().port}/#simulacao`,
    })
    await ate("!!document.querySelector('.experiment-actions')")
    await contexto.test(
      'contagens ficam indisponíveis sem histórico real',
      async () => {
        assert.deepEqual(
          await avaliar(
            "[...document.querySelectorAll('.sir-population-stats dd')].map(elemento=>elemento.textContent)",
          ),
          ['—', '—', '—', '—'],
        )
        assert.deepEqual(
          await avaliar(
            "[...document.querySelectorAll('.simulation-workspace .sir-model small')].map(elemento=>elemento.textContent)",
          ),
          ['—', '—', '—'],
        )
        assert.equal(
          await avaliar(
            "!!document.querySelector('.population-proportion, .isolation-proportion, .simulation-progress, .sir-network-legend')",
          ),
          false,
        )
        assert.match(
          await avaliar(
            "document.querySelector('.simulation-empty').textContent",
          ),
          /Nenhuma simulação executada/,
        )
        assert.match(
          await avaliar(
            "document.querySelector('.simulation-summary').textContent",
          ),
          /Nenhuma rede carregada/,
        )
      },
    )
    await contexto.test(
      'execução usa rótulos de domínio sem códigos de requisitos',
      async () => {
        assert.doesNotMatch(
          await avaliar(
            "document.querySelector('.simulation-controls').textContent",
          ),
          /RF06|RF07/,
        )
      },
    )
    await contexto.test(
      'sidebar recolhida centraliza etapas, preserva nomes e navega por teclado',
      async () => {
        try {
          await comando('Emulation.setDeviceMetricsOverride', {
            width: 1365,
            height: 1000,
            deviceScaleFactor: 1,
            mobile: false,
          })
          const larguraExpandida = await avaliar(
            "document.querySelector('.work-sheet').getBoundingClientRect().width",
          )
          await avaliar("document.querySelector('.nav-toggle').click()")
          await ate(
            "document.querySelector('.nav-toggle').getAttribute('aria-expanded')==='false'",
          )
          assert.ok(
            (await avaliar(
              "document.querySelector('.work-sheet').getBoundingClientRect().width",
            )) > larguraExpandida,
          )
          for (const [largura, tema] of [
            [1365, 'light'],
            [820, 'light'],
            [1365, 'dark'],
          ]) {
            await comando('Emulation.setDeviceMetricsOverride', {
              width: largura,
              height: 1000,
              deviceScaleFactor: 1,
              mobile: false,
            })
            await avaliar(`document.documentElement.dataset.theme='${tema}'`)
            const centros = await avaliar(
              "(()=>{const barra=document.querySelector('.workflow-sidebar').getBoundingClientRect();const botao=document.querySelector('.nav-toggle').getBoundingClientRect();return {barra:barra.x+barra.width/2,botao:botao.x+botao.width/2,etapas:[...document.querySelectorAll('#workflow-nav li')].map(item=>{const numero=item.querySelector('.step-number').getBoundingClientRect();const linha=getComputedStyle(item,'::after');const retangulo=item.getBoundingClientRect();const link=item.querySelector('a');const alvo=link.getBoundingClientRect();return {centro:numero.x+numero.width/2,linha:retangulo.x+parseFloat(linha.left)+parseFloat(linha.width)/2,ultimo:item===item.parentElement.lastElementChild,nome:link.getAttribute('aria-label'),titulo:link.title,largura:alvo.width,altura:alvo.height}})}})()",
            )
            assert.ok(Math.abs(centros.botao - centros.barra) < 1)
            for (const etapa of centros.etapas) {
              assert.ok(Math.abs(etapa.centro - centros.barra) < 1)
              if (!etapa.ultimo)
                assert.ok(Math.abs(etapa.linha - etapa.centro) < 1)
              assert.ok(etapa.nome?.includes('Etapa'))
              assert.ok(etapa.titulo.length > 0)
              assert.ok(etapa.largura >= 44 && etapa.altura >= 44)
            }
            assert.equal(
              await avaliar(
                "document.querySelector('#workflow-nav a[href=\"#simulacao\"]').getAttribute('aria-current')",
              ),
              'step',
            )
            assert.ok(
              await avaliar(
                'document.documentElement.scrollWidth <= innerWidth',
              ),
            )
            await capturarArea(
              `sidebar-${largura}-${tema}`,
              '.workflow-sidebar',
            )
          }
          await comando('Emulation.setDeviceMetricsOverride', {
            width: 390,
            height: 1000,
            deviceScaleFactor: 1,
            mobile: true,
          })
          assert.equal(
            await avaliar(
              "getComputedStyle(document.querySelector('.nav-toggle')).display",
            ),
            'none',
          )
          const etapasMoveis = await avaliar(
            "[...document.querySelectorAll('#workflow-nav a')].map(link=>{const numero=link.querySelector('.step-number').getBoundingClientRect();const texto=link.querySelector('.step-copy');const area=texto.getBoundingClientRect();return {centroNumero:numero.x+numero.width/2,centroTexto:area.x+area.width/2,visivel:getComputedStyle(texto).display!=='none',altura:link.getBoundingClientRect().height}})",
          )
          for (const etapa of etapasMoveis) {
            assert.ok(etapa.visivel && etapa.altura >= 44)
            assert.ok(Math.abs(etapa.centroNumero - etapa.centroTexto) < 1)
          }
          assert.ok(
            await avaliar('document.documentElement.scrollWidth <= innerWidth'),
          )
          await capturarArea('sidebar-mobile-dark', '.workflow-sidebar')
          await comando('Emulation.setDeviceMetricsOverride', {
            width: 1365,
            height: 1000,
            deviceScaleFactor: 1,
            mobile: false,
          })
          await avaliar("document.querySelector('.nav-toggle').focus()")
          await comando('Input.dispatchKeyEvent', {
            type: 'keyDown',
            key: 'Enter',
            code: 'Enter',
            text: '\r',
            unmodifiedText: '\r',
            windowsVirtualKeyCode: 13,
          })
          await comando('Input.dispatchKeyEvent', {
            type: 'keyUp',
            key: 'Enter',
            code: 'Enter',
            windowsVirtualKeyCode: 13,
          })
          await ate(
            "document.querySelector('.nav-toggle').getAttribute('aria-expanded')==='true'",
          )
          await avaliar(
            "document.querySelector('.nav-toggle').click();document.querySelector('#workflow-nav a[href=\"#configuracao\"]').focus()",
          )
          await comando('Input.dispatchKeyEvent', {
            type: 'keyDown',
            key: 'Enter',
            code: 'Enter',
            text: '\r',
            unmodifiedText: '\r',
            windowsVirtualKeyCode: 13,
          })
          await comando('Input.dispatchKeyEvent', {
            type: 'keyUp',
            key: 'Enter',
            code: 'Enter',
            windowsVirtualKeyCode: 13,
          })
          await ate("!!document.querySelector('.configuration-page')")
          assert.equal(
            await avaliar(
              "document.querySelector('#workflow-nav a[href=\"#configuracao\"]').getAttribute('aria-current')",
            ),
            'step',
          )
          await avaliar("window.location.hash='#simulacao'")
          await ate("!!document.querySelector('.simulation-controls')")
        } finally {
          await avaliar(
            "document.documentElement.dataset.theme='light';if(document.querySelector('.nav-toggle')?.getAttribute('aria-expanded')==='false')document.querySelector('.nav-toggle').click()",
          )
          await comando('Emulation.setDeviceMetricsOverride', {
            width: 1365,
            height: 1000,
            deviceScaleFactor: 1,
            mobile: false,
          })
        }
      },
    )
    await contexto.test(
      'execução exige rede e configuração; reiniciar descarta resposta pendente',
      async () => {
        assert.equal(
          await avaliar(
            "document.querySelector('.experiment-actions .button-primary').disabled",
          ),
          true,
        )
        await avaliar(
          `(async()=>{const rede=await(await fetch('/api/rede/gerar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({modelo:'erdos_renyi',numero_individuos:'3',semente:'1',peso:'1',probabilidade_contato:'1'})})).json();await fetch('/api/rede/confirmar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({revisao:rede.revisao})});const formulario={beta:'1',gamma:'1',modo_peso:'intensidade',modo_iniciais:'ids',ids_infectados_iniciais:['0'],semente_epidemia:'42',semente_iniciais:'43',semente_isolamento:'44',limite_passos:'20',revisao_rede:String(rede.revisao),contexto_rede:rede.contexto_rede,intervencao:{estrategia:'grau',fracao:'0.5',inicio:'0',mecanismo:'desativacao'}};sessionStorage.setItem('observatorio-configuracao',JSON.stringify({repeticoes:'2',formulario}));})()`,
        )
        await recarregar()
        await ate(
          "!!document.querySelector('.experiment-actions .button-primary') && !document.querySelector('.experiment-actions .button-primary').disabled",
        )
        await avaliar(
          "[...document.querySelectorAll('.experiment-card')].find(botao=>botao.textContent.includes('Execução Única')).click()",
        )
        const resumo = await avaliar(
          "document.querySelector('.simulation-summary').textContent",
        )
        for (const esperado of [
          /Erdős–Rényi/,
          /1 · Confirmada/,
          /3 indivíduos · 3 contatos/,
          /β = 1 · γ = 1/,
          /20 passos/,
          /Por grau/,
          /1 de 3 pessoas/,
          /Desativação dos contatos/,
        ])
          assert.match(resumo, esperado)
        assert.deepEqual(
          await avaliar(
            "[...document.querySelectorAll('.sir-population-stats dd')].map(elemento=>elemento.textContent)",
          ),
          ['—', '—', '—', '—'],
        )
        await avaliar(
          `window.fetchOriginal=window.fetch;window.fetch=async(...parametros)=>{if(String(parametros[0]).includes('simulacao/executar'))await new Promise(resolve=>setTimeout(resolve,350));return window.fetchOriginal(...parametros)};document.querySelector('.experiment-actions .button-primary').click()`,
        )
        await ate(
          "document.querySelector('.experiment-actions .button-primary').textContent.includes('Consultando')",
        )
        assert.equal(
          await avaliar(
            "document.querySelector('.experiment-actions .button-secondary').disabled",
          ),
          true,
        )
        await avaliar("document.querySelector('.button-reset').click()")
        await avaliar('new Promise(resolve=>setTimeout(resolve,550))')
        assert.equal(
          await avaliar(
            "sessionStorage.getItem('observatorio-resultado-execucao')",
          ),
          null,
        )
        assert.match(
          await avaliar("document.querySelector('.run-status').textContent"),
          /Pausado/,
        )
        await avaliar(
          "window.fetch=window.fetchOriginal;document.querySelector('.experiment-actions .button-primary').click()",
        )
        await ate("!!sessionStorage.getItem('observatorio-resultado-execucao')")
        assert.deepEqual(
          await avaliar(
            "[...document.querySelectorAll('.sir-population-stats dd')].map(elemento=>elemento.textContent)",
          ),
          ['2', '1', '0', '1'],
        )
        assert.equal(
          await avaliar(
            "JSON.parse(sessionStorage.getItem('observatorio-resultado-execucao')).resultado.motivo_termino",
          ),
          'extincao',
        )
      },
    )
    await contexto.test(
      'SIR mantém 100% da população e isolamento usa indicador independente',
      async () => {
        await avaliar("document.querySelector('.button-pause').click()")
        assert.equal(
          await avaliar(
            "document.querySelector('.population-proportion').children.length",
          ),
          3,
        )
        const proporcoes = await avaliar(
          "[...document.querySelectorAll('.population-proportion span')].map(elemento=>parseFloat(elemento.style.width))",
        )
        assert.ok(
          Math.abs(proporcoes.reduce((soma, valor) => soma + valor, 0) - 100) <
            0.001,
        )
        assert.equal(
          await avaliar(
            "!!document.querySelector('.population-proportion .bar-isolado')",
          ),
          false,
        )
        assert.deepEqual(
          await avaliar(
            "(()=>{const indicador=document.querySelector('[role=meter][aria-label=\"Indivíduos em isolamento\"]');return [indicador.getAttribute('aria-valuenow'),indicador.getAttribute('aria-valuemax')]})()",
          ),
          ['1', '3'],
        )
        for (const [largura, tema] of [
          [390, 'light'],
          [820, 'light'],
          [1365, 'light'],
          [390, 'dark'],
        ]) {
          await comando('Emulation.setDeviceMetricsOverride', {
            width: largura,
            height: 1000,
            deviceScaleFactor: 1,
            mobile: largura === 390,
          })
          await avaliar(`document.documentElement.dataset.theme='${tema}'`)
          assert.ok(
            await avaliar('document.documentElement.scrollWidth <= innerWidth'),
          )
          const larguras = await avaliar(
            "(()=>{const barra=document.querySelector('.population-proportion');return {total:barra.getBoundingClientRect().width,segmentos:[...barra.children].reduce((soma,elemento)=>soma+elemento.getBoundingClientRect().width,0)}})()",
          )
          assert.ok(Math.abs(larguras.total - larguras.segmentos) < 0.1)
          await capturarArea(
            `distribuicao-${largura}-${tema}`,
            '.population-distribution',
          )
        }
        await avaliar("document.documentElement.dataset.theme='light'")
      },
    )
    await contexto.test(
      'resultado direto permite JSON e associa horizonte ao cenário',
      async () => {
        await avaliar(
          "sessionStorage.removeItem('observatorio-resultado-execucao');window.location.hash='#resultados'",
        )
        await ate("document.querySelectorAll('.comparison-mean').length===3")
        assert.equal(
          await avaliar(
            "[...document.querySelectorAll('.export-actions button')].find(botao=>botao.textContent.trim()==='JSON').disabled",
          ),
          false,
        )
        assert.match(
          await avaliar(
            "document.querySelector('.result-metrics').textContent",
          ),
          /registrado em t = 1/,
        )
      },
    )
    await contexto.test(
      'faixas são visíveis e acompanham os controles das séries',
      async () => {
        assert.notEqual(
          await avaliar(
            "getComputedStyle(document.querySelector('.band-infectados')).fill",
          ),
          'none',
        )
        assert.equal(
          await avaliar("document.querySelectorAll('.comparison-band').length"),
          3,
        )
        await avaliar(
          "[...document.querySelectorAll('.trajectory-legend button')].find(botao=>botao.textContent.includes('Infectados')).click()",
        )
        await ate("!document.querySelector('.band-infectados')")
        await avaliar(
          "[...document.querySelectorAll('.trajectory-legend button')].find(botao=>botao.textContent.includes('Infectados')).click()",
        )
      },
    )
    await contexto.test(
      'SVG e PNG preservam cores; CSV contém estatísticas reais',
      async () => {
        await avaliar(
          `window.arquivos=[];window.blobs=new Map();const criar=URL.createObjectURL;URL.createObjectURL=blob=>{const endereco=criar(blob);window.blobs.set(endereco,blob);return endereco};HTMLAnchorElement.prototype.click=function(){window.arquivos.push({nome:this.download,blob:window.blobs.get(this.href)})};[...document.querySelectorAll('.export-actions button')].forEach(botao=>botao.click())`,
        )
        await ate(
          "window.arquivos.some(arquivo=>arquivo.nome.endsWith('.png'))",
        )
        const svg = await avaliar(
          "window.arquivos.find(arquivo=>arquivo.nome.endsWith('.svg')).blob.text()",
        )
        assert.match(svg, /stroke="rgb\(/)
        assert.match(svg, /<metadata>/)
        assert.match(
          await avaliar(
            "window.arquivos.find(arquivo=>arquivo.nome.endsWith('metricas-agregadas.csv')).blob.text()",
          ),
          /"media";"desvio_padrao"/,
        )
        assert.ok(
          await avaliar(
            `(async()=>{const imagem=await createImageBitmap(window.arquivos.find(arquivo=>arquivo.nome.endsWith('.png')).blob);const canvas=document.createElement('canvas');canvas.width=imagem.width;canvas.height=imagem.height;const contexto=canvas.getContext('2d');contexto.drawImage(imagem,0,0);const pixels=contexto.getImageData(0,0,canvas.width,canvas.height).data;for(let indice=0;indice<pixels.length;indice+=4)if(pixels[indice+3]&&(pixels[indice]!==pixels[indice+1]||pixels[indice+1]!==pixels[indice+2]))return true;return false})()`,
          ),
        )
      },
    )
    await contexto.test(
      'seleção de execução anterior e layout móvel',
      async () => {
        await ate(
          "document.querySelectorAll('#resultado-anterior option').length >= 3",
        )
        await avaliar(
          "const seletor=document.querySelector('#resultado-anterior');seletor.value=seletor.options[1].value;seletor.dispatchEvent(new Event('change',{bubbles:true}))",
        )
        await ate("!document.querySelector('#execucao-principal')")
        assert.match(
          await avaliar(
            "document.querySelector('.result-metrics').textContent",
          ),
          /Execução única/,
        )
        await comando('Emulation.setDeviceMetricsOverride', {
          width: 390,
          height: 844,
          deviceScaleFactor: 1,
          mobile: true,
        })
        assert.ok(
          await avaliar('document.documentElement.scrollWidth <= innerWidth'),
        )
        await comando('Emulation.setDeviceMetricsOverride', {
          width: 1365,
          height: 900,
          deviceScaleFactor: 1,
          mobile: false,
        })
      },
    )
    await contexto.test(
      'histórico pagina por teclado, preserva CSV completo e reinicia ao trocar cenário',
      async () => {
        await avaliar(`(async()=>{
          const configuracao=JSON.parse(sessionStorage.getItem('observatorio-configuracao'));
          const formulario={...configuracao.formulario,beta:'0',gamma:'0',limite_passos:'123'};
          const resposta=await fetch('/api/rede/comparacao/executar',{
            method:'POST',headers:{'Content-Type':'application/json'},
            body:JSON.stringify({configuracao:formulario,repeticoes:'2'})
          });
          if(!resposta.ok)throw new Error(await resposta.text());
          const comparacao=await resposta.json();
          sessionStorage.setItem('observatorio-resultado-execucao',JSON.stringify({tipo:'comparacao',comparacao}));
        })()`)
        await recarregar()
        await ate(
          "document.querySelectorAll('table[aria-labelledby=history-title] tbody tr').length===50",
        )
        assert.equal(
          await avaliar(
            "document.querySelector('table[aria-labelledby=history-title] tbody td').textContent",
          ),
          '0',
        )
        assert.equal(
          await avaliar(
            'document.querySelector(\'[aria-label="Página anterior do histórico"]\').disabled',
          ),
          true,
        )
        await avaliar(
          "document.querySelector('section[aria-labelledby=history-title] .history-table-wrap').scrollTop=400;document.querySelector('[aria-label=\"Próxima página do histórico\"]').focus()",
        )
        await comando('Input.dispatchKeyEvent', {
          type: 'keyDown',
          key: 'Enter',
          code: 'Enter',
          text: '\r',
          unmodifiedText: '\r',
          windowsVirtualKeyCode: 13,
        })
        await comando('Input.dispatchKeyEvent', {
          type: 'keyUp',
          key: 'Enter',
          code: 'Enter',
          windowsVirtualKeyCode: 13,
        })
        await ate(
          "document.querySelector('table[aria-labelledby=history-title] tbody td').textContent==='50'",
        )
        assert.equal(
          await avaliar(
            "document.querySelector('section[aria-labelledby=history-title] .history-table-wrap').scrollTop",
          ),
          0,
        )
        await avaliar(
          'document.querySelector(\'[aria-label="Última página do histórico"]\').click()',
        )
        await ate(
          "document.querySelectorAll('table[aria-labelledby=history-title] tbody tr').length===24",
        )
        assert.equal(
          await avaliar(
            'document.querySelector(\'[aria-label="Próxima página do histórico"]\').disabled',
          ),
          true,
        )
        assert.match(
          await avaliar(
            "document.querySelector('.history-pagination [role=status]').textContent",
          ),
          /101–124.*Página 3 de 3/,
        )
        const csv = await avaliar(`(async()=>{
          let arquivo;
          const criar=URL.createObjectURL;
          const clicar=HTMLAnchorElement.prototype.click;
          URL.createObjectURL=blob=>{arquivo=blob;return criar(blob)};
          HTMLAnchorElement.prototype.click=function(){};
          document.querySelector('.export-button').click();
          URL.createObjectURL=criar;
          HTMLAnchorElement.prototype.click=clicar;
          return arquivo.text();
        })()`)
        assert.equal(csv.split('\n').length, 125)
        for (const largura of [390, 820, 1365]) {
          await comando('Emulation.setDeviceMetricsOverride', {
            width: largura,
            height: 900,
            deviceScaleFactor: 1,
            mobile: largura === 390,
          })
          assert.ok(
            await avaliar('document.documentElement.scrollWidth <= innerWidth'),
          )
        }
        await avaliar(
          "const seletor=document.querySelector('#execucao-principal');seletor.value='sem_intervencao-1';seletor.dispatchEvent(new Event('change',{bubbles:true}))",
        )
        await ate(
          "document.querySelector('table[aria-labelledby=history-title] tbody td').textContent==='0'",
        )
        assert.equal(
          await avaliar(
            "document.querySelectorAll('table[aria-labelledby=history-title] tbody tr').length",
          ),
          50,
        )
      },
    )
    await contexto.test(
      'filtros abrem médias de infectados sem sobrepor as repetições',
      async () => {
        await avaliar(`(async()=>{
          const rede=await(await fetch('/api/rede/gerar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({modelo:'barabasi_albert',numero_individuos:'60',contatos_por_novo_individuo:'2',semente:'42',peso:'1'})})).json();
          await fetch('/api/rede/confirmar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({revisao:rede.revisao})});
          const formulario={beta:'0.05',gamma:'0.10',modo_peso:'intensidade',modo_iniciais:'sorteio',quantidade_infectados:'3',semente_epidemia:'42',semente_iniciais:'43',semente_isolamento:'44',limite_passos:'120',revisao_rede:String(rede.revisao),contexto_rede:rede.contexto_rede,intervencao:{estrategia:'grau',fracao:'0.2',inicio:'3',mecanismo:'desativacao'}};
          const resposta=await fetch('/api/rede/comparacao/executar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({configuracao:formulario,repeticoes:'5'})});
          if(!resposta.ok)throw new Error(await resposta.text());
          const comparacao=await resposta.json();
          sessionStorage.setItem('observatorio-resultado-execucao',JSON.stringify({tipo:'comparacao',comparacao}));
          sessionStorage.setItem('observatorio-configuracao',JSON.stringify({repeticoes:'5',formulario}));
        })()`)
        await recarregar()
        await ate("document.querySelectorAll('.comparison-mean').length===3")
        assert.equal(
          await avaliar("document.querySelectorAll('[data-repeticao]').length"),
          0,
        )
        assert.equal(
          await avaliar(
            "document.querySelectorAll('.comparison-mean .comparison-i').length",
          ),
          3,
        )
        assert.equal(
          await avaliar(
            "document.querySelectorAll('.comparison-mean .comparison-s, .comparison-mean .comparison-r, .comparison-mean .comparison-q').length",
          ),
          0,
        )
        assert.equal(
          await avaliar("document.querySelectorAll('.comparison-key').length"),
          0,
        )
        assert.match(
          await avaliar(
            "document.querySelector('.trajectory-summary').textContent",
          ),
          /Médias de 5 repetições/,
        )
        await capturarArea(
          'resultados-filtros-medias-desktop',
          '.trajectory-panel',
        )
        await avaliar(
          "window.metricasAntesDosFiltros=document.querySelector('.result-metrics').textContent",
        )
      },
    )
    await contexto.test(
      'cenário e repetição do gráfico não mudam o painel nem os dados originais',
      async () => {
        await avaliar(`for(const botao of document.querySelectorAll('.trajectory-scenarios button'))if(botao.textContent.trim()!=='Por grau')botao.click();
          const modo=document.querySelector('#grafico-modo');modo.value='repeticao';modo.dispatchEvent(new Event('change',{bubbles:true}));`)
        await ate("!!document.querySelector('#grafico-repeticao')")
        await avaliar(
          "const repeticao=document.querySelector('#grafico-repeticao');repeticao.value='5';repeticao.dispatchEvent(new Event('change',{bubbles:true}))",
        )
        await ate(
          'document.querySelectorAll(\'[data-repeticao="5"]\').length===1',
        )
        assert.equal(
          await avaliar(
            "document.querySelectorAll('.comparison-series').length",
          ),
          1,
        )
        assert.equal(
          await avaliar(
            "document.querySelectorAll('.comparison-mean, .comparison-band').length",
          ),
          0,
        )
        assert.match(
          await avaliar(
            "document.querySelector('.comparison-series title').textContent",
          ),
          /Por grau.*repetição 5/,
        )
        assert.equal(
          await avaliar(
            "document.querySelector('.result-metrics').textContent === window.metricasAntesDosFiltros",
          ),
          true,
        )
        assert.equal(
          await avaliar(
            "JSON.parse(sessionStorage.getItem('observatorio-resultado-execucao')).comparacao.execucoes.length",
          ),
          15,
        )
        assert.equal(
          await avaliar("document.querySelector('#execucao-principal').value"),
          'grau-1',
        )
      },
    )
    await contexto.test(
      'intervalo recorta curvas e eixos; SVG, PNG e JSON conservam o escopo',
      async () => {
        await avaliar(
          `const alterar=(id,valor)=>{const campo=document.getElementById(id);Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(campo,valor);campo.dispatchEvent(new Event('input',{bubbles:true}))};alterar('grafico-fim','10');document.querySelector('.trajectory-apply').click();`,
        )
        await ate(
          "document.querySelector('#grafico-fim').value==='10' && document.querySelector('.trajectory-summary').textContent.includes('a 10')",
        )
        await avaliar(
          `{const campo=document.getElementById('grafico-inicio');Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(campo,'3');campo.dispatchEvent(new Event('input',{bubbles:true}));}`,
        )
        await avaliar("document.querySelector('.trajectory-apply').click()")
        await ate(
          "document.querySelector('.trajectory-summary').textContent.includes('passos 3 a 10')",
        )
        assert.deepEqual(
          await avaliar(
            "(()=>{const marcas=[...document.querySelectorAll('.chart-step')].map(item=>Number(item.textContent));return [marcas[0],marcas.at(-1)]})()",
          ),
          [3, 10],
        )
        assert.equal(
          await avaliar(
            "document.querySelector('.comparison-series path').getAttribute('d').split(' ').filter(parte=>parte==='M'||parte==='L').length",
          ),
          8,
        )
        await avaliar(
          `window.arquivos=[];window.blobs=new Map();const criar=URL.createObjectURL;URL.createObjectURL=blob=>{const endereco=criar(blob);window.blobs.set(endereco,blob);return endereco};HTMLAnchorElement.prototype.click=function(){window.arquivos.push({nome:this.download,blob:window.blobs.get(this.href)})};for(const botao of document.querySelectorAll('.export-actions button'))botao.click();`,
        )
        await ate("window.arquivos.some(item=>item.nome.endsWith('.png'))")
        const exportacao = await avaliar(`(async()=>{
          const svg=new DOMParser().parseFromString(await window.arquivos.find(item=>item.nome.endsWith('.svg')).blob.text(),'image/svg+xml');
          const json=JSON.parse(await window.arquivos.find(item=>item.nome.endsWith('.json')).blob.text());
          const png=await createImageBitmap(window.arquivos.find(item=>item.nome.endsWith('.png')).blob);
          return {escopo:svg.documentElement.getAttribute('aria-label'),grupos:svg.querySelectorAll('[data-repeticao="5"]').length,metadados:JSON.parse(svg.querySelector('metadata').textContent).visualizacao.filtros,visualizacao:json.visualizacao.filtros_grafico,execucoes:json.resultado.execucoes.length,alturaPng:png.height};
        })()`)
        assert.match(exportacao.escopo, /passos 3 a 10/)
        assert.equal(exportacao.grupos, 1)
        assert.equal(exportacao.metadados.repeticao, 5)
        assert.equal(exportacao.visualizacao.inicio, 3)
        assert.equal(exportacao.visualizacao.fim, 10)
        assert.equal(exportacao.execucoes, 15)
        assert.equal(exportacao.alturaPng, 904)
        await avaliar(
          `{const campo=document.getElementById('grafico-fim');Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(campo,'999');campo.dispatchEvent(new Event('input',{bubbles:true}));}`,
        )
        await avaliar("document.querySelector('.trajectory-apply').click()")
        await ate("!!document.querySelector('#grafico-intervalo-erro')")
        assert.equal(
          await avaliar(
            "[...document.querySelectorAll('.chart-step')].at(-1).textContent",
          ),
          '10',
        )
        assert.equal(
          await avaliar(
            "document.querySelector('#grafico-fim').getAttribute('aria-invalid')",
          ),
          'true',
        )
        await avaliar(
          `{const campo=document.getElementById('grafico-fim');Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(campo,'10');campo.dispatchEvent(new Event('input',{bubbles:true}));campo.focus();}`,
        )
        await comando('Input.dispatchKeyEvent', {
          type: 'keyDown',
          key: 'Enter',
          code: 'Enter',
          text: '\r',
          unmodifiedText: '\r',
          windowsVirtualKeyCode: 13,
        })
        await comando('Input.dispatchKeyEvent', {
          type: 'keyUp',
          key: 'Enter',
          code: 'Enter',
          windowsVirtualKeyCode: 13,
        })
        await ate("!document.querySelector('#grafico-intervalo-erro')")
        assert.equal(await avaliar('document.activeElement.id'), 'grafico-fim')
        await capturarArea('resultados-filtros-repeticao', '.trajectory-panel')
      },
    )
    await contexto.test(
      'filtros têm estados vazios, passo único e restauração por teclado',
      async () => {
        await avaliar(
          `{const campo=document.getElementById('grafico-inicio');Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(campo,'0');campo.dispatchEvent(new Event('input',{bubbles:true}));}`,
        )
        await avaliar(
          `{const campo=document.getElementById('grafico-fim');Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(campo,'0');campo.dispatchEvent(new Event('input',{bubbles:true}));}`,
        )
        await avaliar("document.querySelector('.trajectory-apply').click()")
        await ate(
          "document.querySelectorAll('.comparison-series circle').length===1",
        )
        assert.equal(
          await avaliar("document.querySelectorAll('.chart-step').length"),
          1,
        )
        await avaliar(
          "document.querySelector('.trajectory-legend button[aria-pressed=true]').click()",
        )
        await ate("!!document.querySelector('.chart-empty')")
        assert.match(
          await avaliar("document.querySelector('.chart-empty').textContent"),
          /Selecione pelo menos um estado/,
        )
        assert.equal(
          await avaliar(
            "[...document.querySelectorAll('.trajectory-actions .export-actions button')].every(botao=>botao.disabled)",
          ),
          true,
        )
        await avaliar("document.querySelector('.trajectory-reset').focus()")
        await comando('Input.dispatchKeyEvent', {
          type: 'keyDown',
          key: 'Enter',
          code: 'Enter',
          text: '\r',
          unmodifiedText: '\r',
          windowsVirtualKeyCode: 13,
        })
        await comando('Input.dispatchKeyEvent', {
          type: 'keyUp',
          key: 'Enter',
          code: 'Enter',
          windowsVirtualKeyCode: 13,
        })
        await ate("document.querySelectorAll('.comparison-mean').length===3")
        assert.equal(
          await avaliar("document.querySelector('#grafico-inicio').value"),
          '0',
        )
        await avaliar(
          "for(const botao of document.querySelectorAll('.trajectory-scenarios button'))botao.click()",
        )
        await ate("!!document.querySelector('.chart-empty')")
        assert.match(
          await avaliar("document.querySelector('.chart-empty').textContent"),
          /Selecione pelo menos um cenário/,
        )
        await avaliar(
          "document.querySelector('.trajectory-reset').click();document.querySelector('.trajectory-deviation input').click()",
        )
        await ate("document.querySelectorAll('.comparison-band').length===0")
        await avaliar(
          "{const modo=document.querySelector('#grafico-modo');modo.value='todas';modo.dispatchEvent(new Event('change',{bubbles:true}))}",
        )
        await ate("document.querySelectorAll('[data-repeticao]').length===15")
        await avaliar("document.querySelector('.trajectory-reset').click()")
        for (const largura of [390, 820, 1365]) {
          await comando('Emulation.setDeviceMetricsOverride', {
            width: largura,
            height: 1000,
            deviceScaleFactor: 1,
            mobile: largura === 390,
          })
          for (const tema of ['light', 'dark']) {
            await avaliar(`document.documentElement.dataset.theme='${tema}'`)
            await avaliar(
              'Promise.all(document.getAnimations().filter(animacao=>animacao.effect?.getComputedTiming().iterations!==Infinity).map(animacao=>animacao.finished.catch(()=>{})))',
            )
            assert.ok(
              await avaliar(
                'document.documentElement.scrollWidth <= innerWidth',
              ),
            )
            await capturarArea(
              `resultados-filtros-${largura}-${tema}`,
              '.trajectory-panel',
            )
          }
        }
        await avaliar("document.documentElement.dataset.theme='light'")
      },
    )
    await contexto.test(
      'nova revisão invalida resultados anteriores',
      async () => {
        await avaliar(
          `(async()=>{const rede=await(await fetch('/api/rede/gerar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({modelo:'erdos_renyi',numero_individuos:'3',semente:'2',peso:'1',probabilidade_contato:'0'})})).json();await fetch('/api/rede/confirmar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({revisao:rede.revisao})});})()`,
        )
        await recarregar()
        await ate("!!document.querySelector('.results-warning')")
        assert.match(
          await avaliar(
            "document.querySelector('.results-warning').textContent",
          ),
          /invalidado/,
        )
        assert.equal(
          await avaliar(
            "document.querySelectorAll('.comparison-series').length",
          ),
          0,
        )
      },
    )
    await contexto.test(
      'IDs grandes permanecem texto após JSON.parse',
      async () => {
        const identificador = await avaliar(
          `(async()=>{const rede=await(await fetch('/api/rede/importar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({arquivo_contatos:{nome:'rede.csv',conteudo_base64:btoa('origem,destino,peso\\n9007199254740993,2,1\\n')},arquivo_individuos:{nome:'pessoas.csv',conteudo_base64:btoa('id\\n9007199254740993\\n2\\n')}})})).json();await fetch('/api/rede/confirmar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({revisao:rede.revisao})});const resultado=await(await fetch('/api/rede/simulacao/executar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({beta:'0',gamma:'1',modo_peso:'intensidade',modo_iniciais:'ids',ids_infectados_iniciais:['9007199254740993'],semente_epidemia:'42',semente_iniciais:'43',semente_isolamento:'44',limite_passos:'2',revisao_rede:String(rede.revisao),contexto_rede:rede.contexto_rede,intervencao:null})})).json();return resultado.manifesto.configuracao.ids_infectados_iniciais[0]})()`,
        )
        assert.equal(identificador, '9007199254740993')
      },
    )
    await contexto.test(
      'resumo reutiliza a validação da Tela 02 e preserva IDs e sementes grandes',
      async () => {
        await avaliar(
          "sessionStorage.removeItem('observatorio-resultado-execucao');window.location.hash='#configuracao'",
        )
        await ate("document.querySelector('#cfg-ids')?.matches(':enabled')")
        await avaliar(
          `for(const [identificador,valor] of [['cfg-ids','9007199254740993'],['cfg-semente_epidemia','900719925474099312345']]){const campo=document.getElementById(identificador);Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(campo,valor);campo.dispatchEvent(new Event('input',{bubbles:true}))}`,
        )
        await avaliar(
          "[...document.querySelectorAll('button')].find(botao=>botao.textContent.includes('Validar configuração')).click()",
        )
        await ate(
          "!!JSON.parse(sessionStorage.getItem('observatorio-configuracao'))?.validacao",
        )
        assert.doesNotMatch(
          await avaliar(
            "document.querySelector('.configuration-summary').textContent",
          ),
          /integrada posteriormente/,
        )
        await avaliar(
          `window.fetchAnterior=window.fetch;window.fetch=(...argumentos)=>{if(String(argumentos[0]).endsWith('/api/rede/configuracao'))throw new Error('O resumo deveria reutilizar a validação salva.');return window.fetchAnterior(...argumentos)};document.querySelector('.configuration-summary a[href="#simulacao"]').focus()`,
        )
        await comando('Input.dispatchKeyEvent', {
          type: 'keyDown',
          key: 'Enter',
          code: 'Enter',
          text: '\r',
          unmodifiedText: '\r',
          windowsVirtualKeyCode: 13,
        })
        await comando('Input.dispatchKeyEvent', {
          type: 'keyUp',
          key: 'Enter',
          code: 'Enter',
          windowsVirtualKeyCode: 13,
        })
        await ate(
          "!!document.querySelector('.simulation-summary') && !document.querySelector('.experiment-actions .button-primary').disabled",
        )
        const resumo = await avaliar(
          "document.querySelector('.simulation-summary').textContent",
        )
        assert.match(
          await avaliar(
            "document.querySelector('.experiment-card[aria-pressed=true]').textContent",
          ),
          /Execução Única/,
        )
        assert.match(resumo, /rede.csv/)
        assert.match(resumo, /9007199254740993/)
        assert.match(resumo, /900719925474099312345/)
        assert.match(resumo, /Sem intervenção/)
        assert.deepEqual(
          await avaliar(
            "[...document.querySelectorAll('.sir-population-stats dd')].map(elemento=>elemento.textContent)",
          ),
          ['—', '—', '—', '—'],
        )
        await avaliar('window.fetch=window.fetchAnterior')
        for (const [largura, tema] of [
          [1365, 'light'],
          [820, 'light'],
          [390, 'dark'],
        ]) {
          await comando('Emulation.setDeviceMetricsOverride', {
            width: largura,
            height: 1000,
            deviceScaleFactor: 1,
            mobile: largura === 390,
          })
          await avaliar(`document.documentElement.dataset.theme='${tema}'`)
          assert.ok(
            await avaliar('document.documentElement.scrollWidth <= innerWidth'),
          )
          await capturarArea(`resumo-${largura}-${tema}`)
        }
        await comando('Emulation.setDeviceMetricsOverride', {
          width: 1365,
          height: 900,
          deviceScaleFactor: 1,
          mobile: false,
        })
        await avaliar("document.documentElement.dataset.theme='light'")
      },
    )
    await contexto.test(
      'resumo resolve o sorteio no backend e identifica sementes base na comparação',
      async () => {
        await avaliar(`window.location.hash='#configuracao'`)
        await ate("!!document.querySelector('.configuration-page')")
        await avaliar(
          `(()=>{const anterior=JSON.parse(sessionStorage.getItem('observatorio-configuracao'));const formulario={...anterior.formulario,modo_iniciais:'sorteio',quantidade_infectados:'1',intervencao:{estrategia:'grau',fracao:'0.5',inicio:'1',mecanismo:'reducao',reducao:'0.25'}};delete formulario.ids_infectados_iniciais;sessionStorage.setItem('observatorio-configuracao',JSON.stringify({repeticoes:'2',formulario}));window.validacoesResumo=[];window.fetchAnterior=window.fetch;window.fetch=async(...argumentos)=>{const resposta=await window.fetchAnterior(...argumentos);if(String(argumentos[0]).endsWith('/api/rede/configuracao'))window.validacoesResumo.push(await resposta.clone().json());return resposta};window.location.hash='#simulacao'})()`,
        )
        await ate(
          "window.validacoesResumo.length===1 && !document.querySelector('.experiment-actions .button-primary').disabled",
        )
        const ids = await avaliar(
          'window.validacoesResumo[0].configuracao.ids_infectados_iniciais',
        )
        assert.equal(ids.length, 1)
        assert.match(
          await avaliar(
            "document.querySelector('.simulation-summary-identifiers').textContent",
          ),
          new RegExp(ids[0]),
        )
        await avaliar(
          "[...document.querySelectorAll('.experiment-card')].find(botao=>botao.textContent.includes('Repetições')).click()",
        )
        const resumo = await avaliar(
          "document.querySelector('.simulation-summary').textContent",
        )
        for (const esperado of [
          /2 repetições/,
          /Semente epidemiológica base/,
          /Sem intervenção · Aleatória · Por grau/,
          /1 de 2 pessoas/,
          /Passo 1/,
          /Redução da intensidade/,
          /redução 0.25/,
          /primeira repetição/,
          /sorteados novamente em cada repetição/,
        ])
          assert.match(resumo, esperado)
        assert.equal(await avaliar('window.validacoesResumo.length'), 1)
        await avaliar('window.fetch=window.fetchAnterior')
      },
    )
    await contexto.test(
      'falha na consulta do resumo não inventa contagens e permite nova tentativa',
      async () => {
        await avaliar("window.location.hash='#configuracao'")
        await ate("!!document.querySelector('.configuration-page')")
        await avaliar(
          `window.fetchAnterior=window.fetch;window.fetch=(...argumentos)=>{if(String(argumentos[0]).endsWith('/api/rede/configuracao'))return Promise.reject(new Error('Falha de conexão no resumo.'));return window.fetchAnterior(...argumentos)};window.location.hash='#simulacao'`,
        )
        await ate(
          "document.querySelector('.simulation-summary [role=alert]')?.textContent.includes('Não foi possível conectar à API local')",
        )
        assert.equal(
          await avaliar(
            "document.querySelector('.experiment-actions .button-primary').disabled",
          ),
          true,
        )
        assert.deepEqual(
          await avaliar(
            "[...document.querySelectorAll('.sir-population-stats dd')].map(elemento=>elemento.textContent)",
          ),
          ['—', '—', '—', '—'],
        )
        await avaliar(
          "window.fetch=window.fetchAnterior;document.querySelector('.simulation-summary-feedback button').focus()",
        )
        await comando('Input.dispatchKeyEvent', {
          type: 'keyDown',
          key: 'Enter',
          code: 'Enter',
          text: '\r',
          unmodifiedText: '\r',
          windowsVirtualKeyCode: 13,
        })
        await comando('Input.dispatchKeyEvent', {
          type: 'keyUp',
          key: 'Enter',
          code: 'Enter',
          windowsVirtualKeyCode: 13,
        })
        await ate(
          "!document.querySelector('.experiment-actions .button-primary').disabled",
        )
        assert.equal(
          await avaliar(
            "!!document.querySelector('.simulation-summary [role=alert]')",
          ),
          false,
        )
      },
    )
    await contexto.test(
      'ausência de infectados mostra zeros reais e reiniciar restaura o estado sem dados',
      async () => {
        await avaliar(
          `(()=>{const anterior=JSON.parse(sessionStorage.getItem('observatorio-configuracao'));const formulario={...anterior.formulario,modo_iniciais:'ids',ids_infectados_iniciais:[],intervencao:null,limite_passos:'5'};delete formulario.quantidade_infectados;sessionStorage.setItem('observatorio-configuracao',JSON.stringify({repeticoes:null,formulario}));sessionStorage.removeItem('observatorio-resultado-execucao')})()`,
        )
        await recarregar()
        await ate(
          "!!document.querySelector('.experiment-actions .button-primary') && !document.querySelector('.experiment-actions .button-primary').disabled",
        )
        await avaliar(
          "document.querySelector('.experiment-actions .button-secondary').click()",
        )
        await ate("document.querySelector('.stat-i').textContent==='0'")
        assert.deepEqual(
          await avaliar(
            "[...document.querySelectorAll('.sir-population-stats dd')].map(elemento=>elemento.textContent)",
          ),
          ['2', '0', '0', '0'],
        )
        assert.match(
          await avaliar(
            "document.querySelector('.simulation-outcome').textContent",
          ),
          /extinção da epidemia em t = 0/,
        )
        assert.match(
          await avaliar(
            "document.querySelector('.simulation-summary-identifiers').textContent",
          ),
          /Nenhum infectado inicial/,
        )
        assert.equal(
          await avaliar(
            "document.querySelector('[role=meter]').getAttribute('aria-valuenow')",
          ),
          '0',
        )
        assert.equal(
          await avaliar(
            "document.querySelector('.population-proportion .bar-s').style.width",
          ),
          '100%',
        )
        await avaliar("document.querySelector('.button-reset').click()")
        await ate("document.querySelector('.stat-i').textContent==='—'")
        assert.equal(
          await avaliar(
            "!!document.querySelector('.population-proportion, .isolation-proportion, .simulation-progress, .sir-network-legend')",
          ),
          false,
        )
      },
    )
    await contexto.test(
      'nova revisão não reaproveita o resumo epidemiológico da rede anterior',
      async () => {
        await avaliar(
          `(async()=>{const rede=await(await fetch('/api/rede/gerar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({modelo:'erdos_renyi',numero_individuos:'2',semente:'7',peso:'1',probabilidade_contato:'0'})})).json();await fetch('/api/rede/confirmar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({revisao:rede.revisao})})})()`,
        )
        await recarregar()
        await ate(
          "document.querySelector('.simulation-summary')?.textContent.includes('Erdős–Rényi')",
        )
        assert.equal(
          await avaliar(
            "document.querySelector('.experiment-actions .button-primary').disabled",
          ),
          true,
        )
        assert.equal(
          await avaliar(
            "!!document.querySelector('.simulation-summary-identifiers')",
          ),
          false,
        )
        assert.doesNotMatch(
          await avaliar(
            "document.querySelector('.simulation-summary').textContent",
          ),
          /900719925474099312345/,
        )
        assert.deepEqual(
          await avaliar(
            "[...document.querySelectorAll('.sir-population-stats dd')].map(elemento=>elemento.textContent)",
          ),
          ['—', '—', '—', '—'],
        )
      },
    )
    await contexto.test(
      'listas extensas de IDs continuam acessíveis por teclado',
      async () => {
        await avaliar(`(async()=>{
        const rede=await(await fetch('/api/rede/gerar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({modelo:'erdos_renyi',numero_individuos:'20',semente:'7',peso:'1',probabilidade_contato:'0'})})).json();
        await fetch('/api/rede/confirmar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({revisao:rede.revisao})});
        const anterior=JSON.parse(sessionStorage.getItem('observatorio-configuracao'));
        const formulario={...anterior.formulario,ids_infectados_iniciais:Array.from({length:20},(_,indice)=>String(indice)),revisao_rede:String(rede.revisao),contexto_rede:rede.contexto_rede};
        const validacao=await(await fetch('/api/rede/configuracao',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(formulario)})).json();
        sessionStorage.setItem('observatorio-configuracao',JSON.stringify({repeticoes:null,formulario,validacao}));
      })()`)
        await recarregar()
        await ate(
          "!!document.querySelector('.simulation-summary-identifiers summary')",
        )
        assert.equal(
          await avaliar(
            "document.querySelector('.simulation-summary details').open",
          ),
          false,
        )
        await avaliar(
          "document.querySelector('.simulation-summary summary').focus()",
        )
        await comando('Input.dispatchKeyEvent', {
          type: 'keyDown',
          key: 'Enter',
          code: 'Enter',
          text: '\r',
          unmodifiedText: '\r',
          windowsVirtualKeyCode: 13,
        })
        await comando('Input.dispatchKeyEvent', {
          type: 'keyUp',
          key: 'Enter',
          code: 'Enter',
          windowsVirtualKeyCode: 13,
        })
        await ate("document.querySelector('.simulation-summary details').open")
        assert.equal(
          await avaliar(
            "document.querySelector('.simulation-summary details p').textContent.split(', ').length",
          ),
          20,
        )
        await comando('Emulation.setDeviceMetricsOverride', {
          width: 390,
          height: 1000,
          deviceScaleFactor: 1,
          mobile: true,
        })
        assert.ok(
          await avaliar('document.documentElement.scrollWidth <= innerWidth'),
        )
        await capturarArea('resumo-ids-expandidos')
      },
    )
    await contexto.test(
      'Tela 02 encaminha a comparação validada para execução real na Tela 03',
      async () => {
        await avaliar(
          "sessionStorage.removeItem('observatorio-resultado-execucao');window.location.hash='#configuracao'",
        )
        await ate("document.querySelector('#cfg-ids')?.matches(':enabled')")
        assert.equal(
          await avaliar("!!document.querySelector('.configuration-summary')"),
          false,
        )
        await avaliar(
          "[...document.querySelectorAll('button')].find(botao=>botao.textContent.trim()==='Validar comparação').click()",
        )
        await ate("!!document.querySelector('.error-summary')")
        assert.equal(
          await avaliar(
            '!!document.querySelector(\'.configuration-summary a[href="#simulacao"]\')',
          ),
          false,
        )
        await avaliar(
          `for(const [identificador,valor] of [['cfg-ids','0'],['cfg-beta','0'],['cfg-gamma','1'],['cfg-limite_passos','2'],['cfg-repeticoes','3']]){const campo=document.getElementById(identificador);Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(campo,valor);campo.dispatchEvent(new Event('input',{bubbles:true}))};document.querySelector('#intervencao-ativa').click()`,
        )
        await ate("!!document.querySelector('#intervencao-fracao')")
        await avaliar(
          "const campo=document.querySelector('#intervencao-fracao');Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(campo,'1');campo.dispatchEvent(new Event('input',{bubbles:true}))",
        )
        await avaliar(
          "[...document.querySelectorAll('button')].find(botao=>botao.textContent.trim()==='Validar comparação').click()",
        )
        await ate(
          "document.querySelector('.configuration-summary h2')?.textContent==='Comparação validada'",
        )
        await avaliar(
          "(()=>{const campo=document.querySelector('#cfg-repeticoes');Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(campo,'4');campo.dispatchEvent(new Event('input',{bubbles:true}))})()",
        )
        await ate("!document.querySelector('.configuration-summary')")
        await avaliar(
          "(()=>{const campo=document.querySelector('#cfg-repeticoes');Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(campo,'3');campo.dispatchEvent(new Event('input',{bubbles:true}))})()",
        )
        await avaliar(
          "[...document.querySelectorAll('button')].find(botao=>botao.textContent.trim()==='Validar comparação').click()",
        )
        await ate(
          "document.querySelector('.configuration-summary h2')?.textContent==='Comparação validada'",
        )
        assert.doesNotMatch(
          await avaliar(
            "document.querySelector('.configuration-summary').textContent",
          ),
          /será liberada|integrada posteriormente|estiver integrada/,
        )
        await ate(
          '!!document.querySelector(\'.configuration-summary a[href="#simulacao"]\')',
        )
        await capturarArea('comparacao-validada', '.configuration-summary')
        await avaliar(
          'document.querySelector(\'.configuration-summary a[href="#simulacao"]\').focus()',
        )
        await comando('Input.dispatchKeyEvent', {
          type: 'keyDown',
          key: 'Enter',
          code: 'Enter',
          text: '\r',
          unmodifiedText: '\r',
          windowsVirtualKeyCode: 13,
        })
        await comando('Input.dispatchKeyEvent', {
          type: 'keyUp',
          key: 'Enter',
          code: 'Enter',
          windowsVirtualKeyCode: 13,
        })
        await ate(
          "document.querySelector('.experiment-actions .button-primary')?.matches(':enabled')",
        )
        assert.match(
          await avaliar(
            "document.querySelector('.experiment-card[aria-pressed=true]').textContent",
          ),
          /Repetições/,
        )
        assert.match(
          await avaliar(
            "document.querySelector('.simulation-summary').textContent",
          ),
          /3 repetições/,
        )
        assert.equal(
          await avaliar(
            "sessionStorage.getItem('observatorio-resultado-execucao')",
          ),
          null,
        )
        await recarregar()
        await ate(
          "document.querySelector('.experiment-actions .button-primary')?.matches(':enabled')",
        )
        assert.match(
          await avaliar(
            "document.querySelector('.experiment-card[aria-pressed=true]').textContent",
          ),
          /Repetições/,
        )
        await avaliar(
          "document.querySelector('.experiment-actions .button-primary').click()",
        )
        await ate(
          "JSON.parse(sessionStorage.getItem('observatorio-resultado-execucao'))?.tipo==='comparacao'",
        )
        await avaliar("document.querySelector('.button-pause').click()")
        const execucoes = await avaliar(
          "JSON.parse(sessionStorage.getItem('observatorio-resultado-execucao')).comparacao.execucoes.map(execucao=>execucao.cenario)",
        )
        assert.equal(execucoes.length, 9)
        assert.deepEqual([...new Set(execucoes)].sort(), [
          'aleatoria',
          'grau',
          'sem_intervencao',
        ])
        assert.deepEqual(
          await avaliar(
            "(()=>{const indicador=document.querySelector('[role=meter]');return [indicador.getAttribute('aria-valuenow'),indicador.getAttribute('aria-valuemax'),indicador.firstElementChild.style.width]})()",
          ),
          ['20', '20', '100%'],
        )
        const proporcoes = await avaliar(
          "[...document.querySelectorAll('.population-proportion span')].map(elemento=>parseFloat(elemento.style.width))",
        )
        assert.ok(
          Math.abs(proporcoes.reduce((soma, valor) => soma + valor, 0) - 100) <
            0.001,
        )
        await capturarArea('isolamento-total', '.population-distribution')
      },
    )
  },
)
