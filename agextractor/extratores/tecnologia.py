from .base import extrair


# Ordem dos campos; os recortes reais sao detectados em cada tabela.
colunas = {
    "idade_feudal": (709, 795),
    "idade_castelos": (795, 889),
    "idade_imperial": (889, 985),
    "mapa_explorado": (985, 1076),
    "pesquisas": (1076, 1165),
    "percentual_pesquisas": (1165, 1250),
}


def extrair_tecnologia(caminho_imagem, quantidade_jogadores, ao_processar_celula=None, pontos_tabela=None):
    return extrair(caminho_imagem, quantidade_jogadores, colunas, ao_processar_celula, pontos_tabela)
