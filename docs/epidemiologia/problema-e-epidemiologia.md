# Etapa 1 - problema e epidemiologia

## 1. Introdução e contextualização


A propagação de uma doença transmissível depende das oportunidades de contato entre indivíduos. Essas oportunidades não se distribuem uniformemente: algumas pessoas mantêm muitos contatos, outras interagem principalmente em um mesmo grupo e determinados contatos conectam regiões pouco relacionadas da população.

Grafos permitem representar indivíduos como vértices e contatos potencialmente transmissores como arestas. Essa representação explicita quais pares podem interagir e permite incorporar diferenças de intensidade dos contatos. O estudo de modelos epidemiológicos em redes oferece uma base para investigar a relação entre a organização dessas conexões e a propagação [1].

A estrutura da rede pode modificar as oportunidades de exposição. Indivíduos com muitos vizinhos podem alcançar mais pessoas; agrupamentos podem concentrar a circulação; e conexões entre grupos podem permitir a chegada da infecção a outras regiões. Entretanto, essas propriedades não determinam isoladamente o resultado, que também depende dos parâmetros, dos infectados iniciais e dos eventos aleatórios.

Comparar estratégias de isolamento permite investigar se critérios diferentes de seleção de pessoas produzem comportamentos distintos sob um mesmo orçamento de intervenção. O isolamento aleatório constitui uma referência simples. A seleção por grau utiliza a estrutura da rede para priorizar indivíduos com maior número de contatos.

Propõe-se um **simulador acadêmico exploratório**, destinado à compreensão desses mecanismos e à aplicação de teoria dos grafos. O projeto não terá calibração com uma doença específica, validação clínica ou capacidade demonstrada de prever epidemias reais. Mesmo utilizando contatos observados, os resultados expressarão consequências das hipóteses do simulador sobre a representação adotada.

## 2. Problema de pesquisa e objetivos

### 2.1. Definição do problema

O problema consiste em representar uma população e seus contatos e planejar a evolução estocástica dos estados epidemiológicos. A ferramenta proposta permitirá comparar ausência de isolamento, seleção aleatória e seleção por grau sob condições controladas.

Cada vértice representa um indivíduo; cada aresta representa um contato potencialmente transmissor. O grafo é simples, sem laços nem contatos duplicados por par não ordenado, não direcionado e ponderado. A ausência de direção descreve o contato; a possibilidade de transmissão depende dos estados dos extremos. Lista de adjacência é a representação principal documentada.

O cadastro inclui indivíduos sem contatos. Na estrutura Python existente, RedeContatos, Contato e Individuo correspondem à rede, ao contato e à pessoa. Os nomes origem e destino identificam extremos, sem direção. O projeto reutiliza essas classes; não introduz outra estrutura paralela de grafo ou aresta.

### 2.2. Pergunta central

**Como a estrutura de uma rede de contatos influencia a propagação de uma epidemia simulada e, sob igual número de pessoas isoladas, como as estratégias aleatória e por grau alteram o pico de infectados e a fração acumulada em relação à ausência de isolamento?**

A comparação entre estruturas será um eixo complementar, utilizando redes sintéticas controladas. Uma estratégia adicional por posição estrutural exige justificativa, critério e orçamento próprios e não integra o mínimo.

### 2.3. Objetivo geral

Planejar um simulador estocástico SIR em rede para investigar a influência da estrutura e comparar estratégias de isolamento por indicadores definidos e reproduzíveis.

### 2.4. Objetivos específicos

1. Especificar transmissão, recuperação e atualização simultânea.
2. Definir parâmetros, domínios, condições iniciais e validação.
3. Definir seleção e efeito do isolamento separadamente do estado SIR.
4. Levantar bases candidatas e procedimentos de preparação.
5. Definir histórico, métricas, denominadores e censura.
6. Planejar cenários e repetições com condições controladas.
7. Representar interações, estados e responsabilidades por UML.

Nesta etapa, a verificação ocorre pela consistência das especificações; nas posteriores, por testes e experimentos a realizar. Não há resultados experimentais nesta contribuição.

### 2.5. Escopo, alternativas e prioridades

A configuração padrão proposta mantém população fechada, topologia estática e isolamento por orçamento. Incubação, reinfecção, vacinação e transmissão fora da rede não são previstas. Padrão não significa que as alternativas tenham sido descartadas ou já implementadas.

| Dimensão | Padrão proposto | Alternativa e prioridade |
|---|---|---|
| Topologia | Estática | Dinâmica, de menor prioridade; regras temporais precisam ser definidas antes da implementação. |
| Política de isolamento | Intervenção única por orçamento | Entrada diária de infectados com probabilidade q, de menor prioridade; protocolo separado. |
| Seleção por orçamento | Aleatória ou por grau, ambas previstas para comparação | Uma não substitui a outra; as duas usam o mesmo k. |
| Infectados iniciais | Seleção manual ou sorteio na interface | Ambas previstas; o sorteio registra e reutiliza os IDs escolhidos. |
| Peso | Intensidade normalizada | Probabilidade direta por contato e passo, explicitamente identificada. |
| Mecanismo de isolamento | Bloqueio lógico total | Redução parcial ou exclusão da rede de contatos, mantidas como alternativas documentadas. |

O diagrama de classes detalha a execução na referência estática por orçamento, com os dois modos de peso e as duas formas de preparação dos IDs. As alternativas dinâmica, q diário e mecanismos adicionais não são apresentadas como implementações concluídas. A ordem restante de implementação e sua inclusão na entrega dependem do planejamento coletivo.

### 2.6. Isolamento de pessoas e bloqueio de contatos

Isolar uma pessoa atua sobre seus contatos incidentes conforme o mecanismo. Bloquear uma aresta atua somente sobre aquela interação. O indicador ativa pode representar uma indisponibilidade própria do contato; sua presença não exige uma interface adicional de bloqueio de arestas. Ponto de articulação é vértice cuja remoção aumenta o número de componentes; ponte é uma aresta com esse efeito. Uma comparação entre essas intervenções exigiria outro critério de custo. O orçamento aqui é número de pessoas, não número de arestas afetadas.

## 3. Modelo epidemiológico SIR

### 3.1. Estados e hipóteses

| Estado | Significado |
|---|---|
| Suscetível (S) | Pode adquirir infecção pelos contatos permitidos com infectados. |
| Infectado (I) | Pode transmitir e está sujeito à recuperação, inclusive quando isolado. |
| Recuperado (R) | Não transmite nem volta a S durante a execução. Representa remoção epidemiológica, sem excluir a pessoa do grafo. |

O ciclo é S → I → R. A tradição dos modelos compartimentais de Kermack e McKendrick [2] fundamenta a organização SIR; as regras discretas aqui são propostas operacionais próprias. Todos têm os mesmos parâmetros epidemiológicos; a heterogeneidade resulta da rede e dos pesos. Estado e isolamento são condições independentes.

### 3.2. Tempo e condições iniciais

t = 0,1,2,... é índice inteiro; cada transição t → t+1 corresponde a um dia do modelo. Essa unidade não é calibrada com tempo de uma doença real. T_max é o número máximo de transições.

Os infectados iniciais são um conjunto explícito de IDs existentes, sem repetição; n₀ é seu tamanho, 0 ≤ n₀ ≤ N. Todos os demais começam em S, R(0)=0 e inicialmente não há isolados antes da intervenção. O conjunto vazio é permitido e produz extinção em t=0. A interface deve oferecer duas opções propostas: informar IDs manualmente ou informar quantidade n₀ e semente para sorteio uniforme sem reposição. O sorteio ocorre na preparação, usa fluxo próprio e mostra os IDs antes da execução. O conjunto resultante fica registrado e é reutilizado nos cenários da mesma repetição; não se sorteia novamente para cada estratégia. A escolha não depende de ferramenta externa à interface.

O campo dia_inicio_infeccao armazena None para quem nunca foi infectado, 0 para infectados iniciais e t+1 para novas infecções. Isolar um infectado inicial não o substitui nem o recupera.

### 3.3. Pesos e probabilidade por contato

Seja G=(V,E), N=|V|>0. O peso simétrico wᵤᵥ=wᵥᵤ é finito em [0,1], com interpretação identificada por configuração. **Intensidade é o modo padrão proposto.** Nesse modo, β é probabilidade por passo em contato de peso 1, com 0 ≤ β ≤ 1. Para contato permitido entre I e S:

**pᵤᵥ = β · wᵤᵥ**.

A relação linear é uma hipótese simplificadora, sem calibração empírica. Peso zero impede transmissão, mas não significa isolamento. Ausência de peso pode ser preparada como intensidade unitária, com essa escolha registrada; não se interpreta peso 1 como transmissão certa quando β<1.

Para duração acumulada dᵤᵥ ≥ 0 em janela declarada, uma transformação candidata é **wᵤᵥ = min(1, dᵤᵥ/dref)**, com dref>0 na mesma unidade. O exemplo dref=900 segundos é didático, não decisão ou calibração. A saturação perde distinção entre durações acima da referência. A escala e a janela devem permanecer iguais em comparações; normalizar separadamente pelo máximo de cada rede pode confundir intensidade e estrutura. Valores brutos acima de 1 exigem preparação antes do cadastro nessa referência.

**Modo alternativo: probabilidade direta.** Quando o peso já expressa probabilidade de transmissão por contato e por passo, adota-se pᵤᵥ=wᵤᵥ. β fica não aplicável, representado por None; não multiplicar novamente. Peso 1 significa transmissão certa em uma exposição permitida nesse modo, mas não no modo intensidade com β<1. Probabilidades referentes a outro intervalo exigem conversão documentada antes da entrada. A escala deve ser comum entre cenários; interpretação não pode mudar silenciosamente durante a execução.

### 3.4. Múltiplas exposições

Seja bᵤᵥ(t)∈{0,1} o indicador ativa do contato existente em t, independente do estado SIR e do isolamento. Um contato ausente ou inativo contribui probabilidade zero. Para contato ativo entre um I e um S do snapshot, aplicar p=βw(t) no modo intensidade ou p=w(t) no modo probabilidade direta. O mecanismo de intervenção modifica disponibilidade, peso ou existência antes desses sorteios.

O motor **não bloqueia adicionalmente pelo booleano isolamento**: a desativação já bloqueou os contatos, a redução deve permitir transmissão residual e a remoção já retirou as interações. Um filtro automático por pessoa isolada anularia incorretamente a redução parcial.

Para suscetível v, Jᵥ(t) reúne os vizinhos infectados no início do passo com contato permitido. Sob independência condicional das tentativas, dados os estados e contatos:

**Pᵥ(t) = 1 − ∏[u ∈ Jᵥ(t)] (1 − pᵤᵥ)**.

O produto vazio vale 1: sem vizinhos elegíveis, Pᵥ=0. Um sorteio uniforme Uᵥ(t) em [0,1) causa S → I se Uᵥ(t)<Pᵥ(t). Há no máximo uma nova infecção por pessoa no passo. Exposições 0,2 e 0,4 dão 1−0,8×0,6=0,52; não se somam as probabilidades.

### 3.5. Recuperação probabilística

Para cada indivíduo v em I no início do passo, um sorteio uniforme Vᵥ(t) em [0,1), independente dos sorteios de transmissão, decide a recuperação se Vᵥ(t)<γ, com γ finito em [0,1]. A transição é aplicada ao final, inclusive para isolados. Recém-infectados não participam desse sorteio no mesmo passo.

γ=0 impede recuperação; γ=1 recupera todos os infectados iniciais do passo ao final, sem impedir sua transmissão anterior quando permitida. Para γ>0, a quantidade de passos infecciosos tem média 1/γ sob essa convenção. Duração fixa não é usada conjuntamente.

β, quando aplicável, e γ são probabilidades discretas adimensionais por passo, não taxas contínuas em tempo inverso. Mudar a duração representada pelo passo exigiria rever os parâmetros. β/γ não será apresentado automaticamente como número reprodutivo da rede.

### 3.6. Ordem das operações e histórico

Simulacao é a única responsável pelo relógio e pelo histórico. MotorSIR calcula e aplica exatamente uma transição por chamada, sem laço próprio, incremento de t ou registro. A preparação de cada instante segue esta convenção:

1. Inicializar S,I,R em t=0 e validar tudo antes de alterar a rede ou consumir sorteios.
2. Ao chegar a um instante t, verificar extinção e limite. Se a execução pode avançar, aplicar a intervenção programada para t, uma única vez.
3. Registrar t,S(t),I(t),R(t),Q(t) exatamente uma vez. Q(t) é o número de isolados **após a intervenção devida nesse instante e antes dos sorteios**. Se o instante é terminal, concluir sem nova transição ou intervenção.
4. Capturar valores dos estados epidemiológicos em t; guardar somente referências a objetos mutáveis não constitui snapshot.
5. Calcular e sortear infecções dos suscetíveis e recuperação dos infectados presentes nesse snapshot. Guardar decisões separadamente.
6. Aplicar conjuntamente as transições pelo motor. Somente Simulacao incrementa t para t+1 e retorna à preparação do novo instante.

Assim, intervenção em t=0 já aparece em Q(0). Em t_int>0, o registro daquele instante inclui seus efeitos, sem gerar um segundo registro com o mesmo índice. Se I(t)=0 ou t=T_max ao chegar ao instante, registrar o término sem aplicar uma intervenção que não teria outra transição a afetar. Não se altera retroativamente um registro já publicado.

Uma execução com H transições produz H+1 registros. O recém-infectado só transmite e pode recuperar a partir do passo seguinte. O infectado que recupera ao final pode ter transmitido naquele passo. A recuperação não libera isolamento nesta referência.

### 3.7. Estratégia, mecanismo e orçamento

**Estratégia** escolhe as pessoas; **mecanismo** aplica o efeito sobre seus contatos. O padrão é DESATIVACAO: desativar explicitamente os contatos incidentes. Os mecanismos REDUCAO e EXCLUSAO seguem os contratos existentes em isolamento.py, sem que sua presença no código comprove integração completa ou testes aprovados do simulador.

Depois de validar toda a intervenção, o coordenador entrega IDs selecionados, mecanismo, orçamento e redução quando aplicável à função aplicar_isolamento(). Ela enumera contatos afetados uma única vez, aplica o efeito e marca as pessoas como isoladas. A seleção e o agendamento não são repetidos nessa função.

Para fração f finita em [0,1], o orçamento é **k=piso(fN)**, sendo N a população inicial. A fração realizada k/N pode diferir de f. A seleção ocorre uma única vez no início de t_int, inteiro com 0 ≤ t_int < T_max, se a execução ainda pode avançar. Não há reposição de alvos ou liberação até o término.

Todos os indivíduos, S,I ou R, são elegíveis. A seleção aleatória amostra k IDs distintos uniformemente sem reposição. A seleção por grau ordena pelo número de vizinhos da rede original, em ordem decrescente, com desempate por ID crescente; não usa pesos nem recalcula graus após cada isolamento. Pessoas de grau zero continuam elegíveis.

O cenário sem intervenção usa k=0, sem sorteios de seleção. Se extinção ocorre antes ou no instante agendado, informar que a intervenção não foi realizada. Com k=N e intervenção em t=0, nenhum contato transmite, mas os infectados continuam sujeitos à recuperação.

### 3.7.1. Mecanismos e políticas alternativos

**Redução parcial:** o parâmetro r (reducao) é a fração retirada, finita em [0,1]. Cada contato incidente a pelo menos uma pessoa selecionada recebe **w_novo=w_anterior×(1−r)** uma única vez, mesmo se ambos os extremos foram selecionados. Sua atividade é preservada, inclusive se já era False. Com peso 0,8 e r=0,5, o resultado é 0,4 em ambos os casos. r=0 preserva o peso e r=1 o zera, sem necessariamente mudar ativa. Não se aplica um segundo fator por extremo. Se for usada a notação residual ρ, ela significa ρ=1−r; não é a fração retirada.

O motor utiliza o peso resultante: p=βw_novo no modo intensidade e p=w_novo no modo direto, sem reaplicar β no segundo. Não combina essa redução com bloqueio automático por isolamento. A fórmula de múltiplas exposições usa os contatos ainda existentes e ativos.

**Remoção dos contatos (EXCLUSAO na API):** remover as ligações incidentes, mantendo o indivíduo cadastrado, com grau zero, e seu estado epidemiológico. Não é exclusão do vértice, recuperação ou morte. N e S,I,R,Q continuam relativos à mesma população; infectados desconectados recuperam normalmente. Remoção de vértices é outra operação, não representada por esse mecanismo.

A intervenção é aplicada uma única vez e permanece até o término. O estado inicial da rede, incluindo pesos e ativa, fica preservado no snapshot/manifesto para reprodução e para iniciar cenários independentes. A referência não oferece liberação; se futuramente adicionada, será necessário restaurar seletivamente a condição anterior, sem reativar contatos bloqueados por outro motivo.

**Política diária q, menor prioridade:** no início de cada passo, cada infectado ainda não isolado tem chance q∈[0,1] de entrar em isolamento, com sorteio próprio. q não é fração populacional e não garante k fixo. Como proposta de protocolo separado, acompanha-se a regra de liberação na recuperação descrita na modelagem do grafo; uma liberação não altera ativa. Nesse protocolo Q pode diminuir, e a seleção por orçamento e o atributo intervencaoAplicada não substituem os eventos diários. O contrato de registro e os testes precisam ser adaptados antes de implementar.

**Topologia dinâmica, menor prioridade:** permite contatos aparecerem/desaparecerem entre instantes; mudança de estado SIR ou bloqueio lógico não constitui, por si só, mudança estrutural. Será necessário definir agenda/regra das mudanças, captura consistente por passo e significado do grau no momento da seleção. Se admitir entrada/saída de pessoas, definir também população de referência e denominadores; as fórmulas da coorte fechada não se transferem automaticamente. Essas regras ainda não foram fechadas.

### 3.8. Término

Extinção ocorre no primeiro instante com I(t)=0, incluindo t=0. Caso contrário, concluir ao completar T_max transições. Se I(T_max)=0, prevalece EXTINCAO; se I(T_max)>0, registrar LIMITE_PASSOS e censura. Ausência de novas infecções em um passo não basta para encerrar enquanto houver infectados.

## 4. Parâmetros

Todos os valores exemplificativos são escolhas didáticas. Não há calibração com doença real. Na execução individual, n₀ é derivado dos IDs; a quantidade de repetições pertence ao protocolo do lote, não ao motor de um passo.

| Parâmetro | Símbolo | Significado | Domínio válido | Exemplo didático |
|---|---|---|---|---|
| Unidade | Δt | Uma transição | 1 dia do modelo, constante | 1 dia do modelo |
| Contágio | β | Probabilidade em peso 1, modo intensidade | Real finito em [0,1]; None no modo probabilidade direta | 0,10 |
| Recuperação | γ | Probabilidade de I → R por passo | Real finito em [0,1] | 0,20 |
| Modo de peso | — | Interpretação explícita | Intensidade (padrão) ou probabilidade direta | Intensidade |
| Peso | wᵤᵥ | Valor interpretado pelo modo | Real finito em [0,1] | 0,50 |
| Atividade própria | bᵤᵥ | Contato habilitado independentemente do isolamento | Booleano | True |
| Referência de duração | dref | Preparação de pesos de duração | Real positivo na unidade de d; fixado na preparação | 900 s |
| População | N | Indivíduos cadastrados, inclusive sem contatos | Inteiro positivo | Contagem do arquivo |
| Infectados iniciais | IDs₀; n₀ | Manual ou sorteio na interface | Subconjunto de V; 0 ≤ n₀ ≤ N; semente no sorteio | IDs 1,2,3 se existentes |
| Estratégia | σ | Seleção de pessoas | Nenhuma, aleatória ou grau original | Grau |
| Mecanismo | — | Efeito sobre os contatos | DESATIVACAO padrão; REDUCAO; EXCLUSAO dos contatos | DESATIVACAO |
| Redução | r | Fração retirada uma vez por contato | [0,1] somente em REDUCAO; None nos demais | 0,50 |
| Fração | f | Parcela solicitada da população | Real finito em [0,1] | 0,10 |
| Orçamento | k | Quantidade selecionada | piso(fN), de 0 a N | 24 se N=242 |
| Início | t_int | Instante antes dos sorteios | Inteiro; 0 ≤ t_int < T_max | 5 se T_max>5 |
| Limite | T_max | Máximo de transições | Inteiro positivo, excluindo bool | 200 |
| Sementes | s | Estado inicial dos fluxos identificados | Inteiros válidos no algoritmo escolhido | Base 2026 |
| Repetições | m | Execuções por cenário | Inteiro positivo; m≥2 para desvio amostral | 30 |

O quadro descreve a referência e seus modos de peso/inicialização. Para as extensões, acrescentar q∈[0,1] na política diária e r∈[0,1] como fração retirada somente na redução parcial; não confundi-los com f ou β. Topologia dinâmica e q têm menor prioridade. Os três mecanismos estão documentados; sua oferta deve ser identificada conforme disponibilidade, sem executar alternativa não implementada. No cenário sem intervenção, f=0. A validação rejeita valores não finitos, IDs ausentes, duplicação na entrada, limites inválidos e incompatibilidades de preparo; apresenta mensagens por campo e exige nova validação se a configuração mudar.

## 5. Métricas

N é sempre a população inicial do próprio resultado, fixa e positiva. Isolamento não reduz N. Seja H o último instante observado.

| Métrica | Definição | Unidade/denominador | Interpretação |
|---|---|---|---|
| Curvas | S(t),I(t),R(t), t=0,...,H | Pessoas; proporções divididas por N | S+I+R=N |
| Isolados | Q(t), contado após intervenção de t | Pessoas; 0 ≤ Q ≤ N | Sobrepõe os estados SIR; não somar aos compartimentos |
| Pico | I_pico=max I(t), de 0 a H | Pessoas; relativo I_pico/N | Inclui infectados isolados |
| Momento do pico | Primeiro t com I(t)=I_pico | Passos/dias do modelo | Primeiro máximo em caso de empate |
| Acumulado | A_H=[N−S(H)]/N=[I(H)+R(H)]/N | População inicial N | Pessoas já infectadas, incluindo n₀ |
| Novas infecções | N−S(H)−n₀ | Pessoas | Infecções posteriores à inicialização |
| Duração | D=primeiro t com I(t)=0 | Passos/dias do modelo | None se não observada |
| Horizonte | H | Passos/dias do modelo | Último instante registrado |
| Diferença média | ΔZ=média(Z_ref−Z_σ) | Mesma unidade de Z | Comparação em repetições correspondentes |
| Redução relativa | 100×[média(Z_ref)−média(Z_σ)]/média(Z_ref) | Percentual; referência positiva | Razão das médias, não média das razões |

Z é o indicador comparado, não a contagem Q de isolados. Redução negativa significa aumento. Com referência zero, apresentar diferença absoluta e redução não aplicável. Como R(0)=0 e não há reinfecção, o acumulado conta cada pessoa uma única vez; ΣI(t) não é total de pessoas distintas. N=10 e I=[2,4,4,0] dão pico 4, proporção 0,4 e primeiro instante 1.

### 5.1. Censura e comparação no horizonte

Se I(H)>0 ao atingir o limite, A_H e pico são observados até H, não necessariamente finais. D permanece None e a apresentação informa D>H. Não substituir por zero ou T_max. Sem infectados iniciais, H=D=0, pico=0, instante do pico=0 e acumulado=0.

Usar horizonte T_max comum. Históricos extintos antes dele podem ser prolongados apenas para alinhamento visual, com I=0 e S,R,Q constantes sob a política permanente; identificar esse prolongamento. Históricos censurados não podem ser completados com I=0.

Apresentar quantidade e proporção de execuções censuradas. Média da duração somente entre extinções deve ser identificada como condicional, com número de observações, pois pode ser enviesada. Diferenças pareadas de duração exigem pares completos e indicação das exclusões. Para momento do pico, preferir diferença em passos; duração menor isoladamente não comprova melhor intervenção.

## 6. Proposta de comparação e reprodutibilidade

### 6.1. Cenários e condições controladas

Comparar referência sem isolamento, seleção aleatória e seleção por grau. Nas intervenções, manter o mesmo k, t_int e bloqueio lógico total; a referência usa k=0. Dentro de cada repetição, manter rede, pesos, β,γ, IDs iniciais e T_max. Variar estrutura constitui outro eixo experimental, com famílias, densidades e escalas declaradas.

Cada execução deve começar com estado independente: reconstruir ou copiar a condição inicial preservando as relações entre objetos dentro da própria execução. Nunca reutilizar estados finais ou indivíduos mutáveis de outra execução. Na comparação padrão por bloqueio lógico, a topologia e os graus estruturais não mudam na desativação; a remoção de contatos altera os graus operacionais. A seleção por grau usa sempre o snapshot anterior à intervenção, nunca um recálculo entre os alvos. Manter também modo de peso, atividades das arestas e mecanismo iguais entre cenários. Mecanismos diferentes e q diário pertencem a experimentos separados, sem presumir custo equivalente ao orçamento.

### 6.2. Execução, consolidação e apresentação

O executor de lotes organiza cenários/repetições e reinicializa as execuções; não recalcula regras do motor. A consolidação usa resultados identificados para médias, desvios e censura. A apresentação mostra histórico individual, cenário/repetição, curvas e síntese. Esses são contratos distintos, não três implementações da mesma comparação; a atribuição pessoal pertence ao planejamento coletivo.

Para m≥2, propor média e desvio-padrão amostral dos picos e acumulados observados. Com m=1, o desvio amostral é não aplicável. Não imputar duração de extinção aos censurados. A quantidade de repetições e os valores experimentais dependem de deliberação e avaliação de custo, sem alegar suficiência estatística automática.

### 6.3. Manifesto de execução

O resultado deverá preservar um manifesto com identificação e assinatura canônica da rede preparada (IDs, pares não ordenados, pesos e atividade própria), fonte/arquivo/janela e transformação; configuração completa, incluindo IDs iniciais; cenário e repetição; sementes-base e efetivas dos fluxos utilizados; algoritmo e derivação das sementes; revisão do projeto, versão do Python e dependências relevantes.

A configuração efetivamente executada e o manifesto devem ser snapshots, sem referências mutáveis que possam mudar a descrição depois da execução. Fluxos de geração da rede, sorteio dos infectados iniciais, seleção de isolamento e eventos epidemiológicos são distintos, com ordem estável de processamento por ID. O algoritmo e a derivação estável ainda precisam ser selecionados e registrados; não se deve depender do hash aleatório de strings do processo nem reaplicar a semente a cada sorteio.

Reproduzir exige a mesma entrada preparada, estado inicial, configuração, sementes, algoritmo, ordem de consumo e ambiente compatível. A mesma semente isolada não garante reprodução. Sementes diferentes podem produzir resultados iguais por acaso ou em casos determinísticos.

Entre repetições, utilizar sementes distintas segundo política registrada; dentro de cada repetição, documentar sua associação aos cenários. Fluxos separados impedem que a seleção consuma o gerador epidemiológico, mas sementes iguais entre estratégias não garantem pareamento por pessoa/evento se o consumo divergir. Não pressupor esse pareamento nas análises.

### 6.4. Estrutura e variabilidade

Famílias e parâmetros dos geradores devem ser definidos no escopo coletivo; não se promete implementar todas as famílias citadas no planejamento. Redes sintéticas permitem controlar N,densidade e pesos; múltiplas realizações ajudam a separar variabilidade topológica de variabilidade epidemiológica. Diferenças entre bases de tamanhos e períodos distintos não serão atribuídas automaticamente à topologia. Uma única execução não demonstra superioridade universal.

## 7. Levantamento de dados


Foram consultadas documentações e publicações originais. Duas candidatas representam contatos presenciais e uma representa relações digitais. A busca incluiu Kaggle, mas a preferência pela plataforma não substitui a adequação dos dados.

### 7.1. Bases candidatas

| Base e origem | Representação e dados confirmados | Adequação e preparação | Limitações e condições |
|---|---|---|---|
| **Primary school: cumulative networks, SocioPatterns** [4] | Pessoas e proximidade presencial. Dois arquivos GEXF diários, anunciados com cerca de 44 e 57 KB. Atributos: turma, gênero, duração acumulada em segundos e contagem de contatos. | Alta adequação à rede estática ponderada. Escolher um dia e converter os atributos para a estrutura própria. | Agregação perde ordem temporal e não cobre contatos externos. CC BY-NC-SA; citar estudo e reconhecer SocioPatterns. |
| **High school contact and friendship networks, SocioPatterns, Marselha, 2013** [6] | Na camada de sensores: estudantes e proximidade presencial. Lista de cinco dias em intervalos de 20 s, tempo, IDs e turmas, cerca de 653 KB; metadados separados. | Agregar uma janela definida, padronizar pares e acumular duração. Separar sensores das camadas de diários e amizade. | Perda de sequência temporal; participação e cobertura limitadas. Página informa CC BY-NC-SA e pede citação de Mastrandrea et al. |
| **Social circles: Facebook, SNAP** [7]; coleção relacionada no **Kaggle** [9] | Usuários e amizade digital. Versão combinada do SNAP: 4.039 vértices e 88.234 arestas, TXT compactado. Coleção contém perfis anonimizados, círculos e redes egocêntricas. | Caso estrutural de maior porte. Usar pesos unitários ou sintéticos, identificados como tais. | Não mede exposição presencial. Página SNAP consultada fornece citação, sem licença explícita de dados; verificar condições antes de redistribuir. |

O estudo da escola primária envolveu 242 participantes: 232 crianças e 10 professores [3]. Esse é o universo observado, não uma garantia de que cada arquivo diário contenha todos os vértices. A contagem deve ser conferida na preparação.

O artigo de Marselha informa 327 estudantes e 5.818 arestas na rede agregada de todo o período [5]. Esses números não devem ser atribuídos a uma agregação de somente um dia.

Os números da terceira candidata pertencem à versão combinada do SNAP. O pacote do Kaggle não será tratado como idêntico. A página dos autores relaciona a coleção à competição [8], mas o arquivo escolhido precisará ser identificado e conferido.

### 7.2. Contato presencial e aproximação social

Sensores de proximidade oferecem uma relação mais direta com exposição presencial que amizade digital. Ainda assim, proximidade não comprova transmissão, e a medição pode omitir pessoas, ambientes e períodos.

Redes digitais poderão apoiar estudos estruturais, apresentadas como aproximações. Não será atribuída às suas arestas uma intensidade epidemiológica observada. A comparação entre formas de medir relações em Marselha evidencia que amizade e contato presencial não são intercambiáveis [5].

### 7.3. Preparação prevista

1. Registrar fonte, versão, arquivo, janela observada e condições de uso.
2. Validar IDs e preservar seu mapeamento para identificadores internos.
3. Remover autoarestas e tratar duplicações sem eliminar registros temporais legítimos.
4. Agregar pares não ordenados e durações, quando necessário.
5. Validar pesos e documentar a transformação.
6. Preservar pessoas sem contatos quando houver cadastro que as identifique.
7. Conferir vértices, arestas e componentes após a preparação.
8. Registrar filtragens e amostragens.

Não se recomenda restringir automaticamente à maior componente: isso altera a população e os denominadores. A preparação alimentará a estrutura própria do grupo, respeitando o enunciado.

### 7.4. Dados observados e redes sintéticas

| Aspecto | Dados observados | Redes sintéticas |
|---|---|---|
| Contribuição | Preservam contatos registrados em contexto específico. | Controlam tamanho, densidade e organização. |
| Limitação | Recorte temporal, cobertura incompleta e interpretação dos pesos. | Dependem das hipóteses do gerador e dos pesos escolhidos. |
| Papel proposto | Caso aplicado e demonstração. | Verificação e investigação controlada da estrutura. |
| Alcance | Restrito ao conjunto preparado e às hipóteses. | Restrito às famílias e configurações geradas. |

**Recomendação a deliberar:** iniciar com uma rede diária da escola primária, já estática, ponderada e de porte reduzido, complementada por redes sintéticas. Marselha é alternativa com maior preparação. Facebook pode ser um caso estrutural adicional, sem substituir contatos presenciais.

## 8. Diagramas UML

Os diagramas representam o projeto da execução; a existência de classes e operações no repositório não comprova o fluxo completo nem resultados experimentais. As fontes editáveis e as imagens são mantidas juntas nas pastas de cada diagrama. A sintaxe de casos de uso e estados segue a documentação PlantUML [10,11].

### 8.1. Casos de uso

![Diagrama de casos de uso](../modelagem/simulador-epidemias/diagramas/casos-de-uso/casos-de-uso.png)

O usuário seleciona a rede, configura modo de peso e parâmetros epidemiológicos, define condições iniciais, limite e sementes, configura o isolamento, executa e consulta resultados. A configuração anteriormente reunida em um único caso foi dividida em dois objetivos: modelo epidemiológico e preparo da execução. As condições iniciais admitem IDs manuais ou sorteio, conforme detalhado no texto. Execução e comparação incluem validação. Topologia dinâmica e política diária q são alternativas de menor prioridade; os mecanismos alternativos estão documentados, com oferta dependente de implementação. A interface deve distinguir opção planejada de disponível e não iniciar opção sem suporte. Formatos e geradores suportados ainda exigem definição coletiva.

### 8.2. Estados do indivíduo

![Diagrama de estados do indivíduo](../modelagem/simulador-epidemias/diagramas/estados-individuo/estados-individuo.png)

As regiões ortogonais representam estado SIR e isolamento simultâneos. Pessoas S,I ou R podem ser isoladas; isolamento não é um quarto estado. Na política padrão não há retorno de R a S nem liberação automática. A política diária alternativa é descrita separadamente e não é o ciclo representado nesta figura. A figura usa os eventos atualização [infecção] e atualização [recuperação], decididos pelos sorteios U e V definidos na seção 3, e mostra suas operações infectar(t+1) e recuperar(). As operações são efetivadas conjuntamente em t+1; a preparação de t_int aplica o mecanismo aos contatos antes desses sorteios. Passar a R mantém a pessoa no grafo.

### 8.3. Classes de projeto

![Diagrama de classes](../modelagem/simulador-epidemias/diagramas/classes-dominio/classes-dominio.png)

O projeto reutiliza os conceitos RedeContatos,Contato,Individuo, com proposta de consultas encapsuladas e mapeamento para a API existente. MotorSIR aplica um passo síncrono; Simulacao controla tempo, intervenção e registro único. RegistroPasso contém S,I,R,Q; ResultadoSimulacao preserva o manifesto; as métricas usam sua população inicial. Classes futuras não são apresentadas como implementadas.

A [explicação consolidada](../modelagem/simulador-epidemias/modelagem-de-classes.md) detalha atributos, operações, relações, restrições e código PlantUML completo. Amplie o [SVG de classes](../modelagem/simulador-epidemias/diagramas/classes-dominio/classes-dominio.svg) para ler os detalhes; a imagem no PDF é uma visão geral.

## 9. Verificações futuras

As verificações abaixo são propostas, não resultados obtidos:

- Conservação S+I+R=N e 0≤Q≤N; S não aumenta, R não diminui; isolamento mantém SIR.
- Cadastro de indivíduos sem contatos; ausência de transmissão entre componentes sem contato.
- β=0 no modo intensidade, ou probabilidades de contato zero no modo direto, sem novas infecções; peso zero sem transmissão nos dois modos; γ=0 sem recuperação; γ=1 recuperando apenas os infectados iniciais do passo.
- Cadeia A–B–C, A inicialmente infectado, β=1, pesos 1 e γ=0: após uma transição, B infectado e C ainda suscetível.
- Múltiplas exposições 0,2 e 0,4 produzindo P=0,52, com gerador controlado para verificar os limiares.
- Intervenção t=0 refletida em Q(0), sem registro duplicado; orçamento zero sem efeito; orçamento total bloqueando contatos.
- Empate do pico usando primeira ocorrência; duração ausente em censura; extinção prevalecendo se coincide com limite.
- Seis resultados distintos para três cenários e duas repetições, sem contaminação de estado; reprodução do manifesto em processos compatíveis.
- Redução de 50% em contato de peso 0,8 produzindo 0,4, com um ou dois extremos selecionados; contato inativo permanecendo inativo.
- Remoção dos contatos preservando pessoa, histórico e N; desativação explícita impedindo transmissão.
- Rejeição de configuração inválida antes de sorteios/mutação, com mensagens identificáveis.

São testes de correspondência à especificação, não validação clínica. Correção, complexidade e desempenho deverão ser avaliados futuramente em conjunto, sem inferir desempenho de código ainda não implementado.

## 10. Conclusão parcial

A referência proposta delimita SIR discreto em população fechada, com rede estática e intensidade normalizada como padrões, preservando probabilidade direta e mecanismos alternativos documentados. Topologia dinâmica e q diário têm menor prioridade; infectados iniciais podem ser manuais ou sorteados na interface. Recuperação probabilística, atualização síncrona, bloqueio lógico por orçamento e histórico com isolados formam uma especificação única para os procedimentos futuros.

Comparações controlarão condições iniciais, parâmetros e orçamento das intervenções; repetições, manifesto e tratamento da censura permitirão discutir variabilidade e limites. A base final, o algoritmo pseudoaleatório, os parâmetros experimentais e a integração coletiva ainda dependem do grupo. Há módulos implementados de rede, carga, geração e isolamento; motor completo, integração e resultados não são certificados por esta documentação. Alterar a política exigirá atualizar conjuntamente esta especificação e os diagramas relacionados.

## Referências


[1] NEWMAN, M. E. J. Spread of epidemic disease on networks. **Physical Review E**, v. 66, n. 1, 016128, 2002. DOI: 10.1103/PhysRevE.66.016128. Disponível em: [https://doi.org/10.1103/PhysRevE.66.016128](https://doi.org/10.1103/PhysRevE.66.016128). Acesso em: 7 nov. 2026.

[2] KERMACK, W. O.; MCKENDRICK, A. G. Contributions to the mathematical theory of epidemics—I. 1927. **Bulletin of Mathematical Biology**, v. 53, n. 1-2, p. 33-55, 1991. DOI: 10.1007/BF02464423. Disponível em: [https://pubmed.ncbi.nlm.nih.gov/2059741/](https://pubmed.ncbi.nlm.nih.gov/2059741/). Acesso em: 7 nov. 2026.

[3] STEHLÉ, J. et al. High-resolution measurements of face-to-face contact patterns in a primary school. **PLOS ONE**, v. 6, n. 8, e23176, 2011. DOI: 10.1371/journal.pone.0023176. Disponível em: [https://doi.org/10.1371/journal.pone.0023176](https://doi.org/10.1371/journal.pone.0023176). Acesso em: 7 nov. 2026.

[4] SOCIOPATTERNS. **Primary school: cumulative networks**. 27 ago. 2011. Conjunto de dados. Disponível em: [https://sociopatterns.org/datasets/primary-school-cumulative-networks/](https://sociopatterns.org/datasets/primary-school-cumulative-networks/). Acesso em: 7 nov. 2026.

[5] MASTRANDREA, R.; FOURNET, J.; BARRAT, A. Contact patterns in a high school: a comparison between data collected using wearable sensors, contact diaries and friendship surveys. **PLOS ONE**, v. 10, n. 9, e0136497, 2015. DOI: 10.1371/journal.pone.0136497. Disponível em: [https://doi.org/10.1371/journal.pone.0136497](https://doi.org/10.1371/journal.pone.0136497). Acesso em: 7 nov. 2026.

[6] SOCIOPATTERNS. **High school contact and friendship networks**. 15 jul. 2015. Conjunto de dados. Disponível em: [https://sociopatterns.org/datasets/high-school-contact-and-friendship-networks/](https://sociopatterns.org/datasets/high-school-contact-and-friendship-networks/). Acesso em: 7 nov. 2026.

[7] STANFORD NETWORK ANALYSIS PROJECT (SNAP). **Social circles: Facebook**. [s. d.]. Conjunto de dados. Disponível em: [https://snap.stanford.edu/data/egonets-Facebook.html](https://snap.stanford.edu/data/egonets-Facebook.html). Acesso em: 7 nov. 2026.

[8] MCAULEY LAB. **Social circles**. [s. d.]. Coleção de dados públicos. Disponível em: [https://mcauleylab.ucsd.edu/public_datasets/amazon_demo/](https://mcauleylab.ucsd.edu/public_datasets/amazon_demo/). Acesso em: 7 nov. 2026.

[9] JOYCENV; JULIANMCAULEY; CUKIERSKI, Will. **Learning social circles in networks**. Kaggle, 2014. Competição. Disponível em: [https://www.kaggle.com/competitions/learning-social-circles](https://www.kaggle.com/competitions/learning-social-circles). Acesso em: 7 nov. 2026.

[10] PLANTUML. **Use case diagram**. [s. d.]. Documentação. Disponível em: [https://plantuml.com/use-case-diagram](https://plantuml.com/use-case-diagram). Acesso em: 7 nov. 2026.

[11] PLANTUML. **State diagram**. [s. d.]. Documentação. Disponível em: [https://plantuml.com/state-diagram](https://plantuml.com/state-diagram). Acesso em: 7 nov. 2026.

## Fontes dos diagramas

- [Casos de uso - PlantUML](../modelagem/simulador-epidemias/diagramas/casos-de-uso/casos-de-uso.puml) e [imagem vetorial](../modelagem/simulador-epidemias/diagramas/casos-de-uso/casos-de-uso.svg).
- [Estados do indivíduo - PlantUML](../modelagem/simulador-epidemias/diagramas/estados-individuo/estados-individuo.puml) e [imagem vetorial](../modelagem/simulador-epidemias/diagramas/estados-individuo/estados-individuo.svg).
- [Classes de projeto - PlantUML](../modelagem/simulador-epidemias/diagramas/classes-dominio/classes-dominio.puml) e [imagem vetorial](../modelagem/simulador-epidemias/diagramas/classes-dominio/classes-dominio.svg).

O código completo do diagrama de classes também integra a explicação de sua modelagem. As fontes PlantUML são os arquivos de referência para alterações nos diagramas.
