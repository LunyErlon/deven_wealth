from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QApplication, QTableWidget, QTableWidgetItem, QHeaderView, QInputDialog, QMessageBox
from PyQt6.QtCore import Qt

class PaginaAnalise(QWidget):
    def __init__(self, db, api, fn_atualizar_carteira=None):
        super().__init__()
        self.db = db
        self.api = api
        self.dados_pesquisa_atual = None
        self.fn_atualizar_carteira = fn_atualizar_carteira
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        titulo = QLabel("Análise de Mercado")
        titulo.setObjectName("tituloPagina")
        
        subtitulo = QLabel("Digite o código do ativo para buscar os dados fundamentais, lembre-se de utilizar .SA para ações brasileiras.")
        subtitulo.setStyleSheet("color: #a6adc8; font-size: 16px; margin-top: 10px; margin-bottom: 20px;")
        
        # Layout horizontal para a barra de pesquisa
        layout_busca = QHBoxLayout()
        
        self.input_ticker = QLineEdit()
        self.input_ticker.setObjectName("inputBusca")
        self.input_ticker.setPlaceholderText("Ex: PETR4.SA, MXRF11.SA, USDBRL=X")
        # Permite dar "Enter" para buscar
        self.input_ticker.returnPressed.connect(self.executar_busca) 
        
        self.btn_buscar = QPushButton("Buscar Ativo")
        self.btn_buscar.setObjectName("btnBuscar")
        self.btn_buscar.clicked.connect(self.executar_busca)
        
        layout_busca.addWidget(self.input_ticker)
        layout_busca.addWidget(self.btn_buscar)
        
        # Label onde o resultado vai aparecer
        self.label_resultado_analise = QLabel("")
        self.label_resultado_analise.setObjectName("resultadoAnalise")

        # Botão de salvar (Apenas visível quando tem resultado)
        self.btn_salvar = QPushButton("💾 Salvar no Catálogo")
        self.btn_salvar.setObjectName("btnSalvar")
        self.btn_salvar.clicked.connect(self.salvar_ativo_banco)
        self.btn_salvar.hide() # Começa escondido
        
        # --- TABELA RADAR DE OPORTUNIDADES ---
        lbl_radar = QLabel("📡 Radar de Oportunidades (Preço Teto)")
        lbl_radar.setStyleSheet("font-size: 18px; font-weight: bold; color: #a6e3a1; margin-top: 20px;")
        
        self.tabela_radar = QTableWidget()
        self.tabela_radar.setColumnCount(5)
        self.tabela_radar.setHorizontalHeaderLabels(["Ticker", "Preço Atual", "Preço Teto", "Status", "Ação"])
        self.tabela_radar.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Empilhando tudo na página
        layout.addWidget(titulo)
        layout.addWidget(subtitulo)
        layout.addLayout(layout_busca)
        layout.addWidget(self.label_resultado_analise)
        layout.addWidget(self.btn_salvar)
        
        layout.addWidget(lbl_radar)
        layout.addWidget(self.tabela_radar)
        
        self.carregar_radar()

    def executar_busca(self):
        """A fenda que processa a pesquisa na API."""
        ticker = self.input_ticker.text().strip().upper()
        
        if not ticker:
            self.label_resultado_analise.setText("Por favor, digite um código de ativo.")
            return
            
        self.label_resultado_analise.setText(f"Consultando dados para {ticker}... Aguarde.")
        self.btn_salvar.hide() # Esconde o botão enquanto busca
        QApplication.processEvents() # Destrava a interface para mostrar a mensagem
        
        # Aciona o motor
        dados = self.api.buscar_dados_ativo(ticker)
        
        if dados:
            # 1. Guarda os dados na memória (Para usar no botão salvar depois)
            self.dados_pesquisa_atual = dados
            
            # Formatando o HTML para exibir na tela
            texto_formatado = (
                f"<h2>{dados['nome']} ({dados['ticker']})</h2>"
                f"<p><b>Preço Atual:</b> R$ {dados['preco_atual']}</p>"
                f"<p><b>Dividend Yield:</b> {dados['dy_atual']}%</p>"
                f"<p><b>P/L (Preço sobre Lucro):</b> {dados['p_l']}</p>"
                f"<p><b>P/VP (Preço sobre VPA):</b> {dados['p_vp']}</p>"
            )
            self.label_resultado_analise.setText(texto_formatado)
            # 2. Mostra o botão "Salvar"
            self.btn_salvar.show()
        else:
            self.dados_pesquisa_atual = None
            self.label_resultado_analise.setText(f"Falha ao encontrar o ativo {ticker}. Verifique o código.")

    def salvar_ativo_banco(self):
        """A fenda que pega os dados da memória e injeta no SQLite"""
        if not self.dados_pesquisa_atual:
            return
            
        ticker = self.dados_pesquisa_atual['ticker']
        
        # Automação simples para adivinhar a "classe" do ativo
        classe = "Ação"
        if ticker.endswith("11.SA"): classe = "FII"
        elif ticker.endswith("=X"): classe = "Moeda"
        elif ticker.endswith("-USD"): classe = "Cripto"

        # 1. Salva no Catálogo (Se já existir, o IGNORE impede erro)
        query_catalogo = "INSERT OR IGNORE INTO ativos_catalogo (ticker, classe, setor) VALUES (?, ?, ?)"
        self.db.executar_query(query_catalogo, (ticker, classe, "Não Definido"))
        
        # 2. Atualiza o Cache de Preços (Se já existir, o REPLACE sobrescreve com os valores de hoje)
        query_cache = """
        INSERT OR REPLACE INTO cache_mercado 
        (ticker_id, ultima_atualizacao, preco_atual, dy_atual, p_vp, p_l)
        VALUES (?, datetime('now', 'localtime'), ?, ?, ?, ?)
        """
        self.db.executar_query(query_cache, (
            ticker,
            self.dados_pesquisa_atual['preco_atual'],
            self.dados_pesquisa_atual['dy_atual'],
            self.dados_pesquisa_atual['p_vp'],
            self.dados_pesquisa_atual['p_l']
        ))
        
        # 3. Feedback visual
        texto_atual = self.label_resultado_analise.text()
        self.label_resultado_analise.setText(texto_atual + "<br><br><span style='color: #a6e3a1;'>✅ Ativo salvo no catálogo com sucesso!</span>")
        self.btn_salvar.hide() # Esconde para não salvar duplicado atoa
        
        if self.fn_atualizar_carteira:
            self.fn_atualizar_carteira()
            
        self.carregar_radar()

    def carregar_radar(self):
        self.tabela_radar.setRowCount(0)
        
        query = """
            SELECT a.ticker, a.preco_teto, c.preco_atual
            FROM ativos_catalogo a
            JOIN cache_mercado c ON a.ticker = c.ticker_id
            ORDER BY a.ticker
        """
        resultados = self.db.buscar_dados(query)
        
        for linha_idx, dados in enumerate(resultados):
            self.tabela_radar.insertRow(linha_idx)
            
            ticker = dados['ticker']
            preco_atual = float(dados['preco_atual'])
            preco_teto = float(dados['preco_teto']) if dados.get('preco_teto') else 0.0
            
            status = "Sem Teto"
            if preco_teto > 0:
                if preco_atual <= preco_teto:
                    status = "🎯 OPORTUNIDADE"
                else:
                    status = "Caro"
            
            item_ticker = QTableWidgetItem(ticker)
            item_atual = QTableWidgetItem(f"R$ {preco_atual:.2f}")
            item_teto = QTableWidgetItem(f"R$ {preco_teto:.2f}" if preco_teto > 0 else "Não Definido")
            
            item_status = QTableWidgetItem(status)
            if preco_teto > 0:
                from PyQt6.QtGui import QColor
                if preco_atual <= preco_teto:
                    item_status.setBackground(QColor(166, 227, 161)) # Verde catppuccin
                    item_status.setForeground(QColor(17, 17, 27)) # Texto escuro
                    item_status.setFont(self.font())
                else:
                    item_status.setBackground(QColor(243, 139, 168)) # Vermelho catppuccin
                    item_status.setForeground(QColor(17, 17, 27))
            
            self.tabela_radar.setItem(linha_idx, 0, item_ticker)
            self.tabela_radar.setItem(linha_idx, 1, item_atual)
            self.tabela_radar.setItem(linha_idx, 2, item_teto)
            self.tabela_radar.setItem(linha_idx, 3, item_status)
            
            btn_teto = QPushButton("Definir Teto")
            btn_teto.setStyleSheet("background-color: transparent; color: #89b4fa; font-weight: bold; text-decoration: underline;")
            btn_teto.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_teto.clicked.connect(lambda checked, t=ticker: self.definir_preco_teto(t))
            self.tabela_radar.setCellWidget(linha_idx, 4, btn_teto)

    def definir_preco_teto(self, ticker):
        valor, ok = QInputDialog.getDouble(self, "Definir Preço Teto", f"Qual o preço máximo (Teto) para investir em {ticker}?", decimals=2, min=0.0, max=10000.0)
        if ok:
            self.db.executar_query("UPDATE ativos_catalogo SET preco_teto = ? WHERE ticker = ?", (valor, ticker))
            self.carregar_radar()
            QMessageBox.information(self, "Sucesso", f"O Radar agora irá te avisar quando {ticker} cair abaixo de R$ {valor:.2f}!")
