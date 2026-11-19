import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { InterventionFields } from '../components/InterventionFields'
import { AppShell } from '../components/AppShell'
import {
  ResumoComparacao,
  ResumoConfiguracao,
} from '../components/ConfigurationSummaries'
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

const rotulosCampos: Record<string, string> = {
  beta: 'Contágio (β)',
  gamma: 'Recuperação (γ)',
  modo_peso: 'Interpretação do peso',
  modo_iniciais: 'Escolha dos infectados iniciais',
  ids_infectados_iniciais: 'IDs iniciais',
  quantidade_infectados: 'Quantidade de infectados iniciais',
  semente_epidemia: 'Semente dos eventos epidemiológicos',
  semente_iniciais: 'Semente dos infectados iniciais',
  semente_isolamento: 'Semente da seleção aleatória',
  limite_passos: 'Limite de passos',
  intervencao: 'Intervenção por isolamento',
  'intervencao.estrategia': 'Estratégia de seleção',
  'intervencao.fracao': 'Fração de pessoas a isolar',
  'intervencao.inicio': 'Dia de início da intervenção',
  'intervencao.mecanismo': 'Mecanismo sobre os contatos',
  'intervencao.reducao': 'Fração de redução dos pesos',
  repeticoes: 'Número de repetições',
  rede: 'Rede de contatos',
  revisao: 'Revisão da rede',
  revisao_rede: 'Revisão da rede',
}

type TipoValidacao = 'individual' | 'comparacao'

function revisaoDaValidacao(
  resultado: ConfiguracaoValidada | ComparacaoValidada,
) {
  return 'configuracao' in resultado
    ? resultado.configuracao.revisao_rede
    : resultado.revisao_rede
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
  const [problemas, setProblemas] = useState<ProblemaCarga[]>([])
  const [resultado, setResultado] = useState<
    ConfiguracaoValidada | ComparacaoValidada | null
  >(null)
  const [validacaoAtiva, setValidacaoAtiva] = useState<TipoValidacao | null>(
    null,
  )
  const validando = validacaoAtiva !== null
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
  const resultadoAtual =
    pronto &&
    resultado &&
    resultado.contexto_rede === rede?.contexto_rede &&
    revisaoDaValidacao(resultado) === rede?.revisao
      ? resultado
      : null
  const configuracaoValida =
    resultadoAtual && 'configuracao' in resultadoAtual ? resultadoAtual : null
  const comparacaoValida =
    resultadoAtual && 'cenarios' in resultadoAtual ? resultadoAtual : null
  const errosRepeticoes = problemas.filter((p) => p.campo === 'repeticoes')

  function invalidarValidacao() {
    pedido.current?.abort()
    pedido.current = null
    setValidacaoAtiva(null)
    setResultado(null)
    setProblemas([])
  }

  function alterar(campo: keyof typeof iniciais, valor: string) {
    invalidarValidacao()
    setCampos((atual) => ({ ...atual, [campo]: valor }))
  }

  function enviar(evento: FormEvent, tipo: TipoValidacao) {
    evento.preventDefault()
    void validar(tipo)
  }

  async function validar(tipo: TipoValidacao) {
    if (!pronto || !rede || pedido.current) return
    const controlador = new AbortController()
    pedido.current = controlador
    setResultado(null)
    setProblemas([])
    setValidacaoAtiva(tipo)
    try {
      const condicoesIniciais =
        campos.modo_iniciais === 'ids'
          ? {
              modo_iniciais: 'ids' as const,
              ids_infectados_iniciais: campos.ids.trim()
                ? campos.ids.trim().split(/[\s,;]+/)
                : [],
            }
          : {
              modo_iniciais: 'sorteio' as const,
              quantidade_infectados: campos.quantidade,
            }
      const modoPeso =
        campos.modo_peso === 'intensidade' ? 'intensidade' : 'probabilidade'
      const formulario: FormularioConfiguracao = {
        beta: modoPeso === 'intensidade' ? campos.beta : null,
        gamma: campos.gamma,
        modo_peso: modoPeso,
        ...condicoesIniciais,
        semente_epidemia: campos.semente_epidemia,
        semente_iniciais: campos.semente_iniciais,
        semente_isolamento: campos.semente_isolamento,
        limite_passos: campos.limite_passos,
        revisao_rede: String(rede.revisao),
        contexto_rede: rede.contexto_rede,
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
      if (
        !atual.confirmada ||
        atual.contexto_rede !== resultado.contexto_rede ||
        atual.revisao !== revisaoDaValidacao(resultado)
      ) {
        throw new Error('A rede mudou. Valide a configuração novamente.')
      }
      setResultado(resultado)
      sessionStorage.setItem(
        'observatorio-configuracao',
        JSON.stringify({
          repeticoes: tipo === 'comparacao' ? repeticoes : null,
          formulario,
        }),
      )
    } catch (erro) {
      if (!controlador.signal.aborted) {
        setProblemas(problemasDoErro(erro))
        requestAnimationFrame(() => erros.current?.focus())
      }
    } finally {
      if (pedido.current === controlador) {
        pedido.current = null
        setValidacaoAtiva(null)
      }
    }
  }

  const camposDoFormulario = { campos, problemas, alterar }

  return (
    <AppShell conectado={conectado} etapaAtiva={2}>
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
        <form onSubmit={(e) => enviar(e, 'individual')} noValidate>
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
                <CampoConfiguracao
                  {...camposDoFormulario}
                  campo="beta"
                  titulo="β — contágio por contato unitário"
                />
              ) : (
                <p>β não se aplica ao modo de probabilidade direta.</p>
              )}
              <CampoConfiguracao
                {...camposDoFormulario}
                campo="gamma"
                titulo="γ — recuperação por passo"
              />
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
            {campos.modo_iniciais === 'ids' ? (
              <CampoConfiguracao
                {...camposDoFormulario}
                campo="ids"
                titulo="IDs iniciais — separe por espaço ou vírgula"
              />
            ) : (
              <CampoConfiguracao
                {...camposDoFormulario}
                campo="quantidade"
                titulo="Quantidade de infectados iniciais"
              />
            )}
            <p>
              Lista vazia ou quantidade zero representam ausência de infectados.
            </p>
          </fieldset>
          <fieldset disabled={!pronto || validando}>
            <legend>Reprodução e horizonte</legend>
            <div className="fields-grid">
              <CampoConfiguracao
                {...camposDoFormulario}
                campo="semente_epidemia"
                titulo="Semente dos eventos epidemiológicos"
              />
              <CampoConfiguracao
                {...camposDoFormulario}
                campo="semente_iniciais"
                titulo="Semente dos infectados iniciais"
              />
              <CampoConfiguracao
                {...camposDoFormulario}
                campo="limite_passos"
                titulo="Limite de passos"
              />
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
            quantidade={
              configuracaoValida?.configuracao.intervencao?.quantidade_isolados
            }
            campoSemente={
              <CampoConfiguracao
                {...camposDoFormulario}
                campo="semente_isolamento"
                titulo="Semente da seleção aleatória"
              />
            }
          />
          <button
            className="button-primary"
            disabled={!pronto || validando}
            type="submit"
          >
            {validacaoAtiva === 'individual'
              ? 'Validando…'
              : 'Validar configuração'}
          </button>
        </form>
        <form onSubmit={(e) => enviar(e, 'comparacao')} noValidate>
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
            <button type="submit">
              {validacaoAtiva === 'comparacao'
                ? 'Validando…'
                : 'Validar comparação'}
            </button>
          </fieldset>
        </form>
        {problemas.length > 0 && (
          <div role="alert" className="error-summary" ref={erros} tabIndex={-1}>
            <strong>Revise os campos indicados</strong>
            <ul>
              {problemas.map((p, i) => (
                <li key={i}>
                  {rotulosCampos[p.campo] ? rotulosCampos[p.campo] + ': ' : ''}
                  {p.mensagem}
                </li>
              ))}
            </ul>
          </div>
        )}
        {comparacaoValida && <ResumoComparacao resultado={comparacaoValida} />}
        {configuracaoValida && (
          <ResumoConfiguracao resultado={configuracaoValida} />
        )}
      </main>
    </AppShell>
  )
}

function CampoConfiguracao({
  campo,
  titulo,
  campos,
  problemas,
  alterar,
}: {
  campo: keyof typeof iniciais
  titulo: string
  campos: typeof iniciais
  problemas: ProblemaCarga[]
  alterar: (campo: keyof typeof iniciais, valor: string) => void
}) {
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
