import os
from pathlib import Path
import re
import shutil
from collections import Counter
from contextvars import ContextVar
import unicodedata

import cv2
import pytesseract

from .caminhos import EMPACOTADO, RAIZ_RECURSOS


def configurar_tesseract():
    if EMPACOTADO:
        pasta = RAIZ_RECURSOS / "tesseract"
        executavel = pasta / "tesseract.exe"
        if not executavel.is_file() or not (pasta / "tessdata" / "eng.traineddata").is_file():
            raise RuntimeError("O pacote OCR está incompleto. Extraia novamente toda a pasta do AgeExtractor.")
        # Vale apenas para este processo e seus subprocessos, sem alterar o Windows.
        os.environ["TESSDATA_PREFIX"] = str(pasta / "tessdata")
    else:
        padrao = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Tesseract-OCR" / "tesseract.exe"
        executavel = os.environ.get("TESSERACT_CMD") or (str(padrao) if padrao.is_file() else shutil.which("tesseract")) or str(padrao)
    pytesseract.pytesseract.tesseract_cmd = str(executavel)


configurar_tesseract()
LEITURAS = ContextVar("leituras_ocr", default=None)


def _remover_destaque(recorte):
    """Retira a estrela amarela que precede o valor no layout de referência."""
    if recorte is None or recorte.size == 0:
        raise ValueError("O recorte para OCR está vazio. Confira o layout da imagem.")

    hsv = cv2.cvtColor(recorte, cv2.COLOR_BGR2HSV)
    amarelo = cv2.inRange(hsv, (20, 50, 80), (60, 255, 255))
    _, _, componentes, _ = cv2.connectedComponentsWithStats(amarelo)

    for x, _, largura, altura, area in componentes[1:]:
        # A margem inclui o contorno escuro da estrela, confundido com dígitos.
        fim = x + largura + 3
        if 10 <= largura < 30 and 10 <= altura < 28 and area >= 65 and fim < recorte.shape[1] * .70:
            return recorte[:, fim:]

    return recorte


def _preparar(recorte, escala=4, ajustar_margens=False, metodo="otsu"):
    cinza = cv2.cvtColor(recorte, cv2.COLOR_BGR2GRAY)
    ampliada = cv2.resize(
        cinza, None, fx=escala, fy=escala, interpolation=cv2.INTER_CUBIC
    )
    if metodo == "cinza":
        binaria = ampliada
    elif metodo == "adaptativo":
        binaria = cv2.adaptiveThreshold(ampliada, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 41, 13)
    else:
        _, binaria = cv2.threshold(ampliada, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    if ajustar_margens:
        x, y, largura, altura = cv2.boundingRect(255 - binaria)
        if largura and altura:
            binaria = binaria[y:y + altura, x:x + largura]

    return cv2.copyMakeBorder(
        binaria, 12, 12, 12, 12, cv2.BORDER_CONSTANT, value=255
    )


def _ler(recorte, caracteres=None):
    # A margem esquerda pode conter a borda da área de ícones adjacente.
    if recorte is not None and recorte.shape[1] > 10:
        recorte = recorte[:, 2:]
    recorte = _remover_destaque(recorte)
    config = "--psm 7"
    if caracteres:
        config += f" -c tessedit_char_whitelist={caracteres}"

    candidatos = []
    validos = []
    for escala, segmentacao, margens in ((3, 7, False), (4, 7, False), (5, 7, False), (4, 8, True), (5, 8, True)):
        if segmentacao == 8 and (caracteres == "0123456789:" or len(set(validos)) > 1 or len(validos) >= 3):
            break
        metodo = f"otsu_{escala}x_psm{segmentacao}"
        dados = pytesseract.image_to_data(_preparar(recorte, escala=escala, ajustar_margens=margens), config=config.replace("--psm 7", f"--psm {segmentacao}"), output_type=pytesseract.Output.DICT)
        tokens = [(t.strip(), float(c)) for t, c in zip(dados["text"], dados["conf"]) if t.strip()]
        texto = " ".join(t for t, _ in tokens)
        confianca = min((c for _, c in tokens), default=0)
        if caracteres == "0123456789:":
            valido = re.fullmatch(r"\d{1,2}:[0-5]\d:[0-5]\d", texto)
            if valido:
                texto = ":".join(f"{int(parte):02}" for parte in texto.split(":"))
        elif caracteres:
            valido = re.fullmatch(r"[0-9]+(?:/[0-9]+)?", texto)
        else:
            texto = "".join(c for c in unicodedata.normalize("NFKD", texto.lower()) if not unicodedata.combining(c))
            valido = texto in ("sim", "nao", "yes", "no")
        candidatos.append({"texto": texto, "confianca": confianca, "metodo": metodo})
        if valido:
            validos.append(texto)
    contagem = Counter(validos)
    texto, votos = contagem.most_common(1)[0] if contagem else ("", 0)
    confianca = max((c["confianca"] for c in candidatos if c["texto"] == texto), default=0)
    # O Tesseract pode atribuir confiança zero quando há whitelist, mesmo
    # com transcrição correta; exigimos concordância nas três escalas nesse caso.
    revisar = votos < 2 or len(contagem) > 1 or (confianca < 35 and votos < 3)
    if LEITURAS.get() is not None:
        LEITURAS.get().append({"candidatos": candidatos, "revisar": revisar})
    return "" if revisar else texto


def ler_numero(recorte):
    return _ler(recorte, "0123456789/")


def ler_tempo(recorte):
    texto = _ler(recorte, "0123456789:").replace(" ", "")
    resultado = re.fullmatch(r"\d{1,2}:[0-5]\d:[0-5]\d", texto)
    return resultado.group() if resultado else texto


def ler_texto(recorte):
    return _ler(recorte)
