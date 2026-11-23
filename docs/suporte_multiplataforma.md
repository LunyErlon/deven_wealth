# Suporte Multiplataforma: Linux, macOS e iOS

Este documento detalha o suporte e a viabilidade do **Deven Wealth** nos diferentes sistemas operacionais: **Linux**, **macOS** (computadores Apple) e **iOS** (dispositivos móveis iPhone/iPad).

---

## 🐧 1. Linux (100% Compatível)

O Deven Wealth possui **compatibilidade nativa e total** com qualquer distribuição Linux moderna (Ubuntu, Debian, Fedora, Manjaro, Arch, Linux Mint, Pop!_OS, etc.).

### Por que funciona tão bem no Linux?
- O ecossistema **PyQt6 (Qt6)** e o interpretador **Python 3** nasceram e são amplamente otimizados em ambientes Unix/Linux.
- Todas as dependências do projeto (`pandas`, `matplotlib`, `cryptography`, `sqlite3`, `ofxparse`, `requests`, `qtawesome`) possuem compilação nativa para as arquiteturas `x86_64` e `aarch64` (ARM).
- Os caminhos de arquivos e assets no código foram padronizados com `os.path.join` e barras universais (`/`).

### Como Rodar no Linux (Código-Fonte):
```bash
git clone https://github.com/LunyErlon/deven_wealth.git
cd deven_wealth
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python gerenciador/main.py
```

### Como Compilar para Binário Executável no Linux:
Disponibilizamos o script pronto [compilar_linux.sh](file:///g:/deven_wealth/compilar_linux.sh):
```bash
chmod +x compilar_linux.sh
./compilar_linux.sh
```
O script gera o executável autônomo em `dist/DevenWealth/DevenWealth`, pronto para ser empacotado como `.tar.gz` ou convertido em um **AppImage**.

---

## 🍎 2. macOS - Computadores Apple (100% Compatível)

Caso a intenção inclua computadores da Apple (**MacBook**, **Mac Mini**, **iMac** ou **Mac Studio**):
- **PyQt6 roda com perfeição no macOS**, com aceleração gráfica Metal e suporte nativo aos chips Apple Silicon (M1, M2, M3, M4) e processadores Intel.
- O tema escuro *Catppuccin Mocha* integra-se elegantemente à barra de títulos e cantos arredondados do macOS.
- O PyInstaller no macOS gera um pacote de aplicativo oficial `.app` que pode ser envelopado em uma imagem de disco `.dmg`.

---

## 📱 3. iOS - Dispositivos Móveis (iPhone e iPad)

### ⚠️ A Realidade Técnica do PyQt6 no iOS:
O **PyQt6 é um framework construído exclusivamente para Desktops** (telas grandes, suporte a mouse, menus suspensos, atalhos de teclado e tabelas densas). Colocar o código PyQt6 atual diretamente no iOS como um app da App Store **não é viável** pelos seguintes motivos fundamentais:

1. **Políticas Rígidas da Apple (App Store Guidelines)**:
   - A Apple proíbe interpretadores que executem código dinâmico não assinado (política W^X / restrição de JIT em memória).
   - Aplicativos iOS exigem compilação através do ecossistema Xcode, com provisionamento de certificados de desenvolvedor da Apple.
2. **Experiência de Usuário Móvel (UX/UI Touch)**:
   - Uma tela de smartphone (5 a 6 polegadas) não comporta janelas flutuantes de desktop, tabelas de 7 colunas (como a de Rendimentos ou Carteira), caixas de diálogo modais pesadas e menus laterais de clique duplo.
   - Um app mobile requer gestos de toque (arrastar para atualizar, swipe para apagar, cards em coluna única, bottom navigation bar e teclado virtual responsivo).

---

### 💡 Como Trazer o Deven Wealth para o iPhone (Opções Viáveis):

Se o objetivo for gerenciar seus investimentos e despesas pelo iPhone, temos **3 caminhos estratégicos**:

#### Opção A: PWA / Web App Responsivo (Mais Rápida e Elegante)
- **Como Funciona:** Aproveitamos toda a lógica já pronta do Deven Wealth (`db_manager.py`, motor 50/30/20, IRPF, radar de dividendos) conectada a uma interface web leve e responsiva (usando FastAPI no backend e Vue/React ou NiceGUI/Flet no front).
- **No iPhone:** O usuário acessa pelo Safari e clica em **"Compartilhar" ➔ "Adicionar à Tela de Início"**.
- **Resultado:** O Deven Wealth vira um ícone no iPhone, abre em tela cheia (sem barra de navegação do Safari), com visual nativo, suporte a modo escuro e funcionamento instantâneo tanto no iOS quanto no Android!

#### Opção B: Migração Front-End com Flet (Python + Flutter)
- **Como Funciona:** O **Flet** é um framework moderno em Python baseado no **Flutter** (o motor gráfico da Google).
- **Vantagem:** Permite escrever código Python que compila nativamente para **iOS, Android, Windows, Linux, Mac e Web**, compartilhando 100% da mesma base de código.

#### Opção C: App Nativo iOS em Swift / SwiftUI
- **Como Funciona:** Criar um aplicativo dedicado para iPhone em Swift/SwiftUI que se comunica com o banco SQLite ou sincroniza os dados via backup seguro cifrado (`.dwb`).
