import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const [simulation, results] = await Promise.all([
  readFile(new URL('../src/pages/SimulationPage.tsx', import.meta.url), 'utf8'),
  readFile(new URL('../src/pages/ResultsPage.tsx', import.meta.url), 'utf8'),
])

test('SimulationPage monta o fluxo de ensaio em sua montagem principal', () => {
  assert.match(simulation, /export function SimulationPage/)
  assert.match(simulation, /<AppShell/)
  assert.match(simulation, /Modo de Experimento/)
  assert.match(simulation, /Execução Única/)
  assert.match(simulation, /Repetições/)
  assert.match(simulation, /Iniciar \/ Continuar Simulação/)
})

test('execução individual chama o backend e persiste o resultado individual', () => {
  assert.match(simulation, /const resultado = await executarSimulacao/)
  assert.match(simulation, /tipo: 'individual', resultado/)
  assert.match(simulation, /setResultadoIndividual\(resultado\)/)
})

test('execução sem configuração validada é bloqueada com diagnóstico', () => {
  assert.match(
    simulation,
    /Valide uma configuração na Tela 02 antes de executar o ensaio/,
  )
  assert.match(simulation, /setRequisicao\('falhou'\)/)
  assert.doesNotMatch(simulation, /await executarSimulacao[\s\S]*!configuracao/)
})

test('modo de repetições executa comparação e registra o lote', () => {
  assert.match(simulation, /modo === 'repeticoes'/)
  assert.match(simulation, /const lote = await executarComparacao/)
  assert.match(simulation, /tipo: 'comparacao'/)
  assert.match(simulation, /comparacao: lote/)
})

test('mudança de revisão ou contexto invalida ensaio e configuração', () => {
  assert.match(
    simulation,
    /O resultado foi invalidado porque a revisão ou o contexto da rede mudou/,
  )
  assert.match(simulation, /sessionStorage\.removeItem\(CHAVE_HISTORICO\)/)
  assert.match(simulation, /sessionStorage\.removeItem\(CHAVE_RESULTADO\)/)
  assert.match(
    results,
    /A configuração foi invalidada porque a revisão ou o contexto da rede mudou/,
  )
  assert.match(
    results,
    /O resultado foi invalidado porque a revisão ou o contexto da rede mudou/,
  )
})

test('ResultsPage monta consulta de resultados, métricas e histórico', () => {
  assert.match(results, /export function ResultsPage/)
  assert.match(results, /Trajetórias da epidemia/)
  assert.match(results, /Pico de infectados/)
  assert.match(results, /Histórico por passo/)
  assert.match(results, /Nenhum ensaio concluído/)
})

test('exportações de Resultados incluem CSV, agregado, JSON, SVG e PNG', () => {
  assert.match(results, /historico-ensaio\.csv/)
  assert.match(results, /trajetorias-comparacao\.csv/)
  assert.match(results, /metadados-ensaio\.json/)
  assert.match(results, /trajetorias-epidemia\.svg/)
  assert.match(results, /trajetorias-epidemia\.png/)
  assert.match(results, /exportarCsvAgregado/)
  assert.match(results, /exportarJson/)
  assert.match(results, /exportarSvg/)
  assert.match(results, /exportarPng/)
})
