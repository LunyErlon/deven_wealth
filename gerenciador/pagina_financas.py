import os
import pandas as pd
from ofxparse import OfxParser
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as mpatches
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QLineEdit, QDoubleSpinBox, QComboBox, 
    QDateEdit, QMessageBox, QDialog, QFormLayout, QFileDialog, QCheckBox, 
    QFrame
)
from PyQt6.QtCore import Qt, QDate
import qtawesome as qta


class ExtratorFaturas:
    """
    Extrator Híbrido (CSV e OFX) com suporte a extratos e faturas de bancos brasileiros:
    Nubank (cartão e conta), Itaú, Bradesco, Santander, Banco do Brasil, Inter, etc.
    """
    @staticmethod
    def detectar_parcelamento(descricao):
        """
        Caçador de padrões de parcelamento em faturas brasileiras via Regex:
        Identifica padrões como '1/10', '02/12', 'PARC 03/05', 'Parcela 1 de 10'.
        Filtra inteligentemente falsos positivos de datas (ex: TED 15/08) garantindo que
        a parcela atual <= total de parcelas e o total esteja entre 2 e 60.
        """
        import re
        padrao = r'(?:parc(?:ela)?\.?\s*)?(\d{1,2})\s*(?:/|\s+de\s+)\s*(\d{1,2})'
        match = re.search(padrao, str(descricao), re.IGNORECASE)
        if match:
            p_atual = int(match.group(1))
            p_total = int(match.group(2))
            if 1 <= p_atual <= p_total and 2 <= p_total <= 60:
                return {
                    "parcelado": True,
                    "parcela_atual": p_atual,
                    "total_parcelas": p_total,
                    "tag": f"{p_atual}/{p_total}"
                }
        return {
            "parcelado": False,
            "parcela_atual": None,
            "total_parcelas": None,
            "tag": None
        }

    @staticmethod
    def extrair(caminho_arquivo):
        ext = os.path.splitext(caminho_arquivo)[1].lower()
        if ext == '.ofx':
            return ExtratorFaturas.extrair_ofx(caminho_arquivo)
        elif ext == '.csv':
            return ExtratorFaturas.extrair_csv(caminho_arquivo)
        else:
            raise ValueError(f"Extensão de arquivo não suportada: '{ext}'. Use faturas .csv ou .ofx.")

    @staticmethod
    def extrair_ofx(caminho_arquivo):
        lista_transacoes = []
        with open(caminho_arquivo, 'rb') as arquivo:
            ofx = OfxParser.parse(arquivo)
            
        contas = []
        if hasattr(ofx, 'accounts') and ofx.accounts:
            contas.extend(ofx.accounts)
        elif hasattr(ofx, 'account') and ofx.account:
            contas.append(ofx.account)
            
        for conta in contas:
            stmt = getattr(conta, 'statement', None)
            if not stmt or not hasattr(stmt, 'transactions'):
                continue
                
            for transacao in stmt.transactions:
                # 1. Data formatada ISO YYYY-MM-DD
                data_str = transacao.date.strftime("%Y-%m-%d") if transacao.date else ""
                
                # 2. Descrição: nos bancos brasileiros (ex: Nubank, Itaú),
                # o campo 'payee' frequentemente é vazio ou genérico ("Compra no débito"),
                # enquanto o nome real do estabelecimento está em 'memo'.
                payee = (transacao.payee or "").strip()
                memo = (transacao.memo or "").strip()
                
                if payee and memo:
                    if memo.lower() in payee.lower():
                        desc = payee
                    elif payee.lower() in memo.lower():
                        desc = memo
                    else:
                        desc = f"{payee} - {memo}"
                elif memo:
                    desc = memo
                elif payee:
                    desc = payee
                else:
                    desc = "Transação sem descrição"
                    
                # Correção preventiva de mojibake (acentos quebrados em OFX ISO-8859-1 vs UTF-8)
                try:
                    if any(c in desc for c in ['Ã©', 'Ã£', 'Ã§', 'Ã³', 'Ã¡', 'Ãª']):
                        desc = desc.encode('latin-1').decode('utf-8')
                except Exception:
                    pass
                    
                # 3. Tratamento de valor e tipo (Despesa / Receita)
                amount = float(transacao.amount)
                if amount < 0:
                    tipo = "Despesa"
                    valor = abs(amount)
                else:
                    tipo = "Receita"
                    valor = amount
                    
                # 4. Caçador de Parcelamento
                info_parc = ExtratorFaturas.detectar_parcelamento(desc)

                lista_transacoes.append({
                    "data": data_str,
                    "descricao": desc,
                    "valor": valor,
                    "tipo": tipo,
                    "parcelado": info_parc["parcelado"],
                    "parcela_atual": info_parc["parcela_atual"],
                    "total_parcelas": info_parc["total_parcelas"],
                    "tag_parcela": info_parc["tag"]
                })
                
        return lista_transacoes

    @staticmethod
    def extrair_csv(caminho_arquivo):
        # 1. Leitura com detecção de múltiplos encodings e separadores
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        df = None
        for enc in encodings:
            try:
                df = pd.read_csv(caminho_arquivo, sep=None, engine='python', encoding=enc)
                if df is not None and len(df.columns) >= 2:
                    break
            except Exception:
                continue
                
        if df is None or df.empty:
            raise ValueError("Não foi possível ler o arquivo CSV ou o arquivo está vazio.")
            
        # 2. Mapeamento heurístico de colunas
        colunas_map = {col: str(col).lower().strip().replace('_', '').replace(' ', '') for col in df.columns}
        
        col_data = None
        col_valor = None
        col_desc = None
        
        for col, clean in colunas_map.items():
            if any(k in clean for k in ['data', 'date', 'dt', 'dia']):
                col_data = col
                break
                
        for col, clean in colunas_map.items():
            if any(k in clean for k in ['valor', 'amount', 'val', 'preco', 'preço']):
                col_valor = col
                break
                
        for col, clean in colunas_map.items():
            if col != col_data and col != col_valor:
                if any(k in clean for k in ['desc', 'titul', 'title', 'histor', 'estabelec', 'lanc', 'lanç', 'memo', 'nome', 'identificador']):
                    col_desc = col
                    break
                    
        if not col_desc:
            sobras = [c for c in df.columns if c not in (col_data, col_valor)]
            if sobras:
                col_desc = sobras[0]
                
        if not col_data or not col_valor:
            raise ValueError(f"Não foi possível identificar colunas obrigatórias de Data e Valor. Colunas encontradas: {list(df.columns)}")
            
        # Identificar se valores brutos contêm valores negativos (extrato tradicional) ou se são fatura de cartão (tudo positivo)
        valores_brutos = []
        for val in df[col_valor].dropna():
            try:
                v_str = str(val).strip().replace("R$", "").replace(" ", "")
                if ',' in v_str and '.' in v_str:
                    v_str = v_str.replace('.', '').replace(',', '.')
                elif ',' in v_str:
                    v_str = v_str.replace(',', '.')
                valores_brutos.append(float(v_str))
            except Exception:
                pass
                
        tem_negativos = any(v < 0 for v in valores_brutos)
        
        lista_transacoes = []
        for _, row in df.iterrows():
            raw_data = row[col_data]
            raw_desc = row[col_desc] if col_desc else "Transação Importada"
            raw_val = row[col_valor]
            
            if pd.isna(raw_data) or pd.isna(raw_val):
                continue
                
            raw_data_str = str(raw_data).strip()
            try:
                if len(raw_data_str) >= 10 and raw_data_str[4] == '-' and raw_data_str[7] == '-':
                    dt = pd.to_datetime(raw_data_str, format='%Y-%m-%d')
                else:
                    dt = pd.to_datetime(raw_data_str, dayfirst=True)
                data_str = dt.strftime("%Y-%m-%d")
            except Exception:
                data_str = raw_data_str[:10]
                
            desc = str(raw_desc).strip()
            if desc.lower() in ['nan', 'none', '']:
                desc = "Transação sem descrição"
                
            val_str = str(raw_val).strip().replace("R$", "").replace(" ", "")
            try:
                if ',' in val_str and '.' in val_str:
                    val_str = val_str.replace('.', '').replace(',', '.')
                elif ',' in val_str:
                    val_str = val_str.replace(',', '.')
                valor_float = float(val_str)
            except Exception:
                continue
                
            if tem_negativos:
                if valor_float < 0:
                    tipo = "Despesa"
                    valor = abs(valor_float)
                else:
                    tipo = "Receita"
                    valor = valor_float
            else:
                desc_lower = desc.lower()
                if "pagamento" in desc_lower or "estorno" in desc_lower or "receb" in desc_lower:
                    tipo = "Receita"
                    valor = valor_float
                else:
                    tipo = "Despesa"
                    valor = valor_float
                    
            # 4. Caçador de Parcelamento
            info_parc = ExtratorFaturas.detectar_parcelamento(desc)

            lista_transacoes.append({
                "data": data_str,
                "descricao": desc,
                "valor": valor,
                "tipo": tipo,
                "parcelado": info_parc["parcelado"],
                "parcela_atual": info_parc["parcela_atual"],
                "total_parcelas": info_parc["total_parcelas"],
                "tag_parcela": info_parc["tag"]
            })
            
        return lista_transacoes


class DialogPurgatorioTransacoes(QDialog):
    """
    O Purgatório de Transações (Fila de Triage e Processamento):
    Os dados extraídos da fatura caem aqui aguardando a conscientização e classificação do usuário.
    Garante o 'Atrito Positivo' da regra 50/30/20 antes de consolidar no Livro-Caixa oficial.
    """
    def __init__(self, lista_transacoes, db, parent=None):
        super().__init__(parent)
        self.lista_transacoes = lista_transacoes
        self.db = db
        self.setWindowTitle("O Purgatório de Transações - Fila de Processamento")
        self.resize(1050, 680)
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
                padding: 5px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus {
                border: 1px solid #89b4fa;
            }
        """)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. Cabeçalho Didático
        lbl_titulo = QLabel("🔥 O Purgatório de Transações")
        lbl_titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #fab387;")
        
        lbl_subtitulo = QLabel(
            "⚡ Atrito Positivo: Os dados abaixo foram importados da fatura bancária. "
            "Examine cada gasto, defina sua categoria e regra 50/30/20 antes de aprovar para o seu Livro-Caixa."
        )
        lbl_subtitulo.setStyleSheet("color: #a6adc8; font-size: 13px;")
        lbl_subtitulo.setWordWrap(True)
        
        layout.addWidget(lbl_titulo)
        layout.addWidget(lbl_subtitulo)

        # 2. Barra de Controle e Ações Rápidas
        layout_controles = QHBoxLayout()
        layout_controles.setSpacing(10)

        self.chk_selecionar_todos = QCheckBox("Marcar Todos")
        self.chk_selecionar_todos.setChecked(True)
        self.chk_selecionar_todos.setStyleSheet("font-weight: bold; color: #cdd6f4;")
        self.chk_selecionar_todos.toggled.connect(self.marcar_desmarcar_todos)

        self.input_filtro = QLineEdit()
        self.input_filtro.setPlaceholderText("🔍 Filtrar por descrição...")
        self.input_filtro.setStyleSheet("min-width: 200px;")
        self.input_filtro.textChanged.connect(self.filtrar_tabela)

        lbl_massa = QLabel("Aplicar categoria aos marcados:")
        lbl_massa.setStyleSheet("color: #cdd6f4; font-weight: bold;")

        self.combo_massa = QComboBox()
        self.combo_massa.setStyleSheet("min-width: 200px;")

        btn_aplicar_massa = QPushButton("⚡ Aplicar em Massa")
        btn_aplicar_massa.setStyleSheet("background-color: #89b4fa; color: #11111b; font-weight: bold; padding: 6px 12px; border-radius: 5px;")
        btn_aplicar_massa.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_aplicar_massa.clicked.connect(self.aplicar_categoria_massa)

        btn_nova_cat = QPushButton("➕ Nova Categoria")
        btn_nova_cat.setStyleSheet("background-color: #f9e2af; color: #11111b; font-weight: bold; padding: 6px 12px; border-radius: 5px;")
        btn_nova_cat.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_nova_cat.clicked.connect(self.abrir_nova_categoria)

        layout_controles.addWidget(self.chk_selecionar_todos)
        layout_controles.addWidget(self.input_filtro)
        layout_controles.addSpacing(15)
        layout_controles.addWidget(lbl_massa)
        layout_controles.addWidget(self.combo_massa)
        layout_controles.addWidget(btn_aplicar_massa)
        layout_controles.addWidget(btn_nova_cat)
        layout_controles.addStretch()

        layout.addLayout(layout_controles)

        # 3. Tabela do Purgatório
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(7)
        self.tabela.setHorizontalHeaderLabels([
            "Importar?", "Data", "Descrição (Editável)", "Valor", "Tipo", "Categoria (A Triage)", "Ação"
        ])
        
        self.tabela.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(0, 80)
        
        self.tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(1, 120)
        
        self.tabela.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        self.tabela.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(3, 130)
        
        self.tabela.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(4, 110)
        
        self.tabela.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(5, 290)
        
        self.tabela.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(6, 60)
        
        layout.addWidget(self.tabela)

        # 4. Rodapé com Estatísticas e Botões de Finalização
        layout_rodape = QHBoxLayout()

        self.lbl_stats = QLabel("Carregando...")
        self.lbl_stats.setStyleSheet("color: #cdd6f4; font-weight: bold; font-size: 13px;")

        btn_cancelar = QPushButton("Descartar Fila")
        btn_cancelar.setStyleSheet("background-color: #45475a; color: #cdd6f4; font-weight: bold; padding: 8px 16px; border-radius: 6px;")
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.clicked.connect(self.reject)

        self.btn_salvar_lote = QPushButton("💾 Salvar Lote no Livro-Caixa")
        self.btn_salvar_lote.setStyleSheet("background-color: #45475a; color: #6c7086; font-weight: bold; padding: 8px 20px; border-radius: 6px; font-size: 14px;")
        self.btn_salvar_lote.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_salvar_lote.clicked.connect(self.salvar_lote)
        self.btn_salvar_lote.setEnabled(False)

        layout_rodape.addWidget(self.lbl_stats)
        layout_rodape.addStretch()
        layout_rodape.addWidget(btn_cancelar)
        layout_rodape.addWidget(self.btn_salvar_lote)

        layout.addLayout(layout_rodape)

        # 5. Preenchimento Inicial
        self.preencher_tabela()
        self.recarregar_combos_categorias()
        self.atualizar_estatisticas()

    def preencher_tabela(self):
        self.tabela.setRowCount(0)
        for i, item in enumerate(self.lista_transacoes):
            self.tabela.insertRow(i)

            # Col 0: Checkbox de seleção
            widget_chk = QWidget()
            layout_chk = QHBoxLayout(widget_chk)
            layout_chk.setContentsMargins(0, 0, 0, 0)
            layout_chk.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk = QCheckBox()
            chk.setChecked(True)
            chk.stateChanged.connect(lambda _, r=i: self.atualizar_estatisticas())
            layout_chk.addWidget(chk)
            self.tabela.setCellWidget(i, 0, widget_chk)

            # Col 1: Data (QDateEdit)
            input_data = QDateEdit()
            input_data.setCalendarPopup(True)
            dt = QDate.fromString(item['data'], "yyyy-MM-dd")
            if dt.isValid():
                input_data.setDate(dt)
            else:
                input_data.setDate(QDate.currentDate())
            self.tabela.setCellWidget(i, 1, input_data)

            # Col 2: Descrição (QLineEdit editável com Badge de Parcelado se houver)
            widget_desc = QWidget()
            layout_desc = QHBoxLayout(widget_desc)
            layout_desc.setContentsMargins(0, 0, 0, 0)
            layout_desc.setSpacing(6)

            input_desc = QLineEdit(item['descricao'])
            input_desc.setStyleSheet("background-color: #313244; color: #cdd6f4;")
            layout_desc.addWidget(input_desc)

            if item.get('parcelado'):
                p_atual = item.get('parcela_atual')
                p_total = item.get('total_parcelas')
                restantes = p_total - p_atual if p_total and p_atual else 0
                lbl_badge = QLabel(f"💳 {item.get('tag_parcela')}")
                lbl_badge.setStyleSheet(
                    "background-color: #313244; color: #89dceb; font-weight: bold; "
                    "font-size: 11px; padding: 2px 6px; border-radius: 4px; border: 1px solid #89dceb;"
                )
                lbl_badge.setToolTip(
                    f"Compra Parcelada: Parcela {p_atual} de {p_total}.\n"
                    f"Ainda restam {restantes} parcela(s) de R$ {float(item['valor']):.2f} nos próximos meses."
                )
                layout_desc.addWidget(lbl_badge)

            self.tabela.setCellWidget(i, 2, widget_desc)

            # Col 3: Valor (QDoubleSpinBox)
            spin_val = QDoubleSpinBox()
            spin_val.setRange(0.01, 10000000.0)
            spin_val.setGroupSeparatorShown(True)
            spin_val.setPrefix("R$ ")
            spin_val.setValue(float(item['valor']))
            spin_val.valueChanged.connect(lambda _, r=i: self.atualizar_estatisticas())
            self.tabela.setCellWidget(i, 3, spin_val)

            # Col 4: Tipo (Despesa / Receita)
            combo_tipo = QComboBox()
            combo_tipo.addItems(["Despesa", "Receita"])
            combo_tipo.setCurrentText(item.get('tipo', 'Despesa'))
            combo_tipo.currentTextChanged.connect(lambda _, r=i: self.atualizar_estatisticas())
            self.tabela.setCellWidget(i, 4, combo_tipo)

            # Col 5: Categoria (Dropdown da Triage - Inicia vazio aguardando o usuário)
            combo_cat = QComboBox()
            combo_cat.setStyleSheet("background-color: #313244; color: #cdd6f4; font-weight: bold;")
            combo_cat.currentIndexChanged.connect(lambda _, r=i: self.atualizar_estatisticas())
            self.tabela.setCellWidget(i, 5, combo_cat)

            # Col 6: Botão Descartar Linha
            widget_del = QWidget()
            layout_del = QHBoxLayout(widget_del)
            layout_del.setContentsMargins(0, 0, 0, 0)
            layout_del.setAlignment(Qt.AlignmentFlag.AlignCenter)
            btn_del = QPushButton()
            btn_del.setIcon(qta.icon('fa5s.trash-alt', color='#f38ba8'))
            btn_del.setStyleSheet("background: transparent; border: none;")
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.setToolTip("Remover esta transação da fila")
            btn_del.clicked.connect(lambda checked, b=btn_del: self.remover_linha(b))
            layout_del.addWidget(btn_del)
            self.tabela.setCellWidget(i, 6, widget_del)

    def recarregar_combos_categorias(self):
        categorias = self.db.buscar_dados("SELECT id, nome, tipo, grupo_regra FROM categorias ORDER BY grupo_regra, nome")
        
        # Combo em massa
        self.combo_massa.blockSignals(True)
        self.combo_massa.clear()
        self.combo_massa.addItem("Selecione para aplicar...", None)
        for cat in categorias:
            grupo = cat.get('grupo_regra', 'Sem Grupo')
            tipo = cat.get('tipo', 'Despesa')
            self.combo_massa.addItem(f"[{grupo}] {cat['nome']} ({tipo})", cat['id'])
        self.combo_massa.blockSignals(False)

        # Atualiza todos os combos da tabela preservando o que já foi selecionado
        for row in range(self.tabela.rowCount()):
            combo = self.tabela.cellWidget(row, 5)
            if not combo:
                continue
            cat_atual_id = combo.currentData()

            combo.blockSignals(True)
            combo.clear()
            combo.addItem("⚠️ [Pendente] Selecione...", None)
            for cat in categorias:
                grupo = cat.get('grupo_regra', 'Sem Grupo')
                tipo = cat.get('tipo', 'Despesa')
                combo.addItem(f"[{grupo}] {cat['nome']} ({tipo})", cat['id'])

            if cat_atual_id is not None:
                idx = combo.findData(cat_atual_id)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            combo.blockSignals(False)

        self.atualizar_estatisticas()

    def remover_linha(self, btn):
        for row in range(self.tabela.rowCount()):
            widget = self.tabela.cellWidget(row, 6)
            if widget and widget.isAncestorOf(btn):
                self.tabela.removeRow(row)
                self.atualizar_estatisticas()
                break

    def marcar_desmarcar_todos(self, checked):
        for row in range(self.tabela.rowCount()):
            if not self.tabela.isRowHidden(row):
                widget_chk = self.tabela.cellWidget(row, 0)
                chk = widget_chk.findChild(QCheckBox) if widget_chk else None
                if chk:
                    chk.setChecked(checked)
        self.atualizar_estatisticas()

    def filtrar_tabela(self, texto):
        termo = texto.strip().lower()
        for row in range(self.tabela.rowCount()):
            widget_desc = self.tabela.cellWidget(row, 2)
            input_desc = widget_desc.findChild(QLineEdit) if widget_desc else None
            desc = input_desc.text().lower() if input_desc else ""
            self.tabela.setRowHidden(row, termo not in desc)

    def aplicar_categoria_massa(self):
        cat_id = self.combo_massa.currentData()
        if not cat_id:
            QMessageBox.warning(self, "Aviso", "Selecione uma categoria válida no campo ao lado para aplicar em massa.")
            return

        alterados = 0
        for row in range(self.tabela.rowCount()):
            if self.tabela.isRowHidden(row):
                continue
            widget_chk = self.tabela.cellWidget(row, 0)
            chk = widget_chk.findChild(QCheckBox) if widget_chk else None
            if chk and chk.isChecked():
                combo_cat = self.tabela.cellWidget(row, 5)
                if combo_cat:
                    idx = combo_cat.findData(cat_id)
                    if idx >= 0:
                        combo_cat.setCurrentIndex(idx)
                        alterados += 1

        self.atualizar_estatisticas()
        QMessageBox.information(self, "Aplicado", f"Categoria aplicada a {alterados} transação(ões) marcada(s)!")

    def abrir_nova_categoria(self):
        dialog = DialogGerenciarCategorias(self.db, self)
        dialog.exec()
        self.recarregar_combos_categorias()

    def atualizar_estatisticas(self):
        total_linhas = self.tabela.rowCount()
        total_marcados = 0
        total_classificados = 0
        soma_despesas = 0.0
        soma_receitas = 0.0

        for row in range(total_linhas):
            widget_chk = self.tabela.cellWidget(row, 0)
            chk = widget_chk.findChild(QCheckBox) if widget_chk else None
            if chk and chk.isChecked():
                total_marcados += 1
                combo_cat = self.tabela.cellWidget(row, 5)
                if combo_cat and combo_cat.currentData() is not None:
                    total_classificados += 1

                spin_val = self.tabela.cellWidget(row, 3)
                combo_tipo = self.tabela.cellWidget(row, 4)
                val = spin_val.value() if spin_val else 0.0
                tipo = combo_tipo.currentText() if combo_tipo else "Despesa"

                if tipo == "Receita":
                    soma_receitas += val
                else:
                    soma_despesas += val

        cor_pendentes = "#f38ba8" if (total_marcados - total_classificados) > 0 else "#a6e3a1"
        self.lbl_stats.setText(
            f"Selecionados: {total_marcados}/{total_linhas} | "
            f"Classificados: <span style='color: {cor_pendentes}; font-weight: bold;'>{total_classificados}/{total_marcados}</span> | "
            f"Despesas: <span style='color: #f38ba8;'>R$ {soma_despesas:.2f}</span> | "
            f"Receitas: <span style='color: #a6e3a1;'>R$ {soma_receitas:.2f}</span>"
        )

        # Regra do Atrito Positivo e Tarefa 2.2: O botão 'Salvar Lote' só fica habilitado
        # quando todas as linhas marcadas estiverem devidamente classificadas.
        todas_classificadas = (total_marcados > 0) and (total_classificados == total_marcados)
        self.btn_salvar_lote.setEnabled(todas_classificadas)
        if todas_classificadas:
            self.btn_salvar_lote.setStyleSheet("background-color: #a6e3a1; color: #11111b; font-weight: bold; padding: 8px 20px; border-radius: 6px; font-size: 14px;")
            self.btn_salvar_lote.setToolTip("Salvar todas as transações classificadas no Livro-Caixa.")
        else:
            self.btn_salvar_lote.setStyleSheet("background-color: #45475a; color: #6c7086; font-weight: bold; padding: 8px 20px; border-radius: 6px; font-size: 14px;")
            pendentes = total_marcados - total_classificados
            if total_marcados == 0:
                self.btn_salvar_lote.setToolTip("Selecione ao menos uma transação para habilitar o salvamento.")
            else:
                self.btn_salvar_lote.setToolTip(f"Atrito Positivo: Faltam {pendentes} transações sem categoria para habilitar o salvamento em lote.")

    def salvar_lote(self):
        transacoes_para_salvar = []
        transacoes_sem_categoria = []

        for row in range(self.tabela.rowCount()):
            widget_chk = self.tabela.cellWidget(row, 0)
            chk = widget_chk.findChild(QCheckBox) if widget_chk else None
            if not chk or not chk.isChecked():
                continue

            input_data = self.tabela.cellWidget(row, 1)
            widget_desc = self.tabela.cellWidget(row, 2)
            input_desc = widget_desc.findChild(QLineEdit) if widget_desc else None
            spin_val = self.tabela.cellWidget(row, 3)
            combo_cat = self.tabela.cellWidget(row, 5)

            data_str = input_data.date().toString("yyyy-MM-dd")
            desc_str = input_desc.text().strip() if input_desc else "Transação sem descrição"
            val = spin_val.value()
            cat_id = combo_cat.currentData()

            if cat_id is None:
                transacoes_sem_categoria.append((data_str, desc_str, val))
            else:
                transacoes_para_salvar.append((data_str, desc_str, val, cat_id))

        if not transacoes_para_salvar and not transacoes_sem_categoria:
            QMessageBox.warning(self, "Aviso", "Nenhuma transação foi marcada para importação.")
            return

        if transacoes_sem_categoria:
            total_pendentes = len(transacoes_sem_categoria)
            msg = (
                f"Existem {total_pendentes} transações marcadas que ainda NÃO foram classificadas!\n\n"
                "O 'Purgatório de Transações' foi projetado sob o princípio do Atrito Positivo: "
                "garantir que você conscientemente defina a categoria de cada gasto antes de aprová-lo.\n\n"
                "Por favor, selecione uma categoria para todas as linhas ou desmarque as que não deseja importar agora."
            )
            QMessageBox.warning(self, "Atrito Positivo: Transações Pendentes", msg)
            return

        if not transacoes_para_salvar:
            QMessageBox.warning(self, "Aviso", "Nenhuma transação classificada pronta para salvar.")
            return

        try:
            # Tarefa 2.3: Inserção em lote usando executar_query_lote (cursor.executemany)
            parametros_lote = [
                (data_str, desc_str, val, cat_id, 'Importado', 0)
                for data_str, desc_str, val, cat_id in transacoes_para_salvar
            ]
            self.db.executar_query_lote(
                "INSERT INTO transacoes (data, descricao, valor, categoria_id, origem, recorrente) VALUES (?, ?, ?, ?, ?, ?)",
                parametros_lote
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Salvar", f"Ocorreu um erro ao salvar o lote no banco de dados:\n{e}")
            return

        QMessageBox.information(
            self,
            "Lote Consolidado!",
            f"🎉 Sucesso!\n\n{len(transacoes_para_salvar)} transação(ões) foram consolidadas com sucesso no seu Livro-Caixa!"
        )
        self.accept()


class DialogBoasVindasRecorrentes(QDialog):
    """
    O Pop-up de Boas-Vindas do Assistente de Início (Contas Recorrentes):
    Atrito Positivo com lista editável (valores e datas ajustáveis) e o Loop Autolimpante.
    """
    def __init__(self, contas_pendentes, mes_atual, mes_passado, db, parent=None):
        super().__init__(parent)
        self.contas_pendentes = contas_pendentes
        self.mes_atual = mes_atual
        self.mes_passado = mes_passado
        self.db = db
        self.setWindowTitle("Assistente de Início - Contas Recorrentes")
        self.resize(920, 560)
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

        meses_nomes = {
            '01': 'Janeiro', '02': 'Fevereiro', '03': 'Março', '04': 'Abril',
            '05': 'Maio', '06': 'Junho', '07': 'Julho', '08': 'Agosto',
            '09': 'Setembro', '10': 'Outubro', '11': 'Novembro', '12': 'Dezembro'
        }
        
        m_atual_num = self.mes_atual.split('-')[1]
        a_atual_num = self.mes_atual.split('-')[0]
        nome_mes_atual = f"{meses_nomes.get(m_atual_num, m_atual_num)}/{a_atual_num}"

        m_pass_num = self.mes_passado.split('-')[1]
        a_pass_num = self.mes_passado.split('-')[0]
        nome_mes_passado = f"{meses_nomes.get(m_pass_num, m_pass_num)}/{a_pass_num}"

        total_inicial = sum(float(c['valor']) for c in self.contas_pendentes)

        res_nome = self.db.buscar_dados("SELECT valor FROM configuracoes WHERE chave='perfil_nome'")
        nome_usuario = res_nome[0]['valor'] if res_nome and res_nome[0]['valor'] else "Investidor"

        # 1. Cabeçalho de Boas-Vindas
        lbl_titulo = QLabel("🔁 Assistente de Início: Contas Recorrentes")
        lbl_titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #fab387;")

        lbl_saudacao = QLabel(
            f"Olá, {nome_usuario}! Iniciamos um novo mês (<b>{nome_mes_atual}</b>). "
            f"Encontrei <b>{len(self.contas_pendentes)} conta(s) recorrente(s)</b> (R$ {total_inicial:.2f}) de {nome_mes_passado}. "
            "Deseja lançá-las agora?"
        )
        lbl_saudacao.setStyleSheet("color: #cdd6f4; font-size: 14px;")
        lbl_saudacao.setWordWrap(True)

        lbl_dica = QLabel(
            "⚡ <b>Pulo do Gato de UX:</b> Altere os valores que variam (ex: energia de R$ 220 para R$ 240) diretamente na tabela abaixo. "
            "<br>Se encerrou ou cancelou alguma assinatura (ex: consórcio), basta <b>desmarcá-la ou excluí-la</b>: ela morrerá naturalmente e não será cobrada no mês seguinte (<i>Loop Autolimpante</i>)."
        )
        lbl_dica.setStyleSheet("background-color: #313244; color: #89b4fa; padding: 10px; border-radius: 6px; font-size: 12px;")
        lbl_dica.setWordWrap(True)

        layout.addWidget(lbl_titulo)
        layout.addWidget(lbl_saudacao)
        layout.addWidget(lbl_dica)

        # 2. Tabela de Contas
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(6)
        self.tabela.setHorizontalHeaderLabels([
            "Lançar?", "Data Prevista", "Descrição", "Categoria / Regra", "Valor Previsto", "Descartar"
        ])

        self.tabela.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(0, 75)

        self.tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(1, 125)

        self.tabela.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        self.tabela.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(3, 210)

        self.tabela.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(4, 135)

        self.tabela.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(5, 70)

        layout.addWidget(self.tabela)

        # 3. Rodapé
        layout_rodape = QHBoxLayout()

        self.lbl_stats = QLabel("Carregando...")
        self.lbl_stats.setStyleSheet("color: #cdd6f4; font-weight: bold; font-size: 13px;")

        btn_cancelar = QPushButton("Lembrar Mais Tarde")
        btn_cancelar.setStyleSheet("background-color: #45475a; color: #cdd6f4; font-weight: bold; padding: 8px 16px; border-radius: 6px;")
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.clicked.connect(self.reject)

        btn_confirmar = QPushButton("💾 Confirmar Lançamentos")
        btn_confirmar.setStyleSheet("background-color: #a6e3a1; color: #11111b; font-weight: bold; padding: 8px 20px; border-radius: 6px; font-size: 14px;")
        btn_confirmar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_confirmar.clicked.connect(self.confirmar_lancamentos)

        layout_rodape.addWidget(self.lbl_stats)
        layout_rodape.addStretch()
        layout_rodape.addWidget(btn_cancelar)
        layout_rodape.addWidget(btn_confirmar)

        layout.addLayout(layout_rodape)

        # 4. Preenchimento Inicial
        self.preencher_tabela()
        self.atualizar_estatisticas()

    def preencher_tabela(self):
        ano_atual = int(self.mes_atual.split('-')[0])
        mes_atual_num = int(self.mes_atual.split('-')[1])
        dias_no_mes = QDate(ano_atual, mes_atual_num, 1).daysInMonth()

        self.tabela.setRowCount(0)
        for i, item in enumerate(self.contas_pendentes):
            self.tabela.insertRow(i)

            # Col 0: Checkbox Lançar (Default marcado)
            widget_chk = QWidget()
            layout_chk = QHBoxLayout(widget_chk)
            layout_chk.setContentsMargins(0, 0, 0, 0)
            layout_chk.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk = QCheckBox()
            chk.setChecked(True)
            chk.stateChanged.connect(lambda _, r=i: self.atualizar_estatisticas())
            layout_chk.addWidget(chk)
            self.tabela.setCellWidget(i, 0, widget_chk)

            # Armazena categoria_id no item de metadados
            table_item_chk = QTableWidgetItem()
            table_item_chk.setData(Qt.ItemDataRole.UserRole, item['categoria_id'])
            self.tabela.setItem(i, 0, table_item_chk)

            # Col 1: Data prevista (dia correspondente no mês atual)
            dia_orig = 1
            if '-' in item.get('data', ''):
                try:
                    dia_orig = int(item['data'].split('-')[2])
                except Exception:
                    dia_orig = 1
            dia_final = min(dia_orig, dias_no_mes)
            data_projetada = QDate(ano_atual, mes_atual_num, dia_final)

            input_data = QDateEdit()
            input_data.setCalendarPopup(True)
            input_data.setDate(data_projetada)
            self.tabela.setCellWidget(i, 1, input_data)

            # Col 2: Descrição (QLineEdit editável)
            desc_limpa = item['descricao'].replace('🔁', '').strip()
            input_desc = QLineEdit(desc_limpa)
            self.tabela.setCellWidget(i, 2, input_desc)

            # Col 3: Categoria / Regra 50/30/20 (Informativo)
            grupo = item.get('grupo_regra', 'Sem Grupo')
            cat_nome = item.get('categoria', 'Geral')
            lbl_cat = QLabel(f"[{grupo}] {cat_nome}")
            lbl_cat.setStyleSheet("color: #89b4fa; font-weight: bold; padding-left: 5px;")
            self.tabela.setCellWidget(i, 3, lbl_cat)

            # Col 4: Valor Previsto (QDoubleSpinBox editável para contas variáveis)
            spin_val = QDoubleSpinBox()
            spin_val.setRange(0.01, 1000000.0)
            spin_val.setGroupSeparatorShown(True)
            spin_val.setPrefix("R$ ")
            spin_val.setValue(float(item['valor']))
            spin_val.valueChanged.connect(lambda _, r=i: self.atualizar_estatisticas())
            self.tabela.setCellWidget(i, 4, spin_val)

            # Col 5: Botão Descartar Linha (Loop Autolimpante)
            widget_del = QWidget()
            layout_del = QHBoxLayout(widget_del)
            layout_del.setContentsMargins(0, 0, 0, 0)
            layout_del.setAlignment(Qt.AlignmentFlag.AlignCenter)
            btn_del = QPushButton()
            btn_del.setIcon(qta.icon('fa5s.trash-alt', color='#f38ba8'))
            btn_del.setStyleSheet("background: transparent; border: none;")
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.setToolTip("Descartar esta conta da lista (Loop Autolimpante)")
            btn_del.clicked.connect(lambda checked, b=btn_del: self.remover_linha(b))
            layout_del.addWidget(btn_del)
            self.tabela.setCellWidget(i, 5, widget_del)

    def remover_linha(self, btn):
        for row in range(self.tabela.rowCount()):
            widget = self.tabela.cellWidget(row, 5)
            if widget and widget.isAncestorOf(btn):
                self.tabela.removeRow(row)
                self.atualizar_estatisticas()
                break

    def atualizar_estatisticas(self):
        total_linhas = self.tabela.rowCount()
        total_marcados = 0
        soma_total = 0.0

        for row in range(total_linhas):
            widget_chk = self.tabela.cellWidget(row, 0)
            chk = widget_chk.findChild(QCheckBox) if widget_chk else None
            if chk and chk.isChecked():
                total_marcados += 1
                spin_val = self.tabela.cellWidget(row, 4)
                if spin_val:
                    soma_total += spin_val.value()

        self.lbl_stats.setText(
            f"Selecionadas para lançamento: <b>{total_marcados}/{total_linhas}</b> | "
            f"Total: <span style='color: #a6e3a1; font-weight: bold;'>R$ {soma_total:.2f}</span>"
        )

    def confirmar_lancamentos(self):
        contas_para_salvar = []
        for row in range(self.tabela.rowCount()):
            widget_chk = self.tabela.cellWidget(row, 0)
            chk = widget_chk.findChild(QCheckBox) if widget_chk else None
            if not chk or not chk.isChecked():
                continue

            input_data = self.tabela.cellWidget(row, 1)
            input_desc = self.tabela.cellWidget(row, 2)
            spin_val = self.tabela.cellWidget(row, 4)
            table_item = self.tabela.item(row, 0)
            cat_id = table_item.data(Qt.ItemDataRole.UserRole) if table_item else None

            data_str = input_data.date().toString("yyyy-MM-dd")
            desc_str = input_desc.text().strip() or "Conta Recorrente"
            valor = spin_val.value()

            contas_para_salvar.append((data_str, desc_str, valor, cat_id))

        if not contas_para_salvar:
            QMessageBox.information(self, "Aviso", "Nenhuma conta foi selecionada para lançamento.")
            self.reject()
            return

        try:
            parametros_recorrentes = [
                (data_str, desc_str, valor, cat_id, 'Recorrente', 1)
                for data_str, desc_str, valor, cat_id in contas_para_salvar
            ]
            self.db.executar_query_lote(
                "INSERT INTO transacoes (data, descricao, valor, categoria_id, origem, recorrente) VALUES (?, ?, ?, ?, ?, ?)",
                parametros_recorrentes
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Salvar", f"Erro ao registrar contas recorrentes no banco de dados:\n{e}")
            return

        QMessageBox.information(
            self,
            "Contas Confirmadas!",
            f"🎉 Sucesso!\n\n{len(contas_para_salvar)} contas recorrentes foram lançadas no seu Livro-Caixa de {self.mes_atual}."
        )
        self.accept()


class DialogGerenciarCategorias(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Gerenciar Categorias")
        self.setMinimumWidth(500)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.input_nome = QLineEdit()
        self.input_nome.setStyleSheet("background-color: #313244; padding: 5px; color: #cdd6f4;")
        self.input_nome.setPlaceholderText("Ex: Ração do Cachorro")
        
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Despesa", "Receita"])
        self.combo_tipo.setStyleSheet("background-color: #313244; padding: 5px; color: #cdd6f4;")
        
        self.combo_grupo = QComboBox()
        self.combo_grupo.addItems(["Necessidades", "Desejos", "Construção de Riqueza", "Sem Grupo"])
        self.combo_grupo.setStyleSheet("background-color: #313244; padding: 5px; color: #cdd6f4;")
        
        self.combo_tipo.currentTextChanged.connect(self.atualizar_grupos)
        
        form_layout.addRow("Nome da Categoria:", self.input_nome)
        form_layout.addRow("Tipo:", self.combo_tipo)
        form_layout.addRow("Regra 50/30/20:", self.combo_grupo)
        
        btn_adicionar = QPushButton("Criar Categoria")
        btn_adicionar.setStyleSheet("background-color: #a6e3a1; color: #11111b; font-weight: bold; padding: 8px;")
        btn_adicionar.clicked.connect(self.adicionar_categoria)
        
        layout.addLayout(form_layout)
        layout.addWidget(btn_adicionar)
        
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(4)
        self.tabela.setHorizontalHeaderLabels(["Nome", "Tipo", "Grupo", "Ação"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tabela)
        
        self.carregar_categorias()
        
    def atualizar_grupos(self, tipo):
        if tipo == "Receita":
            self.combo_grupo.clear()
            self.combo_grupo.addItem("Sem Grupo")
            self.combo_grupo.setEnabled(False)
        else:
            self.combo_grupo.setEnabled(True)
            self.combo_grupo.clear()
            self.combo_grupo.addItems(["Necessidades", "Desejos", "Construção de Riqueza", "Sem Grupo"])
            
    def adicionar_categoria(self):
        nome = self.input_nome.text().strip()
        tipo = self.combo_tipo.currentText()
        grupo = self.combo_grupo.currentText()
        
        if not nome:
            QMessageBox.warning(self, "Aviso", "O nome da categoria não pode estar vazio.")
            return
            
        try:
            self.db.executar_query("INSERT INTO categorias (nome, tipo, grupo_regra) VALUES (?, ?, ?)", (nome, tipo, grupo))
            self.input_nome.clear()
            self.carregar_categorias()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao adicionar: {e}")
            
    def carregar_categorias(self):
        self.tabela.setRowCount(0)
        categorias = self.db.buscar_dados("SELECT id, nome, tipo, grupo_regra FROM categorias ORDER BY nome")
        for linha_idx, cat in enumerate(categorias):
            self.tabela.insertRow(linha_idx)
            self.tabela.setItem(linha_idx, 0, QTableWidgetItem(str(cat['nome'])))
            self.tabela.setItem(linha_idx, 1, QTableWidgetItem(str(cat['tipo'])))
            self.tabela.setItem(linha_idx, 2, QTableWidgetItem(str(cat.get('grupo_regra', 'Sem Grupo'))))
            
            widget_excluir = QWidget()
            layout_excluir = QHBoxLayout(widget_excluir)
            layout_excluir.setContentsMargins(0, 0, 0, 0)
            layout_excluir.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            btn_excluir = QPushButton()
            btn_excluir.setIcon(qta.icon('fa5s.trash-alt', color='#f38ba8'))
            btn_excluir.setStyleSheet("background: transparent; border: none;")
            btn_excluir.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_excluir.clicked.connect(lambda checked, id_cat=cat['id']: self.excluir_categoria(id_cat))
            
            layout_excluir.addWidget(btn_excluir)
            self.tabela.setCellWidget(linha_idx, 3, widget_excluir)
            
    def excluir_categoria(self, id_cat):
        transacoes = self.db.buscar_dados("SELECT id FROM transacoes WHERE categoria_id = ?", (id_cat,))
        if transacoes:
            QMessageBox.warning(self, "Erro", "Não é possível excluir esta categoria pois existem transações vinculadas a ela.")
            return
            
        resposta = QMessageBox.question(self, "Confirmar", "Deseja excluir esta categoria?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resposta == QMessageBox.StandardButton.Yes:
            self.db.executar_query("DELETE FROM categorias WHERE id = ?", (id_cat,))
            self.carregar_categorias()


class PaginaFinancas(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        titulo = QLabel("Contas Pessoais")
        titulo.setObjectName("tituloPagina")
        
        # --- FILTRO MENSAL E IMPORTAÇÃO ---
        layout_filtro = QHBoxLayout()
        lbl_filtro = QLabel("Período:")
        lbl_filtro.setStyleSheet("color: #cdd6f4; font-weight: bold; font-size: 16px;")
        self.combo_mes = QComboBox()
        self.combo_mes.setStyleSheet("background-color: #313244; padding: 5px; color: #cdd6f4; font-size: 14px; min-width: 150px;")
        self.combo_mes.currentIndexChanged.connect(self.carregar_dados)
        
        btn_importar = QPushButton("📥 Importar Fatura (CSV / OFX)")
        btn_importar.setStyleSheet("background-color: #89b4fa; color: #11111b; font-weight: bold; padding: 7px 15px; border-radius: 6px; font-size: 13px;")
        btn_importar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_importar.clicked.connect(self.importar_fatura)

        btn_recorrentes = QPushButton("🔁 Contas Recorrentes")
        btn_recorrentes.setStyleSheet("background-color: #fab387; color: #11111b; font-weight: bold; padding: 7px 15px; border-radius: 6px; font-size: 13px;")
        btn_recorrentes.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_recorrentes.setToolTip("Verificar e lançar contas recorrentes do mês anterior")
        btn_recorrentes.clicked.connect(self.acionar_assistente_recorrentes)
        
        layout_filtro.addWidget(lbl_filtro)
        layout_filtro.addWidget(self.combo_mes)
        layout_filtro.addSpacing(15)
        layout_filtro.addWidget(btn_importar)
        layout_filtro.addWidget(btn_recorrentes)
        layout_filtro.addStretch()

        # --- CARDS DE RESUMO (KPIs Gerais) ---
        layout_kpis = QHBoxLayout()
        
        self.lbl_receitas = QLabel("Receitas\nR$ 0,00")
        self.lbl_receitas.setStyleSheet("background-color: #313244; padding: 15px; border-radius: 8px; color: #a6e3a1; font-weight: bold; font-size: 18px;")
        self.lbl_receitas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_despesas = QLabel("Despesas\nR$ 0,00")
        self.lbl_despesas.setStyleSheet("background-color: #313244; padding: 15px; border-radius: 8px; color: #f38ba8; font-weight: bold; font-size: 18px;")
        self.lbl_despesas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_saldo = QLabel("Saldo Livre\nR$ 0,00")
        self.lbl_saldo.setStyleSheet("background-color: #313244; padding: 15px; border-radius: 8px; color: #89b4fa; font-weight: bold; font-size: 18px;")
        self.lbl_saldo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout_kpis.addWidget(self.lbl_receitas)
        layout_kpis.addWidget(self.lbl_despesas)
        layout_kpis.addWidget(self.lbl_saldo)
        
        # --- INDICADORES DA REGRA 50/30/20 ---
        layout_regra = QHBoxLayout()
        
        self.lbl_pct_necessidades = QLabel("Necessidades\n0.0% (Teto: 50%)")
        self.lbl_pct_necessidades.setStyleSheet("background-color: #313244; padding: 10px; border-radius: 8px; color: #89b4fa; font-weight: bold;")
        self.lbl_pct_necessidades.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_pct_desejos = QLabel("Desejos\n0.0% (Teto: 30%)")
        self.lbl_pct_desejos.setStyleSheet("background-color: #313244; padding: 10px; border-radius: 8px; color: #f9e2af; font-weight: bold;")
        self.lbl_pct_desejos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_pct_riqueza = QLabel("Construção Riqueza\n0.0% (Meta: > 20%)")
        self.lbl_pct_riqueza.setStyleSheet("background-color: #313244; padding: 10px; border-radius: 8px; color: #a6e3a1; font-weight: bold;")
        self.lbl_pct_riqueza.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout_regra.addWidget(self.lbl_pct_necessidades)
        layout_regra.addWidget(self.lbl_pct_desejos)
        layout_regra.addWidget(self.lbl_pct_riqueza)
        
        # --- O FORMULÁRIO DE ENTRADA MANUAL ---
        layout_form = QHBoxLayout()
        
        self.input_data = QDateEdit()
        self.input_data.setCalendarPopup(True)
        self.input_data.setDate(QDate.currentDate())
        self.input_data.setStyleSheet("background-color: #313244; padding: 8px; color: #cdd6f4;")
        
        self.input_desc = QLineEdit()
        self.input_desc.setPlaceholderText("Descrição (Ex: Conta de Luz)")
        self.input_desc.setStyleSheet("background-color: #313244; padding: 8px;")
        
        self.input_valor = QDoubleSpinBox()
        self.input_valor.setGroupSeparatorShown(True)
        self.input_valor.setRange(0.01, 1000000.0)
        self.input_valor.setPrefix("R$ ")
        self.input_valor.setMaximumWidth(150)
        self.input_valor.setStyleSheet("font-size: 14px;")
        
        self.combo_categoria = QComboBox()
        self.combo_categoria.setStyleSheet("background-color: #313244; padding: 8px;")
        
        self.carregar_categorias_combo()
            
        btn_gerenciar_cat = QPushButton("⚙️ Gerenciar")
        btn_gerenciar_cat.setStyleSheet("background-color: #89b4fa; color: #11111b; font-weight: bold; padding: 8px; border-radius: 5px;")
        btn_gerenciar_cat.clicked.connect(self.abrir_gerenciador_categorias)
            
        btn_adicionar_transacao = QPushButton("Adicionar")
        btn_adicionar_transacao.setStyleSheet("background-color: #a6e3a1; color: #11111b; font-weight: bold; padding: 8px; border-radius: 5px;")
        btn_adicionar_transacao.clicked.connect(self.salvar_transacao)
        
        layout_form.addWidget(self.input_data)
        layout_form.addWidget(self.input_desc, 1)
        layout_form.addWidget(self.combo_categoria)
        layout_form.addWidget(btn_gerenciar_cat)
        layout_form.addWidget(self.input_valor)
        layout_form.addWidget(btn_adicionar_transacao)

        # Container do Formulário + Checkbox de Conta Recorrente
        layout_form_container = QVBoxLayout()
        layout_form_container.setSpacing(4)
        layout_form_container.addLayout(layout_form)

        layout_sub_form = QHBoxLayout()
        layout_sub_form.addStretch()
        self.chk_recorrente = QCheckBox("🔁 Conta Recorrente (Repetir mensalmente)")
        self.chk_recorrente.setStyleSheet("color: #fab387; font-weight: bold; font-size: 12px; padding: 2px;")
        self.chk_recorrente.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_recorrente.setToolTip("Marque para que esta despesa seja sugerida automaticamente todo início de mês.")
        layout_sub_form.addWidget(self.chk_recorrente)
        layout_form_container.addLayout(layout_sub_form)
        
        # --- A TABELA DE HISTÓRICO ---
        self.tabela_financas = QTableWidget()
        self.tabela_financas.setColumnCount(7)
        self.tabela_financas.setHorizontalHeaderLabels(["Data", "Descrição", "Categoria", "Tipo", "Grupo", "Valor", "Excluir"])
        self.tabela_financas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Painel Superior: KPIs e Indicadores à Esquerda, Gráfico de Rosca 50/30/20 à Direita
        layout_painel_cards = QHBoxLayout()
        layout_coluna_kpis = QVBoxLayout()
        layout_coluna_kpis.addLayout(layout_kpis)
        layout_coluna_kpis.addLayout(layout_regra)
        layout_painel_cards.addLayout(layout_coluna_kpis, 62)

        # Frame do Gráfico de Rosca 50/30/20
        self.frame_rosca = QFrame()
        self.frame_rosca.setStyleSheet("background-color: #262939; border-radius: 10px; border: 1px solid #313244;")
        layout_frame_rosca = QVBoxLayout(self.frame_rosca)
        layout_frame_rosca.setContentsMargins(10, 8, 10, 8)
        layout_frame_rosca.setSpacing(4)

        self.lbl_titulo_rosca = QLabel("📊 Raio-X 50/30/20 do Mês")
        self.lbl_titulo_rosca.setStyleSheet("color: #cdd6f4; font-weight: bold; font-size: 13px;")
        layout_frame_rosca.addWidget(self.lbl_titulo_rosca)

        self.fig_rosca = Figure(figsize=(3.8, 1.8), dpi=100)
        self.fig_rosca.patch.set_facecolor('#262939')
        self.canvas_rosca = FigureCanvas(self.fig_rosca)
        self.canvas_rosca.setStyleSheet("background-color: transparent;")
        layout_frame_rosca.addWidget(self.canvas_rosca)

        layout_painel_cards.addWidget(self.frame_rosca, 38)

        layout.addWidget(titulo)
        layout.addLayout(layout_filtro)
        layout.addLayout(layout_painel_cards)
        layout.addLayout(layout_form_container)
        layout.addWidget(self.tabela_financas)
        
        self.carregar_meses()

    def importar_fatura(self):
        caminho_arquivo, _ = QFileDialog.getOpenFileName(
            self,
            "Importar Fatura Bancária",
            "",
            "Faturas Bancárias (*.csv *.ofx);;Arquivos OFX (*.ofx);;Arquivos CSV (*.csv);;Todos os Arquivos (*)"
        )
        if not caminho_arquivo:
            return

        try:
            transacoes = ExtratorFaturas.extrair(caminho_arquivo)
        except Exception as e:
            QMessageBox.critical(self, "Erro na Extração", f"Falha ao ler o arquivo bancário:\n\n{e}")
            return

        if not transacoes:
            QMessageBox.warning(self, "Aviso", "Nenhuma transação foi identificada no arquivo.")
            return

        dialog = DialogPurgatorioTransacoes(transacoes, self.db, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            mes_foco = transacoes[0]['data'][:7] if transacoes and 'data' in transacoes[0] else None
            self.carregar_meses(mes_foco=mes_foco)
            self.carregar_dados()

    def acionar_assistente_recorrentes(self):
        janela_principal = self.window()
        if hasattr(janela_principal, 'verificar_contas_recorrentes'):
            janela_principal.verificar_contas_recorrentes(silencioso_se_vazio=False)

    def salvar_transacao(self):
        data_str = self.input_data.date().toString("yyyy-MM-dd")
        descricao = self.input_desc.text().strip()
        valor = self.input_valor.value()
        categoria_id = self.combo_categoria.currentData()
        recorrente = 1 if self.chk_recorrente.isChecked() else 0
        
        if not descricao:
            QMessageBox.warning(self, "Aviso", "A descrição não pode ficar vazia.")
            return
            
        query = "INSERT INTO transacoes (data, descricao, valor, categoria_id, origem, recorrente) VALUES (?, ?, ?, ?, 'Manual', ?)"
        self.db.executar_query(query, (data_str, descricao, valor, categoria_id, recorrente))
        
        self.input_desc.clear()
        self.input_valor.setValue(0.0)
        self.chk_recorrente.setChecked(False)
        
        mes_inserido = data_str[:7]
        self.carregar_meses(mes_foco=mes_inserido)
        self.carregar_dados()
        QMessageBox.information(self, "Sucesso", "Transação registrada!")

    def carregar_categorias_combo(self):
        self.combo_categoria.clear()
        categorias = self.db.buscar_dados("SELECT id, nome, tipo, grupo_regra FROM categorias ORDER BY nome")
        for cat in categorias:
            grupo = cat.get('grupo_regra', 'Sem Grupo')
            self.combo_categoria.addItem(f"[{grupo}] {cat['nome']}", cat['id'])

    def abrir_gerenciador_categorias(self):
        dialog = DialogGerenciarCategorias(self.db, self)
        dialog.exec()
        self.carregar_categorias_combo()

    def carregar_meses(self, mes_foco=None):
        mes_atual_selecionado = mes_foco or self.combo_mes.currentData()
        self.combo_mes.blockSignals(True)
        self.combo_mes.clear()
        
        query = "SELECT DISTINCT substr(data, 1, 7) as mes_ano FROM transacoes ORDER BY mes_ano DESC"
        resultados = self.db.buscar_dados(query)
        
        meses = [res['mes_ano'] for res in resultados if res['mes_ano']]
        mes_hoje = QDate.currentDate().toString("yyyy-MM")
        
        if mes_hoje not in meses:
            meses.append(mes_hoje)
            
        meses = list(set(meses))
        meses.sort(reverse=True)
        
        for m in meses:
            ano, mes = m.split('-')
            self.combo_mes.addItem(f"{mes}/{ano}", m)
            
        if mes_atual_selecionado and self.combo_mes.findData(mes_atual_selecionado) >= 0:
            idx = self.combo_mes.findData(mes_atual_selecionado)
            self.combo_mes.setCurrentIndex(idx)
        else:
            idx = self.combo_mes.findData(mes_hoje)
            if idx >= 0:
                self.combo_mes.setCurrentIndex(idx)
                
        self.combo_mes.blockSignals(False)

    def carregar_dados(self):
        mes_selecionado = self.combo_mes.currentData()
        if not mes_selecionado:
            return
            
        self.tabela_financas.setRowCount(0)
        
        query = f"""
            SELECT t.id, t.data, t.descricao, t.valor, t.recorrente, c.nome as categoria, c.tipo, c.grupo_regra 
            FROM transacoes t
            JOIN categorias c ON t.categoria_id = c.id
            WHERE t.data LIKE '{mes_selecionado}-%'
            ORDER BY t.data DESC
        """
        resultados = self.db.buscar_dados(query)
        
        total_receitas = 0.0
        total_despesas = 0.0
        
        gasto_necessidades = 0.0
        gasto_desejos = 0.0
        gasto_riqueza = 0.0
        
        for linha_idx, dados in enumerate(resultados):
            self.tabela_financas.insertRow(linha_idx)
            
            grupo = dados.get('grupo_regra', 'Sem Grupo')
            valor_transacao = float(dados['valor'])
            
            if dados['tipo'] == "Receita":
                total_receitas += valor_transacao
                item_valor = QTableWidgetItem(f"+ R$ {valor_transacao:.2f}")
                item_valor.setForeground(Qt.GlobalColor.green)
            else:
                total_despesas += valor_transacao
                item_valor = QTableWidgetItem(f"- R$ {valor_transacao:.2f}")
                item_valor.setForeground(Qt.GlobalColor.red)
                
                if grupo == "Necessidades":
                    gasto_necessidades += valor_transacao
                elif grupo == "Desejos":
                    gasto_desejos += valor_transacao
                elif grupo == "Construção de Riqueza":
                    gasto_riqueza += valor_transacao
                
            item_tipo = QTableWidgetItem(str(dados['tipo']))
            item_grupo = QTableWidgetItem(grupo)
            
            desc_texto = str(dados['descricao'])
            if dados.get('recorrente') == 1 and not desc_texto.startswith("🔁"):
                desc_texto = f"🔁 {desc_texto}"
            
            self.tabela_financas.setItem(linha_idx, 0, QTableWidgetItem(str(dados['data'])))
            self.tabela_financas.setItem(linha_idx, 1, QTableWidgetItem(desc_texto))
            self.tabela_financas.setItem(linha_idx, 2, QTableWidgetItem(str(dados['categoria'])))
            self.tabela_financas.setItem(linha_idx, 3, item_tipo)
            self.tabela_financas.setItem(linha_idx, 4, item_grupo)
            self.tabela_financas.setItem(linha_idx, 5, item_valor)

            widget_excluir = QWidget()
            layout_excluir = QHBoxLayout(widget_excluir)
            layout_excluir.setContentsMargins(0, 0, 0, 0)
            layout_excluir.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            btn_excluir = QPushButton()
            btn_excluir.setIcon(qta.icon('fa5s.trash-alt', color='#f38ba8'))
            btn_excluir.setStyleSheet("background-color: transparent; border: none;")
            btn_excluir.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_excluir.clicked.connect(lambda checked, id_trans=dados['id']: self.excluir_transacao(id_trans))
            
            layout_excluir.addWidget(btn_excluir)
            self.tabela_financas.setCellWidget(linha_idx, 6, widget_excluir)

        saldo = total_receitas - total_despesas
        self.lbl_receitas.setText(f"Receitas\nR$ {total_receitas:.2f}")
        self.lbl_despesas.setText(f"Despesas\nR$ {total_despesas:.2f}")
        self.lbl_saldo.setText(f"Saldo Livre\nR$ {saldo:.2f}")

        res_nec = self.db.buscar_dados("SELECT valor FROM configuracoes WHERE chave='meta_necessidades'")
        res_des = self.db.buscar_dados("SELECT valor FROM configuracoes WHERE chave='meta_desejos'")
        res_riq = self.db.buscar_dados("SELECT valor FROM configuracoes WHERE chave='meta_riqueza'")
        
        meta_nec = int(res_nec[0]['valor']) if res_nec else 50
        meta_des = int(res_des[0]['valor']) if res_des else 30
        meta_riq = int(res_riq[0]['valor']) if res_riq else 20

        if total_receitas > 0:
            pct_necessidades = (gasto_necessidades / total_receitas) * 100
            pct_desejos = (gasto_desejos / total_receitas) * 100
            pct_riqueza = (gasto_riqueza / total_receitas) * 100
        else:
            pct_necessidades = pct_desejos = pct_riqueza = 0.0
            
        cor_nec = "#f38ba8" if pct_necessidades > meta_nec else "#89b4fa"
        cor_des = "#f38ba8" if pct_desejos > meta_des else "#f9e2af"
        cor_riq = "#f38ba8" if pct_riqueza < meta_riq and total_receitas > 0 else "#a6e3a1"
        
        self.lbl_pct_necessidades.setText(f"Necessidades\n{pct_necessidades:.1f}% (Teto: {meta_nec}%)")
        self.lbl_pct_necessidades.setStyleSheet(f"background-color: #313244; padding: 10px; border-radius: 8px; color: {cor_nec}; font-weight: bold;")
        
        self.lbl_pct_desejos.setText(f"Desejos\n{pct_desejos:.1f}% (Teto: {meta_des}%)")
        self.lbl_pct_desejos.setStyleSheet(f"background-color: #313244; padding: 10px; border-radius: 8px; color: {cor_des}; font-weight: bold;")
        
        self.lbl_pct_riqueza.setText(f"Construção Riqueza\n{pct_riqueza:.1f}% (Meta: > {meta_riq}%)")
        self.lbl_pct_riqueza.setStyleSheet(f"background-color: #313244; padding: 10px; border-radius: 8px; color: {cor_riq}; font-weight: bold;")

        self.atualizar_grafico_rosca(gasto_necessidades, gasto_desejos, gasto_riqueza, total_despesas, total_receitas, meta_nec, meta_des, meta_riq)

    def atualizar_grafico_rosca(self, gasto_nec, gasto_des, gasto_riq, total_despesas, total_receitas, meta_nec, meta_des, meta_riq):
        self.fig_rosca.clear()
        ax = self.fig_rosca.add_subplot(111)
        ax.set_facecolor('#262939')

        soma_categorizada = gasto_nec + gasto_des + gasto_riq
        if total_despesas > 0:
            labels = []
            valores = []
            cores = []

            base_calc = total_receitas if total_receitas > 0 else total_despesas

            if gasto_nec > 0:
                pct = (gasto_nec / base_calc) * 100
                labels.append(f"Nec: {pct:.0f}%")
                valores.append(gasto_nec)
                cores.append('#89b4fa')

            if gasto_des > 0:
                pct = (gasto_des / base_calc) * 100
                labels.append(f"Des: {pct:.0f}%")
                valores.append(gasto_des)
                cores.append('#f9e2af')

            if gasto_riq > 0:
                pct = (gasto_riq / base_calc) * 100
                labels.append(f"Riq: {pct:.0f}%")
                valores.append(gasto_riq)
                cores.append('#a6e3a1')

            gasto_outros = max(0.0, total_despesas - soma_categorizada)
            if gasto_outros > 0.01:
                pct = (gasto_outros / base_calc) * 100
                labels.append(f"Outros: {pct:.0f}%")
                valores.append(gasto_outros)
                cores.append('#cba6f7')

            wedges, _ = ax.pie(
                valores,
                colors=cores,
                startangle=90,
                wedgeprops=dict(width=0.45, edgecolor='#262939', linewidth=2)
            )

            # Texto Central no buraco da rosca
            texto_centro = f"R$ {total_despesas:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            ax.text(
                0, 0,
                f"Total\n{texto_centro}",
                ha='center', va='center',
                color='#cdd6f4',
                fontsize=8,
                fontweight='bold'
            )

            ax.legend(
                wedges,
                labels,
                loc="center left",
                bbox_to_anchor=(0.95, 0.5),
                frameon=False,
                fontsize=8,
                labelcolor='#cdd6f4'
            )
        else:
            circulo = mpatches.Circle((0, 0), 0.7, color='#313244', fill=False, linewidth=3)
            ax.add_patch(circulo)
            ax.text(0, 0, "Sem Despesas\nno Período", ha='center', va='center', color='#6c7086', fontsize=8)
            ax.set_xlim(-1, 1)
            ax.set_ylim(-1, 1)

        ax.axis('equal')
        self.fig_rosca.subplots_adjust(left=0.02, right=0.62, top=0.98, bottom=0.02)
        self.canvas_rosca.draw()

    def excluir_transacao(self, id_transacao):
        resposta = QMessageBox.question(
            self, "Confirmar Exclusão", 
            "Deseja realmente apagar este registro?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if resposta == QMessageBox.StandardButton.Yes:
            self.db.executar_query("DELETE FROM transacoes WHERE id = ?", (id_transacao,))
            self.carregar_meses()
            self.carregar_dados()
