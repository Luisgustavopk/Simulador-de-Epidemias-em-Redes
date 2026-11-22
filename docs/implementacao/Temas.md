# Temas da interface

A identidade do Observatório utiliza a paleta verde Lima e sua variante Noturno, presentes no protótipo. Os dois temas compartilham os mesmos papéis semânticos. As cores ficam em [`tokens.css`](../../frontend/src/styles/tokens.css), com as substituições do tema escuro em `:root[data-theme='dark']`.

## Paleta

| Token | Claro | Noturno |
| --- | --- | --- |
| `--color-background` | `#E9EDE5` | `#171A18` |
| `--color-surface` | `#FCFDF9` | `#222723` |
| `--color-surface-subtle` | `#F0F3EB` | `#2B312C` |
| `--color-text` | `#20332A` | `#E6EEE7` |
| `--color-text-secondary` | `#475443` | `#C0CEC2` |
| `--color-text-muted` | `#5B6655` | `#A1B0A4` |
| `--color-border` | `#DCE1D5` | `#3C453E` |
| `--color-control-border` | `#819077` | `#77877A` |
| `--color-accent` | `#D4F58C` | `#D4F58C` |
| `--color-on-accent` | `#20332A` | `#20332A` |
| `--color-action` | `#20332A` | `#E3EBDF` |
| `--color-on-action` | `#FCFDF9` | `#1A281F` |
| `--color-focus` | `#415426` | `#D4F58C` |
| `--color-success` | `#3F6B46` | `#9FCCA6` |
| `--color-danger` | `#9C392C` | `#FFB4A6` |
| `--color-danger-surface` | `#FBEBE6` | `#3D2B27` |

Há também tokens de hover, destaque suave, cores SIR e visualização do grafo. O tema Noturno usa tons mais claros para as categorias SIR e para os textos de estado. Cor não substitui o rótulo que identifica um estado ou um erro.

Use `--color-on-accent` para texto ou ícone sobre o destaque lima. `--color-text` representa texto sobre a superfície do tema e fica claro no Noturno; usá-lo sobre o destaque lima reduziria o contraste. A mesma separação vale para `--color-action` e `--color-on-action`.

## Troca e preferência

O botão do cabeçalho alterna o tema da interface inteira. O nome acessível informa a ação: **Usar tema escuro** ou **Usar tema claro**. Em telas menores, o texto visual é recolhido e o nome acessível é preservado. O botão mantém uma área de 44 × 44 px e o indicador de foco.

A escolha fica em `localStorage`, na chave `observatorio-tema`, com valor `light` ou `dark`. Sem uma preferência válida, a interface acompanha `prefers-color-scheme`, incluindo alterações do sistema enquanto a página está aberta. Uma escolha explícita tem prioridade. Alterações da preferência em outra aba da mesma origem são sincronizadas.

Se o armazenamento estiver bloqueado, a troca continua funcionando durante a página atual. Recarregar passa a utilizar novamente a preferência do sistema. A escolha de tema é independente da sessão e da rede mantidas pela API Python.

## Organização

| Arquivo | Responsabilidade |
| --- | --- |
| [`frontend/index.html`](../../frontend/index.html) | Escolher e aplicar o atributo `data-theme` antes de carregar o React, evitando o desenho inicial no tema incorreto. |
| [`useTema.ts`](../../frontend/src/hooks/useTema.ts) | Alternância, persistência, sincronização entre abas, preferência do sistema e atualização de `theme-color`. |
| [`ThemeToggle.tsx`](../../frontend/src/components/ThemeToggle.tsx) | Controle global reutilizado pelo shell. |
| [`tokens.css`](../../frontend/src/styles/tokens.css) | Paletas semânticas, `color-scheme` dos controles nativos e cores de visualização. |
| [`index.css`](../../frontend/src/index.css) | Superfície base, seleção de texto, campos, placeholders, caret e foco. |
| [`App.css`](../../frontend/src/App.css) | Aplicação dos tokens aos componentes e adaptação do cabeçalho. |

Novas telas devem consumir os mesmos tokens por papel. Fundos, textos e bordas precisam acompanhar o tema; os componentes não devem criar outra paleta com valores locais. O estado do controle de tema fica separado da coordenação de carga da rede.

## Tema do grafo

Os controles **Claro** e **Escuro** próximos à topologia continuam restritos ao grafo. As cores claras usam `--color-plot-light-*` e permanecem claras no Noturno. As cores escuras usam `--color-plot-*`, incluindo a variante verde mais profunda do Noturno.

As quatro combinações são válidas: interface clara com grafo claro ou escuro e interface Noturno com grafo claro ou escuro. Trocar o tema global não gera outra rede, não altera a confirmação e não reinicia seleção ou zoom.

## Verificação

Passaram Prettier, ESLint, build TypeScript/Vite e os 11 testes existentes do cliente HTTP. A alteração não modifica o núcleo Python.

No Chromium foram conferidos teclado/foco, persistência, preferência explícita sobre o sistema, sincronização entre abas, alteração da preferência do sistema, armazenamento bloqueado, valor salvo inválido, aplicação antes de carregar o React, funcionamento offline e movimento reduzido. As larguras emuladas de 1440, 1024, 768, 390 e 320 px ficaram sem overflow horizontal.

O axe não encontrou violações nos 11 estados avaliados: vazio Noturno, erro de validação Noturno, as quatro combinações de tema da interface/grafo, Noturno em mobile, erro CSV em mobile nos dois temas e API indisponível nos dois temas. As 24 combinações de tokens medidas atenderam aos limites aplicáveis de 4,5:1 para texto e 3:1 para foco e borda de controles. As capturas em desktop e mobile foram inspecionadas. Essa verificação não substitui testes em dispositivos físicos, outros navegadores e leitores de tela.
