# Contribuições dos integrantes

Registro atualizado em **22 de novembro de 2026**, a partir do histórico integrado à branch `main`, até o commit `53340b8`. As datas e autorias são as registradas pelo Git; as descrições foram conferidas pelas alterações de cada commit.

Foram identificados **89 commits: 81 de entregas e 8 de integração (merges)**. Os merges aparecem separadamente, pois integram contribuições já descritas nas entregas. A quantidade de commits registra o histórico de versionamento e não mede o esforço de cada integrante.

| Integrante | Entregas | Merges | Total |
| --- | ---: | ---: | ---: |
| João Vitor | 26 | 2 | 28 |
| Luis Gustavo | 25 | 2 | 27 |
| Wesley Domingos | 30 | 4 | 34 |
| **Total** | **81** | **8** | **89** |

Os registros `WesleySDz` e `Wesley Domingos` foram agrupados por utilizarem o mesmo e-mail de autoria no Git. A consulta considera os commits alcançáveis pela `main`; alterações exclusivas de outras branches não entram nesta contagem.

## João Vitor

**Autor registrado no Git:** João Vitor.

As entregas abrangem arquitetura, requisitos, protótipos e planejamento; o controle temporal da simulação e as métricas; as telas de ensaio e resultados e sua integração à API. Na Etapa 3, o histórico também registra em seu nome a inclusão dos dados adaptados da escola suíça, do protocolo e das evidências de caracterização e importação.

### Entregas

| Data | Commit | Mensagem | Contribuição |
| --- | --- | --- | --- |
| 12/11/2026 | [3520731](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/3520731e541f72cf7e9a0666c5a3227d1d7f780a) | `doc: documento Arquitetura-Grafos e seu arquivo .md` | Documentação da arquitetura em Markdown e PDF, na pasta de modelagem. |
| 12/11/2026 | [76f59d9](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/76f59d9093c22218afaa9bef657e98305e164b1e) | `doc: diagrama de sequencia` | Inclusão do diagrama de sequência em PDF na documentação da modelagem. |
| 12/11/2026 | [6da7c1b](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/6da7c1b9284d65c1699cd83cc6beea5b99094550) | `docs: documento de requisitos` | Inclusão do documento de requisitos em `docs/Artefatos/Requistos-G.pdf`. |
| 12/11/2026 | [4a8ee12](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/4a8ee12ddd252f8d9bf292fbf2aa0ada14764e72) | `docs: planejamento da Etapa 1` | Registro do planejamento da Etapa 1, com tarefas e entregas previstas. |
| 12/11/2026 | [da19b64](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/da19b641c039215f2a27a2da12b01db427fbf093) | `docs: Prototipo tela-01-rede-de-contatos` | Inclusão do protótipo da Tela 01, dedicada à rede de contatos. |
| 12/11/2026 | [61a5b6b](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/61a5b6b9036b62d8d2da8c9eaec846fae8fa1494) | `docs: Prototipo tela-02-protocolo-sir` | Inclusão do protótipo da Tela 02, dedicada à configuração do protocolo SIR. |
| 12/11/2026 | [0df1337](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/0df1337ad8d60d9addf9a1ffb59bf5143806206d) | `docs: Prototipo tela-03-ensaio` | Inclusão do protótipo da Tela 03, dedicada ao ensaio da simulação. |
| 12/11/2026 | [c377d09](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/c377d09d5c4321e5ae36cf9dd7f2c6b1733e777f) | `docs: Prototipo tela-04-resultados-e-metricas` | Inclusão do protótipo da Tela 04, dedicada aos resultados e às métricas. |
| 13/11/2026 | [15fbcc3](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/15fbcc38fdbe7f5498785c1e8ad8f6d2b0f57404) | `docs: Planejamento etapa 2` | Registro do plano de desenvolvimento da Etapa 2. |
| 18/11/2026 | [4c83aa6](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/4c83aa6b44cca0e907f2e6a8449a90993085afd3) | `feat: : implementa nucleo temporal, classes RegistroPasso e Simulacao com validacoes robustas` | Implementação de `RegistroPasso` e `Simulacao` em `simulacao.py`, com validações e testes. |
| 18/11/2026 | [d6412f5](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/d6412f5bd653ffe658242b908cc1c799001329e0) | `feat: implementa calculo de metricas epidemiologicas e testes unitarios` | Implementação de `MetricasEpidemia` em `metricas.py`, com testes unitários. |
| 18/11/2026 | [ac1e9c6](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/ac1e9c64351c7a6d818ec3a6f2a7e38475445e08) | `feat: cria tela 03 de ensaio passo a passo e controles de execucao` | Criação de `SimulationPage.tsx`, dos controles de execução e da ligação com a navegação e a visualização da rede. |
| 19/11/2026 | [caa4eca](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/caa4ecac7094db1d59d4879a5e7a1760bc9b5a1c) | `feat: implementa Tela 04 de resultados, graficos e exportacao CSV` | Implementação de `ResultsPage`, com gráficos e exportação CSV, e ajustes no serviço TypeScript e na API Python. |
| 19/11/2026 | [85612fd](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/85612fd4e0f06eab7e6aea51a0a1f3d5e038fb9c) | `feat: adiciona endpoints de execucao e testes de integracao da api` | Inclusão dos endpoints de execução, dos contratos TypeScript e de testes de integração da API. |
| 19/11/2026 | [8c39c9f](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/8c39c9f5375f281ef5fc6498d3059e8d2a9fa592) | `fix: ajusta navegacao, telas de configuracao e painel de resultados` | Ajustes na navegação, em `ConfigurationPage` e no painel e nos estilos de `ResultsPage`. |
| 19/11/2026 | [302ad03](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/302ad0390567d59f7b452e4e39c05e7df21945e8) | `feat: adiciona motivo de termino e testes de integracao da api` | Inclusão do motivo de término no contrato dos resultados e de testes de integração da API. |
| 19/11/2026 | [50638fa](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/50638fa8348a448aaa572159aa65927ddd383724) | `feat: conecta tela de ensaio ao backend e exibe curvas comparativas nos resultados` | Conexão da Tela 03 ao backend e apresentação de curvas comparativas na Tela 04. |
| 19/11/2026 | [a732c61](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/a732c617eb15d52417001317ef1b11269049965f) | `fix: correção tela 2` | Correção da tela de configuração em `ConfigurationPage.tsx`. |
| 19/11/2026 | [a2281dc](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/a2281dc2f142e8b40e27d7ca30e373777b141c7a) | `docs: Plano de desenvolvimento etapa 3` | Registro do plano da Etapa 3, incluindo experimentação, análise e entrega final. |
| 19/11/2026 | [36f0a2f](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/36f0a2fad0827554eda7f028135063729c4792ae) | `feat: consolida motor sir, regras de metricas, endpoints e testes python` | Consolidação da simulação, das métricas, da comparação e dos endpoints, com ajustes no serviço de carga e nos testes Python. |
| 19/11/2026 | [459bfbb](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/459bfbb5defc41e62dccdec2e4f76874997ddf8e) | `feat: integra telas de ensaio e resultados ao backend e adiciona testes de frontend` | Integração das telas de ensaio e resultados ao backend, com testes dos serviços e do fluxo das páginas. |
| 21/11/2026 | [3c0ff25](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/3c0ff25201b0a3d7d803a465889d572437c1aef2) | `feat: adiciona protocolos, manifesto e fontes da etapa 3` | Inclusão do protocolo experimental, de sua verificação e do manifesto e das fontes da base escolar. |
| 21/11/2026 | [bdac4d4](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/bdac4d4cfbda59c160662e35daffa20070075c75) | `feat: adiciona datasets de contatos, individuos e duracoes` | Inclusão dos CSVs adaptados da escola suíça: contatos, indivíduos, durações observadas e mapa de identificadores. |
| 21/11/2026 | [68456ca](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/68456ca0ecd8e686617c576d59dea280f925e39f) | `feat: adiciona planilhas de caracterizacao estrutural e distribuicao de graus` | Registro da caracterização da escola, com graus, distribuição de graus, componentes e resumo estrutural. |
| 21/11/2026 | [8a84309](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/8a843094d15ced25dc0125d73275733eb2fb58b0) | `test: adiciona logs de testes, auditoria e arquivos de reproducao` | Inclusão de auditoria de fontes, evidências da importação pela interface, logs de testes, arquivos de reprodução e figuras estruturais. |
| 21/11/2026 | [ef22e29](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/ef22e29e674d07511adb9d5b50c8c89c267efe16) | `docs: adiciona prints de evidencias visuais e documentacao readme da pasta de dados` | Documentação da pasta de dados e inclusão de capturas da interface com a rede importada e confirmada. |

### Integrações

| Data | Commit | Mensagem | Contribuição |
| --- | --- | --- | --- |
| 18/11/2026 | [eec97b6](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/eec97b6dd83ba0efa77dd9457b893fc4d7a6f57d) | `merge: atualiza branch com a main` | Atualização da branch de trabalho com as alterações da `main`. |
| 19/11/2026 | [ee18e5e](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/ee18e5e0418d1cb4966157fffb52eb44fe343188) | `merge: resolve conflitos com branch Luis e integra telas 01, 02 e 03` | Resolução de conflitos com a branch de Luis, incluindo ajustes em `App`, `AppShell` e `NetworkPage` para integrar as telas. |

## Luis Gustavo

**Autor registrado no Git:** Luis Gustavo de Souza Xavier.

As entregas abrangem a inicialização do repositório, a modelagem UML e a documentação epidemiológica; os fluxos aleatórios, as configurações e o motor SIR; os critérios de seleção para isolamento e a comparação de cenários, incluindo formulários, validações e testes.

### Entregas

| Data | Commit | Mensagem | Contribuição |
| --- | --- | --- | --- |
| 29/10/2026 | [5062d89](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/5062d89df40013718d39369f527d413de7068e5b) | `Initial commit` | Inicialização do repositório com o título do projeto no `README.md` e a inclusão da licença em `LICENSE`. |
| 09/11/2026 | [79da730](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/79da73080e3517ceff83bacaf231dc32251a5be0) | `docs: adiciona modelagem de casos de uso` | Modelagem dos casos de uso, com fonte PlantUML e versões SVG e PNG. |
| 09/11/2026 | [9337a85](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/9337a8556b7d74d1a061d54b81492bd3ae94b951) | `docs: adiciona modelagem de estados do indivíduo` | Modelagem dos estados do indivíduo, com fonte PlantUML e versões SVG e PNG. |
| 09/11/2026 | [99294f6](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/99294f67890121b031881e8ced84bf82a5a46b3a) | `docs: adiciona modelagem de classes` | Modelagem de classes, com diagrama e documentação em `modelagem-de-classes.md`. |
| 09/11/2026 | [1191dbc](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/1191dbc778adc54da369d1a9ae9bcbf8b90a01b3) | `docs: adiciona documentação de epidemiologia` | Documentação do problema e da epidemiologia em Markdown e PDF, com atualização dos índices de documentação. |
| 16/11/2026 | [c9fce60](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/c9fce60c6984d552147e62b18586d835f631a17c) | `docs: atualiza modelagens UML` | Atualização dos diagramas UML de casos de uso, classes e estados, incluindo fontes e imagens. |
| 16/11/2026 | [b3de876](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/b3de876b55c11de1f45b080f98a3fbc57ec6bbe7) | `docs: atualiza documento de problema e epidemiologia` | Atualização do PDF sobre o problema e a epidemiologia. |
| 16/11/2026 | [c9972eb](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/c9972eb0067eefa47560408c3271078a371b6cfd) | `feat: adiciona gerador aleatório com fluxos independentes` | Implementação de `aleatoriedade.py`, com fluxos aleatórios independentes e testes. |
| 16/11/2026 | [c84a62a](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/c84a62a60f44fb21bc23aaa2b1763f5131a396d5) | `feat: implementa configuração e condições iniciais` | Implementação de `configuracao.py`, incluindo parâmetros, condições iniciais e testes. |
| 16/11/2026 | [4000104](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/4000104e96e2abdf4f359fe6b5508eae2d0a33d8) | `feat: implementa atualização síncrona do motor SIR` | Implementação da atualização síncrona em `motor_sir.py`, com testes do motor epidemiológico. |
| 16/11/2026 | [4744eb6](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/4744eb6ea0ee3b0299c5fd50b32770e28f8bb627) | `feat: adiciona validação de configuração na API local` | Validação da configuração em `configuracao_api.py`, integração à API local e testes HTTP. |
| 16/11/2026 | [4ef0472](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/4ef0472d5f3564c0c3b0c435ef528e85b1d7caee) | `feat: adiciona interface de configuração epidemiológica` | Implementação da tela de configuração epidemiológica, dos serviços de comunicação e dos testes correspondentes. |
| 16/11/2026 | [431bd8f](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/431bd8f80b3c3f9fed0331225e87bf185fdf2320) | `docs: atualiza modelagem de classes para integração` | Atualização da documentação da modelagem de classes para a integração dos módulos. |
| 16/11/2026 | [42a88cc](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/42a88cc8bd74e8737a0a4919c4d8f3b6f20f4400) | `docs: atualiza documentação de epidemiologia` | Revisão da documentação de epidemiologia em Markdown e do índice em `docs/README.md`. |
| 17/11/2026 | [47aea5f](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/47aea5fce78ef0ddd4149366044e234eb5282ea6) | `fix: corrige precisão da transmissão no motor SIR` | Correção da precisão do cálculo de transmissão no motor SIR, acompanhada de teste de regressão. |
| 17/11/2026 | [5aff4e2](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/5aff4e29f3a846afaf08b5854e082b9bfaeb4ea3) | `feat: implementa estratégias de seleção para isolamento` | Implementação da seleção aleatória e por grau em `estrategias_isolamento.py`, com configuração e testes. |
| 17/11/2026 | [69929e8](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/69929e865fc6d3b2cbc9c2ba464c68cef285ad3b) | `feat: adiciona validação da intervenção na API` | Validação dos campos da intervenção na API, com testes específicos. |
| 17/11/2026 | [397a781](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/397a781b52da7a1ade95bdce6cd574e77570606d) | `feat: adiciona interface de configuração da intervenção` | Implementação de `InterventionFields`, integração ao formulário de configuração e testes do contrato da intervenção. |
| 18/11/2026 | [e20a4b2](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/e20a4b268872beb4f2396a2748fc8f7a365d5173) | `feat: implementa comparação de cenários` | Implementação de `comparacao.py` para executar e consolidar cenários, com testes. |
| 18/11/2026 | [6e7184e](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/6e7184e069ef856852e8cba6b0b375258fb56d7e) | `feat: valida comparação na API` | Validação de comparações na API e integração entre `api_local.py`, `comparacao_api.py` e a configuração. |
| 18/11/2026 | [e91ddad](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/e91ddad47887105da0a41adf0f599479b2eac3a7) | `test: unifica o carregador dos testes` | Unificação do carregador dos testes dos serviços TypeScript em `carregarConfiguracaoApi.mjs`. |
| 18/11/2026 | [8bed5d6](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/8bed5d646baee39a1a11cf572005d0fd6c57eff6) | `feat: implementa formulário de comparação` | Implementação do formulário de comparação, dos contratos do serviço e de seus testes. |
| 18/11/2026 | [2af73d1](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/2af73d10cb7c55c353766b445b616d9eb2fab88f) | `fix: valida a comparação de cenários` | Ajustes nas validações da comparação e em sua relação com sementes, configuração, seleção e motor SIR. |
| 18/11/2026 | [9d56e68](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/9d56e68d9994d1db98b8e44e11e5b8ab65fbdd3f) | `fix: corrige os formulários de validação` | Correções nos formulários e resumos de configuração, nos campos da intervenção e nos contratos de validação. |
| 22/11/2026 | [03d457a](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/03d457a911ad46c2f8ea56b0c3449cd865d058e0) | `fix(doc) ajusta o planejamento` | Atualização dos planejamentos das três etapas para refletir a implementação e a campanha concluída. |

### Integrações

| Data | Commit | Mensagem | Contribuição |
| --- | --- | --- | --- |
| 16/11/2026 | [66394f3](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/66394f31435544dcc135d7d13ca8845a78df947e) | `merge: integra branch Wesley na Luis` | Integração da branch de Wesley à branch de Luis para compatibilizar a configuração e o motor com a rede. |
| 18/11/2026 | [e22cf0c](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/e22cf0c0962090fd8c6d0496e6d56eb7868a537b) | `Merge remote-tracking branch 'origin/Wesley' into Luis` | Nova integração das alterações de Wesley à branch de Luis, com compatibilização dos módulos Python e dos testes. |

## Wesley Domingos

**Autor registrado no Git:** `WesleySDz` e `Wesley Domingos`.

As entregas abrangem a estrutura da rede, importação e geração, análise estrutural, mecanismos de isolamento e serviço de carga; a API local, a estrutura do frontend e as visualizações da rede. O histórico inclui ainda a consolidação de módulos compartilhados, correções e medições, além dos scripts e resultados dos experimentos de topologia da Etapa 3.

### Entregas

| Data | Commit | Mensagem | Contribuição |
| --- | --- | --- | --- |
| 07/11/2026 | [8ec2eec](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/8ec2eec234066686ae1a3237c9fcbedcc5549657) | `docs: referencias` | Organização das referências em `docs/referencias/REFERENCIAS.md`. |
| 07/11/2026 | [b096fe6](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/b096fe6420a7ca88f9f1a48863db42f83f2fa5bc) | `docs: modelagemGrafo.md` | Criação deste registro de contribuições e da documentação `docs/modelagem/ModelagemGrafo.md`. |
| 07/11/2026 | [cccceee](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/cccceeefe534f12de7603374bee1bae746dc2ec2) | `feat: adiciona classes de indivíduo e aresta com testes` | Implementação inicial de indivíduo e aresta, em `individuo.py` e `aresta.py`, com testes. |
| 08/11/2026 | [5aa1759](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/5aa17591ddadfa6518373ba3d50504c6f5fee6f1) | `feat: grafo.py e test` | Implementação inicial de `grafo.py`, testes da estrutura e configuração do projeto em `pyproject.toml`. |
| 08/11/2026 | [8989160](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/8989160a12b6a764dce99d3c188c395f0a0be820) | `docs: regras de transmissão e isolamento` | Documentação das regras de transmissão e isolamento, atualização das referências e ajustes no `.gitignore`. |
| 09/11/2026 | [74ef5d4](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/74ef5d499160a83146a22b5625bf1f05929a1f25) | `refactor: adapta modelos ao diagrama de classes` | Adaptação dos modelos de grafo, indivíduo e aresta ao diagrama de classes, com revisão dos testes. |
| 12/11/2026 | [b709040](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/b709040b8dfec2631a098c96a598cf527e0bbab0) | `docs: historias de usuario` | Inclusão do documento de histórias de usuário. |
| 15/11/2026 | [da7ec2e](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/da7ec2e14e322b0034e6777ceb52d430e061da12) | `feat: estrutura do grafo` | Reorganização do domínio em `RedeContatos`, `Individuo` e `Contato`, com atualização da modelagem e dos testes. |
| 15/11/2026 | [72676d6](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/72676d64704f224c97427e451490b1b2afc02cae) | `feat: importação de redes CSV` | Implementação de `importacao.py`, com leitura de redes CSV, arquivos de exemplo e testes. |
| 15/11/2026 | [6595845](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/6595845ecd7d087aad32c86d0d43a2d509ecab8a) | `feat: geração .py` | Implementação dos geradores de redes em `geracao.py`, com testes. |
| 15/11/2026 | [7e0f6b2](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/7e0f6b22a83affd25b409e2629863161d3cdf328) | `feat: analise_estrutural .py` | Implementação de percursos e métricas da rede em `analise_estrutural.py`, com testes. |
| 15/11/2026 | [ea48e3d](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/ea48e3d971cc8f3fb23d0c19623a0648231442e1) | `feat: adicionar operações de alteração e remoção de contatos` | Inclusão das operações de alteração e remoção de contatos em `Contato` e `RedeContatos`, com testes. |
| 15/11/2026 | [f856fda](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/f856fda054ee7c994440e9753f6b7dfe99ffc8b1) | `feat: implementar mecanismos de isolamento preservando a população` | Implementação dos mecanismos de isolamento em `isolamento.py`, preservando os indivíduos e atualizando testes e módulos relacionados. |
| 15/11/2026 | [1395951](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/1395951ec4de4296d0c2fdd44d860bfbaa36c0cc) | `feat: benchmark_rede` | Inclusão de `benchmark_rede.py` para medição da rede, com ajustes na importação e em seus testes. |
| 15/11/2026 | [b59ccc2](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/b59ccc2bbf7d98010c797b184910a645623aa12f) | `feat: carga de redde .py` | Implementação do serviço de carga em `carga_rede.py`, com testes. |
| 15/11/2026 | [bc8cf64](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/bc8cf64fcbc1e853cb565153dcd5d797815fb5a5) | `perf: otimizar paginação e corrigir contratos da carga de redes` | Otimização da paginação e correção dos contratos do serviço de carga, com ajustes nos testes e no benchmark. |
| 15/11/2026 | [fe31f7a](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/fe31f7ad0fb06cae3b236219c5a0846fb491ee50) | `feat: inicialização front` | Criação da estrutura inicial do frontend com React, TypeScript e Vite. |
| 15/11/2026 | [b56a965](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/b56a965e04209207b07e9f0ec2fc33166dc7ebef) | `feat: tailwind css` | Configuração do Tailwind CSS e das dependências e estilos iniciais do frontend. |
| 15/11/2026 | [ca3da8f](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/ca3da8fc249aed5bf0102d9435b19ecfb1273b95) | `feat: cores padrão e modo escuro` | Definição dos tokens de cores, do tema escuro e dos componentes e controles de alternância do tema. |
| 15/11/2026 | [317d76e](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/317d76e5c48f48863d3fd5a98e8e4ac4c8820d92) | `test: api_local` | Inclusão da API HTTP local em `api_local.py` e de testes do atendimento das requisições. |
| 15/11/2026 | [0c77ffc](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/0c77ffc66a6a746d4e0cf521c5f492d7f8b01383) | `feat: rede.ts` | Definição dos tipos da rede e do serviço `redeApi.ts`, com ligação à estrutura da interface. |
| 15/11/2026 | [d4e63e2](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/d4e63e2bad1fc5fa8061d514244921aa4071013c) | `feat: rede de contatos fornt` | Implementação dos componentes da rede de contatos, da distribuição de graus e da visualização geográfica. |
| 17/11/2026 | [abe6663](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/abe6663433a34ba59919c99ea905070c4fc3aa5d) | `feat: 3d view` | Inclusão da visualização 3D, do controle de câmera e dos layouts, com ajustes nos componentes de inspeção e consulta da rede. |
| 20/11/2026 | [6694bb7](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/6694bb78631833c922fa14c3ed732b556854705a) | `feat: integração main` | Consolidação da execução e dos resultados; inclusão de `ResumoEnsaio`, `TabelaHistorico`, `dadosResultados.ts` e `ResultadoSimulacao`, com ajustes no domínio, na API e nos testes. |
| 20/11/2026 | [4326133](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/4326133702c0ca46bf0696e2529de8980d42e74d) | `fix: sideabr e ensaio` | Correções na barra lateral e na tela de ensaio, inclusão de `benchmark_simulacao.py` e ajustes nos testes de interface e otimização. |
| 22/11/2026 | [7d6f560](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/7d6f560563ac5768cda8bcab21e18a50123fe2bc) | `feat: script rede real` | Inclusão dos scripts de preparação, caracterização, experimentação, análise, verificação e restauração; registro dos controles sintéticos; correção temporal do isolamento, testes e regras de versionamento. |
| 22/11/2026 | [2d66d94](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/2d66d943fbd4a728def78fbc5401dd02afa867a8) | `docs: registra resultados de topologia e guia de Wesley` | Registro dos resultados de topologia de 21 redes e 6.300 trajetórias, com pacote de lotes, hashes, resumos, gráficos, estado experimental e documentação de modelagem e execução. |
| 22/11/2026 | [f69ad66](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/f69ad669153cb0d85a7c5561efc3a45f14e6db4f7) | `fix: resultados front` | Atualização dos gráficos e filtros do frontend, reorganização dos dados, expansão dos testes das telas e consolidação dos artefatos da Etapa 3. |
| 22/11/2026 | [dc3d41c](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/dc3d41c46300be419bf98ad561bb331745744f8f) | `feat: analise de desempenho` | Inclusão dos blocos B/C/D, dos 33 lotes da campanha, das figuras de intervenções e sensibilidade, do benchmark e dos scripts de restauração e verificação. |
| 22/11/2026 | [53340b8](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/53340b834660978860a3c1f2a7d08a66c7d21086) | `docs: slides, video e latex` | Preparação dos PDFs finais, dos slides e dos materiais de demonstração da entrega, com atualização dos índices e do README principal. |

### Integrações

| Data | Commit | Mensagem | Contribuição |
| --- | --- | --- | --- |
| 18/11/2026 | [ddca149](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/ddca14925078e389caa701aa78d4e1cb09876079) | `Merge pull request #1 from Luisgustavopk/Wesley` | Integração da branch de Wesley à `main` pelo pull request #1, reunindo as entregas da rede, da API e da interface. |
| 19/11/2026 | [23e1df2](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/23e1df2b503d4ca5ad795153cddf002345da2534) | `Merge pull request #2 from Luisgustavopk/Luis` | Integração da branch de Luis à `main` pelo pull request #2, reunindo configuração, motor SIR e comparação. |
| 19/11/2026 | [f615760](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/f6157606c1f9ced98372ee7e87fe64349393749f) | `Merge pull request #3 from Luisgustavopk/João` | Integração da branch de João à `main` pelo pull request #3, reunindo simulação temporal, métricas, ensaio e resultados. |
| 22/11/2026 | [4ab90f7](https://github.com/Luisgustavopk/Simulador-de-Epidemias-em-Redes/commit/4ab90f7964373d98ab7bc8512f3d64024f316d87) | `Merge pull request #4 from Luisgustavopk/João` | Integração da branch de João à `main` pelo pull request #4, incluindo dados da escola, protocolo e evidências da Etapa 3. |

## Trabalho compartilhado e limites do registro

A autoria dos commits foi preservada mesmo quando a atividade difere da divisão planejada. Por exemplo, os dados adaptados da escola e as primeiras evidências da Etapa 3 aparecem nos commits de João de 21/11; os scripts de experimentação e os resultados de topologia aparecem nos de Wesley de 22/11.

O isolamento reúne contribuições complementares: Luis implementou os critérios de seleção, Wesley implementou os mecanismos sobre os contatos e João desenvolveu o controle temporal que os aciona. A integração posterior alterou módulos dessas três partes, conforme os commits relacionados acima.

As entregas finais da Etapa 3 incluem dados adaptados, testes, scripts, resultados, gráficos, relatório, slides e benchmark, distribuídos pelos commits acima. Materiais locais não versionados não recebem atribuição por este levantamento.

As entradas sobre testes registram a inclusão ou alteração de código e evidências de teste. A aprovação de uma suíte deve ser conferida em seu respectivo relatório de execução.

## Atualização do registro

Para acrescentar novas contribuições, consultar o histórico integrado à `main` e conferir os arquivos de cada commit. Manter a autoria registrada pelo Git, separar as integrações, atualizar a data e o commit de referência e revisar as contagens. O próprio ajuste deste documento ainda precisa de um novo commit para integrar o histórico descrito.

```bash
git log main --no-merges --date=short --format='%ad | %h | %an | %s'
git log main --merges --date=short --format='%ad | %h | %an | %s'
git show --stat <commit>
```

A divisão prevista de responsabilidades está nos planos da [Etapa 1](docs/Artefatos/Planejamentos/planejamento-etapa1-simulador-epidemias.md), da [Etapa 2](docs/Artefatos/Planejamentos/plano_de_desenvolvimento_etapa_2.md) e da [Etapa 3](docs/Artefatos/Planejamentos/plano_de_desenvolvimento_etapa_3.md). Esses planos descrevem atribuições; as tabelas deste registro descrevem as entregas encontradas no Git.
