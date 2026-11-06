# Documentação: market_api.py

## Propósito
A classe `MarketAPI` é a ponte de comunicação da aplicação com serviços externos via internet para puxar cotações, indicadores financeiros e proventos em tempo real, mantendo tolerância a falhas e contingência automática.

## Como Funciona
Como a Brapi (excelente para ações brasileiras e indicadores) não possui boa cobertura para moedas (USD, EUR) e Criptomoedas, e seu endpoint de dividendos é restrito a planos pagos, este arquivo adota uma **arquitetura híbrida e resiliente**.

### Principais Métodos
- **`buscar_dados_ativo(ticker)`**: O maestro principal. Se o ticket termina em `.SA` (Bolsa Brasileira), ele invoca a abordagem híbrida. Se não, manda direto para o fallback do YFinance.
- **`_buscar_hibrido(ticker_limpo, ticker_original)`**:
  - Tenta primeiro bater no endpoint da **Brapi** para obter preço atual, Dividend Yield, P/L e P/VP.
  - Se algum dado vital (como P/VP ou DY) vier vazio ou nulo da Brapi, a classe aciona a biblioteca **`yfinance`** como um "plano de contenção", complementando o dicionário de resultados sem falhar a consulta do usuário.
- **`_buscar_no_yfinance(ticker)`**: Focado em puxar moedas (ex: `USDBRL=X`) e Criptomoedas (`BTC-USD`) diretamente pelo YFinance, já que a Brapi não lida com elas.
- **`buscar_dividendos_recentes(lista_tickers, dias=45)`**:
  - Consulta os proventos pagos nos últimos 45 dias agrupando os tickers da carteira.
  - Tenta primeiro bater na **Brapi** com o parâmetro `?dividends=true`.
  - **Fallback Automático (HTTP 403 / Free Tier)**: O endpoint de dividendos na Brapi exige o plano pago *Startup*. Ao detectar status code 403 ou ausência de dados, o método automaticamente delega a busca para o **`yfinance`** (`ticker.dividends`), que fornece o histórico completo de dividendos da B3 de forma aberta, gratuita e sem fricção.
  - Retorna uma lista limpa com dicionários contendo `ticker_id`, `data_pagamento`, `tipo_provento`, `valor_por_cota` e metadados.
- **`_tratar_numero(valor)`**: Uma "função escudo" que evita que valores `None`, strings vazias ou quebras de tipos de dados matemáticos corrompam a aplicação. Se algo vier corrompido, ela converte para `0.0`.

## Interligação
- **Instanciado em**: `main.py` (`self.api = MarketAPI(...)`).
- **Injetado em**: 
  - `pagina_analise.py`: Utiliza o motor para pesquisar os tickers e ler os resultados para o usuário.
  - `pagina_config.py`: Utiliza a instância para substituir o *Token* em tempo de execução quando o usuário cadastra um novo na tela de configurações.
  - `pagina_rendimentos.py`: Injetado no construtor para permitir o escaneamento manual de proventos via botão `🔍 Escanear Radar de Dividendos`.
  - `main.py` (Background Thread): Consumido diretamente pelo `WorkerRadarDividendos(QThread)` durante a inicialização assíncrona do aplicativo.
