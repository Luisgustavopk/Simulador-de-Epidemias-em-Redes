import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { InterventionFields } from '../components/InterventionFields'
import { AppShell } from '../components/AppShell'
import { problemasDoErro, redeApi } from '../services/redeApi'
import {
  prepararFormularioIntervencao,
  validarConfiguracao,
} from '../services/configuracaoApi'
import type {
  ConfiguracaoValidada,
  EntradaIntervencao,
} from '../services/configuracaoApi'
import type { InspecaoRede, ProblemaCarga } from '../types/rede'
import './ConfigurationPage.css'

const iniciais = {
  beta: '0.2',
  gamma: '0.1',
  modo_peso: 'intensidade',
  modo_iniciais: 'ids',
  ids: '',
  quantidade: '1',
  semente_epidemia: '42',
  semente_iniciais: '43',
  semente_isolamento: '44',
  limite_passos: '200',
}

export function ConfigurationPage() {
  const [campos, setCampos] = useState(iniciais)
  const [intervencao, setIntervencao] = useState<EntradaIntervencao>({
    ativa: false,
    estrategia: 'aleatoria',
    fracao: '0.1',
    inicio: '0',
    mecanismo: 'desativacao',
    reducao: '0.5',
  })
  const [rede, setRede] = useState<InspecaoRede | null>(null)
  const [conectado, setConectado] = useState(false)
  const [problemas, setProblemas] = useState<ProblemaCarga[]>([])
  const [resumo, setResumo] = useState<ConfiguracaoValidada | null>(null)
  const [validando, setValidando] = useState(false)
  const pedido = useRef<AbortController | null>(null)
  const erros = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const controlador = new AbortController()
    async function consultar() {
      try {
        const atual = await redeApi.inspecionar(controlador.signal)
        if (controlador.signal.aborted) return
        setRede(atual)
        setConectado(true)
      } catch {
        if (!controlador.signal.aborted) setConectado(false)
      }
    }
    void consultar()
    const intervalo = window.setInterval(() => void consultar(), 5000)
    window.addEventListener('focus', consultar)
    return () => {
      controlador.abort()
      pedido.current?.abort()
      window.clearInterval(intervalo)
      window.removeEventListener('focus', consultar)
    }
  }, [])

  const pronto = conectado && !!rede?.confirmada
  const valido =
    pronto && resumo?.configuracao.revisao_rede === rede?.revisao
      ? resumo
      : null

  function alterar(campo: keyof typeof iniciais, valor: string) {
    setValidando(false)
    setResumo(null)
    setProblemas([])
    setCampos((atual) => ({ ...atual, [campo]: valor }))
  }

  async function validar(evento: FormEvent) {
    evento.preventDefault()
    if (!pronto || !rede) return
    pedido.current?.abort()
    const controlador = new AbortController()
    pedido.current = controlador
    setResumo(null)
    setProblemas([])
    setValidando(true)
    try {
      const resultado = await validarConfiguracao(
        {
          beta: campos.modo_peso === 'intensidade' ? campos.beta : null,
          gamma: campos.gamma,
          modo_peso: campos.modo_peso as 'intensidade' | 'probabilidade',
          modo_iniciais: campos.modo_iniciais as 'ids' | 'sorteio',
          ...(campos.modo_iniciais === 'ids'
            ? {
                ids_infectados_iniciais: campos.ids.trim()
                  ? campos.ids.trim().split(/[\s,;]+/)
                  : [],
              }
            : { quantidade_infectados: campos.quantidade }),
          semente_epidemia: campos.semente_epidemia,
          semente_iniciais: campos.semente_iniciais,
          semente_isolamento: campos.semente_isolamento,
          limite_passos: campos.limite_passos,
          revisao_rede: String(rede.revisao),
          intervencao: prepararFormularioIntervencao(intervencao),
        },
        controlador.signal,
      )
      const atual = await redeApi.inspecionar(controlador.signal)
      if (controlador.signal.aborted) return
      setRede(atual)
      if (
        !atual.confirmada ||
        atual.revisao !== resultado.configuracao.revisao_rede
      )
        throw new Error('A rede mudou. Valide a configuração novamente.')
      setResumo(resultado)
    } catch (erro) {
      if (!controlador.signal.aborted) {
        setProblemas(problemasDoErro(erro))
        requestAnimationFrame(() => erros.current?.focus())
      }
    } finally {
      if (!controlador.signal.aborted) setValidando(false)
    }
  }

  function entrada(campo: keyof typeof iniciais, titulo: string) {
    const nomeErro =
      campo === 'ids'
        ? 'ids_infectados_iniciais'
        : campo === 'quantidade'
          ? 'quantidade_infectados'
          : campo
    const erro = problemas.filter((p) => p.campo === nomeErro)
    return (
      <div className="field">
        <label htmlFor={`cfg-${campo}`}>{titulo}</label>
        <input
          id={`cfg-${campo}`}
          value={campos[campo]}
          onChange={(e) => alterar(campo, e.target.value)}
          aria-invalid={erro.length > 0}
          aria-describedby={erro.length ? `erro-${campo}` : undefined}
        />
        {erro.length > 0 && (
          <p className="field-error" id={`erro-${campo}`}>
            {erro.map((p) => p.mensagem).join(' ')}
          </p>
        )}
      </div>
    )
  }

  return (
    <AppShell conectado={conectado} etapaAtiva={1}>
      <main id="conteudo" className="configuration-page">
        <h1>Configuração epidemiológica</h1>
        <p>
          Prepare parâmetros e infectados iniciais. Um passo representa um dia
          do modelo, sem calibração para previsão real.
        </p>
        <p role="status">
          {!conectado
            ? 'Conectando à API local…'
            : pronto
              ? `Rede confirmada · revisão ${rede?.revisao} · ${rede?.resumo?.numero_individuos} indivíduos`
              : 'Gere ou importe e confirme uma rede antes de validar.'}
        </p>
        <a href="#rede">Voltar à rede de contatos</a>
        <form onSubmit={(e) => void validar(e)} noValidate>
          <fieldset disabled={!pronto || validando}>
            <legend>Transmissão e recuperação</legend>
            <div className="field">
              <label htmlFor="cfg-modo">Interpretação do peso</label>
              <select
                id="cfg-modo"
                value={campos.modo_peso}
                onChange={(e) => alterar('modo_peso', e.target.value)}
              >
                <option value="intensidade">Intensidade: p = β × peso</option>
                <option value="probabilidade">
                  Probabilidade direta: p = peso
                </option>
              </select>
            </div>
            <div className="fields-grid">
              {campos.modo_peso === 'intensidade' ? (
                entrada('beta', 'β — contágio por contato unitário')
              ) : (
                <p>β não se aplica ao modo de probabilidade direta.</p>
              )}
              {entrada('gamma', 'γ — recuperação por passo')}
            </div>
          </fieldset>
          <fieldset disabled={!pronto || validando}>
            <legend>Condições iniciais</legend>
            <div className="field">
              <label htmlFor="cfg-iniciais">
                Escolha dos infectados iniciais
              </label>
              <select
                id="cfg-iniciais"
                value={campos.modo_iniciais}
                onChange={(e) => alterar('modo_iniciais', e.target.value)}
              >
                <option value="ids">IDs informados</option>
                <option value="sorteio">
                  Quantidade para sorteio sem reposição
                </option>
              </select>
            </div>
            {campos.modo_iniciais === 'ids'
              ? entrada('ids', 'IDs iniciais — separe por espaço ou vírgula')
              : entrada('quantidade', 'Quantidade de infectados iniciais')}
            <p>
              Lista vazia ou quantidade zero representam ausência de infectados.
            </p>
          </fieldset>
          <fieldset disabled={!pronto || validando}>
            <legend>Reprodução e horizonte</legend>
            <div className="fields-grid">
              {entrada(
                'semente_epidemia',
                'Semente dos eventos epidemiológicos',
              )}
              {entrada('semente_iniciais', 'Semente dos infectados iniciais')}
              {entrada('limite_passos', 'Limite de passos')}
            </div>
          </fieldset>
          <InterventionFields
            campos={intervencao}
            alterar={(novos) => {
              setIntervencao(novos)
              setResumo(null)
              setProblemas([])
            }}
            disabled={!pronto || validando}
            problemas={problemas}
            quantidade={valido?.configuracao.intervencao?.quantidade_isolados}
            campoSemente={entrada(
              'semente_isolamento',
              'Semente da seleção aleatória',
            )}
          />
          <button
            className="button-primary"
            disabled={!pronto || validando}
            type="submit"
          >
            {validando ? 'Validando…' : 'Validar configuração'}
          </button>
        </form>
        {problemas.length > 0 && (
          <div role="alert" className="error-summary" ref={erros} tabIndex={-1}>
            <strong>Revise os campos indicados</strong>
            <ul>
              {problemas.map((p, i) => (
                <li key={i}>
                  {p.campo}: {p.mensagem}
                </li>
              ))}
            </ul>
          </div>
        )}
        {valido && (
          <section
            className="configuration-summary"
            aria-label="Configuração validada"
            aria-live="polite"
          >
            <h2>Configuração validada</h2>
            <p>
              Revisão {valido.configuracao.revisao_rede}; população{' '}
              {valido.populacao}.
            </p>
            <p>
              Modo {valido.configuracao.modo_peso}; β{' '}
              {valido.configuracao.beta ?? 'não aplicável'}; γ{' '}
              {valido.configuracao.gamma}.
            </p>
            <p>
              IDs iniciais:{' '}
              {valido.configuracao.ids_infectados_iniciais.join(', ') ||
                'nenhum'}
              .
            </p>
            <p>Limite: {valido.configuracao.limite_passos} passos.</p>
            <p>
              Sementes — epidemia: {valido.configuracao.semente_epidemia};
              iniciais: {valido.configuracao.semente_iniciais}; isolamento:{' '}
              {valido.configuracao.semente_isolamento}.
            </p>
            {valido.configuracao.intervencao ? (
              <p>
                Intervenção:{' '}
                {valido.configuracao.intervencao.estrategia === 'grau'
                  ? 'por grau'
                  : 'aleatória'}
                ; fração {valido.configuracao.intervencao.fracao};{' '}
                {valido.configuracao.intervencao.quantidade_isolados}{' '}
                {valido.configuracao.intervencao.quantidade_isolados === 1
                  ? 'pessoa'
                  : 'pessoas'}
                ; dia {valido.configuracao.intervencao.inicio}; mecanismo{' '}
                {valido.configuracao.intervencao.mecanismo}.
                {valido.configuracao.intervencao.reducao !== null && (
                  <> Redução: {valido.configuracao.intervencao.reducao}.</>
                )}
              </p>
            ) : (
              <p>Sem intervenção neste cenário.</p>
            )}
            <p>
              A rede de referência continua intacta. A execução completa será
              integrada posteriormente.
            </p>
          </section>
        )}
      </main>
    </AppShell>
  )
}
