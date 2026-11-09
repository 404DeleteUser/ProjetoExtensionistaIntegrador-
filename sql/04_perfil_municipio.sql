-- Perfis de adesão: grupo de cada município gerado pela mineração (mineracao/clusterizar_municipios.py).
-- Só nome do município e perfil: nenhum dado pessoal. O script substitui o conteúdo a cada execução.
-- Rode depois de 01_bronze.sql. Pode ser rodado de novo.

CREATE TABLE IF NOT EXISTS bronze.municipio_perfil (
    municipio text PRIMARY KEY,  -- nome como está na Bronze; a Silver casa com o código IBGE
    perfil    text NOT NULL
);

GRANT SELECT ON bronze.municipio_perfil TO leitor_pei;

-- O Supabase liga RLS nas tabelas novas: sem política, o leitor_pei veria a tabela vazia.
ALTER TABLE bronze.municipio_perfil ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS leitura_leitor_pei ON bronze.municipio_perfil;
CREATE POLICY leitura_leitor_pei ON bronze.municipio_perfil FOR SELECT TO leitor_pei USING (true);
