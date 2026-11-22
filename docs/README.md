# Documentação do simulador

- **[Etapa 1 — PDF único: descrição do problema, justificativa da modelagem e plano de desenvolvimento](Artefatos/Etapa1-Problema-Modelagem-Plano.pdf)**, com os diagramas UML.
- **[Etapa 2 — PDF da implementação da aplicação](Artefatos/Etapa2-Implementacao-Aplicacao.pdf)**, com arquitetura, funcionalidades, telas, contribuições e verificações.
- [Problema e epidemiologia — documentação detalhada](epidemiologia/problema-e-epidemiologia.md).
- [Modelagem do grafo — registro de projeto](modelagem/ModelagemGrafo.md).
- [Proposta de modelagem de classes](modelagem/simulador-epidemias/modelagem-de-classes.md).
- [Referências do projeto](referencias/REFERENCIAS.md).
- [Bases observadas preparadas para a etapa 3](../dados/dados/redes_reais/README.md).
- [Metodologia e configuração-base da etapa 3](../dados/dados/experimentos/README.md).
- [Controles ER/BA gerados e caracterizados](../dados/dados/redes_sinteticas/controles-etapa3-v1/README.md).
- [Resultados dos experimentos de topologia — 6.300 trajetórias](../dados/dados/experimentos/topologia-v1/README.md).
- [Aviso ao integrante B sobre os experimentos](implementacao/Aviso-IntegranteB-Etapa3.md).
- [Simulação, resultados, API e exportação](implementacao/SimulacaoResultados.md).
- [Roteiro do vídeo de demonstração — 16 minutos, com plano de slides para a apresentação presencial](apresentacao/Roteiro-Video-Demonstracao.md).
- [PDF das falas do vídeo, por integrante](apresentacao/Falas-Video-Demonstracao.pdf).
- [PDF do passo a passo do vídeo, com tempos de tela](apresentacao/Passo-a-Passo-Video-Demonstracao.pdf).
- [Apresentação presencial: Canva, PDF e notas](apresentacao/slides/README.md).
- [Amostra de vídeo: importação escolar em 30 segundos](apresentacao/video/Amostra-Importacao-Escola-30s.mp4).
- [Roteiro de apresentação e perguntas — Integrante A: Wesley](apresentacao/Roteiro-IntegranteA-Wesley.md).
- [Guia de estudo dos resultados de topologia — Integrante A: Wesley](apresentacao/Resultados-Etapa3-IntegranteA-Wesley.md).
- [Roteiro de apresentação e perguntas — Integrante B: Luis](apresentacao/Roteiro-IntegranteB-Luis.md).
- [Roteiro de apresentação e perguntas — Integrante C: João](apresentacao/Roteiro-IntegranteC-Joao.md).
- [Guia de funções por arquivo — Integrante A: Wesley](apresentacao/Funcoes-IntegranteA-Wesley.md).
- [Guia de funções por arquivo — Integrante B: Luis](apresentacao/Funcoes-IntegranteB-Luis.md).
- [Guia de funções por arquivo — Integrante C: João](apresentacao/Funcoes-IntegranteC-Joao.md).

## Diagramas da proposta de projeto

| Diagrama | Fonte editável | Imagem vetorial | Imagem PNG |
|---|---|---|---|
| Casos de uso | [PlantUML](modelagem/simulador-epidemias/diagramas/casos-de-uso/casos-de-uso.puml) | [SVG](modelagem/simulador-epidemias/diagramas/casos-de-uso/casos-de-uso.svg) | [PNG](modelagem/simulador-epidemias/diagramas/casos-de-uso/casos-de-uso.png) |
| Estados do indivíduo | [PlantUML](modelagem/simulador-epidemias/diagramas/estados-individuo/estados-individuo.puml) | [SVG](modelagem/simulador-epidemias/diagramas/estados-individuo/estados-individuo.svg) | [PNG](modelagem/simulador-epidemias/diagramas/estados-individuo/estados-individuo.png) |
| Classes de projeto | [PlantUML](modelagem/simulador-epidemias/diagramas/classes-dominio/classes-dominio.puml) | [SVG](modelagem/simulador-epidemias/diagramas/classes-dominio/classes-dominio.svg) | [PNG](modelagem/simulador-epidemias/diagramas/classes-dominio/classes-dominio.png) |

Amplie o SVG para consultar o diagrama de classes. O [PDF da Etapa 1](Artefatos/Etapa1-Problema-Modelagem-Plano.pdf) apresenta a modelagem, as responsabilidades dos componentes e os diagramas. A aplicação oferece dois modos de peso, iniciais manuais ou sorteados e três mecanismos de isolamento por orçamento. Topologia com agenda temporal e política diária q ficam fora do executor.
