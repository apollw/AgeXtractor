# Aplicativo Windows do AgeExtractor

## Pacote para uso

O build gera uma distribuição portátil para Windows x64:

```text
dist/
├── AgeExtractor-Windows-x64.zip
├── AgeExtractor-Windows-x64.zip.sha256
└── AgeExtractor/
    ├── AgeExtractor.exe
    ├── _internal/
    ├── licencas/
    ├── LEIA-ME.txt
    └── VERSOES.json
```

Extraia o ZIP inteiro e abra `AgeExtractor.exe`. A pasta `_internal` precisa permanecer ao lado do executável. O ZIP é o arquivo para copiar para outro computador; somente o EXE não contém todos os recursos.

O pacote inclui o interpretador Python, Tkinter/Tcl/Tk, OpenCV, NumPy, Pillow, pytesseract, o executável Tesseract, suas DLLs e `eng.traineddata`. O usuário final não precisa instalar a IDE, Python ou Tesseract. Esse é o modelo de distribuição em pasta do PyInstaller. [Documentação do PyInstaller](https://pyinstaller.org/en/stable/operating-mode.html).

Esta entrega é portátil, sem assistente de instalação, atalhos no menu Iniciar ou atualização automática. O executável não recebe uma assinatura digital neste build. A interface e a extração continuam locais; a versão web não faz parte deste pacote.

## Resultados e arquivos pessoais

No executável, as pastas padrão ficam em **Documentos\AgeExtractor\entrada** e **Documentos\AgeExtractor\saida**. O programa consulta o caminho de Documentos do Windows, incluindo redirecionamento para OneDrive. É possível selecionar imagens e salvar o JSON em outros locais pela interface.

Os resultados ficam separados da pasta do programa, permitindo substituir a versão portátil sem apagar os dados. Em desenvolvimento, os padrões continuam sendo `dados/entrada/` e `dados/saida/` dentro do projeto.

Os recursos internos são localizados a partir de `sys._MEIPASS` quando o programa está empacotado. Eles não são usados para gravar resultados do usuário. [Informações de execução do PyInstaller](https://www.pyinstaller.org/en/stable/runtime-information.html).

O pacote usa prioritariamente seu próprio Tesseract e define `TESSDATA_PREFIX` apenas no processo da aplicação. Em desenvolvimento, aceita `TESSERACT_CMD`, procura a instalação padrão em Program Files e, depois, o executável no PATH. O modelo em inglês é usado para as estatísticas numéricas e para reconhecer Sim/Não e Yes/No. Consulte [Extração de fotos](EXTRACAO_DE_FOTOS.md) para a validação atual e seus limites.

O pacote não inclui prints, o resultado pessoal existente, fixtures de partidas nem a documentação histórica do projeto.

## Gerar uma nova versão

Execute o build no Windows com Python de 64 bits. Nesta entrega foram usados Python 3.14.5, PyInstaller 6.22.2 e Tesseract 5.5.3.20260724. As versões e hashes do motor e do modelo são registrados em `VERSOES.json` dentro do pacote.

Na raiz do projeto:

```powershell
python -m venv .venv-build
.\.venv-build\Scripts\python.exe -m pip install -r empacotamento/requirements.txt
.\.venv-build\Scripts\python.exe empacotamento/build_windows.py
```

O computador que gera o pacote precisa ter o Tesseract completo instalado. Se estiver em outro local:

```powershell
.\.venv-build\Scripts\python.exe empacotamento/build_windows.py --tesseract "D:\Ferramentas\Tesseract-OCR"
```

O arquivo `empacotamento/AgeExtractor.spec` define a coleta dos componentes, os metadados dos pacotes e a geração sem console. O script de build acrescenta instruções, avisos disponíveis, manifesto de versões e o ZIP com checksum SHA-256. Builds anteriores em `build/` e `dist/AgeExtractor/` podem ser substituídos; não guarde resultados de partidas nessas pastas. A configuração por `.spec` é o mecanismo do PyInstaller para incluir arquivos e bibliotecas adicionais. [Documentação de arquivos spec](https://pyinstaller.org/en/stable/spec-files.html).

`build/`, `dist/` e `.venv-build/` são artefatos locais ignorados pelo Git. O código necessário para reproduzir o empacotamento fica em `empacotamento/`.

## Verificação do pacote

Depois do build:

```powershell
python -m unittest discover -s tests -v
.\.venv-build\Scripts\python.exe empacotamento/testar_pacote.py
```

O teste do pacote verifica o checksum do ZIP, extrai o aplicativo em outra pasta com espaços e acentos e executa o próprio EXE. Remove Python e Tesseract do PATH e fornece caminhos externos inválidos de OCR para conferir que os recursos internos são usados. Também abre a interface oculta, verifica os cinco seletores, testa escrita na pasta do usuário e realiza OCR real de uma imagem sintética contendo `12345`.

O relatório é salvo em `build/validacao-pacote.json`. A pasta temporária do teste é removida ao final; os caminhos registrados nela servem como evidência da execução e não como destinos permanentes.

A atualização acrescenta regressão de OCR com as fotos de quatro jogadores, testes de localização após redimensionamento e testes do ajuste visual. As duas regressões antigas continuam ignoradas pela ausência dos prints originais. O teste do ZIP verifica interface inicializada, escrita disponível e leitura `12345` feita pelo Tesseract dentro do pacote. O arquivo ZIP tem aproximadamente 147 MiB.

O teste automatizado valida os componentes no Windows da máquina de build, sem substituir uma verificação em outro computador ou máquina virtual limpa. Os testes da partida original de 180 campos continuam dependendo das cinco imagens de referência, atualmente ausentes. O autoteste de texto sintético não substitui essa regressão visual.

## Diagnóstico de abertura

Falhas capturadas na inicialização são registradas em `Documentos\AgeExtractor\erro-inicializacao.log`. Para diagnóstico técnico, o executável também aceita:

```powershell
.\AgeExtractor.exe --autoteste "C:\pasta-existente\diagnostico.json"
```

O autoteste usa uma janela oculta e grava um relatório; não abre o fluxo normal de seleção de imagens. A variável de ambiente `AGEXTRACTOR_DADOS` pode substituir a pasta de dados do executável, recurso usado pelo teste de distribuição para não escrever nos documentos reais do usuário.
