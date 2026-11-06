import sqlite3

class DBManager:
    def __init__(self, db_name="deven_wealth.db"):
        self.db_name = db_name

    def conectar(self):
        # Abre a conexão e configura para retornar linhas como dicionários
        conexao = sqlite3.connect(self.db_name)
        conexao.row_factory = sqlite3.Row
        return conexao

    def executar_query(self, query, parametros=()):
        """Uso: INSERT, UPDATE, DELETE. Retorna o ID do último registro inserido."""
        conexao = self.conectar()
        try:
            cursor = conexao.cursor()
            cursor.execute(query, parametros)
            conexao.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Erro ao executar query: {e}")
            conexao.rollback()
        finally:
            conexao.close()

    def executar_query_lote(self, query, lista_parametros):
        """Uso: Inserções ou atualizações em lote (Batch). Usa executemany em uma única transação rápida."""
        if not lista_parametros:
            return 0
        conexao = self.conectar()
        try:
            cursor = conexao.cursor()
            cursor.executemany(query, lista_parametros)
            conexao.commit()
            return cursor.rowcount
        except sqlite3.Error as e:
            print(f"Erro ao executar query em lote: {e}")
            conexao.rollback()
            raise e
        finally:
            conexao.close()

    def buscar_dados(self, query, parametros=()):
        """Uso: SELECT. Retorna uma lista de dicionários com os resultados."""
        conexao = self.conectar()
        try:
            cursor = conexao.cursor()
            cursor.execute(query, parametros)
            # Fetchall pega tudo, e transformamos cada linha em um dicionário real
            linhas = cursor.fetchall()
            return [dict(linha) for linha in linhas]
        except sqlite3.Error as e:
            print(f"Erro ao buscar dados: {e}")
            return []
        finally:
            conexao.close()