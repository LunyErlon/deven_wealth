# Visão Geral e Arquitetura - Deven Wealth

Este documento serve como um mapa do contexto e arquitetura geral da aplicação **Deven Wealth**, um gerenciador de finanças e carteira de investimentos offline-first desenvolvido em Python com interface gráfica usando **PyQt6** e estilização moderna baseada na paleta *Catppuccin Mocha*.

---

## 🎯 Objetivo e Filosofia do Projeto

Fornecer um painel único (Dashboard) e 100% offline-first para o usuário controlar com precisão matemática:
1. **Investimentos**: Acompanhar o patrimônio de ações, fundos imobiliários, moedas e criptomoedas com preço médio, cotações em tempo real e gráficos de alocação.
2. **Finanças Pessoais**: Gerenciar receitas, despesas e metas orçamentárias (Regra 50/30/20 flexível).
3. **Renda Passiva (Bola de Neve)**: Acompanhar o fluxo de proventos recebidos e simular o crescimento dos juros compostos.
4. **Princípio do Atrito Positivo**: Diferente de apps convencionais que inserem dados silenciosamente gerando descontrole, o Deven Wealth utiliza pontos de checagem intencionais (triage) para forçar o usuário a examinar e conscientemente validar cada gasto, conta recorrente e provento.

---

## 🏛️ Arquitetura em Módulos

O sistema é estritamente desacoplado em camadas funcionais:

```
DEVEN_WEALTH/
├── 1. Camada de Persistência & Segurança (Core)
│   ├── db_manager.py          # Wrapper SQLite com suporte a CRUD e Batch (executemany)
│   └── security_manager.py    # Cofre criptografado AES-256 (Fernet) com PBKDF2HMAC
│
├── 2. Camada de Integração Externa (APIs)
│   └── market_api.py          # Cotações e dividendos (Brapi + fallback resiliente yfinance)
│
├── 3. Camada de Orquestração & Janela Principal
│   └── main.py                # MainWindow, QSS global, navegação, threads e timers
│
├── 4. Camada de Apresentação (Views / QWidgets)
│   ├── pagina_login.py        # Tela de registro/desbloqueio do cofre
│   ├── pagina_resumo.py       # KPIs consolidados, gráficos e Máquina do Tempo
│   ├── pagina_carteira.py     # Carteira de ativos, compras e rebalanceador
│   ├── pagina_analise.py      # Busca de ativos e Radar de Oportunidades
│   ├── pagina_financas.py     # Livro-caixa, Purgatório de Faturas e Recorrentes
│   ├── pagina_rendimentos.py  # Histórico de proventos, Bola de Neve e Radar
│   └── pagina_config.py       # Metas 50/30/20, perfil, tokens e exportação Excel
```

---

## ⚙️ Os Três Grandes Motores Inteligentes

### 1. Motor de ETL & O Purgatório de Transações (`pagina_financas.py`)
- **Extrator Híbrido (`ExtratorFaturas`)**:
  - Lê faturas e extratos bancários em `.csv` (via `pandas` com auto-detecção de encoding/separador) e `.ofx` (via `ofxparse` com correção de mojibake e fallbacks `memo`/`payee`).
  - **Caçador de Parcelas (Regex)**: Detecta padrões como `1/10` ou `PARC 02/12`, filtrando datas e gerando tags visuais `💳 [X/Y]`.
- **Fila de Triage ("Purgatório")**: 
  - Interface temporária (`DialogPurgatorioTransacoes`) onde os lançamentos aguardam categorização.
  - O botão *"💾 Salvar Lote"* permanece travado (`setEnabled(False)`) sob o princípio do **Atrito Positivo**, liberando-se apenas quando 100% das transações marcadas receberem classificação.
  - Gravação de dezenas de transações em milissegundos via `executar_query_lote`.

### 2. Motor de Contas Recorrentes (`main.py` + `pagina_financas.py`)
- **Detecção Cross-Month**: Ao iniciar o app, o sistema detecta despesas marcadas com `recorrente = 1` no mês anterior que ainda não constam no mês atual.
- **Assistente de Início (`DialogBoasVindasRecorrentes`)**: Apresenta pop-up com valores e datas editáveis (para contas variáveis como luz/água).
- **Loop Autolimpante**: Ao desmarcar ou excluir uma conta no pop-up, o sistema zera o flag `recorrente` no mês passado, encerrando a cadeia de repetição sem necessidade de interfaces extras de cancelamento.

### 3. Radar Automático de Dividendos (`market_api.py` + `pagina_rendimentos.py`)
- **Varredura em Background**: `WorkerRadarDividendos(QThread)` roda silenciosamente 1.2s após a abertura da aplicação, consultando proventos recentes pagos nos últimos 45 dias.
- **Resiliência Multi-Provedor**: Consulta o endpoint de dividendos da Brapi; caso ocorra restrição de plano (HTTP 403), aciona imediatamente a contingência via `yfinance` para ativos B3 (`.SA`).
- **Atrito da Data-Com (`DialogRadarDividendos`)**: Como a API sabe que a empresa pagou mas não o dia exato de custódia do investidor, o pop-up exibe a coluna editável de **Quantidade Base de Cotas**, garantindo precisão cirúrgica antes de consolidar na base de dados.

---

## 🔄 Fluxo de Dados e Comunicação entre Módulos

1. **Injeção de Dependências**:
   - `main.py` instancia `db = DBManager()` e `api = MarketAPI(db)` e injeta essas instâncias nos construtores das páginas filhas.
2. **Sincronização em Tempo Real via Callbacks**:
   - Operações em `PaginaCarteira`, `PaginaFinancas` e `PaginaRendimentos` disparam callbacks (ex: `fn_atualizar_resumo=self.pagina_resumo.carregar_dados`) para sincronizar KPIs de patrimônio e a Bola de Neve instantaneamente.
3. **Persistência Atômica e Criptografia**:
   - Todas as transações ocorrem no banco SQLite local. Ao encerrar a aplicação (`closeEvent`), o banco `deven_wealth.db` é cifrado com AES-256 gerando `deven_wealth.db.enc` e o arquivo aberto é triturado do disco.
