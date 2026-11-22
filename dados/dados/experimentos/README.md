# Metodologia experimental da etapa 3

Os dados e o protocolo ficam em `dados/dados/`, conforme a reorganização de 22/11/2026. Os scripts e os links desta documentação já usam essa localização.

O [protocolo etapa3-base-v1](protocolo-etapa3-v1.json) define a campanha por delegação do usuário em 21/11/2026. O usuário informou que B ainda não havia definido os parâmetros e solicitou uma configuração-base. O [aviso dirigido a Luis](../../../docs/implementacao/Aviso-IntegranteB-Etapa3.md) reúne os valores e cuidados de execução. O protocolo foi definido antes das execuções e permanece preservado, inclusive seus indicadores históricos de atividade pendente. O [estado atual](estado-etapa3.json) registra o avanço; não houve registro de aceite individual de cada integrante.

**Campanha concluída em 22/11/2026:** os [vinte controles](../redes_sinteticas/controles-etapa3-v1/README.md), o [bloco A](topologia-v1/README.md), os [blocos B/C/D](intervencoes-v1/README.md) e o [benchmark das três redes](desempenho-v1/README.md) estão disponíveis. São **33 lotes, 9.900 trajetórias e 635.259 registros**, com uma censura, além das chamadas separadas de reprodução e instrumentação. O protocolo histórico permanece intacto; o estado atual registra a conclusão.

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

Os controles gerados têm N = 67 e peso 1. Para ER, `p = 1325 / [67 × 66 / 2] = 0,5992763455450023`, produzindo 1.325 arestas em esperança; as realizações podem diferir desse valor. Para BA, o gerador local começa com um núcleo completo de m + 1 indivíduos, e seu total é `M = mN − m(m + 1)/2`. O inteiro m = 24 minimiza a diferença para a escola e produz 1.308 arestas, 17 a menos (−1,28%). Não há igualdade exata de densidade.

Foram usadas dez realizações ER, com sementes 1000–1009, e dez BA, com sementes 2000–2009. Todas foram exportadas, reimportadas e caracterizadas antes da execução. Os valores realizados estão na [tabela das redes](topologia-v1/caracterizacao_redes.csv). A população pequena e o m alto tornam o controle BA denso; sua distribuição foi medida, sem pressupor uma lei de potência. A comparação inclui a variação observada de densidade e grau, além do mecanismo gerador.

| Bloco | Condições | Lotes com 100 repetições e três cenários |
| --- | --- | ---: |
| A | Escola e vinte controles; intervenção principal | 21 |
| B | Escola; redução de 50% dos pesos e exclusão; fração 0,20, início 5 | 2 |
| C | Escola; desativação; produto das frações 0,10/0,20/0,30 pelos inícios 0/5/10, excluindo a condição principal já incluída | 8 |
| D | Escola; β = 0,0025 e 0,01; demais condições principais | 2 |
| Total | Grade executada; A/B/C/D concluídos | 33 |

O JSON enumera cada lote. Foram executadas 9.900 trajetórias; referências reexecutadas em lotes diferentes deixam 8.900 condições únicas, considerando as sementes. A inferência sobre mecanismos, orçamento, início e sensibilidade dos blocos B–D fica restrita à escola. A campanha não pretende estimar todas as interações entre esses fatores.

## Análise, persistência e verificação

Os indicadores primários são pico proporcional e fração acumulada `[I(T)+R(T)]/N`. Também são apresentados pico absoluto, primeiro instante do pico, recuperados finais, horizonte, duração de extinção e motivo de término. Para cada rede e condição, foram calculados média, desvio-padrão amostral e n presente/ausente, além das diferenças pareadas em relação ao cenário sem intervenção. Reduções relativas com referência zero ficam ausentes.

A duração inclui somente extinções observadas, com a proporção censurada ao lado. Todas as repetições permanecem na análise, inclusive as que terminam antes da intervenção. Para os controles, a variação das dez médias por modelo é separada da dispersão das repetições em cada rede; reexecuções de uma referência não aumentam a amostra. O bloco A preserva ambas as dispersões e descreve os resultados sem teste de significância. Qualquer ampliação terá nova versão documentada.

Cada resposta JSON integral e seus manifestos devem ser salvos ao concluir o lote, junto aos CSVs e hashes. A memória da API conserva somente 32 resultados por sessão, insuficientes para os 33 lotes. Foram conferidos população, contagens, orçamento efetivo, pares, motivo de término e cobertura das 100 repetições. O relatório dos erros deverá preservar tentativas que falharem, sem substituição por zero ou por outra semente escolhida por seu resultado.

## Medição de desempenho

Foram medidas sequencialmente escola, ER 1000 e BA 2000, na configuração-base com 100 repetições. As redes estavam carregadas e confirmadas antes do cronômetro. Por rede, foram cinco chamadas sem rastreamento, uma com `tracemalloc` e outra para contar cópias. As sete assinaturas coincidiram com o lote correspondente de A. Essas chamadas não aumentam a amostra epidemiológica.

O [benchmark concluído](desempenho-v1/README.md) conserva os 15 tempos brutos, ambiente, receitas, hashes e limites de medição. As medianas foram 4,090/4,129/4,068 s por lote de 300 trajetórias, com 301 cópias por chamada. O pico adicional de alocações Python foi 6,35/6,65/6,32 MiB; não é RSS. Importação/geração, confirmação, HTTP e navegador ficam fora do escopo.

O executor específico é `scripts/benchmark_etapa3.py`. O CLI antigo `benchmark_simulacao.py` continua gerando BA com m=4; sua saída não pertence a esta grade. As três redes da medição têm N=67 e densidades próximas, sem demonstração de escalabilidade.

## O que está concluído

A escola foi importada, caracterizada e conferida no navegador; vinte controles foram gerados, caracterizados e reproduzidos. A/B/C/D concluíram 33 lotes, com resultados completos, análises e gráficos. Os blocos adicionais abrangem somente a escola. O benchmark das três redes também está concluído; tempos operacionais de execução permanecem distintos dessas cronometragens.

## Fechamento da campanha

Os resultados adicionais e o benchmark foram executados após pedido explícito do usuário. As condições e sementes previstas foram mantidas. O relatório SBC consolida os blocos e as medições; os arquivos compactados de A e de B/C/D, acompanhados de hashes, permitem restaurar as exportações sem recalcular o SIR. As verificações estão nos respectivos diretórios. A receita histórica conserva seus indicadores anteriores à execução; consulte `estado-etapa3.json` para a situação atual.

A [verificação de fechamento](verificacao-fechamento.json) reúne os totais, a preservação dos hashes, os testes e a conferência do PDF e do ZIP locais.
