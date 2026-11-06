# Documentação: main.py

## Propósito
O `main.py` é o ponto de entrada (Entry Point) e o orquestrador principal do aplicativo Deven Wealth. Ele inicializa os serviços centrais, define a arquitetura de navegação, gerencia timers de segundo plano e conecta os sinais e callbacks entre as diferentes páginas do sistema.

---

## Responsabilidades e Arquitetura

### 1. Inicialização e Ciclo de Vida
- Cria a instância `QApplication` do PyQt6.
- Instancia os motores de dados: `self.db = DBManager()` e `self.api = MarketAPI(self.db)`.
- Gerencia o evento de fechamento (`closeEvent`): garante que qualquer transação seja concluída antes de delegar a cifragem do banco para o `SecurityManager`.

---

### 2. Criação do Banco e Migrações Idempotentes (`inicializar_banco_dados`)
- Cria todas as tabelas essenciais (`ativos_catalogo`, `carteira_atual`, `cache_mercado`, `rendimentos`, `transacoes`, `categorias`, `configuracoes`).
- **Mecanismos de Migração Segura**:
  - Inspeciona o esquema existente usando `PRAGMA table_info` antes de executar alterações.
  - Executa `ALTER TABLE categorias ADD COLUMN grupo_regra TEXT DEFAULT 'Sem Grupo'` se a coluna não existir.
  - Executa `ALTER TABLE transacoes ADD COLUMN recorrente INTEGER DEFAULT 0` se a coluna não existir.
- **Carga Inicial Inteligente**: Popula automaticamente o catálogo padrão da Regra 50/30/20 se a tabela de categorias estiver vazia (com categorias essenciais como Moradia, Mercado Básico, Aportes, Lazer, etc.).

---

### 3. Automações em Segundo Plano & Timers Inteligentes
Para garantir que a janela principal abra instantaneamente e sem travamentos perceptíveis para o usuário:
- **Assistente de Contas Recorrentes (`verificar_contas_recorrentes`)**:
  - Agendado via `QTimer.singleShot(400, ...)` logo após a abertura da janela.
  - Varre o mês anterior em busca de contas recorrentes ausentes no mês corrente e exibe o `DialogBoasVindasRecorrentes` com suporte ao **Loop Autolimpante**.
- **Radar de Dividendos Assíncrono (`iniciar_radar_dividendos_background`)**:
  - Agendado via `QTimer.singleShot(1200, ...)` para não disputar I/O com a inicialização.
  - Instancia a `WorkerRadarDividendos(QThread)` em processo paralelo.
  - Se houver proventos recentes para os ativos em custódia, o slot `ao_detectar_dividendos_background()` abre o `DialogRadarDividendos` permitindo a validação da Data-Com.

---

### 4. Layout Base (Chassi) e Navegação
- Constrói a janela principal (`QMainWindow`) com tamanho padrão 1280x800 e proporções responsivas.
- **Barra Lateral de Navegação (Sidebar)**:
  - Menu estilizado com botões que alternam as páginas dentro de um `QStackedWidget`.
  - Ícones dinâmicos gerados via biblioteca `qtawesome` (estilo outline/linha).
  - O método `atualizar_menu()` destaca o botão e o ícone da página ativa em dourado (`#D4AF37`), esmaecendo os inativos.
  - Rodapé embutido com versão, status do sistema e indicador do cofre criptografado.

---

### 5. Injeção de Dependências & Callbacks Cruzados
Ao empilhar as telas no `QStackedWidget`, o `main.py` injeta os serviços necessários:
- `PaginaResumo(self.db)`
- `PaginaCarteira(self.db, fn_atualizar_resumo=self.pagina_resumo.carregar_dados)`
- `PaginaAnalise(self.db, self.api, fn_atualizar_carteira=self.pagina_carteira.carregar_dados)`
- `PaginaFinancas(self.db)`
- `PaginaRendimentos(self.db, self.api, fn_atualizar_resumo=self.pagina_resumo.carregar_dados)`
- `PaginaConfig(self.db, self.api, fn_reset_db=self.reset_banco_dados)`

Essa malha de *callbacks* assegura que qualquer alteração de patrimônio na Carteira ou provento nos Rendimentos atualize a Visão Geral em tempo real.

---

### 6. Estilização Global (QSS Catppuccin Mocha)
O método `aplicar_estilos()` insere o CSS do Qt (QSS) que padroniza:
- Fundo escuro profundo (`#1e1e2e` e `#11111b`).
- Destaques dourados (`#D4AF37`) e acentos suaves (`#89b4fa`, `#a6e3a1`, `#fab387`, `#f38ba8`).
- Tipografia moderna e uniforme em botões, campos de texto, tabelas e cabeçalhos.

---

## Interligação
- **Importa**: Todos os módulos de views (`pagina_*.py`), persistência (`db_manager.py`), API (`market_api.py`) e segurança (`security_manager.py`).
- **Ponto de Entrada**: Inicializado pelo `Launcher` seguro após a validação da senha-mestra.
