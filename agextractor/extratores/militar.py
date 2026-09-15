from .base import extrair


# Ordem dos campos; os recortes reais sao detectados em cada tabela.
colunas = {
    "unidades_mortas": (710, 800),
    "unidades_perdidas": (800, 890),
    "construcoes_destruidas": (890, 980),
    "construcoes_perdidas": (980, 1070),
    "unidades_convertidas": (1070, 1160),
    "maior_exercito": (1160, 1250),
}


def extrair_militar(caminho_imagem, quantidade_jogadores, ao_processar_celula=None, pontos_tabela=None):
    return extrair(caminho_imagem, quantidade_jogadores, colunas, ao_processar_celula, pontos_tabela)
