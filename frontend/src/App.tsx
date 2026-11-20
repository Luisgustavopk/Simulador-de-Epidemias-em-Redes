import { lazy, Suspense, useEffect, useState } from 'react'
import { ConfigurationPage } from './pages/ConfigurationPage'
import { SimulationPage } from './pages/SimulationPage'
import { ResultsPage } from './pages/ResultsPage'
import './App.css'

const HASHES_PERMITIDOS = new Set([
  '',
  '#rede',
  '#configuracao',
  '#simulacao',
  '#resultados',
])

const Rede = lazy(() =>
  import('./pages/NetworkPage').then((m) => ({ default: m.NetworkPage })),
)

export default function App() {
  const hashInicial = window.location.hash
  if (!HASHES_PERMITIDOS.has(hashInicial)) {
    window.history.replaceState(null, '', '#rede')
  }
  const [pagina, setPagina] = useState(() =>
    HASHES_PERMITIDOS.has(hashInicial) && hashInicial ? hashInicial : '#rede',
  )

  useEffect(() => {
    const mudar = () => {
      const hash = window.location.hash
      if (!HASHES_PERMITIDOS.has(hash) || hash === '') {
        window.history.replaceState(null, '', '#rede')
        setPagina('#rede')
        return
      }
      setPagina(hash)
    }
    window.addEventListener('hashchange', mudar)
    return () => window.removeEventListener('hashchange', mudar)
  }, [])

  if (pagina === '#configuracao') {
    return <ConfigurationPage />
  }

  if (pagina === '#simulacao') {
    return (
      <SimulationPage
        onNavegarRede={() => {
          window.location.hash = '#rede'
        }}
      />
    )
  }

  if (pagina === '#resultados') {
    return <ResultsPage />
  }

  return (
    <Suspense fallback={<p role="status">Carregando rede…</p>}>
      <Rede
        onNavegar={() => {
          window.location.hash = '#simulacao'
        }}
      />
    </Suspense>
  )
}
