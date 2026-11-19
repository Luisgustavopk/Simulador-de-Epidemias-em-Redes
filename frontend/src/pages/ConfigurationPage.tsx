import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { InterventionFields } from '../components/InterventionFields'
import { AppShell } from '../components/AppShell'
import { problemasDoErro, redeApi } from '../services/redeApi'
import {
  prepararFormularioIntervencao,
  validarComparacao,
  validarConfiguracao,
} from '../services/configuracaoApi'
import type {
  ComparacaoValidada,
  ConfiguracaoValidada,
  FormularioConfiguracao,
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

const rotulosCenarios = {
  sem_intervencao: 'Sem intervenção',
  aleatoria: 'Seleção aleatória',
  grau: 'Seleção por grau',
}

const rotulosMecanismos = {
  desativacao: 'Desativação dos contatos',
  reducao: 'Redução da intensidade',
  exclusao: 'Exclusão dos contatos',
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
  const [estadoConexao, setEstadoConexao] = useState<
    'inicial' | 'conectada' | 'falhou'
  >('inicial')
  const [problemasConexao, setProblemasConexao] = useState<ProblemaCarga[]>([])
  const conectado = estadoConexao === 'conectada'
  const [repeticoes, setRepeticoes] = useState('2')
  const [comparacao, setComparacao] = useState<ComparacaoValidada | null>(null)
  const [problemas, setProblemas] = useState<ProblemaCarga[]>([])
  const [resumo, setResumo] = useState<ConfiguracaoValidada | null>(null)
  const [validando, setValidando] = useState(false)
  const pedido = useRef<AbortController | null>(null)
  const erros = useRef<HTMLDivElement | null>(null)
  const consultaRede = useRef(0)

  useEffect(() => {
    const controlador = new AbortController()
    async function consultar() {
      const consulta = ++consultaRede.current
      try {
        const atual = await redeApi.inspecionar(controlador.signal)
        if (controlador.signal.aborted || consulta !== consultaRede.current)
          return
        setRede(atual)
        setEstadoConexao('conectada')
        setProblemasConexao([])
      } catch (erro) {
        if (controlador.signal.aborted || consulta !== consultaRede.current)
          return
        setEstadoConexao('falhou')
        setProblemasConexao(problemasDoErro(erro))
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

  const comparacaoValida =
    pronto && comparacao?.revisao_rede === rede?.revisao ? comparacao : null
  const errosRepeticoes = problemas.filter((p) => p.campo === 'repeticoes')

  function invalidarValidacao() {
    pedido.current?.abort()
    pedido.current = null
    setValidando(false)
    setResumo(null)
    setComparacao(null)
    setProblemas([])
  }

  function alterar(campo: keyof typeof iniciais, valor: string) {
    invalidarValidacao()
    setCampos((atual) => ({ ...atual, [campo]: valor }))
  }

  function enviar(evento: FormEvent) {
    evento.preventDefault()
    void validar('individual')
  }

  async function validar(tipo: 'individual' | 'comparacao') {
    if (!pronto || !rede || pedido.current) return
    const controlador = new AbortController()
    pedido.current = controlador
    setResumo(null)
    setComparacao(null)
    setProblemas([])
    setValidando(true)
    try {
      const formulario: FormularioConfiguracao = {
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
      }
      const consulta = ++consultaRede.current
      const resultado =
        tipo === 'comparacao'
          ? await validarComparacao(repeticoes, formulario, controlador.signal)
          : await validarConfiguracao(formulario, controlador.signal)
      const atual = await redeApi.inspecionar(controlador.signal)
      if (controlador.signal.aborted) return
      if (consulta === consultaRede.current) setRede(atual)
      const revisao =
        'configuracao' in resultado
          ? resultado.configuracao.revisao_rede
          : resultado.revisao_rede
      if (!atual.confirmada || atual.revisao !== revisao)
        throw new Error('A rede mudou. Valide a configuração novamente.')
      if ('configuracao' in resultado) setResumo(resultado)
      else setComparacao(resultado)
    } catch (erro) {
      if (!controlador.signal.aborted) {
        setProblemas(problemasDoErro(erro))
        requestAnimationFrame(() => erros.current?.focus())
      }
    } finally {
      if (pedido.current === controlador) {
        pedido.current = null
        setValidando(false)
      }
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
          {estadoConexao === 'inicial'
            ? 'Conectando à API local…'
            : estadoConexao === 'falhou'
              ? problemasConexao.map((problema) => problema.mensagem).join(' ')
              : pronto
                ? `Rede confirmada · revisão ${rede?.revisao} · ${rede?.resumo?.numero_individuos} indivíduos`
                : 'Gere ou importe e confirme uma rede antes de validar.'}
        </p>
        <a href="#rede">Voltar à rede de contatos</a>
        <form onSubmit={enviar} noValidate>
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
              invalidarValidacao()
              setIntervencao(novos)
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
          <fieldset disabled={!pronto || validando}>
            <legend>Comparação com repetições</legend>
            <p>
              Compare a rede sem intervenção com seleção aleatória e por grau.
              Ative a intervenção para definir o orçamento, o dia e o mecanismo
              das duas estratégias.
            </p>
            <div className="field">
              <label htmlFor="cfg-repeticoes">Número de repetições</label>
              <input
                id="cfg-repeticoes"
                inputMode="numeric"
                value={repeticoes}
                onChange={(e) => {
                  invalidarValidacao()
                  setRepeticoes(e.target.value)
                }}
                aria-invalid={errosRepeticoes.length > 0}
                aria-describedby={
                  errosRepeticoes.length ? 'erro-repeticoes' : undefined
                }
              />
              {errosRepeticoes.length > 0 && (
                <p id="erro-repeticoes" className="field-error">
                  {errosRepeticoes.map((p) => p.mensagem).join(' ')}
                </p>
              )}
            </div>
            <p>A comparação usa as três sementes informadas acima como base.</p>
            <button type="button" onClick={() => void validar('comparacao')}>
              Validar comparação
            </button>
          </fieldset>
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
        {comparacaoValida && (
          <section
            className="configuration-summary"
            aria-label="Comparação validada"
            aria-live="polite"
          >
            <h2>Comparação validada</h2>
            <p>
              {comparacaoValida.repeticoes} repetições · revisão{' '}
              {comparacaoValida.revisao_rede} · {comparacaoValida.populacao}{' '}
              indivíduos
            </p>
            <ul>
              {comparacaoValida.cenarios.map((cenario) => (
                <li key={cenario}>{rotulosCenarios[cenario]}</li>
              ))}
            </ul>
            <p>
              Orçamento por intervenção: {comparacaoValida.quantidade_isolados}.
              Dia {comparacaoValida.intervencao.inicio} ·{' '}
              {rotulosMecanismos[comparacaoValida.intervencao.mecanismo]}.
              {comparacaoValida.intervencao.reducao !== null && (
                <> Fração de redução: {comparacaoValida.intervencao.reducao}.</>
              )}
            </p>
            <p>
              {comparacaoValida.modo_iniciais === 'sorteio'
                ? `Infectados iniciais por sorteio em cada repetição: ${comparacaoValida.quantidade_infectados}.`
                : `Infectados iniciais por IDs informados: ${comparacaoValida.quantidade_infectados}.`}
            </p>
            <p>
              Sementes base — epidemia:{' '}
              {comparacaoValida.sementes_base.epidemia}; iniciais:{' '}
              {comparacaoValida.sementes_base.iniciais}; isolamento:{' '}
              {comparacaoValida.sementes_base.isolamento}.
            </p>
            <p id="execucao-comparacao-pendente">
              A execução da comparação será liberada quando a simulação
              individual estiver integrada.
            </p>
            <button
              type="button"
              disabled
              aria-describedby="execucao-comparacao-pendente"
            >
              Executar comparação
            </button>
          </section>
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
