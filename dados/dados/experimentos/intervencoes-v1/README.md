# Intervenções na escola — blocos B, C e D

Os **12 lotes, 3.600 trajetórias e 226.345 registros** foram executados em 22/11/2026, conforme o [protocolo etapa3-base-v1](../protocolo-etapa3-v1.json), preservado sem alteração. Nenhuma trajetória destes blocos foi censurada. O [estado da campanha](../estado-etapa3.json) é separado da receita histórica.

A campanha completa soma **33 lotes, 9.900 trajetórias e 635.259 registros**, incluindo o [bloco A](../topologia-v1/README.md). Há 8.900 condições de execução distintas: referências reexecutadas não aumentam o n independente. Os 1.800 percursos extras de reprodução de B/C/D e os 900 de A ficam fora da amostra, assim como as chamadas do benchmark.

## Condições e resultados

Somente a escola estática de 67 pessoas e 1.325 contatos, peso 1, modo intensidade. γ = 0,10, três iniciais sorteados, até 200 transições, 100 repetições por cenário. Sementes base 10000/20000/30000 para iniciais/epidemia/isolamento, acrescidas de r−1. Cada lote inclui referência, seleção aleatória e por grau, com os mesmos iniciais por repetição. Orçamentos de 10%, 20% e 30% correspondem a 6, 13 e 20 pessoas.

A referência com β = 0,005 e a condição de desativação de 20% em t=5 são reutilizadas do bloco A, sem aumentar sua amostra. Exclusão e desativação deram históricos e métricas idênticos em todos os 300 pares de cenário/repetição. A exclusão modifica a topologia, mas ambos bloqueiam os mesmos contatos nesta intervenção única com seleção fixa.

Fração acumulada, em percentual: **média ± desvio amostral entre 100 repetições na mesma rede**, sem teste de significância. Inclui os três infectados iniciais.

| Lote | Sem intervenção | Aleatória | Por grau |
| --- | ---: | ---: | ---: |
| B_exclusao | 72,13 ± 22,05 | 44,06 ± 21,05 | 33,40 ± 17,14 |
| B_reducao | 72,13 ± 22,05 | 60,72 ± 23,24 | 53,94 ± 22,44 |
| C_f10_t0 | 72,13 ± 22,05 | 54,48 ± 26,59 | 49,57 ± 26,22 |
| C_f10_t10 | 72,13 ± 22,05 | 63,25 ± 22,15 | 59,60 ± 20,12 |
| C_f10_t5 | 72,13 ± 22,05 | 58,33 ± 24,21 | 56,91 ± 22,48 |
| C_f20_t0 | 72,13 ± 22,05 | 38,81 ± 23,47 | 29,27 ± 20,86 |
| C_f20_t10 | 72,13 ± 22,05 | 49,10 ± 20,31 | 41,09 ± 18,28 |
| C_f30_t0 | 72,13 ± 22,05 | 27,45 ± 19,32 | 15,33 ± 13,41 |
| C_f30_t10 | 72,13 ± 22,05 | 41,79 ± 17,94 | 31,04 ± 14,36 |
| C_f30_t5 | 72,13 ± 22,05 | 34,79 ± 18,18 | 22,66 ± 13,35 |
| D_beta0.0025 | 21,06 ± 17,22 | 14,66 ± 11,84 | 11,75 ± 8,39 |
| D_beta0.01 | 96,19 ± 3,03 | 78,82 ± 5,40 | 75,28 ± 11,36 |

Na receita-base, a fração acumulada é 72,13 ± 22,05% sem intervenção, 44,06 ± 21,05% com seleção aleatória e 33,40 ± 17,14% por grau. A redução de 50% conserva transmissão residual e apresenta médias maiores que o bloqueio completo. Na grade executada, maior orçamento e início antecipado reduziram as médias de pico e fração acumulada para ambos os critérios. Isso não assegura vantagem em toda repetição: na condição-base, o pico por grau superou a referência em quatro repetições.

Com β = 0,0025, a fração acumulada por grau foi 11,75%; com β = 0,01, 75,28%. A diferença entre as seleções foi 2,91 e 3,54 pontos percentuais, frente a 10,66 na configuração-base. São contrastes descritivos, sem calibração clínica. B/C/D não permitem generalizar mecanismos, orçamento/início ou sensibilidade às topologias ER/BA.

## Arquivos e reprodução

- [Resumo por condição](resumo_por_condicao.csv): n, ausentes, média e desvio, sem mesclar condições da mesma escola.
- [Consolidação](consolidacao.json): todos os indicadores, diferenças/reduções relativas pareadas e contagens de resultados menores/iguais/maiores que a referência.
- [Censura e aplicação](censura_aplicacao.csv): conserva extinções antes da intervenção, sem excluir repetições.
- [Análise](analise.json), [execução e ambiente](execucao.json) e [verificação](verificacao.json).
- [Lotes completos](lotes-intervencoes-v1.zip) e [SHA-256](lotes-intervencoes-v1.zip.sha256): 12 respostas JSON integrais gzip e seus hashes em um ZIP determinístico, sem dezenas de arquivos individuais no Git.
- Figuras vetoriais: [mecanismos](figuras/mecanismos.pdf), [orçamento/início](figuras/orcamento-inicio.pdf), [sensibilidade](figuras/sensibilidade-beta.pdf). Barras são um desvio amostral; não são intervalos de confiança. Curvas de orçamento mostram médias; desvios permanecem nos resumos.

Para restaurar os CSVs extensos e históricos ignorados pelo Git, sem executar o SIR:

```bash
PYTHONPATH=src python3 scripts/experimentos_intervencoes.py --restaurar
```

A restauração valida o ZIP, os nomes, cada hash e a consolidação regenerada. Recria `lotes/`, `metricas.csv`, `diferencas_pareadas.csv`, `curvas_medias.csv` e `historicos.csv.gz`. Os históricos originais terminam na parada; somente as curvas médias prolongam o estado extinto até t=200 para alinhar o desenho. Ausências não viram zero.

Para executar/reutilizar checkpoints da campanha e conferir seis reproduções completas:

```bash
PYTHONPATH=src python3 scripts/experimentos_intervencoes.py
PYTHONPATH=src python3 scripts/experimentos_intervencoes.py --verificar
```

As verificações recalcularam métricas e agregações, conferiram conservação SIR, cronologia, isolamento, pareamento, sementes, censura e imutabilidade da referência. Os seis lotes reproduzidos cobrem ambos os mecanismos, início zero/tardio, orçamento mínimo/máximo e ambos os valores de β. Os 12 lotes e todas as exportações também foram auditados, com restauração em diretório temporário e hashes idênticos.

Para refazer as figuras sem executar trajetórias (ReportLab disponível no Python do sistema):

```bash
PYTHONPATH=src python3 scripts/analisar_intervencoes.py
```

O script lê também o bloco A e o [benchmark separado](../desempenho-v1/README.md). A versão efetiva do domínio coincide com a usada no bloco A; os hashes de código, rede e entradas permitem conferir a compatibilidade. A revisão Git identifica o ponto de partida; a árvore tinha alterações locais, explicitadas nos registros.
