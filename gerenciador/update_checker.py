import requests
from packaging.version import parse
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextBrowser, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QDesktopServices
import qtawesome as qta

VERSAO_ATUAL = "0.2.0"
REPO_GITHUB = "LunyErlon/deven_wealth"
URL_RELEASES_API = f"https://api.github.com/repos/{REPO_GITHUB}/releases/latest"


class WorkerVerificadorUpdates(QThread):
    """
    Worker assíncrono para checagem silenciosa de novas versões no GitHub Releases.
    Não bloqueia a inicialização do app e tem tolerância a falhas (offline-first).
    """
    nova_versao_detectada = pyqtSignal(dict)
    verificacao_finalizada = pyqtSignal(bool, str) # (tem_nova_versao, mensagem)

    def __init__(self, versao_atual=VERSAO_ATUAL, parent=None):
        super().__init__(parent)
        self.versao_atual = versao_atual.lstrip("v")

    def run(self):
        try:
            headers = {
                "User-Agent": f"DevenWealth-App/{self.versao_atual}",
                "Accept": "application/vnd.github+json"
            }
            resposta = requests.get(URL_RELEASES_API, headers=headers, timeout=3.0)

            if resposta.status_code == 200:
                dados = resposta.json()
                tag_remota = dados.get("tag_name", "").lstrip("v").strip()
                
                if tag_remota:
                    try:
                        eh_mais_recente = parse(tag_remota) > parse(self.versao_atual)
                    except Exception:
                        eh_mais_recente = tag_remota != self.versao_atual

                    if eh_mais_recente:
                        info_update = {
                            "versao": tag_remota,
                            "versao_atual": self.versao_atual,
                            "titulo": dados.get("name") or f"Deven Wealth v{tag_remota}",
                            "notas": dados.get("body") or "Melhorias de desempenho, correções de bugs e novas funcionalidades.",
                            "url_download": dados.get("html_url") or f"https://github.com/{REPO_GITHUB}/releases"
                        }
                        self.nova_versao_detectada.emit(info_update)
                        self.verificacao_finalizada.emit(True, f"Nova versão v{tag_remota} disponível!")
                        return
                    else:
                        self.verificacao_finalizada.emit(False, f"O Deven Wealth já está atualizado na versão mais recente (v{self.versao_atual}).")
                        return
            elif resposta.status_code == 404:
                # Nenhuma release publicada ainda
                self.verificacao_finalizada.emit(False, f"Nenhuma atualização encontrada. Você está na versão v{self.versao_atual}.")
                return
            else:
                self.verificacao_finalizada.emit(False, f"Não foi possível verificar no momento (Código {resposta.status_code}).")
                return

        except Exception as e:
            # Em modo offline ou sem conexão, encerra silenciosamente
            self.verificacao_finalizada.emit(False, "Modo offline ou sem conexão à internet.")


class DialogAtualizacao(QDialog):
    """
    Pop-up elegante para exibir o Changelog / Notas de Atualização
    com botão de download direto para o repositório do GitHub.
    """
    def __init__(self, dados_update, parent=None):
        super().__init__(parent)
        self.dados_update = dados_update
        self.setWindowTitle("Nova Versão Disponível - Deven Wealth")
        self.resize(600, 480)
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QTextBrowser {
                background-color: #181825;
                color: #cdd6f4;
                border: 1px solid #313244;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # 1. Cartão de Destaque Superior
        frame_cabecalho = QFrame()
        frame_cabecalho.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #313244, stop:1 #262939);
                border: 1px solid #45475a;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        layout_cabecalho = QVBoxLayout(frame_cabecalho)
        layout_cabecalho.setSpacing(6)

        lbl_icone_titulo = QLabel(f"🚀 {self.dados_update.get('titulo', 'Nova Atualização!')}")
        lbl_icone_titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #fab387;")
        layout_cabecalho.addWidget(lbl_icone_titulo)

        versao_antiga = self.dados_update.get('versao_atual', VERSAO_ATUAL)
        versao_nova = self.dados_update.get('versao', 'Nova')
        
        lbl_comparativo = QLabel(f"Sua versão atual: <b>v{versao_antiga}</b> ➔ Disponível para atualização: <span style='color: #a6e3a1; font-weight: bold;'>v{versao_nova}</span>")
        lbl_comparativo.setStyleSheet("font-size: 13px; color: #cdd6f4;")
        layout_cabecalho.addWidget(lbl_comparativo)

        layout.addWidget(frame_cabecalho)

        # 2. Changelog / O que há de novo
        lbl_notas_titulo = QLabel("📋 O que mudou nesta versão (Changelog):")
        lbl_notas_titulo.setStyleSheet("font-weight: bold; color: #89b4fa; font-size: 13px;")
        layout.addWidget(lbl_notas_titulo)

        self.txt_notas = QTextBrowser()
        self.txt_notas.setOpenExternalLinks(True)
        # Markdown simples para HTML amigável
        notas_texto = self.dados_update.get('notas', 'Melhorias de desempenho e novidades.')
        notas_formatadas = notas_texto.replace("\n", "<br>")
        self.txt_notas.setHtml(f"<div style='font-family: sans-serif;'>{notas_formatadas}</div>")
        layout.addWidget(self.txt_notas)

        # 3. Aviso sobre os dados locais
        lbl_aviso_banco = QLabel("🔒 <b>Seus dados estão 100% seguros:</b> Atualizar o software não apaga seu cofre ou histórico financeiro.")
        lbl_aviso_banco.setStyleSheet("color: #a6adc8; font-size: 11px;")
        layout.addWidget(lbl_aviso_banco)

        # 4. Rodapé de Ações
        layout_rodape = QHBoxLayout()

        btn_baixar = QPushButton("🌐 Baixar Atualização no GitHub")
        btn_baixar.setStyleSheet("""
            QPushButton {
                background-color: #a6e3a1;
                color: #11111b;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #94e2d5;
            }
        """)
        btn_baixar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_baixar.clicked.connect(self.abrir_link_download)

        btn_lembrar = QPushButton("Lembrar Mais Tarde")
        btn_lembrar.setStyleSheet("""
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                font-weight: bold;
                padding: 10px 18px;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #45475a;
            }
        """)
        btn_lembrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_lembrar.clicked.connect(self.reject)

        layout_rodape.addStretch()
        layout_rodape.addWidget(btn_lembrar)
        layout_rodape.addWidget(btn_baixar)

        layout.addLayout(layout_rodape)

    def abrir_link_download(self):
        url = self.dados_update.get('url_download', f"https://github.com/{REPO_GITHUB}/releases")
        QDesktopServices.openUrl(QUrl(url))
        self.accept()
