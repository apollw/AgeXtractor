"""Diagnóstico: python -m agextractor.ferramentas.analisar_placar [imagem]."""

import argparse
from pathlib import Path

import cv2
import pytesseract

from .. import ocr  # Usa a mesma configuração de Tesseract dos extratores.
from ..caminhos import PASTA_ENTRADA


def main(argv=None):
    parser = argparse.ArgumentParser(description="Exibe os textos e coordenadas OCR do placar.")
    parser.add_argument("imagem", nargs="?", type=Path, default=PASTA_ENTRADA / "placar.jpeg")
    argumentos = parser.parse_args(argv)
    imagem = cv2.imread(str(argumentos.imagem))
    if imagem is None:
        parser.error(f"Não foi possível carregar {argumentos.imagem}")
    imagem = cv2.resize(imagem, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    dados = pytesseract.image_to_data(
        imagem, output_type=pytesseract.Output.DICT, config="--psm 6"
    )
    for i, texto in enumerate(dados["text"]):
        texto = texto.strip()
        if texto:
            print(
                f"{texto:25} "
                f"X={dados['left'][i]:4} Y={dados['top'][i]:4} "
                f"W={dados['width'][i]:4} H={dados['height'][i]:4}"
            )


if __name__ == "__main__":
    main()
