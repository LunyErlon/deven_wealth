# Documentação: pagina_financas.py

## Propósito
Atua como o "Livro-Caixa" do usuário para as finanças do cotidiano. Após a integração da regra **50/30/20**, também atua como um mentor financeiro, alertando visualmente quando gastos de estilo de vida ameaçam as necessidades básicas ou os aportes de riqueza. 

Inclui o **Extrator Híbrido** e **O Purgatório de Transações**, viabilizando a importação de faturas e extratos (CSV e OFX) com triagem inteligente baseada no conceito de **Atrito Positivo**, além do **Motor de Contas Recorrentes** com suporte a contas de valor variável e cancelamento orgânico (**Loop Autolimpante**).

---

## Componentes e Como Funciona

### 1. `ExtratorFaturas` (Motor de ETL Híbrido)
- **Roteamento Inteligente**: Detecta a extensão do arquivo selecionado (`.ofx` ou `.csv`).
- **Motor OFX (`ofxparse`)**:
  - Suporta extratos de contas correntes e faturas de cartões de crédito (`ofx.accounts` e `ofx.account`).
  - Resolve a peculiaridade de bancos brasileiros (ex: Nubank, Itaú), onde o campo `payee` frequentemente é nulo/genérico ("Compra no débito") e o estabelecimento real fica no campo `memo`.
  - Corrige preventivamente inconsistências de codificação de caracteres (*mojibake* entre ISO-8859-1 e UTF-8).
  - Normaliza débitos (despesas) e créditos (receitas) preservando o valor monetário absoluto.
- **Motor CSV (`pandas`)**:
  - Detecção automática de múltiplos encodings (`utf-8`, `utf-8-sig`, `latin-1`, `cp1252`) e delimitadores (`,`, `;`, `\t`).
  - Mapeamento heurístico de colunas (localiza `Data`, `Valor`, `Descrição/Título`).
  - Distingue faturas de cartão de crédito (onde lançamentos de compras são positivos) de extratos tradicionais (onde saídas são negativas).
- **Caçador de Parcelamento (Regex `detectar_parcelamento`)**:
  - Identifica automaticamente compras parceladas no cartão em formatos como `1/10`, `02/12`, `PARC 03/05` ou `Parcela 1 de 10`.
  - Filtra falsos positivos de datas (ex: `TED 15/08`) validando que `1 <= parcela_atual <= total_parcelas` e limites de parcelas de cartão (máx 60).
  - Exibe badges visuais informativos `💳 [1/10]` na tabela com tooltip indicando parcelas restantes e compromisso futuro.

---

### 2. `DialogPurgatorioTransacoes` (Fila de Triage & Atrito Positivo)
- **A Fila Temporária**: Os dados do extrato/fatura entram no sistema, mas **não** vão diretamente para o banco oficial. Ficam retidos aguardando classificação do usuário.
- **Trava de Segurança de Atrito Positivo**:
  - O botão **`💾 Salvar Lote no Livro-Caixa`** inicia **desabilitado (`setEnabled(False)`)**.
  - O botão só se torna verde e clicável quando **100% das transações marcadas receberem uma categoria válida**.
  - Enquanto houver pendências, o botão permanece desabilitado em tom acinzentado com um *tooltip* orientativo (ex: *"Atrito Positivo: Faltam 3 transações sem categoria para habilitar o salvamento em lote"*).
- **Ferramentas de Produtividade**:
  - **`⚡ Aplicar em Massa`**: Permite selecionar dezenas de transações e aplicar uma categoria comum a todas de uma só vez.
  - **Filtro em Tempo Real**: Campo de busca textual por descrição.
  - **Botão `➕ Nova Categoria`**: Abre o `DialogGerenciarCategorias` sem perder o progresso de edição da tabela.
  - **Checkboxes Individuais**: Permite ignorar transações que não devem ser contabilizadas (ex: pagamento de fatura, transferências entre contas próprias).
  - **Estatísticas Dinâmicas**: Atualização instantânea de selecionados, classificados, soma de despesas e receitas.
- **Persistência em Lote de Alta Performance**:
  - O método `salvar_lote()` utiliza `self.db.executar_query_lote()` (`cursor.executemany`), gravando dezenas ou centenas de registros no SQLite em uma única transação atômica em milissegundos com `origem = 'Importado'`.

---

### 3. `DialogBoasVindasRecorrentes` (Assistente de Início & Loop Autolimpante)
- **Detecção Cross-Month**: Pop-up inteligente disparado na inicialização do aplicativo (`main.py`) ou sob demanda pelo botão `🔁 Contas Recorrentes`.
- Compara os gastos recorrentes do mês anterior com os já lançados no mês corrente, levantando o que ainda falta pagar.
- **Lista Editável de Lançamentos**:
  - Permite alterar valores de contas flutuantes (ex: luz, água ou gás) diretamente na tabela antes de confirmar.
  - Sugere automaticamente o mesmo dia de vencimento do mês anterior, ajustado para os limites do mês atual.
- **O Loop Autolimpante**:
  - Ao cancelar um serviço ou terminar de pagar uma conta, o usuário apenas **desmarca** ou exclui a linha no pop-up.
  - O sistema grava apenas as contas marcadas (com `recorrente = 1`). A conta desmarcada é atualizada no mês anterior com `recorrente = 0`, quebrando o elo da corrente para os meses futuros de forma orgânica e sem burocracia.
  - Utiliza `executar_query_lote` para consolidação atômica.

---

### 4. `DialogGerenciarCategorias` (Gestão Dinâmica 50/30/20)
- Permite cadastrar novas categorias escolhendo:
  - **Nome** (ex: "Ração do Pet", "Academia").
  - **Tipo** ("Despesa" ou "Receita").
  - **Grupo da Regra 50/30/20** ("Necessidades", "Desejos", "Construção de Riqueza" ou "Sem Grupo").
- Exclusão com confirmação e atualização dinâmica imediata dos combos em todas as telas.

---

### 5. `PaginaFinancas` (Interface Principal)
- **Painel Superior com Gráfico de Rosca 50/30/20**:
  - **Coluna da Esquerda (KPIs e Indicadores)**:
    - Receitas, Despesas e Saldo Livre.
    - **Cartões 50/30/20 Dinâmicos**: Consultam as metas personalizadas na tabela `configuracoes` (`meta_necessidades`, `meta_desejos`, `meta_riqueza`).
    - **Cores de Alerta**: Alternam automaticamente para tom de alerta (`#f38ba8`) se o percentual de gastos em Necessidades ou Desejos exceder o teto, ou se os investimentos ficarem abaixo da meta.
  - **Coluna da Direita (Gráfico de Rosca / Donut Chart)**:
    - Integrado via Matplotlib (`FigureCanvasQTAgg`), adaptado ao tema Catppuccin Mocha (`#262939` e `#1e1e2e`).
    - Desenha fatias proporcionais de gastos: Necessidades (`#89b4fa`), Desejos (`#f9e2af`), Construção de Riqueza (`#a6e3a1`) e Outros (`#cba6f7`).
    - Centro vazado com valor total monetário das despesas e legenda com percentuais calculados.
    - Caso não haja gastos registrados no mês selecionado, renderiza anel neutro estilizado ("Sem Despesas no Período").
- **Formulário de Inserção Manual**:
  - Data, Descrição, Categoria, Valor e o checkbox `🔁 Conta Recorrente (Repetir mensalmente)`.
- **Tabela de Histórico**:
  - Exibe os lançamentos com identificador visual `🔁` para contas recorrentes, badge de categoria e botão de exclusão.
- **Filtro Mensal e Botões de Ação**:
  - Dropdown com meses disponíveis alimentado dinamicamente por `carregar_meses()`.
  - Botão `📥 Importar Fatura (CSV / OFX)` e botão `🔁 Contas Recorrentes`.

---

## Interligação
- **Recebe**: A instância do banco `DBManager` injetada via construtor pelo `main.py`.
- **Dispara**: Callbacks de atualização de dados e recálculo de orçamentos.
- **Persistência**: Grava e lê das tabelas `transacoes`, `categorias` e `configuracoes` no SQLite com suporte a transações em lote.
