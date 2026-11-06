from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QMessageBox, QFileDialog, QFormLayout, QDateEdit, QSpinBox, QScrollArea)
from PyQt6.QtCore import Qt, QDate
import pandas as pd
from componentes import PasswordInput

class SecaoExpansivel(QWidget):
    def __init__(self, titulo, descricao, conteudo_layout, parent=None):
        super().__init__(parent)
        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(0, 5, 0, 5)
        self.layout_principal.setSpacing(0)
        
        # Botão Cabeçalho
        self.btn_toggle = QPushButton(f"+  {titulo}")
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #D4AF37;
                font-size: 18px;
                font-weight: bold;
                text-align: left;
                padding: 15px 5px;
                border: none;
                border-bottom: 1px solid #313244;
            }
            QPushButton:hover {
                color: #f9e2af;
            }
        """)
        self.btn_toggle.clicked.connect(self.toggle_conteudo)
        
        # Container do conteúdo
        self.container_conteudo = QWidget()
        self.layout_conteudo = QVBoxLayout(self.container_conteudo)
        self.layout_conteudo.setContentsMargins(25, 15, 0, 25)
        
        # Descrição
        if descricao:
            lbl_desc = QLabel(descricao)
            lbl_desc.setStyleSheet("color: #a6adc8; font-size: 14px; margin-bottom: 15px;")
            lbl_desc.setWordWrap(True)
            self.layout_conteudo.addWidget(lbl_desc)
        
        # Adiciona o layout passado
        self.layout_conteudo.addLayout(conteudo_layout)
        
        # Inicialmente oculto
        self.container_conteudo.setVisible(False)
        
        self.layout_principal.addWidget(self.btn_toggle)
        self.layout_principal.addWidget(self.container_conteudo)
        
    def toggle_conteudo(self, checked):
        self.container_conteudo.setVisible(checked)
        if checked:
            self.btn_toggle.setText(self.btn_toggle.text().replace("+", "-", 1))
        else:
            self.btn_toggle.setText(self.btn_toggle.text().replace("-", "+", 1))

class PaginaConfig(QWidget):
    def __init__(self, db, api, fn_reset_db=None, senha_mestra=None):
        super().__init__()
        self.db = db
        self.api = api
        self.fn_reset_db = fn_reset_db
        self.senha_mestra = senha_mestra
        self.setup_ui()

    def setup_ui(self):
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll_area.setWidget(scroll_widget)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        
        titulo = QLabel("Configurações")
        titulo.setStyleSheet("color: #cdd6f4; font-size: 24px; font-weight: bold;")
        
        subtitulo = QLabel("Gerencie suas preferências, chaves de API e dados locais.")
        subtitulo.setStyleSheet("color: #a6adc8; font-size: 14px; margin-top: 5px; margin-bottom: 20px;")
        
        layout.addWidget(titulo)
        layout.addWidget(subtitulo)
        
        estilo_input = "background-color: #313244; padding: 8px; color: #cdd6f4; border-radius: 4px; border: 1px solid #45475a;"
        estilo_label = "color: #cdd6f4; font-weight: bold;"

        # --- SEÇÃO: Perfil ---
        layout_perfil = QFormLayout()
        layout_perfil.setVerticalSpacing(15)
        
        self.input_nome = QLineEdit()
        self.input_nome.setStyleSheet(estilo_input)
        self.input_nome.setPlaceholderText("Seu nome completo")
        self.input_nome.setFixedWidth(350)
        
        self.input_email = QLineEdit()
        self.input_email.setStyleSheet(estilo_input)
        self.input_email.setPlaceholderText("seu@email.com")
        self.input_email.setFixedWidth(350)
        
        self.input_nascimento = QDateEdit()
        self.input_nascimento.setStyleSheet(estilo_input)
        self.input_nascimento.setCalendarPopup(True)
        self.input_nascimento.setDisplayFormat("dd/MM/yyyy")
        self.input_nascimento.setDate(QDate.currentDate())
        self.input_nascimento.setFixedWidth(350)
        
        self.input_senha = PasswordInput("Nova senha mestre")
        estilo_senha = "background-color: #313244; padding: 8px; padding-right: 35px; color: #cdd6f4; border-radius: 4px; border: 1px solid #45475a;"
        self.input_senha.setStyleSheet(estilo_senha)
        self.input_senha.setFixedWidth(350)
        
        self.input_senha_confirma = PasswordInput("Confirme nova senha")
        self.input_senha_confirma.setStyleSheet(estilo_senha)
        self.input_senha_confirma.setFixedWidth(350)
        
        # Carregar dados do perfil se existir
        res_nome = self.db.buscar_dados("SELECT valor FROM configuracoes WHERE chave='perfil_nome'")
        if res_nome: self.input_nome.setText(res_nome[0]['valor'])
        
        res_email = self.db.buscar_dados("SELECT valor FROM configuracoes WHERE chave='perfil_email'")
        if res_email: self.input_email.setText(res_email[0]['valor'])
        
        lbl_nome = QLabel("Nome")
        lbl_nome.setStyleSheet(estilo_label)
        lbl_email = QLabel("Email")
        lbl_email.setStyleSheet(estilo_label)
        lbl_nasc = QLabel("Data Nascimento")
        lbl_nasc.setStyleSheet(estilo_label)
        lbl_senha = QLabel("Nova Senha")
        lbl_senha.setStyleSheet(estilo_label)

        layout_perfil.addRow(lbl_nome, self.input_nome)
        layout_perfil.addRow(lbl_email, self.input_email)
        layout_perfil.addRow(lbl_nasc, self.input_nascimento)
        layout_perfil.addRow(lbl_senha, self.input_senha)
        layout_perfil.addRow("", self.input_senha_confirma)
        
        # --- VERIFICADOR DE REGRAS DE SENHA ---
        self.lbl_req_tamanho = QLabel("✗ Mínimo de 8 caracteres")
        self.lbl_req_maiuscula = QLabel("✗ Pelo menos 1 letra maiúscula")
        self.lbl_req_numero = QLabel("✗ Pelo menos 1 número")
        self.lbl_req_especial = QLabel("✗ Pelo menos 1 caractere especial")
        
        estilo_req_inativo = "color: #f38ba8; font-size: 12px; margin-left: 5px;"
        self.lbl_req_tamanho.setStyleSheet(estilo_req_inativo)
        self.lbl_req_maiuscula.setStyleSheet(estilo_req_inativo)
        self.lbl_req_numero.setStyleSheet(estilo_req_inativo)
        self.lbl_req_especial.setStyleSheet(estilo_req_inativo)
        
        container_regras = QVBoxLayout()
        container_regras.setSpacing(2)
        container_regras.addWidget(self.lbl_req_tamanho)
        container_regras.addWidget(self.lbl_req_maiuscula)
        container_regras.addWidget(self.lbl_req_numero)
        container_regras.addWidget(self.lbl_req_especial)
        
        layout_perfil.addRow("", container_regras)
        self.input_senha.textChanged.connect(self.validar_regras_senha_ui)
        
        btn_salvar_perfil = QPushButton("Salvar Perfil")
        btn_salvar_perfil.setFixedWidth(150)
        btn_salvar_perfil.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_salvar_perfil.setStyleSheet("background-color: #89b4fa; color: #11111b; font-weight: bold; padding: 8px; border-radius: 4px;")
        btn_salvar_perfil.clicked.connect(self.salvar_perfil)
        layout_perfil.addWidget(btn_salvar_perfil)
        
        secao_perfil = SecaoExpansivel("Perfil", "Gerencie seus dados pessoais e altere sua senha de acesso.", layout_perfil)
        layout.addWidget(secao_perfil)

        # --- SEÇÃO: Token da API ---
        layout_token = QVBoxLayout()
        layout_token.setSpacing(10)
        self.input_token = QLineEdit()
        self.input_token.setPlaceholderText("Cole seu token da Brapi aqui...")
        self.input_token.setStyleSheet(estilo_input)
        self.input_token.setFixedWidth(350)
        self.input_token.setMaxLength(35)
        
        if self.api.token_brapi != "COLE_SEU_TOKEN_AQUI":
            self.input_token.setText(self.api.token_brapi)
            
        btn_salvar_token = QPushButton("Salvar Token")
        btn_salvar_token.setFixedWidth(150)
        btn_salvar_token.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_salvar_token.setStyleSheet("background-color: #89b4fa; color: #11111b; font-weight: bold; padding: 8px; border-radius: 4px;")
        btn_salvar_token.clicked.connect(self.atualizar_token_api)
        
        layout_token.addWidget(self.input_token)
        layout_token.addWidget(btn_salvar_token)
        
        secao_token = SecaoExpansivel("Token da Brapi", "Insira seu token para ativar atualizações de preços em tempo real.", layout_token)
        layout.addWidget(secao_token)
        
        # --- SEÇÃO: Backup de Dados ---
        layout_backup = QVBoxLayout()
        layout_backup.setSpacing(10)
        
        btn_exportar_db = QPushButton("Exportar Banco (Criptografado)")
        btn_exportar_db.setMinimumWidth(230)
        btn_exportar_db.setMaximumWidth(360)
        btn_exportar_db.setStyleSheet("background-color: #a6e3a1; color: #11111b; font-weight: bold; padding: 8px; border-radius: 4px;")
        btn_exportar_db.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_exportar_db.clicked.connect(self.exportar_db_seguro)
        
        btn_importar_db = QPushButton("Importar Banco (Criptografado)")
        btn_importar_db.setMinimumWidth(230)
        btn_importar_db.setMaximumWidth(360)
        btn_importar_db.setStyleSheet("background-color: #f9e2af; color: #11111b; font-weight: bold; padding: 8px; border-radius: 4px;")
        btn_importar_db.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_importar_db.clicked.connect(self.importar_db_seguro)
        
        btn_exportar = QPushButton("Exportar Planilha (Excel)")
        btn_exportar.setMinimumWidth(230)
        btn_exportar.setMaximumWidth(360)
        btn_exportar.setStyleSheet("background-color: #89b4fa; color: #11111b; font-weight: bold; padding: 8px; border-radius: 4px;")
        btn_exportar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_exportar.clicked.connect(self.exportar_dados_excel)
        
        layout_backup.addWidget(btn_exportar_db, alignment=Qt.AlignmentFlag.AlignLeft)
        layout_backup.addWidget(btn_importar_db, alignment=Qt.AlignmentFlag.AlignLeft)
        layout_backup.addWidget(btn_exportar, alignment=Qt.AlignmentFlag.AlignLeft)
        
        secao_backup = SecaoExpansivel("Backup de Dados", "Importe ou exporte seus dados criptografados, ou exporte uma planilha.", layout_backup)
        layout.addWidget(secao_backup)

        # --- SEÇÃO: Metas do Orçamento ---
        layout_metas = QFormLayout()
        layout_metas.setVerticalSpacing(15)
        
        self.spin_necessidades = QSpinBox()
        self.spin_necessidades.setRange(0, 100)
        self.spin_necessidades.setSuffix("%")
        self.spin_necessidades.setFixedWidth(80)
        
        self.spin_desejos = QSpinBox()
        self.spin_desejos.setRange(0, 100)
        self.spin_desejos.setSuffix("%")
        self.spin_desejos.setFixedWidth(80)
        
        self.spin_riqueza = QSpinBox()
        self.spin_riqueza.setRange(0, 100)
        self.spin_riqueza.setSuffix("%")
        self.spin_riqueza.setFixedWidth(80)
        
        res_nec = self.db.buscar_dados("SELECT valor FROM configuracoes WHERE chave='meta_necessidades'")
        res_des = self.db.buscar_dados("SELECT valor FROM configuracoes WHERE chave='meta_desejos'")
        res_riq = self.db.buscar_dados("SELECT valor FROM configuracoes WHERE chave='meta_riqueza'")
        
        self.spin_necessidades.setValue(int(res_nec[0]['valor']) if res_nec else 50)
        self.spin_desejos.setValue(int(res_des[0]['valor']) if res_des else 30)
        self.spin_riqueza.setValue(int(res_riq[0]['valor']) if res_riq else 20)
        
        lbl_nec = QLabel("Necessidades:")
        lbl_nec.setStyleSheet(estilo_label)
        lbl_des = QLabel("Desejos:")
        lbl_des.setStyleSheet(estilo_label)
        lbl_riq = QLabel("Construção de Riqueza:")
        lbl_riq.setStyleSheet(estilo_label)
        
        layout_metas.addRow(lbl_nec, self.spin_necessidades)
        layout_metas.addRow(lbl_des, self.spin_desejos)
        layout_metas.addRow(lbl_riq, self.spin_riqueza)
        
        btn_salvar_metas = QPushButton("Salvar Metas")
        btn_salvar_metas.setFixedWidth(150)
        btn_salvar_metas.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_salvar_metas.setStyleSheet("background-color: #89b4fa; color: #11111b; font-weight: bold; padding: 8px; border-radius: 4px;")
        btn_salvar_metas.clicked.connect(self.salvar_metas)
        layout_metas.addWidget(btn_salvar_metas)
        
        secao_metas = SecaoExpansivel("Metas do Orçamento", "Personalize a regra 50/30/20. O total deve somar 100%.", layout_metas)
        layout.addWidget(secao_metas)

        # --- SEÇÃO: Zona de Perigo ---
        layout_perigo = QVBoxLayout()
        btn_zerar_banco = QPushButton("Apagar Todos os Dados")
        btn_zerar_banco.setFixedWidth(200)
        btn_zerar_banco.setStyleSheet("background-color: transparent; border: 1px solid #f38ba8; color: #f38ba8; font-weight: bold; padding: 8px; border-radius: 4px;")
        btn_zerar_banco.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_zerar_banco.clicked.connect(self.zerar_banco_dados)
        layout_perigo.addWidget(btn_zerar_banco)
        
        secao_perigo = SecaoExpansivel("Zona de Perigo", "Atenção: Ações realizadas aqui não podem ser desfeitas.", layout_perigo)
        layout.addWidget(secao_perigo)
        
        layout.addStretch()

    def validar_regras_senha_ui(self, texto):
        import re
        verde = "color: #a6e3a1; font-size: 12px; margin-left: 5px; font-weight: bold;"
        vermelho = "color: #f38ba8; font-size: 12px; margin-left: 5px;"
        
        if len(texto) >= 8:
            self.lbl_req_tamanho.setText("✓ Mínimo de 8 caracteres")
            self.lbl_req_tamanho.setStyleSheet(verde)
        else:
            self.lbl_req_tamanho.setText("✗ Mínimo de 8 caracteres")
            self.lbl_req_tamanho.setStyleSheet(vermelho)
            
        if re.search(r"[A-Z]", texto):
            self.lbl_req_maiuscula.setText("✓ Pelo menos 1 letra maiúscula")
            self.lbl_req_maiuscula.setStyleSheet(verde)
        else:
            self.lbl_req_maiuscula.setText("✗ Pelo menos 1 letra maiúscula")
            self.lbl_req_maiuscula.setStyleSheet(vermelho)
            
        if re.search(r"\d", texto):
            self.lbl_req_numero.setText("✓ Pelo menos 1 número")
            self.lbl_req_numero.setStyleSheet(verde)
        else:
            self.lbl_req_numero.setText("✗ Pelo menos 1 número")
            self.lbl_req_numero.setStyleSheet(vermelho)
            
        if re.search(r"[!@#$%^&*()_+=\-{}\[\]:;\"'<>,.?/\\|]", texto):
            self.lbl_req_especial.setText("✓ Pelo menos 1 caractere especial")
            self.lbl_req_especial.setStyleSheet(verde)
        else:
            self.lbl_req_especial.setText("✗ Pelo menos 1 caractere especial")
            self.lbl_req_especial.setStyleSheet(vermelho)

    def salvar_perfil(self):
        nome = self.input_nome.text().strip()
        email = self.input_email.text().strip()
        senha = self.input_senha.text().strip()
        senha_confirma = self.input_senha_confirma.text().strip()
        
        from security_manager import SecurityManager
        
        if senha or senha_confirma:
            if senha != senha_confirma:
                QMessageBox.warning(self, "Aviso", "As senhas não coincidem.")
                return
            valida, msg = SecurityManager.validar_senha(senha)
            if not valida:
                QMessageBox.warning(self, "Aviso", msg)
                return
        
        if nome:
            self.db.executar_query("INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?, ?)", ("perfil_nome", nome))
        if email:
            self.db.executar_query("INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?, ?)", ("perfil_email", email))
            
        msg = "Perfil atualizado com sucesso!"
        if senha:
            msg += "\\n(A senha foi alterada com sucesso.)"
            sm = SecurityManager()
            sm.configurar_senha(senha)
            self.senha_mestra = senha # Atualiza a referência local
            if hasattr(self.parent(), 'senha_mestra'):
                self.parent().senha_mestra = senha
            self.input_senha.clear()
            self.input_senha_confirma.clear()
            
        QMessageBox.information(self, "Perfil", msg)

    def atualizar_token_api(self):
        novo_token = self.input_token.text().strip()
        if novo_token:
            self.api.token_brapi = novo_token
            QMessageBox.information(self, "Sucesso", "Token atualizado com sucesso!\\nAs próximas consultas já usarão esta chave.")
        else:
            QMessageBox.warning(self, "Aviso", "O token não pode ficar vazio.")

    def salvar_metas(self):
        nec = self.spin_necessidades.value()
        des = self.spin_desejos.value()
        riq = self.spin_riqueza.value()
        
        if (nec + des + riq) != 100:
            QMessageBox.warning(self, "Aviso", "A soma das metas deve ser exatamente 100%.")
            return
            
        self.db.executar_query("INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?, ?)", ("meta_necessidades", str(nec)))
        self.db.executar_query("INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?, ?)", ("meta_desejos", str(des)))
        self.db.executar_query("INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?, ?)", ("meta_riqueza", str(riq)))
        
        QMessageBox.information(self, "Sucesso", "Metas de orçamento atualizadas com sucesso!")

    def exportar_dados_excel(self):
        caminho, _ = QFileDialog.getSaveFileName(
            self, 
            "Salvar Backup", 
            "Backup_DevenWealth.xlsx", 
            "Arquivos Excel (*.xlsx);;Todos os Arquivos (*)"
        )
        
        if not caminho:
            return
            
        query_carteira = """
            SELECT 
                c.ticker_id as Ativo,
                a.classe as Classe,
                a.setor as Setor,
                c.quantidade_total as Quantidade,
                c.preco_medio as Preco_Medio,
                cm.preco_atual as Preco_Atual,
                (c.quantidade_total * c.preco_medio) as Total_Investido,
                (c.quantidade_total * cm.preco_atual) as Saldo_Atual
            FROM carteira_atual c
            JOIN ativos_catalogo a ON c.ticker_id = a.ticker
            JOIN cache_mercado cm ON c.ticker_id = cm.ticker_id
        """
        
        query_financas = """
            SELECT 
                t.data as Data,
                t.descricao as Descricao,
                t.valor as Valor,
                c.nome as Categoria,
                c.tipo as Tipo,
                c.grupo_regra as Grupo
            FROM transacoes t
            LEFT JOIN categorias c ON t.categoria_id = c.id
            ORDER BY t.data DESC
        """
        
        query_rendimentos = """
            SELECT 
                r.data_pagamento as Data,
                r.ticker_id as Ativo,
                a.classe as Classe,
                r.tipo_provento as Tipo_Provento,
                r.qtd_cotas_base as Cotas_Base,
                r.valor_liquido_total as Valor_Liquido
            FROM rendimentos r
            LEFT JOIN ativos_catalogo a ON r.ticker_id = a.ticker
            ORDER BY r.data_pagamento DESC
        """
        
        try:
            conexao = self.db.conectar()
            df_carteira = pd.read_sql_query(query_carteira, conexao)
            df_financas = pd.read_sql_query(query_financas, conexao)
            df_rendimentos = pd.read_sql_query(query_rendimentos, conexao)
            conexao.close()
            
            with pd.ExcelWriter(caminho) as writer:
                df_carteira.to_excel(writer, sheet_name='Minha Carteira', index=False)
                df_financas.to_excel(writer, sheet_name='Contas Pessoais', index=False)
                df_rendimentos.to_excel(writer, sheet_name='Renda Passiva', index=False)
                
            QMessageBox.information(self, "Sucesso", "Relatório Excel exportado com sucesso em 3 abas!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao exportar: {str(e)}")

    def exportar_db_seguro(self):
        caminho, _ = QFileDialog.getSaveFileName(self, "Exportar Banco de Dados", "DevenWealth_Backup.dwb", "Deven Wealth Backup (*.dwb)")
        if not caminho: return
        
        from security_manager import SecurityManager
        import os
        from cryptography.fernet import Fernet
        
        try:
            with open(SecurityManager.DB_PATH, 'rb') as f:
                dados = f.read()
                
            salt = os.urandom(16)
            chave = SecurityManager._derivar_chave(self.senha_mestra, salt)
            f_fernet = Fernet(chave)
            dados_criptografados = f_fernet.encrypt(dados)
            
            with open(caminho, 'wb') as f_enc:
                f_enc.write(salt + dados_criptografados)
                
            QMessageBox.information(self, "Sucesso", "Banco de dados exportado e criptografado com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha na exportação: {e}")

    def importar_db_seguro(self):
        caminho, _ = QFileDialog.getOpenFileName(self, "Importar Banco de Dados", "", "Deven Wealth Backup (*.dwb);;Todos os Arquivos (*)")
        if not caminho: return
        
        from PyQt6.QtWidgets import QInputDialog
        senha_backup, ok = QInputDialog.getText(self, "Senha do Backup", "Digite a senha usada neste backup:", QLineEdit.EchoMode.Password)
        if not ok or not senha_backup: return
        
        from security_manager import SecurityManager
        import os
        from cryptography.fernet import Fernet, InvalidToken
        import sys
        
        try:
            with open(caminho, 'rb') as f_enc:
                conteudo = f_enc.read()
                
            salt = conteudo[:16]
            dados_criptografados = conteudo[16:]
            
            chave = SecurityManager._derivar_chave(senha_backup, salt)
            f_fernet = Fernet(chave)
            
            dados_descriptografados = f_fernet.decrypt(dados_criptografados)
            
            # Escreve por cima do banco atual
            with open(SecurityManager.DB_PATH, 'wb') as f_db:
                f_db.write(dados_descriptografados)
                
            QMessageBox.information(self, "Importação Concluída", "Banco de dados restaurado com sucesso!\\nO aplicativo será encerrado para aplicar as mudanças.")
            sys.exit(0)
            
        except InvalidToken:
            QMessageBox.critical(self, "Erro", "Senha incorreta ou arquivo de backup corrompido.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha na importação: {e}")

    def zerar_banco_dados(self):
        resposta = QMessageBox.warning(
            self, "ATENÇÃO MÁXIMA", 
            "Isso apagará TODO o seu histórico de investimentos e finanças pessoais.\\nEsta ação é irreversível. Deseja continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if resposta == QMessageBox.StandardButton.Yes:
            self.db.executar_query("DELETE FROM transacoes")
            self.db.executar_query("DELETE FROM categorias")
            self.db.executar_query("DELETE FROM carteira_atual")
            self.db.executar_query("DELETE FROM cache_mercado")
            self.db.executar_query("DELETE FROM ativos_catalogo")
            
            if self.fn_reset_db:
                self.fn_reset_db()
            
            QMessageBox.information(self, "Zerar Banco", "O sistema foi resetado para os padrões de fábrica.")
