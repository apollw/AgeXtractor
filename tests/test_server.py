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

    def test_repassa_quatro_cantos_de_cada_tabela(self):
        categorias = ("placar", "militar", "economia", "tecnologia", "sociedade")
        regioes = {categoria: [[10, 20], [900, 20], [900, 600], [10, 600]] for categoria in categorias}
        with tempfile.TemporaryDirectory() as pasta, \
                patch("agextractor.interfaces.server.executar_extracao", return_value={}) as executar, \
                patch("sys.stdout", new_callable=io.StringIO):
            caminho = Path(pasta) / "regioes.json"
            caminho.write_text(json.dumps(regioes), encoding="utf-8")

            main(["--entrada", pasta, "--jogadores", "4", "--regioes", str(caminho)])

            self.assertEqual(executar.call_args.kwargs["regioes"], regioes)

    def test_rejeita_regioes_incompletas(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "regioes.json"
            caminho.write_text(json.dumps({"placar": [[0, 0]] * 4}), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "cinco categorias"):
                main(["--entrada", pasta, "--jogadores", "2", "--regioes", str(caminho)])


if __name__ == "__main__":
    unittest.main()
