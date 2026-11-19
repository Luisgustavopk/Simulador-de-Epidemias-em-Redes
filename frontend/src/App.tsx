import { lazy, Suspense, useEffect, useState } from 'react'
import { ConfigurationPage } from './pages/ConfigurationPage'
import { SimulationPage } from './pages/SimulationPage'
import './App.css'

const Rede = lazy(() =>
  import('./pages/NetworkPage').then((m) => ({ default: m.NetworkPage })),
)

export default function App() {
  const [pagina, setPagina] = useState(() =>
    window.location.hash || '#rede',
  )

  useEffect(() => {
    const mudar = () => setPagina(window.location.hash)
    window.addEventListener('hashchange', mudar)
    return () => window.removeEventListener('hashchange', mudar)
  }, [])

  if (pagina === '#configuracao') {
    return <ConfigurationPage />
  }

  if (pagina === '#simulacao') {
    return <SimulationPage onNavegarRede={() => { window.location.hash = '#rede' }} />
  }

  return (
    <Suspense fallback={<p role="status">Carregando rede…</p>}>
      <Rede onNavegar={() => { window.location.hash = '#simulacao' }} />
    </Suspense>
  )
}
