import yfinance as yf
import requests

class MarketAPI:
    def __init__(self, token_brapi=""):
        self.token_brapi = token_brapi
        self.url_base_brapi = "https://brapi.dev/api/quote"

    def _tratar_numero(self, valor, multiplicador=1.0):
        """Função escudo: Se o valor vier None, vazio ou quebrado, converte para 0.0 com segurança."""
        if valor is None:
            return 0.0
        try:
            return round(float(valor) * multiplicador, 2)
        except (ValueError, TypeError):
            return 0.0

    def buscar_dados_ativo(self, ticker):
        print(f"Buscando dados para {ticker}...")
        
        if ticker.endswith(".SA"):
            ticker_limpo = ticker.replace(".SA", "")
            return self._buscar_hibrido(ticker_limpo, ticker)
        else:
            return self._buscar_no_yfinance(ticker)

    def _buscar_hibrido(self, ticker_limpo, ticker_original):
        """Tenta buscar na Brapi e completa com o yfinance se faltar algo."""
        dados_finais = {
            "ticker": ticker_original,
            "nome": ticker_limpo,
            "preco_atual": 0.0,
            "dy_atual": 0.0,
            "p_l": 0.0,
            "p_vp": 0.0
        }

        # 1. Tenta a Brapi primeiro
        try:
            url = f"{self.url_base_brapi}/{ticker_limpo}?token={self.token_brapi}"
            resposta = requests.get(url)
            dados_brapi = resposta.json()
            
            if "results" in dados_brapi:
                info = dados_brapi["results"][0]
                dados_finais["nome"] = info.get("shortName", ticker_limpo)
                dados_finais["preco_atual"] = self._tratar_numero(info.get("regularMarketPrice"))
                dados_finais["p_l"] = self._tratar_numero(info.get("priceEarnings"))
                # A Brapi às vezes traz o DY como dividendYield (em porcentagem)
                dados_finais["dy_atual"] = self._tratar_numero(info.get("dividendYield", 0.0))
                dados_finais["p_vp"] = self._tratar_numero(info.get("priceToBook"))
        except Exception as e:
            print(f"Aviso Brapi: {e}")

        # 2. Se algum dado fundamentalista vital ainda for 0.0, pede socorro ao yfinance
        if dados_finais["dy_atual"] == 0.0 or dados_finais["p_vp"] == 0.0:
            try:
                ativo_yf = yf.Ticker(ticker_original)
                info_yf = ativo_yf.info
                
                if dados_finais["preco_atual"] == 0.0:
                    dados_finais["preco_atual"] = self._tratar_numero(info_yf.get("currentPrice", info_yf.get("regularMarketPrice")))
                
                if dados_finais["dy_atual"] == 0.0:
                    # Pega o DY cru
                    dy_cru = info_yf.get("dividendYield")
                    if dy_cru is not None:
                        dy_float = float(dy_cru)
                        # Se vier decimal (ex: 0.13), multiplica. Se já vier inteiro (ex: 13.17), mantém.
                        if dy_float < 1.0:
                            dy_float *= 100
                        dados_finais["dy_atual"] = round(dy_float, 2)
                
                if dados_finais["p_vp"] == 0.0:
                    dados_finais["p_vp"] = self._tratar_numero(info_yf.get("priceToBook"))
                    
                if dados_finais["p_l"] == 0.0:
                    dados_finais["p_l"] = self._tratar_numero(info_yf.get("trailingPE"))
            except Exception:
                pass # Ignora erro do yf e segue com o que conseguiu

        return dados_finais

    def _buscar_no_yfinance(self, ticker):
        """Busca moedas e criptos."""
        try:
            ativo = yf.Ticker(ticker)
            info = ativo.info
            preco = info.get("currentPrice", info.get("regularMarketPrice", 0.0))
            
            return {
                "ticker": ticker,
                "nome": info.get("shortName", ticker),
                "preco_atual": self._tratar_numero(preco),
                "dy_atual": 0.0,
                "p_l": 0.0,
                "p_vp": 0.0
            }
        except Exception as e:
            print(f"Erro no yfinance: {e}")
            return None

    def buscar_dividendos_recentes(self, lista_tickers, dias=45):
        """
        Fase 1: O Rastreador na Nuvem de Dividendos (Radar B3).
        Agrupa os ativos e consulta a Brapi (?dividends=true).
        Se a Brapi retornar bloqueada (requer plano pago Startup) ou sem dados,
        aciona o motor de contingência inteligente via yfinance.
        Filtra os pagamentos ocorridos nos últimos 'dias' (padrão 45 dias).
        """
        import datetime
        import pandas as pd

        hoje = datetime.date.today()
        data_limite = hoje - datetime.timedelta(days=dias)
        eventos_dividendos = []

        if not lista_tickers:
            return eventos_dividendos

        # 1. Tentar Brapi com ?dividends=true
        tickers_limpos = [t.replace('.SA', '').strip().upper() for t in lista_tickers if t]
        tickers_brapi_str = ",".join(tickers_limpos)
        usar_fallback_yf = False

        if tickers_limpos:
            try:
                url = f"{self.url_base_brapi}/{tickers_brapi_str}?token={self.token_brapi}&dividends=true"
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])
                    for res in results:
                        ticker = res.get("symbol", "")
                        div_data = res.get("dividendsData", {})
                        cash_divs = []
                        if isinstance(div_data, dict):
                            cash_divs = div_data.get("cashDividends", [])
                        elif "dividends" in res:
                            cash_divs = res.get("dividends", [])

                        for div in cash_divs:
                            pay_date_str = div.get("paymentDate") or div.get("date")
                            if not pay_date_str:
                                continue
                            try:
                                dt_pagamento = pd.to_datetime(pay_date_str).date()
                            except Exception:
                                continue

                            if data_limite <= dt_pagamento <= hoje:
                                rate = float(div.get("rate") or div.get("amount") or 0.0)
                                if rate > 0:
                                    label = str(div.get("label") or ("Rendimento" if "11" in ticker else "Dividendo"))
                                    tipo = "JCP" if "JCP" in label.upper() else ("Rendimento" if "11" in ticker else "Dividendo")
                                    eventos_dividendos.append({
                                        "ticker_id": f"{ticker}.SA",
                                        "ticker_curto": ticker,
                                        "data_pagamento": dt_pagamento.strftime("%Y-%m-%d"),
                                        "valor_por_cota": round(rate, 4),
                                        "tipo_provento": tipo,
                                        "fonte": "Brapi"
                                    })
                else:
                    usar_fallback_yf = True
            except Exception as e:
                print(f"Aviso Brapi dividendos: {e}")
                usar_fallback_yf = True

        # 2. Motor de Contingência via yfinance (caso Brapi seja plano Free ou falhe)
        if usar_fallback_yf or not eventos_dividendos:
            for ticker in lista_tickers:
                ticker_yf = ticker if ticker.endswith(".SA") else f"{ticker}.SA"
                ticker_curto = ticker_yf.replace(".SA", "")
                try:
                    ativo_yf = yf.Ticker(ticker_yf)
                    divs = ativo_yf.dividends
                    if divs is not None and not divs.empty:
                        for dt_idx, rate in divs.items():
                            try:
                                dt_pagamento = pd.to_datetime(dt_idx).date()
                            except Exception:
                                continue

                            if data_limite <= dt_pagamento <= hoje:
                                rate_val = float(rate)
                                if rate_val > 0:
                                    eventos_dividendos.append({
                                        "ticker_id": ticker_yf,
                                        "ticker_curto": ticker_curto,
                                        "data_pagamento": dt_pagamento.strftime("%Y-%m-%d"),
                                        "valor_por_cota": round(rate_val, 4),
                                        "tipo_provento": "Rendimento" if "11" in ticker_curto else "Dividendo",
                                        "fonte": "yfinance"
                                    })
                except Exception as e:
                    print(f"Aviso yfinance dividendos ({ticker}): {e}")

        # Remove duplicatas se houver
        eventos_unicos = []
        chaves_vistas = set()
        for ev in eventos_dividendos:
            chave = (ev["ticker_curto"], ev["data_pagamento"], ev["valor_por_cota"])
            if chave not in chaves_vistas:
                chaves_vistas.add(chave)
                eventos_unicos.append(ev)

        return eventos_unicos

# Bloco de teste
if __name__ == "__main__":
    api = MarketAPI(token_brapi="COLE_SEU_TOKEN_AQUI")
    
    ativos_para_testar = ["PETR4.SA", "MXRF11.SA", "USDBRL=X", "BTC-USD"]
    
    for ativo in ativos_para_testar:
        resultado = api.buscar_dados_ativo(ativo)
        print(f"Resultado: {resultado}\n")