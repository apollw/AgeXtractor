"""Fluxo compartilhado pelo terminal e pela interface gráfica."""

from dataclasses import dataclass
import json
import os
from pathlib import Path
import tempfile
from time import perf_counter

from .caminhos import PASTA_ENTRADA, RESULTADO_PADRAO
from .extratores import economia, militar, placar, sociedade, tecnologia
from .ocr import LEITURAS


CATEGORIAS = (
    ("placar", "Placar", placar),
    ("militar", "Militar", militar),
    ("economia", "Economia", economia),
    ("tecnologia", "Tecnologia", tecnologia),
    ("sociedade", "Sociedade", sociedade),
)


def caminhos_imagens(pasta):
    pasta = Path(pasta)
    caminhos = {nome: pasta / f"{nome}.jpeg" for nome, _, _ in CATEGORIAS}
    if not caminhos["placar"].is_file():
        for nome in ("pontuação.jpeg", "pontuacao.jpeg", "score.jpeg"):
            if (pasta / nome).is_file():
                caminhos["placar"] = pasta / nome
                break
    return caminhos


class ExtracaoCancelada(Exception):
    """Cancelamento solicitado antes da gravação do resultado."""


@dataclass(frozen=True)
class EventoProgresso:
    concluidas: int
    total: int
    mensagem: str
    decorrido: float

    @property
    def percentual(self):
        return 100 * self.concluidas / self.total

    @property
    def restante(self):
        if not self.concluidas:
            return None
        return self.decorrido / self.concluidas * (self.total - self.concluidas)


def executar_extracao(
    quantidade_jogadores=6,
    caminhos=None,
    destino=None,
    ao_progresso=None,
    cancelado=None,
    regioes=None,
):
    """Extrai as cinco categorias e salva o mesmo contrato JSON do main original.

    Callbacks são executados na thread chamadora. Interfaces gráficas devem
    encaminhar os eventos à sua thread de UI, sem manipular widgets aqui.
    """
    if type(quantidade_jogadores) is not int or not 2 <= quantidade_jogadores <= 8:
        raise ValueError("Informe uma quantidade inteira de jogadores entre 2 e 8.")

    if caminhos is None:
        caminhos = caminhos_imagens(PASTA_ENTRADA)
    entradas = {}
    for nome, titulo, _ in CATEGORIAS:
        if not caminhos.get(nome):
            raise ValueError(f"Selecione a imagem de {titulo}.")
        entradas[nome] = Path(caminhos[nome]).expanduser().resolve()
        if not entradas[nome].is_file():
            raise ValueError(f"Imagem de {titulo} não encontrada: {entradas[nome]}")

    if destino is None:
        destino = RESULTADO_PADRAO
    if not str(destino).strip():
        raise ValueError("Escolha onde salvar o arquivo JSON.")
    destino = Path(destino).expanduser().resolve()
    if destino in entradas.values():
        raise ValueError("O destino do JSON não pode ser uma das imagens de entrada.")
    if not destino.parent.is_dir() or destino.is_dir():
        raise ValueError("Escolha um arquivo de saída em uma pasta existente.")

    total = quantidade_jogadores * sum(len(m.colunas) for _, _, m in CATEGORIAS) + 1
    concluidas = 0
    inicio = perf_counter()

    def verificar_cancelamento():
        if cancelado is not None and cancelado():
            raise ExtracaoCancelada("Extração cancelada. O resultado anterior foi preservado.")

    def notificar(mensagem, avancar=False):
        nonlocal concluidas
        if avancar:
            concluidas += 1
        if ao_progresso is not None:
            ao_progresso(EventoProgresso(concluidas, total, mensagem, perf_counter() - inicio))

    extraidos = {}
    leituras_identificadas = {}
    for nome, titulo, modulo in CATEGORIAS:
        verificar_cancelamento()
        notificar(f"{titulo} | iniciando leitura...")

        def celula(numero_jogador, nome_coluna, categoria=titulo):
            verificar_cancelamento()
            if leituras:
                leituras_identificadas[(nome, numero_jogador, nome_coluna)] = leituras[-1]
            campo = nome_coluna.replace("_", " ")
            notificar(
                f"{categoria} | jogador {numero_jogador}/{quantidade_jogadores} | {campo}",
                avancar=True,
            )

        extrair = getattr(modulo, f"extrair_{nome}")
        leituras = []
        token = LEITURAS.set(leituras)
        try:
            opcoes = {"ao_processar_celula": celula}
            if regioes and regioes.get(nome) is not None:
                opcoes["pontos_tabela"] = regioes[nome]
            try:
                extraidos[nome] = extrair(str(entradas[nome]), quantidade_jogadores, **opcoes)
            except ValueError as erro:
                raise ValueError(f"{titulo} → {erro}") from erro
        finally:
            LEITURAS.reset(token)

    jogadores = []
    for i in range(quantidade_jogadores):
        jogador = {"jogador": i + 1}
        for nome, _, _ in CATEGORIAS:
            jogador[nome] = {
                campo: valor for campo, valor in extraidos[nome][i].items()
                if campo != "jogador"
            }
        jogadores.append(jogador)
    resultado = {"quantidade_jogadores": quantidade_jogadores, "jogadores": jogadores}
    avisos = []
    for jogador in jogadores:
        for nome, _, _ in CATEGORIAS:
            for campo, valor in jogador[nome].items():
                if valor is None:
                    origem = "tributo" if campo.startswith("tributo_") else campo
                    leitura = leituras_identificadas.get((nome, jogador["jogador"], origem), {})
                    avisos.append({"jogador": jogador["jogador"], "categoria": nome, "campo": campo,
                                   "motivo": "Leitura ausente, inválida ou divergente entre preparações de OCR.",
                                   "candidatos": leitura.get("candidatos", [])})
        pontos = jogador["placar"]
        if all(isinstance(pontos.get(c), int) for c in ("militar", "economia", "tecnologia", "sociedade", "pontuacao_total")):
            if sum(pontos[c] for c in ("militar", "economia", "tecnologia", "sociedade")) != pontos["pontuacao_total"]:
                avisos.append({"jogador": jogador["jogador"], "categoria": "placar", "campo": "pontuacao_total",
                               "motivo": "A soma das categorias difere da pontuação total. Confira o placar na imagem.", "candidatos": []})
    if avisos:
        resultado["avisos"] = avisos

    verificar_cancelamento()
    notificar(f"Salvando {destino.name}...")
    temporario = None
    try:
        # Só substitui o destino depois que todo o JSON estiver gravado.
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=destino.parent,
            prefix=f".{destino.name}.", suffix=".tmp", delete=False,
        ) as arquivo:
            temporario = Path(arquivo.name)
            json.dump(resultado, arquivo, ensure_ascii=False, indent=4)
        verificar_cancelamento()
        os.replace(temporario, destino)
    finally:
        if temporario is not None:
            temporario.unlink(missing_ok=True)

    notificar(f"Concluído: {destino.name} salvo", avancar=True)
    return resultado
