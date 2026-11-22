# Controles sintéticos da etapa 3

Vinte controles foram gerados e caracterizados em **22/11/2026** com o gerador nativo do simulador. Todas as redes têm **67 indivíduos**, peso unitário, uma componente de tamanho 67 e nenhum indivíduo sem contatos. As topologias permanecem fixas nas 100 repetições epidemiológicas de cada lote.

- **Erdős–Rényi:** `p = 1325/2211 = 0.5992763455450023`, sementes **1000–1009**. O total esperado é 1.325 arestas; os totais realizados variam de **1.291 a 1.360**.
- **Barabási–Albert:** `m = 24`, sementes **2000–2009**, núcleo completo de **25 indivíduos**. O gerador local produz exatamente **1.308 arestas**, grau médio 39,0448 e densidade 0,591588. São 17 arestas a menos que na escola (−1,28%).

O valor de m minimiza a diferença de arestas para a escola entre os inteiros permitidos. A distribuição do controle BA pequeno e denso foi medida; não se pressupõe que ela siga uma lei de potência. ER aproxima a densidade da escola em esperança. A densidade efetiva participa das diferenças observadas entre as redes.

## Caracterização

A escola aparece como referência na primeira linha. `σ(grau)` é o desvio populacional dos 67 graus de cada rede, não a dispersão entre realizações nem um desvio epidemiológico.

| Rede | Semente | Arestas | Grau médio | Grau mín.–máx. | σ(grau) | Densidade | Componentes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| escola_suica_2024 | — | 1325 | 39.5522 | 18–54 | 9.5578 | 0.599276 | 1 |
| er_1000 | 1000 | 1291 | 38.5373 | 26–48 | 4.5788 | 0.583899 | 1 |
| er_1001 | 1001 | 1304 | 38.9254 | 27–51 | 4.3651 | 0.589778 | 1 |
| er_1002 | 1002 | 1302 | 38.8657 | 28–47 | 3.9470 | 0.588874 | 1 |
| er_1003 | 1003 | 1340 | 40.0000 | 32–49 | 3.4984 | 0.606061 | 1 |
| er_1004 | 1004 | 1334 | 39.8209 | 32–47 | 3.7929 | 0.603347 | 1 |
| er_1005 | 1005 | 1318 | 39.3433 | 27–50 | 3.9115 | 0.596110 | 1 |
| er_1006 | 1006 | 1312 | 39.1642 | 31–47 | 4.2059 | 0.593397 | 1 |
| er_1007 | 1007 | 1335 | 39.8507 | 30–50 | 3.8527 | 0.603799 | 1 |
| er_1008 | 1008 | 1360 | 40.5970 | 32–49 | 3.6531 | 0.615106 | 1 |
| er_1009 | 1009 | 1340 | 40.0000 | 29–51 | 4.2002 | 0.606061 | 1 |
| ba_2000 | 2000 | 1308 | 39.0448 | 24–56 | 9.6914 | 0.591588 | 1 |
| ba_2001 | 2001 | 1308 | 39.0448 | 24–56 | 10.7265 | 0.591588 | 1 |
| ba_2002 | 2002 | 1308 | 39.0448 | 24–58 | 10.5596 | 0.591588 | 1 |
| ba_2003 | 2003 | 1308 | 39.0448 | 24–57 | 10.6944 | 0.591588 | 1 |
| ba_2004 | 2004 | 1308 | 39.0448 | 24–57 | 10.7390 | 0.591588 | 1 |
| ba_2005 | 2005 | 1308 | 39.0448 | 24–58 | 10.4816 | 0.591588 | 1 |
| ba_2006 | 2006 | 1308 | 39.0448 | 24–58 | 10.5157 | 0.591588 | 1 |
| ba_2007 | 2007 | 1308 | 39.0448 | 24–55 | 10.3512 | 0.591588 | 1 |
| ba_2008 | 2008 | 1308 | 39.0448 | 24–59 | 10.3958 | 0.591588 | 1 |
| ba_2009 | 2009 | 1308 | 39.0448 | 24–55 | 9.8639 | 0.591588 | 1 |

Cada pasta gerada contém `contatos.csv`, `individuos.csv`, `graus.csv`, `distribuicao_graus.csv`, `componentes.csv` e `manifesto.json`. O [inventário](inventario.json) registra parâmetros, semente, versão do gerador, indicadores, assinatura da topologia e hashes dos CSVs e do código gerador. A distribuição inclui frequências nulas para todos os graus de 0 a 66.

Este README e o inventário são preservados no Git. As vinte pastas `er_*` e `ba_*` ficam no disco, ignoradas pelo Git, pois podem ser regeneradas pelas sementes. Após clonar o repositório, restaure os arquivos antes de importá-los na interface.

A exportação foi reimportada e comparada à rede gerada. Uma segunda geração em diretório temporário reproduziu **todos os CSVs e manifestos**. Graus e componentes das 21 redes foram conferidos diretamente nos CSVs por contagem dos extremos e união de conjuntos, sem chamar os algoritmos de análise do simulador. A [verificação](../../experimentos/topologia-v1/verificacao.json) registra os resultados.

## Uso e reprodução

Na Tela 01, importe `contatos.csv` e `individuos.csv` da mesma pasta e confirme. Use modo **intensidade**: peso 1 não é uma probabilidade calibrada.

A partir da raiz do repositório:

```bash
# Extrai os lotes do pacote e restaura controles e exportações do bloco A.
PYTHONPATH=src python3 scripts/restaurar_artefatos_topologia.py

# Alternativa para apenas gerar os controles; reescreve seu inventário.
PYTHONPATH=src python3 scripts/experimentos_topologia.py --somente-controles
```

Para reproduzir também a conferência e os três lotes de verificação:

```bash
PYTHONPATH=src python3 scripts/verificar_experimentos_topologia.py
```

Os [resultados de topologia](../../experimentos/topologia-v1/README.md) usam estas redes e a escola. A representação da escola é a união estática dos contatos do período inteiro; não há equivalência entre um ID sintético e a identidade de um estudante.
