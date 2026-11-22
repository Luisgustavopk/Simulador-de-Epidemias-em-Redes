# Experimentos de topologia — bloco A

**Concluído em 22/11/2026:** escola, dez ER e dez BA; 100 repetições dos três cenários por rede. Foram salvos **21 lotes, 6.300 trajetórias e 408.914 registros**. Uma trajetória foi censurada no limite; as demais 6.299 terminaram por extinção.

A execução segue o [protocolo etapa3-base-v1](../protocolo-etapa3-v1.json), definido antes desta bateria. O [snapshot usado](protocolo-utilizado.json) conserva o documento tal como foi recebido, inclusive os indicadores históricos de execução pendente. O [estado atual da etapa](../estado-etapa3.json) registra o bloco A concluído e os blocos B/C/D e o benchmark pendentes. O escopo desta entrega não completa os 33 lotes planejados.

## Condições executadas

Todas as redes têm 67 indivíduos e peso 1, no modo intensidade. Usaram-se **β = 0,005; γ = 0,10; três iniciais sorteados sem reposição; até 200 transições; 100 repetições** por rede. A desativação começa em **t = 5** e seleciona **13 pessoas** (`floor(0,20 × 67)`) nos cenários aleatório e por grau. A seleção inclui S/I/R, sem substituição ou liberação. Extinções anteriores à intervenção foram mantidas.

As sementes base são iniciais **10000**, epidemia **20000** e isolamento **30000**. A repetição r, de 1 a 100, usa `base + r − 1`. Os cenários de cada repetição compartilham iniciais e sementes; o mesmo ID em redes diferentes não identifica a mesma pessoa. Depois que as trajetórias divergem, uma semente igual não garante que cada sorteio corresponda ao mesmo indivíduo.

Os [controles](../../redes_sinteticas/controles-etapa3-v1/README.md) usam ER com `p = 1325/2211`, sementes 1000–1009; BA com `m = 24`, núcleo de 25 indivíduos, sementes 2000–2009. A [caracterização das 21 redes](caracterizacao_redes.csv) contém parâmetros estruturais realizados. Todas são conexas. O desvio populacional dos graus é 9,56 na escola, 3,50–4,58 nas ER e 9,69–10,74 nas BA.

## Resultados descritivos

Valores em **percentual da população: média ± desvio-padrão**. Na escola, o desvio é amostral entre as 100 repetições sobre **uma rede fixa**. Em ER/BA, cada célula resume as **dez médias de rede**, cada uma calculada com 100 repetições; o desvio é amostral **entre essas dez médias**. Esses desvios têm níveis distintos e não podem ser comparados como se estimassem a mesma variabilidade. A dispersão de cada conjunto de 100 repetições está no CSV por rede.

| Rede/modelo | Cenário | Pico proporcional (%) | Fração acumulada (%) |
| --- | --- | ---: | ---: |
| Escola | Sem intervenção | 23,12 ± 8,04 | 72,13 ± 22,05 |
| Escola | Aleatória | 15,46 ± 6,47 | 44,06 ± 21,05 |
| Escola | Por grau | 12,37 ± 5,36 | 33,40 ± 17,14 |
| ER | Sem intervenção | 22,26 ± 1,13 | 70,77 ± 1,91 |
| ER | Aleatória | 14,79 ± 0,72 | 43,71 ± 2,82 |
| ER | Por grau | 13,79 ± 0,65 | 40,64 ± 1,92 |
| BA | Sem intervenção | 22,21 ± 0,56 | 69,22 ± 0,82 |
| BA | Aleatória | 14,91 ± 0,58 | 43,79 ± 1,23 |
| BA | Por grau | 12,39 ± 0,50 | 34,16 ± 1,40 |

A fração acumulada usa `[I(T)+R(T)]/67` e inclui as três infecções iniciais. A média dos picos individuais difere do pico da curva média: cada repetição pode atingir seu máximo em outro instante.

Sem intervenção, as médias de pico foram próximas: **23,12% na escola, 22,26% em ER e 22,21% em BA**. As frações acumuladas médias foram 72,13%, 70,77% e 69,22%. Na condição testada, a seleção por grau apresentou médias menores de pico e fração acumulada do que a aleatória nas três famílias. A diferença de fração acumulada entre aleatória e grau foi **10,66 pontos percentuais na escola, 3,07 em ER e 9,64 em BA**. Na escola, a diferença entre referência e grau foi 38,73 pontos percentuais.

A menor diferença entre as duas seleções em ER acompanha sua menor dispersão de graus. Isso é uma interpretação compatível com os resultados, sem isolar causalmente o grau: outras propriedades estruturais também podem influir, a escola tem uma só realização observada e as densidades diferem. Este bloco não calculou comunidades. BA tem 1,28% menos arestas que a escola; ER varia de 1.291 a 1.360. Não foi feito teste de significância, equivalência ou calibração clínica. As médias não significam vantagem em todas as repetições; os sinais favoráveis, empates e diferenças desfavoráveis foram preservados em [analise.json](analise.json).

A única censura ocorreu em **ER 1007, sem intervenção, repetição 33**: I(200) = 1 e R(200) = 53. Sua duração de extinção permanece ausente. Representa **1/1.000** trajetórias sem intervenção de ER e **1/6.300** do bloco inteiro. O horizonte é 200; não foi atribuída extinção artificial. Médias de duração usam apenas extinções observadas; os campos `n` e `ausentes` permitem conferi-las.

As curvas médias estão em [PDF vetorial](figuras/curvas-topologias.pdf) e [SVG](figuras/curvas-topologias.svg). Cada painel compara as três famílias em um cenário, na mesma escala. O traço pontilhado marca t = 5. Após extinção, o último estado serve somente ao alinhamento visual; o histórico original não foi prolongado. As curvas não são estados reais de indivíduos nem reconstituem uma cadeia de transmissão.

## Arquivos e verificação

O pacote dos lotes completos, os resumos, as figuras finais e os registros de origem ficam disponíveis para versionamento. Os 21 lotes e seus 21 hashes são guardados em dois arquivos: um ZIP e seu SHA-256. A pasta `lotes/` extraída, as exportações extensas e as caracterizações individuais permanecem no disco, mas estão no `.gitignore`. Após clonar o repositório, use o comando de restauração abaixo para recriá-las.

| Arquivo | Conteúdo | Destino no Git |
| --- | --- | --- |
| [lotes-topologia-v1.zip](lotes-topologia-v1.zip) | 21 JSONs integrais comprimidos e seus 21 hashes, com pedidos, manifestos efetivos, IDs, sementes, métricas e históricos | Preservar |
| [lotes-topologia-v1.zip.sha256](lotes-topologia-v1.zip.sha256) | SHA-256 do pacote completo | Preservar |
| `lotes/` | Os mesmos 42 arquivos, extraídos para uso local | Ignorado; restaurável pelo pacote |
| `metricas.csv` | Uma linha por trajetória, com sementes efetivas e motivo de término | Ignorado; regenerável |
| `historicos.csv.gz` | Os 408.914 registros S/I/R/Q; leitura direta por `gzip` ou descompactação | Ignorado; regenerável |
| [resumo_por_rede.csv](resumo_por_rede.csv) | Média e desvio amostral das repetições, com observações presentes e ausentes | Preservar |
| [resumo_por_modelo.csv](resumo_por_modelo.csv) | Agregação das médias de rede e identificação do nível do desvio | Preservar |
| [caracterizacao_redes.csv](caracterizacao_redes.csv) | Indicadores estruturais consolidados das 21 redes | Preservar |
| `diferencas_pareadas.csv` | Referência menos intervenção e redução relativa por repetição e indicador primário; diferenças negativas preservadas | Ignorado; regenerável |
| `curvas_medias_por_rede.csv` | I médio por instante em cada rede/cenário, com n observado | Ignorado; regenerável |
| `caracterizacao/` | Graus, distribuição e componentes das 21 redes | Ignorado; regenerável |
| [execucao.json](execucao.json) | Ambiente, revisão Git, hashes de todos os módulos do domínio e do executor, cobertura dos lotes e horários | Preservar |
| [consolidacao.json](consolidacao.json) | Contagens, resumos e hashes dos CSVs | Preservar |
| [verificacao.json](verificacao.json) | Conferência estrutural independente, recálculo das métricas e reprodução integral de três lotes | Preservar |
| [analise.json](analise.json), [protocolo-utilizado.json](protocolo-utilizado.json), [figuras/](figuras/) e este README | Análise, receita utilizada, desenhos finais e documentação | Preservar |
| `execucao.log` | Acompanhamento operacional da execução original | Ignorado; mantido somente no disco |

O [inventário dos controles](../../redes_sinteticas/controles-etapa3-v1/inventario.json) também é preservado. Os CSVs e manifestos de cada controle são regenerados pelas sementes e conferidos contra esse inventário. As regras se restringem às pastas deste bloco; não ocultam os arquivos de origem da escola ou os scripts e testes.

A execução usou diretamente o adaptador Python que atende à API, sem depender do armazenamento HTTP de 32 resultados ou da animação do navegador. Os lotes foram salvos após concluir, com verificação de integridade e compatibilidade antes de aceitar um checkpoint. Nenhuma referência de rede foi alterada pelas intervenções.

As 6.300 trajetórias tiveram conservação S+I+R, monotonicidade de S/R, orçamento e instante de isolamento, cobertura das repetições, iniciais, sementes, motivos de término e métricas conferidos. Os resumos exportados coincidem com os do backend. Uma segunda geração reproduziu os vinte controles; escola, ER 1000 e BA 2000 reproduziram integralmente receitas efetivas, históricos, métricas e resumos. Essas **900 trajetórias extras de verificação** não aumentam o n experimental. Os quatro CSVs da escola preservaram os hashes anteriores. Passaram **178 testes** de executor, geração, metadados, comparação e métricas.

## Reproduzir

Na raiz do projeto, com Python 3.10 ou superior:

```bash
# Após clonar: restaura controles, caracterizações e exportações ignorados pelo Git.
# Extrai os lotes do ZIP; não executa novas trajetórias nem recria o log histórico.
PYTHONPATH=src python3 scripts/restaurar_artefatos_topologia.py
```

O [restaurador](../../../../scripts/restaurar_artefatos_topologia.py) confere o SHA-256 do ZIP, exige os 42 membros previstos e compara os hashes de cada lote com `execucao.json`. Os lotes são extraídos em diretório temporário; em seguida, são regenerados e conferidos os controles, indicadores e CSVs. Somente após essas verificações os arquivos locais são repostos. Um lote local divergente é preservado, e a operação é recusada. O pacote, o inventário, os resumos e os registros da execução original permanecem intactos. A restauração requer o código gerador e o ambiente numérico compatíveis com os registros. Ela usa a biblioteca padrão e o simulador, sem exigir ReportLab.

Os comandos abaixo permitem executar ou conferir operações específicas. Use a restauração acima antes das operações que dependem dos CSVs locais.

```bash
# Gera os controles, executa os lotes ainda ausentes e consolida as exportações.
PYTHONPATH=src python3 scripts/experimentos_topologia.py

# Apenas refaz as tabelas a partir dos lotes salvos, sem novas trajetórias.
PYTHONPATH=src python3 scripts/experimentos_topologia.py --somente-consolidar

# Regenera controles em pasta temporária, audita e repete os três lotes.
PYTHONPATH=src python3 scripts/verificar_experimentos_topologia.py

# Recria síntese e gráficos a partir dos CSVs; requer ReportLab para PDF/SVG.
PYTHONPATH=src python3 scripts/analisar_topologias.py
```

Para reunir novamente os lotes locais, mantendo os mesmos resultados:

```bash
PYTHONPATH=src python3 scripts/restaurar_artefatos_topologia.py --empacotar-lotes
```

O empacotador exige os lotes e hashes da execução registrada. Preserva seus bytes e usa ordem, data e permissões fixas no contêiner ZIP, permitindo reproduzir o pacote. Os membros `.gz` já estão comprimidos e não são recomprimidos. As datas científicas continuam nos manifestos dos resultados.

**Conferência do pacote — 22/11/2026:** o ZIP contém os 42 arquivos originais e ocupa 2.156.638 bytes. Passaram os 14 testes de artefatos, incluindo oito casos novos de empacotamento e integridade. Uma cópia sem lotes extraídos ou derivados restaurou os 21 lotes, vinte controles e as exportações, com 244 arquivos idênticos aos locais; somente o log histórico não foi recriado. A API de execução foi bloqueada nessa conferência para impedir novas trajetórias. O reempacotamento produziu o mesmo ZIP. Um lote local adulterado também foi recusado, preservando todos os arquivos da cópia. Os lotes originais, resumos e registros de execução permaneceram intactos.

Um checkpoint de receita, versão de Python, código de domínio ou topologia incompatível é recusado. Para uma nova versão científica, preserve esta pasta e use outro destino/identificador no executor. Datas e tokens de contexto HTTP não entram na assinatura científica das reproduções; configurações efetivas, históricos e métricas entram.

**Atualização posterior em 22/11/2026:** os [12 lotes adicionais](../intervencoes-v1/README.md), com 3.600 trajetórias, e as [medições de desempenho](../desempenho-v1/README.md) foram concluídos. Os registros originais deste bloco conservam seu escopo histórico; consulte o [estado atual da campanha](../estado-etapa3.json). Os tempos do log desta execução são acompanhamento operacional, sem o protocolo de benchmark. A projeção escolar é estática, com contatos de datas diferentes reunidos; β e γ são escolhas do experimento, sem estimativa para uma doença real.
