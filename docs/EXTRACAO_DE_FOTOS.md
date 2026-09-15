# Extração de fotos e capturas

O problema não era somente a resolução: as fotos novas têm 1599 × 899 pixels,
mas a tabela aparece deslocada e inclinada. Havia ainda interferência colorida
da foto do monitor, estrelas de destaque e quatro jogadores em vez de seis.

## Funcionamento atual

1. Localiza a borda externa da tabela e corrige a perspectiva dos quatro cantos.
2. Normaliza a tabela para uma área de trabalho comum e detecta as linhas
   preenchidas. Quando a quantidade de jogadores já foi informada, procura uma
   sequência completa no espaçamento esperado e usa também as cores e o texto
   da área de identificação para não confundir cabeçalhos de duas linhas com
   jogadores.
3. Se não houver evidência suficiente em todas as posições informadas, compara
   a detecção livre com a quantidade esperada e interrompe a extração com uma
   mensagem; linhas vazias não viram jogadores fictícios.
4. Remove estrelas de destaque com filtro de tamanho e cor, amplia cada célula
   e compara leituras binarizadas em três escalas. Para números/textos sem
   consenso, pode tentar também segmentação de palavra com margens reduzidas.
5. Valida números, percentuais, horários, tributos e os textos Sim/Não/Yes/No.
   Leituras divergentes ou insuficientes ficam como `null`. Confere também a
   soma das categorias do placar contra a pontuação total.

Isso usa processamento local com OpenCV e Tesseract. As fotos não são enviadas
a serviços externos. O progresso continua sendo atualizado por célula e a
interface permanece disponível durante a execução.

## Usar na interface

Selecione a imagem de cada categoria e informe o número de jogadores. Nas
fotos fornecidas são **4 jogadores**; `pontuação.jpeg` corresponde a Placar.
A localização da tabela é automática. Para conferir ou corrigir a região,
clique em **Ajustar tabela**, arraste os quatro cantos da borda externa,
incluindo o cabeçalho e a legenda inferior, e abra **Prévia das células**.
Cada retângulo vermelho deve conter um valor completo.

Ao aplicar, a quantidade de jogadores detectada preenche o seletor. O ajuste
fica associado à imagem durante a sessão; trocar seu caminho descarta o ajuste.
As imagens originais são preservadas. A conclusão informa quantos campos têm
avisos. A revisão dos valores é feita consultando as fotos e o JSON; o programa
ainda não tem um editor de valores extraídos.

No terminal, `pontuação.jpeg`, `pontuacao.jpeg` e `score.jpeg` são alternativas
para `placar.jpeg`. Exemplo para esta partida:

```powershell
python main.py --jogadores 4 --saida dados/saida/resultado_fotos_celular.json
```

## Contrato JSON para a aplicação consumidora

Permanecem `quantidade_jogadores`, `jogadores` e os cinco grupos de estatísticas.
Agora qualquer estatística pode ser `null` quando não é possível lê-la com
segurança. **Não converta `null` em zero, string vazia ou `false`.** Zero e falso
são valores válidos diferentes de informação ausente.

Quando houver pendências, a raiz terá uma lista opcional `avisos`. Cada item
identifica `jogador`, `categoria`, `campo`, `motivo` e `candidatos`. Os candidatos
contêm texto, confiança fornecida pelo Tesseract e método usado; não são valores
confirmados nem probabilidades calibradas. Um aviso também pode acompanhar um
valor preenchido, por exemplo quando a soma do placar não coincide com o total.

A aplicação consumidora deve solicitar o arquivo `.json` completo exportado,
validar a estrutura e apresentar as pendências antes de fazer uma análise
definitiva. Deve pedir ao usuário que confira os campos apontados na imagem ou
forneça uma captura melhor, sem escolher automaticamente um candidato. Análises
parciais devem explicitar os dados ausentes. O índice do jogador representa a
posição da linha; não identifica uma conta e `sobreviveu` não indica vitória.

## Validação e limites

Há uma referência transcrita visualmente das cinco fotos em
`tests/fixtures/fotos_celular/`. Os testes verificam OCR real, detecção das cinco
tabelas, quantidade incorreta e localização após redimensionamento para 1280 e
1920 pixels de largura com margens extras. Os testes de escala validam geometria,
não a precisão de OCR em todas essas resoluções. Há também regressões sintéticas
para tabelas de dois jogadores: elas verificam que uma segunda linha de cabeçalho
não seja contada como participante e que posições vazias continuem rejeitadas.

A localização ainda pressupõe a estrutura de tabela desta tela do jogo. Outros
temas, cabeçalhos, layouts, rotações fortes, ausência da borda ou pouca nitidez
podem exigir ajuste ou uma nova captura. A seleção manual corrige a geometria;
ela não recria dígitos cortados nem recupera informação perdida por desfoque.
Concordância de OCR reduz erros, mas não garante uma transcrição perfeita.

Na execução das fotos fornecidas, 114 dos 120 campos foram preenchidos e
coincidiram com a referência visual. Seis ficaram como `null`, com avisos:

| Jogador | Categoria / campo | Conferência visual |
| --- | --- | --- |
| 1 | placar / tecnologia | 3975; houve divergência entre leituras |
| 3 | tecnologia / idade_castelos | Dígito final parcialmente cortado |
| 4 | militar / unidades_mortas | 157; houve divergência entre leituras |
| 4 | economia / madeira | 39553; houve divergência entre leituras |
| 4 | tecnologia / idade_feudal | Dígito final parcialmente cortado |
| 4 | tecnologia / idade_imperial | Dígito final parcialmente cortado |

O resultado automático está em `dados/saida/resultado_fotos_celular.json`.
Os valores conferidos acima não foram inseridos manualmente na saída para
mascarar as abstenções do OCR. Esta medição vale para a partida fornecida,
não representa uma garantia de precisão em outras imagens.

As capturas originais de seis jogadores continuam ausentes. Sua regressão
permanece marcada como ignorada, sem alegar que a compatibilidade visual com
elas foi comprovada nesta alteração.
