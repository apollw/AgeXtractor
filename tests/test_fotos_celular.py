import json
from pathlib import Path
import tempfile
import unittest

import cv2

from agextractor.extracao import CATEGORIAS, caminhos_imagens, executar_extracao
from agextractor.layout import preparar_tabela, carregar_imagem


FIXTURES = Path(__file__).parent / "fixtures" / "fotos_celular"


class FotosCelular(unittest.TestCase):
    def test_localiza_cinco_tabelas_e_detecta_quantidade_incorreta(self):
        for nome, _, modulo in CATEGORIAS:
            with self.subTest(categoria=nome):
                caminho = FIXTURES / f"{nome}.jpeg"
                tabela = preparar_tabela(caminho, 4)
                self.assertEqual(len(tabela.linhas), 4)
                self.assertEqual(len(tabela.colunas(modulo.colunas)), len(modulo.colunas))
                with self.assertRaisesRegex(ValueError, "Detectei 4"):
                    preparar_tabela(caminho, 6)

    def test_escala_e_margens_nao_dependem_da_resolucao_original(self):
        with tempfile.TemporaryDirectory() as pasta:
            for largura in (1280, 1920):
                for nome, _, modulo in CATEGORIAS:
                    with self.subTest(largura=largura, categoria=nome):
                        original = carregar_imagem(FIXTURES / f"{nome}.jpeg")
                        imagem = cv2.resize(original, (largura, round(original.shape[0] * largura / original.shape[1])))
                        imagem = cv2.copyMakeBorder(imagem, 70, 40, 90, 30, cv2.BORDER_CONSTANT, value=(30,30,30))
                        caminho = Path(pasta) / "redimensionada.png"
                        cv2.imwrite(str(caminho), imagem)
                        tabela = preparar_tabela(caminho, 4)
                        self.assertEqual(len(tabela.colunas(modulo.colunas)), len(modulo.colunas))

    def test_ocr_real_fotos_contra_transcricao_visual_independente(self):
        esperado = json.loads((FIXTURES / "referencia_manual.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as pasta:
            eventos = []
            obtido = executar_extracao(4, caminhos_imagens(FIXTURES), Path(pasta) / "resultado.json", eventos.append)
        avisos = {(a["jogador"],a["categoria"],a["campo"]) for a in obtido.get("avisos",[])}
        corretos = 0
        for real, referencia in zip(obtido["jogadores"], esperado["jogadores"], strict=True):
            for nome, _, _ in CATEGORIAS:
                for campo, valor in referencia[nome].items():
                    chave = (real["jogador"],nome,campo)
                    with self.subTest(campo=chave):
                        if real[nome][campo] is None:
                            self.assertIn(chave, avisos)
                        else:
                            self.assertEqual(real[nome][campo], valor)
                            corretos += 1
        # Horários cortados podem continuar nulos com aviso; quando o OCR obtém
        # consenso suficiente, o valor precisa coincidir com a leitura visual.
        self.assertGreaterEqual(corretos, 110)
        self.assertEqual(eventos[-1].percentual, 100)
        self.assertEqual(len({e.concluidas for e in eventos}), 118)
