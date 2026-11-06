# Visão Geral e Arquitetura - Deven Wealth

Este documento serve como um mapa do contexto e arquitetura geral da aplicação **Deven Wealth**, um gerenciador de finanças e carteira de investimentos desenvolvido em Python com interface gráfica usando **PyQt6**.

## Objetivo do Projeto
Fornecer um painel (Dashboard) único e offline-first para o usuário controlar:
1.  **Investimentos**: Acompanhar o patrimônio de ações, fundos imobiliários, moedas e criptomoedas.
2.  **Finanças Pessoais**: Lançar receitas e despesas para gerenciar o saldo livre do mês.

## Arquitetura em Módulos
Após a refatoração, o sistema foi dividido em três grandes pilares:

### 1. Motores de Dados (Core)
- **`db_manager.py`**: O cérebro local. Gerencia todas as leituras e escritas no banco de dados SQLite (`deven_wealth.db`), retornando dicionários em Python para facilitar o uso na interface.
- **`market_api.py`**: O cérebro na nuvem. Responsável por buscar as cotações, dividend yields (DY) e indicadores (P/VP, P/L) através de integrações externas (Brapi e YFinance).

### 2. A Ponte e o Chassi (Entry Point)
- **`main.py`**: A espinha dorsal do aplicativo. Ele desenha a janela, aplica o design escuro global via QSS (CSS do Qt), instancia o motor de dados (DB e API) e gerencia o menu de navegação lateral. Ele **não processa as telas em si**, mas empilha as telas independentes.

### 3. As Páginas (Views)
Cada tela do aplicativo agora é um componente `QWidget` isolado que herda propriedades do banco e da API.
- **`pagina_resumo.py`**: Consome os dados consolidados para montar KPIs e um gráfico visual.
- **`pagina_carteira.py`**: Interage com o banco para adicionar aportes e calcular o preço médio dos ativos.
- **`pagina_analise.py`**: Onde a pesquisa usando o motor da `market_api.py` acontece. Aqui é a porta de entrada para salvar um ativo no catálogo.
- **`pagina_financas.py`**: O livro-caixa diário. Não se comunica com a API de mercado, apenas interage com as tabelas de finanças do SQLite.
- **`pagina_rendimentos.py`**: Acompanhamento de proventos e dividendos com gráfico do efeito bola de neve e histórico com exclusão.
- **`pagina_config.py`**: Utilitário global para gerenciar a chave da API (Token) e apagar o banco em caso de necessidade.

## Interligações e Fluxo de Dados

1. Ao abrir o aplicativo (`main.py`), a base de dados SQLite é checada e criada se não existir.
2. Os motores `db` e `api` são criados no `main.py` e passados via parâmetro (Injeção de Dependência) para as páginas. Por exemplo: `PaginaAnalise(self.db, self.api)`.
3. Para que a **Visão Geral** seja atualizada sempre que uma nova compra for registrada na **Carteira**, o `main.py` passa uma função de *callback* entre as páginas. Quando algo muda, a página aciona o callback para forçar as outras a recarregarem os dados do banco atualizado.
