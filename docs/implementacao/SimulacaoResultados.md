# Simulação, resultados e exportação

## Ciclo temporal

`Simulacao(rede, configuracao)` recebe uma `ConfiguracaoSimulacao` validada pelo domínio e cria sua própria cópia da rede. Os infectados iniciais são preparados com o fluxo de sorteio correspondente. Ao chegar a cada instante, inclusive zero, o registrador conta os estados e verifica extinção e limite antes de aplicar a intervenção devida. O registro já inclui os isolados desse instante, antes da transição para o seguinte. Instantes terminais são registrados sem nova intervenção.

O motor usa os estados do início do intervalo e aplica as transições em conjunto. A execução termina por extinção ou limite, sem recuperar artificialmente infectados remanescentes. Uma execução sem infectados termina em zero. O registro guarda contadores independentes dos indivíduos.

`executar()` devolve `ResultadoSimulacao`, congelado, com configuração efetiva, histórico em tupla, métricas, motivo de término, população e índice de repetição quando disponível. Revisão e sementes são acessíveis pelo resultado. Chamadas repetidas retornam o mesmo resultado concluído. A construção antiga com apenas rede e limite permanece compatível e serve como registrador temporal; código novo deve fornecer a configuração.

Com configuração, `executar_passo()` e seu alias `avancar()` aplicam exatamente uma atualização síncrona sobre o instante já preparado e preparam o próximo antes de registrá-lo. Com início um e orçamento de duas pessoas, por exemplo, Q nos registros 0, 1, 2 e 3 é `0, 2, 2, 2`, desde que a execução chegue a t=1 com infectados e ainda possa avançar. O motor e seu fluxo aleatório são mantidos entre chamadas: avançar manualmente e depois chamar `executar()` produz o mesmo histórico da execução contínua. Após extinção ou limite, novos avanços devolvem o último registro sem duplicá-lo.

`inicializar()` restaura uma cópia do retrato capturado na construção, incluindo pessoas, contatos, pesos e disponibilidade. Reaplica os IDs iniciais efetivos, recria o gerador epidemiológico e a estratégia de isolamento com as mesmas sementes e reaplica a intervenção em zero quando prevista e ainda há infectados. Sem infectados iniciais, encerra com um único registro e zero isolados. Relógio, histórico e cache do resultado são reiniciados, sem modificar a rede recebida nem resultados anteriores. Mudanças posteriores na rede recebida não alteram esse retrato. No registrador legado, o primeiro uso continua observando a rede fornecida; a reinicialização explícita passa a trabalhar sobre uma cópia do retrato original, sem executar o motor por conta própria.

O adaptador HTTP chama esse ciclo de domínio, sem reimplementar transmissão ou agendamento. Cada cenário e repetição recebe uma rede limpa. A bateria deriva sementes por `base + índice`, com fluxos separados para epidemia, infectados iniciais e isolamento.

## API e consulta

- `POST /api/rede/simulacao/executar`: executa um cenário e devolve histórico, métricas, manifesto e `resultado_id`.
- `POST /api/rede/comparacao/executar`: executa os três cenários e preserva resultados individuais, estatísticas agregadas e manifestos efetivos por repetição.
- `GET /api/rede/resultados`: lista resultados da sessão.
- `GET /api/rede/resultados/<id>`: devolve uma cópia serializável do resultado, incluindo seu ID.

JSON e cookie de sessão seguem o adaptador existente. Revisão, confirmação e contexto são verificados. Todos os IDs individuais e sementes do manifesto são texto para preservar inteiros maiores que o limite seguro do JavaScript. A sessão mantém até 32 resultados, expira conforme a API e não é armazenamento permanente em disco. Ao ultrapassar o limite, os mais antigos são removidos; exporte os experimentos que precisar conservar.

A tela de resultados permite consultar execuções anteriores da rede atual e selecionar cenário/repetição para o painel e o histórico. Resultados de outra revisão/contexto não são exibidos como se pertencessem à rede atual.

## Tela de execução

O resumo do ensaio apresenta nome/origem e revisão da rede confirmada, população e contatos, parâmetros e modo de peso, limite, modalidade/repetições, sementes dos três fluxos, IDs iniciais efetivos e todos os parâmetros de isolamento, incluindo o orçamento efetivo em pessoas. IDs e sementes permanecem textuais; listas de mais de 12 IDs usam um controle nativo de expansão acessível por teclado. Na comparação, o resumo identifica sementes base e IDs da primeira repetição, esclarecendo a derivação das sementes e o novo sorteio por repetição.

A validação individual salva pela Tela 02 é reutilizada para a mesma rede confirmada. Configurações antigas sem essa resposta e configurações salvas pela validação de comparação consultam o endpoint de validação individual antes da execução. Seleção sorteada e orçamento vêm do domínio, não são reconstruídos no navegador. Enquanto a validação não estiver disponível para o contexto/revisão atuais, os controles de início e avanço permanecem desabilitados. Falhas de consulta permitem nova tentativa e revisão da configuração.

Após validar, a Tela 02 oferece um link para preparar o ensaio na Tela 03, tanto para a execução única como para a comparação. A modalidade inicial acompanha a configuração salva: com repetições, abre a comparação; sem repetições, abre a execução única. Os cenários não são executados automaticamente pela navegação. O usuário revisa o resumo e seleciona Iniciar / Continuar Simulação; a troca manual de modalidade continua disponível. Alterar a configuração remove o resumo validado e seu link até uma nova validação.

Antes de receber o histórico, os contadores S/I/R e isolados exibem `—`, distinguindo ausência de dados de um zero efetivamente registrado. Não há população epidemiológica de exemplo, progresso ou barras de estados fictícios. O grafo mostra apenas a estrutura da rede. Após a resposta, a tela usa as contagens reais, informa motivo de término e horizonte observado e permite reproduzir os registros. A atribuição visual de estados por ID continua ilustrativa e identificada como tal. Reiniciar remove o histórico exibido e restaura os contadores indisponíveis, mantendo o resumo validado. Resultados de outro contexto/revisão não alimentam os contadores.

A barra de distribuição contém somente S/I/R, cuja soma corresponde a 100% da população. O isolamento possui um indicador separado, com contagem, percentual e semântica acessível de medidor. Isolados já pertencem a S, I ou R: não constituem um quarto grupo disjunto nem aumentam a população. Ambos os indicadores usam o mesmo registro real do instante reproduzido e ficam ausentes antes do histórico e após reiniciar.

## Gráficos e estatística

Há quatro séries: suscetíveis, infectados, recuperados e isolados. Todas usam o mesmo eixo temporal. O painel e a tabela acompanham a execução selecionada, inclusive seu horizonte e motivo de término.

O gráfico abre com infectados e, em lotes, médias por cenário. Os filtros permitem ativar outros estados, escolher cenários, alternar entre médias, uma repetição e todas as repetições, selecionar a repetição e definir os passos inicial/final. O intervalo é confirmado por Aplicar ou Enter; valores inválidos recebem mensagem próxima aos campos e preservam o gráfico anterior. A faixa de desvio pode ser ocultada no modo de médias. A legenda não enumera cada combinação de cenário e repetição. O botão de restauração retorna à visualização inicial.

Esses filtros atuam somente no gráfico, sem alterar o painel, a tabela ou as métricas consolidadas. As médias continuam usando todas as repetições do cenário; selecionar uma repetição exibe suas trajetórias individuais. SVG e PNG usam o desenho filtrado e identificam o intervalo; o JSON conserva o lote completo e os filtros escolhidos. CSVs mantêm seu escopo completo. Sem estados, cenários ou registros no intervalo, a tela informa a ausência de curvas e desabilita as imagens.

Na comparação, cores identificam estratégias e padrões de traço distinguem estados. As linhas mais grossas representam médias, e as áreas representam um desvio-padrão amostral quando habilitadas. Os controles de estado ocultam linhas e áreas correspondentes.

A agregação usa apenas repetições do mesmo cenário do lote. O horizonte é comum aos cenários. Após extinção, o último registro é mantido até esse horizonte, pois não haverá novas transições. Uma observação isolada usa desvio visual zero; nas estatísticas das métricas, o desvio indefinido permanece ausente. Não são misturados resultados de lotes diferentes.

O mapa de indivíduos continua ilustrativo: os estados por ID são inferidos dos contadores e essa limitação é informada na tela. O histórico agregado não permite reconstruir quem foi infectado em cada passo.

## Exportação

- Histórico CSV: contadores da execução selecionada, com identificação do cenário e da repetição.
- CSV de trajetórias: históricos individuais de todo o lote.
- CSV agregado: `cenario`, `metrica`, `n`, `ausentes`, `media` e `desvio_padrao`, extraídos do resumo efetivamente recebido e exibido.
- JSON: resultado exibido, manifestos completos e seleção visual, sem depender da existência de um cache anterior.
- SVG: cópia autônoma do gráfico, com estilos computados incorporados, cabeçalho e metadados JSON.
- PNG: rasterização em escala 2× desse mesmo SVG, preservando cores, cabeçalho e legenda.

Os nomes identificam projeto, revisão e data. CSV e JSON incluem data local, fuso e manifesto; SVG incorpora metadados e cabeçalho; PNG inclui identificação, sementes e parâmetros visíveis. As estatísticas não são recalculadas com regras diferentes no exportador. As curvas médias usam a mesma função na apresentação e nos testes.

Reiniciar cancela a requisição no cliente e descarta sua resposta. O cálculo síncrono já iniciado no servidor pode terminar e continuar disponível na listagem; o cliente não promete interromper o processamento Python.

## Processamento e memória

A construção pública de `Simulacao` preserva por padrão um retrato próprio para reinicialização. Os controllers podem usar `copiar_referencia=False` somente quando dispõem de uma referência privada, mantida estável durante o uso da simulação. Esse modo não modifica a referência: ainda cria uma rede de trabalho independente em cada início. A API reutiliza a cópia confirmada entregue pelo serviço; a comparação padrão compartilha esse retrato apenas para leitura entre os cenários sequenciais. Executores personalizados de `executar_comparacao()` continuam recebendo suas próprias cópias, preservando o contrato anterior.

Assim, o caminho HTTP individual realiza duas cópias completas e a comparação padrão realiza `1 + 3 × repetições`, em vez de três e `1 + 9 × repetições`. O histórico conta a população uma única vez por registro e reutiliza a contagem de infectados para decidir a parada.

O motor prepara a ordem crescente de pessoas e vizinhos uma vez por topologia. `RedeContatos.versao_topologia` muda ao acrescentar pessoas/contatos, remover contatos ou desconectar uma pessoa com contatos. A exclusão invalida o índice antes do próximo avanço; a substituição de contatos também é detectada mesmo quando as quantidades totais não mudam. Pesos e disponibilidade são lidos dos contatos atuais, sem copiar valores para o cache. A validação integral é repetida quando mudam rede, topologia, configuração ou revisão. A validação do instante continua ocorrendo em cada chamada.

As transições, a ordem de combinação das probabilidades e a quantidade/ordem dos sorteios permanecem iguais às da implementação sem cache. O índice acrescenta memória linear em pessoas e contatos, compensada nos cenários medidos pela redução das cópias. Não se trata de memória constante nem de garantia de ganho para toda rede.

A tabela de resultados renderiza no máximo 50 registros por página, com controles de primeira, anterior, próxima e última página, status acessível e reinício ao trocar a execução. Paginar atualiza somente o componente da tabela, sem recalcular o gráfico. CSV e JSON continuam exportando o histórico completo, não apenas a página visível. Os máximos são obtidos sem expandir históricos em argumentos, e cada trajetória comparada usa a escala temporal comum sem recalcular seu horizonte para cada ponto: a construção da linha passa de quadrática para linear na quantidade de registros.

Os históricos completos continuam em memória para consulta, curvas e exportação. Esta otimização não acrescenta limites de população, passos, repetições ou bytes retidos; os limites operacionais e o orçamento de memória por sessão permanecem decisões próprias.

Para medir tempo sem instrumentação, pico adicional de alocações Python em execução separada, número de cópias e assinatura reprodutível dos dados:

```bash
PYTHONPATH=src .venv/bin/python scripts/benchmark_simulacao.py
```

O script usa BA com `m=4`, semente de rede 42, sementes epidemiológica/iniciais/isolamento 42/43/44, `beta=0.02`, `gamma=0`, um infectado inicial e 60 passos. Mede execuções individuais com 1.000/4.000 pessoas e uma comparação de três repetições na menor população, com fração de isolamento 0,1, início em 2 e desativação. As assinaturas excluem os timestamps dos manifestos. Os parâmetros de tamanho e quantidade de medições podem ser ajustados pela linha de comando. O pico de `tracemalloc` não representa RSS total, a rede previamente carregada ou a memória do navegador.

## Verificação

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q
cd frontend
npm test
npm run build
npm run lint
npm run format:check
```

Os testes Node incluem execução real de React/Vite, API Python e Chromium headless, sem novas bibliotecas. `CHROME_BIN` permite indicar um Chromium instalado e `PYTHON_BIN` um Python com o projeto disponível. Sem navegador instalado, o teste correspondente é registrado como ignorado; os demais continuam executando. O ambiente de desenvolvimento usual utiliza `.venv/bin/python`.

Os testes verificam cancelamento visual, bloqueio de controles, JSON no carregamento direto, faixas, cores do SVG/PNG, CSV agregado, consulta de execuções e invalidação por revisão. A tela de execução também é exercitada sem histórico, com validação reutilizada, IDs sorteados e inteiros grandes, falha de consulta e nova tentativa, contagens reais iguais a zero, reinicialização e lista de IDs expansível por teclado. A avaliação histórica e as evidências da correção estão em `AvaliacaoBranchJoao.md`. Isso não substitui uma bateria científica completa nem um artigo SBC final com resultados experimentais revisados.
