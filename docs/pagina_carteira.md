# Documentação: pagina_carteira.py

## Propósito
É o componente responsável por listar o inventário do usuário (sua carteira de ativos) através de uma tabela e permitir o registro de novas compras de ações/criptos.

## Como Funciona
Possui três classes em seu interior:
1. **`DialogoCompra(QDialog)`**: Uma pequena janela flutuante (Pop-up) desenhada para que o usuário informe "Quantidade" e "Preço Pago" sobre um ativo.
2. **`DialogoRebalanceamento(QDialog)`**: O Assessor Virtual. Lê as classes de ativos do catálogo, soma o patrimônio atual do usuário por classe e permite que ele defina as porcentagens-alvo ideais (ex: 60% Ações, 40% FIIs). Ao informar o Aporte Mensal, o algoritmo sugere matematicamente os ativos que o usuário deve comprar para manter a carteira equilibrada.
3. **`PaginaCarteira(QWidget)`**: A página em si.
   - **`setup_ui()`**: Cria uma `QTableWidget` com 9 colunas. E os botões de ação (Registrar Compra e Assessor Virtual).
   - **`carregar_dados()`**: Lê do banco de dados a intersecção do que o usuário tem na carteira (`carteira_atual`) junto com as informações de cotação mais recentes (`cache_mercado`). Preenche a tabela dinamicamente. Para a coluna 8, cria botões de exclusão na tabela usando ícones de lixeira (FontAwesome) centralizados, para uma UX limpa e moderna.
   - **`abrir_registro_compra()`**: Lê qual linha o usuário selecionou na tabela e abre o `DialogoCompra`. Quando o diálogo é aceito, ele calcula o novo "Preço Médio" matematicamente (levando em conta a quantidade velha vs quantidade nova) e salva (INSERT/UPDATE) no banco de dados SQLite.
   - **`abrir_rebalanceamento()`**: Instancia e exibe o `DialogoRebalanceamento`.
   - **`excluir_ativo()`**: Remove completamente os traços do ativo, deletando-o em cascata das tabelas `carteira_atual`, `cache_mercado` e `ativos_catalogo`, garantindo que o ativo desapareça definitivamente do catálogo e do sistema.

## Interligação
- Possui injeção de dependência do `db_manager.py` (via construtor).
- Ao final de um evento de exclusão ou compra, esta página verifica se recebeu o gatilho `self.fn_atualizar_resumo` (injetado via construtor pelo `main.py`) e o executa, forçando a "Visão Geral" a atualizar seus KPIs.
