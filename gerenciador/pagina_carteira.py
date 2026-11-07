from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QDialog, QFormLayout, QDoubleSpinBox, 
    QMessageBox, QFrame, QScrollArea, QAbstractItemView
)
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
        self.parent_page = parent
        self.compras_sugeridas = []
        self.setWindowTitle("Assessor Virtual - Rebalanceamento Inteligente de Carteira")
        self.resize(760, 680)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        lbl_info = QLabel(
            "Defina as porcentagens ideais para cada classe de ativo. O algoritmo calculará exatamente onde e quanto aportar "
            "para reequilibrar seu portfólio de forma matemática, sem vendas desnecessárias."
        )
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("color: #a6adc8; font-size: 13px; margin-bottom: 5px;")
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
        frame_metas = QFrame()
        frame_metas.setStyleSheet("background-color: #262939; border-radius: 8px; padding: 10px;")
        form_layout = QFormLayout(frame_metas)
        form_layout.setContentsMargins(10, 8, 10, 8)
        form_layout.setSpacing(8)
        
        for c in todas_classes:
            spin = QDoubleSpinBox()
            spin.setGroupSeparatorShown(True)
            spin.setRange(0, 100)
            spin.setSuffix("%")
            spin.setStyleSheet("background-color: #313244; color: #cdd6f4; font-weight: bold; padding: 4px;")
            
            res_alvo = self.db.buscar_dados(f"SELECT valor FROM configuracoes WHERE chave='alvo_classe_{c}'")
            if res_alvo:
                spin.setValue(float(res_alvo[0]['valor']))
            else:
                spin.setValue(0.0)
                
            self.inputs_alvo[c] = spin
            
            atual_val = self.patrimonio_por_classe.get(c, 0.0)
            atual_pct = (atual_val / self.patrimonio_total * 100) if self.patrimonio_total > 0 else 0
            
            lbl_classe = QLabel(f"{c} (Atual: {atual_pct:.1f}% | R$ {atual_val:.2f}):")
            lbl_classe.setStyleSheet("font-weight: bold; color: #cdd6f4;")
            form_layout.addRow(lbl_classe, spin)
            
        layout.addWidget(frame_metas)
        
        # --- SEÇÃO DO APORTE COM BOTÃO PUXAR SALDO LIVRE ---
        frame_aporte = QFrame()
        frame_aporte.setStyleSheet("background-color: #1e1e2e; border: 1px solid #313244; border-radius: 8px; padding: 10px;")
        layout_aporte_box = QVBoxLayout(frame_aporte)
        
        layout_aporte = QHBoxLayout()
        lbl_aporte = QLabel("Valor do Aporte Livre: R$")
        lbl_aporte.setStyleSheet("color: #a6e3a1; font-weight: bold; font-size: 14px;")
        layout_aporte.addWidget(lbl_aporte)
        
        self.input_aporte = QDoubleSpinBox()
        self.input_aporte.setGroupSeparatorShown(True)
        self.input_aporte.setRange(0, 10000000)
        self.input_aporte.setDecimals(2)
        self.input_aporte.setStyleSheet("background-color: #313244; color: #a6e3a1; font-weight: bold; font-size: 15px; padding: 6px;")
        layout_aporte.addWidget(self.input_aporte, 1)

        btn_puxar_saldo = QPushButton("⚡ Puxar Saldo Livre (Finanças)")
        btn_puxar_saldo.setStyleSheet("background-color: #fab387; color: #11111b; font-weight: bold; padding: 8px 14px; border-radius: 6px;")
        btn_puxar_saldo.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_puxar_saldo.setToolTip("Puxar o saldo positivo não gasto das Contas Pessoais deste mês.")
        btn_puxar_saldo.clicked.connect(self.puxar_saldo_livre_financas)
        layout_aporte.addWidget(btn_puxar_saldo)
        
        layout_aporte_box.addLayout(layout_aporte)

        btn_calcular = QPushButton("🎯 Calcular Rebalanceamento Inteligente")
        btn_calcular.setStyleSheet("background-color: #89b4fa; color: #11111b; font-weight: bold; padding: 10px; border-radius: 6px; font-size: 14px; margin-top: 5px;")
        btn_calcular.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_calcular.clicked.connect(self.calcular_rebalanceamento)
        layout_aporte_box.addWidget(btn_calcular)

        layout.addWidget(frame_aporte)

        # --- TABELA DE SUGESTÕES DE COMPRA ---
        self.lbl_titulo_sugestoes = QLabel("📋 Compras Recomendadas por Ativo:")
        self.lbl_titulo_sugestoes.setStyleSheet("color: #cdd6f4; font-weight: bold; font-size: 14px; margin-top: 5px;")
        self.lbl_titulo_sugestoes.hide()
        layout.addWidget(self.lbl_titulo_sugestoes)

        self.tabela_sugestoes = QTableWidget()
        self.tabela_sugestoes.setColumnCount(6)
        self.tabela_sugestoes.setHorizontalHeaderLabels(["Ativo", "Classe", "Preço Atual", "Cotas a Comprar", "Total a Investir", "Status"])
        self.tabela_sugestoes.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela_sugestoes.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela_sugestoes.setStyleSheet("background-color: #262939; color: #cdd6f4; font-size: 13px;")
        self.tabela_sugestoes.hide()
        layout.addWidget(self.tabela_sugestoes)
        
        self.lbl_resultado = QLabel("")
        self.lbl_resultado.setWordWrap(True)
        self.lbl_resultado.setStyleSheet("background-color: #313244; padding: 10px; border-radius: 6px; font-size: 13px; color: #cdd6f4;")
        self.lbl_resultado.hide()
        layout.addWidget(self.lbl_resultado)

        self.btn_executar_compras = QPushButton("🚀 Lançar Compras Sugeridas na Carteira")
        self.btn_executar_compras.setStyleSheet("background-color: #a6e3a1; color: #11111b; font-weight: bold; padding: 12px; border-radius: 6px; font-size: 14px;")
        self.btn_executar_compras.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_executar_compras.hide()
        self.btn_executar_compras.clicked.connect(self.executar_compras_sugeridas)
        layout.addWidget(self.btn_executar_compras)

    def puxar_saldo_livre_financas(self, mostrar_alerta=True):
        mes_atual = datetime.now().strftime("%Y-%m")
        query = """
            SELECT c.tipo, t.valor 
            FROM transacoes t
            LEFT JOIN categorias c ON t.categoria_id = c.id
            WHERE t.data LIKE ?
        """
        res = self.db.buscar_dados(query, (f"{mes_atual}-%",))
        total_rec = sum(float(r['valor']) for r in res if r['tipo'] == 'Receita')
        total_desp = sum(float(r['valor']) for r in res if r['tipo'] != 'Receita')
        saldo_livre = max(0.0, total_rec - total_desp)

        if saldo_livre > 0:
            self.input_aporte.setValue(saldo_livre)
            if mostrar_alerta:
                QMessageBox.information(
                    self,
                    "Saldo Livre Localizado!",
                    f"🎉 Saldo livre de {mes_atual} identificado nas Contas Pessoais: R$ {saldo_livre:.2f}.\n\n"
                    "Valor inserido automaticamente no campo de aporte!"
                )
        else:
            if mostrar_alerta:
                QMessageBox.information(
                    self,
                    "Saldo Livre Indisponível",
                    f"Nenhum saldo positivo restante foi encontrado nas transações do mês {mes_atual}. "
                    "Você pode digitar manualmente o valor do aporte desejado."
                )

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
        
        texto_resumo = "<b>🎯 Alocação Sugerida por Classe:</b><br>"
        aporte_restante = aporte
        self.compras_sugeridas = []
        
        for c, dif in recomendacoes:
            if aporte_restante <= 0:
                break
            valor_aportar_classe = min(dif, aporte_restante)
            texto_resumo += f"• <b>{c}</b>: Aportar <b>R$ {valor_aportar_classe:.2f}</b><br>"
            aporte_restante -= valor_aportar_classe

            # Busca os ativos cadastrados desta classe
            query_ativos = """
                SELECT a.ticker, a.classe, IFNULL(a.preco_teto, 999999) as preco_teto,
                       IFNULL(cart.quantidade_total, 0) as qtd_atual,
                       IFNULL(cart.preco_medio, 0) as pm_atual,
                       IFNULL(cm.preco_atual, 0) as preco_atual
                FROM ativos_catalogo a
                LEFT JOIN carteira_atual cart ON a.ticker = cart.ticker_id
                JOIN cache_mercado cm ON a.ticker = cm.ticker_id
                WHERE a.classe = ? AND cm.preco_atual > 0
                ORDER BY (IFNULL(cart.quantidade_total, 0) * cm.preco_atual) ASC
            """
            ativos_classe = self.db.buscar_dados(query_ativos, (c,))
            if not ativos_classe:
                continue

            saldo_classe_restante = valor_aportar_classe
            for ativo in ativos_classe:
                if saldo_classe_restante <= 0:
                    break
                p_atual = float(ativo['preco_atual'])
                if p_atual <= 0:
                    continue

                # Criptos aceitam fracionário; ações e FIIs usam cotas inteiras
                eh_cripto = (c.upper() in ["CRIPTO", "CRIPTOMOEDAS", "CRIPTOMOEDA", "MOEDA", "MOEDAS"])
                if eh_cripto:
                    cotas = round(saldo_classe_restante / p_atual, 4)
                else:
                    cotas = int(saldo_classe_restante / p_atual)

                if cotas > 0:
                    gasto_ativo = round(cotas * p_atual, 2)
                    saldo_classe_restante -= gasto_ativo
                    
                    status = "🎯 Abaixo do Teto" if p_atual <= float(ativo['preco_teto']) else "Preço de Mercado"
                    self.compras_sugeridas.append({
                        "ticker": ativo['ticker'],
                        "classe": ativo['classe'],
                        "preco_atual": p_atual,
                        "cotas": cotas,
                        "total_gasto": gasto_ativo,
                        "qtd_atual": float(ativo['qtd_atual']),
                        "pm_atual": float(ativo['pm_atual']),
                        "status": status
                    })

        if aporte_restante > 0:
            texto_resumo += f"<br><span style='color: #f9e2af;'>Restante livre: R$ {aporte_restante:.2f} após equilibrar as metas de classe.</span>"

        # Popula a tabela de compras sugeridas
        self.tabela_sugestoes.setRowCount(0)
        for i, s in enumerate(self.compras_sugeridas):
            self.tabela_sugestoes.insertRow(i)
            self.tabela_sugestoes.setItem(i, 0, QTableWidgetItem(s['ticker']))
            self.tabela_sugestoes.setItem(i, 1, QTableWidgetItem(s['classe']))
            self.tabela_sugestoes.setItem(i, 2, QTableWidgetItem(f"R$ {s['preco_atual']:.2f}"))
            
            fmt_cotas = f"{s['cotas']:.4f}" if isinstance(s['cotas'], float) else f"{s['cotas']}"
            self.tabela_sugestoes.setItem(i, 3, QTableWidgetItem(fmt_cotas))
            self.tabela_sugestoes.setItem(i, 4, QTableWidgetItem(f"R$ {s['total_gasto']:.2f}"))
            
            item_status = QTableWidgetItem(s['status'])
            if "🎯" in s['status']:
                item_status.setForeground(Qt.GlobalColor.green)
            self.tabela_sugestoes.setItem(i, 5, item_status)

        self.lbl_resultado.setText(texto_resumo)
        self.lbl_resultado.show()
        
        if self.compras_sugeridas:
            self.lbl_titulo_sugestoes.show()
            self.tabela_sugestoes.show()
            self.btn_executar_compras.show()
        else:
            self.lbl_titulo_sugestoes.hide()
            self.tabela_sugestoes.hide()
            self.btn_executar_compras.hide()

    def executar_compras_sugeridas(self):
        if not self.compras_sugeridas:
            return

        total_geral = sum(s['total_gasto'] for s in self.compras_sugeridas)
        msg = (
            f"Deseja registrar automaticamente essas {len(self.compras_sugeridas)} compra(s) sugeridas "
            f"somando R$ {total_geral:.2f} no seu portfólio?\n\n"
            "O Preço Médio e as quantidades serão recalculados com precisão."
        )
        resposta = QMessageBox.question(
            self,
            "Confirmar Rebalanceamento Automatizado",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resposta != QMessageBox.StandardButton.Yes:
            return

        hoje_str = datetime.now().strftime("%Y-%m-%d")
        cat_aporte = self.db.buscar_dados("SELECT id FROM categorias WHERE nome = 'Aportes em Investimentos'")
        cat_id = cat_aporte[0]['id'] if cat_aporte else None

        for s in self.compras_sugeridas:
            ticker = s['ticker']
            qtd_comprada = s['cotas']
            preco_pago = s['preco_atual']
            qtd_antiga = s['qtd_atual']
            pm_antigo = s['pm_atual']

            nova_qtd = qtd_antiga + qtd_comprada
            novo_pm = ((qtd_antiga * pm_antigo) + (qtd_comprada * preco_pago)) / nova_qtd

            # Atualiza carteira
            self.db.executar_query(
                "INSERT OR REPLACE INTO carteira_atual (ticker_id, quantidade_total, preco_medio) VALUES (?, ?, ?)",
                (ticker, nova_qtd, novo_pm)
            )

            # Opcional: registra saída nas finanças se categoria de Aportes existir
            if cat_id:
                self.db.executar_query(
                    "INSERT INTO transacoes (data, descricao, valor, categoria_id, origem, recorrente) VALUES (?, ?, ?, ?, 'Rebalanceador', 0)",
                    (hoje_str, f"Aporte Automatizado: {ticker} ({qtd_comprada} cotas)", s['total_gasto'], cat_id)
                )

        QMessageBox.information(
            self,
            "Rebalanceamento Concluído!",
            f"🎉 Sucesso!\n\nForam adquiridos os ativos sugeridos, seu Preço Médio foi atualizado e sua carteira agora está perfeitamente rebalanceada!"
        )

        if self.parent_page:
            self.parent_page.carregar_dados()
            if self.parent_page.fn_atualizar_resumo:
                self.parent_page.fn_atualizar_resumo()

        self.accept()
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
        
        self.btn_irpf = QPushButton("📑 Declaração IRPF")
        self.btn_irpf.setStyleSheet("background-color: #fab387; color: #11111b; font-weight: bold; padding: 10px; border-radius: 5px;")
        self.btn_irpf.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_irpf.clicked.connect(self.abrir_irpf)
        
        layout_acoes.addWidget(self.btn_registrar_compra)
        layout_acoes.addWidget(self.btn_rebalancear)
        layout_acoes.addWidget(self.btn_irpf)
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

    def abrir_irpf(self):
        from dialog_irpf import DialogRelatorioIRPF
        dialogo = DialogRelatorioIRPF(self.db, self)
        dialogo.exec()
