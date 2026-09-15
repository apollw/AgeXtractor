from .base import extrair


# Ordem dos campos; os recortes reais sao detectados em cada tabela.
colunas = {
    "comida": (710, 800),
    "madeira": (800, 895),
    "pedra": (895, 985),
    "ouro": (985, 1076),
    "lucro_comercial": (1076, 1165),
    "tributo": (1165, 1250),
}


def extrair_economia(caminho_imagem, quantidade_jogadores, ao_processar_celula=None, pontos_tabela=None):
    return extrair(caminho_imagem, quantidade_jogadores, colunas, ao_processar_celula, pontos_tabela)
