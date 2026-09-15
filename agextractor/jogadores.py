def gerar_linhas(quantidade_jogadores):

    if quantidade_jogadores < 2 or quantidade_jogadores > 8:
        raise ValueError(
            "A quantidade de jogadores deve estar entre 2 e 8."
        )

    # Faixas centradas no texto, sem a mudança de fundo entre linhas.
    # Coordenadas do layout de referência de 1600 × 899 pixels.
    centros_y = [259, 300, 342, 383, 425, 466, 507, 548]
    return [(y - 12, y + 13) for y in centros_y[:quantidade_jogadores]]
