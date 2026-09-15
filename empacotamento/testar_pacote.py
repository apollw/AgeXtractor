"""Extrai o ZIP em outra pasta e testa o EXE sem Python/Tesseract no PATH."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile


RAIZ = Path(__file__).resolve().parents[1]


def main():
    arquivo = RAIZ / "dist" / "AgeExtractor-Windows-x64.zip"
    esperado = arquivo.with_suffix(".zip.sha256").read_text().split()[0]
    assert hashlib.sha256(arquivo.read_bytes()).hexdigest() == esperado
    with tempfile.TemporaryDirectory(prefix="teste portátil ", dir=RAIZ / "build") as pasta:
        pasta = Path(pasta)
        with zipfile.ZipFile(arquivo) as pacote:
            pacote.extractall(pasta)
        executavel = pasta / "AgeExtractor" / "AgeExtractor.exe"
        relatorio = pasta / "diagnostico.json"
        ambiente = dict(os.environ)
        for chave in ("PYTHONHOME", "PYTHONPATH", "TCL_LIBRARY", "TK_LIBRARY"):
            ambiente.pop(chave, None)
        windows = Path(os.environ.get("SystemRoot", r"C:\Windows"))
        ambiente.update({
            "PATH": os.pathsep.join((str(windows / "System32"), str(windows))),
            "TESSERACT_CMD": str(pasta / "tesseract-inexistente.exe"),
            "TESSDATA_PREFIX": str(pasta / "modelo-inexistente"),
            "AGEXTRACTOR_DADOS": str(pasta / "dados do usuário"),
        })
        processo = subprocess.run(
            [str(executavel), "--autoteste", str(relatorio)], cwd=pasta,
            env=ambiente, timeout=90, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if processo.returncode != 0 or not relatorio.is_file():
            log = pasta / "dados do usuário" / "erro-inicializacao.log"
            raise RuntimeError(log.read_text(encoding="utf-8") if log.is_file() else f"EXE falhou: {processo.returncode}")
        dados = json.loads(relatorio.read_text(encoding="utf-8"))
        assert dados["sucesso"] and dados["empacotado"]
        assert Path(dados["executavel_ocr"]).is_relative_to(pasta / "AgeExtractor")
        assert dados["texto_ocr"] == "12345"
        dados["teste_zip_sha256"] = esperado
        dados["observacao"] = "ZIP extraído em pasta temporária; PATH sem Python/Tesseract; interface oculta e OCR real. Caminhos temporários são removidos após o teste."
        (RAIZ / "build" / "validacao-pacote.json").write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(dados, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
