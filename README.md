# AgeExtractor

Extrai estatísticas de partidas de Age of Empires II a partir de cinco prints e gera um JSON organizado por jogador.

## Executável pronto para Windows

O pacote portátil fica em [dist/AgeExtractor-Windows-x64.zip](dist/AgeExtractor-Windows-x64.zip). Extraia o ZIP inteiro e abra **AgeExtractor.exe** dentro da pasta extraída, mantendo `_internal` ao lado dele. A distribuição inclui Python, interface e Tesseract; o usuário final não precisa instalar essas dependências nem usar uma IDE.

Os resultados do executável são salvos por padrão em **Documentos\AgeExtractor\saida\resultado.json**, ou no destino escolhido na janela. O programa aceita de 2 a 8 jogadores e cinco categorias de imagens, com localização automática da tabela, correção de perspectiva e ajuste visual dos quatro cantos.

Consulte [Empacotamento Windows](docs/EMPACOTAMENTO_WINDOWS.md) para gerar novas versões e validar o ZIP. As instruções abaixo são para executar e desenvolver a partir do código Python.

## Organização

```text
AgeXtractor/
├── AgeExtractor.pyw             # Abre a interface sem console no Windows
├── interface.py                 # Atalho da interface gráfica
├── main.py                      # Atalho do terminal
├── requirements.txt             # Dependências Python
├── empacotamento/               # Build Windows, especificação, testes do ZIP e instruções
├── agextractor/
│   ├── caminhos.py              # Caminhos padrão do projeto
│   ├── extracao.py              # Fluxo compartilhado, progresso e gravação
│   ├── layout.py                # Localização, perspectiva, linhas e colunas
│   ├── jogadores.py             # Referência antiga de coordenadas
│   ├── ocr.py                   # Preparação das células e Tesseract
│   ├── extratores/              # Placar, militar, economia, tecnologia e sociedade
│   ├── interfaces/
│   │   ├── cli.py               # Execução e progresso no terminal
│   │   └── gui.py               # Janela, seleção de arquivos e progresso
│   └── ferramentas/
│       └── analisar_placar.py    # Diagnóstico de textos e coordenadas OCR
├── dados/
│   ├── entrada/                 # Prints usados pelo terminal por padrão
│   └── saida/                   # JSON gerado; resultado existente preservado
├── docs/
│   └── VISAO_GERAL.md           # Análise histórica do negócio e funcionamento
└── tests/
    ├── test_extracao.py         # Regressão do OCR pelo terminal
    ├── test_fluxo.py            # Parâmetros, cancelamento e falhas
    ├── test_interface.py        # Interface e regressão do OCR pela janela
    ├── test_organizacao.py      # Imports, atalhos e caminhos
    └── fixtures/
        ├── resultado_esperado.json
        └── imagens/            # Prints originais necessários à regressão
```

O código funcional fica em `agextractor/`; os arquivos de execução na raiz são atalhos pequenos. Os extratores compartilham a detecção da tabela e a leitura das células. Os arquivos de dados ficam separados do código e dos exemplos usados pelos testes.

## Preparação

Instale as bibliotecas no ambiente Python usado para executar o projeto:

```powershell
python -m pip install -r requirements.txt
```

Para executar pelo código, o Tesseract OCR precisa estar instalado separadamente. A configuração em [agextractor/ocr.py](agextractor/ocr.py) aceita `TESSERACT_CMD`, procura a instalação padrão abaixo e, depois, o executável no PATH. No pacote EXE, o OCR já vem incluído.

```text
C:\Program Files\Tesseract-OCR\tesseract.exe
```

A interface requer Tkinter com Tcl/Tk, normalmente incluído na instalação do Python para Windows.

## Interface gráfica

Abra `AgeExtractor.pyw` com duplo clique, se `.pyw` estiver associado ao Python, ou execute na raiz do projeto:

```powershell
python interface.py
```

1. Informe de **2 a 8 jogadores**.
2. Selecione o print correspondente a cada categoria: Placar, Militar, Economia, Tecnologia e Sociedade.
3. Escolha onde salvar o JSON. O padrão é `dados/saida/resultado.json`.
4. Clique em **Iniciar extração** e acompanhe o progresso por célula e o tempo estimado.

As imagens podem estar em outras pastas e ter nomes diferentes. O processamento ocorre em segundo plano; é possível cancelar após a célula em andamento. A saída anterior só é substituída quando a gravação completa termina.

## Terminal

Coloque em `dados/entrada/` os arquivos `placar.jpeg`, `militar.jpeg`, `economia.jpeg`, `tecnologia.jpeg` e `sociedade.jpeg`, e execute:

```powershell
python main.py
```

O padrão continua sendo seis jogadores. O JSON é salvo em `dados/saida/resultado.json` e também impresso em `stdout`; o progresso utiliza `stderr`.

Para escolher outros caminhos ou a quantidade de jogadores:

```powershell
python main.py --entrada "C:\Partidas\prints" --saida "C:\Partidas\partida.json" --jogadores 4
python main.py --help
```

A pasta de saída escolhida precisa existir. Os caminhos padrão são calculados a partir da localização do projeto, independentemente da pasta de onde o programa for chamado. Caminhos relativos informados nos argumentos são resolvidos a partir da pasta de execução. Em outra pasta, invoque o atalho por seu caminho completo, por exemplo `python "C:\caminho\AgeXtractor\main.py"`.

## Diagnóstico e testes

Para imprimir os textos e suas coordenadas no placar, execute a partir da raiz:

```powershell
python -m agextractor.ferramentas.analisar_placar "C:\Partidas\prints\placar.jpeg"
```

Sem argumento, essa ferramenta usa `dados/entrada/placar.jpeg`. As coordenadas impressas se referem à imagem ampliada duas vezes.

Execute os testes a partir da raiz:

```powershell
python -m unittest discover -s tests -v
```

**As imagens de referência antigas continuam ausentes.** Duas regressões de seis jogadores são ignoradas até que os prints originais sejam colocados em `tests/fixtures/imagens/`. A nova regressão de OCR real usa as cinco fotos de celular e uma transcrição visual independente em `tests/fixtures/fotos_celular/`. Não compare referências com imagens de outra partida. Os testes da janela requerem uma sessão gráfica com Tcl/Tk disponível.

## Dados e limites atuais

O JSON mantém `quantidade_jogadores` e a lista `jogadores`, com os grupos `placar`, `militar`, `economia`, `tecnologia` e `sociedade`. São 30 estatísticas por jogador. O identificador `jogador` é a posição na tabela, não um nome ou conta; `sobreviveu` não indica vitória.

As cinco imagens precisam ser da mesma partida e manter a mesma ordem de jogadores. A resolução de entrada não precisa ser exatamente 1600 × 899: a tabela é localizada e alinhada automaticamente. Use **Ajustar tabela** na interface para conferir os recortes. Leituras duvidosas ficam como `null`, com `avisos` no JSON. Consulte [Extração de fotos e contrato JSON](docs/EXTRACAO_DE_FOTOS.md) para funcionamento, uso, testes e limites.

A [visão geral do negócio e funcionamento](docs/VISAO_GERAL.md) preserva a análise feita nas etapas anteriores, incluindo o dicionário de dados e os erros de OCR corrigidos. Para caminhos e comandos atuais, use este README.

Para importar a função de extração em outro código Python:

```python
from agextractor.extracao import executar_extracao
```

## Execução headless para o AgeNexus

O módulo `agextractor.interfaces.server` executa sem Tkinter e escreve somente o contrato JSON em `stdout`. O progresso e eventuais falhas são emitidos como linhas JSON estruturadas em `stderr`, permitindo que o AgeNexus atualize a interface sem misturar diagnósticos ao resultado. Ele recebe uma pasta temporária contendo `placar.jpeg`, `militar.jpeg`, `economia.jpeg`, `tecnologia.jpeg` e `sociedade.jpeg`:

```powershell
python -m agextractor.interfaces.server --entrada "C:\Partida\prints" --jogadores 4
```

O modo servidor também aceita `--regioes caminho.json`. O arquivo deve mapear cada uma das cinco categorias para os quatro cantos da tabela, nas coordenadas da imagem original. Isso permite que a interface web reproduza o ajuste de perspectiva da versão Windows sem criar cópias permanentes das capturas.

Em contêiner Linux, instale `requirements-server.txt` e o executável Tesseract. O AgeNexus fixa uma revisão deste repositório durante o build, cria uma pasta isolada por processamento e remove as imagens após a execução. O JSON continua sujeito à revisão humana antes de preencher ou salvar estatísticas.

Arquivos antigos e documentos que já não estavam presentes não foram recriados. Os novos caminhos substituem os imports diretos dos módulos que antes ficavam na raiz.
