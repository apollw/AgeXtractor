"""Entrada headless usada pela integração do AgeNexus."""

import argparse
import json
from pathlib import Path
import tempfile

from ..extracao import caminhos_imagens, executar_extracao


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Extrai as cinco imagens e escreve somente o contrato JSON em stdout."
    )
    parser.add_argument("--entrada", type=Path, required=True)
    parser.add_argument("--jogadores", type=int, choices=range(2, 9), required=True)
    argumentos = parser.parse_args(argv)

    # O modo servidor não mantém arquivos de saída. O chamador recebe o JSON
    # por stdout e controla o ciclo de vida das imagens de entrada.
    with tempfile.TemporaryDirectory(prefix="agextractor-output-") as pasta:
        resultado = executar_extracao(
            argumentos.jogadores,
            caminhos_imagens(argumentos.entrada),
            Path(pasta) / "resultado.json",
        )
    print(json.dumps(resultado, ensure_ascii=False))


if __name__ == "__main__":
    main()
