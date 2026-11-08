"""Carga diária da Bronze: lê a API do Recadastramento, anonimiza em memória e grava no Postgres.

Variáveis de ambiente: CHAVE_ANONIMIZACAO, DATABASE_URL e a fonte:
- RECADASTRAMENTO_API_URL e RECADASTRAMENTO_API_TOKEN (carga diária pelo Actions); ou
- ARQUIVO_PLANILHA: caminho de um CSV baixado da planilha (carga manual, no computador local).
No computador local, podem vir de um .env na raiz do projeto (fora do git).
Só imprime contagens: os logs do Actions são públicos.
"""

import csv
import hashlib
import hmac
import json
import os
import sys
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

# Coluna na Bronze -> cabeçalho na planilha. Nome nunca é lido.
COLUNAS = {
    "dre": "DRE",
    "municipio": "Municipio",
    "lotacao": "Lotacao",
    "tipo_lotacao": "TipoLotacao",
    "funcao": "Funcao",
    "tipo_vinculo": "TipoVinculo",
    "situacao": "Situação",
}
MATRICULA, VINCULO = "Matrícula", "Vínculo"  # só entram no HMAC
DIAS_DE_RETENCAO = 7
TEMPO_LIMITE_S = 120
ARQUIVO_ENV = Path(__file__).resolve().parent.parent / ".env"


def carregar_env(caminho):
    """Lê linhas NOME=valor de um .env, sem sobrescrever o que já foi definido no terminal."""
    if not caminho.exists():
        return
    for linha in caminho.read_text(encoding="utf-8-sig").splitlines():
        nome, separador, valor = linha.strip().partition("=")
        if separador and not nome.startswith("#"):
            os.environ.setdefault(nome.strip(), valor.strip().strip("\"'"))


def normalizar(texto):
    """Sem acento, sem diferenciar caixa e com os espaços reduzidos (mesma regra do DataHub)."""
    sem_acento = unicodedata.normalize("NFD", str(texto)).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.split()).lower()


def limpo(valor):
    return " ".join(str("" if valor is None else valor).split())


def ler_api(url, token):
    destino = url + ("&" if "?" in url else "?") + urllib.parse.urlencode({"token": token})
    try:
        with urllib.request.urlopen(destino, timeout=TEMPO_LIMITE_S) as resposta:
            return json.load(resposta)
    except Exception as falha:
        # Sem a URL na mensagem: ela carrega o token.
        raise RuntimeError(f"Falha ao ler a API: {type(falha).__name__}") from None


def ler_arquivo(caminho):
    """Lê o CSV da planilha no mesmo formato da API. Aceita ',' ou ';' e UTF-8 ou a codificação do Excel."""
    with open(caminho, "rb") as arquivo:
        bruto = arquivo.read()
    try:
        texto = bruto.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = bruto.decode("cp1252", errors="replace")
    separador = csv.Sniffer().sniff(texto[:4096], delimiters=",;").delimiter
    cabecalho, *linhas = csv.reader(texto.splitlines(), delimiter=separador)
    return {"ok": True, "cabecalho": cabecalho, "linhas": linhas}


def anonimizar(corpo, chave):
    """Devolve (registros, contagens). Cada registro: (id_servidor, *COLUNAS)."""
    if not isinstance(corpo, dict) or corpo.get("ok") is not True:
        raise RuntimeError("A API recusou o pedido ou devolveu outro formato.")
    posicoes = {normalizar(nome): i for i, nome in enumerate(corpo.get("cabecalho", []))}
    faltando = [n for n in (*COLUNAS.values(), MATRICULA, VINCULO) if normalizar(n) not in posicoes]
    if faltando:
        raise RuntimeError(f"A planilha mudou: faltam as colunas {', '.join(faltando)}.")

    registros, sem_matricula, duplicadas = {}, 0, 0
    linhas = corpo.get("linhas", [])
    for linha in linhas:
        def valor(nome):
            i = posicoes[normalizar(nome)]
            return limpo(linha[i]) if i < len(linha) else ""

        matricula = valor(MATRICULA)
        if not matricula:
            sem_matricula += 1
            continue
        chave_pessoa = f"{matricula}|{valor(VINCULO)}".encode()
        id_servidor = hmac.new(chave, chave_pessoa, hashlib.sha256).hexdigest()
        if id_servidor in registros:
            duplicadas += 1
            continue
        registros[id_servidor] = (id_servidor, *(valor(n) for n in COLUNAS.values()))

    contagens = {"lidas": len(linhas), "sem_matricula": sem_matricula, "duplicadas": duplicadas}
    return list(registros.values()), contagens


def gravar(registros, database_url):
    """Grava a carga do dia, atualiza o SCD2 e apaga cargas antigas, numa única transação."""
    import psycopg  # só aqui: os testes de anonimização rodam sem banco

    with psycopg.connect(database_url) as con:  # commit ao sair; rollback se der erro
        data = con.execute("SELECT (now() AT TIME ZONE 'America/Cuiaba')::date").fetchone()[0]
        if con.execute("SELECT 1 FROM bronze.carga WHERE data_carga = %s LIMIT 1", (data,)).fetchone():
            return data, None
        colunas = ", ".join(("data_carga", "id_servidor", *COLUNAS))
        with con.cursor().copy(f"COPY bronze.carga ({colunas}) FROM STDIN") as copia:
            for registro in registros:
                copia.write_row((data, *registro))
        fechadas, abertas = con.execute("SELECT * FROM bronze.atualizar_historico(%s)", (data,)).fetchone()
        con.execute("DELETE FROM bronze.carga WHERE data_carga <= %s - %s", (data, DIAS_DE_RETENCAO))
        return data, {"versoes_fechadas": fechadas, "versoes_abertas": abertas}


def main():
    carregar_env(ARQUIVO_ENV)
    arquivo = os.environ.get("ARQUIVO_PLANILHA")
    nomes = ["CHAVE_ANONIMIZACAO", "DATABASE_URL"]
    if not arquivo:
        nomes += ["RECADASTRAMENTO_API_URL", "RECADASTRAMENTO_API_TOKEN"]
    faltando = [n for n in nomes if not os.environ.get(n)]
    if faltando:
        sys.exit(f"Variáveis de ambiente ausentes: {', '.join(faltando)}")
    env = os.environ

    corpo = ler_arquivo(arquivo) if arquivo else ler_api(env["RECADASTRAMENTO_API_URL"], env["RECADASTRAMENTO_API_TOKEN"])
    registros, contagens = anonimizar(corpo, env["CHAVE_ANONIMIZACAO"].encode())
    database_url = env["DATABASE_URL"]
    if not registros:
        # Gravar uma carga vazia fecharia o histórico de todos os servidores.
        sys.exit("Nenhuma linha válida na planilha; nada foi gravado.")
    data, historico = gravar(registros, database_url)
    if historico is None:
        print(f"{data}: carga do dia já existia; nada foi gravado.")
        return
    print(f"{data}: {len(registros)} gravadas | {contagens} | {historico}")


if __name__ == "__main__":
    main()
