"""Entrada headless usada pela integração do AgeNexus."""

import argparse
import json
import math
from pathlib import Path
import sys
import tempfile

from ..extracao import CATEGORIAS, caminhos_imagens, executar_categoria, executar_extracao


def _emitir_evento(tipo, **dados):
    print(json.dumps({"tipo": tipo, **dados}, ensure_ascii=False), file=sys.stderr, flush=True)


def _carregar_regioes(caminho, categorias_esperadas=None):
    if caminho is None:
        return None

    with caminho.open(encoding="utf-8") as arquivo:
        documento = json.load(arquivo)
    categorias = set(categorias_esperadas or (nome for nome, _, _ in CATEGORIAS))
    if set(documento) != categorias:
        esperado = "as cinco categorias" if len(categorias) == len(CATEGORIAS) else f"somente {next(iter(categorias))}"
        raise ValueError(f"As regiões devem informar exatamente {esperado}.")

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
    parser.add_argument(
        "--categoria", choices=[nome for nome, _, _ in CATEGORIAS],
        help="Extrai somente uma categoria e devolve um fragmento incremental.",
    )
    argumentos = parser.parse_args(argv)

    ultima_etapa = "Preparando as imagens"

    def progresso(evento):
        nonlocal ultima_etapa
        ultima_etapa = evento.mensagem
        _emitir_evento(
            "progresso",
            concluidas=evento.concluidas,
            total=evento.total,
            percentual=round(evento.percentual, 2),
            mensagem=evento.mensagem,
        )

    try:
        categorias = [argumentos.categoria] if argumentos.categoria else None
        regioes = _carregar_regioes(argumentos.regioes, categorias)

        if argumentos.categoria:
            categoria = argumentos.categoria
            resultado = executar_categoria(
                categoria,
                argumentos.jogadores,
                argumentos.entrada / f"{categoria}.jpeg",
                ao_progresso=progresso,
                pontos=regioes[categoria] if regioes else None,
            )
        else:
            # O modo servidor não mantém arquivos de saída. O chamador recebe o JSON
            # por stdout e controla o ciclo de vida das imagens de entrada.
            with tempfile.TemporaryDirectory(prefix="agextractor-output-") as pasta:
                resultado = executar_extracao(
                    argumentos.jogadores,
                    caminhos_imagens(argumentos.entrada),
                    Path(pasta) / "resultado.json",
                    ao_progresso=progresso,
                    regioes=regioes,
                )
    except Exception as erro:
        _emitir_evento(
            "erro",
            codigo="FalhaNaExtracao",
            etapa=ultima_etapa,
            mensagem=str(erro) or type(erro).__name__,
        )
        return 1

    print(json.dumps(resultado, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
