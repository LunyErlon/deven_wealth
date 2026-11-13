# Guia de Compilação: Deven Wealth para Executável (.exe)

Este guia explica como compilar o **Deven Wealth** em um arquivo executável autônomo para Windows (`.exe`), permitindo que qualquer pessoa baixe e use sem precisar instalar o Python manualmente.

---

## 🔒 1. Segurança e Privacidade Antes da Compilação

O código do Deven Wealth foi 100% higienizado:
- **Sem tokens hardcoded:** O token da Brapi é cadastrado pelo próprio usuário no primeiro uso e salvo com criptografia no banco de dados local.
- **Sem dados pessoais:** Nome e saudações são dinâmicos com base no perfil cadastrado (`perfil_nome`) ou "Investidor".
- **Sem banco de dados embutido:** O `.gitignore` ignora todos os arquivos `.db`, `.enc` e backups `.dwb`. O executável gerado não conterá nenhuma informação privada do desenvolvedor. Quando outro usuário abrir o `.exe`, o sistema apresentará a tela de boas-vindas para criar o cofre e definir a senha-mestra dele.

---

## ⚡ 2. Compilação Rápida em 1 Clique

Disponibilizamos scripts prontos na raiz do repositório:

- **Via Prompt / Duplo-clique:** Execute o arquivo `compilar.bat`.
- **Via PowerShell:** Execute o script `.\compilar.ps1`.

O script faz tudo sozinho:
1. Detecta o ambiente virtual (`.venv`).
2. Garante que o `pyinstaller` está instalado.
3. Executa a compilação com todas as bibliotecas necessárias (`matplotlib`, `qtawesome`, `packaging`, etc.) e os assets visuais.
4. Gera a pasta pronta para distribuição em `dist\DevenWealth\`.

---

## 🛠️ 3. Compilação Manual via Linha de Comando

Se preferir executar o comando manualmente pelo terminal:

```powershell
# 1. Instalar o PyInstaller
pip install pyinstaller

# 2. Compilar
python -m PyInstaller --clean --noconsole --name "DevenWealth" `
    --icon "gerenciador\assets\Logo_Principal.png" `
    --add-data "gerenciador\assets;assets" `
    --hidden-import "packaging.version" `
    --hidden-import "openpyxl" `
    --hidden-import "matplotlib.backends.backend_qtagg" `
    --hidden-import "ofxparse" `
    --hidden-import "yfinance" `
    --collect-all "qtawesome" `
    gerenciador\main.py
```

### Explicação dos Parâmetros:
- `--noconsole`: Oculta a janela preta do terminal do Windows ao abrir o app.
- `--name "DevenWealth"`: Nome do executável (`DevenWealth.exe`).
- `--icon`: Aplica o ícone oficial da DEVEN no executável.
- `--add-data "gerenciador\assets;assets"`: Embutir as imagens e logos necessários para a interface.
- `--collect-all "qtawesome"`: Garante que as fontes de ícones do FontAwesome/MaterialIcons sejam empacotadas.
- `--hidden-import`: Inclui módulos carregados dinamicamente em tempo de execução.

---

## 📦 4. Como Distribuir para os Usuários (GitHub Releases)

1. Após a compilação, vá até a pasta `dist\DevenWealth`.
2. Clique com o botão direito na pasta `DevenWealth` e selecione **Enviar para ➔ Pasta compactada (zip)** (ou use 7-Zip/WinRAR).
3. Renomeie o arquivo gerado para algo como `DevenWealth-v0.2.0-Windows.zip`.
4. No GitHub, vá na sua release e anexe o arquivo `.zip` na seção de **Assets**.
5. Qualquer pessoa só precisará baixar o `.zip`, descompactar e dar dois cliques em `DevenWealth.exe`!
