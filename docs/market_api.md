# Documentação: market_api.py

## Propósito
A classe `MarketAPI` é a ponte de comunicação da aplicação com serviços externos via internet para puxar cotações e indicadores financeiros em tempo real.

## Como Funciona
Como a Brapi (boa para ações brasileiras e indicadores) não possui boa cobertura para moedas (USD, EUR) e Criptomoedas, este arquivo adota uma **abordagem híbrida**.

### Principais Métodos
- **`buscar_dados_ativo(ticker)`**: O maestro principal. Se o ticket termina em `.SA` (Bolsa Brasileira), ele invoca a abordagem híbrida. Se não, manda direto para o fallback do YFinance.
- **`_buscar_hibrido(ticker_limpo, ticker_original)`**:
  - Tenta primeiro bater no endpoint da **Brapi** para pegar preço atual, Dividend Yield, P/L e P/VP.
  - Se algum dado vital (como P/VP ou DY) vier vazio ou nulo da Brapi, a classe aciona a biblioteca **`yfinance`** como um "plano de contenção", complementando o dicionário de resultados sem falhar a consulta do usuário.
- **`_buscar_no_yfinance(ticker)`**: Focado em puxar moedas (ex: `USDBRL=X`) e Criptomoedas (`BTC-USD`) diretamente pelo YFinance, já que a Brapi não lida com elas.
- **`buscar_dividendos_recentes(lista_tickers, dias=45)`**:
  - Consulta os proventos pagos nos últimos 45 dias agrupando os tickers da carteira.
  - Tenta bater na **Brapi** via `?dividends=true`.
  - Caso a Brapi retorne bloqueada (o endpoint de dividendos na Brapi exige plano pago *Startup*) ou sem dados, aciona automaticamente o motor de contingência via **`yfinance`**, que fornece o histórico de dividendos de ativos B3 de forma aberta e precisa.
- **`_tratar_numero(valor)`**: Uma "função escudo" que evita que valores `None` ou quebras de tipos de dados matemáticos corrompam a aplicação. Se algo vem sujo, ela converte para `0.0`.

## Interligação
- **Instanciado em**: `main.py` (`self.api = MarketAPI(...)`).
- **Injetado em**: 
  - `pagina_analise.py`: Utiliza o motor para pesquisar os tickers e ler os resultados para o usuário.
  - `pagina_config.py`: Utiliza a instância para substituir o *Token* em tempo de execução quando o usuário cadastra um novo na tela de configurações.
