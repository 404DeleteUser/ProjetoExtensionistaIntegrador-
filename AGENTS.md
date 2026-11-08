# AGENTS.md — Projeto Extensionista Integrador (PEI)

Arquivo central de instruções para qualquer agente (Claude, Codex, etc.). Leia este arquivo inteiro antes de qualquer tarefa. Outros arquivos de agente (ex.: `CLAUDE.md`) apenas apontam para cá; não duplique regras neles.

## 1. Projeto

Projeto de Inteligência de Negócios: monitoramento **agregado** do Recadastramento de servidores da SEDUC-MT.

- Fonte de contexto: o DataHub (`https://github.com/404DeleteUser/SEDUC---DataHub`, página "Recadastramento"). **Somente leitura**: consulte para entender dados e regras; nunca altere, faça commit ou push nele.
- Commits deste projeto vão apenas para este repositório.

## 2. Regras obrigatórias de engenharia

Valem durante toda a tarefa, não só na análise inicial. Se várias se aplicarem, siga todas.

- [`regras/ask-refactoring.md`](regras/ask-refactoring.md): faça só o pedido; peça autorização antes de refatorar fora do escopo.
- [`regras/isolation.md`](regras/isolation.md): liste arquivos e motivos antes de editar, mapeie dependências, preserve contratos e verifique regressões.
- [`regras/suggest-code.md`](regras/suggest-code.md): se houver abordagem materialmente melhor, pause e peça decisão (A/B) antes de implementar.
- **Simplicidade:** faça da forma mais simples e eficiente, com o mínimo de código.
- **Só informação durável:** ao documentar, elimine o que perde validade com o tempo (datas pontuais, status e prazos temporários) e mantenha o genérico, útil ao projeto a longo prazo.
- **Explicação:** explique passo a passo e o porquê de cada etapa (o projeto é defendido em banca).
- Nunca afirme que algo foi testado ou verificado sem ter sido. Silêncio não é aprovação.

## 3. LGPD (inegociável)

- Anonimizar já na carga da Bronze: remover nome, CPF e matrícula; substituir o identificador por um código sem relação com a pessoa.
- Manter apenas: DRE, município, tipo de lotação, vínculo, função e situação.
- O repositório é público: só scripts e dados agregados ou de exemplo. **Nunca** versionar a base real nem dados individuais.

## 4. Decisões aprovadas

Não contrarie sem aprovação do usuário.

- Escopo: só o agregado — mapa de MT por município (% concluído, aguardando validação, em andamento, não iniciado), situação por DRE, tipo de vínculo, tipo de lotação e funções. Nada individual.
- Arquitetura Medallion em PostgreSQL, com schemas `bronze`, `silver` e `gold`.
- ETL Bronze → Silver com Power Query, incluindo qualidade de dados; nomes de município padronizados para bater com o mapa.
- Star Schema na Gold: `fato_recadastramento` (1 linha por servidor anonimizado por data de leitura) + `dim_municipio`, `dim_dre`, `dim_lotacao`, `dim_vinculo`, `dim_funcao`, `dim_situacao`, `dim_tempo`.
- Histórico: snapshot diário da base, alimentando `dim_tempo`, a inteligência de tempo em DAX e o painel estratégico.
- Power BI com três painéis: operacional (situação por escola/lotação), gerencial (mapa + DRE/município) e estratégico (% geral, evolução diária e projeção da meta).
- Mineração de dados (KDD/CRISP-DM): clusterizar municípios pelo perfil de adesão ou classificar quem tende a ficar "não iniciado".

## 5. Entregáveis exigidos pelo PEI

Arquitetura Medallion; inventário das fontes com amostras; scripts SQL de extração (SELECT, JOIN, GROUP BY, CTEs, funções de janela, views); requisitos analíticos e catálogo de indicadores (pergunta → indicador → fórmula → fonte); modelo conceitual e lógico em Star Schema (fato, dimensões, granularidade, dimensão tempo, chaves substitutas); ETL em Power Query; mineração de dados com relatório; modelo semântico no Power BI com drill-down/OLAP e medidas DAX de todos os indicadores; três painéis; repositório git público.

## 6. Fonte de verdade

1. Código e scripts atuais deste repositório.
2. Este arquivo.
3. Arquivos em `regras/`.
4. Demais documentos.

Se algo divergir, sinalize ao usuário antes de agir.
