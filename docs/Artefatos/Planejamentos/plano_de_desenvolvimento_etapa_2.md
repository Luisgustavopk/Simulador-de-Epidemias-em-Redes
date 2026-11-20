# Plano de Desenvolvimento: Etapa 2 — Implementação (Núcleo + Interface)

Este documento estabelece o cronograma de execução, a divisão equilibrada de responsabilidades entre os integrantes (A, B e C), as diretrizes de controle de versão (Git) e a matriz de riscos para a **Etapa 2 (Implementação do Núcleo, Algoritmos e Interface)** do Simulador de Epidemias em Redes (Modelo SIR).

## 1. Diretrizes Gerais e Governança do Projeto

Para garantir a qualidade técnica, a participação igualitária na codificação e o cumprimento das restrições acadêmicas:

* **Restrição Tecnológica (RNF01):** Toda a estrutura de dados do grafo (listas de adjacência, vértices e arestas), algoritmos de percurso/análise e o motor estocástico SIR serão implementados **nativamente em Python (3.10+)**, sendo estritamente vedado o uso de bibliotecas de grafos prontas (ex: `NetworkX`, `igraph`).
* **Estratégia de Desenvolvimento por Fatias Verticais:** Cada integrante é responsável por desenvolver tanto o seu módulo de domínio (*back-end*) quanto a respectiva tela/aba na interface gráfica (*front-end*), evitando gargalos e conflitos de edição simultânea.
* **Fluxo de Trabalho no Git:**
  * A branch `main` conterá apenas código estável, testado e integrado.
  * O desenvolvimento ocorrerá em branches dedicadas por integrante/fatia (ex: `feat/rede-ui`, `feat/motor-parametros-ui`, `feat/simulacao-resultados-ui`).
  * Toda integração na `main` exigirá *Pull Request* revisado por pelo menos um outro integrante do grupo.
  * Todos os integrantes devem manter histórico de *commits* individuais, atômicos e semânticos.

## 2. Planejamento da Etapa 2: Implementação (Núcleo + Interface)

**Objetivo da Etapa 2:** Implementar de forma modular e paralela todas as funcionalidades de domínio (grafos, motor SIR, isolamento, ciclo temporal e métricas) conectadas às suas respectivas telas/abas funcionais da interface gráfica.

### 2.1. Divisão Equilibrada de Tarefas (Etapa 2)

#### **Integrante A — Topologia de Rede (Domínio) + Tela de Carga e Inspeção (UI)**
* **Núcleo (Lógica):**
  * Implementar nativamente as classes `RedeContatos`, `Individuo` e `Contato` utilizando listas de adjacência para grafos não direcionados e ponderados.
  * Desenvolver os leitores/parsers de arquivos externos (redes observadas) e os geradores de redes sintéticas (RF01).
  * Implementar algoritmos nativos de busca (BFS/DFS) para verificação de conectividade/componentes e cálculo de grau estrutural.
* **Interface Gráfica (UI):**
  * Desenvolver a **Aba/Área 1 (Carga e Inspeção da Rede)**: componentes para seleção de arquivo externo ou geração sintética, exibição de resumo estrutural (número de nós, arestas, grau médio) e mensagens de validação estrutural.

#### **Integrante B — Motor SIR e Isolamento (Domínio) + Tela de Parâmetros e Intervenção (UI)**
* **Núcleo (Lógica):**
  * Implementar a classe `MotorSIR` com atualização síncrona passo a passo ($t \rightarrow t+1$), aplicando as probabilidades combinadas de infecção ($\beta$) e recuperação ($\gamma$) (RF06).
  * Implementar `GeradorAleatorio` encapsulando sementes (*seeds*) controladas e independentes para garantir reprodutibilidade estatística (RNF02).
  * Implementar as estratégias de intervenção (`EstrategiaIsolamento` aleatória e por grau estrutural) e `ConfiguracaoSimulacao` com regras de validação de limites (RF02, RF03, RF04, RF05).
* **Interface Gráfica (UI):**
  * Desenvolver a **Aba/Área 2 (Configuração de Parâmetros e Isolamento)**: formulários rotulados com indicação de obrigatoriedade para taxas ($\beta, \gamma$), IDs iniciais, sementes, orçamento/estratégia de isolamento e feedback visual claro para entradas inválidas (RNF03).

#### **Integrante C — Orquestração Temporal e Métricas (Domínio) + Tela de Execução e Resultados (UI)**
* **Núcleo (Lógica):**
  * Implementar a classe `Simulacao` gerenciando o ciclo por passos discretos ($t \rightarrow t+1$), os critérios de parada (extinção do surto ou limite de passos) e o disparo agendado das intervenções.
  * Implementar `RegistroPasso`, `ResultadoSimulacao` e `MetricasEpidemia` para armazenar o histórico ($S, I, R$, isolados) e calcular pico de infecção, instante do pico e fração acumulada (RF08, RF10).
* **Interface Gráfica (UI):**
  * Desenvolver a **Aba/Área 3 e 4 (Execução e Consulta de Resultados)**: controles de disparo da simulação, exibição do motivo de término, plotagem das curvas epidemiológicas ($S, I, R$, isolados) e painel de métricas finais (RF09).

### 2.2. Marcos de Entrega da Etapa 2

1. **Marco 2.1 (Núcleo Validado):** Classes de domínio (`RedeContatos`, `ConfiguracaoSimulacao`, `MotorSIR`, `EstrategiaIsolamento`, `Simulacao` e `ResultadoSimulacao`) implementadas e validadas com testes unitários.
2. **Marco 2.2 (Telas Individuais Operacionais):** Cada integrante conclui sua respectiva aba/área da interface conectada à sua lógica de domínio.
3. **Marco 2.3 (Unificação da Interface):** Integração das áreas na janela principal do aplicativo (RNF03), permitindo o fluxo completo ponta a ponta.

## 3. Matriz de Riscos e Mitigação (Etapa 2)

| Risco Identificado | Probabilidade | Impacto | Ação Preventiva / Plano de Mitigação |
| :--- | :--- | :--- | :--- |
| **Desempenho lento** em redes grandes devido à implementação nativa em Python | Média | Alto | Utilizar estruturas nativas eficientes (dicionários e conjuntos `set` para listas de adjacência com busca $O(1)$) e evitar cópias desnecessárias do grafo a cada passo. |
| **Inconsistência visual** entre as telas desenvolvidas separadamente pelos integrantes | Média | Médio | Definir previamente um guia simples de estilos (paleta, fontes, tamanhos de janela e layout de abas) antes de iniciar a codificação da UI. |
| **Divergência na integração** entre as fatias dos integrantes A, B e C | Média | Alto | Seguir rigorosamente as assinaturas de métodos e tipos definidos no Diagrama de Classes e nos Diagramas de Sequência da Etapa 1. |
| **Perda de reprodutibilidade** nos experimentos comparativos | Baixa | Alto | Isolar as instâncias de `GeradorAleatorio` por processo (epidemia vs. escolha de isolamento) e registrar a semente utilizada em cada `ResultadoSimulacao`. |