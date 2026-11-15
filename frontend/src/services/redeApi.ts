import type {
  FormularioGeracao,
  IndividuoInspecionado,
  InspecaoRede,
  PaginaContatos,
  PaginaIndividuos,
  PreviaRede,
  ProblemaCarga,
} from '../types/rede'

export class ErroApi extends Error {
  readonly problemas: ProblemaCarga[]

  constructor(problemas: ProblemaCarga[]) {
    super(problemas.map((problema) => problema.mensagem).join(' '))
    this.name = 'ErroApi'
    this.problemas = problemas
  }
}

async function solicitar<T>(
  caminho: string,
  opcoes: RequestInit = {},
): Promise<T> {
  let resposta: Response
  try {
    resposta = await fetch(`/api/rede${caminho}`, {
      credentials: 'same-origin',
      ...opcoes,
    })
  } catch (erro) {
    if (erro instanceof DOMException && erro.name === 'AbortError') throw erro
    throw new ErroApi([
      {
        campo: 'conexao',
        mensagem:
          'Não foi possível conectar à API local. Verifique se o servidor Python está em execução e tente novamente.',
      },
    ])
  }
  const dados: unknown = await resposta.json().catch(() => null)
  if (!resposta.ok || !dados) {
    const recebidos =
      dados &&
      typeof dados === 'object' &&
      'problemas' in dados &&
      Array.isArray(dados.problemas)
        ? dados.problemas.filter(
            (problema): problema is ProblemaCarga =>
              problema !== null &&
              typeof problema === 'object' &&
              'campo' in problema &&
              typeof problema.campo === 'string' &&
              'mensagem' in problema &&
              typeof problema.mensagem === 'string',
          )
        : []
    const problemas = recebidos.length
      ? recebidos
      : [
          {
            campo: 'conexao',
            mensagem:
              'A API local não respondeu como esperado. Verifique o servidor Python e tente novamente.',
          },
        ]
    throw new ErroApi(problemas)
  }
  return dados as T
}

function enviar<T>(caminho: string, dados: unknown): Promise<T> {
  return solicitar<T>(caminho, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dados),
  })
}

async function codificarArquivo(arquivo: File) {
  if (arquivo.size > 5 * 1024 * 1024) {
    throw new ErroApi([
      {
        campo: 'arquivos',
        mensagem:
          'Cada arquivo deve ter até 5 MiB para envio pela interface local.',
      },
    ])
  }
  const conteudo_base64 = await new Promise<string>((resolve, reject) => {
    const leitor = new FileReader()
    leitor.onerror = () =>
      reject(
        new ErroApi([
          {
            campo: 'arquivos',
            mensagem: `Não foi possível ler ${arquivo.name}. Selecione o arquivo novamente.`,
          },
        ]),
      )
    leitor.onload = () => resolve(String(leitor.result).split(',')[1])
    leitor.readAsDataURL(arquivo)
  })
  return { nome: arquivo.name, conteudo_base64 }
}

export const redeApi = {
  inspecionar: (signal?: AbortSignal) =>
    solicitar<InspecaoRede>('', { signal }),
  gerar: (campos: FormularioGeracao) => enviar<InspecaoRede>('/gerar', campos),
  importar: async (
    contatos: File,
    individuos: File | null,
    delimitador: string,
  ) => {
    const dados = {
      arquivo_contatos: await codificarArquivo(contatos),
      arquivo_individuos: individuos
        ? await codificarArquivo(individuos)
        : null,
      delimitador,
    }
    if (new Blob([JSON.stringify(dados)]).size > 8 * 1024 * 1024) {
      throw new ErroApi([
        {
          campo: 'arquivos',
          mensagem:
            'Os dois arquivos juntos excedem o limite de envio de 8 MiB após codificação. Use arquivos menores.',
        },
      ])
    }
    return enviar<InspecaoRede>('/importar', dados)
  },
  confirmar: (revisao: number) =>
    enviar<InspecaoRede>('/confirmar', { revisao }),
  previa: (revisao: number, signal?: AbortSignal) =>
    solicitar<PreviaRede>(`/previa?revisao=${revisao}`, { signal }),
  individuo: (revisao: number, id: string, signal?: AbortSignal) =>
    solicitar<IndividuoInspecionado>(
      `/individuo?revisao=${revisao}&id=${encodeURIComponent(id)}`,
      { signal },
    ),
  individuos: (revisao: number, inicio: number, signal?: AbortSignal) =>
    solicitar<PaginaIndividuos>(
      `/individuos?revisao=${revisao}&inicio=${inicio}&limite=10`,
      { signal },
    ),
  contatos: (revisao: number, inicio: number, signal?: AbortSignal) =>
    solicitar<PaginaContatos>(
      `/contatos?revisao=${revisao}&inicio=${inicio}&limite=10`,
      { signal },
    ),
}

export function problemasDoErro(erro: unknown): ProblemaCarga[] {
  return erro instanceof ErroApi && erro.problemas.length
    ? erro.problemas
    : [
        {
          campo: 'formulario',
          mensagem: 'Não foi possível concluir a operação. Tente novamente.',
        },
      ]
}

export function redeDesatualizada(erro: unknown): boolean {
  return (
    erro instanceof ErroApi &&
    erro.problemas.some(
      (problema) => problema.campo === 'revisao' || problema.campo === 'rede',
    )
  )
}
