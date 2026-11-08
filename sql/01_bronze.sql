-- Camada Bronze: dados da planilha do Recadastramento já anonimizados.
-- Rode uma vez no SQL Editor do Supabase (ou psql). Pode ser rodado de novo sem perder dados.

CREATE SCHEMA IF NOT EXISTS bronze;

-- Leitura de cada dia, como veio da planilha (sem nome, matrícula e vínculo).
-- Guarda só os últimos 7 dias: serve para auditoria e reprocessamento.
CREATE TABLE IF NOT EXISTS bronze.carga (
    data_carga   date     NOT NULL,
    id_servidor  char(64) NOT NULL,  -- HMAC-SHA256(matrícula|vínculo), em hexadecimal
    dre          text     NOT NULL,
    municipio    text     NOT NULL,
    lotacao      text     NOT NULL,
    tipo_lotacao text     NOT NULL,
    funcao       text     NOT NULL,
    tipo_vinculo text     NOT NULL,
    situacao     text     NOT NULL,
    PRIMARY KEY (data_carga, id_servidor)
);

-- Histórico em SCD Tipo 2: uma linha por versão de cada servidor.
-- Só grava quando algo muda; valido_ate NULL = versão vigente.
CREATE TABLE IF NOT EXISTS bronze.historico (
    id_servidor  char(64) NOT NULL,
    dre          text     NOT NULL,
    municipio    text     NOT NULL,
    lotacao      text     NOT NULL,
    tipo_lotacao text     NOT NULL,
    funcao       text     NOT NULL,
    tipo_vinculo text     NOT NULL,
    situacao     text     NOT NULL,
    valido_de    date     NOT NULL,
    valido_ate   date,
    PRIMARY KEY (id_servidor, valido_de),
    CHECK (valido_ate IS NULL OR valido_ate >= valido_de)
);

-- Garante no máximo uma versão vigente por servidor.
CREATE UNIQUE INDEX IF NOT EXISTS historico_vigente
    ON bronze.historico (id_servidor) WHERE valido_ate IS NULL;

-- Aplica a carga do dia ao histórico:
--   1. fecha a versão vigente de quem mudou algum atributo ou saiu da planilha;
--   2. abre versão para quem ficou sem versão vigente (novo ou acabou de mudar).
CREATE OR REPLACE FUNCTION bronze.atualizar_historico(p_data date)
RETURNS TABLE (fechadas integer, abertas integer)
LANGUAGE plpgsql AS $$
DECLARE
    v_fechadas integer;
    v_abertas  integer;
BEGIN
    UPDATE bronze.historico h
       SET valido_ate = p_data - 1
     WHERE h.valido_ate IS NULL
       AND NOT EXISTS (
           SELECT 1
             FROM bronze.carga c
            WHERE c.data_carga = p_data
              AND c.id_servidor = h.id_servidor
              AND (c.dre, c.municipio, c.lotacao, c.tipo_lotacao, c.funcao, c.tipo_vinculo, c.situacao)
                = (h.dre, h.municipio, h.lotacao, h.tipo_lotacao, h.funcao, h.tipo_vinculo, h.situacao));
    GET DIAGNOSTICS v_fechadas = ROW_COUNT;

    INSERT INTO bronze.historico
           (id_servidor, dre, municipio, lotacao, tipo_lotacao, funcao, tipo_vinculo, situacao, valido_de)
    SELECT c.id_servidor, c.dre, c.municipio, c.lotacao, c.tipo_lotacao, c.funcao, c.tipo_vinculo, c.situacao, p_data
      FROM bronze.carga c
     WHERE c.data_carga = p_data
       AND NOT EXISTS (
           SELECT 1 FROM bronze.historico h
            WHERE h.id_servidor = c.id_servidor AND h.valido_ate IS NULL);
    GET DIAGNOSTICS v_abertas = ROW_COUNT;

    RETURN QUERY SELECT v_fechadas, v_abertas;
END;
$$;

-- Usuário somente leitura para o código local e o Power BI.
-- Troque <SENHA> só na hora de rodar; nunca grave a senha neste arquivo.
-- CREATE ROLE leitor_pei LOGIN PASSWORD '<SENHA>';
-- GRANT USAGE ON SCHEMA bronze TO leitor_pei;
-- GRANT SELECT ON ALL TABLES IN SCHEMA bronze TO leitor_pei;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA bronze GRANT SELECT ON TABLES TO leitor_pei;
