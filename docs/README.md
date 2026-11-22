# Documentação do simulador

- **[Etapa 1 — PDF único: descrição do problema, justificativa da modelagem e plano de desenvolvimento](Artefatos/Etapa1-Problema-Modelagem-Plano.pdf)**, com os diagramas UML.
- **[Etapa 2 — PDF da implementação da aplicação](Artefatos/Etapa2-Implementacao-Aplicacao.pdf)**, com arquitetura, funcionalidades, telas, contribuições e verificações.
- **[Etapa 3 — Relatório técnico final em PDF, formato SBC](Artefatos/Etapa3-Relatorio-Tecnico.pdf)**, com 15 páginas, resultados dos 33 lotes, desempenho, discussão e conclusões.
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

## Diagramas da proposta de projeto

| Diagrama | Fonte editável | Imagem vetorial | Imagem PNG |
|---|---|---|---|
| Casos de uso | [PlantUML](modelagem/simulador-epidemias/diagramas/casos-de-uso/casos-de-uso.puml) | [SVG](modelagem/simulador-epidemias/diagramas/casos-de-uso/casos-de-uso.svg) | [PNG](modelagem/simulador-epidemias/diagramas/casos-de-uso/casos-de-uso.png) |
| Estados do indivíduo | [PlantUML](modelagem/simulador-epidemias/diagramas/estados-individuo/estados-individuo.puml) | [SVG](modelagem/simulador-epidemias/diagramas/estados-individuo/estados-individuo.svg) | [PNG](modelagem/simulador-epidemias/diagramas/estados-individuo/estados-individuo.png) |
| Classes de projeto | [PlantUML](modelagem/simulador-epidemias/diagramas/classes-dominio/classes-dominio.puml) | [SVG](modelagem/simulador-epidemias/diagramas/classes-dominio/classes-dominio.svg) | [PNG](modelagem/simulador-epidemias/diagramas/classes-dominio/classes-dominio.png) |

Amplie o SVG para consultar o diagrama de classes. O [PDF da Etapa 1](Artefatos/Etapa1-Problema-Modelagem-Plano.pdf) apresenta a modelagem, as responsabilidades dos componentes e os diagramas. A aplicação oferece dois modos de peso, iniciais manuais ou sorteados e três mecanismos de isolamento por orçamento. Topologia com agenda temporal e política diária q ficam fora do executor.
