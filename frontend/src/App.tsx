import { useState } from 'react'
import { NetworkPage } from './pages/NetworkPage'
import { SimulationPage } from './pages/SimulationPage'
import './App.css'

export default function App() {
  const [pagina, setPagina] = useState<'rede' | 'simulacao'>(
    window.location.hash === '#rede' ? 'rede' : 'simulacao',
  )

  function navegar(destino: 'rede' | 'simulacao') {
    window.history.replaceState(null, '', `#${destino}`)
    setPagina(destino)
  }

  return pagina === 'rede' ? (
    <NetworkPage onNavegar={() => navegar('simulacao')} />
  ) : (
    <SimulationPage
      onNavegarRede={() => navegar('rede')}
    />
  )
}
