"""Gera a pasta portátil e o ZIP de distribuição para Windows x64."""

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys


RAIZ = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tesseract", type=Path, default=Path(r"C:\Program Files\Tesseract-OCR"))
    argumentos = parser.parse_args()
    if sys.platform != "win32" or platform.architecture()[0] != "64bit":
        parser.error("Este build deve ser executado com Python de 64 bits no Windows.")

    motor = argumentos.tesseract.resolve()
    for arquivo in (motor / "tesseract.exe", motor / "tessdata" / "eng.traineddata"):
        if not arquivo.is_file():
            parser.error(f"Recurso OCR ausente: {arquivo}")
    ambiente = {**os.environ, "AGEXTRACTOR_TESSERACT": str(motor)}
    distribuicao = (RAIZ / "dist").resolve()
    trabalho = (RAIZ / "build").resolve()
    # --noconfirm pode substituir builds anteriores; restringe ambos ao projeto.
    for pasta in (distribuicao, trabalho):
        if not pasta.is_relative_to(RAIZ):
            raise ValueError("O destino de build precisa ficar dentro do projeto.")
    subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--noconfirm",
         "--distpath", str(distribuicao), "--workpath", str(trabalho),
         str(RAIZ / "empacotamento" / "AgeExtractor.spec")],
        cwd=RAIZ, env=ambiente, check=True,
    )
    pacote = distribuicao / "AgeExtractor"
    shutil.copy2(RAIZ / "empacotamento" / "LEIA-ME.txt", pacote / "LEIA-ME.txt")
    licencas = pacote / "licencas"
    licencas.mkdir(exist_ok=True)
    python_licenca = Path(sys.base_prefix) / "LICENSE.txt"
    if python_licenca.is_file():
        shutil.copy2(python_licenca, licencas / "Python-LICENSE.txt")
    import PyInstaller
    for arquivo in Path(PyInstaller.__file__).parent.parent.glob("pyinstaller-*.dist-info/licenses/*"):
        if arquivo.is_file():
            shutil.copy2(arquivo, licencas / f"PyInstaller-{arquivo.name}")

    versoes = {
        "python": platform.python_version(), "arquitetura": platform.machine(),
        "pacotes": {nome: importlib.metadata.version(nome) for nome in (
            "pyinstaller", "pyinstaller-hooks-contrib", "opencv-python", "pytesseract", "numpy", "pillow", "packaging"
        )},
        "tesseract_sha256": hashlib.sha256((motor / "tesseract.exe").read_bytes()).hexdigest(),
        "modelo_ingles_sha256": hashlib.sha256((motor / "tessdata" / "eng.traineddata").read_bytes()).hexdigest(),
    }
    (pacote / "VERSOES.json").write_text(json.dumps(versoes, indent=2), encoding="utf-8")
    arquivo_zip = Path(shutil.make_archive(
        str(distribuicao / "AgeExtractor-Windows-x64"), "zip", distribuicao, "AgeExtractor"
    ))
    resumo = hashlib.sha256(arquivo_zip.read_bytes()).hexdigest()
    arquivo_zip.with_suffix(".zip.sha256").write_text(f"{resumo}  {arquivo_zip.name}\n", encoding="ascii")
    print(f"Executável: {pacote / 'AgeExtractor.exe'}", flush=True)
    print(f"Pacote: {arquivo_zip} ({arquivo_zip.stat().st_size / 1024 ** 2:.1f} MB)", flush=True)


if __name__ == "__main__":
    main()
