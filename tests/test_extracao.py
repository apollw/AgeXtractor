"""Regressão com valores transcritos manualmente das imagens do projeto.

Requer OpenCV, pytesseract e o executável Tesseract configurado em ocr.py.
O main.py é executado em pasta temporária para preservar a saída do usuário.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


RAIZ = Path(__file__).resolve().parents[1]
FIXTURES = RAIZ / "tests" / "fixtures"


class ExtracaoDasImagens(unittest.TestCase):
    def test_fluxo_completo_confere_os_180_campos(self):
        categorias = ("placar", "militar", "economia", "tecnologia", "sociedade")
        faltantes = [nome for nome in categorias if not (FIXTURES / "imagens" / f"{nome}.jpeg").is_file()]
        if faltantes:
            self.skipTest("Imagens de referência ausentes em tests/fixtures/imagens: " + ", ".join(faltantes))
        esperado = json.loads(
            (FIXTURES / "resultado_esperado.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory(prefix="agextractor-teste-") as pasta:
            for categoria in categorias:
                shutil.copy2(FIXTURES / "imagens" / f"{categoria}.jpeg", pasta)
            processo = subprocess.run(
                [sys.executable, str(RAIZ / "main.py"), "--entrada", pasta,
                 "--saida", str(Path(pasta) / "resultado.json")],
                cwd=pasta,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=300,
            )
            self.assertEqual(processo.returncode, 0, processo.stderr)
            obtido = json.loads(
                (Path(pasta) / "resultado.json").read_text(encoding="utf-8")
            )

        self.assertEqual(set(obtido), set(esperado))
        self.assertEqual(obtido["quantidade_jogadores"], 6)
        self.assertEqual(len(obtido["jogadores"]), 6)
        for real, referencia in zip(obtido["jogadores"], esperado["jogadores"]):
            self.assertEqual(set(real), set(referencia))
            self.assertEqual(real["jogador"], referencia["jogador"])
            for categoria, campos in referencia.items():
                if categoria == "jogador":
                    continue
                self.assertEqual(set(real[categoria]), set(campos))
                for campo, valor in campos.items():
                    with self.subTest(jogador=real["jogador"], categoria=categoria, campo=campo):
                        self.assertIs(type(real[categoria][campo]), type(valor))
                        self.assertEqual(real[categoria][campo], valor)


if __name__ == "__main__":
    unittest.main()
