import { useEffect, useRef, useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'
import { Icon } from '../../../components/Icon'
import type { FormularioGeracao, ProblemaCarga } from '../../../types/rede'

interface Props {
  ocupado: boolean
  operacao: string | null
  conectado: boolean
  problemas: ProblemaCarga[]
  redePreservada: boolean
  onMudarModo: () => void
  onGerar: (campos: FormularioGeracao) => Promise<void>
  onImportar: (
    contatos: File,
    pessoas: File | null,
    delimitador: string,
  ) => Promise<void>
}

const campos: Record<string, string> = {
  modelo: 'modelo',
  numero_individuos: 'numero_individuos',
  semente: 'semente',
  peso: 'peso',
  contatos_por_novo_individuo: 'contatos_por_novo_individuo',
  probabilidade_contato: 'probabilidade_contato',
  arquivo_contatos: 'arquivo_contatos',
  arquivo_individuos: 'arquivo_individuos',
  arquivos: 'arquivo_contatos',
  delimitador: 'delimitador',
}

function Field({
  nome,
  label,
  valor,
  onChange,
  ajuda,
  erros,
  inteiro = false,
}: {
  nome: string
  label: string
  valor: string
  onChange: (valor: string) => void
  ajuda?: string
  erros: ProblemaCarga[]
  inteiro?: boolean
}) {
  const erro = erros.find((p) => p.campo === nome)
  return (
    <div className="field">
      <label htmlFor={nome}>{label}</label>
      <input
        id={nome}
        name={nome}
        type="text"
        inputMode={inteiro ? 'numeric' : 'decimal'}
        value={valor}
        onChange={(e) => onChange(e.target.value)}
        required
        autoComplete="off"
        aria-invalid={!!erro}
        aria-describedby={
          [ajuda && `${nome}-hint`, erro && `${nome}-error`]
            .filter(Boolean)
            .join(' ') || undefined
        }
      />
      {ajuda && (
        <small id={`${nome}-hint`} className="field-hint">
          {ajuda}
        </small>
      )}
      {erro && (
        <small id={`${nome}-error`} className="field-error">
          {erro.mensagem}
        </small>
      )}
    </div>
  )
}

function FileField({
  id,
  label,
  arquivo,
  onChange,
  erro,
}: {
  id: string
  label: string
  arquivo: File | null
  onChange: (arquivo: File | null) => void
  erro?: ProblemaCarga
}) {
  function selecionar(evento: ChangeEvent<HTMLInputElement>) {
    onChange(evento.target.files?.[0] ?? null)
    evento.target.value = ''
  }
  return (
    <div className="file-field">
      <label className={`file-drop ${erro ? 'invalid' : ''}`} htmlFor={id}>
        <Icon nome="upload" size={20} />
        <span>
          <strong>{label}</strong>
          <small>CSV UTF-8 · até 5 MiB</small>
        </span>
        <input
          id={id}
          type="file"
          accept=".csv,text/csv"
          onChange={selecionar}
          aria-invalid={!!erro}
          aria-describedby={`${id}-status${erro ? ` ${id}-error` : ''}`}
        />
      </label>
      <div className="file-status" id={`${id}-status`}>
        <Icon nome="file" size={14} />
        <span>{arquivo?.name ?? 'Nenhum arquivo selecionado'}</span>
        {arquivo && (
          <button
            type="button"
            className="text-button"
            onClick={() => onChange(null)}
            aria-label={`Remover ${arquivo.name}`}
          >
            Remover
          </button>
        )}
      </div>
      {erro && (
        <small id={`${id}-error`} className="field-error">
          {erro.mensagem}
        </small>
      )}
    </div>
  )
}

export function NetworkSource({
  ocupado,
  operacao,
  conectado,
  problemas,
  redePreservada,
  onMudarModo,
  onGerar,
  onImportar,
}: Props) {
  const [modo, setModo] = useState<'gerar' | 'importar'>('gerar')
  const [formulario, setFormulario] = useState<FormularioGeracao>({
    modelo: 'barabasi_albert',
    numero_individuos: '1250',
    contatos_por_novo_individuo: '4',
    probabilidade_contato: '0,02',
    peso: '1',
    semente: '42',
  })
  const [contatos, setContatos] = useState<File | null>(null)
  const [pessoas, setPessoas] = useState<File | null>(null)
  const [delimitador, setDelimitador] = useState(',')
  const [erroLocal, setErroLocal] = useState(false)
  const sumario = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (problemas.length) sumario.current?.focus()
  }, [problemas])

  function mudar(nome: keyof FormularioGeracao, valor: string) {
    setFormulario((atual) => ({ ...atual, [nome]: valor }))
  }

  function submeter(evento: FormEvent) {
    evento.preventDefault()
    if (modo === 'gerar') {
      const { modelo, numero_individuos, peso, semente } = formulario
      void onGerar({
        modelo,
        numero_individuos,
        peso,
        semente,
        ...(modelo === 'barabasi_albert'
          ? {
              contatos_por_novo_individuo:
                formulario.contatos_por_novo_individuo,
            }
          : { probabilidade_contato: formulario.probabilidade_contato }),
      })
    } else if (contatos) {
      setErroLocal(false)
      void onImportar(contatos, pessoas, delimitador)
    } else {
      setErroLocal(true)
      document.getElementById('arquivo_contatos')?.focus()
    }
  }

  return (
    <aside className="network-source" aria-labelledby="source-title">
      <div className="source-heading">
        <h2 id="source-title">Construir a rede</h2>
        <Icon nome="network" />
      </div>
      <div className="source-modes" role="group" aria-label="Origem da rede">
        <button
          type="button"
          aria-pressed={modo === 'gerar'}
          onClick={() => {
            setModo('gerar')
            setErroLocal(false)
            onMudarModo()
          }}
          disabled={ocupado}
        >
          Gerar
        </button>
        <button
          type="button"
          aria-pressed={modo === 'importar'}
          onClick={() => {
            setModo('importar')
            setErroLocal(false)
            onMudarModo()
          }}
          disabled={ocupado}
        >
          Importar
        </button>
      </div>
      {!!problemas.length && (
        <div ref={sumario} tabIndex={-1} className="error-summary" role="alert">
          <strong>Não foi possível concluir</strong>
          <ul>
            {problemas.slice(0, 20).map((p, indice) => (
              <li key={indice}>
                <a href={`#${campos[p.campo] ?? 'api-status'}`}>
                  {p.arquivo &&
                    `${p.arquivo}${p.linha ? `, linha ${p.linha}` : ''}${p.coluna ? `, ${p.coluna}` : ''}: `}
                  {p.mensagem}
                </a>
              </li>
            ))}
          </ul>
          {problemas.length > 20 && (
            <p>
              Mostrando os primeiros 20 de{' '}
              {problemas.length.toLocaleString('pt-BR')} problemas. Corrija
              esses registros e carregue o arquivo novamente para conferir os
              demais.
            </p>
          )}
          {redePreservada && <p>A última rede válida foi preservada.</p>}
        </div>
      )}
      <form
        noValidate
        onSubmit={submeter}
        aria-label={
          modo === 'gerar' ? 'Gerar rede sintética' : 'Importar rede observada'
        }
        aria-busy={ocupado}
      >
        <fieldset disabled={ocupado}>
          <legend className="sr-only">
            {modo === 'gerar' ? 'Parâmetros da geração' : 'Arquivos da rede'}
          </legend>
          {modo === 'gerar' ? (
            <>
              <div className="field">
                <label htmlFor="modelo">Topologia</label>
                <select
                  id="modelo"
                  value={formulario.modelo}
                  onChange={(e) => {
                    mudar('modelo', e.target.value)
                    onMudarModo()
                  }}
                >
                  <option value="barabasi_albert">
                    Barabási–Albert · livre de escala
                  </option>
                  <option value="erdos_renyi">Erdős–Rényi · aleatória</option>
                </select>
              </div>
              <div className="fields-grid">
                <Field
                  nome="numero_individuos"
                  label="Indivíduos · N"
                  valor={formulario.numero_individuos}
                  onChange={(v) => mudar('numero_individuos', v)}
                  erros={problemas}
                  inteiro
                />
                {formulario.modelo === 'barabasi_albert' ? (
                  <Field
                    nome="contatos_por_novo_individuo"
                    label="Contatos por nó · m"
                    valor={formulario.contatos_por_novo_individuo ?? ''}
                    onChange={(v) => mudar('contatos_por_novo_individuo', v)}
                    erros={problemas}
                    inteiro
                  />
                ) : (
                  <Field
                    nome="probabilidade_contato"
                    label="Probabilidade · p"
                    valor={formulario.probabilidade_contato ?? ''}
                    onChange={(v) => mudar('probabilidade_contato', v)}
                    erros={problemas}
                  />
                )}
                <Field
                  nome="semente"
                  label="Semente"
                  valor={formulario.semente}
                  onChange={(v) => mudar('semente', v)}
                  erros={problemas}
                  inteiro
                />
                <Field
                  nome="peso"
                  label="Peso dos contatos"
                  valor={formulario.peso}
                  onChange={(v) => mudar('peso', v)}
                  erros={problemas}
                />
              </div>
              <p className="source-help">
                {formulario.modelo === 'barabasi_albert'
                  ? 'Cada novo indivíduo se conecta a m pessoas, com preferência por quem já tem mais contatos. Use 1 ≤ m < N.'
                  : 'Cada par de indivíduos tem probabilidade p de conexão. A rede pode ter componentes separadas.'}
              </p>
              <button
                className="button-primary full-width"
                disabled={!conectado || ocupado}
              >
                {operacao === 'gerando'
                  ? 'Gerando rede…'
                  : 'Gerar rede sintética'}
                <Icon nome="arrow" />
              </button>
              <p className="source-help">
                Pesos entre 0 e 1. A mesma topologia, parâmetros e semente
                reproduzem a rede.
              </p>
            </>
          ) : (
            <>
              <FileField
                id="arquivo_contatos"
                label="Arquivo de contatos"
                arquivo={contatos}
                onChange={(file) => {
                  setContatos(file)
                  setErroLocal(false)
                }}
                erro={
                  erroLocal
                    ? {
                        campo: 'arquivo_contatos',
                        mensagem: 'Selecione um arquivo de contatos.',
                      }
                    : problemas.find((p) => p.campo === 'arquivo_contatos')
                }
              />
              <p className="source-help">
                Cabeçalho: <code>origem,destino,peso</code>. Peso ausente ou
                vazio assume 1.
              </p>
              <FileField
                id="arquivo_individuos"
                label="Cadastro de indivíduos (opcional)"
                arquivo={pessoas}
                onChange={setPessoas}
                erro={problemas.find((p) => p.campo === 'arquivo_individuos')}
              />
              <p className="source-help">
                CSV com cabeçalho <code>id</code> e todas as pessoas, incluindo
                as que não têm contatos.
              </p>
              <div className="field">
                <label htmlFor="delimitador">Separador de colunas</label>
                <select
                  id="delimitador"
                  value={delimitador}
                  onChange={(e) => setDelimitador(e.target.value)}
                >
                  <option value=",">Vírgula (,)</option>
                  <option value=";">Ponto e vírgula (;)</option>
                  <option value={'\t'}>Tabulação</option>
                </select>
              </div>
              <button
                className="button-primary full-width"
                disabled={!conectado || ocupado}
              >
                {operacao === 'importando'
                  ? 'Importando rede…'
                  : 'Carregar arquivos'}
                <Icon nome="arrow" />
              </button>
              <a
                className="example-link"
                href="/exemplos/contatos.csv"
                download
              >
                Baixar exemplo de contatos <Icon nome="file" size={14} />
              </a>
            </>
          )}
        </fieldset>
      </form>
    </aside>
  )
}
