# Documentação: pagina_financas.py

## Propósito
Atua como o "Livro-Caixa" do usuário para as finanças do cotidiano. Após a atualização da regra "50/30/20", ele também atua como um mentor financeiro, impedindo que o usuário mascare gastos de estilo de vida como se fossem essenciais para sobrevivência. Agora conta com o **Extrator Híbrido** e **O Purgatório de Transações**, viabilizando a importação de faturas e extratos (CSV e OFX) com triage e o conceito de *Atrito Positivo*.

## Como Funciona
A classe `PaginaFinancas` lida com transações simples, divididas inteligentemente em Macro-Categorias e filtradas por mês, suportando lançamentos manuais e em lote por importação bancária.

- **`ExtratorFaturas` (Fase 1 - Extrator Híbrido)**:
  - Roteador inteligente que detecta a extensão (`.ofx` ou `.csv`).
  - **Motor OFX (`ofxparse`)**:
    - Suporta arquivos OFX de contas correntes e cartões de crédito (`ofx.accounts` e `ofx.account`).
    - Resolve a peculiaridade de bancos brasileiros (ex: Nubank, Itaú), onde o campo `payee` frequentemente é vazio/genérico ("Compra no débito") e o estabelecimento real fica no campo `memo`.
    - Corrige preventivamente inconsistências de codificação de caracteres (mojibake entre ISO-8859-1 e UTF-8).
    - Detecta débitos (despesas) e créditos (receitas) preservando o valor absoluto positivo no banco de dados.
  - **Motor CSV (`pandas`)**:
    - Detecção automática de múltiplos encodings (`utf-8`, `utf-8-sig`, `latin-1`, `cp1252`) e separadores (`,`, `;`, `\t`).
    - Mapeamento heurístico de colunas (localiza `Data`, `Valor`, `Descrição/Título`).
    - Distingue faturas de cartão de crédito (onde lançamentos são positivos mas representam despesas) de extratos tradicionais (onde despesas são negativas).
  - **Caçador de Parcelamento (Regex `detectar_parcelamento`)**:
    - Identifica automaticamente compras parceladas no cartão em padrões como `1/10`, `02/12`, `PARC 03/05` ou `Parcela 1 de 10`.
    - Filtra falsos positivos de datas (ex: `TED 15/08`) validando que `parcela_atual <= total_parcelas` e limites de parcelas de cartão.
    - Exibe badges visuais informativas `💳 [1/10]` na tabela de triage com tooltip de parcelas restantes e compromisso futuro.

- **`DialogPurgatorioTransacoes` (Fase 2 - Fila de Processamento e Atrito Positivo)**:
  - Tabela intermediária de triage: os dados do arquivo bancário entram no sistema, mas **não** são salvos diretamente no banco de dados oficial.
  - Obriga o usuário a examinar cada gasto e selecionar sua respectiva categoria e grupo da regra 50/30/20.
  - **Controles Avançados**:
    - Checkboxes individuais para marcar/desmarcar transações que não devem ser importadas (ex: pagamento de fatura, transferências entre contas próprias).
    - Filtro de busca em tempo real por descrição.
    - Classificação rápida em massa para agilizar itens semelhantes.
    - Botão "➕ Nova Categoria": permite criar na hora uma categoria faltante sem perder o progresso da tabela.
    - Contador de estatísticas dinâmicas (linhas selecionadas, pendentes de classificação, somatórios de despesas e receitas).
  - **Validação Didática**:
    - Se o usuário tentar salvar o lote com transações pendentes de categoria, o sistema exibe um alerta de Atrito Positivo, perguntando se ele deseja voltar para classificar ou importar apenas as que já foram categorizadas.
    - Insere no banco com `origem = 'Importado'`.

- **`DialogBoasVindasRecorrentes` (Assistente de Início & Loop Autolimpante)**:
  - Pop-up inteligente de início de mês acionado automaticamente pelo `main.py` ou manualmente pelo botão `🔁 Contas Recorrentes`.
  - Compara o mês anterior com o mês atual para identificar quais despesas recorrentes (`recorrente = 1`) ainda estão pendentes.
  - **Lista Editável de Lançamentos**:
    - Permite ajustar valores flutuantes (ex: luz, água ou gás) diretamente na tabela antes de confirmar.
    - Sugere automaticamente o mesmo dia de vencimento do mês anterior ajustado para os limites do mês atual.
    - Permite editar descrições.
  - **O Loop Autolimpante**:
    - Se o usuário terminou de pagar uma conta (ex: consórcio) ou cancelou um serviço (ex: streaming), basta **desmarcar** ou excluir da lista.
    - Ao confirmar, o sistema grava apenas as contas marcadas (com `recorrente = 1`). A conta desmarcada não entra no mês atual, quebrando o elo da corrente.
    - No mês seguinte, o motor fará a varredura olhando para o mês anterior e essa conta não existirá mais para o radar, sumindo organicamente sem necessidade de telas extras de cancelamento.

- **`setup_ui()`**:
  1. Possui os KPIs normais de Receita, Despesa e Saldo Livre.
  2. Possui um segundo nível de KPIs **"A Regra 50/30/20"**: Mostra de forma ativa a porcentagem do seu salário que está indo para Necessidades, Desejos e Construção de Riqueza.
  3. **Filtro Mensal e Ações:** No topo da página, um seletor exibe os meses disponíveis, acompanhado do botão `📥 Importar Fatura (CSV / OFX)` e do botão `🔁 Contas Recorrentes`.
  4. Formulário de inserção manual: Conta com o checkbox `🔁 Conta Recorrente (Repetir mensalmente)` logo abaixo dos inputs para marcar gastos periódicos.
  5. Tabela de histórico: Exibe o indicador visual `🔁` na descrição de todas as despesas recorrentes ativas.

- **`importar_fatura()`**:
  - Abre o seletor `QFileDialog` filtrando por `.csv` e `.ofx`.
  - Aciona o `ExtratorFaturas` e abre o `DialogPurgatorioTransacoes`.
  - Ao concluir, atualiza automaticamente o seletor de meses e recarrega os dados do orçamento.

- **`carregar_meses()`**: Identifica todas as datas em que houveram lançamentos no banco de dados, compila em uma lista de meses (ex: "10/2026") e atualiza o filtro no topo da página.

- **`carregar_dados()`**: 
  A leitura do banco é filtrada usando a restrição `WHERE t.data LIKE 'YYYY-MM-%'` de acordo com o Mês/Ano selecionado no topo da página. Calcula porcentagens da regra 50/30/20 com alertas visuais dinâmicos.

- **`salvar_transacao()`**: Pega os dados dos campos do formulário manual e joga na tabela `transacoes` com `origem = 'Manual'`.

- **`excluir_transacao(id)`**: Remove o registro usando o ID do SQLite.

- **`DialogGerenciarCategorias`** e **`abrir_gerenciador_categorias()`**: Permite ao usuário criar novas categorias vinculadas à regra 50/30/20 ("Necessidades", "Desejos", "Construção de Riqueza") ou excluí-las caso não haja transações atreladas.

## Interligação
- Recebe a instância do banco (`self.db`) injetada via construtor.
- Totalmente compatível com SQLite e o ecossistema criptografado do Deven Wealth.
