# Simulador de Epidemias em Redes

Aplicação científica para importar ou gerar redes de contatos, executar modelos epidemiológicos SIR, comparar estratégias de isolamento e visualizar os resultados. O projeto combina uma API local em Python, uma interface web em React/TypeScript e uma campanha experimental documentada.

## Recursos

- importação de redes por CSV e geração de redes Erdős-Rényi e Barabási-Albert;
- inspeção estrutural, prévia paginada e visualização 2D/3D dos indivíduos;
- modelo SIR com transmissão por contato ou probabilidade direta;
- sementes separadas para indivíduos iniciais, eventos epidemiológicos e isolamento;
- execução individual e comparação com repetições;
- estratégias aleatória e por grau, com desativação, redução ou exclusão de contatos;
- histórico por passo, métricas agregadas, gráficos e exportação em CSV, JSON, SVG e PNG;
- persistência temporária dos resultados em sessão da API e no navegador;
- scripts de experimentos, análises, restauração de artefatos e benchmark.

## Arquitetura

```text
frontend/                 Interface React, TypeScript e Vite
src/simulador/            Domínio, motor SIR, API local e carga de redes
tests/                    Testes Python do domínio e da API
scripts/                  Experimentos, análises e instrumentação
dados/dados/              Redes, resultados experimentais e artefatos
docs/                     Especificação, modelagem e relatórios
entrega/                  PDFs finais preparados para entrega
```

O frontend consome a API em `/api`. A API mantém redes e resultados em memória; reiniciá-la limpa o estado da sessão. Os dados experimentais arquivados são independentes da interface.

## Executar localmente

Requisitos: Python 3.10 ou superior e Node.js compatível com o frontend.

1. Inicie a API na raiz do projeto:

```bash
PYTHONPATH=src python3 -m simulador.api_local
```

Por padrão, a API fica em `http://127.0.0.1:8000`. Outra porta pode ser informada com `--porta`, por exemplo:

```bash
PYTHONPATH=src python3 -m simulador.api_local --porta 8001
```

2. Em outro terminal, instale e execute o frontend:

```bash
cd frontend
npm ci
npm run dev
```

O endereço exibido pelo Vite será normalmente `http://localhost:5173`. As requisições `/api` são encaminhadas para a API local na porta 8000.

## Testes e verificações

Testes Python:

```bash
PYTHONPATH=src python3 -m pytest
```

Testes e validações do frontend:

```bash
cd frontend
npm test
npm run build
npm run lint
npm run format:check
```

O README completo da interface, os fluxos das quatro telas e os comandos disponíveis estão em [frontend/README.md](frontend/README.md).

## Experimentos da etapa 3

A campanha concluiu **33 lotes, 9.900 trajetórias científicas e 635.259 registros**. Os experimentos compararam uma rede escolar com controles Erdős-Rényi e Barabási-Albert, além de mecanismos, orçamento, instante de início e sensibilidade em relação a β.

- [Metodologia e estado da campanha](dados/dados/experimentos/README.md)
- [Topologias — bloco A](dados/dados/experimentos/topologia-v1/README.md)
- [Intervenções — blocos B, C e D](dados/dados/experimentos/intervencoes-v1/README.md)
- [Desempenho — benchmark](dados/dados/experimentos/desempenho-v1/README.md)
- [Redes reais e preparo da base escolar](dados/dados/redes_reais/README.md)
- [Controles sintéticos ER/BA](dados/dados/redes_sinteticas/controles-etapa3-v1/README.md)
- [Dados, restauração e integridade dos artefatos](dados/README.md)

Os lotes extensos são preservados em dois arquivos ZIP acompanhados de hashes. Scripts locais restauram os históricos, métricas e curvas ignorados pelo Git sem executar novamente o modelo SIR.

## Documentação

- [Índice geral da documentação](docs/README.md)
- [Problema e epidemiologia](docs/epidemiologia/problema-e-epidemiologia.md)
- [Modelagem do grafo](docs/modelagem/ModelagemGrafo.md)
- [Classes e diagramas](docs/modelagem/simulador-epidemias/modelagem-de-classes.md)
- [Etapa 1 — problema, modelagem e plano](docs/Artefatos/Etapa1-Problema-Modelagem-Plano.pdf)
- [Etapa 2 — implementação da aplicação](docs/Artefatos/Etapa2-Implementacao-Aplicacao.pdf)
- [Etapa 3 — relatório técnico final](docs/Artefatos/Etapa3-Relatorio-Tecnico.pdf)

O PDF da Etapa 1 reúne o problema, a justificativa da modelagem e o plano de desenvolvimento. A Etapa 2 documenta a aplicação implementada. O relatório da Etapa 3 consolida os experimentos, o desempenho e as conclusões no formato técnico do projeto.
