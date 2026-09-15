import unittest

import cv2
import numpy as np

from agextractor.layout import _centros_por_quantidade


class DeteccaoLinhas(unittest.TestCase):
    def test_quantidade_conhecida_ignora_cabecalho_de_duas_linhas(self):
        imagem = np.full((899, 1600, 3), 225, dtype=np.uint8)

        # Segunda linha de um cabeçalho denso, próxima da primeira linha real.
        for x in range(710, 1230, 75):
            cv2.rectangle(imagem, (x, 232), (x + 45, 241), (35, 35, 35), -1)

        # Duas linhas reais deslocadas 19 px em relação à grade de referência.
        for y, cor in ((278, (30, 150, 65)), (319, (170, 45, 170))):
            cv2.rectangle(imagem, (250, y - 10), (610, y + 10), cor, -1)
            for x in range(710, 1230, 90):
                cv2.rectangle(imagem, (x, y - 6), (x + 24, y + 6), (25, 25, 25), -1)

        centros = _centros_por_quantidade(imagem, 2)

        self.assertIsNotNone(centros)
        self.assertTrue(all(abs(real - esperado) <= 1 for real, esperado in zip(centros, (278, 319))))
        self.assertEqual(41, centros[1] - centros[0])

    def test_rejeita_quantidade_sem_evidencia_em_todas_as_linhas(self):
        imagem = np.full((899, 1600, 3), 225, dtype=np.uint8)
        for y in (278, 319):
            cv2.rectangle(imagem, (250, y - 10), (610, y + 10), (30, 150, 65), -1)

        self.assertIsNone(_centros_por_quantidade(imagem, 4))


if __name__ == "__main__":
    unittest.main()
