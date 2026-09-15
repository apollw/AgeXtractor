from .base import extrair


# Ordem dos campos; os recortes reais sao detectados em cada tabela.
colunas = {
    "militar": (710, 800),
    "economia": (800, 890),
    "tecnologia": (890, 980),
    "sociedade": (980, 1070),
    "pontuacao_total": (1070, 1165),
}


def extrair_placar(caminho_imagem, quantidade_jogadores, ao_processar_celula=None, pontos_tabela=None):
    return extrair(caminho_imagem, quantidade_jogadores, colunas, ao_processar_celula, pontos_tabela)
