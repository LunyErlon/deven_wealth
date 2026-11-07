from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, 
    QDateEdit, QDoubleSpinBox, QMessageBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QDialog, QCheckBox, QApplication
)
from PyQt6.QtCore import Qt, QDate, QThread, pyqtSignal
import qtawesome as qta

# For matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt


class WorkerRadarDividendos(QThread):
    """
    OBS 1: Gatilho em Segundo Plano (QThread).
    Consulta os proventos recentes na nuvem sem travar a interface gráfica.
    """
    dividendos_detectados = pyqtSignal(list)
    finalizado_sem_dividendos = pyqtSignal()
    erro = pyqtSignal(str)

    def __init__(self, api, holdings, rendimentos_existentes, parent=None):
        super().__init__(parent)
        self.api = api
        self.holdings = holdings  # [{'ticker_id': 'MXRF11.SA', 'quantidade_total': 100}, ...]
        self.rendimentos_existentes = rendimentos_existentes  # [{'ticker_id': ..., 'data_pagamento': ...}, ...]

    def run(self):
        try:
            if not self.holdings or not self.api:
                self.finalizado_sem_dividendos.emit()
                return

            tickers = [h['ticker_id'] for h in self.holdings if h.get('quantidade_total', 0) > 0]
            if not tickers:
                self.finalizado_sem_dividendos.emit()
                return

            mapa_qtd = {}
            for h in self.holdings:
                t_raw = h['ticker_id']
                t_limpo = t_raw.replace('.SA', '').upper()
                mapa_qtd[t_raw] = float(h['quantidade_total'])
                mapa_qtd[t_limpo] = float(h['quantidade_total'])

            ja_registrados = set()
            for r in self.rendimentos_existentes:
                t_limpo = r['ticker_id'].replace('.SA', '').upper()
                dt = r['data_pagamento']
                ja_registrados.add((t_limpo, dt))

            eventos = self.api.buscar_dividendos_recentes(tickers, dias=45)

            pendentes = []
            for ev in eventos:
                chave = (ev['ticker_curto'].upper(), ev['data_pagamento'])
                if chave not in ja_registrados:
                    qtd = mapa_qtd.get(ev['ticker_id'], mapa_qtd.get(ev['ticker_curto'], 1.0))
                    ev['qtd_cotas_sugerida'] = qtd
                    ev['valor_total_estimado'] = round(qtd * ev['valor_por_cota'], 2)
                    pendentes.append(ev)

            if pendentes:
                self.dividendos_detectados.emit(pendentes)
            else:
                self.finalizado_sem_dividendos.emit()
        except Exception as e:
            self.erro.emit(str(e))


class DialogRadarDividendos(QDialog):
    """
    Fase 3 & 4: Pop-up de Validação do Radar de Dividendos (Atrito Positivo com o Desafio da Data-Com).
    Permite validar a quantidade base de cotas que realmente tinha direito na Data-Com
    antes de injetar no banco de dados e alimentar o efeito Bola de Neve.
    """
    def __init__(self, dividendos_detectados, db, fn_atualizar_rendimentos=None, fn_atualizar_resumo=None, parent=None):
        super().__init__(parent)
        self.dividendos_detectados = dividendos_detectados
        self.db = db
        self.fn_atualizar_rendimentos = fn_atualizar_rendimentos
        self.fn_atualizar_resumo = fn_atualizar_resumo
        self.setWindowTitle("Radar de Dividendos B3 - Proventos Detectados")
        self.resize(980, 560)
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QLabel {
                color: #cdd6f4;
            }
            QTableWidget {
                background-color: #181825;
                color: #cdd6f4;
                gridline-color: #313244;
                border: 1px solid #45475a;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #313244;
                color: #cdd6f4;
                font-weight: bold;
                padding: 6px;
                border: 1px solid #45475a;
            }
            QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 4px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus {
                border: 1px solid #89b4fa;
            }
        """)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(22, 22, 22, 22)

        ativos_unicos = sorted(list(set(d['ticker_curto'] for d in self.dividendos_detectados)))
        lista_ativos_str = ", ".join(ativos_unicos)

        # 1. Cabeçalho de Boas-Vindas
        lbl_titulo = QLabel("🎉 Radar da B3: Novos Pagamentos de Proventos!")
        lbl_titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #a6e3a1;")

        lbl_saudacao = QLabel(
            f"Olá, Luny! Boas notícias: o Radar da B3 identificou <b>{len(self.dividendos_detectados)} pagamento(s) recente(s)</b> "
            f"para os ativos da sua carteira (<b>{lista_ativos_str}</b>). Deseja conferir e registrar agora?"
        )
        lbl_saudacao.setStyleSheet("color: #cdd6f4; font-size: 14px;")
        lbl_saudacao.setWordWrap(True)

        lbl_dica = QLabel(
            "⚡ <b>Atrito Positivo (O Desafio da 'Data-Com'):</b> O sistema sugeriu a quantidade de cotas que você possui atualmente na carteira. "
            "Contudo, apenas as cotas compradas <i>até a Data-Com</i> (data de corte) têm direito a este pagamento. "
            "<br>Se você comprou novas cotas após a data de corte, basta <b>ajustar a coluna 'Qtd. Cotas Base'</b> para o número exato pago pela sua corretora."
        )
        lbl_dica.setStyleSheet("background-color: #313244; color: #89b4fa; padding: 10px; border-radius: 6px; font-size: 12px;")
        lbl_dica.setWordWrap(True)

        layout.addWidget(lbl_titulo)
        layout.addWidget(lbl_saudacao)
        layout.addWidget(lbl_dica)

        # 2. Tabela de Proventos Detectados
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(8)
        self.tabela.setHorizontalHeaderLabels([
            "Registrar?", "Ativo", "Data Pagamento", "Tipo", "Valor / Cota", "Qtd. Cotas Base", "Total Líquido", "Descartar"
        ])

        self.tabela.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(0, 75)

        self.tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(1, 110)

        self.tabela.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(2, 125)

        self.tabela.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(3, 120)

        self.tabela.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(4, 115)

        self.tabela.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        self.tabela.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(6, 130)

        self.tabela.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(7, 65)

        layout.addWidget(self.tabela)

        # 3. Rodapé
        layout_rodape = QHBoxLayout()

        self.lbl_stats = QLabel("Carregando...")
        self.lbl_stats.setStyleSheet("color: #cdd6f4; font-weight: bold; font-size: 13px;")

        btn_cancelar = QPushButton("Lembrar Mais Tarde")
        btn_cancelar.setStyleSheet("background-color: #45475a; color: #cdd6f4; font-weight: bold; padding: 8px 16px; border-radius: 6px;")
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.clicked.connect(self.reject)

        btn_confirmar = QPushButton("💾 Confirmar Recebimentos")
        btn_confirmar.setStyleSheet("background-color: #a6e3a1; color: #11111b; font-weight: bold; padding: 8px 20px; border-radius: 6px; font-size: 14px;")
        btn_confirmar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_confirmar.clicked.connect(self.confirmar_recebimentos)

        layout_rodape.addWidget(self.lbl_stats)
        layout_rodape.addStretch()
        layout_rodape.addWidget(btn_cancelar)
        layout_rodape.addWidget(btn_confirmar)

        layout.addLayout(layout_rodape)

        # 4. Preenchimento Inicial
        self.preencher_tabela()
        self.atualizar_estatisticas()

    def preencher_tabela(self):
        self.tabela.setRowCount(0)
        for i, item in enumerate(self.dividendos_detectados):
            self.tabela.insertRow(i)

            # Col 0: Checkbox Registrar
            widget_chk = QWidget()
            layout_chk = QHBoxLayout(widget_chk)
            layout_chk.setContentsMargins(0, 0, 0, 0)
            layout_chk.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk = QCheckBox()
            chk.setChecked(True)
            chk.stateChanged.connect(lambda _, r=i: self.atualizar_estatisticas())
            layout_chk.addWidget(chk)
            self.tabela.setCellWidget(i, 0, widget_chk)

            # Metadados
            table_item = QTableWidgetItem()
            table_item.setData(Qt.ItemDataRole.UserRole, item)
            self.tabela.setItem(i, 0, table_item)

            # Col 1: Ativo (Ticker)
            lbl_ativo = QLabel(f"<b>{item['ticker_curto']}</b>")
            lbl_ativo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_ativo.setStyleSheet("color: #fab387; font-size: 13px;")
            self.tabela.setCellWidget(i, 1, lbl_ativo)

            # Col 2: Data Pagamento (QDateEdit)
            input_data = QDateEdit()
            input_data.setCalendarPopup(True)
            dt = QDate.fromString(item['data_pagamento'], "yyyy-MM-dd")
            if dt.isValid():
                input_data.setDate(dt)
            else:
                input_data.setDate(QDate.currentDate())
            self.tabela.setCellWidget(i, 2, input_data)

            # Col 3: Tipo de Provento
            combo_tipo = QComboBox()
            combo_tipo.addItems(["Rendimento", "Dividendo", "JCP"])
            combo_tipo.setCurrentText(item.get('tipo_provento', 'Rendimento'))
            self.tabela.setCellWidget(i, 3, combo_tipo)

            # Col 4: Valor por Cota
            val_cota = float(item['valor_por_cota'])
            lbl_val_cota = QLabel(f"R$ {val_cota:.4f}")
            lbl_val_cota.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_val_cota.setStyleSheet("color: #a6e3a1; font-weight: bold;")
            self.tabela.setCellWidget(i, 4, lbl_val_cota)

            # Col 5: Qtd. Cotas Base (Editável)
            spin_cotas = QDoubleSpinBox()
            spin_cotas.setRange(0.01, 10000000.0)
            spin_cotas.setGroupSeparatorShown(True)
            spin_cotas.setValue(float(item.get('qtd_cotas_sugerida', 1.0)))
            self.tabela.setCellWidget(i, 5, spin_cotas)

            # Col 6: Total Líquido (QLabel calculado dinamicamente)
            total_calc = spin_cotas.value() * val_cota
            lbl_total = QLabel(f"R$ {total_calc:.2f}")
            lbl_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_total.setStyleSheet("color: #a6e3a1; font-weight: bold; font-size: 13px;")
            self.tabela.setCellWidget(i, 6, lbl_total)

            # Conecta recálculo ao alterar cotas
            spin_cotas.valueChanged.connect(lambda val, r=i, vc=val_cota: self.recalcular_linha(r, vc))

            # Col 7: Botão Descartar
            widget_del = QWidget()
            layout_del = QHBoxLayout(widget_del)
            layout_del.setContentsMargins(0, 0, 0, 0)
            layout_del.setAlignment(Qt.AlignmentFlag.AlignCenter)
            btn_del = QPushButton()
            btn_del.setIcon(qta.icon('fa5s.trash-alt', color='#f38ba8'))
            btn_del.setStyleSheet("background: transparent; border: none;")
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.setToolTip("Descartar este provento")
            btn_del.clicked.connect(lambda checked, b=btn_del: self.remover_linha(b))
            layout_del.addWidget(btn_del)
            self.tabela.setCellWidget(i, 7, widget_del)

    def recalcular_linha(self, row, valor_cota):
        spin_cotas = self.tabela.cellWidget(row, 5)
        lbl_total = self.tabela.cellWidget(row, 6)
        if spin_cotas and lbl_total:
            total = spin_cotas.value() * valor_cota
            lbl_total.setText(f"R$ {total:.2f}")
        self.atualizar_estatisticas()

    def remover_linha(self, btn):
        for row in range(self.tabela.rowCount()):
            widget = self.tabela.cellWidget(row, 7)
            if widget and widget.isAncestorOf(btn):
                self.tabela.removeRow(row)
                self.atualizar_estatisticas()
                break

    def atualizar_estatisticas(self):
        total_linhas = self.tabela.rowCount()
        total_marcados = 0
        soma_proventos = 0.0

        for row in range(total_linhas):
            widget_chk = self.tabela.cellWidget(row, 0)
            chk = widget_chk.findChild(QCheckBox) if widget_chk else None
            if chk and chk.isChecked():
                total_marcados += 1
                spin_cotas = self.tabela.cellWidget(row, 5)
                table_item = self.tabela.item(row, 0)
                meta = table_item.data(Qt.ItemDataRole.UserRole) if table_item else {}
                val_cota = float(meta.get('valor_por_cota', 0.0))
                cotas = spin_cotas.value() if spin_cotas else 0.0
                soma_proventos += (cotas * val_cota)

        self.lbl_stats.setText(
            f"Selecionados: <b>{total_marcados}/{total_linhas}</b> | "
            f"Total Proventos: <span style='color: #a6e3a1; font-weight: bold;'>R$ {soma_proventos:.2f}</span>"
        )

    def confirmar_recebimentos(self):
        rendimentos_para_salvar = []
        for row in range(self.tabela.rowCount()):
            widget_chk = self.tabela.cellWidget(row, 0)
            chk = widget_chk.findChild(QCheckBox) if widget_chk else None
            if not chk or not chk.isChecked():
                continue

            table_item = self.tabela.item(row, 0)
            meta = table_item.data(Qt.ItemDataRole.UserRole) if table_item else {}
            
            input_data = self.tabela.cellWidget(row, 2)
            combo_tipo = self.tabela.cellWidget(row, 3)
            spin_cotas = self.tabela.cellWidget(row, 5)

            ticker_id = meta.get('ticker_id')
            data_str = input_data.date().toString("yyyy-MM-dd")
            tipo_str = combo_tipo.currentText()
            cotas = spin_cotas.value()
            valor_cota = float(meta.get('valor_por_cota', 0.0))
            valor_liquido = round(cotas * valor_cota, 2)

            rendimentos_para_salvar.append((ticker_id, data_str, tipo_str, cotas, valor_liquido))

        if not rendimentos_para_salvar:
            QMessageBox.information(self, "Aviso", "Nenhum provento foi selecionado para registro.")
            self.reject()
            return

        try:
            self.db.executar_query_lote("""
                INSERT INTO rendimentos (ticker_id, data_pagamento, tipo_provento, qtd_cotas_base, valor_liquido_total)
                VALUES (?, ?, ?, ?, ?)
            """, rendimentos_para_salvar)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Salvar", f"Falha ao registrar proventos no banco de dados:\n{e}")
            return

        total_reais = sum(r[4] for r in rendimentos_para_salvar)
        QMessageBox.information(
            self,
            "Bola de Neve em Ação!",
            f"🎉 Sucesso!\n\n{len(rendimentos_para_salvar)} provento(s) somando R$ {total_reais:.2f} "
            f"foram consolidados no seu histórico de renda passiva.\n\nSua Bola de Neve está crescendo!"
        )

        if callable(self.fn_atualizar_rendimentos):
            self.fn_atualizar_rendimentos()
        if callable(self.fn_atualizar_resumo):
            self.fn_atualizar_resumo()

        self.accept()


class PaginaRendimentos(QWidget):
    def __init__(self, db, api=None, fn_atualizar_resumo=None):
        super().__init__()
        self.db = db
        self.api = api
        self.fn_atualizar_resumo = fn_atualizar_resumo
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Cabeçalho com Título e Botão do Radar
        layout_cabecalho = QHBoxLayout()
        lbl_titulo = QLabel("Rendimentos / Renda Passiva")
        lbl_titulo.setObjectName("tituloPagina")

        self.btn_irpf = QPushButton("📑 Informes IRPF")
        self.btn_irpf.setStyleSheet(
            "background-color: #fab387; color: #11111b; font-weight: bold; "
            "padding: 7px 16px; border-radius: 6px; font-size: 13px;"
        )
        self.btn_irpf.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_irpf.setToolTip("Abrir Relatório Auxiliar de Imposto de Renda (Proventos e Rendimentos)")
        self.btn_irpf.clicked.connect(self.abrir_irpf)

        self.btn_radar = QPushButton("🔍 Escanear Radar de Dividendos")
        self.btn_radar.setStyleSheet(
            "background-color: #89b4fa; color: #11111b; font-weight: bold; "
            "padding: 7px 16px; border-radius: 6px; font-size: 13px;"
        )
        self.btn_radar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_radar.setToolTip("Consultar a B3 e identificar pagamentos de dividendos recentes dos seus ativos")
        self.btn_radar.clicked.connect(self.escanear_radar_manual)

        layout_cabecalho.addWidget(lbl_titulo)
        layout_cabecalho.addStretch()
        layout_cabecalho.addWidget(self.btn_irpf)
        layout_cabecalho.addWidget(self.btn_radar)
        layout.addLayout(layout_cabecalho)

        # Formulário de Inserção Manual
        form_layout = QHBoxLayout()

        # Ativo
        layout_ativo = QVBoxLayout()
        layout_ativo.addWidget(QLabel("Ativo"))
        self.combo_ativo = QComboBox()
        self.combo_ativo.setStyleSheet("padding: 5px; font-size: 14px; background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 4px;")
        layout_ativo.addWidget(self.combo_ativo)
        form_layout.addLayout(layout_ativo)

        # Data do Pagamento
        layout_data = QVBoxLayout()
        layout_data.addWidget(QLabel("Data do Pagamento"))
        self.date_pagamento = QDateEdit()
        self.date_pagamento.setCalendarPopup(True)
        self.date_pagamento.setDate(QDate.currentDate())
        self.date_pagamento.setStyleSheet("padding: 5px; font-size: 14px; background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 4px;")
        layout_data.addWidget(self.date_pagamento)
        form_layout.addLayout(layout_data)

        # Tipo de Provento
        layout_tipo = QVBoxLayout()
        layout_tipo.addWidget(QLabel("Tipo de Provento"))
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Rendimento", "Dividendo", "JCP"])
        self.combo_tipo.setStyleSheet("padding: 5px; font-size: 14px; background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 4px;")
        layout_tipo.addWidget(self.combo_tipo)
        form_layout.addLayout(layout_tipo)

        # Quantidade de Cotas Base
        layout_cotas = QVBoxLayout()
        layout_cotas.addWidget(QLabel("Qtd. de Cotas Base"))
        self.spin_cotas = QDoubleSpinBox()
        self.spin_cotas.setGroupSeparatorShown(True)
        self.spin_cotas.setRange(0.01, 1000000)
        self.spin_cotas.setValue(1)
        self.spin_cotas.setStyleSheet("font-size: 14px;")
        layout_cotas.addWidget(self.spin_cotas)
        form_layout.addLayout(layout_cotas)

        # Valor Líquido Total
        layout_valor = QVBoxLayout()
        layout_valor.addWidget(QLabel("Valor Líquido Total (R$)"))
        self.spin_valor = QDoubleSpinBox()
        self.spin_valor.setGroupSeparatorShown(True)
        self.spin_valor.setRange(0.01, 10000000)
        self.spin_valor.setPrefix("R$ ")
        self.spin_valor.setStyleSheet("font-size: 14px;")
        layout_valor.addWidget(self.spin_valor)
        form_layout.addLayout(layout_valor)

        layout.addLayout(form_layout)

        # Botão Salvar Manual
        self.btn_salvar = QPushButton("Registrar Rendimento")
        self.btn_salvar.setObjectName("btnSalvar")
        self.btn_salvar.clicked.connect(self.registrar_rendimento)
        layout.addWidget(self.btn_salvar, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addSpacing(20)

        # Gráfico Bola de Neve
        self.fig, self.ax = plt.subplots(figsize=(8, 3))
        self.fig.patch.set_facecolor('#1e1e2e')
        self.ax.set_facecolor('#1e1e2e')
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)
        
        layout.addSpacing(20)

        # Tabela Histórico
        self.tabela_historico = QTableWidget()
        self.tabela_historico.setColumnCount(6)
        self.tabela_historico.setHorizontalHeaderLabels(["Ativo", "Data", "Tipo", "Cotas Base", "Valor Recebido", "Excluir"])
        self.tabela_historico.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tabela_historico)

    def escanear_radar_manual(self):
        """Fase 2: Acionamento sob demanda do Radar de Dividendos."""
        holdings = self.db.buscar_dados("SELECT ticker_id, quantidade_total FROM carteira_atual WHERE quantidade_total > 0")
        if not holdings:
            QMessageBox.information(
                self, 
                "Radar de Dividendos B3", 
                "Você ainda não possui ativos registrados na carteira para escanear proventos."
            )
            return

        if not self.api:
            QMessageBox.warning(self, "Aviso", "MarketAPI não configurada.")
            return

        # Feedback visual durante o rastreamento
        self.btn_radar.setEnabled(False)
        self.btn_radar.setText("⏳ Escaneando B3...")
        QApplication.processEvents()

        try:
            rendimentos_existentes = self.db.buscar_dados("SELECT ticker_id, data_pagamento FROM rendimentos")
            tickers = [h['ticker_id'] for h in holdings]
            
            mapa_qtd = {}
            for h in holdings:
                t_raw = h['ticker_id']
                t_limpo = t_raw.replace('.SA', '').upper()
                mapa_qtd[t_raw] = float(h['quantidade_total'])
                mapa_qtd[t_limpo] = float(h['quantidade_total'])

            ja_registrados = {(r['ticker_id'].replace('.SA', '').upper(), r['data_pagamento']) for r in rendimentos_existentes}
            
            eventos = self.api.buscar_dividendos_recentes(tickers, dias=45)
            pendentes = []
            for ev in eventos:
                chave = (ev['ticker_curto'].upper(), ev['data_pagamento'])
                if chave not in ja_registrados:
                    qtd = mapa_qtd.get(ev['ticker_id'], mapa_qtd.get(ev['ticker_curto'], 1.0))
                    ev['qtd_cotas_sugerida'] = qtd
                    ev['valor_total_estimado'] = round(qtd * ev['valor_por_cota'], 2)
                    pendentes.append(ev)

            if pendentes:
                dialog = DialogRadarDividendos(
                    pendentes, 
                    self.db, 
                    fn_atualizar_rendimentos=self.carregar_dados,
                    fn_atualizar_resumo=self.fn_atualizar_resumo,
                    parent=self
                )
                dialog.exec()
            else:
                QMessageBox.information(
                    self, 
                    "Radar de Dividendos B3", 
                    "🎉 Tudo em dia!\n\nNenhum pagamento novo de dividendos foi encontrado nos últimos 45 dias para os ativos da sua carteira."
                )
        except Exception as e:
            QMessageBox.critical(self, "Erro no Radar", f"Falha ao escanear dividendos:\n{e}")
        finally:
            self.btn_radar.setEnabled(True)
            self.btn_radar.setText("🔍 Escanear Radar de Dividendos")

    def carregar_dados(self):
        self.combo_ativo.clear()
        ativos = self.db.buscar_dados("SELECT ticker_id FROM carteira_atual")
        for ativo in ativos:
            self.combo_ativo.addItem(ativo['ticker_id'])
            
        self.atualizar_historico_e_grafico()

    def registrar_rendimento(self):
        ticker_id = self.combo_ativo.currentText()
        if not ticker_id:
            QMessageBox.warning(self, "Aviso", "Não há ativos na carteira para registrar rendimento.")
            return
            
        data = self.date_pagamento.date().toString("yyyy-MM-dd")
        tipo = self.combo_tipo.currentText()
        cotas = self.spin_cotas.value()
        valor = self.spin_valor.value()
        
        if valor <= 0:
            QMessageBox.warning(self, "Aviso", "O valor líquido total deve ser maior que zero.")
            return
        
        query_insert = """
            INSERT INTO rendimentos (ticker_id, data_pagamento, tipo_provento, qtd_cotas_base, valor_liquido_total)
            VALUES (?, ?, ?, ?, ?)
        """
        id_inserido = self.db.executar_query(query_insert, (ticker_id, data, tipo, cotas, valor))
        
        if id_inserido:
            self.mostrar_magica_didatica(id_inserido)
            self.atualizar_historico_e_grafico()
            if callable(self.fn_atualizar_resumo):
                self.fn_atualizar_resumo()
            self.spin_valor.setValue(0.01)
            
    def mostrar_magica_didatica(self, rendimento_id):
        query = """
            SELECT 
                r.ticker_id,
                r.valor_liquido_total,
                r.qtd_cotas_base,
                (r.valor_liquido_total / r.qtd_cotas_base) as dividendo_por_cota,
                c.preco_medio,
                ((r.valor_liquido_total / r.qtd_cotas_base) / c.preco_medio) * 100 as yield_on_cost_porcentagem,
                cm.preco_atual
            FROM rendimentos r
            JOIN carteira_atual c ON r.ticker_id = c.ticker_id
            LEFT JOIN cache_mercado cm ON r.ticker_id = cm.ticker_id
            WHERE r.id = ?
        """
        resultados = self.db.buscar_dados(query, (rendimento_id,))
        if resultados:
            res = resultados[0]
            ticker = res['ticker_id']
            div_por_cota = res['dividendo_por_cota']
            yoc = res['yield_on_cost_porcentagem']
            valor_total = res['valor_liquido_total']
            
            preco_cota = res['preco_atual'] if res['preco_atual'] else res['preco_medio']
            
            if div_por_cota > 0 and preco_cota > 0:
                numero_magico = preco_cota / div_por_cota
            else:
                numero_magico = 0
                
            mensagem = f"🎉 Parabéns! Você registrou o rendimento de {ticker}.\n\n"
            mensagem += f"📊 Lição 1 - Valor por Cota:\n"
            mensagem += f"A cada cota que você tinha, a empresa te pagou R$ {div_por_cota:.2f} de 'aluguel' este mês.\n\n"
            
            mensagem += f"📈 Lição 2 - Yield on Cost (A métrica dos bilionários):\n"
            mensagem += f"O seu rendimento real sobre o dinheiro que VOCÊ tirou do bolso foi de {yoc:.2f}%!\n"
            mensagem += f"Isso ensina por que manter bons ativos por muito tempo enriquece.\n\n"
            
            mensagem += f"✨ Lição 3 - A Barra do Número Mágico:\n"
            if numero_magico > 0:
                mensagem += f"O Número Mágico de {ticker} é ~{numero_magico:.0f} cotas (para que o dividendo pague uma nova cota sozinho).\n"
                cotas_compradas = valor_total / preco_cota
                perc_nova_cota = cotas_compradas * 100
                if perc_nova_cota >= 100:
                    mensagem += f"Com os R$ {valor_total:.2f} recebidos, você já consegue comprar {cotas_compradas:.1f} novas cotas! A bola de neve está girando."
                else:
                    mensagem += f"Seus R$ {valor_total:.2f} já pagam {perc_nova_cota:.1f}% de uma nova cota! Continue reinvestindo."
                    
            QMessageBox.information(self, "Mágica dos Juros Compostos", mensagem)

    def atualizar_historico_e_grafico(self):
        rendimentos = self.db.buscar_dados("SELECT * FROM rendimentos ORDER BY data_pagamento DESC")
        self.tabela_historico.setRowCount(len(rendimentos))
        for i, rend in enumerate(rendimentos):
            self.tabela_historico.setItem(i, 0, QTableWidgetItem(rend['ticker_id']))
            self.tabela_historico.setItem(i, 1, QTableWidgetItem(rend['data_pagamento']))
            self.tabela_historico.setItem(i, 2, QTableWidgetItem(rend['tipo_provento']))
            self.tabela_historico.setItem(i, 3, QTableWidgetItem(str(rend['qtd_cotas_base'])))
            self.tabela_historico.setItem(i, 4, QTableWidgetItem(f"R$ {rend['valor_liquido_total']:.2f}"))
            
            widget_excluir = QWidget()
            layout_excluir = QHBoxLayout(widget_excluir)
            layout_excluir.setContentsMargins(0, 0, 0, 0)
            layout_excluir.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            btn_excluir = QPushButton()
            btn_excluir.setIcon(qta.icon('fa5s.trash-alt', color='#f38ba8'))
            btn_excluir.setStyleSheet("background-color: transparent; border: none;")
            btn_excluir.setCursor(Qt.CursorShape.PointingHandCursor)
            
            btn_excluir.clicked.connect(lambda checked, id_rend=rend['id']: self.excluir_rendimento(id_rend))
            
            layout_excluir.addWidget(btn_excluir)
            self.tabela_historico.setCellWidget(i, 5, widget_excluir)
            
        dados_grafico = self.db.buscar_dados("""
            SELECT strftime('%Y-%m', data_pagamento) as mes, SUM(valor_liquido_total) as total 
            FROM rendimentos 
            GROUP BY mes 
            ORDER BY mes ASC
        """)
        
        self.ax.clear()
        self.ax.set_facecolor('#1e1e2e')
        if dados_grafico:
            meses = [d['mes'] for d in dados_grafico]
            totais = [d['total'] for d in dados_grafico]
            
            barras = self.ax.bar(meses, totais, color='#a6e3a1')
            self.ax.set_title("Efeito Bola de Neve (Dividendos)", color='#cdd6f4', pad=15)
            self.ax.tick_params(colors='#cdd6f4')
            self.ax.spines['bottom'].set_color('#313244')
            self.ax.spines['top'].set_visible(False)
            self.ax.spines['right'].set_visible(False)
            self.ax.spines['left'].set_color('#313244')
            
            for barra in barras:
                altura = barra.get_height()
                self.ax.annotate(f'R$ {altura:.2f}',
                                 xy=(barra.get_x() + barra.get_width() / 2, altura),
                                 xytext=(0, 3),  
                                 textcoords="offset points",
                                 ha='center', va='bottom', color='#cdd6f4')
        else:
            self.ax.text(0.5, 0.5, 'Nenhum rendimento registrado', 
                         color='#cdd6f4', ha='center', va='center', transform=self.ax.transAxes)

        self.fig.tight_layout()
        self.canvas.draw()

    def excluir_rendimento(self, id_rendimento):
        resposta = QMessageBox.question(
            self, "Confirmar Exclusão", 
            "Deseja realmente apagar este registro de rendimento?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if resposta == QMessageBox.StandardButton.Yes:
            self.db.executar_query("DELETE FROM rendimentos WHERE id = ?", (id_rendimento,))
            self.atualizar_historico_e_grafico()
            if callable(self.fn_atualizar_resumo):
                self.fn_atualizar_resumo()

    def abrir_irpf(self):
        from dialog_irpf import DialogRelatorioIRPF
        dialog = DialogRelatorioIRPF(self.db, self)
        dialog.exec()
