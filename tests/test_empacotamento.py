import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from agextractor import caminhos, ocr


class RecursosEmpacotados(unittest.TestCase):
    def test_dados_do_usuario_ficam_fora_dos_recursos_do_exe(self):
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            recursos = raiz / "programa" / "_internal"
            usuario = raiz / "usuario com espaco"
            spec = importlib.util.spec_from_file_location("caminhos_empacotados", caminhos.__file__)
            modulo = importlib.util.module_from_spec(spec)
            with patch.object(sys, "frozen", True, create=True), patch.object(sys, "_MEIPASS", str(recursos), create=True):
                with patch.dict(os.environ, {"AGEXTRACTOR_DADOS": str(usuario)}):
                    spec.loader.exec_module(modulo)
            self.assertEqual(modulo.RAIZ_RECURSOS, recursos)
            self.assertEqual(modulo.RESULTADO_PADRAO, usuario / "saida" / "resultado.json")
            modulo.preparar_pastas()
            self.assertTrue(modulo.PASTA_ENTRADA.is_dir())
            self.assertTrue(modulo.PASTA_SAIDA.is_dir())
            self.assertFalse(recursos.exists())

    def test_exe_prefere_motor_e_modelo_incluidos(self):
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            modelo = raiz / "tesseract" / "tessdata" / "eng.traineddata"
            modelo.parent.mkdir(parents=True)
            modelo.touch()
            executavel = raiz / "tesseract" / "tesseract.exe"
            executavel.touch()
            with patch.object(ocr, "EMPACOTADO", True), patch.object(ocr, "RAIZ_RECURSOS", raiz):
                with patch.object(ocr.pytesseract.pytesseract, "tesseract_cmd", "anterior"):
                    with patch.dict(os.environ, {"TESSERACT_CMD": "invalido", "TESSDATA_PREFIX": "invalido"}):
                        ocr.configurar_tesseract()
                        self.assertEqual(ocr.pytesseract.pytesseract.tesseract_cmd, str(executavel))
                        self.assertEqual(os.environ["TESSDATA_PREFIX"], str(modelo.parent))
                        modelo.unlink()
                        with self.assertRaisesRegex(RuntimeError, "incompleto"):
                            ocr.configurar_tesseract()


if __name__ == "__main__":
    unittest.main()
