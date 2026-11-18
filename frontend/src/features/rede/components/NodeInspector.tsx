import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Icon } from '../../../components/Icon'
import {
  problemasDoErro,
  redeApi,
  redeDesatualizada,
} from '../../../services/redeApi'
import type { IndividuoInspecionado, PreviaRede } from '../../../types/rede'

export function NodeInspector({
  revisao,
  previa,
  selecionado,
  onSelecionar,
  onAtualizar,
}: {
  revisao: number
  previa: PreviaRede | null
  selecionado: string | null
  onSelecionar: (id: string) => void
  onAtualizar: () => Promise<void>
}) {
  const campoBusca = useRef<HTMLInputElement>(null)
  const [tentativa, setTentativa] = useState(0)
  const [consulta, setConsulta] = useState<{
    chave: string
    pessoa?: IndividuoInspecionado
    erro?: string
    desatualizada?: boolean
    idInvalido?: boolean
  } | null>(null)
  const chave = `${revisao}:${selecionado}:${tentativa}`
  const atual = consulta?.chave === chave ? consulta : null
  useEffect(() => {
    if (selecionado === null) return
    const controlador = new AbortController()
    redeApi
      .individuo(revisao, selecionado, controlador.signal)
      .then((pessoa) => {
        if (!controlador.signal.aborted)
          setConsulta({
            chave: `${revisao}:${selecionado}:${tentativa}`,
            pessoa,
          })
      })
      .catch((erro: unknown) => {
        if (!controlador.signal.aborted)
          setConsulta({
            chave: `${revisao}:${selecionado}:${tentativa}`,
            erro: problemasDoErro(erro)[0].mensagem,
            desatualizada: redeDesatualizada(erro),
            idInvalido: problemasDoErro(erro).some((p) => p.campo === 'id'),
          })
      })
    return () => controlador.abort()
  }, [revisao, selecionado, tentativa])

  function buscar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const id = String(new FormData(evento.currentTarget).get('id') ?? '').trim()
    if (!id) return
    if (id === selecionado) setTentativa((atual) => atual + 1)
    else onSelecionar(id)
    requestAnimationFrame(() => campoBusca.current?.focus())
  }
  const estados = { S: 'Suscetível', I: 'Infectado', R: 'Recuperado' }
  return (
    <section className="node-inspector" aria-labelledby="inspector-title">
      <h3 id="inspector-title">Inspecionar um indivíduo</h3>
      <form onSubmit={buscar} className="node-search">
        <label htmlFor="id-individuo" className="sr-only">
          ID do indivíduo
        </label>
        <input
          key={selecionado}
          ref={campoBusca}
          id="id-individuo"
          name="id"
          type="text"
          inputMode="numeric"
          defaultValue={selecionado ?? ''}
          placeholder="Digite um ID"
          required
          aria-invalid={atual?.idInvalido || undefined}
          aria-describedby={`id-help${atual?.erro ? ' id-error' : ''}`}
        />
        <button className="button-secondary" aria-label="Buscar indivíduo">
          <Icon nome="search" size={17} />
        </button>
      </form>
      {previa && (
        <div className="field">
          <label htmlFor="no-previa">Ou selecione na prévia, por grau</label>
          <select
            id="no-previa"
            value={
              previa.individuos.some((p) => p.id === selecionado)
                ? selecionado!
                : ''
            }
            onChange={(e) => e.target.value && onSelecionar(e.target.value)}
          >
            <option value="">Selecionar indivíduo</option>
            {previa.individuos.map((p) => (
              <option key={p.id} value={p.id}>
                ID {p.id} · grau {p.grau}
              </option>
            ))}
          </select>
        </div>
      )}
      <p id="id-help" className="field-hint">
        A busca por ID consulta toda a rede, inclusive pessoas fora da prévia.
      </p>
      <div className="node-result" role="status" aria-live="polite">
        {atual?.erro ? (
          <div>
            <p id="id-error" className="field-error">
              {atual.erro}
            </p>
            {!atual.idInvalido && (
              <button
                type="button"
                className="text-button"
                onClick={() =>
                  atual.desatualizada
                    ? void onAtualizar()
                    : setTentativa((anterior) => anterior + 1)
                }
              >
                {atual.desatualizada ? 'Atualizar rede' : 'Tentar novamente'}
              </button>
            )}
          </div>
        ) : atual?.pessoa ? (
          <>
            <div className="node-degree">
              <strong>{atual.pessoa.grau.toLocaleString('pt-BR')}</strong>
              <span>
                contatos
                <br />
                diretos
              </span>
            </div>
            <dl>
              <div>
                <dt>Estado SIR</dt>
                <dd>
                  {estados[atual.pessoa.estado]} ({atual.pessoa.estado})
                </dd>
              </div>
              <div>
                <dt>Isolamento</dt>
                <dd>{atual.pessoa.isolamento ? 'Isolado' : 'Não isolado'}</dd>
              </div>
            </dl>
          </>
        ) : (
          <p className="field-hint">
            {selecionado
              ? 'Consultando indivíduo…'
              : 'Escolha um nó no grafo ou busque seu ID.'}
          </p>
        )}
      </div>
    </section>
  )
}
