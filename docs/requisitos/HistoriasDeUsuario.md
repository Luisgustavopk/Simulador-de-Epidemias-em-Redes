# Histórias de usuário — Simulador de Epidemias em Redes

## Como ler este documento

As histórias seguem o formato **Como** [ator], **quero** [ação], **para** [benefício]. Cada uma apresenta critérios de aceitação, prioridade, complexidade e vínculo com os requisitos de origem.

Este documento especifica o comportamento esperado do produto; não representa uma declaração de funcionalidades já implementadas.

## Atores

| Ator | Papel no sistema |
| --- | --- |
| Usuário acadêmico | Seleciona a rede, configura o modelo SIR e as intervenções, executa simulações e comparações e consulta os resultados. |

O sistema executa automaticamente a validação, as atualizações da simulação e o registro do histórico. 

## Regras de negócio que valem para todas as histórias

- **RN1. Rede de contatos.** A rede observada ou sintética é representada por um grafo não direcionado e ponderado. Os indivíduos possuem IDs únicos e as arestas representam contatos.
- **RN2. Estados epidemiológicos.** Cada indivíduo pertence a exatamente um estado SIR: suscetível (S), infectado (I) ou recuperado/removido epidemiologicamente (R). As transições do modelo são S → I e I → R.
- **RN3. Isolamento independente.** Isolamento é uma condição separada do estado SIR e pode ser aplicado a indivíduos S, I ou R. A quantidade de isolados não constitui um quarto estado e não deve ser somada a S + I + R.
- **RN4. Estratégia e mecanismo.** A estratégia escolhe as pessoas a isolar, de forma aleatória ou por grau estrutural. O mecanismo define o efeito sobre os contatos: desativação, redução dos pesos ou exclusão da rede de contatos. Excluir um indivíduo dessa rede não equivale a recuperá-lo nem a mudar automaticamente seu estado para R.
- **RN5. Orçamento populacional.** O orçamento limita a quantidade de pessoas abrangidas pela intervenção, e não o número de arestas afetadas. Nas comparações, as estratégias usam o mesmo orçamento de pessoas.
- **RN6. Validação obrigatória.** Tanto a execução individual quanto a comparação com repetições incluem a validação de todas as entradas. Uma configuração inválida não pode iniciar o motor.
- **RN7. Atualização síncrona.** As transições do passo t → t + 1 usam os estados epidemiológicos do início do passo e são aplicadas em conjunto ao final. Um indivíduo recém-infectado não transmite nem se recupera no mesmo passo em que se infectou.
- **RN8. Comparação consistente.** Dentro de cada repetição, os cenários comparados partem da mesma rede, dos mesmos parâmetros epidemiológicos e das mesmas condições iniciais. Mantêm também o mesmo orçamento populacional; diferenças de intervenção são identificadas nos resultados.
- **RN9. Reprodutibilidade.** A mesma configuração completa, incluindo rede, condições iniciais e sementes dos processos aleatórios, deve produzir a mesma trajetória epidemiológica e os mesmos resultados.
- **RN10. Término identificado.** A execução termina pela ausência de infectados ou por atingir o limite de passos. O motivo fica associado ao histórico e aos resultados daquela execução.

## Convenções adotadas nos critérios de aceitação

Para tornar os critérios verificáveis, este documento explicita as seguintes convenções de especificação:

- **Tempo e inicialização:** o passo representa um dia do modelo. O dia 0 registra a condição inicial; cada atualização produz o registro do dia seguinte. O limite de passos é um inteiro positivo. Os IDs selecionados começam em I e os demais indivíduos começam em S, pois as fontes não preveem uma entrada para recuperados iniciais.
- **Conjunto inicial vazio:** é permitido representar uma população sem infectados. Nesse caso, registra-se o dia 0 e a execução termina por ausência de infectados, sem realizar transições.
- **População de referência:** N₀ é o total de indivíduos no início da execução. A exclusão usada como intervenção afeta os contatos, mas preserva o registro epidemiológico das pessoas. Sem entradas ou saídas demográficas, S(t) + I(t) + R(t) = N₀.
- **Métricas:** o pico é o maior valor de I(t), incluindo o dia 0. Se houver empate, o dia do pico é a primeira ocorrência. A fração acumulada é a quantidade de indivíduos infectados ao menos uma vez, incluindo os infectados iniciais, dividida por N₀; cada pessoa entra uma única vez no numerador.
- **Término simultâneo:** se a ausência de infectados ocorrer exatamente no limite de passos, o motivo principal é a extinção do surto. O total de passos realizados continua registrado.
- **Repetições:** sementes e identificadores são registrados por repetição e cenário. Repetir a mesma semente com a mesma configuração reproduz a execução; para obter novas realizações estocásticas, utilizam-se sementes distintas. A política de associação de sementes entre estratégias deve ser documentada.

## Rede de contatos

### US01 · Carregar uma rede observada

**Como** usuário acadêmico, **quero** carregar uma rede de contatos a partir de um arquivo externo, **para** simular a propagação de uma epidemia em uma rede observada.

- Posso escolher um arquivo em um dos formatos declarados como suportados pelo sistema.
- A importação identifica os indivíduos, seus contatos e os pesos das arestas, formando um grafo não direcionado e ponderado (RN1).
- O esquema do arquivo informa como representar IDs, contatos e pesos, incluindo a regra adotada quando o arquivo não fornece pesos.
- Arquivos ilegíveis, linhas malformadas, IDs inconsistentes e pesos incompatíveis com a interpretação selecionada geram mensagens que permitem localizar e corrigir o problema.
- Uma importação inválida não é disponibilizada como rede válida para execução.
- Após a importação, posso conferir a origem da rede e as quantidades de indivíduos e contatos carregados.

**Prioridade:** Alta  
**Complexidade:** Alta — compartilhada com a US02 no RF01.  
**Requisitos relacionados:** RF01, RF05 e RNF01.

### US02 · Gerar uma rede sintética

**Como** usuário acadêmico, **quero** gerar uma rede sintética a partir de um modelo e de seus parâmetros, **para** estudar a propagação em estruturas de contato controladas.

- Posso selecionar um modelo de geração suportado e informar seus parâmetros, incluindo o número de indivíduos.
- A interface informa os parâmetros exigidos pelo modelo e rejeita combinações que não permitam gerar uma rede válida.
- A rede gerada possui IDs únicos e é não direcionada e ponderada (RN1).
- Posso conferir o modelo utilizado e as quantidades de indivíduos e contatos gerados.
- Quando a geração utiliza aleatoriedade, a semente é controlada e registrada, permitindo reconstruir a mesma rede com os mesmos parâmetros.
- A geração utiliza algoritmos implementados pelo grupo, conforme RNF01. Erdős–Rényi e Barabási–Albert são exemplos citados na análise de complexidade; os modelos efetivamente exigidos precisam ser definidos pela equipe.

**Prioridade:** Alta  
**Complexidade:** Alta — compartilhada com a US01 no RF01.  
**Requisitos relacionados:** RF01, RNF01 e RNF02.

### US03 · Configurar a interpretação dos pesos e a topologia

**Como** usuário acadêmico, **quero** configurar a interpretação dos pesos e a topologia da rede entre as opções suportadas, **para** que os contatos representem as hipóteses do experimento.

- Posso identificar a interpretação adotada para os pesos e a regra usada para convertê-los em probabilidades de transmissão.
- A regra de transmissão produz probabilidades entre 0 e 1 e é aplicada de forma consistente em toda a execução.
- A configuração identifica a topologia utilizada e informa se a estrutura de contatos permanece estática ou se admite mudanças ao longo dos passos.
- O caráter não direcionado e ponderado da rede é preservado. A referência à topologia no diagrama não estabelece, por si só, a obrigatoriedade de oferecer uma topologia dinâmica.
- A interpretação dos pesos e a topologia utilizadas ficam associadas à configuração da execução e são mantidas entre os cenários de uma comparação, salvo a alteração causada pela intervenção estudada.

**Prioridade:** Não atribuída no PDF — complemento explícito do diagrama.  
**Complexidade:** Não classificada separadamente na lista fornecida.  
**Requisitos relacionados:** Complementa RF01, RF05, RF06 e RF07.

## Parâmetros e condições iniciais

### US04 · Configurar os parâmetros epidemiológicos

**Como** usuário acadêmico, **quero** informar as taxas de transmissão β e de recuperação γ, **para** ajustar o comportamento epidemiológico da simulação.

- Posso informar valores numéricos finitos para β e γ no intervalo fechado de 0 a 1.
- Os valores 0 e 1 são aceitos para ambos os parâmetros.
- Campos vazios, textos, valores não finitos e números fora do intervalo são rejeitados com identificação do campo a corrigir.
- Os parâmetros validados ficam disponíveis para revisão e são os mesmos efetivamente utilizados pelo motor.

**Prioridade:** Alta  
**Complexidade:** Baixa.  
**Requisitos relacionados:** RF02 e RF05.

### US05 · Definir os infectados iniciais e o limite de passos

**Como** usuário acadêmico, **quero** informar os IDs dos infectados iniciais e o limite de passos, **para** definir o ponto de partida e a duração máxima do experimento.

- Posso selecionar ou informar um conjunto de IDs pertencentes à rede carregada ou gerada.
- IDs inexistentes são identificados e impedem a execução até a correção.
- Um mesmo ID não pode representar duas pessoas nem aumentar artificialmente a contagem de infectados iniciais.
- O limite de passos aceita apenas um inteiro positivo.
- Antes da execução, posso conferir o conjunto de infectados iniciais e o limite configurado.
- O dia 0 e o caso sem infectados iniciais seguem as convenções deste documento.

**Prioridade:** Média  
**Complexidade:** Média.  
**Requisitos relacionados:** RF03 e RF05.

## Isolamento e validação

### US06 · Configurar a intervenção de isolamento

**Como** usuário acadêmico, **quero** escolher a estratégia, o mecanismo, o orçamento populacional e o início do isolamento, **para** avaliar como a intervenção altera a propagação da epidemia.

- Posso escolher entre seleção aleatória de pessoas e seleção baseada no grau estrutural dos indivíduos na rede.
- Posso escolher o mecanismo de desativação de contatos, redução dos pesos ou exclusão da rede de contatos, conforme o diagrama.
- Posso informar o orçamento de pessoas e o passo de início da intervenção. O início é um inteiro não negativo e deve ser compatível com o horizonte configurado.
- O orçamento convertido em pessoas não pode ser negativo nem maior que a população disponível; orçamento zero representa ausência de pessoas isoladas pela intervenção.
- A intervenção respeita o orçamento populacional e pode selecionar indivíduos S, I ou R, mantendo o isolamento separado do estado epidemiológico (RN3 a RN5).
- A redução de pesos exige uma intensidade válida e informa seu efeito. A desativação e a exclusão impedem os contatos abrangidos conforme a regra do mecanismo escolhido.
- A seleção aleatória utiliza uma semente controlada. A regra de cálculo do grau e o desempate da seleção por grau são documentados e reproduzíveis.
- A configuração completa da intervenção fica vinculada aos resultados da execução.

**Prioridade:** Alta  
**Complexidade:** Média.  
**Requisitos relacionados:** RF04, RF05 e RNF02.

### US07 · Validar a configuração antes de executar

**Como** usuário acadêmico, **quero** que a configuração seja validada e que os problemas sejam identificados antes da execução, **para** corrigir entradas incompatíveis e obter resultados consistentes.

- A validação verifica a presença de uma rede válida e não vazia, os parâmetros β e γ, os IDs iniciais e o limite de passos.
- Também verifica a interpretação dos pesos, a topologia e a coerência da estratégia, do mecanismo, do orçamento e do início do isolamento.
- Para comparações, verifica ainda o número de repetições e as condições comuns entre os cenários.
- Enquanto houver erros, os comandos de execução ficam indisponíveis. Uma tentativa de execução por outro ponto de entrada também deve ser recusada pela validação centralizada.
- As mensagens identificam os problemas e preservam os dados já informados para correção.
- Alterar uma entrada depois de validá-la exige nova validação antes de iniciar o motor.
- Tanto “Executar simulação” quanto “Executar comparação com repetições” realizam essa validação, conforme as relações «include» do diagrama.

**Prioridade:** Alta  
**Complexidade:** Média.  
**Requisitos relacionados:** RF05, com verificação das entradas de RF01 a RF04 e RF07.

## Execução e comparação

### US08 · Executar uma simulação estocástica

**Como** usuário acadêmico, **quero** executar a simulação com a configuração validada e uma semente controlada, **para** observar a evolução da epidemia e reproduzir o experimento.

- A execução somente começa depois da validação da configuração (US07).
- O motor avança em passos discretos t → t + 1 e aplica as transições S → I e I → R de forma síncrona (RN7).
- A transmissão considera os contatos, a interpretação dos pesos e o efeito do isolamento configurado, a partir do passo previsto para sua aplicação.
- Os processos aleatórios utilizam geradores com sementes registradas. A recuperação de infectados continua possível durante o isolamento.
- A mesma configuração completa e as mesmas sementes reproduzem exatamente a trajetória e os resultados (RN9).
- O estado inicial e cada passo concluído são registrados no histórico (US10).
- A execução termina ao não haver infectados ou ao atingir o limite de passos, mantendo o resultado disponível para consulta.

**Prioridade:** Alta  
**Complexidade:** Alta.  
**Requisitos relacionados:** RF06, RF05, RF08 e RNF02.

### US09 · Comparar estratégias com repetições

**Como** usuário acadêmico, **quero** executar cenários repetidos com estratégias de intervenção diferentes e condições comparáveis, **para** avaliar a eficácia das estratégias diante da variabilidade estocástica.

- Posso informar as estratégias a comparar e um número inteiro positivo de repetições.
- A comparação somente começa depois da validação da configuração (US07).
- Em cada repetição, os cenários usam a mesma rede de partida, os mesmos parâmetros β e γ, os mesmos infectados iniciais e o mesmo limite de passos.
- As estratégias comparadas utilizam o mesmo orçamento de pessoas. Para uma comparação somente entre estratégias de seleção, o mecanismo, sua intensidade e o início do isolamento também permanecem iguais.
- Cada cenário começa de uma cópia independente da condição inicial; estados e contatos alterados por uma execução não contaminam a seguinte.
- Cada resultado identifica a repetição, a estratégia, a configuração e as sementes utilizadas.
- Posso consultar os históricos, as curvas e as métricas de cada cenário, identificando a qual repetição pertencem.
- Reexecutar o experimento com a mesma configuração e a mesma sequência de sementes reproduz os resultados. O método de agregação estatística entre repetições será definido pela equipe.

**Prioridade:** Média  
**Complexidade:** Média.  
**Requisitos relacionados:** RF07, RF05, RF08, RF09, RF10 e RNF02.

## Histórico e resultados

### US10 · Consultar o histórico diário e o motivo do término

**Como** usuário acadêmico, **quero** consultar as contagens diárias e o motivo do término de cada execução, **para** acompanhar a evolução da população e interpretar o resultado.

- O sistema registra o dia 0 e, após cada atualização concluída, o dia e as quantidades de S, I, R e isolados.
- As contagens de um dia correspondem ao mesmo instante da simulação e não misturam estados anteriores e posteriores à atualização.
- Os isolados continuam incluídos em um dos estados SIR; a soma S + I + R corresponde à população acompanhada, conforme RN3 e a convenção de N₀.
- A execução registra o motivo do término: extinção do surto ou limite de passos.
- O histórico identifica o último dia registrado e o total de passos realizados, inclusive quando a execução termina no dia 0.
- Em comparações, os registros ficam separados por cenário e repetição e sustentam as curvas e as métricas exibidas.
- O registro é automático, sem exigir uma ação do usuário a cada dia. O RF08 não exige, por si só, exportação em arquivo ou persistência entre sessões.

**Prioridade:** Alta  
**Complexidade:** Média.  
**Requisitos relacionados:** RF08 e o caso de uso de consulta do motivo do término.

### US11 · Consultar as curvas epidemiológicas

**Como** usuário acadêmico, **quero** visualizar as curvas de suscetíveis, infectados e recuperados ao longo do tempo, **para** analisar a evolução da epidemia e o efeito das intervenções.

- O gráfico utiliza os dados do histórico da execução selecionada e apresenta as séries S, I e R.
- O eixo horizontal identifica os dias/passos e o vertical identifica a quantidade de indivíduos; as séries possuem identificação legível.
- Os valores apresentados correspondem às contagens registradas, incluindo o dia 0 e o último dia da execução.
- Em comparações, posso identificar a estratégia e a repetição associadas a cada curva consultada.
- Quando não houver uma execução disponível, a interface informa que é necessário executá-la antes de consultar resultados.
- A consulta gráfica é obrigatória. A atualização do gráfico durante a execução não está estabelecida como exigência nas fontes.

**Prioridade:** Alta  
**Complexidade:** Alta.  
**Requisitos relacionados:** RF09 e RF08.

### US12 · Consultar as métricas finais

**Como** usuário acadêmico, **quero** consultar o pico de infecção e a fração acumulada de infectados, **para** resumir o impacto da epidemia e comparar os resultados dos cenários.

- O resultado apresenta o pico de infectados como o maior valor de I(t) no histórico e informa o primeiro dia em que esse pico ocorreu.
- A fração acumulada corresponde ao total de pessoas infectadas ao menos uma vez, incluindo os infectados iniciais, dividido por N₀, conforme as convenções deste documento.
- A fração é apresentada entre 0 e 1 ou como percentual equivalente, com a unidade identificada. Somar I(t) ao longo dos dias não pode contar novamente uma mesma pessoa para essa métrica.
- O painel identifica a execução, os passos realizados e o motivo do término, permitindo interpretar métricas de uma simulação interrompida pelo limite de passos.
- Em comparações, as métricas ficam identificadas por estratégia e repetição, com as mesmas definições e unidades.
- As métricas são consistentes com o histórico e com a condição inicial, inclusive no caso sem infectados.

**Prioridade:** Alta  
**Complexidade:** Baixa.  
**Requisitos relacionados:** RF10 e RF08.

## Requisitos não funcionais

Estes itens são condições técnicas e de qualidade que sustentam as histórias.

### RNF01 · Implementação nativa dos grafos e do motor

A estrutura de grafo, os algoritmos de busca e análise e o motor de simulação devem ser implementados pelo grupo, sem bibliotecas de grafos prontas como NetworkX.

- A importação e a geração de redes alimentam estruturas implementadas pelo grupo.
- O cálculo de grau e a execução SIR utilizam os algoritmos do projeto, sem delegar essas responsabilidades a bibliotecas prontas de grafos ou simulação.
- A restrição não equivale a uma proibição geral de bibliotecas de interface ou plotagem; sua utilização deve respeitar as demais regras do projeto.

**Prioridade:** Alta.

### RNF02 · Reprodutibilidade estatística

Execuções com a mesma configuração completa e as mesmas sementes devem produzir exatamente os mesmos resultados e trajetórias epidemiológicas.

- As sementes dos processos aleatórios, a rede e a configuração utilizadas ficam associadas à execução.
- Geração de rede, seleção aleatória de pessoas e transições epidemiológicas possuem aleatoriedade controlada.
- A ordem de processamento e os critérios de desempate não introduzem variações não controladas.
- A verificação compara o histórico completo e as métricas finais de duas execuções equivalentes, e não apenas resultados estatisticamente próximos.

**Prioridade:** Alta.

### RNF03 · Organização visual do fluxo de trabalho

A interface gráfica apresenta áreas visualmente separadas para carga da rede, configuração, execução e consulta dos resultados, permitindo realizar o fluxo completo sem depender de um manual.

- A área de rede permite identificar se a origem é observada ou sintética.
- A configuração reúne os parâmetros epidemiológicos, as condições iniciais e as intervenções.
- A execução indica a disponibilidade dos comandos conforme a validação e o estado da execução.
- Os resultados permitem consultar curvas, métricas e motivo do término da execução selecionada.
- Mensagens e rótulos permitem compreender o próximo passo e corrigir entradas inválidas no próprio fluxo.

**Prioridade:** Média.

## Complexidade dos requisitos funcionais


| Requisito | Complexidade | Justificativa |
| --- | --- | --- |
| RF01 · Seleção de rede observada ou sintética | Alta | Exige leitura e parsing nativo de arquivos externos, como listas de adjacência ou CSV, e algoritmos próprios de geração de redes sintéticas, como Erdős–Rényi ou Barabási–Albert, sem bibliotecas prontas como NetworkX. Os formatos e modelos citados são exemplos, sujeitos à definição do escopo. |
| RF02 · Configuração de parâmetros epidemiológicos | Baixa | Envolve captura e validação, pela interface, de valores numéricos de ponto flutuante para β e γ entre 0 e 1. |
| RF03 · Definição das condições iniciais | Média | Requer validar e mapear os IDs informados, garantindo que pertencem aos nós existentes, além de validar o limite de passos. |
| RF04 · Configuração das regras de isolamento | Média | Envolve seleção de estratégias aleatórias ou baseadas em grau estrutural e aplicação de cotas populacionais, associadas ao mecanismo e ao início da intervenção. |
| RF05 · Validação da configuração | Média | Exige uma rotina centralizada que cruze as entradas antes de liberar a execução, garantindo consistência matemática e estrutural. |
| RF06 · Execução da simulação estocástica | Alta | Envolve o ciclo temporal discretizado t → t + 1, a atualização síncrona dos estados SIR e o controle dos geradores pseudoaleatórios com sementes para garantir repetibilidade. |
| RF07 · Execução de comparações com repetições | Média | Depende de uma camada de controle sobre o motor para executar múltiplos cenários com condições equivalentes e manter seus resultados separados. |
| RF08 · Registro do histórico diário | Média | Exige estruturar o histórico por passo temporal, armazenando as contagens S, I, R e isolados e identificando a condição de término. |
| RF09 · Consulta de curvas epidemiológicas | Alta | Envolve plotagem gráfica das curvas temporais a partir dos dados do motor e atualização da visualização conforme o resultado consultado. |
| RF10 · Consulta de métricas finais | Baixa | Baseia-se em cálculos diretos sobre o histórico e os totais consolidados, como o pico de infectados e a fração acumulada, para exibição em painel. |

## Matriz de rastreabilidade com os requisitos funcionais

| Requisito do PDF | Prioridade | Complexidade | Histórias |
| --- | --- | --- | --- |
| RF01 · Selecionar rede observada ou sintética | Alta | Alta | US01, US02; US03 complementa a configuração da rede. |
| RF02 · Configurar parâmetros epidemiológicos | Alta | Baixa | US04 |
| RF03 · Definir condições iniciais e limite de passos | Média | Média | US05 |
| RF04 · Configurar regras de isolamento | Alta | Média | US06 |
| RF05 · Validar a configuração da simulação | Alta | Média | US07, incluída em US08 e US09. |
| RF06 · Executar simulação estocástica | Alta | Alta | US08 |
| RF07 · Executar comparações com repetições | Média | Média | US09 |
| RF08 · Registrar histórico diário e motivo do término | Alta | Média | US10; fornece dados para US11 e US12. |
| RF09 · Consultar curvas epidemiológicas | Alta | Alta | US11 |
| RF10 · Consultar métricas finais | Alta | Baixa | US12 |

## Matriz de rastreabilidade com os casos de uso

| Elemento do diagrama | Histórias e regras relacionadas |
| --- | --- |
| Selecionar rede observada ou sintética | US01, US02 |
| Configurar interpretação do peso e topologia da rede | US03 |
| Configurar parâmetros SIR e condições iniciais | US04, US05 |
| Configurar estratégia, mecanismo, orçamento e início do isolamento | US06 |
| Executar simulação | US08 |
| Executar comparação com repetições | US09 |
| Validar configuração, incluída nas duas modalidades de execução | US07, US08, US09; RN6. |
| Consultar curvas SIR, métricas e motivo do término | US10, US11, US12 |
| Isolamento independente do estado S, I ou R | US06, US10; RN3. |
| Mecanismos de desativação, redução de pesos ou exclusão | US06; RN4. |
| Mesma rede, parâmetros e condições iniciais por repetição | US09; RN8. |
| Mesmo orçamento de pessoas entre estratégias interventivas | US06, US09; RN5 e RN8. |

## Matriz de rastreabilidade com os requisitos não funcionais

| Requisito do PDF | Prioridade | Histórias sustentadas |
| --- | --- | --- |
| RNF01 · Restrição ao uso de bibliotecas de grafos | Alta | US01, US02, US03, US06, US08, US09 |
| RNF02 · Reprodutibilidade estatística | Alta | US02, US06, US08, US09; histórico e resultados de US10 a US12. |
| RNF03 · Organização visual do fluxo de trabalho | Média | US01 a US12. |