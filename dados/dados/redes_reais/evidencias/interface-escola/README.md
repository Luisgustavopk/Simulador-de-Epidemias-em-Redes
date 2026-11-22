# Conferência da escola na interface

O percurso foi executado em 21/11/2026 no Chrome, com a interface Vite e a API Python reais, em processos próprios e perfil de navegador temporário. O teste não substituiu respostas HTTP nem gerou uma rede sintética no lugar dos arquivos. Não executou a simulação epidemiológica.

Foram selecionados `contatos.csv` e `individuos.csv` na Tela 01, mantendo vírgula como separador. O botão **Carregar arquivos** importou a rede; depois, **Confirmar rede** a disponibilizou para configuração.

| Verificação | Resultado |
| --- | --- |
| População / contatos completos | 67 / 1.325 |
| Grau médio / máximo | 39,55223880597015 / 54 |
| Componentes / indivíduos sem contatos | 1 / 0 |
| Inspeção do ID 25 | Grau 54, suscetível e não isolado |
| Renderização | Canvas preenchido nas vistas 3D e Mapa |
| Dados de contatos | Paginação apresenta total de 1.325 |
| Confirmação | Rede confirmada na página e na API |
| Respostas da API observadas | Todas com HTTP 200 |
| Exceções JavaScript observadas | Nenhuma |

A prévia contém os 67 indivíduos e **1.200 das 1.325 arestas**, conforme o limite do adaptador HTTP. A página identifica esse recorte; as medidas usam todos os contatos. As posições no mapa são ilustrativas. Não foi necessário alterar os arquivos de entrada ou a aplicação.

As capturas mostram [3D](rede-escolar-3d.png), [Mapa](rede-escolar-mapa.png), [medidas e inspeção](rede-escolar-medidas.png) e [confirmação](rede-escolar-confirmacao.png). A [página completa](rede-escolar-pagina-completa.png) conserva a navegação e a tabela como evidência adicional. O [registro JSON](verificacao.json) contém ambiente, hashes, requisições, contagens e enquadramentos.

Para repetir a partir da raiz, com as dependências existentes do frontend, Chrome e `.venv` disponíveis:

```bash
node scripts/verificar_base_escola_interface.mjs
```

O [script](../../../../../scripts/verificar_base_escola_interface.mjs) abre os arquivos pelo controle de upload do navegador e aciona os botões da interface. As consultas GET posteriores conferem os valores; a importação e a confirmação são feitas pelos controles. Ao concluir, encerra apenas os processos que iniciou. A conferência cobre a vista desktop registrada, sem representar um teste de desempenho, de dispositivos móveis ou de todos os navegadores.
