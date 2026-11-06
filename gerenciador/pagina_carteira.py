from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QFormLayout, QDoubleSpinBox, QMessageBox
from PyQt6.QtCore import Qt
import qtawesome as qta

class DialogoCompra(QDialog):
    def __init__(self, ticker, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Registrar Compra - {ticker}")
        self.resize(320, 200)
        
        layout = QFormLayout(self)
        
        # Campo para Quantidade (Aceita decimais por causa de criptos)
        self.input_qtd = QDoubleSpinBox()
        self.input_qtd.setGroupSeparatorShown(True)
        self.input_qtd.setRange(0.0001, 1000000.0)
        self.input_qtd.setDecimals(4)
        
        # Campo para Preço Pago
        self.input_preco = QDoubleSpinBox()
        self.input_preco.setGroupSeparatorShown(True)
        self.input_preco.setRange(0.01, 1000000.0)
        self.input_preco.setDecimals(2)
        self.input_preco.setPrefix("R$ ")
        
        # Botão Salvar
        self.btn_confirmar = QPushButton("Confirmar Compra")
        self.btn_confirmar.setStyleSheet("background-color: #a6e3a1; color: #11111b; font-weight: bold; padding: 10px; border-radius: 6px;")
        self.btn_confirmar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirmar.clicked.connect(self.accept) # 'accept' fecha o pop-up com sucesso
        
        layout.addRow("Quantidade de Cotas:", self.input_qtd)
        layout.addRow("Preço Pago (Unidade):", self.input_preco)
        layout.addRow("", self.btn_confirmar)
        
    def get_dados(self):
        return self.input_qtd.value(), self.input_preco.value()

class DialogoRebalanceamento(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Assessor Virtual - Rebalanceamento de Carteira")
        self.setMinimumWidth(600)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        lbl_info = QLabel("Defina a % ideal para cada classe de ativo. O sistema indicará onde você deve investir seu aporte para balancear a carteira.")
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("color: #a6adc8; margin-bottom: 10px;")
        layout.addWidget(lbl_info)
        
        # Puxa o total atual por classe
        query_atual = """
            SELECT a.classe, SUM(cart.quantidade_total * c.preco_atual) as total
            FROM carteira_atual cart
            JOIN ativos_catalogo a ON cart.ticker_id = a.ticker
            JOIN cache_mercado c ON cart.ticker_id = c.ticker_id
            GROUP BY a.classe
        """
        res_atual = self.db.buscar_dados(query_atual)
        self.patrimonio_por_classe = {r['classe']: float(r['total']) for r in res_atual}
        self.patrimonio_total = sum(self.patrimonio_por_classe.values())
        
        res_classes = self.db.buscar_dados("SELECT DISTINCT classe FROM ativos_catalogo ORDER BY classe")
        todas_classes = [r['classe'] for r in res_classes]
        
        self.inputs_alvo = {}
        form_layout = QFormLayout()
        
        for c in todas_classes:
            spin = QDoubleSpinBox()
            spin.setGroupSeparatorShown(True)
            spin.setRange(0, 100)
            spin.setSuffix("%")
            
            res_alvo = self.db.buscar_dados(f"SELECT valor FROM configuracoes WHERE chave='alvo_classe_{c}'")
            if res_alvo:
                spin.setValue(float(res_alvo[0]['valor']))
            else:
                spin.setValue(0.0)
                
            self.inputs_alvo[c] = spin
            
            atual_val = self.patrimonio_por_classe.get(c, 0.0)
            atual_pct = (atual_val / self.patrimonio_total * 100) if self.patrimonio_total > 0 else 0
            
            lbl_classe = QLabel(f"{c} (Atual: {atual_pct:.1f}% | R$ {atual_val:.2f}):")
            lbl_classe.setStyleSheet("font-weight: bold;")
            form_layout.addRow(lbl_classe, spin)
            
        layout.addLayout(form_layout)
        
        layout_aporte = QHBoxLayout()
        lbl_aporte = QLabel("Valor do Aporte Mensal Livre: R$")
        lbl_aporte.setStyleSheet("color: #a6e3a1; font-weight: bold;")
        layout_aporte.addWidget(lbl_aporte)
        self.input_aporte = QDoubleSpinBox()
        self.input_aporte.setGroupSeparatorShown(True)
        self.input_aporte.setRange(0, 10000000)
        self.input_aporte.setDecimals(2)
        self.input_aporte.setStyleSheet("color: #a6e3a1; font-weight: bold;")
        layout_aporte.addWidget(self.input_aporte)
        layout.addLayout(layout_aporte)
        
        btn_calcular = QPushButton("Calcular Rebalanceamento")
        btn_calcular.setStyleSheet("background-color: #89b4fa; color: #11111b; font-weight: bold; padding: 10px; margin-top: 10px;")
        btn_calcular.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_calcular.clicked.connect(self.calcular_rebalanceamento)
        layout.addWidget(btn_calcular)
        
        self.lbl_resultado = QLabel("")
        self.lbl_resultado.setWordWrap(True)
        self.lbl_resultado.setStyleSheet("background-color: #313244; padding: 15px; border-radius: 8px; font-size: 15px; line-height: 1.5;")
        self.lbl_resultado.hide()
        layout.addWidget(self.lbl_resultado)
        
    def calcular_rebalanceamento(self):
        soma_alvos = sum(spin.value() for spin in self.inputs_alvo.values())
        if abs(soma_alvos - 100.0) > 0.01:
            QMessageBox.warning(self, "Aviso", f"A soma das porcentagens alvo deve ser exatamente 100%. Atual: {soma_alvos:.1f}%")
            return
            
        aporte = self.input_aporte.value()
        if aporte <= 0:
            QMessageBox.warning(self, "Aviso", "Insira um valor de aporte maior que zero.")
            return
            
        patrimonio_futuro = self.patrimonio_total + aporte
        recomendacoes = []
        
        for c, spin in self.inputs_alvo.items():
            self.db.executar_query("INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?, ?)", (f"alvo_classe_{c}", str(spin.value())))
            
            alvo_pct = spin.value() / 100.0
            valor_ideal = patrimonio_futuro * alvo_pct
            valor_atual = self.patrimonio_por_classe.get(c, 0.0)
            
            diferenca = valor_ideal - valor_atual
            if diferenca > 0:
                recomendacoes.append((c, diferenca))
                
        recomendacoes.sort(key=lambda x: x[1], reverse=True)
        
        texto = "<b>🎯 Plano de Ação (Onde Investir seu Aporte):</b><br><br>"
        aporte_restante = aporte
        
        for c, dif in recomendacoes:
            if aporte_restante <= 0:
                break
            valor_aportar = min(dif, aporte_restante)
            texto += f"• Compre <b>R$ {valor_aportar:.2f}</b> em ativos da classe <b>{c}</b><br>"
            aporte_restante -= valor_aportar
            
        if aporte_restante > 0:
            texto += f"<br><span style='color: #f9e2af;'>Você ainda tem R$ {aporte_restante:.2f} livres após equilibrar as metas. Reinvista nos seus melhores ativos!</span>"
            
        self.lbl_resultado.setText(texto)
        self.lbl_resultado.show()

class PaginaCarteira(QWidget):
    def __init__(self, db, fn_atualizar_resumo=None):
        super().__init__()
        self.db = db
        self.fn_atualizar_resumo = fn_atualizar_resumo
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        titulo = QLabel("Minha Carteira (Catálogo)")
        titulo.setObjectName("tituloPagina")
        
        # Layout horizontal para botões de ação
        layout_acoes = QHBoxLayout()
        self.btn_registrar_compra = QPushButton("➕ Registrar Compra")
        self.btn_registrar_compra.setStyleSheet("background-color: #f9e2af; color: #11111b; font-weight: bold; padding: 10px; border-radius: 5px; max-width: 200px;")
        self.btn_registrar_compra.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_registrar_compra.clicked.connect(self.abrir_registro_compra)
        
        self.btn_rebalancear = QPushButton("⚖️ Assessor Virtual (Rebalancear)")
        self.btn_rebalancear.setStyleSheet("background-color: #89b4fa; color: #11111b; font-weight: bold; padding: 10px; border-radius: 5px;")
        self.btn_rebalancear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_rebalancear.clicked.connect(self.abrir_rebalanceamento)
        
        layout_acoes.addWidget(self.btn_registrar_compra)
        layout_acoes.addWidget(self.btn_rebalancear)
        layout_acoes.addStretch() # Empurra os botões pra esquerda
        
        self.tabela_carteira = QTableWidget()
        # Vamos aumentar para 8 colunas para mostrar a quantidade e o preço médio!
        self.tabela_carteira.setColumnCount(9) 
        self.tabela_carteira.setHorizontalHeaderLabels(["Ticker", "Classe", "Qtd", "Preço Médio", "Preço Atual", "DY (%)", "P/VP", "Total Atual", "Excluir"])
        
        header = self.tabela_carteira.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(titulo)
        layout.addLayout(layout_acoes) # Adiciona a barra de botões
        layout.addWidget(self.tabela_carteira)

    def carregar_dados(self):
        """Limpa a tabela e busca os dados atualizados no SQLite."""
        self.tabela_carteira.setRowCount(0) # Zera as linhas da tabela
        
        # O SQL une as informações fixas (catalogo) com as dinâmicas (cache)
        query = """
            SELECT 
                a.ticker, a.classe, 
                IFNULL(cart.quantidade_total, 0) as qtd, 
                IFNULL(cart.preco_medio, 0) as pm,
                c.preco_atual, c.dy_atual, c.p_vp
            FROM ativos_catalogo a
            JOIN cache_mercado c ON a.ticker = c.ticker_id
            LEFT JOIN carteira_atual cart ON a.ticker = cart.ticker_id
        """
        resultados = self.db.buscar_dados(query)
        
        # Preenchendo linha por linha
        for linha_idx, dados in enumerate(resultados):
            self.tabela_carteira.insertRow(linha_idx)
            
            # Calculando o Total Patrimonial (Qtd * Preço Atual)
            patrimonio_atual = float(dados['qtd']) * float(dados['preco_atual'])
            
            # Convertendo os valores para o formato que a tabela aceita (QTableWidgetItem)
            self.tabela_carteira.setItem(linha_idx, 0, QTableWidgetItem(dados['ticker']))
            self.tabela_carteira.setItem(linha_idx, 1, QTableWidgetItem(dados['classe']))
            self.tabela_carteira.setItem(linha_idx, 2, QTableWidgetItem(f"{dados['qtd']:.4f}")) # 4 casas por causa de cripto
            self.tabela_carteira.setItem(linha_idx, 3, QTableWidgetItem(f"R$ {dados['pm']:.2f}"))
            self.tabela_carteira.setItem(linha_idx, 4, QTableWidgetItem(f"R$ {dados['preco_atual']:.2f}"))
            self.tabela_carteira.setItem(linha_idx, 5, QTableWidgetItem(f"{dados['dy_atual']}%"))
            self.tabela_carteira.setItem(linha_idx, 6, QTableWidgetItem(f"{dados['p_vp']}"))
            self.tabela_carteira.setItem(linha_idx, 7, QTableWidgetItem(f"R$ {patrimonio_atual:.2f}"))

            # --- NOVO: BOTÃO DE EXCLUIR ---
            widget_excluir = QWidget()
            layout_excluir = QHBoxLayout(widget_excluir)
            layout_excluir.setContentsMargins(0, 0, 0, 0)
            layout_excluir.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            btn_excluir = QPushButton()
            btn_excluir.setIcon(qta.icon('fa5s.trash-alt', color='#f38ba8'))
            btn_excluir.setStyleSheet("background-color: transparent; border: none;")
            btn_excluir.setCursor(Qt.CursorShape.PointingHandCursor)
            
            # Truque do Python: o 't=dados['ticker']' garante que o botão lembre qual ativo ele deve apagar
            btn_excluir.clicked.connect(lambda checked, t=dados['ticker']: self.excluir_ativo(t))
            
            layout_excluir.addWidget(btn_excluir)
            self.tabela_carteira.setCellWidget(linha_idx, 8, widget_excluir)

    def excluir_ativo(self, ticker):
        # Pergunta de confirmação para evitar cliques acidentais
        resposta = QMessageBox.question(
            self, "Confirmar Exclusão", 
            f"Tem certeza que deseja remover o ativo {ticker} do seu catálogo?\nIsso apagará o histórico de preço médio dele.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if resposta == QMessageBox.StandardButton.Yes:
            self.db.executar_query("DELETE FROM carteira_atual WHERE ticker_id = ?", (ticker,))
            self.db.executar_query("DELETE FROM cache_mercado WHERE ticker_id = ?", (ticker,))
            self.db.executar_query("DELETE FROM ativos_catalogo WHERE ticker = ?", (ticker,))
            self.carregar_dados() # Recarrega a tabela e atualiza os gráficos!
            if self.fn_atualizar_resumo:
                self.fn_atualizar_resumo()

    def abrir_registro_compra(self):
        # 1. Verifica se tem alguma linha selecionada na tabela
        linha_selecionada = self.tabela_carteira.currentRow()
        if linha_selecionada < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um ativo na tabela primeiro!")
            return
            
        # 2. Pega o nome do Ticker da coluna 0
        ticker = self.tabela_carteira.item(linha_selecionada, 0).text()
        
        # 3. Abre o Pop-up
        dialogo = DialogoCompra(ticker, self)
        if dialogo.exec(): # Se o usuário clicou em "Confirmar Compra"
            qtd_comprada, preco_pago = dialogo.get_dados()
            
            # --- MATEMÁTICA DO PREÇO MÉDIO ---
            # Busca se já temos esse ativo na carteira
            busca = self.db.buscar_dados("SELECT quantidade_total, preco_medio FROM carteira_atual WHERE ticker_id = ?", (ticker,))
            
            if busca: # Já tínhamos o ativo, faz o cálculo do preço médio
                qtd_anterior = busca[0]['quantidade_total']
                pm_anterior = busca[0]['preco_medio']
                
                nova_qtd = qtd_anterior + qtd_comprada
                # Fórmula do PM: ((Qtd Velha * Preço Velho) + (Qtd Nova * Preço Novo)) / Nova Qtd Total
                novo_pm = ((qtd_anterior * pm_anterior) + (qtd_comprada * preco_pago)) / nova_qtd
            else: # Primeira compra
                nova_qtd = qtd_comprada
                novo_pm = preco_pago
                
            # Salva no banco (REPLACE atualiza se existir, INSERT cria se for novo)
            query = "INSERT OR REPLACE INTO carteira_atual (ticker_id, quantidade_total, preco_medio) VALUES (?, ?, ?)"
            self.db.executar_query(query, (ticker, nova_qtd, novo_pm))
            
            QMessageBox.information(self, "Sucesso", f"Compra de {ticker} registrada!\nNovo PM: R$ {novo_pm:.2f}")
            self.carregar_dados() # Atualiza a tabela imediatamente
            if self.fn_atualizar_resumo:
                self.fn_atualizar_resumo()

    def abrir_rebalanceamento(self):
        dialogo = DialogoRebalanceamento(self.db, self)
        dialogo.exec()
