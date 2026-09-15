"""Seleção visual dos quatro cantos e prévia da tabela retificada."""

import tkinter as tk
from tkinter import ttk, messagebox

import cv2
from PIL import Image, ImageTk

from ..layout import carregar_imagem, localizar_tabela, preparar_tabela


class AjusteTabela:
    def __init__(self, parent, caminho, nomes, pontos, aplicar):
        self.caminho, self.nomes, self.aplicar = caminho, nomes, aplicar
        original = carregar_imagem(caminho)
        self.escala = min(1, 1050 / original.shape[1], 600 / original.shape[0])
        self.janela = tk.Toplevel(parent)
        self.janela.title("Ajustar tabela")
        self.janela.transient(parent)
        self.janela.grab_set()
        ttk.Label(self.janela, text="Arraste os quatro cantos da borda externa da tabela, incluindo cabeçalho e legenda inferior.", padding=10).pack()
        foto = Image.fromarray(cv2.cvtColor(original, cv2.COLOR_BGR2RGB))
        foto = foto.resize((round(original.shape[1] * self.escala), round(original.shape[0] * self.escala)))
        self.foto = ImageTk.PhotoImage(foto, master=self.janela)
        self.canvas = tk.Canvas(self.janela, width=foto.width, height=foto.height, highlightthickness=0)
        self.canvas.pack()
        self.canvas.create_image(0, 0, anchor="nw", image=self.foto)
        if pontos is None:
            try:
                pontos = localizar_tabela(original).tolist()
            except ValueError:
                h, w = original.shape[:2]
                pontos = [[w*.15,h*.2],[w*.85,h*.2],[w*.85,h*.8],[w*.15,h*.8]]
        self.pontos = [[x*self.escala,y*self.escala] for x,y in pontos]
        self.arrastando = None
        self.canvas.bind("<Button-1>", self._pressionar)
        self.canvas.bind("<B1-Motion>", self._mover)
        self.canvas.bind("<ButtonRelease-1>", lambda e: setattr(self, "arrastando", None))
        self.info = tk.StringVar(value="Confira a prévia antes de aplicar. A imagem original será preservada.")
        ttk.Label(self.janela, textvariable=self.info, padding=8).pack()
        acoes = ttk.Frame(self.janela, padding=8)
        acoes.pack(fill="x")
        ttk.Button(acoes, text="Prévia das células", command=self._previa).pack(side="left")
        ttk.Button(acoes, text="Aplicar ajuste", command=self._salvar).pack(side="right")
        self._desenhar()

    def _desenhar(self):
        self.canvas.delete("marcacao")
        self.canvas.create_polygon(*[v for p in self.pontos for v in p], outline="#00ffff", fill="", width=2, tags="marcacao")
        for i, (x,y) in enumerate(self.pontos):
            self.canvas.create_oval(x-8,y-8,x+8,y+8,fill="#00ffff",tags="marcacao")
            self.canvas.create_text(x,y-18,text=str(i+1),fill="red",tags="marcacao")

    def _pressionar(self, evento):
        i = min(range(4), key=lambda i: (self.pontos[i][0]-evento.x)**2+(self.pontos[i][1]-evento.y)**2)
        if (self.pontos[i][0]-evento.x)**2+(self.pontos[i][1]-evento.y)**2 < 900:
            self.arrastando = i

    def _mover(self, evento):
        if self.arrastando is not None:
            self.pontos[self.arrastando] = [max(0,min(evento.x,self.foto.width()-1)),max(0,min(evento.y,self.foto.height()-1))]
            self._desenhar()

    def _validar(self):
        pontos = [[x/self.escala,y/self.escala] for x,y in self.pontos]
        tabela = preparar_tabela(self.caminho, pontos=pontos)
        tabela.colunas(self.nomes)
        self.info.set(f"Detectados {len(tabela.linhas)} jogadores. O ajuste será usado somente nesta imagem.")
        return tabela

    def _previa(self):
        try:
            tabela = self._validar()
        except ValueError as erro:
            messagebox.showerror("Confira os cantos", str(erro), parent=self.janela)
            return
        imagem = tabela.imagem.copy()
        for y1,y2 in tabela.linhas:
            for x1,x2 in tabela.colunas(self.nomes).values():
                cv2.rectangle(imagem,(x1,y1),(x2,y2),(0,0,255),1)
        foto = Image.fromarray(cv2.cvtColor(imagem[198:655,231:1353],cv2.COLOR_BGR2RGB))
        janela = tk.Toplevel(self.janela)
        janela.title("Prévia — cada retângulo deve conter um valor completo")
        label = ttk.Label(janela)
        label.foto = ImageTk.PhotoImage(foto, master=janela)
        label.configure(image=label.foto)
        label.pack()

    def _salvar(self):
        try:
            tabela = self._validar()
        except ValueError as erro:
            messagebox.showerror("Confira os cantos", str(erro), parent=self.janela)
            return
        self.aplicar(tabela.pontos.tolist(), len(tabela.linhas))
        self.janela.destroy()
