# Bases observadas para a etapa 3

A base real principal escolhida é a rede de contatos presenciais da escola de Berna, coletada em 2024. A escolha foi delegada pelo usuário em 21/11/2026 e priorizou contato presencial observado, recência e compatibilidade verificada com o simulador. A pasta mantém somente a base selecionada para o projeto. Os CSVs têm cabeçalhos em português, IDs inteiros e pesos unitários.

| Base | Origem e período de coleta | Indivíduos | Contatos únicos preparados | Uso previsto |
| --- | --- | ---: | ---: | --- |
| [Escola suíça](escola_suica_2024/) | Berna, Suíça; 22/01 a 08/03/2024; publicação de 2025 | 67 | 1.325 | Base real principal para a bateria epidemiológica |

A base passou pelo importador Python e pelo serviço de carga usado pela interface, incluindo a confirmação da rede. Os resultados estão no manifesto da pasta escolar. A carga também foi conferida na Tela 01 com o Chrome, incluindo Mapa, 3D, inspeção e confirmação; as [evidências do navegador](evidencias/interface-escola/README.md) registram o percurso. Essa conferência no navegador não executou epidemias. O [bloco A de topologias](../experimentos/topologia-v1/README.md) foi executado depois, em 22/11/2026, com a rede completa.

## Critérios de seleção e preferência por PT-BR

A busca consultou o catálogo público e a API do Kaggle, além de repositórios dos autores e fontes científicas. Foram priorizados registros com indivíduos identificáveis por códigos e pares de contatos, procedência verificável e download público. As datas de coleta foram separadas das datas de publicação e atualização do catálogo.

Não foi encontrada, nesta busca, uma base brasileira recente de **pares de contatos presenciais** que pudesse ser verificada e importada diretamente. Isso não significa que tal base não exista. A escola suíça foi escolhida pela coleta de 2024 e pela proximidade com o objeto do simulador. A documentação local e os arquivos importáveis foram preparados em português brasileiro.

Outras fontes verificadas:

| Fonte consultada | Avaliação |
| --- | --- |
| [Kaggle: UK Social Contact Network](https://www.kaggle.com/datasets/thedevastator/uk-social-contact-network) | A atualização de 2023 remete a um estudo de 2013, com arquivos de questionário. Não foi adotado como rede completa de pares identificados. |
| [Kaggle: Peruvian Social Contact Network](https://www.kaggle.com/datasets/thedevastator/peruvian-social-contact-network) | Espelho de questionários de 2015, atualizado em 2023; não atende ao recorte brasileiro nem à prioridade de coleta recente. |
| [Ministério da Saúde: SRAG 2019–2026](https://dadosabertos.saude.gov.br/dataset/srag-2019-a-2026) | Fonte brasileira em português, atualizada em 2026. Registra notificações, não uma lista de quem encontrou quem; não foi convertida artificialmente em contatos. |
| [SocioPatterns: redes domiciliares sul-africanas](https://sociopatterns.org/datasets) | Alternativa pertinente: coleta de 2020–2021 e publicação de 2023. A base escolar selecionada possui coleta posterior. |

## Escola suíça: origem e tratamento

Fonte: [projeto público OSF naut4](https://osf.io/naut4/) e Banholzer et al., *The relative contribution of close-proximity contacts, shared classroom exposure and indoor air quality to respiratory virus transmission in schools*, [Nature Communications, 2025](https://doi.org/10.1038/s41467-025-66719-3). O estudo acompanhou estudantes de quatro turmas em Berna. A versão pública contém códigos anonimizados, sem os demais dados pessoais restritos mencionados no artigo.

Foi usado `contact-duration-acc-based-att-65.csv`, versão 1 do OSF, com filtro de acelerômetro e atenuação de −65 dBm. Esse arquivo é usado pelo [código de análise dos autores](https://osf.io/download/jpaf4/). As durações estão em segundos; o script original as divide por 60 ao apresentar minutos.

O preparo executa estas operações:

1. Lê todos os pares e conserva os 67 códigos encontrados, incluindo pessoas que eventualmente não tivessem contatos válidos.
2. Exclui durações `NA` da projeção, sem transformá-las em zero e sem imputação. Exige duração positiva, ambos os participantes presentes e movimento positivo nos dois sensores.
3. Une os contatos positivos do período em pares não dirigidos únicos. Ocorrências do mesmo par em dias diferentes formam uma única aresta.
4. Converte os códigos para inteiros consecutivos de 0 a 66, em ordem lexicográfica dos códigos originais. `mapa_ids.csv` preserva essa correspondência.
5. Grava peso 1 em todas as arestas. A soma das durações observadas e a quantidade de dias com contato ficam em `duracoes_observadas.csv`, para permitir outra ponderação posteriormente.

O arquivo possui 87.932 registros de pares por data: 36.392 têm duração ausente; 13.128 registros com duração conhecida ficam fora do filtro de presença/movimento; 31.475 têm duração válida zero; 6.937 têm duração positiva válida. Estes últimos originam 1.325 arestas, com 1.520.080 segundos de contato somados. As contagens são categorias exclusivas da preparação, não estimativas de risco de infecção.

Esta é uma **projeção estática de todo o período**, diferente de uma rede diária ou de uma reprodução temporal dos sensores. Ela reúne oportunidades de contato de datas diferentes. Peso 1 indica a existência de contato observado, sem afirmar que todas as durações foram iguais. Não foram usados diagnósticos clínicos para definir infectados iniciais.

## Importar na aplicação

Na Tela 01, escolha **Importar CSV** e envie os dois arquivos da mesma pasta:

- contatos: `contatos.csv`;
- cadastro opcional de indivíduos: `individuos.csv`;
- separador: vírgula.

Confira as contagens da tabela e confirme a rede. `mapa_ids.csv` e `duracoes_observadas.csv` são arquivos de auditoria, com outro esquema, e não devem ser enviados ao importador.

Na configuração epidemiológica, a representação binária preparada corresponde ao modo **intensidade**: com peso 1, a probabilidade por contato é `beta × 1`. Se for escolhido o modo **probabilidade direta**, o sistema interpreta peso 1 como probabilidade de transmissão de 100% por contato com um infectado a cada passo. Nenhuma dessas probabilidades foi estimada a partir dos datasets.

No Python, a partir da raiz do projeto:

```bash
PYTHONPATH=src python3 - <<'PY'
from simulador import importar_rede_csv

pasta = "dados/dados/redes_reais/escola_suica_2024"
rede = importar_rede_csv(
    f"{pasta}/contatos.csv",
    arquivo_individuos=f"{pasta}/individuos.csv",
).rede
print(rede.numero_individuos, rede.numero_contatos)  # 67 1325
PY
```

## Reproduzir e conferir

O [preparador](../../../scripts/preparar_redes_reais.py) usa somente a biblioteca padrão e o próprio simulador. O arquivo original é preservado localmente em `originais/escola_suica_2024/`, ignorado pelo Git. Os CSVs preparados e o manifesto ficam em `escola_suica_2024/`; o catálogo [fontes.json](fontes.json) registra a seleção.

```bash
# Base real principal: baixa as fontes ausentes.
PYTHONPATH=src python3 scripts/preparar_redes_reais.py --baixar

# Repetir com os originais já baixados, sem acessar a internet.
PYTHONPATH=src python3 scripts/preparar_redes_reais.py
```

O script verifica SHA-256 antes de processar uma fonte, recusa versões diferentes, registros diários repetidos e extremos inválidos. Cada `manifesto.json` registra origem, versão, regras, contagens, ambiente Python e hashes dos originais, dos CSVs, do catálogo e do preparador. Em novas execuções, os CSVs devem ter hashes idênticos; o horário no manifesto muda.

O catálogo [fontes.json](fontes.json) preserva as condições de uso encontradas. O nó OSF não declara licença específica. A licença CC BY 4.0 do artigo não foi atribuída automaticamente ao CSV.

Em 21/11/2026, uma segunda preparação, com download em pasta vazia, produziu os mesmos hashes de todos os CSVs. Uma auditoria independente comparou os pares preparados com a fonte, conferiu o cadastro integral e a soma das durações. Também passaram os 134 testes existentes de importação e serviço de carga. Os registros estão em [evidencias/](evidencias/).

## Caracterização estrutural

A [caracterização da rede preparada](escola_suica_2024/caracterizacao/README.md) está concluída, com tabela, distribuição de graus, componentes e arquivos para reprodução.

| Indicador | Resultado |
| --- | ---: |
| Grau médio | 39,5522 |
| Grau mínimo / máximo | 18 / 54 |
| Densidade | 59,93% |
| Componentes conexas | 1, com os 67 estudantes |
| Indivíduos sem contatos | 0 |

Os [CSVs e o registro dos cálculos](escola_suica_2024/caracterizacao/) preservam os valores sem arredondamento e os hashes das entradas. O gráfico está disponível em [PDF](escola_suica_2024/caracterizacao/distribuicao_graus.pdf) e [SVG](escola_suica_2024/caracterizacao/distribuicao_graus.svg). A contagem foi conferida diretamente nos arquivos; passaram também os 53 testes existentes de análise estrutural. A componente única e a densidade descrevem a união de contatos de todo o período, sem garantir que os caminhos existiram na mesma data ou na ordem necessária à transmissão.

```bash
PYTHONPATH=src python3 scripts/caracterizar_rede_real.py
# PDF e SVG opcionais, com ReportLab disponível no ambiente:
PYTHONPATH=src python3 scripts/caracterizar_rede_real.py --graficos
```

## Protocolo definido e próximas execuções

O usuário delegou a configuração-base em 21/11/2026. O [protocolo etapa3-base-v1](../experimentos/README.md) adota a janela completa de 22/01 a 08/03/2024 e peso unitário, β = 0,005, γ = 0,10, três infectados iniciais, 200 transições e 100 repetições por lote. A grade prevê a escola e vinte controles sintéticos, com sementes e condições registradas no JSON. O [aviso ao integrante B](../../../docs/implementacao/Aviso-IntegranteB-Etapa3.md) reúne os cuidados de execução e análise.

A preparação, a importação, a caracterização e a conferência no navegador estão concluídas. Os [vinte controles](../redes_sinteticas/controles-etapa3-v1/README.md) foram gerados e caracterizados. O [bloco A](../experimentos/topologia-v1/README.md) concluiu 21 lotes e 6.300 trajetórias. Restam os blocos B/C/D e as medições de desempenho, conforme o [estado atual](../experimentos/estado-etapa3.json). As condições agora estão definidas e não devem ser tratadas como valores pendentes. A caracterização continua válida para esta projeção; mudanças na janela ou nos critérios de contato exigirão outra preparação e novo cálculo.
