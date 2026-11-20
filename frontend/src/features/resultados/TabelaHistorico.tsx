import { useRef, useState } from 'react'
import type { RegistroResultado } from '../../services/configuracaoApi'

const REGISTROS_POR_PAGINA = 50

export function TabelaHistorico({
  historico,
}: {
  historico: readonly RegistroResultado[]
}) {
  const [pagina, setPagina] = useState(0)
  const tabela = useRef<HTMLDivElement | null>(null)
  const paginas = Math.max(
    1,
    Math.ceil(historico.length / REGISTROS_POR_PAGINA),
  )
  const atual = Math.min(pagina, paginas - 1)
  const inicio = atual * REGISTROS_POR_PAGINA
  const registros = historico.slice(inicio, inicio + REGISTROS_POR_PAGINA)

  function irParaPagina(proxima: number) {
    setPagina(proxima)
    if (tabela.current) tabela.current.scrollTop = 0
  }

  return (
    <>
      <div className="history-table-wrap" ref={tabela}>
        <table className="history-table" aria-labelledby="history-title">
          <thead>
            <tr>
              <th scope="col">t</th>
              <th scope="col">S</th>
              <th scope="col">I</th>
              <th scope="col">R</th>
              <th scope="col">Isolados</th>
            </tr>
          </thead>
          <tbody>
            {registros.map((registro) => (
              <tr key={registro.passo}>
                <td>{registro.passo}</td>
                <td>{registro.suscetiveis}</td>
                <td>{registro.infectados}</td>
                <td>{registro.recuperados}</td>
                <td>{registro.isolados}</td>
              </tr>
            ))}
            {!historico.length && (
              <tr>
                <td colSpan={5} className="history-empty">
                  Nenhum histórico registrado.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <nav
        className="pagination history-pagination"
        aria-label="Paginação do histórico"
      >
        <span role="status">
          {historico.length
            ? `${inicio + 1}–${inicio + registros.length} de ${historico.length.toLocaleString('pt-BR')} registros · Página ${atual + 1} de ${paginas}`
            : 'Nenhum registro'}
        </span>
        <div>
          <button
            type="button"
            className="button-secondary"
            aria-label="Primeira página do histórico"
            disabled={atual === 0}
            onClick={() => irParaPagina(0)}
          >
            «
          </button>
          <button
            type="button"
            className="button-secondary"
            aria-label="Página anterior do histórico"
            disabled={atual === 0}
            onClick={() => irParaPagina(atual - 1)}
          >
            Anterior
          </button>
          <button
            type="button"
            className="button-secondary"
            aria-label="Próxima página do histórico"
            disabled={atual === paginas - 1}
            onClick={() => irParaPagina(atual + 1)}
          >
            Próxima
          </button>
          <button
            type="button"
            className="button-secondary"
            aria-label="Última página do histórico"
            disabled={atual === paginas - 1}
            onClick={() => irParaPagina(paginas - 1)}
          >
            »
          </button>
        </div>
      </nav>
    </>
  )
}
