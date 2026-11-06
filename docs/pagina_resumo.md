# Documentação: pagina_resumo.py

## Propósito
É o painel de controle principal (Dashboard) do investidor. Consolida métricas macroeconômicas de patrimônio líquido, distribuição percentual de investimentos por classe, taxa de poupança, gráficos patrimoniais e a ferramenta preditiva da **Máquina do Tempo** para projeção de independência financeira.

---

## Componentes e Como Funciona

### 1. KPIs de Alto Nível
- **Patrimônio Líquido Total**: Soma do saldo atual de todas as posições em carteira (`carteira_atual` cruzado com cotações de `cache_mercado`) somado ao saldo livre acumulado.
- **Taxa de Poupança / Aportes**: Percentual das receitas canalizadas para a categoria macro "Construção de Riqueza".
- **Renda Passiva Mensal**: Média e somatório de dividendos e proventos recentes recebidos.

---

### 2. Visualizações Gráficas (Matplotlib integrado ao PyQt6)
- **Canvas Integrado (`FigureCanvasQTAgg`)**:
  - Renderiza gráficos com tema escuro condizente com a paleta *Catppuccin Mocha*.
- **Gráfico de Alocação de Ativos (Donut / Pizza)**:
  - Distribuição percentual do patrimônio por classe de ativo (Ações, FIIs, Cripto, Renda Fixa).
  - Identifica desbalanceamentos visuais na carteira.
- **Gráfico de Rendimentos Acumulados**:
  - Exibe a trajetória dos proventos recebidos nos últimos meses, ilustrando o efeito da Bola de Neve.

---

### 3. A Máquina do Tempo (`calcular_maquina_tempo`)
- Simulador preditivo e didático de juros compostos voltado à independência financeira:
  - **Média Histórica de Aportes**: O sistema calcula a média mensal real de aportes do usuário com base nas transações da categoria "Construção de Riqueza".
  - **Inputs Customizáveis**:
    - Patrimônio Inicial (puxado automaticamente da carteira atual).
    - Aporte Mensal estimado.
    - Taxa de Rentabilidade Anual esperada (ex: 10% a.a.).
    - Meta Patrimonial de Independência Financeira (ex: R$ 1.000.000,00).
  - **Motor Matemático**:
    - Simula mês a mês a fórmula dos juros compostos com aportes periódicos:
      $$M_{t+1} = M_t \times (1 + i_{\text{mensal}}) + \text{Aporte}$$
    - Determina com precisão de data o **ano e o mês exatos** em que a meta estipulada será alcançada.

---

## Interligação
- **Injeção de Dependência**: Recebe `self.db` (`DBManager`) via construtor no `main.py`.
- **Ponto Central de Callbacks**:
  - O método `self.carregar_dados` é exportado e injetado como callback nas páginas:
    - `PaginaCarteira` (ao comprar ou excluir ativos).
    - `PaginaFinancas` (ao registrar receitas ou aportes).
    - `PaginaRendimentos` (ao confirmar novos dividendos).
  - Qualquer alteração patrimonial no aplicativo reflete instantaneamente nos gráficos e KPIs da Visão Geral sem necessidade de reiniciar o software.
