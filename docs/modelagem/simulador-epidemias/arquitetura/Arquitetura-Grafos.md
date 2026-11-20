# Arquitetura do Sistema

A arquitetura do simulador foi projetada seguindo o princípio de separação de
responsabilidades e modularidade, dividindo o sistema nos módulos essenciais de
domínio e interface que se articulam para realizar a simulação estocástica da
epidemia em redes.

## 1. Descrição dos Módulos e Comunicação

- **Módulo de Grafo (domínio da rede):** responsável por gerenciar a topologia
  estática do grafo não direcionado e ponderado através de listas de
  adjacência, mantendo os vértices (`Individuo`) e arestas (`Contato`). Valida
  internamente a consistência estrutural dos pares e pesos.

- **Módulo de Algoritmos (seleção para isolamento e buscas):** contém as
  estratégias de intervenção, como isolamento aleatório e por grau estrutural,
  e os algoritmos de percurso e conectividade necessários para a análise
  estrutural da rede. Cada estratégia é responsável por validar seus próprios
  parâmetros de preparo antes da execução.

- **Módulo de Dados (configuração e resultados):** responsável pelo carregamento
  ou geração das redes e pelo salvamento do histórico de execução
  (`RegistroPasso` e `MetricasEpidemia`). A responsabilidade de validação de
  entradas é distribuída: a classe de configuração valida os limites numéricos
  e probabilísticos, enquanto os módulos especializados validam suas próprias
  restrições de domínio.

- **Módulo de Simulação (execução):** núcleo de controle temporal da ferramenta.
  A classe `Simulacao` gerencia o ciclo por passos discretos (`t → t + 1`), o
  controle do fluxo, o acionamento do cronograma de intervenções e a
  consolidação do resultado.

  Em contrapartida, a classe `MotorSIR` assume exclusivamente a responsabilidade
  de calcular as regras probabilísticas de infecção combinada e recuperação,
  utilizando geradores estocásticos independentes (`GeradorAleatorio`).

- **Módulo de Interface (interface e apresentação):** camada responsável por
  intermediar a interação com o usuário acadêmico, coletando parâmetros,
  acionando o controlador de simulação e plotando as curvas epidemiológicas e
  métricas consolidadas.

## 2. Tecnologias Escolhidas

- **Linguagem de programação:** Python (versão 3.10 ou posterior), escolhida
  pela familiaridade do grupo e pela agilidade no desenvolvimento das
  estruturas de dados e da visualização.

- **Estruturação de dados:** implementação nativa e própria das estruturas de
  grafos e dos algoritmos de simulação, cumprindo rigorosamente a restrição de
  proibição de bibliotecas externas de grafos, como NetworkX.

- **Controle de versão:** Git, com versionamento estruturado em branches e
  histórico de commits individuais para cada integrante.

## 3. Decisões Ainda Pendentes

- Confirmação final da base de dados de redes reais, como datasets obtidos no
  Kaggle, que serão utilizadas nos testes experimentais.

- Definição exata da biblioteca gráfica que será empregada para renderizar a
  interface de usuário na Etapa 2, como Tkinter, PyQt ou frameworks web leves.
