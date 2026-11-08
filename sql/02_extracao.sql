-- Views de extração da Bronze: SELECT, JOIN, GROUP BY, CTEs, funções de janela e views.
-- Rode depois de 01_bronze.sql. Pode ser rodado de novo (CREATE OR REPLACE).
-- Situações comparadas em minúsculas: a padronização completa é feita na Silver (Power Query).

-- 1. Snapshot diário: abre o histórico SCD2 em 1 linha por servidor por dia.
--    Fonte do fato_recadastramento (granularidade: servidor anonimizado × dia).
CREATE OR REPLACE VIEW bronze.vw_snapshot_diario AS
WITH periodo AS (
    SELECT (SELECT min(valido_de) FROM bronze.historico) AS inicio,
           (SELECT max(data_carga) FROM bronze.carga)    AS fim
),
calendario AS (
    SELECT dia::date AS data
      FROM periodo, generate_series(periodo.inicio, periodo.fim, interval '1 day') AS dia
)
SELECT c.data, h.id_servidor, h.dre, h.municipio, h.lotacao, h.tipo_lotacao,
       h.funcao, h.tipo_vinculo, h.situacao
  FROM calendario c
  JOIN bronze.historico h
    ON c.data >= h.valido_de
   AND c.data <= coalesce(h.valido_ate, c.data);

-- 2. Situação atual por DRE e município, com % concluído e ranking dentro da DRE.
--    Fonte do mapa e do painel gerencial.
CREATE OR REPLACE VIEW bronze.vw_resumo_municipio AS
WITH vigente AS (
    SELECT dre, municipio, lower(situacao) AS situacao
      FROM bronze.historico
     WHERE valido_ate IS NULL
),
contagem AS (
    SELECT dre, municipio,
           count(*)                                                   AS total,
           count(*) FILTER (WHERE situacao = 'concluído')             AS concluido,
           count(*) FILTER (WHERE situacao = 'aguardando validação')  AS aguardando_validacao,
           count(*) FILTER (WHERE situacao = 'em andamento')          AS em_andamento,
           count(*) FILTER (WHERE situacao = 'não iniciado')          AS nao_iniciado
      FROM vigente
     GROUP BY dre, municipio
)
SELECT dre, municipio, total, concluido, aguardando_validacao, em_andamento, nao_iniciado,
       total - concluido - aguardando_validacao - em_andamento - nao_iniciado AS outras_situacoes,
       round(100.0 * concluido / total, 1)                                    AS pct_concluido,
       RANK() OVER (PARTITION BY dre ORDER BY concluido::numeric / total DESC) AS ranking_na_dre
  FROM contagem;

-- 3. Evolução diária: % concluído, novos concluídos no dia (LAG), média móvel de 7 dias
--    e dias estimados para concluir todos no ritmo atual. Fonte do painel estratégico.
CREATE OR REPLACE VIEW bronze.vw_evolucao_diaria AS
WITH diario AS (
    SELECT data,
           count(*)                                              AS total,
           count(*) FILTER (WHERE lower(situacao) = 'concluído') AS concluido
      FROM bronze.vw_snapshot_diario
     GROUP BY data
),
variacao AS (
    SELECT *, concluido - LAG(concluido) OVER (ORDER BY data) AS novos_concluidos
      FROM diario
),
ritmo AS (
    SELECT *, avg(novos_concluidos) OVER (ORDER BY data ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS media_7d
      FROM variacao
)
SELECT data, total, concluido,
       round(100.0 * concluido / total, 1) AS pct_concluido,
       novos_concluidos,
       round(media_7d, 1)                  AS media_movel_7d,
       CASE WHEN media_7d > 0 THEN ceil((total - concluido) / media_7d)::integer END AS dias_para_concluir
  FROM ritmo;
