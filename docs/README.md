# Documentação do simulador

- [Problema e epidemiologia](epidemiologia/problema-e-epidemiologia.md) e [PDF](epidemiologia/problema-e-epidemiologia.pdf).
- [Modelagem do grafo vigente](modelagem/ModelagemGrafo.md).
- [Proposta de modelagem de classes](modelagem/simulador-epidemias/modelagem-de-classes.md).
- [Referências do projeto](referencias/REFERENCIAS.md).
- [Bases observadas preparadas para a etapa 3](../dados/dados/redes_reais/README.md).
- [Metodologia e configuração-base da etapa 3](../dados/dados/experimentos/README.md).
- [Controles ER/BA gerados e caracterizados](../dados/dados/redes_sinteticas/controles-etapa3-v1/README.md).
- [Resultados dos experimentos de topologia — 6.300 trajetórias](../dados/dados/experimentos/topologia-v1/README.md).
- [Aviso ao integrante B sobre os experimentos](implementacao/Aviso-IntegranteB-Etapa3.md).
- [Simulação, resultados, API e exportação](implementacao/SimulacaoResultados.md).
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

Amplie o SVG para consultar o diagrama de classes. Epidemiologia e diagramas especificam uma configuração de referência proposta: rede estática, intensidade como peso padrão e isolamento por orçamento; probabilidade direta e os três mecanismos seguem os contratos documentados de isolamento.py. Infectados iniciais podem ser manuais ou sorteados; dinâmica e q diário têm menor prioridade. A confirmação coletiva e a compatibilização com os documentos dos demais módulos continuam pendentes; esses artefatos não comprovam implementação.
