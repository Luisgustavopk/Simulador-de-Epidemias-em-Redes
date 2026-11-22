# Localização dos dados

Os arquivos do projeto ficam em **[dados/](dados/)**, dentro desta pasta, conforme a organização adotada em 22/11/2026.

- [Base escolar, preparo e caracterização](dados/redes_reais/README.md).
- [Protocolo experimental e configuração-base](dados/experimentos/README.md).
- [Controles ER/BA gerados e caracterizados](dados/redes_sinteticas/controles-etapa3-v1/README.md).
- [Resultados dos experimentos de topologia — 6.300 trajetórias](dados/experimentos/topologia-v1/README.md).
- [Conferência da base na interface](dados/redes_reais/evidencias/interface-escola/README.md).
- [Aviso ao integrante B](../docs/implementacao/Aviso-IntegranteB-Etapa3.md).

Os scripts na raiz do repositório já usam `dados/dados/` como destino padrão. O CSV original baixado fica em `dados/dados/redes_reais/originais/`, a partir da raiz do repositório, ignorado pelo Git, para permitir a reprodução local. A [conferência da reorganização](dados/redes_reais/evidencias/reorganizacao-2026-11-22.json) registra os arquivos preservados e as cópias idênticas removidas.

## O que preservar no Git

No bloco de topologias, preserve `lotes-topologia-v1.zip` e seu `.sha256`, protocolos, resumos por rede/modelo, caracterização consolidada, inventário, verificações, análise, figuras finais e documentação. O ZIP contém os 21 lotes `.json.gz` e seus 21 hashes individuais. Os scripts e testes também devem acompanhar a entrega.

As exportações extensas de históricos, métricas, diferenças e curvas, os graus/componentes individuais e as pastas de controles sintéticos são regeneráveis e estão no `.gitignore`. A pasta `lotes/` extraída também é ignorada; seu conteúdo é preservado no pacote. Os arquivos existentes continuam no disco. O log operacional também é local; os horários, o ambiente e a cobertura dos lotes permanecem registrados em `execucao.json`.

Após clonar o repositório, execute na raiz:

```bash
PYTHONPATH=src python3 scripts/restaurar_artefatos_topologia.py
```

O comando confere o pacote, os hashes individuais e os registros preservados antes de repor os lotes e arquivos derivados, sem executar novas simulações. Consulte os [detalhes dos artefatos](dados/experimentos/topologia-v1/README.md#arquivos-e-verificação).

**Organização em 22/11/2026:** a primeira seleção preservou 55 dos 243 arquivos das pastas de resultados e controles. O empacotamento substitui os 42 lotes/hashes individuais por dois arquivos disponíveis para versionamento, reduzindo a seleção a 15 arquivos. Os originais locais continuam presentes, junto dos 188 derivados ou logs que já estavam ignorados. A conferência inicial restaurou 242 arquivos idênticos, sem o log histórico. Com o pacote, a restauração conferiu 244 arquivos, incluindo ZIP e hash, sem novas trajetórias; os 14 testes de artefatos passaram. Os [detalhes](dados/experimentos/topologia-v1/README.md#reproduzir) incluem as verificações de integridade e preservação de arquivos locais.
