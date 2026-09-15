"""Interface Tkinter. Inicie com: python interface.py"""

from pathlib import Path
from queue import Empty, Queue
import threading
from time import perf_counter
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ..caminhos import PASTA_ENTRADA, RESULTADO_PADRAO, preparar_pastas
from ..extracao import CATEGORIAS, ExtracaoCancelada, executar_extracao
from .ajuste import AjusteTabela


class Aplicacao:
    def __init__(self, janela):
        self.janela = janela
        janela.title("AgeExtractor — Extrair estatísticas")
        janela.geometry("940x720")
        janela.minsize(860, 720)
        self.executando = False
        self.fechar_ao_terminar = False
        self.eventos = Queue()
        self.cancelamento = threading.Event()
        self.trabalhador = None
        self.ultimo_evento = None
        self.inicio = None
        self.controles = []
        self.quantidade = tk.StringVar(value="6")
        self.caminhos = {nome: tk.StringVar() for nome, _, _ in CATEGORIAS}
        self.regioes = {}
        for nome, variavel in self.caminhos.items():
            variavel.trace_add("write", lambda *args, categoria=nome: self.regioes.pop(categoria, None))
        self.destino = tk.StringVar(value=str(RESULTADO_PADRAO))
        self.status = tk.StringVar(value="Selecione as cinco imagens para começar.")
        self.percentual = tk.StringVar(value="0,0%")
        self.tempo = tk.StringVar(value="Tempo decorrido: 0s")
        self.detalhe = tk.StringVar(value="Nenhuma extração em andamento.")
        self._construir()
        janela.protocol("WM_DELETE_WINDOW", self._fechar)
        self.agendamento = janela.after(80, self._receber_eventos)

    def _construir(self):
        estilo = ttk.Style(self.janela)
        if "vista" in estilo.theme_names():
            estilo.theme_use("vista")
        estilo.configure("Titulo.TLabel", font=("Segoe UI", 22, "bold"))
        estilo.configure("Percentual.TLabel", font=("Segoe UI", 15, "bold"))

        corpo = ttk.Frame(self.janela, padding=24)
        corpo.pack(fill="both", expand=True)
        corpo.columnconfigure(0, weight=1)
        ttk.Label(corpo, text="AgeExtractor", style="Titulo.TLabel").grid(sticky="w")
        ttk.Label(corpo, text="Selecione os prints da partida e exporte as estatísticas em JSON.").grid(
            sticky="w", pady=(4, 18)
        )

        configuracao = ttk.Frame(corpo)
        configuracao.grid(sticky="ew", pady=(0, 14))
        ttk.Label(configuracao, text="Número de jogadores:").pack(side="left")
        seletor = ttk.Spinbox(configuracao, from_=2, to=8, width=5, textvariable=self.quantidade)
        seletor.pack(side="left", padx=10)
        self.controles.append(seletor)
        ttk.Label(configuracao, text="De 2 a 8 jogadores").pack(side="left")

        imagens = ttk.LabelFrame(corpo, text="Imagens de cada categoria", padding=12)
        imagens.grid(sticky="ew")
        imagens.columnconfigure(1, weight=1)
        for linha, (nome, titulo, _) in enumerate(CATEGORIAS):
            ttk.Label(imagens, text=titulo, width=12).grid(row=linha, column=0, sticky="w")
            entrada = ttk.Entry(imagens, textvariable=self.caminhos[nome])
            entrada.grid(row=linha, column=1, sticky="ew", padx=(0, 8), pady=5)
            botao = ttk.Button(
                imagens, text="Selecionar…",
                command=lambda categoria=nome, rotulo=titulo: self._selecionar(categoria, rotulo),
            )
            botao.grid(row=linha, column=2)
            ajustar = ttk.Button(imagens, text="Ajustar tabela", command=lambda categoria=nome: self._ajustar(categoria))
            ajustar.grid(row=linha, column=3, padx=(6, 0))
            self.controles.extend((entrada, botao, ajustar))

        ajuda = ttk.Label(
            corpo,
            text="Use imagens da mesma partida e com os jogadores na mesma ordem. "
                 "A tabela é localizada e alinhada automaticamente. Use Ajustar tabela para conferir os recortes. "
                 "Leituras duvidosas serão salvas como null e sinalizadas no JSON.",
            wraplength=860,
        )
        ajuda.grid(sticky="ew", pady=(8, 14))
        corpo.bind("<Configure>", lambda evento: ajuda.configure(wraplength=max(300, evento.width - 12)))

        saida = ttk.LabelFrame(corpo, text="Arquivo de saída", padding=12)
        saida.grid(sticky="ew")
        saida.columnconfigure(0, weight=1)
        entrada = ttk.Entry(saida, textvariable=self.destino)
        entrada.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        botao = ttk.Button(saida, text="Salvar como…", command=self._selecionar_destino)
        botao.grid(row=0, column=1)
        self.controles.extend((entrada, botao))
        ttk.Label(saida, text="Se o arquivo já existir, será substituído somente após a conclusão.").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(6, 0)
        )

        andamento = ttk.LabelFrame(corpo, text="Progresso da extração", padding=12)
        andamento.grid(sticky="ew", pady=16)
        andamento.columnconfigure(0, weight=1)
        ttk.Label(andamento, textvariable=self.status).grid(row=0, column=0, sticky="w")
        ttk.Label(andamento, textvariable=self.percentual, style="Percentual.TLabel").grid(
            row=0, column=1, sticky="e", padx=(10, 0)
        )
        self.barra = ttk.Progressbar(andamento, maximum=100, mode="determinate")
        self.barra.grid(row=1, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Label(andamento, textvariable=self.tempo).grid(row=2, column=0, columnspan=2, sticky="w")
        ttk.Label(andamento, textvariable=self.detalhe, wraplength=700).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(6, 0)
        )

        acoes = ttk.Frame(corpo)
        acoes.grid(sticky="ew")
        self.iniciar_botao = ttk.Button(acoes, text="Iniciar extração", command=self.iniciar)
        self.iniciar_botao.pack(side="right")
        self.cancelar_botao = ttk.Button(acoes, text="Cancelar", command=self.cancelar, state="disabled")
        self.cancelar_botao.pack(side="right", padx=10)
        self.controles.append(self.iniciar_botao)

    def _selecionar(self, categoria, titulo):
        caminho = filedialog.askopenfilename(
            parent=self.janela, title=f"Selecionar imagem — {titulo}", initialdir=str(PASTA_ENTRADA),
            filetypes=[("Imagens", "*.jpeg *.jpg *.png *.bmp *.tif *.tiff *.webp"), ("Todos os arquivos", "*.*")],
        )
        if caminho:
            self.caminhos[categoria].set(caminho)

    def _selecionar_destino(self):
        atual = Path(self.destino.get().strip() or "resultado.json")
        caminho = filedialog.asksaveasfilename(
            parent=self.janela, title="Salvar resultado da extração",
            defaultextension=".json", filetypes=[("JSON", "*.json")],
            initialdir=str(atual.parent), initialfile=atual.name,
        )
        if caminho:
            self.destino.set(caminho)

    def _ajustar(self, categoria):
        caminho = self.caminhos[categoria].get().strip()
        modulo = next(m for n, _, m in CATEGORIAS if n == categoria)
        def aplicar(pontos, quantidade):
            self.regioes[categoria] = pontos
            self.quantidade.set(str(quantidade))
            self.status.set(f"Tabela de {categoria} ajustada — {quantidade} jogadores")
        try:
            AjusteTabela(self.janela, caminho, modulo.colunas, self.regioes.get(categoria), aplicar)
        except (ValueError, OSError) as erro:
            messagebox.showerror("Selecione uma imagem válida", str(erro), parent=self.janela)

    def iniciar(self):
        if self.executando:
            return
        try:
            quantidade = int(self.quantidade.get())
            if not 2 <= quantidade <= 8:
                raise ValueError
        except ValueError:
            messagebox.showerror("Número de jogadores", "Informe um número inteiro entre 2 e 8.", parent=self.janela)
            return
        caminhos = {nome: valor.get().strip() for nome, valor in self.caminhos.items()}
        for nome, titulo, _ in CATEGORIAS:
            if not caminhos[nome] or not Path(caminhos[nome]).expanduser().is_file():
                messagebox.showerror("Imagem necessária", f"Selecione um arquivo existente para {titulo}.", parent=self.janela)
                return
        destino = self.destino.get().strip()
        if not destino or Path(destino).suffix.lower() != ".json":
            messagebox.showerror("Arquivo de saída", "Escolha um arquivo de saída com extensão .json.", parent=self.janela)
            return

        self.executando = True
        self.cancelamento.clear()
        self.ultimo_evento = None
        self.inicio = perf_counter()
        self.barra["value"] = 0
        self.percentual.set("0,0%")
        self.status.set("Preparando extração…")
        self.tempo.set("Tempo decorrido: 0s")
        self.detalhe.set("O progresso será atualizado a cada célula processada.")
        for controle in self.controles:
            controle.configure(state="disabled")
        self.iniciar_botao.configure(text="Extraindo…")
        self.cancelar_botao.configure(state="normal")
        self.trabalhador = threading.Thread(
            target=self._extrair, args=(quantidade, caminhos, destino, dict(self.regioes)), daemon=True
        )
        self.trabalhador.start()

    def _extrair(self, quantidade, caminhos, destino, regioes=None):
        # Esta thread não acessa variáveis nem widgets do Tkinter.
        try:
            resultado = executar_extracao(
                quantidade, caminhos, destino,
                ao_progresso=lambda evento: self.eventos.put(("progresso", evento)),
                cancelado=self.cancelamento.is_set,
                regioes=regioes,
            )
        except ExtracaoCancelada as erro:
            self.eventos.put(("cancelado", str(erro)))
        except Exception as erro:
            self.eventos.put(("erro", str(erro)))
        else:
            self.eventos.put(("concluido", (str(Path(destino).expanduser().resolve()), len(resultado.get("avisos", [])))))

    def _receber_eventos(self):
        try:
            while True:
                tipo, valor = self.eventos.get_nowait()
                if tipo == "progresso":
                    self.ultimo_evento = valor
                    self.barra["value"] = valor.percentual
                    self.percentual.set(f"{valor.percentual:.1f}%".replace(".", ","))
                    if not self.cancelamento.is_set():
                        self.status.set(valor.mensagem)
                    self.detalhe.set(f"{valor.concluidas} de {valor.total} etapas concluídas")
                else:
                    self._terminar(tipo, valor)
        except Empty:
            pass

        if self.inicio is not None:
            if self.executando:
                decorrido = perf_counter() - self.inicio
                self.tempo.set(f"Tempo decorrido: {decorrido:.0f}s")
                if self.ultimo_evento and self.ultimo_evento.restante is not None:
                    self.tempo.set(self.tempo.get() + f" | Restante estimado: {self.ultimo_evento.restante:.0f}s")
            elif self.ultimo_evento:
                self.tempo.set(f"Tempo decorrido: {self.ultimo_evento.decorrido:.0f}s")

        if self.fechar_ao_terminar and not self.executando:
            self.janela.destroy()
            return
        self.agendamento = self.janela.after(80, self._receber_eventos)

    def _terminar(self, tipo, valor):
        self.executando = False
        for controle in self.controles:
            controle.configure(state="normal")
        self.iniciar_botao.configure(text="Iniciar extração")
        self.cancelar_botao.configure(state="disabled")
        if tipo == "concluido":
            arquivo, avisos = valor
            self.status.set(f"Concluído — {avisos} campos precisam de revisão" if avisos else "Concluído — JSON salvo com sucesso")
            self.detalhe.set(f"Arquivo: {arquivo}" + ("\nConsulte a lista 'avisos' no JSON e confira os valores nas imagens." if avisos else ""))
        elif tipo == "cancelado":
            self.status.set("Extração cancelada")
            self.detalhe.set(valor)
        else:
            self.status.set("Não foi possível concluir a extração")
            self.detalhe.set("Confira as imagens, o destino e a instalação do Tesseract.")
            if not self.fechar_ao_terminar:
                messagebox.showerror("Falha na extração", valor, parent=self.janela)

    def cancelar(self):
        if self.executando:
            self.cancelamento.set()
            self.cancelar_botao.configure(state="disabled")
            self.status.set("Cancelando após a leitura da célula atual…")

    def _fechar(self):
        if self.executando:
            self.fechar_ao_terminar = True
            self.cancelar()
        else:
            self.janela.after_cancel(self.agendamento)
            self.janela.destroy()


def main():
    preparar_pastas()
    janela = tk.Tk()
    Aplicacao(janela)
    janela.mainloop()


if __name__ == "__main__":
    main()
