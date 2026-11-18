import { useLayoutEffect, useMemo, useRef, useState } from 'react'
import { Icon } from '../../../components/Icon'
import type { PreviaRede } from '../../../types/rede'
import { distribuirEm3D, ZOOM_MAXIMO, ZOOM_MINIMO } from './layout/graph3d'
import { useCameraRede } from './hooks/useCameraRede'
import { RenderizadorRede3D } from './renderers/drawNetwork3D'
import { RenderizadorRedeMapa } from './renderers/drawNetworkMap'
import { distribuirNoMapa } from './layout/graphMap'
import type {
  RenderizadorRede,
  VisualizacaoRede,
} from './renderers/networkRenderer'
import type { ModoNavegacao } from './hooks/useCameraRede'
import './NetworkScene.css'

interface Props {
  previa: PreviaRede
  selecionado: string | null
  onSelecionar: (id: string) => void
  ocupado: boolean
  visualizacao: VisualizacaoRede
  estadosPorNo?: Record<string, 'S' | 'I' | 'R' | 'isolado'>
  compacto?: boolean
}

const direcoes = [
  { nome: 'esquerda', x: -1, y: 0, classe: 'direction-left' },
  { nome: 'cima', x: 0, y: -1, classe: 'direction-up' },
  { nome: 'baixo', x: 0, y: 1, classe: 'direction-down' },
  { nome: 'direita', x: 1, y: 0, classe: 'direction-right' },
]

export function NetworkScene({
  previa,
  selecionado,
  onSelecionar,
  ocupado,
  visualizacao,
  estadosPorNo,
  compacto = false,
}: Props) {
  const [modo3D, setModo] = useState<ModoNavegacao>('girar')
  const mapa = visualizacao === 'mapa'
  const modo = mapa ? 'mover' : modo3D
  const maximoZoom = mapa ? 8 : ZOOM_MAXIMO
  const [lente, setLente] = useState(false)
  const canvas = useRef<HTMLCanvasElement>(null)
  const renderizador = useRef<RenderizadorRede | null>(null)
  const [indisponivel, setIndisponivel] = useState(false)
  const { area, zoom, eventos, navegar, zoomPorPasso, restaurar, redesenhar } =
    useCameraRede(modo, onSelecionar, renderizador, visualizacao)
  const nos = useMemo(() => distribuirEm3D(previa), [previa])
  const locais = useMemo(() => distribuirNoMapa(previa), [previa])
  const ids = useMemo(() => new Set(nos.map((no) => no.id)), [nos])
  const filtrar = lente && selecionado !== null && ids.has(selecionado)

  useLayoutEffect(() => {
    const elemento = canvas.current
    const contexto = elemento?.getContext('2d', { alpha: false })
    if (!elemento || !contexto) {
      setIndisponivel(true)
      return
    }
    const desenho = mapa
      ? new RenderizadorRedeMapa(elemento, contexto, locais, previa, estadosPorNo)
      : new RenderizadorRede3D(elemento, contexto, nos, previa, estadosPorNo)
    // O Canvas é reutilizado; remova somente a dica de hover da vista anterior.
    elemento.title = ''
    delete elemento.dataset.nodeHover
    renderizador.current = desenho
    const atualizarTema = () => {
      desenho.atualizarPaleta()
      redesenhar()
    }
    const observador = new MutationObserver(atualizarTema)
    observador.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme'],
    })
    const painel = elemento.closest('.graph-panel')
    if (painel)
      observador.observe(painel, {
        attributes: true,
        attributeFilter: ['class'],
      })
    redesenhar()
    return () => {
      observador.disconnect()
      renderizador.current = null
    }
  }, [nos, locais, previa, mapa, estadosPorNo, redesenhar])

  useLayoutEffect(() => {
    renderizador.current?.selecionar(selecionado, filtrar)
    redesenhar()
  }, [selecionado, filtrar, nos, mapa, redesenhar])

  return (
    <>
      <div className="graph-canvas-wrap">
        <div
          ref={area}
          className={`graph-viewport graph-mode-${modo}`}
          tabIndex={0}
          role="group"
          aria-label={
            mapa ? 'Visualização da rede no mapa' : 'Visualização 3D da rede'
          }
          aria-describedby="graph-navigation-help graph-caption"
          {...eventos}
        >
          <canvas
            ref={canvas}
            className="network-canvas"
            role="img"
            aria-label={`Prévia ${mapa ? 'no mapa' : '3D'} com ${previa.individuos.length} indivíduos e ${previa.contatos.length} contatos reais. Tamanho indica grau em uma escala comum entre redes. A seleção tem cor de destaque, anel e ID. ${mapa ? 'Posições geográficas ilustrativas, sem vínculo com localizações reais.' : 'Perspectiva indica profundidade.'} A inspeção por ID permite selecionar qualquer pessoa.`}
          />
          {indisponivel && (
            <p className="graph-render-error" role="status">
              Visualização indisponível neste navegador. Consulte os indivíduos
              e contatos abaixo.
            </p>
          )}
        </div>
        {ocupado && (
          <div className="graph-loading" role="status">
            Carregando rede…
          </div>
        )}
        <span className="graph-coordinate-note">
          {mapa
            ? 'Geografia ilustrativa · sem localização real'
            : 'Disposição 3D · posições ilustrativas'}
        </span>
      </div>
      {!compacto && <div className="graph-navigation">
        {!mapa && (
          <div
            className="graph-navigation-mode"
            role="group"
            aria-label="Modo de navegação"
          >
            <button
              aria-pressed={modo === 'girar'}
              onClick={() => setModo('girar')}
            >
              <Icon nome="orbit" size={16} />
              Girar
            </button>
            <button
              aria-pressed={modo === 'mover'}
              onClick={() => setModo('mover')}
            >
              <Icon nome="move" size={16} />
              Mover
            </button>
          </div>
        )}
        <div
          className="graph-directions"
          role="group"
          aria-label={
            modo === 'girar' ? 'Rotação da rede' : 'Deslocamento da rede'
          }
        >
          {direcoes.map((direcao) => (
            <button
              key={direcao.nome}
              aria-label={`${modo === 'girar' ? 'Girar' : 'Mover'} para ${direcao.nome}`}
              className={direcao.classe}
              onClick={() => navegar(direcao.x, direcao.y)}
            >
              <Icon nome="arrow" size={16} />
            </button>
          ))}
        </div>
        <div
          className="graph-controls"
          role="group"
          aria-label="Zoom da prévia"
        >
          <button
            aria-label="Diminuir zoom"
            disabled={zoom <= ZOOM_MINIMO}
            onClick={() => zoomPorPasso(-0.2)}
          >
            <Icon nome="minus" size={16} />
          </button>
          <output aria-label="Zoom atual">{Math.round(zoom * 100)}%</output>
          <button
            aria-label="Aumentar zoom"
            disabled={zoom >= maximoZoom}
            onClick={() => zoomPorPasso(0.2)}
          >
            <Icon nome="plus" size={16} />
          </button>
          <button
            aria-label="Restaurar visualização"
            onClick={() => {
              restaurar()
              setLente(false)
            }}
          >
            <Icon nome="home" size={16} />
          </button>
        </div>
      </div>}
      {!compacto && <p className="graph-navigation-help" id="graph-navigation-help">
        Arraste para {modo === 'girar' ? 'girar' : 'mover'} · role para
        aproximar. No toque, use dois dedos para mover e pinçar. Com foco na
        rede: setas navegam, Shift + setas movem, +/− ajustam o zoom e Home
        restaura.
        {mapa &&
          ' As posições no mapa são fictícias; distância e localização não alteram os contatos ou seus pesos.'}
      </p>}
      {!compacto && <div className="graph-bottom">
        <div className="graph-legend" role="group" aria-label="Legenda da rede">
          <span>
            <b className="node-key" aria-hidden="true" />
            Indivíduo
          </span>
          <span>
            <b className="selection-key" aria-hidden="true" />
            Selecionado
          </span>
          <span>Tamanho pelo grau</span>
        </div>
        <button
          className="contact-lens"
          aria-pressed={filtrar}
          disabled={selecionado === null || !ids.has(selecionado)}
          onClick={() => setLente(!filtrar)}
        >
          <Icon nome="eye" size={15} />
          {filtrar ? 'Mostrar todos os contatos' : 'Contatos do nó'}
        </button>
      </div>}
    </>
  )
}
