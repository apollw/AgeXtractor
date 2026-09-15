"""Caminhos padrão independentes da pasta de execução do programa."""

import os
from pathlib import Path
import sys


EMPACOTADO = getattr(sys, "frozen", False)
RAIZ_PROJETO = Path(__file__).resolve().parents[1]
RAIZ_RECURSOS = Path(getattr(sys, "_MEIPASS", RAIZ_PROJETO))


def pasta_documentos():
    if os.name == "nt":
        import ctypes
        caminho = ctypes.create_unicode_buffer(32768)
        # CSIDL_PERSONAL considera também Documentos redirecionado/OneDrive.
        if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, caminho) == 0:
            return Path(caminho.value)
    return Path.home() / "Documents"


if EMPACOTADO:
    RAIZ_DADOS = Path(os.environ["AGEXTRACTOR_DADOS"]) if os.environ.get("AGEXTRACTOR_DADOS") else pasta_documentos() / "AgeExtractor"
else:
    RAIZ_DADOS = RAIZ_PROJETO / "dados"

PASTA_ENTRADA = RAIZ_DADOS / "entrada"
PASTA_SAIDA = RAIZ_DADOS / "saida"
RESULTADO_PADRAO = PASTA_SAIDA / "resultado.json"


def preparar_pastas():
    PASTA_ENTRADA.mkdir(parents=True, exist_ok=True)
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
