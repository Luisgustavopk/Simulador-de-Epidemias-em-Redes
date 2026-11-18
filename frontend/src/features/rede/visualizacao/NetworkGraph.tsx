import { useState } from 'react'
import { Icon } from '../../../components/Icon'
import type { InspecaoRede, PreviaRede } from '../../../types/rede'
import { descreverOrigem } from '../../../types/rede'
import { NetworkScene } from './NetworkScene'
import type { VisualizacaoRede } from './renderers/networkRenderer'
import { useTelaCheia } from './hooks/useTelaCheia'
import './NetworkGraph.css'

interface Props {
  versaoVisual: number
  rede: InspecaoRede | null
  previa: PreviaRede | null
  selecionado: string | null
  onSelecionar: (id: string) => void
  ocupado: boolean
  erro: string
  onRepetir: () => void
}

export function NetworkGraph({
  versaoVisual,
  rede,
  previa,
  selecionado,
  onSelecionar,
  ocupado,
  erro,
  onRepetir,
}: Props) {
  const [tema, setTema] = useState<'dark' | 'light'>('dark')
  const [visualizacao, setVisualizacao] = useState<VisualizacaoRede>('3d')
  const {
    painel,
    botao,
    ativa: telaCheia,
    alternando,
    erro: erroTelaCheia,
    alternar,
  } = useTelaCheia()

  return (
    <section
      ref={painel}
      id="graph-view"
      className="network-inspection"
      aria-labelledby="graph-title"
    >
      <div className="graph-heading">
        <div>
          <h2 id="graph-title">Topologia de contatos</h2>
          <p>{descreverOrigem(rede)}</p>
        </div>
        <div className="graph-heading-actions">
          <div
            className="graph-view-switch"
            role="group"
            aria-label="Visualização da rede"
          >
            <button
              type="button"
              aria-pressed={visualizacao === 'mapa'}
              onClick={() => setVisualizacao('mapa')}
            >
              Mapa
            </button>
            <button
              type="button"
              aria-pressed={visualizacao === '3d'}
              onClick={() => setVisualizacao('3d')}
            >
              3D
            </button>
          </div>
          <div className="graph-theme" role="group" aria-label="Tema do grafo">
            <button
              onClick={() => setTema('light')}
              aria-pressed={tema === 'light'}
            >
              Claro
            </button>
            <button
              onClick={() => setTema('dark')}
              aria-pressed={tema === 'dark'}
            >
              Escuro
            </button>
          </div>
          <button
            ref={botao}
            className="graph-fullscreen"
            type="button"
            aria-controls="graph-view"
            aria-expanded={telaCheia}
            aria-busy={alternando}
            disabled={!previa && !telaCheia}
            onClick={() => void alternar()}
          >
            <Icon nome={telaCheia ? 'collapse' : 'reset'} size={16} />
            {telaCheia ? 'Sair da tela cheia' : 'Tela cheia'}
          </button>
        </div>
      </div>
      {telaCheia && previa && (
        <div className="graph-fullscreen-selection">
          <label htmlFor="graph-selected-node">
            Selecionar indivíduo na prévia
          </label>
          <select
            id="graph-selected-node"
            value={
              previa.individuos.some((no) => no.id === selecionado)
                ? selecionado!
                : ''
            }
            onChange={(evento) => {
              if (evento.target.value !== '') onSelecionar(evento.target.value)
            }}
          >
            <option value="">
              {selecionado === null
                ? 'Selecione um indivíduo'
                : 'ID selecionado fora da prévia'}
            </option>
            {previa.individuos.map((no) => (
              <option key={no.id} value={no.id}>
                ID {no.id} · grau {no.grau}
              </option>
            ))}
          </select>
        </div>
      )}
      {erroTelaCheia && (
        <p className="graph-fullscreen-error" role="status">
          {erroTelaCheia}
        </p>
      )}
      <div
        className={`graph-panel graph-${tema}`}
        aria-busy={ocupado || (!!rede?.disponivel && !previa && !erro)}
      >
        {previa ? (
          <NetworkScene
            key={versaoVisual}
            visualizacao={visualizacao}
            previa={previa}
            selecionado={selecionado}
            onSelecionar={onSelecionar}
            ocupado={ocupado}
          />
        ) : (
          <div className="graph-canvas-wrap">
            <div className="graph-empty">
              <Icon nome={erro ? 'alert' : 'network'} size={46} />
              <strong>
                {erro
                  ? 'Prévia indisponível'
                  : rede?.disponivel
                    ? 'Preparando a visualização…'
                    : 'Sua rede começa aqui'}
              </strong>
              <p>
                {erro ||
                  (rede?.disponivel
                    ? 'Organizando os indivíduos e seus contatos.'
                    : 'Gere uma topologia ou importe seus contatos para explorar a estrutura da população.')}
              </p>
              {erro && (
                <button className="graph-retry" onClick={onRepetir}>
                  Tentar novamente
                </button>
              )}
            </div>
            {ocupado && (
              <div className="graph-loading" role="status">
                Carregando rede…
              </div>
            )}
          </div>
        )}
      </div>
      <p className="graph-caption" id="graph-caption">
        {previa ? (
          <>
            {`${previa.parcial ? 'Prévia parcial' : 'Rede completa'}: ${previa.individuos.length.toLocaleString('pt-BR')} de ${previa.total_individuos.toLocaleString('pt-BR')} indivíduos e ${previa.contatos.length.toLocaleString('pt-BR')} de ${previa.total_contatos.toLocaleString('pt-BR')} contatos. `}
            {previa.individuos.length < previa.total_individuos &&
              'Recorte dos indivíduos com maior grau. '}
            As medidas abaixo consideram toda a população.
          </>
        ) : (
          'Gere ou importe uma rede para visualizar os contatos.'
        )}
      </p>
    </section>
  )
}
