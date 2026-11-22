# Desempenho — receita-base da etapa 3

Medição sequencial em 22/11/2026, na mesma máquina, sem execução concorrente dos experimentos ou testes. As três redes foram carregadas e confirmadas **antes** da cronometragem. Cada chamada executa 100 repetições × 3 cenários e monta a resposta do adaptador `executar_comparacao_api`.

| Rede | Registros/chamada | Mediana de 5 chamadas (s) | Pico adicional Python (MiB) | Cópias/chamada |
| --- | ---: | ---: | ---: | ---: |
| escola_suica_2024 | 18986 | 4,090 | 6,349 | 301 |
| er_1000 | 20225 | 4,129 | 6,647 | 301 |
| ba_2000 | 18912 | 4,068 | 6,315 | 301 |

Ambiente: **AMD Ryzen 7 7735HS with Radeon Graphics**, Python 3.13.3, Linux-6.17.6-lux-amd64-x86_64-with-glibc2.41, 13,34 GiB de RAM física. O [JSON de medições](medicoes.json) registra revisão Git, alterações locais, hashes do domínio/executores, assinaturas das redes, configurações e todos os tempos brutos.

Tempo: cinco chamadas sem instrumentação, `perf_counter`, incluindo execução e montagem da resposta. O cálculo/verificação de assinaturas ocorre depois do intervalo cronometrado. Não houve descarte seletivo nem aquecimento adicional. [Tempos brutos](tempos.csv), [resumo](resumo.csv) e [gráfico](figuras/desempenho.pdf).

Memória: outra chamada após coleta de lixo, usando `tracemalloc`, com a rede já carregada. O valor é o pico adicional de alocações rastreadas do Python; **não é RSS**, consumo do navegador ou memória total do sistema. MiB = 2²⁰ bytes. Essa chamada instrumentada não entra na mediana de tempo.

Cópias: uma chamada separada substitui temporariamente `RedeContatos.copiar` por um contador que delega ao original. Foram 301 cópias: uma referência privada do lote e uma rede de trabalho por trajetória. O método é restaurado ao sair do contexto.

As **sete chamadas de cada rede** coincidiram com a assinatura integral do lote científico correspondente, desconsiderando apenas datas e contexto da sessão. São 21 chamadas/6.300 trajetórias adicionais de instrumentação, que não aumentam a amostra epidemiológica. A [verificação](verificacao.json) registra essa separação.

O escopo exclui HTTP, navegador, importação/geração e confirmação da rede. Os três grafos têm apenas N=67 e densidades próximas; diferenças pequenas de tempo não demonstram vantagem geral de uma topologia nem escalabilidade. O ambiente compartilhado pode ter ruído de escalonamento. Nenhum limite de aprovação de tempo ou memória foi inventado.

Reprodução na raiz:

```bash
PYTHONPATH=src python3 scripts/benchmark_etapa3.py
```

Execute sem outros ensaios concorrentes. Para refazer somente as figuras, use `scripts/analisar_intervencoes.py` com ReportLab, após restaurar os resultados B/C/D quando necessário.
