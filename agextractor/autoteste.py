"""Verifica os recursos efetivamente carregados pelo executável empacotado."""

import json
from pathlib import Path
import tempfile
import tkinter as tk

import cv2
import numpy as np
import pytesseract

from .caminhos import EMPACOTADO, PASTA_SAIDA, RAIZ_RECURSOS, preparar_pastas
from .interfaces.gui import Aplicacao
from .ocr import ler_numero


def executar(relatorio):
    preparar_pastas()
    janela = tk.Tk()
    janela.withdraw()
    app = Aplicacao(janela)
    try:
        janela.update_idletasks()
        versao_tk = janela.tk.call("info", "patchlevel")
        assert len(app.caminhos) == 5
        assert app.quantidade.get() == "6"
        imagem = np.full((55, 230, 3), 255, dtype=np.uint8)
        cv2.putText(imagem, "12345", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2, cv2.LINE_AA)
        texto = ler_numero(imagem)
        if texto != "12345":
            raise RuntimeError(f"O teste real de OCR retornou {texto!r}, esperado '12345'.")
        with tempfile.NamedTemporaryFile(dir=PASTA_SAIDA, suffix=".tmp") as arquivo:
            arquivo.write(b"teste de escrita")
        executavel = Path(pytesseract.pytesseract.tesseract_cmd).resolve()
        if EMPACOTADO and not executavel.is_relative_to(RAIZ_RECURSOS.resolve()):
            raise RuntimeError("O executável tentou usar um Tesseract externo ao pacote.")
        dados = {
            "sucesso": True, "empacotado": EMPACOTADO,
            "tk": versao_tk, "opencv": cv2.__version__,
            "tesseract": str(pytesseract.get_tesseract_version()),
            "executavel_ocr": str(executavel), "texto_ocr": texto,
            "pasta_saida": str(PASTA_SAIDA), "categorias_na_interface": len(app.caminhos),
        }
        Path(relatorio).write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    finally:
        app._fechar()
