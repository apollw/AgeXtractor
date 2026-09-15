import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agextractor.interfaces.server import main


class InterfaceServidor(unittest.TestCase):
    def test_emite_somente_json_e_nao_persiste_resultado(self):
        esperado = {"quantidade_jogadores": 2, "jogadores": []}
        with tempfile.TemporaryDirectory() as pasta, \
                patch("agextractor.interfaces.server.executar_extracao", return_value=esperado) as executar, \
                patch("sys.stdout", new_callable=io.StringIO) as saida:
            main(["--entrada", pasta, "--jogadores", "2"])

            self.assertEqual(json.loads(saida.getvalue()), esperado)
            self.assertEqual(executar.call_args.args[0], 2)
            self.assertEqual(executar.call_args.args[1]["placar"], Path(pasta) / "placar.jpeg")
            self.assertFalse(Path(executar.call_args.args[2]).exists())


if __name__ == "__main__":
    unittest.main()
