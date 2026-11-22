# Metodologia experimental da etapa 3

O [protocolo etapa3-base-v1](protocolo-etapa3-v1.json) define a campanha por delegação do usuário em 21/11/2026. O usuário informou que B ainda não havia definido os parâmetros e solicitou uma configuração-base. O [aviso dirigido a Luis](../../docs/implementacao/Aviso-IntegranteB-Etapa3.md) reúne os valores e cuidados de execução. A definição do protocolo não significa que a campanha foi realizada ou que houve aceite individual de cada integrante.

## Representação e condições comuns

A rede escolar adota a união dos contatos válidos de 22/01 a 08/03/2024, com 67 indivíduos, 1.325 arestas e peso 1, sem imputação de medições ausentes. Essa escolha conserva a [preparação e a caracterização verificadas](../redes_reais/escola_suica_2024/caracterizacao/README.md) e permite comparar topologias com a mesma interpretação binária de contato. As durações permanecem disponíveis para auditoria; não foram normalizadas ou usadas para estimar risco.

O [estudo de origem](https://doi.org/10.1038/s41467-025-66719-3) utiliza medições temporais e informações clínicas e ambientais. A campanha deste projeto investiga o comportamento de uma projeção estática sob SIR. Não reproduz as condições de transmissão do artigo. Um passo é uma unidade abstrata, sem equivalência definida com um dia de coleta.

| Condição | Definição |
| --- | --- |
| Transmissão | Modo intensidade; β = 0,005 e peso unitário |
| Recuperação | γ = 0,10 por passo |
| Iniciais | Sorteio de três IDs sem reposição; S(0) = 64, I(0) = 3 e R(0) = 0 |
| Parada | Extinção ou limite de 200 transições |
| Repetições | 100 por rede e condição |
| Cenários | Sem intervenção, aleatória e por grau |
| Intervenção principal | Desativação, fração 0,20 (13 pessoas), início t = 5 |
| Sementes base | Iniciais 10000; epidemia 20000; isolamento 30000 |

β e γ não foram calibrados para uma doença. Com grau médio 39,5522, a razão `β × grau_médio / γ` é aproximadamente 1,98. Ela foi usada somente para escolher uma escala inicial de transmissão em uma rede densa, sem afirmar que corresponde ao R₀ do modelo ou à reprodução de uma doença. A sensibilidade definida abaixo permite examinar a dependência dos resultados em relação a β. Cem repetições constituem o tamanho adotado para a descrição estocástica; não foram apresentadas como garantia de poder estatístico ou de erro máximo.

Os fluxos de iniciais, epidemia e isolamento são separados. Na repetição r, numerada de 1 a 100, as sementes efetivas recebem r − 1. As mesmas bases são usadas em todas as condições, e cada resultado deve conservar a configuração e os IDs resolvidos. A comparação não estabelece identidade entre pessoas reais e IDs das redes sintéticas.

## Controles e grade

Os controles terão N = 67 e peso 1. Para ER, `p = 1325 / [67 × 66 / 2] = 0,5992763455450023`, produzindo 1.325 arestas em esperança; as realizações podem diferir desse valor. Para BA, o gerador local começa com um núcleo completo de m + 1 indivíduos, e seu total é `M = mN − m(m + 1)/2`. O inteiro m = 24 minimiza a diferença para a escola e produz 1.308 arestas, 17 a menos (−1,28%). Não há igualdade exata de densidade.

Serão usadas dez realizações ER, com sementes 1000–1009, e dez BA, com sementes 2000–2009. Cada uma precisará ser gerada e caracterizada antes da execução. A população pequena e o m alto tornam o controle BA denso; sua distribuição deverá ser medida, sem pressupor uma lei de potência. A comparação inclui a variação observada de densidade e grau, além do mecanismo gerador.

| Bloco | Condições | Lotes com 100 repetições e três cenários |
| --- | --- | ---: |
| A | Escola e vinte controles; intervenção principal | 21 |
| B | Escola; redução de 50% dos pesos e exclusão; fração 0,20, início 5 | 2 |
| C | Escola; desativação; produto das frações 0,10/0,20/0,30 pelos inícios 0/5/10, excluindo a condição principal já incluída | 8 |
| D | Escola; β = 0,0025 e 0,01; demais condições principais | 2 |
| Total | Grade definida, ainda não executada | 33 |

O JSON enumera cada lote. São 9.900 trajetórias planejadas; referências reexecutadas em lotes diferentes deixam 8.900 condições únicas, considerando as sementes. A inferência sobre mecanismos, orçamento, início e sensibilidade dos blocos B–D fica restrita à escola. A campanha não pretende estimar todas as interações entre esses fatores.

## Análise, persistência e verificação

Os indicadores primários são pico proporcional e fração acumulada `[I(T)+R(T)]/N`. Também serão apresentados pico absoluto, primeiro instante do pico, recuperados finais, horizonte, duração de extinção e motivo de término. Para cada rede e condição, serão calculados média, desvio-padrão amostral e n presente/ausente, além das diferenças pareadas em relação ao cenário sem intervenção. Reduções relativas com referência zero serão ausentes.

A duração incluirá somente extinções observadas, com a proporção censurada ao lado. Todas as repetições permanecem na análise, inclusive as que terminam antes da intervenção. Para os controles, a variação das dez médias por modelo será separada da dispersão das repetições em cada rede; reexecuções de uma referência não aumentam a amostra. A estabilidade das médias e a dispersão deverão ser examinadas após a campanha; qualquer ampliação terá nova versão documentada.

Cada resposta JSON integral e seus manifestos devem ser salvos ao concluir o lote, junto aos CSVs e hashes. A memória da API conserva somente 32 resultados por sessão, insuficientes para os 33 lotes. Serão conferidos população, contagens, orçamento efetivo, pares, motivo de término e cobertura das 100 repetições. O relatório dos erros deverá preservar tentativas que falharem, sem substituição por zero ou por outra semente escolhida por seu resultado.

## Medição de desempenho

Serão medidas sequencialmente a escola, ER de semente 1000 e BA de semente 2000, no lote principal de 100 repetições. A rede estará carregada e confirmada antes do cronômetro. Cada operação terá cinco medições sem rastreamento, resumidas pela mediana de `perf_counter()`, uma execução adicional com `tracemalloc` e outra para cópias e assinatura. Essas execuções de instrumentação são separadas das 9.900 trajetórias da campanha epidemiológica.

O escopo inclui execução e montagem da resposta; exclui preparo da rede, HTTP e desenho. O pico de `tracemalloc` mede alocações adicionais Python e não RSS. As três redes devem usar a mesma máquina, sem pedidos concorrentes, registrando SO, CPU, RAM, Python, revisão e hashes efetivos. Esse registro será coletado na execução, sem usar o ambiente de testes como se já fosse uma medição.

A rotina `medir(operacao, 5)` do benchmark pode receber a operação com as redes acima. O CLI atual de `benchmark_simulacao.py` gera BA com m = 4; sua saída não deve ser atribuída a esta grade sem adaptar a entrada. A instrumentação ainda precisa ser preparada e executada.

## O que está concluído

A base escolar passou pelo importador, pelo serviço de carga, pela caracterização nativa e pelo [percurso no Chrome](../redes_reais/evidencias/interface-escola/README.md), incluindo Mapa, 3D, medidas e confirmação. O desenho possui limite de 1.200 arestas; a rede completa e suas contagens têm 1.325. A configuração-base e a grade estão definidas. Os controles sintéticos, a campanha, as medições e suas conclusões permanecem por executar.
