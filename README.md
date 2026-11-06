# 🪙 Deven Wealth

> **Gerenciador Pessoal de Finanças e Carteira de Investimentos Offline-First com Princípio de Atrito Positivo e Arquitetura PyQt6.**

O **Deven Wealth** é uma aplicação desktop desenvolvida em Python e PyQt6 com design moderno baseado na paleta *Catppuccin Mocha*. Foi projetada para fornecer controle patrimonial total, segurança criptográfica e disciplina financeira sem depender de serviços em nuvem de terceiros que expõem seus dados bancários.

---

## ✨ Principais Funcionalidades

### 1. 📊 Visão Geral e Carteira de Investimentos
- **Dashboard Consolidado:** Acompanhamento de patrimônio líquido em tempo real, saldo livre e gráficos de alocação de ativos.
- **Suporte Multi-Classe:** Ações, Fundos Imobiliários (FIIs), Criptomoedas, Moedas e Renda Fixa.
- **Preço Médio e Rentabilidade:** Cálculo automatizado de preço médio (PM), saldo investido e saldo atualizado via cotações de mercado.
- **Metas de Alocação:** Ajuste de metas percentuais por classe de ativos com feedback visual de rebalanceamento.

### 2. 📥 Motor de ETL & "O Purgatório de Transações" (Atrito Positivo)
- **Extrator Híbrido:** Leitura de extratos bancários e faturas de cartão de crédito em `.csv` e `.ofx` (usando `ofxparse` e `pandas`).
- **Detecção de Parcelamento Inteligente:** Algoritmo Regex que identifica compras parceladas (ex: `💳 [1/10]`), filtra datas e calcula parcelas pendentes.
- **O Purgatório:** Tela de triagem intermediária onde os dados não entram direto no banco. O usuário classifica os gastos com categorização em lote (`⚡ Aplicar em Massa`), garantindo controle e consciência sobre cada despesa antes de consolidar.
- **Batch Processing:** Inserção em milissegundos no SQLite utilizando `executemany`.

### 3. 🎯 Orçamento 50/30/20 & Categorias Dinâmicas
- **Regra 50/30/20 Flexível:** Definição personalizada de metas orçamentárias (ex: 50% Necessidades, 30% Desejos, 20% Construção de Riqueza) ou metas customizadas (ex: 40/20/40).
- **Cores Dinâmicas:** Alertas visuais automáticos nos cartões caso os tetos de gastos sejam superados.
- **Gerenciador de Categorias:** Criação e exclusão dinâmica de categorias amarradas às regras macro do orçamento.

### 4. 🔁 Motor de Contas Recorrentes (Loop Autolimpante)
- **Detecção Cross-Month:** Varredura automática ao iniciar o mês identificando despesas recorrentes do mês anterior que ainda não foram lançadas.
- **Pop-up de Confirmação Editável:** Permite ajustar valores de contas variáveis (água, luz) antes de lançar.
- **Loop Autolimpante:** Desmarcar ou excluir uma conta no pop-up encerra o ciclo de cobrança recorrente sem telas extras burocráticas.

### 5. 🔍 Radar Automático de Dividendos (Bola de Neve)
- **Rastreador de Proventos:** Integração com Brapi e fallback resiliente com `yfinance` para capturar proventos recentes dos ativos da carteira.
- **Thread em Segundo Plano:** Execução silenciosa via `QThread` no startup do app, sem congelar a interface.
- **Atrito da Data-Com:** Pop-up de validação permitindo ajustar a *Quantidade Base de Cotas* recebida antes de gravar na base.
- **Gráfico Bola de Neve:** Visualização do histórico acumulado de proventos e renda passiva.

### 6. 🔐 Segurança e Criptografia
- **Cofre Criptografado (AES-256 via PBKDF2/Fernet):** Seus dados são salvos em formato encriptado com sua senha-mestra.
- **Autenticação Segura:** Verificação contra senhas padrão e hashes protegidos com Salt aleatório.
- **Exportação Multiformato:** Exportação segura em `.xlsx` (com 3 abas: "Minha Carteira", "Contas Pessoais" e "Renda Passiva") e backup cifrado `.dwb`.

---

## 🛠️ Tecnologias Utilizadas

- **Python 3.12+**
- **PyQt6:** Interface gráfica desktop e ciclo de eventos
- **SQLite3:** Banco de dados relacional local offline-first
- **Pandas & OpenPyXL:** Manipulação de dados e exportação para planilhas
- **OfxParse:** Parser de extratos bancários Open Financial Exchange
- **Cryptography:** Derivação de chaves PBKDF2 e cifras simétricas Fernet
- **YFinance & Requests:** Consulta de cotações e proventos da B3
- **Matplotlib:** Gráficos patrimoniais integrados ao Qt

---

## 🚀 Como Executar

### 1. Clonar o Repositório
```bash
git clone https://github.com/LunyErlon/LunyErlon.git
cd LunyErlon/DEVEN_WEALTH
```

### 2. Criar e Ativar o Ambiente Virtual
```bash
python -m venv .venv

# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Linux / MacOS:
source .venv/bin/activate
```

### 3. Instalar as Dependências
```bash
pip install -r requirements.txt
```

### 4. Iniciar o Aplicativo
```bash
python gerenciador/main.py
```

No primeiro acesso, o sistema detectará que não há cofre criado e apresentará a tela para você cadastrar sua **Senha-Mestra**. Todas as tabelas e categorias inteligentes padrão serão criadas automaticamente.

---

## 📁 Estrutura do Projeto

```
DEVEN_WEALTH/
├── docs/                   # Documentação arquitetural detalhada de cada módulo
├── gerenciador/
│   ├── assets/             # Ícones e imagens
│   ├── componentes.py      # Componentes UI reutilizáveis (PasswordInput, etc.)
│   ├── db_manager.py       # Camada de persistência SQLite com suporte a Batch
│   ├── main.py             # Ponto de entrada, navegação e orquestração de threads
│   ├── market_api.py       # Integrações Brapi e yfinance com cache
│   ├── pagina_analise.py   # Pesquisa e análise de ativos
│   ├── pagina_carteira.py  # Gestão de compras, vendas e preço médio
│   ├── pagina_config.py    # Configurações, metas 50/30/20 e backups
│   ├── pagina_financas.py  # Livro-caixa, ETL Purgatório e contas recorrentes
│   ├── pagina_login.py     # Cofre, cadastro de senha-mestra e desbloqueio
│   ├── pagina_rendimentos.py# Radar de dividendos e gráfico da Bola de Neve
│   ├── pagina_resumo.py    # Dashboard consolidado de patrimônio
│   └── security_manager.py # Criptografia AES-256 e hashes de segurança
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 📄 Licença
Desenvolvido por **Luny Erlon** no ecossistema **Deven**.
