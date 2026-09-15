"""Leitura das células após a localização da tabela, sem zeros inventados."""

from ..layout import preparar_tabela
from ..ocr import ler_numero, ler_tempo, ler_texto


def extrair(caminho, quantidade, nomes, ao_processar_celula=None, pontos_tabela=None):
    tabela = preparar_tabela(caminho, quantidade, pontos_tabela)
    colunas = tabela.colunas(nomes)
    jogadores = []
    for numero, (y1, y2) in enumerate(tabela.linhas, 1):
        dados = {"jogador": numero}
        for campo, (x1, x2) in colunas.items():
            recorte = tabela.imagem[y1:y2, x1:x2]
            if campo.startswith("idade_"):
                dados[campo] = ler_tempo(recorte) or None
            elif campo == "sobreviveu":
                texto = ler_texto(recorte)
                dados[campo] = True if texto in ("sim", "yes") else False if texto in ("nao", "no") else None
            elif campo == "tributo":
                texto = ler_numero(recorte)
                partes = texto.split("/")
                validas = len(partes) == 2 and all(p.isdigit() for p in partes)
                dados["tributo_enviado"] = int(partes[0]) if validas else None
                dados["tributo_recebido"] = int(partes[1]) if validas else None
            else:
                texto = ler_numero(recorte)
                valor = int(texto) if texto.isdigit() else None
                if campo in ("mapa_explorado", "percentual_pesquisas") and valor is not None and valor > 100:
                    valor = None
                dados[campo] = valor
            if ao_processar_celula is not None:
                ao_processar_celula(numero, campo)
        jogadores.append(dados)
    return jogadores
