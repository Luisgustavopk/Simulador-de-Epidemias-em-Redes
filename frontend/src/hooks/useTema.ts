import { useEffect, useLayoutEffect, useRef, useState } from 'react'

type Tema = 'light' | 'dark'
const CHAVE_TEMA = 'observatorio-tema'

function preferenciaSalva(): Tema | null {
  try {
    const valor = localStorage.getItem(CHAVE_TEMA)
    return valor === 'light' || valor === 'dark' ? valor : null
  } catch {
    return null
  }
}

export function useTema() {
  // O bootstrap de index.html já escolheu o tema antes do primeiro desenho.
  const [tema, setTema] = useState<Tema>(() =>
    document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light',
  )
  const escolhaLocal = useRef<Tema | null>(null)

  useLayoutEffect(() => {
    document.documentElement.dataset.theme = tema
    const meta = document.querySelector<HTMLMetaElement>(
      'meta[name="theme-color"]',
    )
    if (meta)
      meta.content = getComputedStyle(document.documentElement)
        .getPropertyValue('--color-background')
        .trim()
  }, [tema])

  useEffect(() => {
    const sistema = window.matchMedia('(prefers-color-scheme: dark)')
    function sincronizar() {
      setTema(
        preferenciaSalva() ??
          escolhaLocal.current ??
          (sistema.matches ? 'dark' : 'light'),
      )
    }
    function aoAlterarArmazenamento(evento: StorageEvent) {
      if (evento.key === CHAVE_TEMA || evento.key === null) {
        escolhaLocal.current = preferenciaSalva()
        sincronizar()
      }
    }
    sistema.addEventListener('change', sincronizar)
    window.addEventListener('storage', aoAlterarArmazenamento)
    return () => {
      sistema.removeEventListener('change', sincronizar)
      window.removeEventListener('storage', aoAlterarArmazenamento)
    }
  }, [])

  function alternar() {
    const proximo = tema === 'dark' ? 'light' : 'dark'
    escolhaLocal.current = proximo
    try {
      localStorage.setItem(CHAVE_TEMA, proximo)
    } catch {
      // Sem armazenamento, a escolha vale enquanto a página estiver aberta.
    }
    setTema(proximo)
  }

  return { tema, alternar }
}
