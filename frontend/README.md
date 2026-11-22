# Interface web — Observatório

Interface React, TypeScript e Vite do Simulador de Epidemias em Redes. A aplicação integra carga e inspeção de redes, configuração do modelo SIR, execução individual ou comparativa e leitura dos resultados.

## Fluxo disponível

A navegação possui quatro etapas:

1. **Rede de contatos** — importa ou gera uma rede, confirma uma revisão e permite inspeção estrutural.
2. **Configuração** — define β, γ, infectados iniciais, sementes, horizonte e intervenção.
3. **Simulação** — executa uma trajetória ou uma comparação com repetições.
4. **Resultados** — apresenta métricas, histórico, gráficos, exportações e resultados anteriores da mesma rede.

As páginas são acessadas pelos fragmentos `#rede`, `#configuracao`, `#simulacao` e `#resultados`.

## Executar localmente

Na raiz do repositório, com o ambiente Python ativo:

```bash
PYTHONPATH=src python -m simulador.api_local
```

Em outro terminal:

```bash
cd frontend
npm ci
npm run dev
```

A interface fica disponível pelo endereço informado pelo Vite, normalmente `http://localhost:5173`. O Vite encaminha `/api` para a API local em `127.0.0.1:8000`.

Se a API não estiver disponível, a interface informa a falha de conexão. Reiniciar a API remove as redes e execuções mantidas em memória.

## Tela 01 — Rede de contatos

É possível:

- importar um arquivo `contatos.csv` e, opcionalmente, `individuos.csv`;
- selecionar o separador vírgula, ponto e vírgula ou tabulação;
- gerar redes Erdős-Rényi ou Barabási-Albert com N, parâmetros e semente;
- confirmar a revisão da rede para usar nas etapas seguintes;
- consultar população, contatos, pesos, grau médio, densidade, componentes e distribuição de graus;
- buscar indivíduos pelo ID e consultar seus contatos;
- navegar pelos registros paginados de indivíduos e contatos;
- alternar a prévia entre mapa mundial ilustrativo e visualização 3D.

A prévia mostra até 180 indivíduos e 1.200 contatos. As métricas, inspeções e cálculos consideram a rede completa. O mapa e o 3D usam posições ilustrativas: os arquivos CSV não fornecem coordenadas e essas posições não alteram pesos, arestas ou resultados epidemiológicos.

Na prévia 3D, arraste para girar, use a roda ou os controles para aproximar e desviar. No mapa, arraste para mover e ajuste o zoom. Tela cheia, seleção de indivíduo, filtro de contatos e temas do grafo estão disponíveis nos dois modos.

## Tela 02 — Configuração

A configuração aceita:

- **Intensidade:** β multiplicado pelo peso de cada contato;
- **Probabilidade direta:** β não se aplica;
- γ para recuperação;
- IDs explícitos ou quantidade sorteada sem reposição;
- sementes independentes para iniciais, eventos epidemiológicos e isolamento;
- limite máximo de passos abstratos;
- intervenção aleatória ou por grau;
- fração isolada e instante de início;
- desativação dos contatos, redução da intensidade ou exclusão dos contatos.

A interface valida os parâmetros antes da preparação do ensaio. Alterar ou recarregar a rede invalida o contexto anterior e exige nova validação.

Em comparação, o usuário define o número de repetições. Os cenários são sem intervenção, seleção aleatória e seleção por grau.

## Tela 03 — Simulação

Após validar uma configuração, a tela permite:

- calcular a simulação completa antes da reprodução;
- avançar um passo por vez;
- iniciar ou continuar a reprodução;
- pausar o ensaio;
- percorrer o histórico calculado;
- acompanhar S, I, R e isolados;
- reiniciar a reprodução;
- continuar com uma simulação individual ou uma comparação.

No modo repetições, a interface permite selecionar cenário e repetição para examinar cada trajetória.

O estado visual dos nós é ilustrativo. Para contagens, métricas e histórico, considere os registros armazenados pelo backend.

## Tela 04 — Resultados

A tela de resultados oferece:

- pico de infectados e instante do pico;
- fração acumulada;
- fração final recuperada;
- horizonte observado e motivo de término;
- histórico em tabela paginada;
- gráficos dos cenários e das repetições;
- métricas agregadas com médias e faixas de dispersão;
- recuperação de execuções anteriores da mesma revisão da rede;
- exportação de histórico em CSV e JSON;
- exportação do gráfico em SVG e PNG;
- CSV agregado e CSV de trajetórias para comparações.

Os resultados ficam associados ao contexto e à revisão da rede confirmada. Um resultado não é reaplicado a outra rede ou revisão.

## Scripts disponíveis

No diretório `frontend`:

```bash
npm run dev          # servidor de desenvolvimento
npm run build        # compilação TypeScript e build de produção
npm run preview      # prévia local do build
npm run lint         # lint ESLint e React Hooks
npm run format       # formata os arquivos com Prettier
npm run format:check # verifica a formatação
npm test             # testes de funções e cliente HTTP
```

Para o build completo, deixe a API Python ativa, pois a prévia precisa consultar `/api/rede`.

## Testes

Os testes unitários usam `node:test` e o compilador TypeScript. Eles cobrem principalmente o cliente HTTP e funções de layout, projeção e câmera.

A verificação Python relacionada à API e ao domínio continua na raiz do repositório:

```bash
PYTHONPATH=src python -m pytest
```

Os testes frontend também podem ser executados pela plataforma configurada do projeto:

```bash
npm test
npm run build
npm run lint
```

## Organização do código

```text
src/
├── App.tsx                  # Navegação das quatro etapas
├── components/              # Shell, menu, cabeçalho e componentes comuns
├── features/
│   └── rede/
│       ├── components/      # Importação, distribuição e inspetor
│       └── visualizacao/    # Mapa, 3D, câmera e desenho
├── features/resultados/     # Gráficos, tabelas e formatos de exportação
├── hooks/                   # Carga e sincronização da rede
├── pages/                   # Telas 01, 02, 03 e 04
├── services/                # Cliente da API Python
├── styles/                  # Tema, tokens e estilos globais
└── types/                   # Contratos compartilhados do frontend
```

## Tema e acessibilidade

O cabeçalho alterna entre tema claro e Noturno. A preferência fica salva no navegador. A interface também oferece foco visível, navegação por teclado, regiões de status e controles alternativos aos gestos da visualização.

Os tokens visuais ficam em `src/styles/tokens.css`. O Tailwind é integrado pelo plugin `@tailwindcss/vite`; componentes personalizados reutilizam os mesmos tokens em vez de criar paletas isoladas.

## Persistência local

O navegador usa `sessionStorage` para guardar temporariamente a configuração validada, o histórico em reprodução e o resultado selecionado. Esses dados são associados à rede confirmada e podem ser invalidados após uma mudança.

Os experimentos arquivados da Etapa 3 não são gerados pelo navegador em tempo de demonstração. Os arquivos científicos ficam em `dados/dados/experimentos/topologia-v1/`.

Consulte a [documentação da interface](../docs/implementacao/InterfaceRede.md), o [contrato de carga](../docs/implementacao/CargaInspecao.md) e o [índice da documentação](../docs/README.md) para detalhes da integração e dos resultados.
