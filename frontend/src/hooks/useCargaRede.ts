import { useCallback, useEffect, useRef, useState } from 'react'
import {
  problemasDoErro,
  redeApi,
  redeDesatualizada,
} from '../services/redeApi'
import type {
  FormularioGeracao,
  InspecaoRede,
  PreviaRede,
  ProblemaCarga,
} from '../types/rede'

export function useCargaRede() {
  const [rede, setRede] = useState<InspecaoRede | null>(null)
  const [previa, setPrevia] = useState<PreviaRede | null>(null)
  const [conexao, setConexao] = useState<'conectando' | 'online' | 'offline'>(
    'conectando',
  )
  const [operacao, setOperacao] = useState<
    'gerando' | 'importando' | 'confirmando' | 'atualizando' | null
  >(null)
  const [problemas, setProblemas] = useState<ProblemaCarga[]>([])
  const [erroPrevia, setErroPrevia] = useState('')
  const [mensagem, setMensagem] = useState('')
  // A revisão numérica reinicia quando a API ou a sessão é recriada.
  const [versaoVisual, setVersaoVisual] = useState(0)
  const emAndamento = useRef(false)
  const pedidoPrevia = useRef<AbortController | null>(null)

  const carregarPrevia = useCallback(async (inspecao: InspecaoRede) => {
    pedidoPrevia.current?.abort()
    setPrevia(null)
    setErroPrevia('')
    if (!inspecao.disponivel) return
    const controlador = new AbortController()
    pedidoPrevia.current = controlador
    try {
      const resultado = await redeApi.previa(
        inspecao.revisao,
        controlador.signal,
      )
      if (!controlador.signal.aborted) setPrevia(resultado)
    } catch (erro) {
      if (!controlador.signal.aborted)
        setErroPrevia(problemasDoErro(erro)[0].mensagem)
    }
  }, [])

  const aplicarInspecao = useCallback(
    async (resultado: InspecaoRede) => {
      setRede(resultado)
      setVersaoVisual((atual) => atual + 1)
      setConexao('online')
      setProblemas([])
      setMensagem('')
      await carregarPrevia(resultado)
    },
    [carregarPrevia],
  )

  const tratarFalha = useCallback((erro: unknown) => {
    const novos = problemasDoErro(erro)
    setConexao(novos.some((p) => p.campo === 'conexao') ? 'offline' : 'online')
    setProblemas(novos)
  }, [])

  async function consultar() {
    try {
      const resultado = await redeApi.inspecionar()
      await aplicarInspecao(resultado)
      return resultado
    } catch (erro) {
      tratarFalha(erro)
    }
  }

  useEffect(() => {
    const controlador = new AbortController()
    redeApi
      .inspecionar(controlador.signal)
      .then((resultado) => {
        if (!controlador.signal.aborted) return aplicarInspecao(resultado)
      })
      .catch((erro: unknown) => {
        if (!controlador.signal.aborted) tratarFalha(erro)
      })
    return () => {
      controlador.abort()
      pedidoPrevia.current?.abort()
    }
  }, [aplicarInspecao, tratarFalha])

  async function sincronizar() {
    if (emAndamento.current) return
    emAndamento.current = true
    setOperacao('atualizando')
    try {
      await consultar()
    } finally {
      emAndamento.current = false
      setOperacao(null)
    }
  }

  async function executar(
    tipo: NonNullable<typeof operacao>,
    acao: () => Promise<InspecaoRede>,
  ) {
    // O ref bloqueia uma segunda operação antes mesmo do próximo render.
    if (emAndamento.current) return
    emAndamento.current = true
    setOperacao(tipo)
    setProblemas([])
    setMensagem('')
    try {
      const resultado = await acao()
      setRede(resultado)
      if (tipo !== 'confirmando') setVersaoVisual((atual) => atual + 1)
      setConexao('online')
      setMensagem(
        tipo === 'confirmando'
          ? 'Rede confirmada para as próximas etapas.'
          : 'Rede carregada. Confira a estrutura e confirme para continuar.',
      )
      if (tipo !== 'confirmando') await carregarPrevia(resultado)
    } catch (erro) {
      const novos = problemasDoErro(erro)
      setProblemas(novos)
      if (novos.some((p) => p.campo === 'conexao')) setConexao('offline')
      if (redeDesatualizada(erro)) {
        const atual = await consultar()
        if (atual)
          setMensagem(
            atual.disponivel
              ? 'A rede mudou. A inspeção foi atualizada; confira os dados antes de confirmar.'
              : 'A rede não está mais disponível nesta sessão. Gere ou importe novamente.',
          )
      }
    } finally {
      emAndamento.current = false
      setOperacao(null)
    }
  }

  return {
    rede,
    versaoVisual,
    previa: previa?.revisao === rede?.revisao ? previa : null,
    conexao,
    operacao,
    problemas,
    erroPrevia,
    mensagem,
    sincronizar,
    limparProblemas: () => setProblemas([]),
    repetirPrevia: sincronizar,
    gerar: (campos: FormularioGeracao) =>
      executar('gerando', () => redeApi.gerar(campos)),
    importar: (contatos: File, individuos: File | null, delimitador: string) =>
      executar('importando', () =>
        redeApi.importar(contatos, individuos, delimitador),
      ),
    confirmar: () =>
      rede && executar('confirmando', () => redeApi.confirmar(rede.revisao)),
  }
}
