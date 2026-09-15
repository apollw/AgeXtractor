"""Entrada do aplicativo Windows, com diagnóstico para builds sem console."""

import argparse
from pathlib import Path
import sys
import traceback


def main():
    parser = argparse.ArgumentParser(description="AgeExtractor para Windows")
    parser.add_argument("--autoteste", type=Path, help="Executa diagnóstico oculto e grava um relatório JSON")
    argumentos = parser.parse_args()
    try:
        if argumentos.autoteste:
            from .autoteste import executar
            executar(argumentos.autoteste)
        else:
            from .interfaces.gui import main as abrir_interface
            abrir_interface()
    except Exception:
        from .caminhos import RAIZ_DADOS
        erro = traceback.format_exc()
        registro = RAIZ_DADOS / "erro-inicializacao.log"
        try:
            registro.parent.mkdir(parents=True, exist_ok=True)
            registro.write_text(erro, encoding="utf-8")
        except OSError:
            registro = None
        if argumentos.autoteste:
            if sys.stderr is not None:
                print(erro, file=sys.stderr)
            raise SystemExit(1)
        import ctypes
        mensagem = "Não foi possível iniciar o AgeExtractor."
        if registro:
            mensagem += f"\nDetalhes em: {registro}"
        ctypes.windll.user32.MessageBoxW(None, mensagem, "AgeExtractor", 0x10)
        raise SystemExit(1)
