import json
from pathlib import Path
import tempfile
import threading
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from agextractor.extracao import CATEGORIAS, ExtracaoCancelada, executar_categoria, executar_extracao


class FluxoCompartilhado(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.pasta = Path(self.temporario.name)
        self.caminhos = {}
        for nome, _, _ in CATEGORIAS:
            arquivo = self.pasta / f"print escolhido {nome}.png"
            arquivo.touch()
            self.caminhos[nome] = str(arquivo)
        self.destino = self.pasta / "saida escolhida.json"
        self.destino.write_text("resultado anterior", encoding="utf-8")

    def extratores_simulados(self, pilha):
        mocks = []
        for nome, _, modulo in CATEGORIAS:
            def simular(caminho, quantidade, ao_processar_celula, colunas=modulo.colunas):
                for i in range(1, quantidade + 1):
                    for coluna in colunas:
                        ao_processar_celula(i, coluna)
                return [{"jogador": i, "valor": i} for i in range(1, quantidade + 1)]
            mocks.append(pilha.enter_context(patch.object(modulo, f"extrair_{nome}", side_effect=simular)))
        return mocks

    def test_quantidade_e_caminhos_personalizados_com_progresso_real(self):
        # Verifica encaminhamento e consolidação; não mede OCR de layouts 2/8.
        for quantidade in (2, 8):
            with self.subTest(quantidade=quantidade), ExitStack() as pilha:
                mocks = self.extratores_simulados(pilha)
                eventos = []

                def receber(evento):
                    eventos.append(evento)
                    if evento.percentual == 100:
                        self.assertEqual(json.loads(self.destino.read_text())["quantidade_jogadores"], quantidade)

                resultado = executar_extracao(quantidade, self.caminhos, self.destino, receber)
                self.assertEqual(len(resultado["jogadores"]), quantidade)
                for (nome, _, _), mock in zip(CATEGORIAS, mocks):
                    self.assertEqual(mock.call_args.args, (str(Path(self.caminhos[nome]).resolve()), quantidade))
                total = quantidade * 29 + 1
                self.assertEqual(eventos[-1].concluidas, total)
                self.assertEqual(sorted(set(e.concluidas for e in eventos)), list(range(total + 1)))
                self.assertEqual(json.loads(self.destino.read_text()), resultado)

    def test_cancelamento_preserva_saida_anterior(self):
        cancelamento = threading.Event()
        with ExitStack() as pilha:
            self.extratores_simulados(pilha)
            with self.assertRaises(ExtracaoCancelada):
                executar_extracao(
                    6, self.caminhos, self.destino,
                    lambda evento: cancelamento.set() if evento.concluidas == 1 else None,
                    cancelamento.is_set,
                )
        self.assertEqual(self.destino.read_text(), "resultado anterior")

    def test_falha_ao_salvar_preserva_saida_e_remove_temporario(self):
        with ExitStack() as pilha:
            self.extratores_simulados(pilha)
            pilha.enter_context(patch("agextractor.extracao.os.replace", side_effect=PermissionError("arquivo ocupado")))
            with self.assertRaises(PermissionError):
                executar_extracao(6, self.caminhos, self.destino)
        self.assertEqual(self.destino.read_text(), "resultado anterior")
        self.assertEqual(list(self.pasta.glob("*.tmp")), [])

    def test_entradas_invalidas_nao_alteram_saida(self):
        for quantidade in (1, 9, True, "6"):
            with self.subTest(quantidade=quantidade), self.assertRaises(ValueError):
                executar_extracao(quantidade, self.caminhos, self.destino)
        with self.assertRaisesRegex(ValueError, "Militar"):
            executar_extracao(6, {**self.caminhos, "militar": ""}, self.destino)
        with self.assertRaisesRegex(ValueError, "entrada"):
            executar_extracao(6, self.caminhos, self.caminhos["placar"])
        self.assertEqual(self.destino.read_text(), "resultado anterior")

    def test_categoria_isolada_devolve_fragmento_com_progresso(self):
        eventos = []
        def simular(caminho, quantidade, ao_processar_celula, pontos_tabela):
            for numero in range(1, quantidade + 1):
                for campo in ("unidades_mortas", "unidades_perdidas", "construcoes_destruidas",
                              "construcoes_perdidas", "unidades_convertidas", "maior_exercito"):
                    ao_processar_celula(numero, campo)
            return [{"jogador": numero, "unidades_mortas": numero} for numero in range(1, quantidade + 1)]

        with patch("agextractor.extracao.militar.extrair_militar", side_effect=simular):
            resultado = executar_categoria(
                "militar", 2, self.caminhos["militar"], eventos.append,
                pontos=[[10, 10], [900, 10], [900, 600], [10, 600]],
            )

        self.assertEqual(resultado["categoria"], "militar")
        self.assertEqual(resultado["jogadores"][1]["militar"]["unidades_mortas"], 2)
        self.assertEqual(eventos[-1].percentual, 100)


if __name__ == "__main__":
    unittest.main()
