import type { ConfiguracaoValidada } from '../../services/configuracaoApi'
import { descreverOrigem, type InspecaoRede } from '../../types/rede'

const mecanismos = {
  desativacao: 'Desativação dos contatos',
  reducao: 'Redução da intensidade',
  exclusao: 'Exclusão dos contatos',
}

export function ResumoEnsaio({
  rede,
  validacao,
  modo,
  repeticoes,
  carregando,
  erro,
  onRepetir,
}: {
  rede: InspecaoRede | null
  validacao: ConfiguracaoValidada | null
  modo: 'unica' | 'repeticoes'
  repeticoes: string
  carregando: boolean
  erro: string
  onRepetir: () => void
}) {
  const configuracao = validacao?.configuracao
  const intervencao = configuracao?.intervencao
  const ids = configuracao?.ids_infectados_iniciais ?? []
  const sorteio = validacao?.modo_iniciais === 'sorteio'

  return (
    <section
      className="simulation-summary"
      aria-busy={carregando}
      aria-labelledby="simulation-summary-title"
    >
      <h2 id="simulation-summary-title">Resumo do ensaio</h2>
      <dl className="simulation-summary-grid">
        <div>
          <dt>Nome e origem da rede</dt>
          <dd>{descreverOrigem(rede)}</dd>
        </div>
        <div>
          <dt>Revisão da rede</dt>
          <dd>
            {rede?.disponivel
              ? `${rede.revisao} · ${rede.confirmada ? 'Confirmada' : 'Não confirmada'}`
              : '—'}
          </dd>
        </div>
        <div>
          <dt>População e contatos</dt>
          <dd>
            {rede?.resumo
              ? `${rede.resumo.numero_individuos.toLocaleString('pt-BR')} ${rede.resumo.numero_individuos === 1 ? 'indivíduo' : 'indivíduos'} · ${rede.resumo.numero_contatos.toLocaleString('pt-BR')} ${rede.resumo.numero_contatos === 1 ? 'contato' : 'contatos'}`
              : '—'}
          </dd>
        </div>
        {configuracao && (
          <>
            <div>
              <dt>Parâmetros epidemiológicos</dt>
              <dd>
                β = {configuracao.beta ?? 'não aplicável'} · γ ={' '}
                {configuracao.gamma}
              </dd>
            </div>
            <div>
              <dt>Interpretação dos pesos</dt>
              <dd>
                {configuracao.modo_peso === 'intensidade'
                  ? 'Intensidade · p = β × peso'
                  : 'Probabilidade direta · p = peso'}
              </dd>
            </div>
            <div>
              <dt>Limite e modalidade</dt>
              <dd>
                {configuracao.limite_passos} passos ·{' '}
                {modo === 'unica'
                  ? 'Execução única'
                  : `${repeticoes} repetições`}
              </dd>
            </div>
            <div>
              <dt>
                Semente epidemiológica{modo === 'repeticoes' ? ' base' : ''}
              </dt>
              <dd>{configuracao.semente_epidemia}</dd>
            </div>
            <div>
              <dt>
                Semente dos infectados iniciais
                {modo === 'repeticoes' ? ' base' : ''}
              </dt>
              <dd>{configuracao.semente_iniciais}</dd>
            </div>
            <div>
              <dt>
                Semente de isolamento{modo === 'repeticoes' ? ' base' : ''}
              </dt>
              <dd>{configuracao.semente_isolamento}</dd>
            </div>
            <div>
              <dt>Estratégia de isolamento</dt>
              <dd>
                {!intervencao
                  ? 'Sem intervenção'
                  : modo === 'repeticoes'
                    ? 'Sem intervenção · Aleatória · Por grau'
                    : intervencao.estrategia === 'grau'
                      ? 'Por grau'
                      : 'Aleatória'}
              </dd>
            </div>
            <div>
              <dt>Orçamento por intervenção</dt>
              <dd>
                {intervencao
                  ? `${intervencao.quantidade_isolados} de ${validacao.populacao} pessoas · fração ${intervencao.fracao}`
                  : 'Não se aplica — sem intervenção'}
              </dd>
            </div>
            <div>
              <dt>Início e mecanismo</dt>
              <dd>
                {intervencao
                  ? `Passo ${intervencao.inicio} · ${mecanismos[intervencao.mecanismo]}`
                  : 'Não se aplica — sem intervenção'}
                {intervencao?.reducao != null && (
                  <> · redução {intervencao.reducao}</>
                )}
              </dd>
            </div>
            <div className="simulation-summary-identifiers">
              <dt>
                IDs iniciais
                {modo === 'repeticoes' ? ' da primeira repetição' : ''}
              </dt>
              <dd>
                {ids.length > 12 ? (
                  <details>
                    <summary>
                      Consultar os {ids.length} IDs selecionados
                    </summary>
                    <p>{ids.join(', ')}</p>
                  </details>
                ) : (
                  ids.join(', ') || 'Nenhum infectado inicial'
                )}
                <small>
                  {sorteio
                    ? 'Seleção sorteada pelo backend.'
                    : 'IDs informados na configuração validada.'}
                  {modo === 'repeticoes' && (
                    <>
                      {' '}
                      As sementes de cada fluxo usam base + índice da repetição
                      (iniciando em zero).
                      {sorteio
                        ? ' Os IDs são sorteados novamente em cada repetição.'
                        : ''}
                    </>
                  )}
                </small>
              </dd>
            </div>
          </>
        )}
      </dl>
      {configuracao ? (
        <p className="simulation-summary-note" role="status">
          Parâmetros validados para esta revisão. Rede não direcionada e
          ponderada; a topologia muda somente pela intervenção configurada.
        </p>
      ) : erro ? (
        <div className="simulation-summary-feedback">
          <p role="alert">{erro}</p>
          <button
            type="button"
            className="button-secondary"
            onClick={onRepetir}
          >
            Tentar consultar novamente
          </button>
          <a href="#configuracao">Revisar configuração</a>
        </div>
      ) : (
        <p role="status" className="simulation-summary-note">
          {carregando
            ? 'Consultando a configuração validada…'
            : 'Confirme a rede e valide a configuração da revisão atual na Tela 02.'}
          {!carregando && (
            <>
              {' '}
              <a href="#configuracao">Abrir configuração</a>
            </>
          )}
        </p>
      )}
    </section>
  )
}
