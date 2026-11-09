-- Consultas exploratórias sobre a Bronze: volume, período, nulos e inconsistências.
-- Só leitura: devolvem contagens agregadas (nenhuma linha individual).

-- 1. Volume e período: cargas guardadas e versões do histórico.
SELECT min(data_carga) AS primeira_carga, max(data_carga) AS ultima_carga,
       count(DISTINCT data_carga) AS dias_carregados, count(*) AS linhas_em_carga
  FROM bronze.carga;

SELECT count(*)                                 AS versoes,
       count(*) FILTER (WHERE valido_ate IS NULL) AS servidores_vigentes,
       count(DISTINCT id_servidor)              AS servidores_ja_vistos
  FROM bronze.historico;

-- 2. Valores distintos e vazios por coluna (situação vigente).
SELECT 'dre' AS coluna, count(DISTINCT dre) AS distintos, count(*) FILTER (WHERE coalesce(btrim(dre), '') = '') AS vazios FROM bronze.historico WHERE valido_ate IS NULL
UNION ALL SELECT 'municipio', count(DISTINCT municipio), count(*) FILTER (WHERE coalesce(btrim(municipio), '') = '') FROM bronze.historico WHERE valido_ate IS NULL
UNION ALL SELECT 'lotacao', count(DISTINCT lotacao), count(*) FILTER (WHERE coalesce(btrim(lotacao), '') = '') FROM bronze.historico WHERE valido_ate IS NULL
UNION ALL SELECT 'tipo_lotacao', count(DISTINCT tipo_lotacao), count(*) FILTER (WHERE coalesce(btrim(tipo_lotacao), '') = '') FROM bronze.historico WHERE valido_ate IS NULL
UNION ALL SELECT 'funcao', count(DISTINCT funcao), count(*) FILTER (WHERE coalesce(btrim(funcao), '') = '') FROM bronze.historico WHERE valido_ate IS NULL
UNION ALL SELECT 'tipo_vinculo', count(DISTINCT tipo_vinculo), count(*) FILTER (WHERE coalesce(btrim(tipo_vinculo), '') = '') FROM bronze.historico WHERE valido_ate IS NULL
UNION ALL SELECT 'situacao', count(DISTINCT situacao), count(*) FILTER (WHERE coalesce(btrim(situacao), '') = '') FROM bronze.historico WHERE valido_ate IS NULL;

-- 3. Situações como chegam (detecta grafias fora do padrão).
SELECT situacao, count(*) AS servidores
  FROM bronze.historico
 WHERE valido_ate IS NULL
 GROUP BY situacao
 ORDER BY servidores DESC;

-- 4. Municípios sem correspondência no IBGE, comparando sem caixa, acento e apóstrofo (como a Silver).
WITH chave AS (
    SELECT 'ÁÀÂÃÉÊÍÓÔÕÚÜÇ' AS com_acento, 'AAAAEEIOOOUUC' AS sem_acento
)
SELECT h.municipio, count(*) AS servidores
  FROM bronze.historico h
  CROSS JOIN chave c
  LEFT JOIN bronze.municipio_ibge i
    ON replace(translate(upper(i.municipio), c.com_acento, c.sem_acento), '''', '')
     = replace(translate(upper(h.municipio), c.com_acento, c.sem_acento), '''', '')
 WHERE h.valido_ate IS NULL AND i.codigo_ibge IS NULL
 GROUP BY h.municipio
 ORDER BY servidores DESC;

-- 5. Municípios atendidos por mais de uma DRE (motivo de a DRE ser atributo da lotação).
SELECT municipio, count(DISTINCT dre) AS dres, string_agg(DISTINCT dre, ' | ') AS quais
  FROM bronze.historico
 WHERE valido_ate IS NULL
 GROUP BY municipio
HAVING count(DISTINCT dre) > 1
 ORDER BY municipio;

-- 6. Nomes de lotação repetidos em municípios diferentes (motivo da chave lotação + município + DRE).
SELECT lotacao, count(DISTINCT municipio) AS municipios
  FROM bronze.historico
 WHERE valido_ate IS NULL
 GROUP BY lotacao
HAVING count(DISTINCT municipio) > 1
 ORDER BY municipios DESC, lotacao;
