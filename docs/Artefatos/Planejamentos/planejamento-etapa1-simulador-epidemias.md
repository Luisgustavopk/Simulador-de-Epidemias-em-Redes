# Planejamento da Etapa 1 — Simulador de Epidemias em Redes

Trabalho Prático de Grafos — Tema 7 (grupo de 3 integrantes).

Legenda: itens marcados **(enunciado)** vêm do PDF do trabalho; itens marcados **(recomendação)** são sugestões para o grupo discutir e aceitar ou rejeitar.

---

## 1. O que a Etapa 1 exige

**Do enunciado:**

- Escolher o tema, definir o problema, levantar dados e modelar o grafo.
- UML será avaliada na modelagem.
- Entregável: documento com **descrição do problema, justificativa da modelagem e plano de desenvolvimento**.

**Pontos do enunciado que mudam o planejamento:**

- As três partes têm a **mesma data de entrega (22/11)**. A Etapa 1 não tem prazo próprio, mas é a base das outras duas. Restam cerca de 3 semanas para tudo (ferramenta, relatório de 12 a 15 páginas, vídeo de 12 a 18 min e apresentação de 10 min). Por isso, **a Etapa 1 deve ficar pronta em cerca de uma semana**.
- **É proibido usar bibliotecas prontas para criar e processar o grafo** (como NetworkX), salvo para comparação de desempenho. A estrutura de grafo e os algoritmos são implementados pelo grupo.
- O vídeo deve mostrar as features **de cada aluno**, e os commits individuais são avaliados. O ideal é que a divisão de módulos já nasça na Etapa 1.
- Falta de qualquer item resulta em nota zero, e cada membro entrega sua própria cópia.
- O relatório final é em LaTeX no template SBC. **(recomendação)** Escrever o documento da Etapa 1 já nesse template, para reaproveitar o texto no relatório final.

**Decisões e artefatos a produzir:**

1. Pergunta central do projeto (qual problema o simulador investiga).
2. Modelo do grafo (vértices, arestas, tipo e atributos).
3. Modelo epidemiológico e parâmetros.
4. Mapeamento algoritmo → funcionalidade.
5. Fonte de dados (Kaggle ou geradores próprios).
6. Diagramas UML e esboço de interface.
7. Plano de desenvolvimento (módulos, responsáveis, cronograma, riscos).

---

## 2. Divisão do trabalho entre os 3 integrantes

A divisão é por **área**, com revisão cruzada. Cada pessoa também vira dona de um conjunto de módulos na Etapa 2, o que facilita o vídeo e a avaliação dos commits.

| | **Integrante A (Luis): Problema e epidemiologia** | **Integrante B (Wesley): Grafo e algoritmos** | **Integrante C (João): Arquitetura, interface e plano** |
|---|---|---|---|
| **Texto** | Contextualização, pergunta de pesquisa, objetivos, modelo SIR, parâmetros, métricas de resultado, dados | Modelagem do grafo, justificativas, atributos, mapeamento de algoritmos, complexidade esperada | Arquitetura, requisitos, wireframes, plano de desenvolvimento, cronograma, riscos, Git |
| **Diagramas** | Casos de uso, diagrama de estados do indivíduo (S→I→R) | Diagrama de classes, exemplo ilustrado do grafo | Diagrama de sequência, componentes (opcional), wireframes |
| **Dono na Etapa 2 (sugestão)** | Motor de simulação, parâmetros, métricas, experimentos | Estrutura do grafo, algoritmos, geradores de rede | Interface gráfica, leitura de dados, visualização, testes |

**Tarefas compartilhadas:**

- Reunião de decisões (todos).
- Introdução e conclusão (A escreve, B e C revisam).
- Integração do documento em LaTeX (B monta, todos revisam).
- Revisão cruzada: A revisa B, B revisa C, C revisa A.

---

## 3. Sequência de execução

| Fase | O que fazer | Depende de |
|---|---|---|
| **0. Reunião de decisões** (dia 1) | Fechar as decisões da seção "Recomendação final" | — |
| **1. Rascunhos paralelos** (dias 2 a 4) | A: problema e modelo epidemiológico. B: grafo e algoritmos. C: requisitos, arquitetura e estrutura do repositório | Fase 0 |
| **2. Diagramas** (dias 3 a 5) | Casos de uso e estados (A), classes (B), sequência e wireframes (C) | Classes dependem da modelagem de B. Sequência depende das classes |
| **3. Integração** (dias 5 a 6) | B monta o documento. Revisão cruzada | Fases 1 e 2 |
| **4. Fechamento** (dia 7) | Ajustes, PDF, commit final | Fase 3 |

**Cronograma sugerido (recomendação):**

- Etapa 1 pronta por volta de 5/11.
- Protótipo funcional por volta de 14/11.
- Relatório, vídeo e slides entre 15/11 e 20/11, com margem antes de 22/11.

---

## 4. Modelagem do problema

### 4.1 Problema específico (recomendação)

Um simulador que apenas "roda uma epidemia" é pouco analítico. Sugestão de pergunta central:

> **"Como a estrutura da rede de contatos influencia a propagação de uma epidemia, e qual estratégia de isolamento é mais eficaz: aleatória, por grau ou por posição estrutural (pontos de articulação e pontes)?"**

Ela é viável e aproveita bem o conteúdo da disciplina, porque a estratégia estrutural usa conectividade e separabilidade. O experimento é simples: rodar a mesma epidemia com diferentes estratégias de isolamento (com o mesmo número de pessoas isoladas) e comparar o resultado.

### 4.2 Vértices e arestas

- **Vértice:** um indivíduo.
- **Aresta:** um contato em que pode haver transmissão (convívio, trabalho, amizade).

### 4.3 Tipo do grafo

| Característica | Escolha | Justificativa |
|---|---|---|
| Direção | **Não direcionado** | O contato físico é simétrico. Se A encontra B, B encontra A. Para propagação de *informação* (um dos usos do tema), o direcionado faria sentido, mas pode ficar como extensão futura. |
| Pesos | **Ponderado** | O peso representa a intensidade do contato (frequência ou duração) e entra no cálculo da probabilidade de transmissão. Redes reais têm contatos mais e menos intensos. |
| Dinâmica | **Topologia estática, estado dinâmico** | A rede de contatos fica fixa durante a simulação, mas o estado dos nós muda a cada passo (S, I, R). O isolamento é **lógico**: marca nós ou arestas como inativos, sem apagar do grafo. |

Redes que mudam ao longo do tempo (contatos que surgem e somem) complicam bastante a modelagem e podem ficar de fora desta versão.

### 4.4 Atributos

**Indivíduo:**

- identificador;
- estado (Suscetível, Infectado, Recuperado);
- dia da infecção;
- isolado (sim/não);
- *opcional:* grupo (idade ou comunidade).

**Conexão:**

- peso (intensidade do contato);
- ativa (sim/não), que muda quando há isolamento.

### 4.5 Parâmetros da epidemia

O enunciado do tema cita taxa de contágio, recuperação e isolamento. Sugestão:

| Parâmetro | Significado |
|---|---|
| β (contágio) | Probabilidade base de transmissão por contato a cada passo, modulada pelo peso da aresta |
| γ (recuperação) | Probabilidade de recuperação por passo, ou duração da infecção |
| Isolamento | Estratégia, fração de nós isolados e dia de início |
| Pacientes zero | Quantidade e escolha dos infectados iniciais |
| Passos e semente | Duração da simulação e semente do gerador aleatório, para reproduzir resultados |

### 4.6 Algoritmos estudados e onde aplicá-los

| Conteúdo da disciplina | Uso no simulador | Prioridade |
|---|---|---|
| **Representação (lista de adjacência)** | Estrutura base. É a adequada para redes esparsas. | Essencial |
| **BFS** | Propagação em "gerações" a partir dos infectados, distância em saltos, alcance potencial | Essencial |
| **DFS e conectividade** | Componentes conexas. O tamanho da maior componente indica o teto da epidemia. | Essencial |
| **Separabilidade (articulações e pontes)** | Alvos de isolamento estrutural. É o diferencial do projeto. | Essencial |
| **Árvores** | Árvore de contágio (quem infectou quem), registrada durante a simulação e visualizada | Essencial |
| **Dijkstra** | Caminho de transmissão mais provável entre dois indivíduos (usando custo = −log da probabilidade) e tempo mínimo de chegada | Desejável |
| **AGM (Prim e Kruskal)** | "Esqueleto" da rede para visualização | Opcional |
| Floyd-Warshall, Bellman-Ford | O(V³) é inviável em redes grandes. Sem uso claro. | Dispensável |
| Hamiltoniano/Euleriano, Isomorfismo, Emparelhamento | Sem relação natural com o tema | Dispensável |
| Fluxo máximo | Corte mínimo para isolamento ótimo seria interessante, mas é complexo | Extensão futura |
| Ordenação topológica | Só serviria em variantes direcionadas | Dispensável |

O **núcleo** é: lista de adjacência, BFS, DFS/componentes, articulações e pontes, e árvore de contágio. Dijkstra é bom de ter, e o resto fica de fora. O enunciado não exige usar todos os algoritmos.

---

## 5. O que já basta e o que exige estudo

**Já visto na disciplina (suficiente para o núcleo):**
representação de grafos, BFS, DFS, conectividade, separabilidade, árvores, Dijkstra. Confirmar nos slides 09 se articulações e pontes foram cobertas. Se não foram, entram no bloco abaixo.

**Conceitos que provavelmente exigem estudo adicional:**

- Modelo SIR: conceito simples, 1 a 2 horas de leitura.
- Simulação estocástica em passos discretos e repetição de execuções (Monte Carlo), com média dos resultados.
- Geradores de redes aleatórias, se usarem dados sintéticos: Erdős–Rényi, Barabási–Albert (hubs) e Watts–Strogatz (mundo pequeno). São fáceis de implementar.
- Detecção de pontos de articulação e pontes pelo método dos tempos de descoberta e *low-link* (Tarjan), que é uma extensão da DFS.
- Métricas de resultado: pico de infectados, dia do pico, taxa de ataque final (fração que se infectou), duração.
- Centralidade de grau (trivial). Closeness e betweenness são opcionais e mais pesadas.
- Visualização de grafos (layout de posições dos nós) e a ferramenta de interface escolhida.

**Modelos epidemiológicos possíveis:**

- **SIR (recomendado):** simples e suficiente.
- **SIS:** variação em que o recuperado volta a ser suscetível.
- **SEIR:** inclui incubação. Só se sobrar tempo.
- Vacinação como extensão do isolamento.

Não é preciso resolver equações diferenciais nem estudar modelos avançados.

---

## 6. UML e artefatos de modelagem

| Artefato | Objetivo | Importância |
|---|---|---|
| **Diagrama de classes** | Estrutura do software (Grafo, Individuo, Conexao, Simulacao, Estrategia de isolamento, etc.) | Alta |
| **Casos de uso** | O que o usuário pode fazer (carregar rede, configurar parâmetros, simular, comparar estratégias) | Alta |
| **Diagrama de estados** | Ciclo do indivíduo: Suscetível → Infectado → Recuperado (e isolado) | Alta |
| **Diagrama de sequência** | Interação entre interface, simulação e grafo ao executar uma simulação | Média/alta |
| **Diagrama de atividades** | Fluxo de um passo da simulação | Média |
| **Diagrama de componentes** | Visão da arquitetura em módulos | Baixa |
| **Wireframes das telas** (não é UML) | Esboço da interface gráfica exigida na Etapa 2 | Média/alta |
| **Desenho de um grafo exemplo** (não é UML) | Ilustrar a modelagem com 8 a 10 nós | Alta |

Para ferramenta de desenho, PlantUML ou draw.io servem. Versionar os arquivos-fonte no repositório e exportar as imagens para o LaTeX.

---

## 7. Estrutura sugerida para o documento

1. **Introdução**: contexto, motivação, objetivos
2. **Descrição do problema**
   - 2.1 Pergunta de pesquisa
   - 2.2 Escopo e limites
   - 2.3 Modelo epidemiológico e parâmetros
   - 2.4 Métricas de avaliação
3. **Dados**: fonte (Kaggle ou geradores), formato, pré-processamento previsto
4. **Modelagem do grafo**
   - 4.1 Vértices, arestas e atributos
   - 4.2 Tipo do grafo e justificativas
   - 4.3 Estrutura de dados escolhida
   - 4.4 Exemplo ilustrado
5. **Algoritmos**: tabela de algoritmo, funcionalidade e complexidade esperada
6. **Modelagem UML**: casos de uso, classes, estados, sequência
7. **Arquitetura e interface**: módulos, tecnologias, wireframes
8. **Plano de desenvolvimento**: requisitos, divisão de responsabilidades, cronograma, riscos e mitigação
9. **Estratégia de validação**: como testar a correção e comparar o desempenho (aqui o NetworkX pode ser usado só para comparação)
10. **Referências**

---

## 8. Organização do repositório Git

```
/
├── README.md
├── .gitignore
├── docs/
│   ├── etapa1/        (main.tex, template SBC, figuras/)
│   ├── diagramas/     (fontes .puml ou .drawio + imagens exportadas)
│   └── decisoes.md    (ata das decisões do grupo)
├── data/              (README com a fonte; arquivos grandes fora do Git)
├── src/
│   ├── grafo/         (estrutura de grafo)
│   ├── algoritmos/    (BFS, DFS, articulações, Dijkstra)
│   ├── epidemia/      (modelo, simulação, estratégias)
│   ├── dados/         (leitura e geradores)
│   └── interface/
├── tests/
└── experimentos/      (scripts e resultados)
```

**Estratégia de commits:**

- `main` estável. Todo trabalho em branches `feat/...`, `docs/...` ou `fix/...`, integradas por pull request **revisado por outro integrante**.
- Commits pequenos e frequentes, com prefixo (`docs:`, `feat:`, `fix:`, `test:`) e mensagem clara.
- Cada um commita **com o próprio usuário e e-mail configurados**, porque os commits individuais são avaliados. Nunca commitar pelo colega.
- Usar issues ou um quadro de tarefas para registrar quem faz o quê. Isso também comprova as responsabilidades pedidas no relatório.
- Evitar um commit gigante no fim. O histórico ao longo do tempo é parte da avaliação.

---

## Recomendação final: como começar

**Decisões conjuntas (reunião de 1 hora):**

1. **Linguagem** entre C/C++, Java e Python. Python é mais rápido para desenvolver e para a interface, mas Java ou C++ são mais rápidos com redes grandes. Escolher pela familiaridade do grupo.
2. **Pergunta central** (a da seção 4.1 ou uma variação).
3. **Modelo:** SIR, ou SIR com extensões.
4. **Dados:** dataset de rede do Kaggle, geradores próprios, ou os dois.
5. **Escopo de algoritmos:** o núcleo da seção 4.6 mais Dijkstra, sim ou não.
6. **Tecnologia da interface** (desktop ou web).
7. **Perguntas ao professor:** (a) bibliotecas apenas de *desenhar* grafos (visualização) são permitidas? (b) o dataset escolhido é adequado? (c) o documento da Etapa 1 pode já ser no template SBC?

**Primeiras tarefas:**

- **A:** redigir o problema, o SIR com parâmetros e as métricas. Pesquisar 2 ou 3 datasets no Kaggle. Fazer o diagrama de estados.
- **B:** definir a estrutura do grafo e os atributos, estudar articulações e pontes, montar a tabela de algoritmos e rascunhar o diagrama de classes.
- **C:** organizar o repositório, instalar o template SBC, esboçar os wireframes e montar o cronograma.
