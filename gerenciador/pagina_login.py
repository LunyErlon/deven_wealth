from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QMessageBox, QStackedWidget,
                             QApplication)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
import requests

from security_manager import SecurityManager
from componentes import PasswordInput

class LoginWindow(QWidget):
    def __init__(self, fn_login_sucesso):
        super().__init__()
        self.fn_login_sucesso = fn_login_sucesso
        self.setWindowTitle("Deven Wealth - Segurança")
        self.resize(500, 600)
        self.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")
        self.setup_ui()

    def setup_ui(self):
        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Logo
        lbl_logo = QLabel("Deven Wealth")
        lbl_logo.setStyleSheet("font-size: 32px; font-weight: bold; color: #cdd6f4; margin-bottom: 20px;")
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout_principal.addWidget(lbl_logo)

        self.stack = QStackedWidget()
        self.layout_principal.addWidget(self.stack)

        self.setup_tela_login()
        self.setup_tela_registro()

        if SecurityManager.banco_esta_criptografado():
            self.stack.setCurrentIndex(0) # Login
        else:
            self.stack.setCurrentIndex(1) # Registro

    def setup_tela_login(self):
        tela = QWidget()
        layout = QVBoxLayout(tela)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        lbl_titulo = QLabel("Acessar sua Carteira")
        lbl_titulo.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.input_senha_login = PasswordInput("Sua Senha-Mestra")
        self.input_senha_login.setStyleSheet("background-color: #313244; padding: 15px; padding-right: 40px; border-radius: 8px; font-size: 16px;")

        btn_entrar = QPushButton("Desbloquear Cofre")
        btn_entrar.setStyleSheet("background-color: #a6e3a1; color: #11111b; font-weight: bold; padding: 15px; border-radius: 8px; font-size: 16px; margin-top: 20px;")
        btn_entrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_entrar.clicked.connect(self.tentar_login)

        layout.addWidget(lbl_titulo)
        layout.addWidget(self.input_senha_login)
        layout.addWidget(btn_entrar)
        self.stack.addWidget(tela) # Index 0

    def setup_tela_registro(self):
        tela = QWidget()
        layout = QVBoxLayout(tela)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        lbl_titulo = QLabel("Bem-vindo! Crie seu cofre local.")
        lbl_titulo.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Nome
        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText("Seu Nome")
        self.input_nome.setStyleSheet("background-color: #313244; padding: 12px; border-radius: 8px; font-size: 14px; margin-bottom: 10px;")

        # Senha Mestra
        self.input_senha_reg = PasswordInput("Crie uma Senha-Mestra Forte")
        self.input_senha_reg.setStyleSheet("background-color: #313244; padding: 12px; padding-right: 40px; border-radius: 8px; font-size: 14px; margin-bottom: 5px;")

        # Confirmação da Senha Mestra
        self.input_senha_reg_confirma = PasswordInput("Confirme a Senha-Mestra")
        self.input_senha_reg_confirma.setStyleSheet("background-color: #313244; padding: 12px; padding-right: 40px; border-radius: 8px; font-size: 14px; margin-bottom: 10px;")

        # Token Brapi
        self.input_token = QLineEdit()
        self.input_token.setPlaceholderText("Token da Brapi API")
        self.input_token.setStyleSheet("background-color: #313244; padding: 12px; border-radius: 8px; font-size: 14px; margin-bottom: 5px;")

        # Link Brapi
        btn_link_brapi = QPushButton("Não tem token? Crie uma conta grátis na Brapi")
        btn_link_brapi.setStyleSheet("color: #89b4fa; text-align: left; background: transparent; text-decoration: underline;")
        btn_link_brapi.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_link_brapi.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://brapi.dev")))

        btn_criar = QPushButton("Concluir Cadastro e Criptografar")
        btn_criar.setStyleSheet("background-color: #89b4fa; color: #11111b; font-weight: bold; padding: 15px; border-radius: 8px; font-size: 16px; margin-top: 20px;")
        btn_criar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_criar.clicked.connect(self.registrar_usuario)

        layout.addWidget(lbl_titulo)
        layout.addWidget(self.input_nome)
        layout.addWidget(self.input_senha_reg)
        layout.addWidget(self.input_senha_reg_confirma)
        layout.addWidget(self.input_token)
        layout.addWidget(btn_link_brapi)
        layout.addWidget(btn_criar)
        self.stack.addWidget(tela) # Index 1

    def tentar_login(self):
        senha = self.input_senha_login.text()
        if not senha:
            QMessageBox.warning(self, "Aviso", "Digite sua senha.")
            return

        if SecurityManager.descriptografar_banco(senha):
            self.fn_login_sucesso(senha, None)
        else:
            QMessageBox.critical(self, "Erro", "Senha incorreta ou banco corrompido.")

    def registrar_usuario(self):
        nome = self.input_nome.text().strip()
        senha = self.input_senha_reg.text()
        senha_confirma = self.input_senha_reg_confirma.text()
        token = self.input_token.text().strip()

        if not nome or not senha or not token:
            QMessageBox.warning(self, "Aviso", "Preencha todos os campos obrigatórios.")
            return
            
        if senha != senha_confirma:
            QMessageBox.warning(self, "Aviso", "As senhas não coincidem.")
            return
            
        valida, msg = SecurityManager.validar_senha(senha)
        if not valida:
            QMessageBox.warning(self, "Aviso", msg)
            return

        # Valida token Brapi
        try:
            resp = requests.get(f"https://brapi.dev/api/quote/PETR4?token={token}")
            if resp.status_code != 200:
                QMessageBox.critical(self, "Erro na Brapi", "O Token fornecido é inválido ou expirou.")
                return
        except Exception:
            QMessageBox.critical(self, "Erro", "Falha ao conectar com a Brapi para validar o token.")
            return

        # Tudo certo, cria o banco criptografado
        SecurityManager.criar_banco_seguro(senha)
        
        # Descriptografa pra abrir e passar o controle
        SecurityManager.descriptografar_banco(senha)
        self.fn_login_sucesso(senha, token)
