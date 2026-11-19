import { readFile } from 'node:fs/promises'
import ts from 'typescript'

function modulo(fonte, importacoes) {
  const { outputText } = ts.transpileModule(fonte, {
    compilerOptions: {
      target: ts.ScriptTarget.ES2023,
      module: ts.ModuleKind.ESNext,
    },
    transformers: {
      before: [
        ({ factory }) =>
          (arquivo) =>
            factory.updateSourceFile(
              arquivo,
              arquivo.statements.map((declaracao) => {
                if (!ts.isImportDeclaration(declaracao)) return declaracao
                const url = importacoes.get(declaracao.moduleSpecifier.text)
                if (!url) return declaracao
                return factory.updateImportDeclaration(
                  declaracao,
                  declaracao.modifiers,
                  declaracao.importClause,
                  factory.createStringLiteral(url),
                  declaracao.attributes,
                )
              }),
            ),
      ],
    },
  })
  return `data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`
}

export async function carregarConfiguracaoApi() {
  const [fonteConfiguracao, fonteRede] = await Promise.all(
    ['configuracaoApi', 'redeApi'].map((nome) =>
      readFile(new URL(`../src/services/${nome}.ts`, import.meta.url), 'utf8'),
    ),
  )
  const rede = modulo(fonteRede, new Map())
  return import(modulo(fonteConfiguracao, new Map([['./redeApi', rede]])))
}
