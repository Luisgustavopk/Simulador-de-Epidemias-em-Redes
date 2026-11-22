# Referências do trabalho

**Atualização: 22 de novembro de 2026.** Esta bibliografia reúne somente os fundamentos e as fontes diretamente relacionados ao modelo, aos geradores de redes, à implementação e aos dados usados no projeto.

<a id="kermack1991"></a>

## 1. Modelo epidêmico SIR

KERMACK, W. O.; MCKENDRICK, A. G. Contributions to the mathematical theory of epidemics—I. **Bulletin of Mathematical Biology**, v. 53, n. 1–2, p. 33–55, 1991. Republicação do trabalho de 1927. DOI: [10.1007/BF02464423](https://doi.org/10.1007/BF02464423). Registro: [PubMed](https://pubmed.ncbi.nlm.nih.gov/2059741/). Acesso em: 22 nov. 2026.

**Uso no projeto:** Fundamentação histórica dos compartimentos SIR e da organização suscetível–infectado–recuperado.

<a id="newman2002"></a>

## 2. Epidemias em redes

NEWMAN, M. E. J. Spread of epidemic disease on networks. **Physical Review E**, v. 66, n. 1, artigo 016128, 2002. DOI: [10.1103/PhysRevE.66.016128](https://doi.org/10.1103/PhysRevE.66.016128). Texto: [publicação da APS](https://journals.aps.org/pre/pdf/10.1103/PhysRevE.66.016128). Acesso em: 22 nov. 2026.

**Uso no projeto:** Relação entre organização da rede e propagação de doenças.

<a id="koher2019"></a>

## 3. Contatos temporais e propagação

KOHER, A.; LENTZ, H. H. K.; GLEESON, J. P.; HÖVEL, P. Contact-Based Model for Epidemic Spreading on Temporal Networks. **Physical Review X**, v. 9, n. 3, artigo 031017, 2019. DOI: [10.1103/PhysRevX.9.031017](https://doi.org/10.1103/PhysRevX.9.031017). Texto: [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7219481/). Acesso em: 22 nov. 2026.

**Uso no projeto:** Fundamentação da representação por contatos. O projeto usa uma rede estática e não implementa o método de passagem de mensagens do artigo.

<a id="sofonea2022"></a>

## 4. Fundamentos e hipóteses dos modelos epidemiológicos

SOFONEA, M. T.; CAUCHEMEZ, S.; BOËLLE, P.-Y. Epidemic models: why and how to use them. **Anaesthesia, Critical Care & Pain Medicine**, v. 41, n. 2, artigo 101048, 2022. DOI: [10.1016/j.accpm.2022.101048](https://doi.org/10.1016/j.accpm.2022.101048). Texto: [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8882476/). Acesso em: 22 nov. 2026.

**Uso no projeto:** Interpretação das hipóteses, cenários e limitações do modelo acadêmico.

<a id="codeco2008"></a>

## 5. Redes em epidemiologia

CODEÇO, C. T.; COELHO, F. C. Redes: um olhar sistêmico para a epidemiologia de doenças transmissíveis. **Ciência & Saúde Coletiva**, v. 13, n. 6, p. 1767–1774, 2008. DOI: [10.1590/S1413-81232008000600011](https://doi.org/10.1590/S1413-81232008000600011). Texto: [SciELO](https://www.scielo.br/j/csc/a/qbqdmfv364nYw8gvGwWXy7f/). Acesso em: 22 nov. 2026.

**Uso no projeto:** Contextualização do papel dos contatos e da estrutura social na transmissão.

<a id="gomes2024"></a>

## 6. Ciência de redes e teoria dos grafos

GOMES, P. F. Uma introdução à Ciência de Redes e Teoria de Grafos. **Revista Brasileira de Ensino de Física**, v. 46, e20240190, 2024. DOI: [10.1590/1806-9126-RBEF-2024-0190](https://doi.org/10.1590/1806-9126-RBEF-2024-0190). Texto: [SciELO](https://www.scielo.br/j/rbef/a/GLGWtVsYZ7zysCBc3Xktf6b/). Acesso em: 22 nov. 2026.

**Uso no projeto:** Definições de grau, componentes e representação em grafos.

<a id="gilbert1959"></a>

## 7. Redes aleatórias G(N,p)

GILBERT, E. N. Random Graphs. **The Annals of Mathematical Statistics**, v. 30, n. 4, p. 1141–1144, 1959. DOI: [10.1214/aoms/1177706098](https://doi.org/10.1214/aoms/1177706098). Acesso em: 22 nov. 2026.

**Uso no projeto:** Fundamentação da construção Erdős–Rényi do projeto, em que cada par recebe o mesmo peso probabilístico independente.

<a id="erdos1959"></a>

## 8. Redes aleatórias

ERDŐS, P.; RÉNYI, A. On random graphs I. **Publicationes Mathematicae Debrecen**, v. 6, p. 290–297, 1959. Disponível no [acervo do Instituto Alfréd Rényi](https://www.renyi.hu/~p_erdos/1959-11.pdf). Acesso em: 22 nov. 2026.

**Uso no projeto:** Origem histórica da família de redes aleatórias usada como controle.

<a id="barabasi1999"></a>

## 9. Redes livres de escala

BARABÁSI, A.-L.; ALBERT, R. Emergence of scaling in random networks. **Science**, v. 286, n. 5439, p. 509–512, 1999. DOI: [10.1126/science.286.5439.509](https://doi.org/10.1126/science.286.5439.509). Versão dos autores: [arXiv](https://arxiv.org/abs/cond-mat/9910332). Acesso em: 22 nov. 2026.

**Uso no projeto:** Fundamentação do controle com crescimento e ligação preferencial.

<a id="pinto2023"></a>

## 10. Interface para simulação em redes

PINTO, E. R.; NEPOMUCENO, E. G.; KUSAK, J.; CAMPANHARO, A. S. L. O. EPIGUI: Graphical User Interface for Simulating Epidemics on Networks. **Trends in Computational and Applied Mathematics**, v. 24, n. 1, p. 91–120, 2023. DOI: [10.5540/tcam.2022.024.01.00091](https://doi.org/10.5540/tcam.2022.024.01.00091). Texto: [SBMAC](https://tcam.sbmac.org.br/tema/article/view/1689). Acesso em: 22 nov. 2026.

**Uso no projeto:** Trabalho relacionado sobre interface e simulação epidemiológica em redes.

<a id="tavares2018dissertacao"></a>

## 11. Simulação em redes baseadas em passeios aleatórios

TAVARES, J. V. B. **Simulação escalável de epidemias em redes baseadas em passeios aleatórios com caracterização de transições de fase**. 2018. Dissertação (Mestrado) – Universidade Federal do Rio de Janeiro. Disponível em: [Pantheon UFRJ](https://pantheon.ufrj.br/items/a6d142ba-8cbd-41f3-b687-5f15c4df8ffd). Acesso em: 22 nov. 2026.

**Uso no projeto:** Trabalho relacionado sobre simulação e desempenho em redes epidemiológicas.

<a id="tavares2018wperformance"></a>

## 12. Desempenho da simulação em redes

TAVARES, J. V. B.; IACOBELLI, G.; FIGUEIREDO, D. R. Simulação escalável de epidemias em redes baseadas em passeios aleatórios. **Anais do XVII Workshop em Desempenho de Sistemas Computacionais e de Comunicação**, 2018, p. 280–285. DOI: [10.5753/wperformance.2018.3337](https://doi.org/10.5753/wperformance.2018.3337). Texto: [SBC](https://sol.sbc.org.br/index.php/wperformance/article/view/3337). Acesso em: 22 nov. 2026.

**Uso no projeto:** Artigo relacionado ao trabalho de Tavares sobre execução escalável.

<a id="banholzer2025"></a>

## 13. Dados da escola de Berna

BANHOLZER, N.; MUNDAY, J. D.; JENT, P. et al. The relative contribution of close-proximity contacts, shared classroom exposure and indoor air quality to respiratory virus transmission in schools. **Nature Communications**, v. 16, artigo 11678, 2025. DOI: [10.1038/s41467-025-66719-3](https://doi.org/10.1038/s41467-025-66719-3). Texto: [Nature Communications](https://www.nature.com/articles/s41467-025-66719-3). Acesso em: 22 nov. 2026.

**Uso no projeto:** Procedência dos contatos presenciais observados na escola secundária suíça usada nos experimentos.

<a id="osf-escola"></a>

## 14. Repositório dos dados escolares

BANHOLZER, N. et al. **Respiratory virus transmission in schools: A longitudinal study of molecular, physical proximity and air quality data**. Open Science Framework, 2025. Repositório: [OSF naut4](https://osf.io/naut4/). Arquivo utilizado: [contact-duration-acc-based-att-65.csv](https://osf.io/download/vygsf/), versão 1. Acesso em: 22 nov. 2026.

**Uso no projeto:** Fonte dos 67 indivíduos e dos 1.325 pares únicos preparados com peso unitário. Regras e hashes estão no [manifesto da base](../../dados/dados/redes_reais/escola_suica_2024/manifesto.json).
