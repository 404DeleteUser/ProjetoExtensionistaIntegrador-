# Requisitos analíticos

## Problema de negócio

A SEDUC-MT precisa recadastrar todos os servidores da rede estadual. Sem uma visão consolidada, não se sabe **onde** o recadastramento está atrasado, **por quê** e **se a meta será cumprida no prazo**. O projeto entrega um painel de acompanhamento agregado, atualizado todos os dias.

**Meta oficial:** 90% dos servidores com recadastramento concluído até 31/12/2026.

## Usuários

| Usuário | Decisão que o painel apoia | Painel |
|---|---|---|
| Equipe do recadastramento (SEDUC) | Quais escolas e lotações cobrar hoje | Operacional |
| Gestores das DREs | Quais municípios da sua DRE precisam de ação | Gerencial e Operacional |
| Gestão da SEDUC | A meta será cumprida? Onde concentrar esforço? | Estratégico e Perfis de adesão |

As perguntas de negócio e os indicadores estão em [`catalogo-indicadores.md`](catalogo-indicadores.md).

## Requisitos funcionais

| Nº | Requisito |
|---|---|
| RF01 | Carregar a planilha do recadastramento uma vez por dia, de forma automática |
| RF02 | Guardar o histórico de situação de cada servidor sem perder dias (SCD Tipo 2) |
| RF03 | Mostrar o total de servidores e a quantidade e o % de cada situação |
| RF04 | Mostrar o % concluído por município num mapa de MT, em faixas de 20 pontos |
| RF05 | Mostrar a situação por DRE, ordenada da mais atrasada para a mais adiantada |
| RF06 | Mostrar a distribuição por tipo de vínculo, tipo de lotação e função |
| RF07 | Filtrar por DRE, município, tipo de lotação, tipo de vínculo, função e situação, com um botão para limpar os filtros |
| RF08 | Navegar de DRE para município e de município para lotação (drill-down) |
| RF09 | Mostrar a evolução diária, a média móvel de 7 dias e a projeção da data de conclusão |
| RF10 | Comparar o andamento com a meta oficial: % atingido, faltantes, dias restantes, ritmo necessário e situação |
| RF11 | Agrupar os municípios por perfil de adesão (mineração de dados) e mostrar os perfis no mapa |
| RF12 | Registrar a qualidade dos dados: o que cada regra de limpeza corrigiu |

## Requisitos não funcionais

| Nº | Categoria | Requisito |
|---|---|---|
| RNF01 | Privacidade (LGPD) | Nome, matrícula e número do vínculo nunca chegam ao banco. O servidor é identificado por HMAC-SHA256 com chave secreta |
| RNF02 | Privacidade (LGPD) | Os painéis mostram só contagens e percentuais, nunca linhas individuais |
| RNF03 | Privacidade (LGPD) | O repositório é público e só contém código e dados fictícios ou públicos. Os logs do GitHub Actions mostram só contagens |
| RNF04 | Segurança | Segredos (URL e token da API, chave de anonimização, senha do banco) ficam só nos Secrets do GitHub e no `.env` local, fora do git |
| RNF05 | Segurança | O Power BI lê o banco com um usuário somente leitura (`leitor_pei`), com RLS e política de leitura |
| RNF06 | Confiabilidade | A carga é idempotente (só uma por dia) e grava tudo numa única transação. Um dia sem carga não abre buraco no histórico |
| RNF07 | Confiabilidade | Uma carga vazia nunca é gravada (fecharia o histórico de todos os servidores) |
| RNF08 | Manutenibilidade | O Power BI é versionado como texto (`.pbip`: TMDL e PBIR) |
| RNF09 | Desempenho | A Bronze guarda só 7 dias de carga bruta. O histórico guarda só mudanças |
| RNF10 | Custo | Só serviços gratuitos: Supabase (plano free), GitHub Actions e Power BI Desktop |
| RNF11 | Usabilidade | Situações com ordem e cores fixas em todos os visuais. Cartões sem histórico mostram "Sem histórico" em vez de vazio |

## Casos de uso do ETL

### UC01 – Carga diária (Fonte → Bronze)

- **Ator:** GitHub Actions (agendado às 23h de Cuiabá) ou execução manual.
- **Fluxo principal:**
  1. Lê a planilha pela API (ou por um CSV local).
  2. Confere se o cabeçalho tem todas as colunas esperadas.
  3. Para cada linha: descarta o nome, calcula `id_servidor = HMAC(chave, matrícula|vínculo)` e mantém os 7 atributos.
  4. Grava em `bronze.carga` e atualiza `bronze.historico` (fecha as versões que mudaram e abre as novas).
  5. Apaga as cargas com mais de 7 dias.
  6. Imprime só as contagens (lidas, sem matrícula, repetidas, versões fechadas e abertas).
- **Exceções:**
  - o dia já foi carregado → não faz nada;
  - o cabeçalho mudou → para com erro, citando as colunas que faltam;
  - nenhuma linha válida → para sem gravar;
  - qualquer erro no banco → a transação é desfeita.

### UC02 – Bronze → Silver (Power Query)

- **Ator:** atualização do Power BI.
- **Fluxo:**
  1. Lê `bronze.vw_snapshot_diario` (uma linha por servidor por dia).
  2. Padroniza os textos, troca vazios por "Não informado" e converte as situações para os nomes oficiais.
  3. Corrige os nomes de município pelo de-para e casa com o código IBGE.
  4. Gera as tabelas de qualidade e de municípios sem código.
- **Detalhes:** [`etl.md`](etl.md).

### UC03 – Silver → Gold (modelo do Power BI)

- **Ator:** atualização do Power BI.
- **Fluxo:**
  1. Gera as dimensões com chaves substitutas.
  2. Gera o fato com as chaves das dimensões.
  3. Os relacionamentos e as medidas DAX respondem ao catálogo de indicadores.
- **Detalhes:** [`modelo-dimensional.md`](modelo-dimensional.md).

### UC04 – Perfis de adesão (mineração)

- **Ator:** analista, sob demanda.
- **Fluxo:**
  1. Executa `python -m mineracao.clusterizar_municipios --gravar`.
  2. O script agrega por município no banco, agrupa os municípios com K-means e grava `bronze.municipio_perfil`.
  3. A próxima atualização do Power BI mostra os novos perfis.
- **Detalhes:** [`mineracao.md`](mineracao.md).
