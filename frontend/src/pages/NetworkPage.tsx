import { useState } from 'react'
import { AppShell } from '../components/AppShell'
import { Icon } from '../components/Icon'
import { DegreeDistribution } from '../features/rede/components/DegreeDistribution'
import { NetworkGraph } from '../features/rede/visualizacao/NetworkGraph'
import { NetworkRecords } from '../features/rede/components/NetworkRecords'
import { NetworkSource } from '../features/rede/components/NetworkSource'
import { NodeInspector } from '../features/rede/components/NodeInspector'
import { useCargaRede } from '../hooks/useCargaRede'
import { descreverOrigem } from '../types/rede'

export function NetworkPage() {
  const carga = useCargaRede()
  const [selecao, setSelecao] = useState<{
    versao: number
    id: string
  } | null>(null)
  const rede = carga.rede
  const resumo = rede?.resumo ?? null
  const selecionado =
    selecao?.versao === carga.versaoVisual ? (selecao?.id ?? null) : null
  const ocupado = !!carga.operacao
  function selecionar(id: string) {
    if (rede) setSelecao({ versao: carga.versaoVisual, id })
  }
  const medidas = [
    ['Indivíduos', 'N', resumo?.numero_individuos],
    ['Contatos', 'E', resumo?.numero_contatos],
    ['Grau médio', '⟨k⟩', resumo?.grau_medio],
    ['Grau máximo', 'k máx.', resumo?.grau_maximo],
  ] as const

  return (
    <AppShell conectado={carga.conexao === 'online'}>
      <main id="conteudo" className="workspace" tabIndex={-1}>
        <div className="workspace-heading">
          <div>
            <h1>Rede de contatos</h1>
            <p>
              Explore os caminhos que uma epidemia pode percorrer.
              <br className="desktop-break" /> Importe sua população ou construa
              uma rede sintética.
            </p>
          </div>
          <div
            className="sir-model"
            role="img"
            aria-label="Modelo SIR: suscetível, infectado e recuperado. A configuração será feita na próxima etapa."
          >
            <span>
              <b>S</b>
              <small>Suscetível</small>
            </span>
            <i>
              β<Icon nome="arrow" size={33} />
            </i>
            <span>
              <b>I</b>
              <small>Infectado</small>
            </span>
            <i>
              γ<Icon nome="arrow" size={33} />
            </i>
            <span>
              <b>R</b>
              <small>Recuperado</small>
            </span>
          </div>
        </div>
        <div
          className={`api-status ${carga.conexao === 'offline' ? 'api-offline' : ''}`}
          id="api-status"
          tabIndex={-1}
          role="status"
        >
          {carga.conexao === 'offline' ? (
            <>
              <Icon nome="alert" />
              <span>
                API local indisponível. Inicie{' '}
                <code>python -m simulador.api_local</code> na raiz do projeto.
              </span>
              <button
                className="text-button"
                disabled={ocupado}
                onClick={() => void carga.sincronizar()}
              >
                {carga.operacao === 'atualizando'
                  ? 'Reconectando…'
                  : 'Reconectar'}
              </button>
            </>
          ) : carga.conexao === 'conectando' ? (
            'Conectando ao ambiente local…'
          ) : (
            <>
              <span className="connection-dot online" />
              <span>Ambiente pronto para carregar sua rede.</span>
              {rede?.disponivel && (
                <button
                  className="text-button"
                  disabled={ocupado}
                  onClick={() => void carga.sincronizar()}
                >
                  {carga.operacao === 'atualizando'
                    ? 'Atualizando…'
                    : 'Atualizar rede'}
                </button>
              )}
            </>
          )}
        </div>
        <div className="network-workbench">
          <NetworkGraph
            c={carga.versaoVisual}
            rede={rede}
            previa={carga.previa}
            selecionado={selecionado}
            onSelecionar={selecionar}
            ocupado={
              ocupado &&
              carga.operacao !== 'confirmando' &&
              carga.operacao !== 'atualizando'
            }
            erro={carga.erroPrevia}
            onRepetir={() => void carga.repetirPrevia()}
          />
          <NetworkSource
            ocupado={ocupado}
            operacao={carga.operacao}
            conectado={carga.conexao === 'online'}
            problemas={carga.problemas.filter((p) => p.campo !== 'conexao')}
            redePreservada={!!rede?.disponivel}
            onMudarModo={carga.limparProblemas}
            onGerar={carga.gerar}
            onImportar={carga.importar}
          />
        </div>
        <section className="network-analytics" aria-label="Análise estrutural">
          <div className="structure-measures">
            <h2>Medidas da rede</h2>
            <p className="analysis-context">
              {resumo
                ? `${resumo.numero_componentes.toLocaleString('pt-BR')} componente(s) conexa(s) · ${resumo.conexa ? 'Rede conectada' : 'Rede desconexa'}`
                : 'As medidas serão calculadas após a carga.'}
            </p>
            <dl className="network-stats">
              {medidas.map(([titulo, simbolo, valor]) => (
                <div key={titulo}>
                  <dt>
                    {titulo}
                    <small>{simbolo}</small>
                  </dt>
                  <dd title={valor === undefined ? undefined : String(valor)}>
                    {valor === undefined
                      ? '—'
                      : valor.toLocaleString(
                          'pt-BR',
                          simbolo === '⟨k⟩'
                            ? { maximumSignificantDigits: 4 }
                            : undefined,
                        )}
                  </dd>
                </div>
              ))}
            </dl>
            <p className="analysis-context">
              Grafo não direcionado · intensidades normalizadas em [0, 1]
            </p>
            {rede?.disponivel ? (
              <NodeInspector
                key={carga.versaoVisual}
                revisao={rede.revisao}
                previa={carga.previa}
                selecionado={selecionado}
                onSelecionar={selecionar}
                onAtualizar={carga.sincronizar}
              />
            ) : (
              <div className="inspector-empty">
                <Icon nome="search" />
                <p>
                  Carregue uma rede para consultar indivíduos e seus contatos.
                </p>
              </div>
            )}
          </div>
          <DegreeDistribution resumo={resumo} />
        </section>
        {rede?.disponivel && (
          <NetworkRecords
            key={carga.versaoVisual}
            revisao={rede.revisao}
            onSelecionar={selecionar}
            onAtualizar={carga.sincronizar}
          />
        )}
        <div
          className={`confirmation-bar ${rede?.confirmada ? 'is-confirmed' : ''}`}
        >
          <div>
            <span
              className={`confirmation-icon ${rede?.disponivel ? 'ready' : ''}`}
            >
              <Icon nome={rede?.confirmada ? 'check' : 'network'} size={18} />
            </span>
            <div>
              <strong>
                {rede?.confirmada
                  ? 'Rede confirmada'
                  : rede?.disponivel
                    ? 'Estrutura pronta para inspeção'
                    : 'Nenhuma rede carregada'}
              </strong>
              <p role="status">
                {carga.mensagem ||
                  (rede?.confirmada
                    ? `${descreverOrigem(rede)} · disponível para as próximas etapas.`
                    : rede?.disponivel
                      ? 'Confira os dados e confirme esta rede para configurar o cenário.'
                      : 'Escolha uma origem para começar o estudo.')}
              </p>
            </div>
          </div>
          <button
            className="button-primary"
            disabled={
              !rede?.disponivel ||
              !!rede.confirmada ||
              ocupado ||
              carga.conexao !== 'online'
            }
            onClick={() => void carga.confirmar()}
          >
            {carga.operacao === 'confirmando'
              ? 'Confirmando…'
              : rede?.confirmada
                ? 'Rede confirmada'
                : 'Confirmar rede'}
            <Icon nome={rede?.confirmada ? 'check' : 'arrow'} />
          </button>
        </div>
        {rede?.confirmada && (
          <p className="next-step-note">
            A rede está disponível no serviço de carga. A tela de configuração
            será integrada na próxima etapa.
          </p>
        )}
      </main>
    </AppShell>
  )
}
