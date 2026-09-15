# Imagens de referência para testes de OCR

Os testes de regressão esperam `placar.jpeg`, `militar.jpeg`, `economia.jpeg`, `tecnologia.jpeg` e `sociedade.jpeg` da partida de seis jogadores transcrita em `../resultado_esperado.json`.

Essas imagens não estavam mais presentes no projeto durante a reorganização. Por isso, os dois testes de OCR real são explicitamente ignorados enquanto os arquivos estiverem ausentes. Os testes de fluxo, interface e configuração continuam independentes desses prints.

Para reativar a regressão de 180 campos, recoloque aqui as cinco imagens originais. Não use prints de outra partida com o mesmo resultado esperado. Imagens de novas extrações pertencem a `dados/entrada/` ou à pasta escolhida pelo usuário.
