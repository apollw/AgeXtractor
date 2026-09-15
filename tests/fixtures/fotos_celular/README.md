# Referência das fotos de celular

Fotos fornecidas em `dados/entrada` em setembro de 2026, copiadas sem edição.
`pontuação.jpeg` foi copiada com o nome `placar.jpeg` neste conjunto.

`referencia_manual.json` foi transcrito por inspeção visual, independentemente
do resultado do OCR. São quatro jogadores e 120 campos. Três horários têm
dígitos finais parcialmente cortados na própria imagem e estão representados
por `null`: jogador 3 / idade_castelos e jogador 4 / idade_feudal e idade_imperial.
Esses valores não devem ser inferidos a partir dos candidatos do OCR.

O teste permite abstenções sinalizadas, exige pelo menos 110 valores corretos
e rejeita qualquer valor preenchido diferente da referência. As fotos não
substituem as capturas antigas de seis jogadores e não entram no executável.
