# Guia de Compilação Multiplataforma: Windows, Linux e macOS

Este guia detalha o passo a passo completo para compilar o **Deven Wealth** em executáveis autônomos para **Windows** (`.exe`), **Linux** (binário ELF / AppImage) e **macOS** (`.app` para MacBooks e Macs de mesa).

---

## 🔒 1. Segurança e Privacidade Garantidas
Antes da compilação, o código foi totalmente higienizado:
- **Zero tokens no código:** O token da Brapi agora é preenchido pelo usuário final na criação do cofre e criptografado localmente.
- **Zero dados pessoais:** O nome e saudações são dinâmicos com base no perfil cadastrado (`perfil_nome`) ou "Investidor".
- **Sem bancos inclusos:** O `.gitignore` bloqueia qualquer arquivo `.db`, `.enc` ou `.dwb`. O executável gerado inicia limpo, pronto para o usuário cadastrar sua própria senha-mestra.

---

## 💻 2. Como Funciona a Compilação em Cada Sistema

O **PyInstaller** não realiza *cross-compilation* (compilação cruzada direta entre sistemas diferentes), pois ele empacota as bibliotecas dinâmicas C e os binários nativos do sistema onde está sendo executado (`.dll` no Windows, `.so` no Linux e `.dylib` no macOS).

Por isso, você tem **duas formas de compilar**:
1. **Localmente:** Rodando o script específico no sistema operacional correspondente.
2. **Na Nuvem (100% Automático via GitHub Actions):** O GitHub compila os três sistemas simultaneamente nos servidores dele e anexa os arquivos prontos na sua Release!

---

## 🪟 3. Compilação no Windows (.exe)

### Método Rápido em 1 Clique:
- Dê dois cliques em [compilar.bat](file:///g:/deven_wealth/compilar.bat) ou execute no PowerShell:
```powershell
.\compilar.ps1
```

### Método Manual via Terminal:
```powershell
pip install pyinstaller
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
- **Saída:** Pasta `dist\DevenWealth\DevenWealth.exe`.
- **Distribuição:** Compacte a pasta `DevenWealth` em `DevenWealth-Windows.zip`.

---

## 🐧 4. Compilação no Linux (Binário ELF / AppImage)

### Método Rápido via Script:
Execute no terminal Linux:
```bash
chmod +x compilar_linux.sh
./compilar_linux.sh
```

### Método Manual via Terminal:
```bash
pip install pyinstaller
python3 -m PyInstaller --clean --noconsole --name "DevenWealth" \
    --add-data "gerenciador/assets:assets" \
    --hidden-import "packaging.version" \
    --hidden-import "openpyxl" \
    --hidden-import "matplotlib.backends.backend_qtagg" \
    --hidden-import "ofxparse" \
    --hidden-import "yfinance" \
    --collect-all "qtawesome" \
    gerenciador/main.py
```
- **Saída:** Pasta `dist/DevenWealth/DevenWealth`.
- **Distribuição:** Compacte a pasta em `.tar.gz`:
```bash
tar -czvf DevenWealth-Linux.tar.gz -C dist DevenWealth
```

---

## 🍎 5. Compilação no macOS (MacBooks e Macs de Mesa)

### Método Rápido via Script:
Execute no terminal do macOS:
```bash
chmod +x compilar_mac.sh
./compilar_mac.sh
```

### Método Manual via Terminal:
```bash
pip install pyinstaller
python3 -m PyInstaller --clean --noconsole --name "DevenWealth" \
    --windowed \
    --icon "gerenciador/assets/Logo_Principal.png" \
    --add-data "gerenciador/assets:assets" \
    --hidden-import "packaging.version" \
    --hidden-import "openpyxl" \
    --hidden-import "matplotlib.backends.backend_qtagg" \
    --hidden-import "ofxparse" \
    --hidden-import "yfinance" \
    --collect-all "qtawesome" \
    gerenciador/main.py
```
- **Saída:** Pacote de aplicativo macOS `dist/DevenWealth.app`.
- **Distribuição:** Compacte o aplicativo preservando os links simbólicos do macOS:
```bash
cd dist && zip -r -y ../DevenWealth-macOS.zip DevenWealth.app && cd ..
```
No Mac, o usuário só precisa descompactar e arrastar o `DevenWealth.app` para a pasta **Aplicativos (Applications)**!

---

## ☁️ 6. Compilação Automática dos 3 Sistemas no GitHub (Recomendado!)

Configuramos o fluxo de integração contínua em `.github/workflows/build_releases.yml`.

### Como Funciona:
Você **não precisa ter um computador Mac ou Linux em casa**:
1. No seu repositório no GitHub, quando você publicar uma nova **Release** (ex: `v0.2.0`), os servidores gratuitos do GitHub disparam 3 máquinas virtuais em paralelo:
   - Um servidor **Windows** que gera `DevenWealth-Windows.zip`.
   - Um servidor **Ubuntu Linux** que gera `DevenWealth-Linux.tar.gz`.
   - Um servidor **macOS Apple Silicon** que gera `DevenWealth-macOS.zip`.
2. Em poucos minutos, os 3 arquivos aparecem automaticamente anexados para download na sua Release no GitHub!

### Disparo Manual (Sem publicar release):
Se quiser gerar os pacotes a qualquer momento:
1. Acesse seu repositório no GitHub ➔ Aba **Actions**.
2. Clique no workflow **Build Multiplataforma (Windows, Linux, macOS)** no menu à esquerda.
3. Clique no botão **Run workflow** ➔ **Run workflow**.
