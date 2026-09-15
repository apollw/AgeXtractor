import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agextractor.extracao import EventoProgresso
from agextractor.interfaces.server import main


class InterfaceServidor(unittest.TestCase):
    def test_emite_somente_json_e_nao_persiste_resultado(self):
        esperado = {"quantidade_jogadores": 2, "jogadores": []}
        def extrair(*args, **kwargs):
            kwargs["ao_progresso"](EventoProgresso(3, 10, "Militar | jogador 1/2 | unidades", 1.0))
            return esperado

        with tempfile.TemporaryDirectory() as pasta, \
                patch("agextractor.interfaces.server.executar_extracao", side_effect=extrair) as executar, \
                patch("sys.stdout", new_callable=io.StringIO) as saida, \
                patch("sys.stderr", new_callable=io.StringIO) as diagnostico:
            codigo = main(["--entrada", pasta, "--jogadores", "2"])

            self.assertEqual(codigo, 0)
            self.assertEqual(json.loads(saida.getvalue()), esperado)
            evento = json.loads(diagnostico.getvalue())
            self.assertEqual(evento["tipo"], "progresso")
            self.assertEqual(evento["percentual"], 30)
            self.assertIn("Militar", evento["mensagem"])
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

            codigo = main(["--entrada", pasta, "--jogadores", "4", "--regioes", str(caminho)])

            self.assertEqual(codigo, 0)
            self.assertEqual(executar.call_args.kwargs["regioes"], regioes)

    def test_rejeita_regioes_incompletas(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "regioes.json"
            caminho.write_text(json.dumps({"placar": [[0, 0]] * 4}), encoding="utf-8")

            with patch("sys.stdout", new_callable=io.StringIO) as saida, \
                    patch("sys.stderr", new_callable=io.StringIO) as diagnostico:
                codigo = main(["--entrada", pasta, "--jogadores", "2", "--regioes", str(caminho)])

            self.assertEqual(codigo, 1)
            self.assertEqual(saida.getvalue(), "")
            erro = json.loads(diagnostico.getvalue())
            self.assertEqual(erro["tipo"], "erro")
            self.assertEqual(erro["etapa"], "Preparando as imagens")
            self.assertIn("cinco categorias", erro["mensagem"])

    def test_informa_etapa_e_motivo_sem_traceback(self):
        with tempfile.TemporaryDirectory() as pasta, \
                patch("agextractor.interfaces.server.executar_extracao", side_effect=ValueError(
                    "Tecnologia → encontrei 6 colunas, mas esta categoria requer 7.")), \
                patch("sys.stdout", new_callable=io.StringIO) as saida, \
                patch("sys.stderr", new_callable=io.StringIO) as diagnostico:
            codigo = main(["--entrada", pasta, "--jogadores", "2"])

            self.assertEqual(codigo, 1)
            self.assertEqual(saida.getvalue(), "")
            erro = json.loads(diagnostico.getvalue())
            self.assertEqual(erro["tipo"], "erro")
            self.assertIn("Tecnologia", erro["mensagem"])
            self.assertNotIn("Traceback", diagnostico.getvalue())

    def test_extrai_somente_a_categoria_solicitada(self):
        esperado = {
            "quantidade_jogadores": 2,
            "categoria": "militar",
            "jogadores": [{"jogador": 1, "militar": {"unidades_mortas": 12}}],
        }
        regioes = {"militar": [[10, 20], [900, 20], [900, 600], [10, 600]]}
        with tempfile.TemporaryDirectory() as pasta, \
                patch("agextractor.interfaces.server.executar_categoria", return_value=esperado) as executar, \
                patch("sys.stdout", new_callable=io.StringIO) as saida:
            caminho = Path(pasta) / "regioes.json"
            caminho.write_text(json.dumps(regioes), encoding="utf-8")

            codigo = main([
                "--entrada", pasta, "--jogadores", "2", "--categoria", "militar",
                "--regioes", str(caminho),
            ])

            self.assertEqual(codigo, 0)
            self.assertEqual(json.loads(saida.getvalue()), esperado)
            self.assertEqual(executar.call_args.args[:3],
                             ("militar", 2, Path(pasta) / "militar.jpeg"))
            self.assertEqual(executar.call_args.kwargs["pontos"], regioes["militar"])


if __name__ == "__main__":
    unittest.main()
