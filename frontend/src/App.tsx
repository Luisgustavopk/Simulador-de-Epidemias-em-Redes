import { lazy, Suspense, useEffect, useState } from 'react'
import { ConfigurationPage } from './pages/ConfigurationPage'
import './App.css'

const Rede = lazy(() =>
  import('./pages/NetworkPage').then((m) => ({ default: m.NetworkPage })),
)

export default function App() {
  const [pagina, setPagina] = useState(() => window.location.hash)
  useEffect(() => {
    const mudar = () => setPagina(window.location.hash)
    window.addEventListener('hashchange', mudar)
    return () => window.removeEventListener('hashchange', mudar)
  }, [])
  return pagina === '#configuracao' ? (
    <ConfigurationPage />
  ) : (
    <Suspense fallback={<p role="status">Carregando rede…</p>}>
      <Rede />
    </Suspense>
  )
}
