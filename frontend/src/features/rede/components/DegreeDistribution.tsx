import type { ResumoEstrutural } from '../../../types/rede'

export function DegreeDistribution({
  resumo,
}: {
  resumo: ResumoEstrutural | null
}) {
  const dados = resumo?.distribuicao_graus ?? []
  const maiorGrau = resumo?.grau_maximo ?? 0
  // Agrupamento apenas para desenho; as frequências são calculadas no Python.
  const tamanhoFaixa = Math.max(1, Math.ceil((maiorGrau + 1) / 28))
  const faixas = new Map<number, number>()
  for (const item of dados) {
    const faixa = Math.floor(item.grau / tamanhoFaixa) * tamanhoFaixa
    faixas.set(faixa, (faixas.get(faixa) ?? 0) + item.quantidade)
  }
  const frequenciaMaxima = Math.max(
    2,
    Math.ceil(Math.max(1, ...faixas.values()) / 2) * 2,
  )
  const quantidadeFaixas = Math.floor(maiorGrau / tamanhoFaixa) + 1
  return (
    <figure className="degree-figure">
      <figcaption>Distribuição de grau</figcaption>
      <p>Como os contatos se distribuem pela população.</p>
      {resumo ? (
        <svg
          viewBox="0 0 520 218"
          role="img"
          aria-label={`Distribuição de graus de ${resumo.numero_individuos} indivíduos. Grau máximo ${maiorGrau}. ${resumo.individuos_sem_contatos} indivíduos sem contatos.`}
        >
          {[0, 0.5, 1].map((fracao) => (
            <g key={fracao}>
              <line
                x1="45"
                x2="508"
                y1={175 - fracao * 145}
                y2={175 - fracao * 145}
                className="chart-grid"
              />
              <text x="35" y={179 - fracao * 145} textAnchor="end">
                {Math.round(frequenciaMaxima * fracao).toLocaleString('pt-BR')}
              </text>
            </g>
          ))}
          {[...faixas.entries()].map(([faixa, quantidade]) => (
            <rect
              key={faixa}
              className="histogram-bar"
              x={48 + (faixa / tamanhoFaixa / quantidadeFaixas) * 455}
              y={175 - (quantidade / frequenciaMaxima) * 145}
              width={Math.max(1, 455 / quantidadeFaixas - 2)}
              height={(quantidade / frequenciaMaxima) * 145}
              rx="1"
            >
              <title>{`Grau ${faixa}${tamanhoFaixa > 1 ? `–${Math.min(maiorGrau, faixa + tamanhoFaixa - 1)}` : ''}: ${quantidade} indivíduos`}</title>
            </rect>
          ))}
          <text x="48" y="196">
            0
          </text>
          <text x="505" y="196" textAnchor="end">
            {maiorGrau}
          </text>
          <text x="277" y="216" textAnchor="middle">
            Número de contatos · grau
          </text>
        </svg>
      ) : (
        <div className="chart-empty">
          <div className="chart-empty-axis" />
          <p>
            A distribuição aparece depois
            <br />
            de carregar uma rede.
          </p>
        </div>
      )}
      {resumo && (
        <p className="chart-caption">
          {resumo.individuos_sem_contatos.toLocaleString('pt-BR')} indivíduo(s)
          sem contatos
          {tamanhoFaixa > 1
            ? ` · barras agrupadas a cada ${tamanhoFaixa} graus`
            : ' · uma barra por grau'}
          .
        </p>
      )}
    </figure>
  )
}
