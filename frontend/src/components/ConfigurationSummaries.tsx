import type {
  ComparacaoValidada,
  ConfiguracaoValidada,
} from '../services/configuracaoApi'

const rotulosCenarios = {
  sem_intervencao: 'Sem intervenção',
  aleatoria: 'Seleção aleatória',
  grau: 'Seleção por grau',
}

const rotulosMecanismos = {
  desativacao: 'Desativação dos contatos',
  reducao: 'Redução da intensidade',
  exclusao: 'Exclusão dos contatos',
}

export function ResumoComparacao({
  resultado,
}: {
  resultado: ComparacaoValidada
}) {
  return (
    <section
      className="configuration-summary"
      aria-label="Comparação validada"
      aria-live="polite"
    >
      <h2>Comparação validada</h2>
      <p>
        {resultado.repeticoes} repetições · revisão {resultado.revisao_rede} ·{' '}
        {resultado.populacao} indivíduos
      </p>
      <ul>
        {resultado.cenarios.map((cenario) => (
          <li key={cenario}>{rotulosCenarios[cenario]}</li>
        ))}
      </ul>
      <p>
        Orçamento por intervenção: {resultado.quantidade_isolados} de{' '}
        {resultado.populacao}. Fração de isolamento:{' '}
        {resultado.intervencao.fracao}. Dia {resultado.intervencao.inicio} ·{' '}
        {rotulosMecanismos[resultado.intervencao.mecanismo]}.
        {resultado.intervencao.reducao !== null && (
          <> Fração de redução: {resultado.intervencao.reducao}.</>
        )}
      </p>
      <p>
        {resultado.modo_iniciais === 'sorteio'
          ? `Infectados iniciais por sorteio em cada repetição: ${resultado.quantidade_infectados}.`
          : `Infectados iniciais por IDs informados: ${resultado.quantidade_infectados}.`}
      </p>
      <p>
        Sementes base — epidemia: {resultado.sementes_base.epidemia}; iniciais:{' '}
        {resultado.sementes_base.iniciais}; isolamento:{' '}
        {resultado.sementes_base.isolamento}.
      </p>
      <p>Limite: {resultado.limite_passos} passos.</p>
      <p id="execucao-comparacao-orientacao">
        Revise os três cenários na Tela 03. O cálculo começa ao selecionar
        Iniciar / Continuar Simulação.
      </p>
      <a
        className="button-primary"
        href="#simulacao"
        aria-describedby="execucao-comparacao-orientacao"
      >
        Preparar comparação na Tela 03
      </a>
    </section>
  )
}

export function ResumoConfiguracao({
  resultado,
}: {
  resultado: ConfiguracaoValidada
}) {
  const { configuracao, populacao } = resultado
  const { intervencao } = configuracao
  return (
    <section
      className="configuration-summary"
      aria-label="Configuração validada"
      aria-live="polite"
    >
      <h2>Configuração validada</h2>
      <p>
        Revisão {configuracao.revisao_rede}; população {populacao}.
      </p>
      <p>
        Modo {configuracao.modo_peso}; β {configuracao.beta ?? 'não aplicável'};
        γ {configuracao.gamma}.
      </p>
      <p>
        IDs iniciais:{' '}
        {configuracao.ids_infectados_iniciais.join(', ') || 'nenhum'}.
      </p>
      <p>Limite: {configuracao.limite_passos} passos.</p>
      <p>
        Sementes — epidemia: {configuracao.semente_epidemia}; iniciais:{' '}
        {configuracao.semente_iniciais}; isolamento:{' '}
        {configuracao.semente_isolamento}.
      </p>
      {intervencao ? (
        <p>
          Intervenção:{' '}
          {intervencao.estrategia === 'grau' ? 'por grau' : 'aleatória'}; fração{' '}
          {intervencao.fracao}; {intervencao.quantidade_isolados}{' '}
          {intervencao.quantidade_isolados === 1 ? 'pessoa' : 'pessoas'}; dia{' '}
          {intervencao.inicio}; mecanismo{' '}
          {rotulosMecanismos[intervencao.mecanismo]}.
          {intervencao.reducao !== null && (
            <> Redução: {intervencao.reducao}.</>
          )}
        </p>
      ) : (
        <p>Sem intervenção neste cenário.</p>
      )}
      <p>
        A rede de referência continua intacta. Revise o ensaio na Tela 03 e
        selecione Iniciar / Continuar Simulação para executar.
      </p>
      <a className="button-primary" href="#simulacao">
        Preparar execução única na Tela 03
      </a>
    </section>
  )
}
