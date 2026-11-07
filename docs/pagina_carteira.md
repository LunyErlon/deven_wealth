# Documentação: pagina_carteira.py

## Propósito
É o componente responsável por gerenciar a custódia patrimonial do usuário (sua carteira de ativos). Permite registrar novas compras com cálculo automático de Preço Médio ponderado, acompanhar rentabilidade e saldos atualizados, excluir posições e utilizar o **Assessor Virtual de Rebalanceamento**.

---

## Componentes e Como Funciona

### 1. `DialogoCompra(QDialog)`
- Pop-up modal para entrada de novas ordens de compra de um ativo já existente no catálogo.
- **Campos**:
  - Quantidade de cotas compradas (`QDoubleSpinBox`).
  - Preço unitário pago (`QDoubleSpinBox`).
- **Cálculo de Preço Médio Ponderado**:
  $$\text{PM}_{\text{novo}} = \frac{(\text{Qtd}_{\text{antiga}} \times \text{PM}_{\text{antigo}}) + (\text{Qtd}_{\text{nova}} \times \text{Preço}_{\text{novo}})}{\text{Qtd}_{\text{antiga}} + \text{Qtd}_{\text{nova}}}$$
- Atualiza ou insere o registro na tabela `carteira_atual` e executa o callback `fn_atualizar_resumo`.

---

### 2. `DialogoRebalanceamento(QDialog)` (O Assessor Virtual Inteligente)
- Ferramenta matemática para guiar aportes mensais sem decisões emocionais e de forma automatizada.
- **Integração com Saldo Livre das Finanças**:
  - Botão **`⚡ Puxar Saldo Livre (Finanças)`**: Consulta instantaneamente o livro-caixa do mês corrente (`transacoes`), calculando receitas menos despesas e preenchendo automaticamente o campo de aporte livre.
- **Leitura e Armazenamento de Metas**:
  - Identifica as classes de ativos existentes na carteira (ex: Ações, FIIs, Cripto, Renda Fixa).
  - Consulta e salva as porcentagens-alvo na tabela `configuracoes` (`alvo_classe_{c}`).
  - Valida se a soma das metas percentuais totaliza 100%.
- **Algoritmo de Sugestão de Compras por Ativo Individual**:
  - Calcula a alocação necessária para cada classe atingir a meta ideal.
  - Para cada classe defasada, busca os ativos no catálogo e cache de cotações (`cache_mercado`), priorizando os que estão mais distantes da proporção ideal e checando se o preço atual está abaixo do **Preço-Teto** configurado.
  - Calcula exatamente quantas cotas adquirir (cotas inteiras para ações/FIIs e fracionadas para criptoativos).
  - Exibe uma tabela rica de sugestões: `[Ativo | Classe | Preço Atual | Cotas a Comprar | Total a Investir | Status]`.
- **Execução Automatizada em 1 Clique**:
  - Botão **`🚀 Lançar Compras Sugeridas na Carteira`**: Registra todas as ordens de compra de uma vez, recalculando os Preços Médios ponderados na `carteira_atual` e registrando o aporte na categoria "Construção de Riqueza", disparando a atualização em tempo real de todas as telas.

---

### 3. `PaginaCarteira(QWidget)` (Tabela de Custódia)
- **Barra de Ações**:
  - Botão `➕ Registrar Compra` (entrada manual de compras individuais).
  - Botão `⚖️ Assessor Virtual (Rebalancear)` (dispara o rebalanceamento automatizado).
  - Botão `📑 Declaração IRPF` (abre o Relatório Auxiliar de Imposto de Renda).
- **Tabela com 9 Colunas**:
  - `Ativo` (Ticker)
  - `Classe` (Ações, FII, etc.)
  - `Setor`
  - `Qtd Total`
  - `Preço Médio (R$)`
  - `Preço Atual (R$)` (atualizado pelo cache de mercado)
  - `Total Investido (R$)`
  - `Saldo Atual (R$)`
  - `Ações` (Botão de exclusão centralizado com ícone de lixeira em tom coral)
- **Exclusão Segura em Cascata (`excluir_ativo`)**:
  - Remove as referências do ativo nas tabelas `carteira_atual`, `cache_mercado` e `ativos_catalogo`.
  - Recarrega a tabela e atualiza os KPIs da `PaginaResumo`.

---

## Interligação
- **Injeção de Dependências**: Recebe `self.db` (`DBManager`) e o callback `fn_atualizar_resumo` via construtor do `main.py`.
- **Tabelas Envolvidas**: `carteira_atual`, `ativos_catalogo`, `cache_mercado` e `configuracoes`.
