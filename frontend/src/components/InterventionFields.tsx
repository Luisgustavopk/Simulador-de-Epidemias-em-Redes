import type { ReactNode } from 'react'
import type { EntradaIntervencao } from '../services/configuracaoApi'
import type { ProblemaCarga } from '../types/rede'

export function InterventionFields({
  campos,
  alterar,
  disabled,
  problemas,
  quantidade,
  campoSemente,
}: {
  campos: EntradaIntervencao
  alterar: (campos: EntradaIntervencao) => void
  disabled: boolean
  problemas: ProblemaCarga[]
  quantidade: number | undefined
  campoSemente: ReactNode
}) {
  function erro(campo: string) {
    return problemas.filter((p) => p.campo === `intervencao.${campo}`)
  }
  function mensagem(campo: string) {
    const erros = erro(campo)
    return erros.length ? (
      <p id={`erro-intervencao-${campo}`} className="field-error">
        {erros.map((p) => p.mensagem).join(' ')}
      </p>
    ) : null
  }
  function acessibilidade(campo: string) {
    return {
      'aria-invalid': erro(campo).length > 0,
      'aria-describedby': erro(campo).length
        ? `erro-intervencao-${campo}`
        : undefined,
    }
  }
  return (
    <fieldset disabled={disabled}>
      <legend>Intervenção por isolamento</legend>
      <label className="intervention-toggle" htmlFor="intervencao-ativa">
        <input
          id="intervencao-ativa"
          type="checkbox"
          checked={campos.ativa}
          onChange={(e) => alterar({ ...campos, ativa: e.target.checked })}
        />
        Incluir intervenção neste cenário
      </label>
      {!campos.ativa ? (
        <p>Sem intervenção: nenhuma pessoa será selecionada para isolamento.</p>
      ) : (
        <>
          <p>
            A estratégia escolhe as pessoas. O mecanismo define o efeito sobre
            seus contatos.
          </p>
          <div className="fields-grid">
            <div className="field">
              <label htmlFor="intervencao-estrategia">
                Estratégia de seleção
              </label>
              <select
                id="intervencao-estrategia"
                value={campos.estrategia}
                onChange={(e) =>
                  alterar({
                    ...campos,
                    estrategia: e.target
                      .value as EntradaIntervencao['estrategia'],
                  })
                }
                {...acessibilidade('estrategia')}
              >
                <option value="aleatoria">Aleatória, sem reposição</option>
                <option value="grau">Por grau: mais contatos primeiro</option>
              </select>
              {mensagem('estrategia')}
            </div>
            <div className="field">
              <label htmlFor="intervencao-fracao">
                Fração de pessoas a isolar
              </label>
              <input
                id="intervencao-fracao"
                value={campos.fracao}
                onChange={(e) => alterar({ ...campos, fracao: e.target.value })}
                {...acessibilidade('fracao')}
              />
              {mensagem('fracao')}
              <p>De 0 a 1. Por exemplo, 0,25 corresponde a 25% da população.</p>
            </div>
            <div className="field">
              <label htmlFor="intervencao-quantidade">Pessoas a isolar</label>
              <output id="intervencao-quantidade" aria-live="polite">
                {quantidade ?? 'Calcule ao validar'}
              </output>
              <p>
                A quantidade vem da fração, arredondada para baixo. Pessoas sem
                contatos também são elegíveis.
              </p>
            </div>
            <div className="field">
              <label htmlFor="intervencao-inicio">
                Dia de início da intervenção
              </label>
              <input
                id="intervencao-inicio"
                value={campos.inicio}
                onChange={(e) => alterar({ ...campos, inicio: e.target.value })}
                {...acessibilidade('inicio')}
              />
              {mensagem('inicio')}
              <p>
                Dia 0: antes da primeira atualização. Use um dia menor que o
                limite de passos.
              </p>
            </div>
            <div className="field">
              <label htmlFor="intervencao-mecanismo">
                Mecanismo sobre os contatos
              </label>
              <select
                id="intervencao-mecanismo"
                value={campos.mecanismo}
                onChange={(e) =>
                  alterar({
                    ...campos,
                    mecanismo: e.target
                      .value as EntradaIntervencao['mecanismo'],
                  })
                }
                {...acessibilidade('mecanismo')}
              >
                <option value="desativacao">Desativação dos contatos</option>
                <option value="reducao">Redução da intensidade</option>
                <option value="exclusao">Exclusão dos contatos</option>
              </select>
              {mensagem('mecanismo')}
              <p>Os três mecanismos preservam as pessoas e seus estados SIR.</p>
            </div>
            {campos.mecanismo === 'reducao' && (
              <div className="field">
                <label htmlFor="intervencao-reducao">
                  Fração de redução dos pesos
                </label>
                <input
                  id="intervencao-reducao"
                  value={campos.reducao}
                  onChange={(e) =>
                    alterar({ ...campos, reducao: e.target.value })
                  }
                  {...acessibilidade('reducao')}
                />
                {mensagem('reducao')}
                <p>
                  0 mantém a intensidade; 1 remove toda a intensidade dos
                  contatos afetados.
                </p>
              </div>
            )}
          </div>
          <p>
            O grau usa a rede original; empates seguem o ID crescente. A semente
            controla somente a seleção aleatória.
          </p>
        </>
      )}
      <div className="fields-grid">{campoSemente}</div>
      <p>A semente não é consumida quando não há seleção aleatória.</p>
      <p>
        Esta tela configura uma intervenção única. Sua aplicação no dia
        escolhido depende da integração da execução.
      </p>
    </fieldset>
  )
}
