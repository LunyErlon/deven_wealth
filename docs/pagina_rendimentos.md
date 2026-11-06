# Documentação: pagina_rendimentos.py

## Propósito
É o componente responsável pelo gerenciamento de renda passiva (dividendos, rendimentos de FIIs e Juros sobre Capital Próprio - JCP). Permite ao investidor registrar proventos recebidos, visualizar um gráfico do efeito bola de neve ao longo dos meses e gerenciar o histórico de pagamentos com opção de exclusão.

Inclui o **Radar Automático de Dividendos**, que realiza o cruzamento de dados em tempo real entre os ativos da carteira e a B3 (via Brapi e YFinance), com o princípio de **Atrito Positivo** para solucionar o desafio da **Data-Com**.

---

## Componentes e Como Funciona

### 1. `WorkerRadarDividendos(QThread)` (Varredura Paralela)
- Executa em segundo plano sem congelar a interface gráfica do PyQt6.
- **Thread-Safety com SQLite**:
  - Como conexões SQLite não podem transitar entre threads em Python, o `main.py` ou a página realizam as consultas no banco local na thread principal da UI, passando apenas dicionários puros (`dict`) para o Worker.
- O Worker consome `MarketAPI.buscar_dividendos_recentes(tickers, dias=45)`, cruza os proventos pagos com os já registrados e emite o sinal Qt `dividendos_encontrados(list)` apenas se houver novidades.

---

### 2. `DialogRadarDividendos(QDialog)` (Atrito Positivo & O Desafio da Data-Com)
- Pop-up de validação acionado automaticamente na inicialização (se houver proventos) ou sob demanda pelo botão manual.
- **O Desafio da Data-Com**:
  - A API externa informa a data de pagamento e o valor por cota, mas **não** sabe a data exata em que o investidor comprou as cotas na corretora.
  - Apenas o usuário sabe se suas cotas estavam sob custódia no dia de corte (*Data-Com*).
  - O diálogo sugere a quantidade total de cotas atual, mas disponibiliza uma coluna editável de **Quantidade Base de Cotas** (`QDoubleSpinBox`).
  - Ao alterar as cotas, o valor líquido total é recalculado dinamicamente em tempo real.
- **Persistência em Lote de Alta Performance**:
  - O método `confirmar_recebimentos()` grava todos os proventos validados de uma só vez via `self.db.executar_query_lote()` (`cursor.executemany`), garantindo gravação instantânea e atômica.
  - Aciona os callbacks `fn_atualizar_rendimentos` e `fn_atualizar_resumo` para refletir imediatamente nos gráficos de patrimônio e proventos.

---

### 3. `PaginaRendimentos` (Interface Principal)
- **Cabeçalho com Botão do Radar**:
  - Contém o botão `🔍 Escanear Radar de Dividendos`, que ativa o método `escanear_radar_manual()` mostrando feedback visual e abrindo o pop-up com as novidades da B3.
- **Formulário de Entrada Manual**:
  - Combo de ativos alimentado exclusivamente pelos ativos presentes em `carteira_atual`.
  - Data de pagamento (`QDateEdit` com calendário).
  - Tipo de provento ("Rendimento", "Dividendo", "JCP").
  - Cotas base e valor líquido total.
- **Feedback Didático ("A Mágica dos Juros Compostos")**:
  - Ao registrar um provento, o método `mostrar_magica_didatica()` calcula:
    - Valor líquido unitário por cota.
    - *Yield on Cost* (YoC) real sobre o preço médio do investidor.
    - O **"Número Mágico"**: quantas cotas são necessárias para que os proventos mensais comprem uma nova cota do ativo automaticamente.
- **Gráfico do Efeito Bola de Neve**:
  - Gráfico de barras integrado via `matplotlib` (`FigureCanvasQTAgg`), agrupado cronologicamente por mês (`YYYY-MM`), demonstrando a evolução da renda passiva.
- **Tabela de Histórico e Exclusão**:
  - Exibe o histórico de proventos com botão de exclusão em tom coral (`#f38ba8`) estilizado com `qtawesome`.
  - O método `excluir_rendimento(id)` solicita confirmação de segurança e remove o registro do banco de dados, recalculando a Bola de Neve instantaneamente.

---

## Interligação
- **Recebe via Construtor**:
  - `self.db`: Instância de persistência local SQLite.
  - `self.api`: Instância da `MarketAPI` para o radar manual.
  - `fn_atualizar_resumo`: Callback para atualizar o Dashboard Geral (`PaginaResumo`) após registrar proventos.
- **Tabelas Envolvidas**: `carteira_atual`, `rendimentos` e `ativos_catalogo`.
