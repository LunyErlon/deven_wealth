from datetime import datetime
import pandas as pd
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QComboBox, QMessageBox, QTabWidget, 
    QWidget, QFileDialog, QApplication, QFrame
)
from PyQt6.QtCore import Qt
import qtawesome as qta


class DialogRelatorioIRPF(QDialog):
    """
    Relatório Auxiliar de Declaração de Imposto de Renda (IRPF):
    Gera o informe estruturado para preenchimento do programa da Receita Federal:
    - Bens e Direitos (Custo Histórico de Aquisição em 31/12) com Discriminação pronta para copiar.
    - Rendimentos Isentos e Não Tributáveis (Dividendos de Ações e Rendimentos de FIIs).
    - Rendimentos com Tributação Exclusiva / Definitiva (JCP - Juros sobre Capital Próprio).
    - Exportação em planilha Excel (.xlsx) com abas separadas.
    """
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Relatório Auxiliar de Imposto de Renda (IRPF)")
        self.resize(980, 680)
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QTabWidget::pane {
                border: 1px solid #313244;
                background-color: #1e1e2e;
                border-radius: 6px;
            }
            QTabBar::tab {
                background-color: #262939;
                color: #a6adc8;
                padding: 10px 20px;
                font-weight: bold;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #313244;
                color: #89b4fa;
            }
            QTableWidget {
                background-color: #181825;
                color: #cdd6f4;
                gridline-color: #313244;
                border: 1px solid #313244;
                border-radius: 6px;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #313244;
                color: #cdd6f4;
                font-weight: bold;
                padding: 6px;
                border: none;
            }
        """)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Cabeçalho com Seletor de Ano
        layout_topo = QHBoxLayout()
        
        lbl_titulo = QLabel("📑 Guia de Declaração de IRPF")
        lbl_titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #fab387;")
        layout_topo.addWidget(lbl_titulo)
        layout_topo.addStretch()

        lbl_ano = QLabel("Ano-Calendário (Base):")
        lbl_ano.setStyleSheet("color: #cdd6f4; font-weight: bold; font-size: 14px;")
        layout_topo.addWidget(lbl_ano)

        self.combo_ano = QComboBox()
        self.combo_ano.setStyleSheet("background-color: #313244; color: #cdd6f4; font-size: 14px; padding: 5px 12px; font-weight: bold;")
        
        ano_atual = datetime.now().year
        # Popula os últimos 5 anos
        for y in range(ano_atual, ano_atual - 5, -1):
            self.combo_ano.addItem(str(y), y)
        self.combo_ano.currentIndexChanged.connect(self.carregar_relatorio)
        layout_topo.addWidget(self.combo_ano)

        layout.addLayout(layout_topo)

        # Aviso Didático da Receita Federal
        frame_aviso = QFrame()
        frame_aviso.setStyleSheet("background-color: #262939; border-radius: 6px; padding: 8px; border-left: 4px solid #89b4fa;")
        layout_aviso = QVBoxLayout(frame_aviso)
        layout_aviso.setContentsMargins(10, 6, 10, 6)
        lbl_aviso = QLabel(
            "ℹ️ <b>Regra da Receita Federal:</b> Em <i>Bens e Direitos</i>, declare sempre o <b>Custo de Aquisição (Preço Médio Pago)</b> "
            "e <u>nunca</u> a cotação de mercado. O informe abaixo já calcula o custo total exato e formata o texto oficial de discriminação."
        )
        lbl_aviso.setWordWrap(True)
        lbl_aviso.setStyleSheet("color: #bac2de; font-size: 12px;")
        layout_aviso.addWidget(lbl_aviso)
        layout.addWidget(frame_aviso)

        # Abas do IRPF
        self.tabs = QTabWidget()

        # Aba 1: Bens e Direitos
        self.tab_bens = QWidget()
        layout_tab_bens = QVBoxLayout(self.tab_bens)
        self.tabela_bens = QTableWidget()
        self.tabela_bens.setColumnCount(6)
        self.tabela_bens.setHorizontalHeaderLabels([
            "Código IRPF", "Ativo", "Qtd em 31/12", "Custo Total (R$)", "Discriminação Oficial", "Copiar"
        ])
        self.tabela_bens.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tabela_bens.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tabela_bens.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tabela_bens.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tabela_bens.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.tabela_bens.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        layout_tab_bens.addWidget(self.tabela_bens)
        self.tabs.addTab(self.tab_bens, "🏛️ Bens e Direitos (Custo em 31/12)")

        # Aba 2: Rendimentos Isentos
        self.tab_isentos = QWidget()
        layout_tab_isentos = QVBoxLayout(self.tab_isentos)
        self.tabela_isentos = QTableWidget()
        self.tabela_isentos.setColumnCount(5)
        self.tabela_isentos.setHorizontalHeaderLabels([
            "Código IRPF", "Ativo", "Tipo", "Total Recebido no Ano (R$)", "Copiar"
        ])
        self.tabela_isentos.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tabela_isentos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tabela_isentos.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tabela_isentos.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tabela_isentos.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        layout_tab_isentos.addWidget(self.tabela_isentos)
        self.tabs.addTab(self.tab_isentos, "💰 Rendimentos Isentos (Dividendos / FIIs)")

        # Aba 3: Tributação Exclusiva (JCP)
        self.tab_exclusiva = QWidget()
        layout_tab_exclusiva = QVBoxLayout(self.tab_exclusiva)
        self.tabela_exclusiva = QTableWidget()
        self.tabela_exclusiva.setColumnCount(5)
        self.tabela_exclusiva.setHorizontalHeaderLabels([
            "Código IRPF", "Ativo", "Tipo", "Total Líquido Recebido (R$)", "Copiar"
        ])
        self.tabela_exclusiva.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tabela_exclusiva.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tabela_exclusiva.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tabela_exclusiva.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tabela_exclusiva.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        layout_tab_exclusiva.addWidget(self.tabela_exclusiva)
        self.tabs.addTab(self.tab_exclusiva, "🔒 Tributação Exclusiva (JCP)")

        layout.addWidget(self.tabs)

        # Rodapé com Botão Exportar Planilha e Fechar
        layout_rodape = QHBoxLayout()
        
        btn_exportar_excel = QPushButton("📑 Exportar Caderno IRPF Completo (.xlsx)")
        btn_exportar_excel.setStyleSheet("background-color: #89b4fa; color: #11111b; font-weight: bold; padding: 10px 18px; border-radius: 6px; font-size: 13px;")
        btn_exportar_excel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_exportar_excel.clicked.connect(self.exportar_excel_irpf)
        
        btn_fechar = QPushButton("Fechar")
        btn_fechar.setStyleSheet("background-color: #45475a; color: #cdd6f4; font-weight: bold; padding: 10px 20px; border-radius: 6px;")
        btn_fechar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_fechar.clicked.connect(self.accept)

        layout_rodape.addWidget(btn_exportar_excel)
        layout_rodape.addStretch()
        layout_rodape.addWidget(btn_fechar)
        layout.addLayout(layout_rodape)

        self.carregar_relatorio()

    def classificar_codigo_bens(self, classe, ticker):
        classe_upper = str(classe).upper()
        ticker_upper = str(ticker).upper()
        
        if "AÇ" in classe_upper or "ACAO" in classe_upper or "AÇÕES" in classe_upper:
            return "Grupo 03 - Código 01 (Ações)"
        elif "FII" in classe_upper or "IMOBILI" in classe_upper:
            return "Grupo 07 - Código 03 (Fundos Imobiliários)"
        elif "CRIPTO" in classe_upper or "MOEDA" in classe_upper:
            if "BTC" in ticker_upper:
                return "Grupo 08 - Código 01 (Bitcoin)"
            elif "ETH" in ticker_upper:
                return "Grupo 08 - Código 02 (Altcoins)"
            elif "USD" in ticker_upper:
                return "Grupo 08 - Código 03 (Stablecoins)"
            return "Grupo 08 - Código 99 (Outros Criptoativos)"
        elif "RENDA FIXA" in classe_upper or "TESOURO" in classe_upper:
            return "Grupo 04 - Código 02 (Títulos Públicos / Privados)"
        return "Grupo 99 - Outros Bens"

    def carregar_relatorio(self):
        ano_selecionado = self.combo_ano.currentText()

        # 1. Carrega Bens e Direitos
        query_bens = """
            SELECT 
                c.ticker_id, 
                a.setor, 
                a.classe, 
                c.quantidade_total, 
                c.preco_medio,
                (c.quantidade_total * c.preco_medio) as custo_aquisicao
            FROM carteira_atual c
            JOIN ativos_catalogo a ON c.ticker_id = a.ticker
            WHERE c.quantidade_total > 0
            ORDER BY a.classe, c.ticker_id
        """
        bens = self.db.buscar_dados(query_bens)
        self.tabela_bens.setRowCount(0)

        for i, b in enumerate(bens):
            self.tabela_bens.insertRow(i)
            cod_irpf = self.classificar_codigo_bens(b['classe'], b['ticker_id'])
            qtd = float(b['quantidade_total'])
            pm = float(b['preco_medio'])
            custo_total = float(b['custo_aquisicao'])
            setor_info = f" ({b['setor']})" if b.get('setor') else ""

            # Formata discriminação recomendada para o programa do IRPF
            if "CRIPTO" in str(b['classe']).upper():
                discriminacao = (
                    f"{qtd:.6f} unidades do criptoativo {b['ticker_id']}{setor_info}, "
                    f"custodiadas em carteira própria/exchange, ao custo total de aquisição de R$ {custo_total:,.2f}."
                )
            elif "FII" in str(b['classe']).upper():
                discriminacao = (
                    f"{int(qtd)} cotas do Fundo de Investimento Imobiliário {b['ticker_id']}{setor_info}, "
                    f"custodiadas em corretora de valores, ao custo total de aquisição de R$ {custo_total:,.2f} (Preço Médio de R$ {pm:.2f})."
                )
            else:
                discriminacao = (
                    f"{int(qtd)} ações ordinárias/preferenciais de {b['ticker_id']}{setor_info}, "
                    f"custodiadas em corretora de valores, ao custo total de aquisição de R$ {custo_total:,.2f} (Preço Médio de R$ {pm:.2f})."
                )

            self.tabela_bens.setItem(i, 0, QTableWidgetItem(cod_irpf))
            self.tabela_bens.setItem(i, 1, QTableWidgetItem(f"{b['ticker_id']}{setor_info}"))
            fmt_qtd = f"{qtd:.4f}" if "CRIPTO" in str(b['classe']).upper() else f"{int(qtd)}"
            self.tabela_bens.setItem(i, 2, QTableWidgetItem(fmt_qtd))
            self.tabela_bens.setItem(i, 3, QTableWidgetItem(f"R$ {custo_total:,.2f}"))
            self.tabela_bens.setItem(i, 4, QTableWidgetItem(discriminacao))

            btn_copiar = QPushButton()
            btn_copiar.setIcon(qta.icon('fa5s.copy', color='#89b4fa'))
            btn_copiar.setStyleSheet("background-color: transparent; border: none; padding: 4px;")
            btn_copiar.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_copiar.setToolTip("Copiar Discriminação para colar na Declaração da Receita Federal")
            btn_copiar.clicked.connect(lambda _, txt=discriminacao: self.copiar_texto(txt))
            self.tabela_bens.setCellWidget(i, 5, btn_copiar)

        # 2. Carrega Rendimentos Isentos e Tributação Exclusiva
        query_rendimentos = """
            SELECT 
                r.ticker_id, 
                a.setor, 
                a.classe, 
                r.tipo_provento, 
                SUM(r.valor_liquido_total) as total_ano
            FROM rendimentos r
            JOIN ativos_catalogo a ON r.ticker_id = a.ticker
            WHERE r.data_pagamento LIKE ?
            GROUP BY r.ticker_id, r.tipo_provento
            ORDER BY r.ticker_id
        """
        rendimentos = self.db.buscar_dados(query_rendimentos, (f"{ano_selecionado}-%",))
        
        self.tabela_isentos.setRowCount(0)
        self.tabela_exclusiva.setRowCount(0)
        
        idx_isento = 0
        idx_exclusivo = 0

        for r in rendimentos:
            tipo = str(r['tipo_provento']).upper()
            total = float(r['total_ano'])
            ativo = f"{r['ticker_id']}" + (f" ({r['setor']})" if r.get('setor') else "")

            if "JCP" in tipo or "JUROS" in tipo:
                # Código 10 da Receita: Juros sobre Capital Próprio
                self.tabela_exclusiva.insertRow(idx_exclusivo)
                cod = "Código 10 (Juros sobre Capital Próprio)"
                desc = f"JCP recebido de {ativo} no ano de {ano_selecionado}: R$ {total:.2f}"
                
                self.tabela_exclusiva.setItem(idx_exclusivo, 0, QTableWidgetItem(cod))
                self.tabela_exclusiva.setItem(idx_exclusivo, 1, QTableWidgetItem(ativo))
                self.tabela_exclusiva.setItem(idx_exclusivo, 2, QTableWidgetItem(r['tipo_provento']))
                self.tabela_exclusiva.setItem(idx_exclusivo, 3, QTableWidgetItem(f"R$ {total:,.2f}"))

                btn_cop = QPushButton()
                btn_cop.setIcon(qta.icon('fa5s.copy', color='#fab387'))
                btn_cop.setStyleSheet("background-color: transparent; border: none;")
                btn_cop.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_cop.setToolTip("Copiar Resumo")
                btn_cop.clicked.connect(lambda _, txt=desc: self.copiar_texto(txt))
                self.tabela_exclusiva.setCellWidget(idx_exclusivo, 4, btn_cop)
                idx_exclusivo += 1
            else:
                # Isentos: Dividendos (09) ou Rendimentos de FII (26 - Outros)
                self.tabela_isentos.insertRow(idx_isento)
                if "FII" in str(r['classe']).upper() or "RENDIMENTO" in tipo:
                    cod = "Código 26 - Outros (Rendimentos de FII)"
                else:
                    cod = "Código 09 - Lucros e Dividendos"

                desc = f"Rendimentos isentos recebidos de {ativo} no ano de {ano_selecionado}: R$ {total:.2f}"
                self.tabela_isentos.setItem(idx_isento, 0, QTableWidgetItem(cod))
                self.tabela_isentos.setItem(idx_isento, 1, QTableWidgetItem(ativo))
                self.tabela_isentos.setItem(idx_isento, 2, QTableWidgetItem(r['tipo_provento']))
                self.tabela_isentos.setItem(idx_isento, 3, QTableWidgetItem(f"R$ {total:,.2f}"))

                btn_cop = QPushButton()
                btn_cop.setIcon(qta.icon('fa5s.copy', color='#a6e3a1'))
                btn_cop.setStyleSheet("background-color: transparent; border: none;")
                btn_cop.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_cop.setToolTip("Copiar Resumo")
                btn_cop.clicked.connect(lambda _, txt=desc: self.copiar_texto(txt))
                self.tabela_isentos.setCellWidget(idx_isento, 4, btn_cop)
                idx_isento += 1

    def copiar_texto(self, texto):
        clipboard = QApplication.clipboard()
        clipboard.setText(texto)
        QMessageBox.information(
            self,
            "Copiado!",
            f"📋 Texto copiado para a área de transferência com sucesso!\n\nPronto para colar diretamente no programa do IRPF:\n\n\"{texto}\""
        )

    def exportar_excel_irpf(self):
        ano_selecionado = self.combo_ano.currentText()
        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Caderno de IRPF",
            f"Caderno_IRPF_AnoBase_{ano_selecionado}.xlsx",
            "Planilha Excel (*.xlsx)"
        )
        if not caminho:
            return

        try:
            # 1. DataFrame Bens
            linhas_bens = []
            for r in range(self.tabela_bens.rowCount()):
                linhas_bens.append({
                    "Código IRPF": self.tabela_bens.item(r, 0).text(),
                    "Ativo": self.tabela_bens.item(r, 1).text(),
                    "Qtd em 31/12": self.tabela_bens.item(r, 2).text(),
                    "Custo Total de Aquisição": self.tabela_bens.item(r, 3).text(),
                    "Discriminação Completa": self.tabela_bens.item(r, 4).text()
                })
            df_bens = pd.DataFrame(linhas_bens)

            # 2. DataFrame Isentos
            linhas_isentos = []
            for r in range(self.tabela_isentos.rowCount()):
                linhas_isentos.append({
                    "Código IRPF": self.tabela_isentos.item(r, 0).text(),
                    "Ativo": self.tabela_isentos.item(r, 1).text(),
                    "Tipo de Provento": self.tabela_isentos.item(r, 2).text(),
                    "Total Recebido no Ano": self.tabela_isentos.item(r, 3).text()
                })
            df_isentos = pd.DataFrame(linhas_isentos)

            # 3. DataFrame Exclusiva
            linhas_exclusiva = []
            for r in range(self.tabela_exclusiva.rowCount()):
                linhas_exclusiva.append({
                    "Código IRPF": self.tabela_exclusiva.item(r, 0).text(),
                    "Ativo": self.tabela_exclusiva.item(r, 1).text(),
                    "Tipo de Provento": self.tabela_exclusiva.item(r, 2).text(),
                    "Total Líquido Recebido": self.tabela_exclusiva.item(r, 3).text()
                })
            df_exclusiva = pd.DataFrame(linhas_exclusiva)

            with pd.ExcelWriter(caminho) as writer:
                df_bens.to_excel(writer, sheet_name="Bens e Direitos (Custo)", index=False)
                df_isentos.to_excel(writer, sheet_name="Rendimentos Isentos", index=False)
                df_exclusiva.to_excel(writer, sheet_name="Tributação Exclusiva (JCP)", index=False)

            QMessageBox.information(
                self,
                "Caderno IRPF Exportado!",
                f"🎉 Sucesso!\n\nSeu Caderno de IRPF para o Ano-Base {ano_selecionado} foi exportado com sucesso em:\n{caminho}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Exportar", f"Falha ao gerar planilha de IRPF:\n{e}")
