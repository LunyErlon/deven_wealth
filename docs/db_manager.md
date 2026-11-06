# Documentação: db_manager.py

## Propósito
A classe `DBManager` é a camada de persistência e acesso a dados (DAO/Repository) do Deven Wealth. Ela isola o código da interface gráfica das especificidades do SQLite local (`deven_wealth.db`), gerenciando conexões, conversão de tipos, integridade transacional e operações em lote de alta performance.

---

## Como Funciona

O `DBManager` encapsula o driver `sqlite3` nativo do Python, aplicando padronização no retorno das consultas e tratamento seguro de exceções com rollback automático em caso de falha.

### Principais Métodos

#### 1. `conectar()`
- Abre a conexão com o arquivo do banco de dados SQLite (`deven_wealth.db`).
- Configura `conexao.row_factory = sqlite3.Row`. Isso permite que qualquer resultado de leitura seja acessado tanto por índice numérico quanto pelo nome da coluna, sendo posteriormente convertido para dicionários nativos (`dict`).

#### 2. `executar_query(query, parametros=())`
- Utilizado para operações de escrita pontuais (`INSERT`, `UPDATE`, `DELETE`).
- Abre a conexão, instancia o cursor e executa a instrução parametrizada (prevenindo vulnerabilidades de SQL Injection).
- Em caso de sucesso, efetua o `conexao.commit()` e retorna o `cursor.lastrowid` (útil para recuperar chaves primárias geradas).
- Em caso de erro, executa `conexao.rollback()` para evitar inconsistências no banco e fecha a conexão no bloco `finally`.

#### 3. `executar_query_lote(query, lista_parametros)`
- **Operações em Lote de Alta Performance (Batch)**:
  - Projetado para persistir dezenas ou centenas de registros em milissegundos usando `cursor.executemany(query, lista_parametros)`.
  - Executa todas as inserções sob **uma única transação atômica** (`BEGIN TRANSACTION ... COMMIT`).
  - Reduz o tempo de inserção de múltiplos segundos (no loop individual) para cerca de 1 a 2 milissegundos.
  - Retorna `cursor.rowcount` com a contagem total de linhas afetadas.
  - Utilizado amplamente em:
    - **O Purgatório de Transações** (`DialogPurgatorioTransacoes`): para salvar lotes de faturas bancárias importadas.
    - **Assistente de Início** (`DialogBoasVindasRecorrentes`): para lançar em massa as contas recorrentes do mês.
    - **Radar de Dividendos** (`DialogRadarDividendos`): para consolidar lotes de proventos validados.

#### 4. `buscar_dados(query, parametros=())`
- Utilizado para consultas de leitura (`SELECT`).
- Executa a query com parâmetros sanitizados e invoca `cursor.fetchall()`.
- Converte iterativamente os objetos `sqlite3.Row` em dicionários reais do Python (`[dict(linha) for linha in linhas]`), facilitando o consumo por componentes do PyQt6 e pelo Pandas.

---

## Interligação
- **Instanciado em**: `main.py` (`self.db = DBManager()`).
- **Injetado em**: Todas as páginas da aplicação (`PaginaResumo`, `PaginaCarteira`, `PaginaAnalise`, `PaginaFinancas`, `PaginaRendimentos`, `PaginaConfig`).
- **Segurança**: Quando o aplicativo é fechado, o arquivo `deven_wealth.db` gerenciado por esta classe é criptografado pelo `SecurityManager` e removido do disco.
