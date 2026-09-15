import gc
import json
from pathlib import Path
import shutil
import tempfile
import time
import tkinter as tk
import unittest
from unittest.mock import patch

from agextractor.extracao import ExtracaoCancelada
from agextractor.interfaces.gui import Aplicacao


RAIZ = Path(__file__).resolve().parents[1]


class InterfaceGrafica(unittest.TestCase):
    def setUp(self):
        try:
            self.janela = tk.Tk()
        except tk.TclError as erro:
            self.skipTest(f"Teste gráfico requer Tk e sessão de desktop: {erro}")
        self.janela.withdraw()
        self.app = Aplicacao(self.janela)
        self.temporario = tempfile.TemporaryDirectory(prefix="agextractor-gui-")
        self.addCleanup(self.temporario.cleanup)
        self.addCleanup(self.limpar_interface)
        self.pasta = Path(self.temporario.name)
        self.destino = self.pasta / "resultado selecionado.json"
        self.app.destino.set(str(self.destino))
        for nome, variavel in self.app.caminhos.items():
            arquivo = self.pasta / f"captura com acentuação {nome}.jpeg"
            # Erro e cancelamento usam um extrator simulado; não dependem de imagens.
            arquivo.touch()
            variavel.set(str(arquivo))

    def limpar_interface(self):
        if self.app.executando:
            self.app.cancelar()
            self.aguardar()
        self.app._fechar()
        self.app = None
        self.janela = None
        # Destrutores Tcl/Tk precisam rodar na thread principal, antes de
        # iniciar a thread de OCR do próximo teste com uma nova janela.
        gc.collect()

    def aguardar(self):
        limite = time.monotonic() + 120
        atualizacoes = 0
        percentuais = set()
        while self.app.executando and time.monotonic() < limite:
            self.janela.update()
            atualizacoes += 1
            percentuais.add(float(self.app.barra["value"]))
            time.sleep(0.01)
        self.assertFalse(self.app.executando, "Extração excedeu o tempo de teste")
        self.app.trabalhador.join(timeout=2)
        self.assertFalse(self.app.trabalhador.is_alive())
        return atualizacoes, percentuais

    def test_interface_com_ocr_real_preserva_os_180_campos(self):
        fixtures = RAIZ / "tests" / "fixtures"
        faltantes = [nome for nome in self.app.caminhos if not (fixtures / "imagens" / f"{nome}.jpeg").is_file()]
        if faltantes:
            self.skipTest("Imagens de referência ausentes em tests/fixtures/imagens: " + ", ".join(faltantes))
        for nome, variavel in self.app.caminhos.items():
            shutil.copy2(fixtures / "imagens" / f"{nome}.jpeg", variavel.get())
        with patch("agextractor.interfaces.gui.messagebox.showerror") as erro:
            self.app.iniciar()
            self.assertEqual(str(self.app.iniciar_botao["state"]), "disabled")
            atualizacoes, percentuais = self.aguardar()
            erro.assert_not_called()
        esperado = json.loads((fixtures / "resultado_esperado.json").read_text())
        self.assertEqual(json.loads(self.destino.read_text()), esperado)
        self.assertGreater(atualizacoes, 100)
        self.assertGreater(len(percentuais), 30)
        self.assertEqual(float(self.app.barra["value"]), 100)
        self.assertIn("Concluído", self.app.status.get())
        self.assertEqual(str(self.app.iniciar_botao["state"]), "normal")

    def test_cancelamento_reabilita_interface(self):
        def executar(*args, **kwargs):
            self.app.cancelamento.wait(2)
            raise ExtracaoCancelada("Extração cancelada")

        with patch("agextractor.interfaces.gui.executar_extracao", side_effect=executar):
            self.app.iniciar()
            self.app.cancelar()
            self.aguardar()
        self.assertEqual(self.app.status.get(), "Extração cancelada")
        self.assertEqual(str(self.app.iniciar_botao["state"]), "normal")
        self.assertFalse(self.destino.exists())

    def test_erro_reabilita_interface_e_informa_usuario(self):
        with patch("agextractor.interfaces.gui.executar_extracao", side_effect=RuntimeError("OCR indisponível")):
            with patch("agextractor.interfaces.gui.messagebox.showerror") as erro:
                self.app.iniciar()
                self.aguardar()
                erro.assert_called_once()
        self.assertEqual(str(self.app.iniciar_botao["state"]), "normal")
        self.assertLess(float(self.app.barra["value"]), 100)
        self.assertFalse(self.destino.exists())

    def test_conclusao_com_pendencias_e_regiao_encaminhada(self):
        self.app.regioes["placar"] = [[1,1],[100,1],[100,80],[1,80]]
        with patch("agextractor.interfaces.gui.executar_extracao", return_value={"avisos": [{"campo": "madeira"}]}) as extrair:
            self.app.iniciar()
            self.aguardar()
        self.assertEqual(extrair.call_args.kwargs["regioes"], self.app.regioes)
        self.assertIn("1 campos precisam de revisão", self.app.status.get())
        self.app.caminhos["placar"].set("outra.png")
        self.assertNotIn("placar", self.app.regioes)

    def test_ajuste_visual_aplica_cantos_e_quantidade(self):
        from agextractor.interfaces.ajuste import AjusteTabela
        from agextractor.extratores.placar import colunas
        caminho = RAIZ / "tests/fixtures/fotos_celular/placar.jpeg"
        aplicados = []
        dialogo = AjusteTabela(self.janela, caminho, colunas, None, lambda p,q: aplicados.append((p,q)))
        dialogo._previa()
        dialogo._salvar()
        self.assertEqual(aplicados[0][1], 4)
        self.assertEqual(len(aplicados[0][0]), 4)


if __name__ == "__main__":
    unittest.main()
