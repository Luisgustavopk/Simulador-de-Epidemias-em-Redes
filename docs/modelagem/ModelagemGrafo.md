# Modelagem do grafo

## Objetivo e escopo mínimo

O **Simulador de Epidemias em Redes** deve representar uma rede de indivíduos e simular a propagação de doenças ou informações, permitindo ajustar parâmetros como taxa de contágio, recuperação e isolamento.

Esta modelagem atende à alternativa de **propagação de doenças**, utilizando o modelo SIR. Para cumprir o escopo mínimo, o simulador deve:

- Representar os indivíduos e seus contatos por meio de um grafo.
- Simular a propagação da doença entre indivíduos conectados ao longo de sucessivas iterações.
- Permitir que o usuário ajuste as taxas de contágio, recuperação e isolamento.
- Atualizar o estado epidemiológico dos indivíduos e a condição de isolamento durante a execução.

## Modelo adotado

A simulação utiliza o modelo epidemiológico **SIR**, no qual cada indivíduo pode estar em um dos seguintes estados:

- **S — Suscetível (*Susceptible*):** indivíduo suscetível à infecção.
- **I — Infectado (*Infected*):** indivíduo infectado.
- **R — Recuperado ou removido (*Recovered*):** indivíduo recuperado ou removido da população considerada pelo modelo.

## Parâmetros ajustáveis

Para a versão mínima, a simulação é organizada em passos discretos. As taxas são interpretadas como **probabilidades por iteração**, com valores entre **0 e 1**, e devem ser configuráveis pelo usuário antes da execução.

| Parâmetro | Descrição |
| --- | --- |
| `taxaContagio` | Probabilidade básica de um indivíduo infectado transmitir a doença a um indivíduo suscetível durante um contato em uma iteração. Controla a transição de S para I. |
| `taxaRecuperacao` | Probabilidade de um indivíduo infectado se recuperar em uma iteração. Controla a transição de I para R. |
| `taxaIsolamento` | Probabilidade de um indivíduo infectado que ainda não está isolado passar para isolamento em uma iteração. |

A `taxaContagio` é um parâmetro global da simulação. O `peso` de uma aresta descreve um contato específico e deve ser considerado no cálculo da probabilidade de transmissão desse contato.

## Tipo de grafo

O grafo é **não direcionado, simples e ponderado**. As arestas representam contatos sem orientação, não há laços nem múltiplas arestas entre o mesmo par de vértices, e cada aresta possui um peso associado.

## Vértices

Cada vértice representa um indivíduo.

## Arestas

Cada aresta representa um contato entre dois indivíduos, por meio do qual pode ocorrer a transmissão do vírus.

## Pesos

O peso de uma aresta pode representar:

- **Probabilidade de transmissão:** chance de o vírus ser transmitido durante o contato.
- **Intensidade do contato:** medida associada a fatores como a duração do contato e a proximidade entre os indivíduos.

Essas são interpretações alternativas. O significado do peso deve ser definido de acordo com a configuração adotada para a simulação.

## Representação

- **Lista de adjacência:** representação principal do grafo.
- **Matriz de adjacência:** representação alternativa.
- **Lista de arestas:** representação alternativa.

A classe [`Grafo`](../../src/simulador/grafo.py) implementa a lista de adjacência com indivíduos indexados por identificador e vizinhanças indexadas pelos identificadores dos contatos. Cada aresta é compartilhada pelas duas direções da conexão e contabilizada uma única vez.

## Topologia

Uma **topologia estática** é suficiente para a versão mínima. As configurações possíveis são:

- **Estática:** a estrutura de vértices e arestas permanece inalterada durante a simulação.
- **Dinâmica (extensão opcional):** a estrutura pode ser atualizada a cada iteração, com operações como a adição ou a remoção de indivíduos.

## Isolamento

O isolamento pode ser representado de duas formas:

- **Remoção do indivíduo da rede:** exclusão do vértice que representa o indivíduo e das arestas associadas a ele.
- **Isolamento lógico:** manutenção do indivíduo na rede, com redução dos pesos ou desativação das arestas que o conectam aos demais indivíduos.

O **isolamento lógico** permite atender ao requisito mínimo mantendo os indivíduos na rede. O parâmetro `taxaIsolamento` controla a entrada de indivíduos infectados nessa condição.

## Ciclo da simulação

Antes da execução, devem ser definidos a rede, os indivíduos inicialmente infectados, os parâmetros ajustáveis e o limite de iterações.

Em cada iteração, o simulador deve:

1. Avaliar a entrada em isolamento dos indivíduos infectados, de acordo com `taxaIsolamento`, e aplicar seus efeitos aos contatos.
2. Avaliar novas infecções entre indivíduos suscetíveis conectados a indivíduos infectados, considerando `taxaContagio`, os pesos das arestas e os efeitos do isolamento.
3. Avaliar a recuperação dos indivíduos infectados, de acordo com `taxaRecuperacao`.
4. Aplicar as transições de estado e registrar as quantidades de indivíduos suscetíveis, infectados, recuperados e isolados.

As novas infecções e recuperações devem ser calculadas com base nos estados epidemiológicos do início da iteração e aplicadas em conjunto ao final. Assim, um indivíduo infectado nessa etapa só poderá transmitir a doença a partir da iteração seguinte.

A execução termina quando não houver mais indivíduos infectados ou quando o limite de iterações for atingido.

## Atributos do vértice (indivíduo)

- **`id`:** identificador inteiro do indivíduo; sua unicidade na rede será controlada pelo grafo.
- **`estado`:** estado epidemiológico atual do indivíduo (S, I ou R).
- **`isolamento`:** valor booleano que indica se o indivíduo está isolado.
- **`dia_inicio_infeccao`:** dia em que o indivíduo foi infectado, quando aplicável. Este é o nome adotado em Python para o atributo inicialmente descrito como `diaInicioInfeccao`.

## Atributos da aresta (conexão entre dois indivíduos)

- **`peso`:** valor que representa a probabilidade de transmissão do vírus ou a intensidade do contato, conforme a interpretação adotada na simulação.
- **`ativa`:** valor booleano que indica se a conexão está ativa, permitindo representar o isolamento por meio da desativação da aresta.
- **`origem`:** referência ao vértice que representa o primeiro indivíduo da conexão.
- **`destino`:** referência ao vértice que representa o segundo indivíduo da conexão.

Como o grafo é não direcionado, os nomes `origem` e `destino` identificam apenas as duas extremidades da aresta, sem atribuir uma direção à conexão.

## Observações

- O estado epidemiológico (`estado`) e a condição de isolamento (`isolamento`) são registrados separadamente. Assim, um indivíduo pode estar **infectado e isolado ao mesmo tempo**.
- A passagem para o estado R e a exclusão do vértice são operações distintas. A remoção do indivíduo da rede depende da configuração adotada para a simulação.

## Referências do projeto

As referências fornecidas para consulta estão registradas em [REFERENCIAS.md](../referencias/REFERENCIAS.md), no padrão ABNT e com links públicos para as obras.

Os dois trabalhos sobre passeios aleatórios representam os vértices como localidades, entre as quais os indivíduos se deslocam. Essa abordagem deve ser distinguida da modelagem adotada neste projeto, em que os vértices representam indivíduos e as arestas representam contatos.
