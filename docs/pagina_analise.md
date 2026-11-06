# Documentação: pagina_analise.py

## Propósito
É o componente de "Busca de Cotações" e porta de entrada (Catálogo) para inclusão de novos ativos no ecossistema local do Deven Wealth. Também gerencia o **Radar de Oportunidades**, monitorando preços-teto configurados pelo investidor contra as cotações de mercado.

---

## Componentes e Como Funciona

### 1. Barra de Pesquisa e Consulta em Tempo Real
- **Campo de Busca (`QLineEdit`)**: O investidor digita o ticker (ex: `PETR4`, `MXRF11`, `BTC-USD`, `USDBRL=X`).
- **Execução Desacoplada (`executar_busca`)**:
  - Aciona o motor híbrido da `MarketAPI.buscar_dados_ativo()`.
  - Dispara `QApplication.processEvents()` para garantir fluidez na UI sem congelamentos perceptíveis.
  - Exibe um cartão estilizado com:
    - **Cotação Atual**
    - **Dividend Yield (DY %)**
    - **P/VP (Preço sobre Valor Patrimonial)**
    - **P/L (Preço sobre Lucro)**
    - Nome da Empresa / Fundo e Setor de Atuação
  - Habilita o botão **"➕ Salvar no Catálogo"**.

---

### 2. Persistência no Catálogo (`salvar_ativo_banco`)
- Ao clicar em salvar:
  - Grava os metadados estáticos na tabela `ativos_catalogo` (`ticker`, `nome`, `classe`, `setor`).
  - Grava os indicadores financeiros em tempo real na tabela `cache_mercado` (`preco_atual`, `dy_atual`, `p_vp`, `p_l`, `ultima_atualizacao`).
  - Aciona o callback `fn_atualizar_carteira` para que a tela de Carteira imediatamente disponibilize o novo ativo para registro de compras.
  - Atualiza a visualização do Radar de Oportunidades.

---

### 3. O Radar de Oportunidades & Preço-Teto
- **Tabela Interativa**: Lista todos os ativos já cadastrados no catálogo local.
- **Definição de Preço-Teto (`definir_preco_teto`)**:
  - Permite ao investidor clicar na linha do ativo e estabelecer o valor máximo que aceita pagar (baseado em valuation ou Graham/Bazin).
  - O valor é gravado na coluna `preco_teto` da tabela `ativos_catalogo`.
- **Destaque Visual ("🎯 OPORTUNIDADE")**:
  - Compara continuamente `preco_atual <= preco_teto`.
  - Se a cotação estiver abaixo ou igual ao teto, a linha da tabela é destacada com fundo em verde brilhante e o badge **"🎯 OPORTUNIDADE"**, indicando momento favorável para compra.

---

## Interligação
- **Injeção de Dependências**:
  - `self.db` (`DBManager`): Para gravar e consultar ativos e indicadores.
  - `self.api` (`MarketAPI`): Para executar requisições HTTP e capturar dados de mercado.
  - `fn_atualizar_carteira`: Callback para sincronizar o catálogo com a `PaginaCarteira`.
- **Tabelas Envolvidas**: `ativos_catalogo` e `cache_mercado`.
