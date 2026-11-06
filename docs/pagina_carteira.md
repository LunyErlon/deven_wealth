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

### 2. `DialogoRebalanceamento(QDialog)` (O Assessor Virtual)
- Ferramenta matemática para guiar aportes mensais sem decisões emocionais.
- **Leitura e Armazenamento de Metas**:
  - Identifica as classes de ativos existentes na carteira (ex: Ações, FIIs, Cripto, Renda Fixa).
  - Consulta e salva as porcentagens-alvo na tabela `configuracoes` (`alvo_classe_{c}`).
  - Valida se a soma das metas percentuais totaliza 100%.
- **Algoritmo de Sugestão de Aporte**:
  - O usuário informa o valor total disponível para investir no mês.
  - O algoritmo calcula o patrimônio futuro projetado $(\text{Patrimônio Atual} + \text{Novo Aporte})$ e a quantia ideal que cada classe deveria ter.
  - Compara a alocação atual de cada classe contra o alvo e sugere a distribuição ótima do aporte para os ativos mais distantes do objetivo, equilibrando a carteira sem necessidade de vender posições.

---

### 3. `PaginaCarteira(QWidget)` (Tabela de Custódia)
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
