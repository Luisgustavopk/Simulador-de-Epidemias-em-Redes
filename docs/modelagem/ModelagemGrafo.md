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

Para a versão mínima, a simulação é organizada em passos discretos: **cada iteração corresponde a um dia do modelo**. As taxas são interpretadas como **probabilidades por dia**, com valores entre **0 e 1**, e devem ser configuráveis pelo usuário antes da execução.

| Parâmetro | Descrição |
| --- | --- |
| `taxaContagio` (β) | Probabilidade básica de transmissão em um contato de peso 1 durante um dia. O peso ajusta essa probabilidade conforme a regra abaixo. Controla a transição de S para I. |
| `taxaRecuperacao` (γ) | Probabilidade de um indivíduo infectado se recuperar em um dia. Controla a transição de I para R e também se aplica aos infectados isolados. |
| `taxaIsolamento` (q) | Probabilidade de um indivíduo infectado que ainda não está isolado entrar em isolamento no início de um dia. Controla a entrada nessa condição, e não a eficácia do isolamento. |

A `taxaContagio` é um parâmetro global da simulação. O `peso` de uma aresta descreve um contato específico e deve ser considerado no cálculo da probabilidade de transmissão desse contato.

## Tipo de grafo

O grafo é **não direcionado, simples e ponderado**. As arestas representam contatos sem orientação, não há laços nem múltiplas arestas entre o mesmo par de vértices, e cada aresta possui um peso associado.

## Vértices

Cada vértice representa um indivíduo.

## Arestas

Cada aresta representa um contato entre dois indivíduos, por meio do qual pode ocorrer a transmissão do vírus.

## Pesos e probabilidade de transmissão

Na versão inicial, o peso representa a **intensidade relativa do contato**. Ele deve ser finito e não negativo: peso 0 representa exposição nula, peso 1 é o contato de referência e peso 2 corresponde ao dobro dessa intensidade. Valores fracionários e acima de 1 são aceitos.

Para um contato permitido entre um indivíduo infectado e um suscetível, a probabilidade diária será:

$$
p_{ij} = \min(1, \beta \cdot w_{ij})
$$

O limite superior garante que a probabilidade não ultrapasse 100%. A intensidade não é tratada como uma probabilidade por si só.

Exemplo com `taxaContagio = 0,20`:

| Peso do contato | Probabilidade diária de transmissão |
| --- | --- |
| 0 | 0% |
| 0,5 | 10% |
| 1 | 20% |
| 2 | 40% |
| 6 | 100%, pelo limite superior |

Se a base não fornecer pesos, cada contato receberá peso 1. Quando os pesos forem construídos a partir de duração ou frequência, a unidade de referência deve ser documentada e aplicada de forma consistente. Uma unidade de peso terá o mesmo significado dentro do experimento.

A regra linear com limite superior é uma **escolha de modelagem deste projeto**. Koher et al. discutem diferentes interpretações para os pesos e uma ponderação linear da transmissão; o teto adotado aqui complementa essa regra para os pesos acima de 1 aceitos pelas classes. Essa regra não é atribuída ao EPIGUI, que utiliza redes não ponderadas. Ver [referências bibliográficas](../referencias/REFERENCIAS.md).

### Vários vizinhos infectados

Para um suscetível exposto a vários vizinhos infectados, adotamos independência condicional entre as tentativas de transmissão, dados os estados e os contatos daquele dia. A probabilidade de pelo menos uma transmissão será:

$$
P_j = 1 - \prod_{i \in \mathcal{I}_j}(1 - p_{ij})
$$

O conjunto `I_j` contém apenas os vizinhos infectados com contato permitido. Sem vizinhos elegíveis, a probabilidade é zero. O motor fará **um sorteio por suscetível**, usando a probabilidade combinada, e registrará no máximo uma nova infecção por indivíduo no dia.

Por exemplo, duas exposições com probabilidades 20% e 40% resultam em `1 - (0,80 × 0,60) = 52%`. As probabilidades dos contatos não são somadas.

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

A versão inicial adota **isolamento lógico total**, mantendo todos os indivíduos e contatos na estrutura do grafo. A transmissão por uma aresta só será permitida quando todas as condições abaixo forem atendidas:

- A aresta está ativa: `aresta.ativa == True`.
- Nenhum dos dois extremos está isolado.
- Um extremo está infectado e o outro está suscetível no início do dia.

Se qualquer extremo estiver isolado ou a aresta estiver inativa, a probabilidade de transmissão por esse contato será **zero**, independentemente do peso.

### Entrada e duração

No início de cada dia, cada infectado ainda não isolado terá uma tentativa de entrada em isolamento com probabilidade `taxaIsolamento`. Quem não entrar poderá ser novamente avaliado no dia seguinte, se continuar infectado e sem isolamento.

- Com q = 0, não há novas entradas automáticas em isolamento; condições de isolamento já existentes continuam sendo respeitadas.
- Com q = 1, todos os infectados elegíveis entram em isolamento antes da avaliação do contágio daquele dia.
- O isolamento de um infectado dura até sua recuperação. O motor deverá liberar essa condição ao aplicar a transição I → R no final do dia. O método `Individuo.recuperar()` continua responsável apenas pela transição de estado; a liberação exige uma chamada explícita a `liberar_isolamento()` pelo motor.
- Um indivíduo que já começa isolado terá essa restrição respeitada desde o dia 0. Se não houver uma transição I → R, a condição permanece até uma liberação explícita.

A probabilidade de recuperação permanece igual para infectados isolados e não isolados.

### Preservação dos contatos

O isolamento será avaliado pelos indicadores dos indivíduos, **sem sobrescrever `peso` ou `ativa`**. Assim, liberar um indivíduo não reativa uma aresta que estava inativa por outro motivo e não libera um contato cujo outro extremo ainda está isolado.

O método `Grafo.vizinhos()` continuará retornando os vizinhos estruturais, incluindo contatos bloqueados. O motor filtrará os contatos permitidos. A redução parcial dos contatos poderá ser estudada como extensão futura; a regra da versão inicial é o bloqueio total.

## Ciclo da simulação

Antes da execução, devem ser definidos a rede, os indivíduos inicialmente infectados, os parâmetros ajustáveis e o limite de iterações.

A condição inicial é registrada no dia 0. Em cada passo do dia t para o dia t + 1, o simulador deve:

1. Registrar os valores dos estados epidemiológicos no início do dia. Como os modelos são mutáveis, guardar apenas uma tupla de referências aos indivíduos não preserva esses valores.
2. Avaliar a entrada em isolamento dos infectados iniciais do dia, de acordo com `taxaIsolamento`. As novas restrições já afetam os contatos desse passo.
3. Avaliar as novas infecções, usando os estados iniciais, os contatos permitidos e a probabilidade combinada por suscetível.
4. Avaliar a recuperação de todos os infectados iniciais, incluindo os isolados, de acordo com `taxaRecuperacao`.
5. Aplicar em conjunto as transições S → I e I → R no final do passo. As novas infecções recebem `dia_inicio_infeccao = t + 1`; os indivíduos que se recuperam são liberados do isolamento.
6. Registrar as quantidades de suscetíveis, infectados, recuperados e isolados no dia t + 1.

Um recém-infectado só poderá transmitir, recuperar-se ou entrar automaticamente em isolamento a partir do passo seguinte. Um infectado que vai se recuperar no final do dia ainda pode transmitir durante esse dia se seus contatos estiverem permitidos.

Os sorteios de isolamento, contágio e recuperação serão distintos. A recuperação não reutilizará o sorteio que avaliou a entrada em isolamento.

A execução termina quando não houver mais indivíduos infectados ou quando o limite de iterações for atingido.

## Atributos do vértice (indivíduo)

- **`id`:** identificador inteiro do indivíduo; sua unicidade na rede será controlada pelo grafo.
- **`estado`:** estado epidemiológico atual do indivíduo (S, I ou R).
- **`isolamento`:** valor booleano que indica se o indivíduo está isolado.
- **`dia_inicio_infeccao`:** dia em que o indivíduo foi infectado, quando aplicável. Este é o nome adotado em Python para o atributo inicialmente descrito como `diaInicioInfeccao`.

## Atributos da aresta (conexão entre dois indivíduos)

- **`peso`:** intensidade relativa do contato, representada por um número finito e não negativo. A probabilidade de transmissão é calculada a partir de `taxaContagio` e desse peso.
- **`ativa`:** valor booleano que indica a disponibilidade direta do contato. Uma aresta inativa bloqueia a transmissão; o isolamento dos indivíduos não sobrescreve esse atributo.
- **`origem`:** referência ao vértice que representa o primeiro indivíduo da conexão.
- **`destino`:** referência ao vértice que representa o segundo indivíduo da conexão.

Como o grafo é não direcionado, os nomes `origem` e `destino` identificam apenas as duas extremidades da aresta, sem atribuir uma direção à conexão.

## Observações

- O estado epidemiológico (`estado`) e a condição de isolamento (`isolamento`) são registrados separadamente. Assim, um indivíduo pode estar **infectado e isolado ao mesmo tempo**.
- A passagem para o estado R e a exclusão do vértice são operações distintas. Na versão inicial, os vértices são mantidos e a soma S + I + R permanece igual à população total. Os isolados são contados separadamente, pois também pertencem a um dos estados S, I ou R.

## Referências do projeto

As referências fornecidas para consulta estão registradas em [REFERENCIAS.md](../referencias/REFERENCIAS.md), no padrão ABNT e com links públicos para as obras.

Os dois trabalhos sobre passeios aleatórios representam os vértices como localidades, entre as quais os indivíduos se deslocam. Essa abordagem deve ser distinguida da modelagem adotada neste projeto, em que os vértices representam indivíduos e as arestas representam contatos.
