"""Localiza e retifica a tabela antes de delimitar suas células."""

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


DESTINO = np.float32([[231, 198], [1353, 198], [1353, 655], [231, 655]])


def ordenar_pontos(pontos):
    pontos = np.asarray(pontos, dtype=np.float32)
    if pontos.shape != (4, 2) or not np.isfinite(pontos).all():
        raise ValueError("Selecione os quatro cantos da tabela.")
    soma = pontos.sum(axis=1)
    diferenca = np.diff(pontos, axis=1).ravel()
    ordenados = np.array([pontos[soma.argmin()], pontos[diferenca.argmin()], pontos[soma.argmax()], pontos[diferenca.argmax()]])
    if len(np.unique(ordenados, axis=0)) != 4 or not cv2.isContourConvex(ordenados):
        raise ValueError("Os quatro cantos precisam formar um quadrilátero convexo.")
    if cv2.contourArea(ordenados) < 100:
        raise ValueError("A região selecionada é muito pequena.")
    return ordenados


def carregar_imagem(caminho):
    imagem = cv2.imread(str(Path(caminho)))
    if imagem is None:
        raise ValueError(f"Não foi possível carregar a imagem: {caminho}")
    return imagem


def localizar_tabela(imagem):
    escala = min(1.0, 1600 / max(imagem.shape[:2]))
    menor = cv2.resize(imagem, None, fx=escala, fy=escala) if escala < 1 else imagem
    cinza = cv2.GaussianBlur(cv2.cvtColor(menor, cv2.COLOR_BGR2GRAY), (5, 5), 0)
    candidatos = []
    for limites in ((30, 90), (15, 60), (60, 150)):
        bordas = cv2.Canny(cinza, *limites)
        bordas = cv2.morphologyEx(bordas, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        contornos, _ = cv2.findContours(bordas, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for contorno in contornos:
            poligono = cv2.approxPolyDP(contorno, .02 * cv2.arcLength(contorno, True), True)
            if len(poligono) != 4 or not cv2.isContourConvex(poligono):
                continue
            area = cv2.contourArea(poligono)
            if not .06 < area / (menor.shape[0] * menor.shape[1]) < .85:
                continue
            pontos = ordenar_pontos(poligono.reshape(4, 2))
            largura = (np.linalg.norm(pontos[1] - pontos[0]) + np.linalg.norm(pontos[2] - pontos[3])) / 2
            altura = (np.linalg.norm(pontos[3] - pontos[0]) + np.linalg.norm(pontos[2] - pontos[1])) / 2
            if 2.1 < largura / altura < 3.4:
                candidatos.append((area, pontos / escala))
        if candidatos:
            return max(candidatos, key=lambda item: item[0])[1]
    raise ValueError("Não consegui localizar a tabela. Use 'Ajustar tabela' e marque seus quatro cantos, incluindo cabeçalho e legenda inferior.")


def intervalos(mascara):
    inicio = None
    encontrados = []
    for i, marcado in enumerate(np.r_[mascara, False]):
        if marcado and inicio is None:
            inicio = i
        elif not marcado and inicio is not None:
            encontrados.append((inicio, i))
            inicio = None
    return encontrados


@dataclass
class Tabela:
    imagem: np.ndarray
    pontos: np.ndarray
    linhas: list

    def colunas(self, nomes):
        cinza = cv2.cvtColor(self.imagem, cv2.COLOR_BGR2GRAY)
        tinta = (cinza[203:236, 690:1250] < 100).sum(axis=0) > 1
        tinta = cv2.morphologyEx(tinta.astype(np.uint8)[None, :], cv2.MORPH_CLOSE, np.ones((1, 11), np.uint8)).ravel()
        grupos = [(a, b) for a, b in intervalos(tinta) if b - a >= 10]
        if len(grupos) != len(nomes):
            raise ValueError(f"Encontrei {len(grupos)} colunas de estatísticas, mas esta categoria requer {len(nomes)}. Confira a categoria selecionada e o recorte da tabela.")
        centros = np.array([690 + (a + b) / 2 for a, b in grupos])
        passo = np.median(np.diff(centros))
        if passo < 60 or passo > 115 or np.ptp(np.diff(centros)) > 30:
            raise ValueError("Não foi possível separar as colunas com segurança. Confira a região da tabela.")
        limites = np.r_[centros[0] - passo / 2, (centros[:-1] + centros[1:]) / 2, centros[-1] + passo / 2].round().astype(int)
        return {nome: (int(limites[i] + 3), int(limites[i + 1] + 3)) for i, nome in enumerate(nomes)}


def preparar_tabela(caminho, quantidade=None, pontos=None):
    imagem = carregar_imagem(caminho)
    pontos = ordenar_pontos(pontos) if pontos is not None else localizar_tabela(imagem)
    if (pontos < 0).any() or (pontos[:, 0] >= imagem.shape[1]).any() or (pontos[:, 1] >= imagem.shape[0]).any():
        raise ValueError("Os cantos precisam estar dentro da imagem.")
    matriz = cv2.getPerspectiveTransform(pontos, DESTINO)
    alinhada = cv2.warpPerspective(imagem, matriz, (1600, 899), flags=cv2.INTER_CUBIC)
    cinza = cv2.GaussianBlur(cv2.cvtColor(alinhada, cv2.COLOR_BGR2GRAY), (3, 3), 0)
    contagem = (cinza[238:578, 720:1240] < 100).sum(axis=1)
    faixas = [(a, b) for a, b in intervalos(contagem > max(6, contagem.max() * .20)) if 3 <= b - a <= 28]
    centros = [round(238 + (a + b) / 2) for a, b in faixas]
    if not 2 <= len(centros) <= 8 or (len(centros) > 1 and any(not 28 <= b - a <= 55 for a, b in zip(centros, centros[1:]))):
        raise ValueError("Não foi possível reconhecer as linhas dos jogadores. Confira o foco da foto e ajuste a tabela.")
    if quantidade is not None and len(centros) != quantidade:
        raise ValueError(f"Detectei {len(centros)} jogadores na imagem, mas foram informados {quantidade}. Ajuste o número de jogadores ou a região da tabela.")
    return Tabela(alinhada, pontos, [(y - 12, y + 13) for y in centros])
