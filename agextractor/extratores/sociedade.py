from .base import extrair


# Ordem dos campos; os recortes reais sao detectados em cada tabela.
colunas = {
    "maravilhas": (710, 800),
    "castelos": (800, 890),
    "reliquias_capturadas": (890, 980),
    "ouro_reliquias": (980, 1070),
    "maximo_aldeoes": (1070, 1160),
    "sobreviveu": (1160, 1250),
}


def extrair_sociedade(caminho_imagem, quantidade_jogadores, ao_processar_celula=None, pontos_tabela=None):
    return extrair(caminho_imagem, quantidade_jogadores, colunas, ao_processar_celula, pontos_tabela)
