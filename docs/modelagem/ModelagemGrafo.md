# Modelagem do grafo

Este documento descreve a modelagem vigente da rede. As [histórias de usuário](../requisitos/HistoriasDeUsuario.md) e os requisitos continuam sendo a base. As decisões complementares sobre duração do isolamento, pesos normalizados e composição da redução foram autorizadas pelo usuário em **15/11/2026** e registradas em [Mecanismos de isolamento](../implementacao/Isolamento.md).

A [versão histórica](ModelagemGrafo-historico-2026-11-15.md) preserva o texto anterior para rastrear as divergências. A entrada diária por q, liberação na recuperação e pesos acima de 1 dessa versão foram substituídos pelas regras abaixo.

## Estrutura e responsabilidades

O grafo é simples, não direcionado e ponderado, representado por listas de adjacência indexadas pelo ID do vizinho. Cada contato é compartilhado pelas duas adjacências e contado uma vez. Não há laços nem contatos duplicados, inclusive invertidos. A implementação utiliza estruturas nativas de Python.

- `Individuo`: ID inteiro estável, estado SIR, condição de isolamento e instante da primeira infecção. IDs zero e negativos são válidos; booleanos não são IDs.
- `Contato`: extremos estáveis, intensidade normalizada `peso` e disponibilidade explícita `ativa`. As propriedades são somente leitura para consumidores; a rede controla suas alterações.
- `RedeContatos`: cadastro epidemiológico permanente e estrutura dos contatos. Mantém pessoas sem contatos, inclusive após uma intervenção de exclusão.

As APIs, validações e custos estão em [Estrutura da rede](../implementacao/EstruturaGrafo.md). A topologia permanece estática entre intervenções; a exclusão programada pode remover contatos. Não há dinâmica demográfica implementada.

## Estado epidemiológico e população

Cada pessoa está em exatamente um estado SIR: S, I ou R. São permitidas somente S → I e I → R, sem reinfecção. R significa recuperação/remoção epidemiológica, sem remoção automática de contatos ou de pessoas do cadastro.

A construção começa em S, não isolado e sem instante de infecção. A configuração deve aplicar `infectar(0)` aos infectados iniciais. Novas infecções devem receber t+1; a recuperação preserva o instante da infecção.

Isolamento é uma dimensão separada, aplicável a S, I ou R. Os isolados também pertencem a um dos compartimentos. O cadastro não perde pessoas por intervenção, mantendo **S(t) + I(t) + R(t) = N₀**. Um infectado desconectado continua elegível para recuperação.

## Pesos e regra prevista de transmissão

O peso representa intensidade normalizada finita em **[0, 1]**. A importação e os geradores adotam peso 1 quando aplicável como padrão. Peso zero mantém o contato na estrutura e fornece exposição nula. Não há interpretação implementada de intensidade acima de 1 ou de peso como probabilidade pronta.

Para integração do futuro motor, adota-se `p_uv = β × peso_atual` em contatos disponíveis; em contatos desativados, `p_uv = 0`. β é uma probabilidade por passo em [0, 1]. O peso atual já incorpora a redução da intervenção, sem aplicar o fator novamente. Essa é uma decisão operacional complementar, sem atribuir a fórmula literalmente à US03.

Para vários vizinhos infectados, a hipótese complementar de independência condicional produz `P_v = 1 − produto(1 − p_uv)`, com P_v = 0 sem exposições. O futuro motor deverá sortear uma vez por suscetível e manter as probabilidades em [0, 1]. As equações estão especificadas; o motor probabilístico ainda não está implementado.

## Intervenção de isolamento

A configuração identifica estratégia, mecanismo, orçamento de pessoas e passo de início. A seleção aleatória deve usar semente; a seleção por grau deve usar a rede de referência antes de modificar contatos, com desempate declarado. A seleção, o desempate e o agendamento pertencem às próximas etapas.

A política adotada tem uma aplicação no início de `t_int`, antes das decisões epidemiológicas do passo, com alvos fixos e únicos. Pode selecionar S, I ou R. O orçamento limita pessoas, não arestas; zero não seleciona ninguém. O isolamento persiste até o fim da execução, inclusive após recuperação, sem reposição de alvos ou liberação automática no encerramento.

| Mecanismo | Efeito |
| --- | --- |
| Desativação | Torna os contatos incidentes indisponíveis, preservando pesos e adjacências. |
| Redução | Aplica `peso_apos = peso_antes × (1 − r)`, com r em [0, 1], uma vez por contato abrangido. Preserva disponibilidade anterior e topologia. |
| Exclusão | Remove os contatos incidentes das duas adjacências. Mantém a pessoa cadastrada, com grau zero e o mesmo estado epidemiológico. |

Dois extremos selecionados não duplicam a redução. Um contato já desativado permanece indisponível. A redução parcial permite transmissão quando sua probabilidade efetiva for positiva; não há filtro universal de transmissão pelo booleano de isolamento.

`Individuo.isolar()` apenas marca a pessoa. `Contato.ativa` é independente dessa marca. A função `aplicar_isolamento()` coordena os efeitos, valida a seleção inteira antes de alterar a rede e rejeita isolamento prévio, conforme o protocolo de intervenção única. Redes de cenários diferentes são cópias independentes da mesma referência.

## Atualização síncrona e encerramento

O motor e o controlador ainda serão implementados. Seu contrato previsto é:

1. Validar todas as entradas antes de executar e registrar a condição inicial no dia 0.
2. No início de cada passo t, aplicar a intervenção se este for `t_int`. Com início em zero, aplicar antes da primeira atualização epidemiológica.
3. Calcular infecção e recuperação usando os estados epidemiológicos em t e os contatos disponíveis após a intervenção. Guardar os valores de estado, pois referências aos objetos mutáveis não constituem uma fotografia.
4. Avaliar recuperação com γ em [0, 1] para todos os infectados em t, incluindo isolados e pessoas sem contatos.
5. Aplicar em conjunto S → I e I → R em t+1, preservando isolamento. Recém-infectados não transmitem nem se recuperam no mesmo passo; um infectado que recuperará ao final ainda pode transmitir no passo se houver contato permitido.
6. Registrar S, I, R e isolados e verificar extinção ou limite de passos. O limite não transforma infectados em R. Não acrescentar liberação ou restauração de contatos no encerramento.

Um passo equivale a um dia do modelo, sem calibração automática com uma doença real. As sementes da geração, seleção e dinâmica devem ser controladas e associadas à configuração completa. A execução deve terminar no dia 0 se não houver infectados, sem aplicar uma atualização epidemiológica.

## Análise estrutural e situação da implementação

BFS, DFS, componentes e grau consideram contatos cadastrados, inclusive peso zero e desativados. Desativação e redução preservam essas métricas; exclusão altera a topologia. Pessoas desconectadas continuam no denominador do grau médio e formam componentes unitárias. Consulte [Análise estrutural](../implementacao/AnaliseEstrutural.md).

Estão implementados domínio, CSV, geração ER/BA, cópias, análise estrutural e aplicação dos três mecanismos. Permanecem pendentes motor, seleção aleatória/por grau, agendamento, validação centralizada, comparações e histórico completo. Consulte a [revisão técnica](../implementacao/RevisaoTecnica.md) para evidências e limites.

## Referências do projeto

As fontes de estudo estão em [REFERENCIAS.md](../referencias/REFERENCIAS.md). As decisões de implementação e suas limitações estão identificadas separadamente das fontes de estudo.
