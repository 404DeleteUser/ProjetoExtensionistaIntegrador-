"""Testes da anonimização (sem rede e sem banco): python -m unittest discover -s ingestao"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from carregar_bronze import anonimizar, carregar_env, ler_arquivo

CABECALHO = ["DRE", "Municipio", "Lotacao", "TipoLotacao", "Nome",
             "Funcao", "TipoVinculo", "Matrícula", "Vínculo", "Situação"]
LINHA = ["Cuiabá", "Cuiabá", "EE Exemplo", "Escola", "Fulano de Tal",
         "Professor", "Efetivo", "123456", "1", "Concluído"]
CHAVE = b"chave-de-teste"


def corpo(*linhas):
    return {"ok": True, "cabecalho": CABECALHO, "linhas": list(linhas)}


class TestAnonimizar(unittest.TestCase):
    def test_remove_nome_matricula_e_vinculo(self):
        registros, _ = anonimizar(corpo(LINHA), CHAVE)
        texto = repr(registros)
        self.assertNotIn("Fulano", texto)
        self.assertNotIn("123456", texto)
        self.assertEqual(registros[0][1:], ("Cuiabá", "Cuiabá", "EE Exemplo", "Escola",
                                            "Professor", "Efetivo", "Concluído"))

    def test_codigo_estavel_e_dependente_da_chave(self):
        (a,), _ = anonimizar(corpo(LINHA), CHAVE)
        (b,), _ = anonimizar(corpo(LINHA), CHAVE)
        (c,), _ = anonimizar(corpo(LINHA), b"outra-chave")
        self.assertEqual(a[0], b[0])
        self.assertNotEqual(a[0], c[0])
        self.assertEqual(len(a[0]), 64)

    def test_vinculos_diferentes_geram_codigos_diferentes(self):
        outro_vinculo = LINHA[:8] + ["2", "Concluído"]
        registros, _ = anonimizar(corpo(LINHA, outro_vinculo), CHAVE)
        self.assertEqual(len(registros), 2)

    def test_conta_sem_matricula_e_duplicadas(self):
        sem_matricula = LINHA[:7] + ["", "1", "Concluído"]
        registros, contagens = anonimizar(corpo(LINHA, LINHA, sem_matricula), CHAVE)
        self.assertEqual(len(registros), 1)
        self.assertEqual(contagens, {"lidas": 3, "sem_matricula": 1, "duplicadas": 1})

    def test_cabecalho_sem_acento_e_caixa_diferente(self):
        cabecalho = [nome.upper().replace("í", "i").replace("ã", "a") for nome in CABECALHO]
        registros, _ = anonimizar({"ok": True, "cabecalho": cabecalho, "linhas": [LINHA]}, CHAVE)
        self.assertEqual(len(registros), 1)

    def test_falha_se_faltar_coluna(self):
        with self.assertRaisesRegex(RuntimeError, "Situação"):
            anonimizar({"ok": True, "cabecalho": CABECALHO[:-1], "linhas": []}, CHAVE)

    def test_falha_se_api_recusar(self):
        with self.assertRaises(RuntimeError):
            anonimizar({"ok": False, "erro": "token inválido"}, CHAVE)


class TestLerArquivo(unittest.TestCase):
    def ler(self, separador, codificacao):
        conteudo = "\n".join(separador.join(linha) for linha in (CABECALHO, LINHA))
        with tempfile.NamedTemporaryFile("wb", suffix=".csv", delete=False) as arquivo:
            arquivo.write(conteudo.encode(codificacao))
        try:
            return ler_arquivo(arquivo.name)
        finally:
            os.remove(arquivo.name)

    def test_google_sheets_virgula_utf8(self):
        self.assertEqual(self.ler(",", "utf-8"), corpo(LINHA))

    def test_excel_ponto_e_virgula_utf8_com_bom(self):
        self.assertEqual(self.ler(";", "utf-8-sig"), corpo(LINHA))

    def test_excel_ponto_e_virgula_cp1252(self):
        self.assertEqual(self.ler(";", "cp1252"), corpo(LINHA))


class TestCarregarEnv(unittest.TestCase):
    def test_le_env_sem_sobrescrever_o_terminal(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta, ".env")
            caminho.write_text('# comentário\nPEI_A="do arquivo"\nPEI_B=C:\\x\\y.csv\n', encoding="utf-8")
            with mock.patch.dict(os.environ, {"PEI_B": "do terminal"}):
                carregar_env(caminho)
                self.assertEqual(os.environ["PEI_A"], "do arquivo")
                self.assertEqual(os.environ["PEI_B"], "do terminal")
            self.assertNotIn("PEI_A", os.environ)

    def test_sem_env_nao_faz_nada(self):
        carregar_env(Path(tempfile.gettempdir(), "nao-existe", ".env"))


if __name__ == "__main__":
    unittest.main()
