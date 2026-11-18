import { useEffect, useRef, useState } from 'react'

/** Mantém o estado alinhado ao navegador, inclusive ao sair com Esc. */
export function useTelaCheia() {
  const painel = useRef<HTMLElement>(null)
  const botao = useRef<HTMLButtonElement>(null)
  const [ativa, setAtiva] = useState(false)
  const [alternando, setAlternando] = useState(false)
  const [erro, setErro] = useState('')
  const pendente = useRef(false)
  const montado = useRef(false)

  useEffect(() => {
    montado.current = true
    const elemento = painel.current
    if (!elemento) return
    let estavaAtiva = false
    function sincronizar() {
      const atual = document.fullscreenElement === elemento
      setAtiva(atual)
      if (atual)
        elemento
          ?.querySelector<HTMLElement>('.graph-viewport')
          ?.focus({ preventScroll: true })
      else if (estavaAtiva) botao.current?.focus({ preventScroll: true })
      estavaAtiva = atual
    }
    function teclado(evento: KeyboardEvent) {
      if (document.fullscreenElement !== elemento) return
      if (evento.key === 'Escape') {
        void document.exitFullscreen().catch(() => undefined)
      } else if (evento.key === 'Tab') {
        const focaveis = elemento?.querySelectorAll<HTMLElement>(
          'button:not(:disabled), select:not(:disabled), [tabindex="0"]',
        )
        if (!focaveis?.length) return
        const primeiro = focaveis[0],
          ultimo = focaveis[focaveis.length - 1]
        if (evento.shiftKey && document.activeElement === primeiro) {
          evento.preventDefault()
          ultimo.focus()
        } else if (!evento.shiftKey && document.activeElement === ultimo) {
          evento.preventDefault()
          primeiro.focus()
        }
      }
    }
    document.addEventListener('fullscreenchange', sincronizar)
    document.addEventListener('keydown', teclado)
    return () => {
      montado.current = false
      document.removeEventListener('fullscreenchange', sincronizar)
      document.removeEventListener('keydown', teclado)
      if (document.fullscreenElement === elemento)
        void document.exitFullscreen().catch(() => undefined)
    }
  }, [])

  async function alternar() {
    const elemento = painel.current
    if (!elemento || pendente.current) return
    pendente.current = true
    setAlternando(true)
    setErro('')
    try {
      if (document.fullscreenElement === elemento)
        await document.exitFullscreen()
      else if (
        document.fullscreenEnabled &&
        typeof elemento.requestFullscreen === 'function'
      )
        await elemento.requestFullscreen()
      else
        setErro(
          'Tela cheia indisponível neste navegador. A navegação e o zoom da rede continuam disponíveis.',
        )
    } catch {
      if (montado.current)
        setErro(
          'Não foi possível alterar a tela cheia. Tente novamente pelo botão.',
        )
    } finally {
      pendente.current = false
      if (montado.current) setAlternando(false)
    }
  }

  return { painel, botao, ativa, alternando, erro, alternar }
}
