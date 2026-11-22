# Plano de Desenvolvimento: Etapa 3 — Experimentação, Comparação e Entrega Final

Este documento estabelece o cronograma de execução, a divisão equilibrada de responsabilidades entre os integrantes (A, B e C), as diretrizes de controle de versão (Git) e a matriz de riscos para a **Etapa 3 (Integração Visual, Experimentação e Entrega Final)** do Simulador de Epidemias em Redes (Modelo SIR).

## 1. Diretrizes Gerais e Governança do Projeto

Para garantir a qualidade técnica, a participação igualitária na codificação e o cumprimento das restrições acadêmicas:

* **Restrição Tecnológica (RNF01):** Toda a estrutura de dados do grafo (listas de adjacência, vértices e arestas), algoritmos de percurso/análise e o motor estocástico SIR serão implementados **nativamente em Python (3.10+)**, sendo estritamente vedado o uso de bibliotecas de grafos prontas (ex: `NetworkX`, `igraph`).
* **Estratégia de Desenvolvimento por Fatias Verticais:** Cada integrante é responsável por desenvolver tanto o seu módulo de domínio (*back-end*) quanto a respectiva tela/aba na interface gráfica (*front-end*), evitando gargalos e conflitos de edição simultânea.
* **Fluxo de Trabalho no Git:**
  * A branch `main` conterá apenas código estável, testado e integrado.
  * O desenvolvimento ocorrerá em branches dedicadas por integrante/fatia (ex: `feat/rede-ui`, `feat/motor-parametros-ui`, `feat/simulacao-resultados-ui`).
  * Toda integração na `main` exigirá *Pull Request* revisado por pelo menos um outro integrante do grupo.
  * Todos os integrantes devem manter histórico de *commits* individuais, atômicos e semânticos.

## 2. Planejamento da Etapa 3: Experimentação, Comparação e Entrega Final

**Objetivo da Etapa 3:** Refinar a interface comparativa, executar baterias de experimentos com redes reais e sintéticas, analisar o impacto das estratégias de isolamento e consolidar o artigo/relatório técnico final (template SBC).

### 2.1. Divisão Equilibrada de Tarefas (Etapa 3)

#### **João — Datasets Reais, Experimentos Topológicos e Seção de Metodologia**
* **Implementação/Ajustes:** Refinar a importação de grandes redes observadas na UI e otimizar consultas de vizinhança se necessário.
* **Experimentação:** Selecionar e padronizar datasets de redes reais (ex: interação social) e gerar redes sintéticas de controle, executando cenários que avaliam o impacto da topologia na propagação.
* **Documentação SBC:** Redigir a caracterização estrutural das redes e a metodologia experimental no artigo.

#### **Wesley — Bateria de Comparações Estocásticas e Análise Estatística**
* **Implementação/Ajustes:** Implementar o suporte à execução de múltiplas repetições com sementes controladas na tela de configuração/execução (RF07).
* **Experimentação:** Rodar baterias comparativas entre: (1) cenário sem intervenção, (2) isolamento aleatório e (3) isolamento por grau estrutural, variando orçamento e passo de início.
* **Documentação SBC:** Consolidar médias e desvios-padrão das repetições e redigir a análise crítica sobre a eficácia das estratégias de isolamento.

#### **Luis — Visualização Comparativa na UI, Testes Finais e Consolidação SBC**
* **Implementação/Ajustes:** Aprimorar a tela de resultados para sobrepor/comparar graficamente curvas de diferentes estratégias e exportar gráficos em alta resolução (RF07, RF09).
* **Validação:** Executar testes de regressão verificando 100% dos Requisitos Funcionais (RF01–RF10) e Não Funcionais (RNF01–RNF03).
* **Documentação SBC:** Integrar todas as seções no template LaTeX da SBC, revisar diagramas UML, formatação e preparar o pacote final de entrega.

### 2.2. Marcos de Entrega da Etapa 3

1. **Marco 3.1 (Coleta Experimental):** Execução concluída de todas as baterias de simulação e armazenamento das tabelas e gráficos consolidados.
2. **Marco 3.2 (Redação do Artigo/Relatório):** Seções de Metodologia, Resultados, Análise Comparativa e Conclusão redigidas e revisadas.
3. **Marco 3.3 (Entrega Final):** Repositório Git limpo, código documentado e PDF final compilado no padrão SBC validado por todos os integrantes.

## 3. Matriz de Riscos e Mitigação (Etapa 3)

| Risco Identificado | Probabilidade | Impacto | Ação Preventiva / Plano de Mitigação |
| :--- | :--- | :--- | :--- |
| **Desempenho lento** em redes grandes devido à implementação nativa em Python | Média | Alto | Utilizar estruturas nativas eficientes (dicionários e conjuntos `set` para listas de adjacência com busca $O(1)$) e evitar cópias desnecessárias do grafo a cada passo. |
| **Inconsistência visual** entre as telas desenvolvidas separadamente pelos integrantes | Média | Médio | Definir previamente um guia simples de estilos (paleta, fontes, tamanhos de janela e layout de abas) antes de iniciar a codificação da UI. |
| **Divergência na integração** entre as fatias dos integrantes A, B e C | Média | Alto | Seguir rigorosamente as assinaturas de métodos e tipos definidos no Diagrama de Classes e nos Diagramas de Sequência da Etapa 1. |
| **Perda de reprodutibilidade** nos experimentos comparativos | Baixa | Alto | Isolar as instâncias de `GeradorAleatorio` por processo (epidemia vs. escolha de isolamento) e registrar a semente utilizada em cada `ResultadoSimulacao`. |