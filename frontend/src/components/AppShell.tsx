import { useState } from 'react'
import type { ReactNode } from 'react'
import { Icon } from './Icon'
import { ThemeToggle } from './ThemeToggle'

const etapas = [
  {
    titulo: 'Rede de contatos',
    descricao: 'Carga e inspeção',
    destino: '#rede',
  },
  {
    titulo: 'Configuração',
    descricao: 'Modelo SIR e intervenção',
    destino: '#configuracao',
  },
  { titulo: 'Simulação', descricao: 'Em desenvolvimento' },
  { titulo: 'Resultados', descricao: 'Em desenvolvimento' },
]

export function AppShell({
  children,
  conectado,
  etapaAtiva = 0,
}: {
  children: ReactNode
  conectado: boolean
  etapaAtiva?: 0 | 1
}) {
  const [recolhida, setRecolhida] = useState(false)
  return (
    <>
      <a className="skip-link" href="#conteudo">
        Ir para o conteúdo
      </a>
      <header className="app-header">
        <a
          className="brand"
          href="#conteudo"
          aria-label="Observatório — início"
        >
          <svg
            className="brand-mark"
            viewBox="0 0 40 44"
            fill="none"
            aria-hidden="true"
          >
            <path
              d="m7 12 13-7 13 7v18l-13 8L7 30V12Zm0 0 13 9 13-9M20 21v17M7 30l13-9 13 9"
              stroke="currentColor"
              strokeWidth="1.5"
            />
            <circle cx="20" cy="5" r="3" fill="currentColor" />
            <circle cx="7" cy="30" r="3" fill="currentColor" />
            <circle cx="33" cy="30" r="3" fill="currentColor" />
            <circle
              cx="20"
              cy="21"
              r="4"
              fill="var(--color-accent)"
              stroke="currentColor"
              strokeWidth="1.5"
            />
          </svg>
          <span>
            <strong>Observatório</strong>
            <small>Epidemias em redes · modelo SIR</small>
          </span>
        </a>
        <div className="header-actions">
          <div className="header-meta">
            <span className={`connection-dot ${conectado ? 'online' : ''}`} />
            {conectado ? 'Ambiente local conectado' : 'Ambiente local'}
            <span className="header-model">S → I → R</span>
          </div>
          <ThemeToggle />
        </div>
      </header>
      <div className={`app-frame ${recolhida ? 'sidebar-collapsed' : ''}`}>
        <aside className="workflow-sidebar" aria-label="Navegação do estudo">
          <button
            className="nav-toggle"
            onClick={() => setRecolhida(!recolhida)}
            aria-expanded={!recolhida}
            aria-controls="workflow-nav"
            aria-label={recolhida ? 'Expandir navegação' : 'Recolher navegação'}
          >
            <Icon nome="menu" />
            <span>Etapas do estudo</span>
          </button>
          <nav id="workflow-nav" aria-label="Etapas do estudo">
            <ol>
              {etapas.map(({ titulo, descricao, destino }, indice) => (
                <li
                  key={titulo}
                  className={indice === etapaAtiva ? 'current' : ''}
                  aria-current={indice === etapaAtiva ? 'step' : undefined}
                >
                  {destino ? (
                    <a href={destino}>
                      <span className="step-number">{indice + 1}</span>
                      <span className="step-copy">
                        <strong>{titulo}</strong>
                        <small>{descricao}</small>
                      </span>
                    </a>
                  ) : (
                    <>
                      <span className="step-number">{indice + 1}</span>
                      <span className="step-copy">
                        <strong>{titulo}</strong>
                        <small>{descricao}</small>
                      </span>
                    </>
                  )}
                </li>
              ))}
            </ol>
          </nav>
          <p className="sidebar-note">
            Da estrutura da população
            <br />à evolução da epidemia.
          </p>
        </aside>
        <div className="work-sheet">
          {children}
          <footer className="app-footer">
            <span>Observatório · Simulador de Epidemias em Redes</span>
            <span>Grafo simples, não direcionado e ponderado</span>
          </footer>
        </div>
      </div>
    </>
  )
}
