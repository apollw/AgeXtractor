from contextlib import redirect_stdout
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from agextractor.caminhos import PASTA_ENTRADA, RAIZ_PROJETO, RESULTADO_PADRAO
from agextractor.interfaces import cli


class OrganizacaoDoProjeto(unittest.TestCase):
    def test_atalho_terminal_funciona_fora_da_raiz(self):
        with tempfile.TemporaryDirectory() as pasta:
            processo = subprocess.run(
                [sys.executable, str(RAIZ_PROJETO / "main.py"), "--help"],
                cwd=pasta, capture_output=True, timeout=30,
            )
        self.assertEqual(processo.returncode, 0, processo.stderr)
        self.assertIn(b"--entrada", processo.stdout)
        self.assertIn(b"--saida", processo.stdout)

    def test_imports_e_caminhos_independem_da_pasta_atual(self):
        codigo = (
            "import main, interface; "
            "from agextractor.caminhos import PASTA_ENTRADA, RESULTADO_PADRAO; "
            "print(PASTA_ENTRADA); print(RESULTADO_PADRAO)"
        )
        with tempfile.TemporaryDirectory() as pasta:
            processo = subprocess.run(
                [sys.executable, "-c", codigo], cwd=pasta,
                env={**os.environ, "PYTHONPATH": str(RAIZ_PROJETO), "PYTHONIOENCODING": "utf-8"},
                capture_output=True, text=True, encoding="utf-8", timeout=30,
            )
        self.assertEqual(processo.returncode, 0, processo.stderr)
        self.assertEqual(processo.stdout.splitlines(), [str(PASTA_ENTRADA), str(RESULTADO_PADRAO)])

    def test_cli_encaminha_os_caminhos_e_a_quantidade(self):
        with tempfile.TemporaryDirectory() as pasta:
            entrada = Path(pasta) / "prints"
            saida = Path(pasta) / "partida.json"
            with patch.object(cli, "executar_extracao", return_value={"ok": True}) as executar:
                with redirect_stdout(io.StringIO()) as exibido:
                    cli.main(["--entrada", str(entrada), "--saida", str(saida), "--jogadores", "4"])
            quantidade, caminhos, destino = executar.call_args.args
            self.assertEqual(quantidade, 4)
            self.assertEqual(destino, saida)
            self.assertEqual(caminhos["militar"], entrada / "militar.jpeg")
            self.assertEqual(len(caminhos), 5)
            self.assertIn('"ok": true', exibido.getvalue())


if __name__ == "__main__":
    unittest.main()
