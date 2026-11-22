# Conferência da modelagem com a implementação

Revisão de 22/11/2026 para a consolidação do relatório SBC. Foram consultadas as fontes e exportações já existentes de casos de uso, estados e classes, o PDF de sequência e os módulos atuais do domínio. Os diagramas originais foram preservados; não foi criado um substituto para eles.

Os documentos da Etapa 1 registram o projeto anterior à implementação. O relatório técnico descreve os contratos atuais; o diagrama completo de classes e o PDF de sequência originais não devem ser apresentados como inventário literal das assinaturas Python atuais.

| Artefato | Conferência e interpretação |
| --- | --- |
| [Casos de uso](diagramas/casos-de-uso/casos-de-uso.puml) | Seleção/importação e geração, configuração, validação, execução, comparação e consulta possuem correspondência na aplicação. O desenho é uma visão funcional resumida; não enumera todos os controles e downloads. |
| [Estados](diagramas/estados-individuo/estados-individuo.puml) | S→I→R, ausência de reinfecção e regiões independentes para isolamento correspondem a `Individuo`. Recuperação conserva isolamento. O controle temporal só prepara intervenção em instante não terminal, antes do registro e da próxima transição. A figura incluída no SBC é a exportação original, sem redesenho. |
| [Classes de projeto](diagramas/classes-dominio/classes-dominio.puml) | As entidades, adjacências compartilhadas, associações de contatos, estratégias e separação do motor permanecem pertinentes. Há diferenças de contratos e ciclo de vida discriminadas abaixo. A figura de classes centrais já existente no relatório mostra somente o núcleo da rede, sem substituir o desenho completo. |
| [Sequência de projeto](<diagramas/diagrama-de-sequncia/D.Sequencia Grafos.pdf>) | Preserva a intenção de validar, executar passos síncronos e calcular indicadores. A interface atual acessa a API e recebe o histórico completo; não chama uma transição Python por clique. A criação e o registro do resultado diferem do desenho inicial, conforme a tabela abaixo. |

## Contratos usados no relatório final

| Tema do desenho inicial | Implementação consultada |
| --- | --- |
| Parâmetros da intervenção diretamente em `ConfiguracaoSimulacao` | [configuracao.py](../../../src/simulador/configuracao.py) separa `ConfiguracaoIntervencao`, opcional, de `ConfiguracaoSimulacao`; ambas são dataclasses congeladas. Os IDs resolvidos são tuplas. |
| Seleção devolvendo `set[Individuo]` | [estrategias_isolamento.py](../../../src/simulador/estrategias_isolamento.py) devolve `tuple[int, ...]`. Os mecanismos são aplicados por [isolamento.py](../../../src/simulador/isolamento.py), fora da seleção. |
| Gerador recebendo semente e nome de fluxo | [aleatoriedade.py](../../../src/simulador/aleatoriedade.py) recebe uma semente. A configuração e o executor mantêm instâncias separadas para iniciais, epidemia e isolamento. |
| `MotorSIR` devolvendo `RegistroPasso` na sequência | [motor_sir.py](../../../src/simulador/motor_sir.py) aplica transições e retorna `None`; [simulacao.py](../../../src/simulador/simulacao.py) controla relógio e cria os registros. |
| Resultado mutável criado na inicialização e alimentado por `registrar()` | `Simulacao` mantém o histórico durante o cálculo. Ao concluir, cria [ResultadoSimulacao](../../../src/simulador/resultado.py), congelado, com histórico em tupla, configuração, métricas e motivo. Não há a sequência de chamadas `registrar()/concluir()` no resultado atual. |
| Manifesto dentro do resultado de domínio | [comparacao_api.py](../../../src/simulador/comparacao_api.py) acrescenta manifesto na serialização; o manipulador HTTP acrescenta o ID da sessão. O resultado Python permanece independente do transporte. |
| Métricas construídas com população, registros e motivo | [metricas.py](../../../src/simulador/metricas.py) recebe histórico e população. A propriedade `duracao_extincao` preserva ausência em censura; o resultado identifica o motivo de término. |

As seções 3, 4 e 5 do SBC adotam esses contratos, incluindo o isolamento em Q(t) no próprio instante e a reprodução local do histórico. A conferência não altera a atribuição de autoria dos artefatos nem transforma uma decisão de implementação posterior em decisão original da Etapa 1.
