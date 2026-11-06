# Documentação: db_manager.py

## Propósito
A classe `DBManager` é a camada de persistência de dados. Ela age como uma interface limpa entre o código Python em várias páginas do projeto e o banco de dados local SQLite (`deven_wealth.db`).

## Como Funciona
O arquivo contém a classe `DBManager`, inicializada com o nome do arquivo do banco. 
Para evitar que o resto do aplicativo precise lidar diretamente com as esquisitices e ponteiros do SQLite (como os cursores tradicionais que retornam tuplas `(1, "Ação")`), ele abstrai isso retornando dados em formato de dicionário `{"id": 1, "tipo": "Ação"}`.

### Principais Métodos
- **`conectar()`**: Abre uma conexão SQLite e aplica `sqlite3.Row` no `row_factory`. Isso é o que permite o retorno dos dados em dicionários.
- **`executar_query(query, parametros)`**: Utilizado para operações de escrita (CRUD) individuais - `INSERT`, `UPDATE`, `DELETE`. Ele abre a conexão, faz o commit, retorna o ID gerado, lida com exceções (rollback) e fecha a conexão com segurança no bloco `finally`.
- **`executar_query_lote(query, lista_parametros)`**: Utilizado para operações de escrita em lote (*Batch*) em milissegundos utilizando `cursor.executemany(...)` dentro de uma única transação atômica. Essencial para salvar lotes de transações do Purgatório de Faturas, lote de Contas Recorrentes e confirmação em lote de dividendos do Radar.
- **`buscar_dados(query, parametros)`**: Utilizado para operações de leitura (`SELECT`). Ele busca todos os dados, converte as linhas do `sqlite3.Row` para dicionários nativos do Python e retorna uma lista.

## Interligação
- **Instanciado em**: `main.py` (`self.db = DBManager()`).
- **Injetado em**: É passado como dependência para TODAS as páginas da interface no momento em que elas são criadas (`PaginaResumo(self.db)`, `PaginaCarteira(self.db)`, etc.). As páginas o utilizam para ler saldos, gravar transações ou ler o preço médio da carteira.
