"""Mineração de dados (CRISP-DM): agrupa os municípios pelo perfil de adesão ao recadastramento.

Lê só agregados por município da Bronze (nenhuma linha individual sai do banco), padroniza as
variáveis, escolhe o número de grupos pela silhueta e aplica K-means. Imprime só agregados.
Uso, na raiz do repositório: python -m mineracao.clusterizar_municipios [--gravar]
Com --gravar, substitui o conteúdo de bronze.municipio_perfil (sql/04_perfil_municipio.sql).
"""
import os
import sys

import numpy as np
import psycopg
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from ingestao.carregar_bronze import ARQUIVO_ENV, carregar_env

SEMENTE = 42
GRUPOS_TESTADOS = range(2, 9)

# Situação vigente de cada servidor (valido_ate IS NULL), somada por município.
SQL = """
SELECT municipio,
       count(*)                                                                  AS servidores,
       avg((lower(situacao) = 'não iniciado')::int)                              AS pct_nao_iniciado,
       avg((lower(situacao) = 'em andamento')::int)                              AS pct_em_andamento,
       avg((lower(situacao) = 'aguardando validação')::int)                      AS pct_aguardando,
       avg((lower(situacao) = 'concluído')::int)                                 AS pct_concluido,
       avg((lower(tipo_vinculo) LIKE 'tempor%')::int)                            AS pct_temporario,
       avg((lower(tipo_lotacao) LIKE '%campo%' OR lower(tipo_lotacao) LIKE '%ind%gena%')::int)
                                                                                 AS pct_campo_indigena
  FROM bronze.historico
 WHERE valido_ate IS NULL
 GROUP BY municipio
"""
VARIAVEIS = ["pct_nao_iniciado", "pct_em_andamento", "pct_aguardando", "pct_concluido",
             "pct_temporario", "pct_campo_indigena", "log_servidores"]
# Nome do perfil = a variável em que o grupo mais se destaca (maior média padronizada).
NOMES = {
    "pct_nao_iniciado": "Parados", "pct_em_andamento": "Em andamento",
    "pct_aguardando": "Travados na validação", "pct_concluido": "Avançados",
    "pct_temporario": "Muitos temporários", "pct_campo_indigena": "Campo e indígena",
    "log_servidores": "Polos regionais",
}


def nomear(x_padronizado, rotulos, k):
    nomes = []
    for g in range(k):
        nome = NOMES[VARIAVEIS[int(x_padronizado[rotulos == g].mean(axis=0).argmax())]]
        nomes.append(nome if nome not in nomes else f"{nome} {nomes.count(nome) + 1}")
    return nomes


def main():
    carregar_env(ARQUIVO_ENV)
    with psycopg.connect(os.environ["DATABASE_URL"]) as con:
        con.read_only = True  # a mineração nunca grava
        linhas = con.execute(SQL).fetchall()

    municipios = [l[0] for l in linhas]
    servidores = np.array([l[1] for l in linhas], dtype=float)
    # log do tamanho: Cuiabá (milhares) não pode dominar municípios com dezenas de servidores
    x = np.column_stack([np.array([l[2:] for l in linhas], dtype=float), np.log(servidores)])
    x_padronizado = StandardScaler().fit_transform(x)

    print(f"Municípios: {len(municipios)} | servidores: {int(servidores.sum())}")
    print("\nSilhueta por número de grupos (quanto maior, mais separados):")
    melhor_k, melhor_s = None, -1
    for k in GRUPOS_TESTADOS:
        rotulos = KMeans(k, n_init=10, random_state=SEMENTE).fit_predict(x_padronizado)
        s = silhouette_score(x_padronizado, rotulos)
        print(f"  k={k}: {s:.3f}")
        if s > melhor_s:
            melhor_k, melhor_s = k, s

    rotulos = KMeans(melhor_k, n_init=10, random_state=SEMENTE).fit_predict(x_padronizado)
    nomes = nomear(x_padronizado, rotulos, melhor_k)
    print(f"\nEscolhido k={melhor_k} (silhueta {melhor_s:.3f}). Perfil médio de cada grupo:")
    print("perfil                  munic  servid  " + "  ".join(v[:12].rjust(12) for v in VARIAVEIS[:-1]))
    for g in range(melhor_k):
        m = rotulos == g
        medias = x[m, :-1].mean(axis=0)
        print(f"{nomes[g]:<22}  {m.sum():>5}  {int(servidores[m].sum()):>6}  "
              + "  ".join(f"{v:>12.1%}" for v in medias))
    print("\nMunicípios por perfil:")
    for g in range(melhor_k):
        print(f"  {nomes[g]}: " + ", ".join(sorted(np.array(municipios)[rotulos == g])))

    if "--gravar" in sys.argv:  # grava o perfil de cada município para o Power BI
        with psycopg.connect(os.environ["DATABASE_URL"]) as con:
            con.execute("DELETE FROM bronze.municipio_perfil")
            con.cursor().executemany("INSERT INTO bronze.municipio_perfil VALUES (%s, %s)",
                                     [(m, nomes[g]) for m, g in zip(municipios, rotulos)])
        print(f"\nGravados {len(municipios)} municípios em bronze.municipio_perfil.")


if __name__ == "__main__":
    main()
