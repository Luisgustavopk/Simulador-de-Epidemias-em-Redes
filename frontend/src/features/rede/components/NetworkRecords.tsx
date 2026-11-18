import { useEffect, useState } from 'react'
import { Icon } from '../../../components/Icon'
import {
  problemasDoErro,
  redeApi,
  redeDesatualizada,
} from '../../../services/redeApi'
import type { PaginaContatos, PaginaIndividuos } from '../../../types/rede'

export function NetworkRecords({
  revisao,
  onSelecionar,
  onAtualizar,
}: {
  revisao: number
  onSelecionar: (id: string) => void
  onAtualizar: () => Promise<void>
}) {
  const [tipo, setTipo] = useState<'individuos' | 'contatos'>('individuos')
  const [inicio, setInicio] = useState(0)
  const [tentativa, setTentativa] = useState(0)
  const [resultado, setResultado] = useState<{
    chave: string
    pagina?: PaginaContatos | PaginaIndividuos
    erro?: string
    desatualizada?: boolean
  } | null>(null)
  const chave = `${revisao}:${tipo}:${inicio}:${tentativa}`
  const atual = resultado?.chave === chave ? resultado : null
  useEffect(() => {
    const controlador = new AbortController()
    redeApi[tipo](revisao, inicio, controlador.signal)
      .then((pagina) => {
        if (!controlador.signal.aborted)
          setResultado({
            chave: `${revisao}:${tipo}:${inicio}:${tentativa}`,
            pagina,
          })
      })
      .catch((erro: unknown) => {
        if (!controlador.signal.aborted)
          setResultado({
            chave: `${revisao}:${tipo}:${inicio}:${tentativa}`,
            erro: problemasDoErro(erro)[0].mensagem,
            desatualizada: redeDesatualizada(erro),
          })
      })
    return () => controlador.abort()
  }, [tipo, inicio, revisao, tentativa])
  const pagina = atual?.pagina
  const total = pagina?.total ?? 0
  const colunas = tipo === 'individuos' ? 3 : 4
  return (
    <section className="network-records" aria-labelledby="records-title">
      <div className="records-heading">
        <h2 id="records-title">Dados da rede</h2>
        <div
          className="record-modes"
          role="group"
          aria-label="Dados a consultar"
        >
          <button
            aria-pressed={tipo === 'individuos'}
            onClick={() => {
              setTipo('individuos')
              setInicio(0)
            }}
          >
            Indivíduos
          </button>
          <button
            aria-pressed={tipo === 'contatos'}
            onClick={() => {
              setTipo('contatos')
              setInicio(0)
            }}
          >
            Contatos
          </button>
        </div>
      </div>
      <div
        className="table-scroll"
        tabIndex={0}
        role="region"
        aria-label={`Tabela de ${tipo}`}
        aria-busy={!atual}
      >
        <table>
          <caption className="sr-only">
            {tipo === 'individuos'
              ? 'Indivíduos ordenados por grau decrescente e ID crescente no empate'
              : 'Contatos não direcionados da rede'}
          </caption>
          <thead>
            <tr>
              {(tipo === 'individuos'
                ? ['ID do indivíduo', 'Grau', 'Inspeção']
                : ['Origem', 'Destino', 'Peso', 'Contato']
              ).map((titulo) => (
                <th key={titulo} scope="col">
                  {titulo}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {!atual ? (
              <tr>
                <td colSpan={colunas}>Carregando registros…</td>
              </tr>
            ) : atual.erro ? (
              <tr>
                <td colSpan={colunas}>
                  <p className="field-error" role="alert">
                    {atual.erro}
                  </p>
                  <button
                    className="text-button"
                    onClick={() =>
                      atual.desatualizada
                        ? void onAtualizar()
                        : setTentativa((anterior) => anterior + 1)
                    }
                  >
                    {atual.desatualizada
                      ? 'Atualizar rede'
                      : 'Tentar novamente'}
                  </button>
                </td>
              </tr>
            ) : pagina && 'individuos' in pagina && pagina.individuos.length ? (
              pagina.individuos.map((p) => (
                <tr key={p.id}>
                  <td>
                    <span className="id-cell" title={p.id}>
                      {p.id}
                    </span>
                  </td>
                  <td>{p.grau}</td>
                  <td>
                    <button
                      className="text-button"
                      onClick={() => {
                        onSelecionar(p.id)
                        requestAnimationFrame(() =>
                          document.getElementById('id-individuo')?.focus(),
                        )
                      }}
                    >
                      Inspecionar <Icon nome="arrow" size={14} />
                    </button>
                  </td>
                </tr>
              ))
            ) : pagina && 'contatos' in pagina && pagina.contatos.length ? (
              pagina.contatos.map((c) => (
                <tr key={`${c.origem}:${c.destino}`}>
                  <td>
                    <span className="id-cell" title={c.origem}>
                      {c.origem}
                    </span>
                  </td>
                  <td>
                    <span className="id-cell" title={c.destino}>
                      {c.destino}
                    </span>
                  </td>
                  <td title={String(c.peso)}>
                    {c.peso.toLocaleString('pt-BR', {
                      maximumSignificantDigits: 8,
                      notation:
                        c.peso > 0 && c.peso < 0.000001
                          ? 'scientific'
                          : 'standard',
                    })}
                  </td>
                  <td>{c.ativa ? 'Disponível' : 'Desativado'}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={colunas}>
                  Esta rede não possui{' '}
                  {tipo === 'individuos' ? 'indivíduos' : 'contatos'}.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="pagination">
        <span role="status">
          {pagina
            ? total
              ? `${inicio + 1}–${Math.min(inicio + 10, total)} de ${total.toLocaleString('pt-BR')} ${tipo === 'individuos' ? 'indivíduos' : 'contatos'}`
              : tipo === 'individuos'
                ? 'Nenhum indivíduo'
                : 'Nenhum contato'
            : atual?.erro
              ? 'Consulta indisponível'
              : 'Consultando…'}
        </span>
        <div>
          <button
            className="button-secondary"
            disabled={inicio === 0 || !atual}
            onClick={() => setInicio(Math.max(0, inicio - 10))}
          >
            Anterior
          </button>
          <button
            className="button-secondary"
            disabled={!pagina || inicio + 10 >= total}
            onClick={() => setInicio(inicio + 10)}
          >
            Próxima
          </button>
        </div>
      </div>
    </section>
  )
}
