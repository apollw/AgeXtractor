import argparse
import json
import shutil
import sys

from ..caminhos import PASTA_ENTRADA, RESULTADO_PADRAO
from ..extracao import CATEGORIAS, caminhos_imagens, executar_extracao
from pathlib import Path


class Progresso:
    def __init__(self):
        self.concluidas = 0
        self.largura_anterior = 0
        self.interativo = sys.stderr.isatty()

    def atualizar(self, evento):
        avancou = evento.concluidas > self.concluidas
        self.concluidas = evento.concluidas
        largura = max(1, shutil.get_terminal_size().columns - 1)
        tamanho_barra = max(10, min(30, largura - 85))
        preenchido = int(evento.percentual / 100 * tamanho_barra)
        barra = '#' * preenchido + '-' * (tamanho_barra - preenchido)
        tempo = f'{evento.decorrido:.0f}s'
        if 0 < evento.concluidas < evento.total:
            tempo += f' | restante ~{evento.restante:.0f}s'
        linha = f'[{barra}] {evento.percentual:6.1f}% | {tempo} | {evento.mensagem}'

        if self.interativo:
            linha = linha[:largura]
            print(
                '\r' + linha.ljust(min(self.largura_anterior, largura)),
                end='', file=sys.stderr, flush=True,
            )
            self.largura_anterior = len(linha)
        elif not avancou or evento.concluidas == evento.total:
            print(linha, file=sys.stderr, flush=True)

    def finalizar(self):
        if self.interativo:
            print(file=sys.stderr, flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Extrai estatísticas das cinco imagens da partida.")
    parser.add_argument("--entrada", type=Path, default=PASTA_ENTRADA, help="Pasta com as cinco imagens JPEG")
    parser.add_argument("--saida", type=Path, default=RESULTADO_PADRAO, help="Arquivo JSON de saída")
    parser.add_argument("--jogadores", type=int, choices=range(2, 9), default=6, help="Quantidade de jogadores (2 a 8)")
    argumentos = parser.parse_args(argv)
    progresso = Progresso()
    try:
        resultado = executar_extracao(
            argumentos.jogadores,
            caminhos_imagens(argumentos.entrada),
            argumentos.saida,
            ao_progresso=progresso.atualizar,
        )
    finally:
        progresso.finalizar()
    print(json.dumps(resultado, ensure_ascii=False, indent=4))


if __name__ == '__main__':
    main()
