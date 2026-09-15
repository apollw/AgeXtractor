"""Entrada headless usada pela integração do AgeNexus."""

import argparse
import json
import math
from pathlib import Path
import tempfile

from ..extracao import CATEGORIAS, caminhos_imagens, executar_extracao


def _carregar_regioes(caminho):
    if caminho is None:
        return None

    with caminho.open(encoding="utf-8") as arquivo:
        documento = json.load(arquivo)
    categorias = {nome for nome, _, _ in CATEGORIAS}
    if set(documento) != categorias:
        raise ValueError("As regiões devem informar exatamente as cinco categorias.")

    regioes = {}
    for categoria, pontos in documento.items():
        if (not isinstance(pontos, list) or len(pontos) != 4 or
                any(not isinstance(ponto, list) or len(ponto) != 2 for ponto in pontos)):
            raise ValueError(f"A região de {categoria} deve possuir quatro pontos.")
        if any(type(valor) not in (int, float) or not math.isfinite(valor)
               for ponto in pontos for valor in ponto):
            raise ValueError(f"A região de {categoria} contém uma coordenada inválida.")
        regioes[categoria] = pontos
    return regioes


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Extrai as cinco imagens e escreve somente o contrato JSON em stdout."
    )
    parser.add_argument("--entrada", type=Path, required=True)
    parser.add_argument("--jogadores", type=int, choices=range(2, 9), required=True)
    parser.add_argument(
        "--regioes", type=Path,
        help="JSON opcional com os quatro cantos da tabela em cada imagem.",
    )
    argumentos = parser.parse_args(argv)
    regioes = _carregar_regioes(argumentos.regioes)

    # O modo servidor não mantém arquivos de saída. O chamador recebe o JSON
    # por stdout e controla o ciclo de vida das imagens de entrada.
    with tempfile.TemporaryDirectory(prefix="agextractor-output-") as pasta:
        resultado = executar_extracao(
            argumentos.jogadores,
            caminhos_imagens(argumentos.entrada),
            Path(pasta) / "resultado.json",
            regioes=regioes,
        )
    print(json.dumps(resultado, ensure_ascii=False))


if __name__ == "__main__":
    main()
