# Executar pelo script build_windows.py para incluir o OCR e os avisos.
import os
from pathlib import Path

from PyInstaller.utils.hooks import copy_metadata

raiz = Path(SPECPATH).parent
tesseract = Path(os.environ.get("AGEXTRACTOR_TESSERACT", r"C:\Program Files\Tesseract-OCR"))
obrigatorios = [tesseract / "tesseract.exe", tesseract / "tessdata" / "eng.traineddata"]
for arquivo in obrigatorios:
    if not arquivo.is_file():
        raise FileNotFoundError(f"Recurso OCR necessário para empacotar: {arquivo}")

# Mantém o executável e suas DLLs juntos, sem modificar os binários do OCR.
dados = [(str(tesseract / "tesseract.exe"), "tesseract")]
dados += [(str(arquivo), "tesseract") for arquivo in sorted(tesseract.glob("*.dll"))]
dados += [(str(tesseract / "tessdata" / "eng.traineddata"), "tesseract/tessdata")]
if (tesseract / "doc").is_dir():
    dados += [(str(tesseract / "doc"), "tesseract/doc")]
for pacote in ("opencv-python", "numpy", "pillow", "pytesseract", "packaging"):
    dados += copy_metadata(pacote)

a = Analysis(
    [str(raiz / "AgeExtractor.pyw")], pathex=[str(raiz)],
    binaries=[], datas=dados, hiddenimports=[], hookspath=[],
    runtime_hooks=[], excludes=["pytest", "IPython", "matplotlib"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name="AgeExtractor",
    debug=False, bootloader_ignore_signals=False, strip=False,
    upx=False, console=False,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="AgeExtractor")
