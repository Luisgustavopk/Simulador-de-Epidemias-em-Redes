import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from 'react'
import type { KeyboardEvent, MouseEvent, PointerEvent, RefObject } from 'react'
import {
  aproximar,
  CAMERA_INICIAL,
  deslocar,
  girar,
  ZOOM_MINIMO,
  ZOOM_MAXIMO,
} from '../layout/graph3d'
import type {
  RenderizadorRede,
  VisualizacaoRede,
} from '../renderers/networkRenderer'
import type { Camera3D } from '../layout/graph3d'

export type ModoNavegacao = 'girar' | 'mover'
interface PosicaoPonteiro {
  x: number
  y: number
}
interface Gesto {
  inicio: PosicaoPonteiro
  modo: ModoNavegacao
  id: string | null
  arrastou: boolean
}

export function useCameraRede(
  modo: ModoNavegacao,
  onSelecionar: (id: string) => void,
  renderizador: RefObject<RenderizadorRede | null>,
  visualizacao: VisualizacaoRede,
) {
  const maximoZoom = visualizacao === 'mapa' ? 8 : ZOOM_MAXIMO
  const limiteDeslocamento = visualizacao === 'mapa' ? 12 : 2
  const area = useRef<HTMLDivElement>(null)
  const tamanho = useRef({ largura: 720, altura: 420 })
  const [zoom, setZoom] = useState(1)
  const estadoZoom = useRef('100:false:false')
  const atual = useRef<Camera3D>({ ...CAMERA_INICIAL })
  const cameras = useRef({
    '3d': { ...CAMERA_INICIAL },
    mapa: { ...CAMERA_INICIAL },
  })
  const quadro = useRef(0)
  const ponteiros = useRef(new Map<number, PosicaoPonteiro>())
  const gesto = useRef<Gesto | null>(null)

  const redesenhar = useCallback(() => {
    if (quadro.current) return
    quadro.current = requestAnimationFrame(() => {
      quadro.current = 0
      renderizador.current?.desenhar(atual.current, tamanho.current)
      const valor = atual.current.zoom
      const estado = `${Math.round(valor * 100)}:${valor <= ZOOM_MINIMO}:${valor >= maximoZoom}`
      // Só o indicador de zoom passa pelo React. Girar e mover desenham diretamente.
      if (estado !== estadoZoom.current) {
        estadoZoom.current = estado
        setZoom(valor)
      }
    })
  }, [renderizador, maximoZoom])

  const atualizar = useCallback(
    (operacao: (camera: Camera3D) => Camera3D) => {
      atual.current = operacao(atual.current)
      cameras.current[visualizacao] = atual.current
      redesenhar()
    },
    [redesenhar, visualizacao],
  )

  const encerrar = useCallback(() => {
    const ids = [...ponteiros.current.keys()]
    ponteiros.current.clear()
    gesto.current = null
    for (const id of ids) {
      if (area.current?.hasPointerCapture(id))
        area.current.releasePointerCapture(id)
    }
  }, [])

  useLayoutEffect(() => {
    encerrar()
    atual.current = cameras.current[visualizacao]
    redesenhar()
  }, [visualizacao, encerrar, redesenhar])

  useEffect(() => {
    const elemento = area.current
    if (!elemento) return
    const observador = new ResizeObserver(([entrada]) => {
      const { width, height } = entrada.contentRect
      if (width > 0 && height > 0)
        tamanho.current = { largura: width, altura: height }
      redesenhar()
    })
    observador.observe(elemento)
    const rolar = (evento: WheelEvent) => {
      // Ctrl/Meta + roda continuam disponíveis para o zoom do navegador.
      if (evento.ctrlKey || evento.metaKey) return
      evento.preventDefault()
      const unidade =
        evento.deltaMode === 1
          ? 16
          : evento.deltaMode === 2
            ? tamanho.current.altura
            : 1
      const delta = Math.max(-120, Math.min(120, evento.deltaY * unidade))
      atualizar((vista) =>
        aproximar(vista, Math.exp(-delta * 0.0018), maximoZoom),
      )
    }
    elemento.addEventListener('wheel', rolar, { passive: false })
    window.addEventListener('blur', encerrar)
    return () => {
      observador.disconnect()
      elemento.removeEventListener('wheel', rolar)
      window.removeEventListener('blur', encerrar)
      encerrar()
      cancelAnimationFrame(quadro.current)
      quadro.current = 0
    }
  }, [atualizar, encerrar, redesenhar, maximoZoom])

  useEffect(() => () => encerrar(), [modo, encerrar])

  function iniciar(evento: PointerEvent<HTMLDivElement>) {
    if (![0, 1, 2].includes(evento.button) || ponteiros.current.size >= 2)
      return
    evento.preventDefault()
    evento.currentTarget.focus({ preventScroll: true })
    const ponto = { x: evento.clientX, y: evento.clientY }
    ponteiros.current.set(evento.pointerId, ponto)
    if (ponteiros.current.size === 1) {
      const retangulo = evento.currentTarget.getBoundingClientRect()
      const id =
        renderizador.current?.individuoEm(
          ponto.x - retangulo.left,
          ponto.y - retangulo.top,
          evento.pointerType === 'touch' ? 20 : 10,
        ) ?? null
      renderizador.current?.indicarPonteiro(null)
      gesto.current = {
        inicio: ponto,
        modo: evento.shiftKey || evento.button !== 0 ? 'mover' : modo,
        id: evento.button === 0 ? id : null,
        arrastou: false,
      }
    } else if (gesto.current) gesto.current.arrastou = true
    evento.currentTarget.setPointerCapture(evento.pointerId)
  }

  function mover(evento: PointerEvent<HTMLDivElement>) {
    const anterior = ponteiros.current.get(evento.pointerId)
    const ativo = gesto.current
    if (!anterior || !ativo) {
      if (evento.pointerType !== 'touch') {
        const retangulo = evento.currentTarget.getBoundingClientRect()
        renderizador.current?.indicarPonteiro(
          renderizador.current.individuoEm(
            evento.clientX - retangulo.left,
            evento.clientY - retangulo.top,
          ),
        )
      }
      return
    }
    const antes = [...ponteiros.current.values()]
    const ponto = { x: evento.clientX, y: evento.clientY }
    ponteiros.current.set(evento.pointerId, ponto)
    if (Math.hypot(ponto.x - ativo.inicio.x, ponto.y - ativo.inicio.y) > 5)
      ativo.arrastou = true
    const altura = tamanho.current.altura || 1
    if (ponteiros.current.size === 2) {
      const depois = [...ponteiros.current.values()]
      const distanciaAntes = Math.hypot(
        antes[1].x - antes[0].x,
        antes[1].y - antes[0].y,
      )
      const distanciaDepois = Math.hypot(
        depois[1].x - depois[0].x,
        depois[1].y - depois[0].y,
      )
      const dx =
        (depois[0].x + depois[1].x - antes[0].x - antes[1].x) / (2 * altura)
      const dy =
        (depois[0].y + depois[1].y - antes[0].y - antes[1].y) / (2 * altura)
      atualizar((vista) =>
        deslocar(
          aproximar(
            vista,
            distanciaAntes > 1 ? distanciaDepois / distanciaAntes : 1,
            maximoZoom,
          ),
          dx,
          dy,
          limiteDeslocamento,
        ),
      )
    } else {
      const dx = (ponto.x - anterior.x) / altura
      const dy = (ponto.y - anterior.y) / altura
      atualizar((vista) =>
        ativo.modo === 'mover'
          ? deslocar(vista, dx, dy, limiteDeslocamento)
          : girar(vista, dx * 3, dy * 3),
      )
    }
  }

  function finalizar(evento: PointerEvent<HTMLDivElement>) {
    if (!ponteiros.current.has(evento.pointerId)) return
    const ativo = gesto.current
    ponteiros.current.delete(evento.pointerId)
    if (!ponteiros.current.size) gesto.current = null
    if (evento.currentTarget.hasPointerCapture(evento.pointerId))
      evento.currentTarget.releasePointerCapture(evento.pointerId)
    if (ativo && !ativo.arrastou && ativo.id !== null) onSelecionar(ativo.id)
  }

  function navegar(x: number, y: number, moverVista = modo === 'mover') {
    atualizar((vista) =>
      moverVista
        ? deslocar(vista, x * 0.12, y * 0.12, limiteDeslocamento)
        : girar(vista, x * 0.2, y * 0.2),
    )
  }

  function zoomPorPasso(passo: number) {
    atualizar((vista) =>
      aproximar(vista, (vista.zoom + passo) / vista.zoom, maximoZoom),
    )
  }

  function restaurar() {
    encerrar()
    atualizar(() => ({ ...CAMERA_INICIAL }))
  }

  function teclado(evento: KeyboardEvent<HTMLDivElement>) {
    if (evento.altKey || evento.ctrlKey || evento.metaKey) return
    const direcoes: Record<string, [number, number]> = {
      ArrowLeft: [-1, 0],
      ArrowRight: [1, 0],
      ArrowUp: [0, -1],
      ArrowDown: [0, 1],
    }
    if (direcoes[evento.key])
      navegar(...direcoes[evento.key], evento.shiftKey || modo === 'mover')
    else if (evento.key === '+' || evento.key === '=') zoomPorPasso(0.2)
    else if (evento.key === '-') zoomPorPasso(-0.2)
    else if (evento.key === 'Home') restaurar()
    else return
    evento.preventDefault()
  }

  return {
    area,
    zoom,
    redesenhar,
    navegar,
    zoomPorPasso,
    restaurar,
    eventos: {
      onPointerDown: iniciar,
      onPointerMove: mover,
      onPointerUp: finalizar,
      onPointerLeave: () => renderizador.current?.indicarPonteiro(null),
      onPointerCancel: encerrar,
      onLostPointerCapture: (evento: PointerEvent<HTMLDivElement>) => {
        if (ponteiros.current.has(evento.pointerId)) encerrar()
      },
      onKeyDown: teclado,
      onContextMenu: (evento: MouseEvent) => evento.preventDefault(),
    },
  }
}
