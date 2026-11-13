import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QStackedWidget
from PyQt6.QtCore import Qt

from market_api import MarketAPI 
from db_manager import DBManager

from pagina_resumo import PaginaResumo
from pagina_carteira import PaginaCarteira
from pagina_analise import PaginaAnalise
from pagina_financas import PaginaFinancas
from pagina_rendimentos import PaginaRendimentos
from pagina_config import PaginaConfig
from pagina_login import LoginWindow
from security_manager import SecurityManager
from update_checker import WorkerVerificadorUpdates, DialogAtualizacao, VERSAO_ATUAL
import os

def obter_diretorio_base():
    """
    Retorna o diretório base correto para localização de assets e recursos,
    funcionando perfeitamente tanto em modo script quanto empacotado em executável (.exe) via PyInstaller.
    """
    if getattr(sys, 'frozen', False):
        base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        if not os.path.exists(os.path.join(base, "assets")) and os.path.exists(os.path.join(base, "gerenciador", "assets")):
            base = os.path.join(base, "gerenciador")
        return base
    return os.path.dirname(os.path.abspath(__file__))

class DevenWealthWindow(QMainWindow):
    def __init__(self, senha_mestra, token_brapi=None, nome_usuario=None):
        super().__init__()
        self.senha_mestra = senha_mestra

        # INICIAMOS O MOTOR
        self.api = MarketAPI(token_brapi="")
        self.db = DBManager()
        self.inicializar_banco_dados()
        
        # Gerenciamento de Nome de Usuário (Perfil)
        if nome_usuario:
            self.db.executar_query("INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?, ?)", ("perfil_nome", nome_usuario))

        # Gerenciamento de Token
        if token_brapi:
            self.db.executar_query("INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?, ?)", ("token_brapi", token_brapi))
            self.api.token_brapi = token_brapi
        else:
            res_token = self.db.buscar_dados("SELECT valor FROM configuracoes WHERE chave='token_brapi'")
            if res_token and res_token[0]['valor']:
                self.api.token_brapi = res_token[0]['valor']
        
        # Configurações da Janela Principal
        self.setWindowTitle(f"Deven Wealth - Dashboard v{VERSAO_ATUAL}")
        self.resize(1100, 700)
        
        # O Widget Central
        self.widget_central = QWidget()
        self.setCentralWidget(self.widget_central)
        
        self.layout_principal = QHBoxLayout(self.widget_central)
        self.layout_principal.setContentsMargins(0, 0, 0, 0)
        self.layout_principal.setSpacing(0)
        
        # ==========================================
        # BARRA LATERAL (MENU ESQUERDO)
        # ==========================================
        self.menu_lateral = QFrame()
        self.menu_lateral.setObjectName("menuLateral")
        self.menu_lateral.setMinimumWidth(280)
        self.menu_lateral.setMaximumWidth(350)
        
        self.layout_menu = QVBoxLayout(self.menu_lateral)
        self.layout_menu.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout_menu.setSpacing(15)
        self.layout_menu.setContentsMargins(20, 30, 20, 20)
        
        # Container for Principal Logo and Title
        self.container_logo_principal = QWidget()
        self.layout_logo_principal = QHBoxLayout(self.container_logo_principal)
        self.layout_logo_principal.setContentsMargins(0, 0, 0, 0)
        self.layout_logo_principal.setSpacing(10)
        self.layout_logo_principal.setAlignment(Qt.AlignmentFlag.AlignCenter)

        from PyQt6.QtGui import QPixmap
        base_dir = obter_diretorio_base()

        self.icon_principal = QLabel()
        path_principal = os.path.join(base_dir, "assets", "Logo_Principal.png")
        pixmap_principal = QPixmap(path_principal).scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.icon_principal.setPixmap(pixmap_principal)
        
        self.logo = QLabel("Deven Wealth")
        self.logo.setObjectName("logo")
        self.logo.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        self.layout_logo_principal.addWidget(self.icon_principal)
        self.layout_logo_principal.addWidget(self.logo)
        
        self.layout_menu.addWidget(self.container_logo_principal)

        # DS SYSTEM B Logo below
        self.logo_ds = QLabel()
        self.logo_ds.setAlignment(Qt.AlignmentFlag.AlignCenter)
        path_ds = os.path.join(base_dir, "assets", "Logo_DS_SYSTEM_B.png")
        pixmap_ds = QPixmap(path_ds).scaled(150, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.logo_ds.setPixmap(pixmap_ds)
        self.layout_menu.addWidget(self.logo_ds)
        
        self.layout_menu.addSpacing(30)
        
        self.btn_resumo = QPushButton(" Visão Geral")
        self.btn_carteira = QPushButton(" Minha Carteira")
        self.btn_analise = QPushButton(" Análise de Mercado")
        self.btn_rendimentos = QPushButton(" Rendimentos")
        self.btn_financas = QPushButton(" Contas Pessoais")
        self.btn_config = QPushButton(" Configurações")
        
        self.layout_menu.addWidget(self.btn_resumo)
        self.layout_menu.addWidget(self.btn_carteira)
        self.layout_menu.addWidget(self.btn_analise)
        self.layout_menu.addWidget(self.btn_rendimentos)
        self.layout_menu.addWidget(self.btn_financas)
        self.layout_menu.addStretch()
        self.layout_menu.addWidget(self.btn_config)
        
        # ==========================================
        # ÁREA CENTRAL (Telas Múltiplas)
        # ==========================================
        self.area_conteudo = QFrame()
        self.area_conteudo.setObjectName("areaConteudo")
        self.layout_conteudo = QVBoxLayout(self.area_conteudo)
        
        self.stack = QStackedWidget()
        self.layout_conteudo.addWidget(self.stack)
        
        # Instanciando as páginas dos arquivos separados
        self.pagina_resumo = PaginaResumo(self.db)
        self.pagina_carteira = PaginaCarteira(self.db, fn_atualizar_resumo=self.pagina_resumo.carregar_dados)
        self.pagina_analise = PaginaAnalise(self.db, self.api, fn_atualizar_carteira=self.pagina_carteira.carregar_dados)
        self.pagina_rendimentos = PaginaRendimentos(self.db, api=self.api, fn_atualizar_resumo=self.pagina_resumo.carregar_dados)
        self.pagina_financas = PaginaFinancas(self.db)
        self.pagina_config = PaginaConfig(self.db, self.api, fn_reset_db=self.reset_banco_dados, senha_mestra=self.senha_mestra)
        
        self.stack.addWidget(self.pagina_resumo)    # Índice 0
        self.stack.addWidget(self.pagina_carteira)  # Índice 1
        self.stack.addWidget(self.pagina_analise)   # Índice 2
        self.stack.addWidget(self.pagina_rendimentos) # Índice 3
        self.stack.addWidget(self.pagina_financas)  # Índice 4
        self.stack.addWidget(self.pagina_config)    # Índice 5
        
        # Ações dos botões do menu
        self.btn_resumo.clicked.connect(self.abrir_tela_resumo)
        self.btn_carteira.clicked.connect(self.abrir_tela_carteira)
        self.btn_analise.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.btn_rendimentos.clicked.connect(self.abrir_tela_rendimentos)
        self.btn_financas.clicked.connect(self.abrir_tela_financas)
        self.btn_config.clicked.connect(lambda: self.stack.setCurrentIndex(5))
        
        # Pílula de Atualização Disponível (UI/UX Opção A)
        self.btn_update = QPushButton("🚀 Nova Versão Disponível!")
        self.btn_update.setObjectName("btnUpdateDisponivel")
        self.btn_update.setStyleSheet("""
            QPushButton#btnUpdateDisponivel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #fab387, stop:1 #f9e2af);
                color: #11111b;
                font-weight: bold;
                font-size: 11px;
                padding: 8px 10px;
                border-radius: 6px;
                border: none;
                margin-top: 10px;
            }
            QPushButton#btnUpdateDisponivel:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #f9e2af, stop:1 #fab387);
            }
        """)
        self.btn_update.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_update.hide()
        self.btn_update.clicked.connect(self.abrir_dialogo_update)
        self.layout_menu.addWidget(self.btn_update)
        self.dados_update_disponivel = None

        # Rodapé no menu lateral
        self.layout_menu.addSpacing(10)
        self.rodape = QLabel(f"Deven Wealth v{VERSAO_ATUAL} • DEVEN")
        self.rodape.setObjectName("rodape")
        self.rodape.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rodape.setFixedHeight(25)
        self.layout_menu.addWidget(self.rodape)

        self.layout_principal.addWidget(self.menu_lateral)
        self.layout_principal.addWidget(self.area_conteudo)
        
        self.layout_principal.setStretchFactor(self.menu_lateral, 1)
        self.layout_principal.setStretchFactor(self.area_conteudo, 4)
        
        self.stack.currentChanged.connect(self.atualizar_menu)
        self.aplicar_estilos()
        self.abrir_tela_resumo() # Carrega inicial
        self.atualizar_menu(0)

        # Agendamento suave do Assistente de Início (Contas Recorrentes)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(400, self.verificar_contas_recorrentes)

        # Agendamento suave do Radar de Dividendos em segundo plano (QThread)
        QTimer.singleShot(1200, self.iniciar_radar_dividendos_background)

        # Agendamento suave da checagem de atualizações no GitHub (QThread)
        QTimer.singleShot(2500, self.iniciar_verificacao_updates)

    def atualizar_menu(self, index):
        import qtawesome as qta
        from PyQt6.QtCore import QSize
        botoes = [
            (self.btn_resumo, 'mdi.view-dashboard-outline'),
            (self.btn_carteira, 'mdi.wallet-outline'),
            (self.btn_analise, 'mdi.trending-up'),
            (self.btn_rendimentos, 'mdi.cash-multiple'),
            (self.btn_financas, 'mdi.book-open-outline'),
            (self.btn_config, 'mdi.cog-outline')
        ]
        for i, (btn, icon_name) in enumerate(botoes):
            if i == index:
                btn.setProperty("selecionado", True)
                btn.setIcon(qta.icon(icon_name, color='#D4AF37'))
            else:
                btn.setProperty("selecionado", False)
                btn.setIcon(qta.icon(icon_name, color='#6c6c6c'))
            btn.setIconSize(QSize(20, 20))
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def inicializar_banco_dados(self):
        """Garante que TODAS as tabelas do Deven Wealth existam no SQLite."""
        self.db.executar_query("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                tipo TEXT NOT NULL
            )
        """)
        
        # Migração: Adiciona a nova coluna se não existir
        cols = self.db.buscar_dados("PRAGMA table_info(categorias)")
        col_names = [col['name'] for col in cols] if cols else []
        if 'grupo_regra' not in col_names:
            self.db.executar_query("ALTER TABLE categorias ADD COLUMN grupo_regra TEXT DEFAULT 'Sem Grupo'")

        self.db.executar_query("""
            CREATE TABLE IF NOT EXISTS transacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                descricao TEXT NOT NULL,
                valor REAL NOT NULL,
                categoria_id INTEGER,
                origem TEXT,
                recorrente INTEGER DEFAULT 0,
                FOREIGN KEY(categoria_id) REFERENCES categorias(id)
            )
        """)

        # Migração: Adiciona a coluna recorrente na tabela transacoes se não existir
        cols_trans = self.db.buscar_dados("PRAGMA table_info(transacoes)")
        col_names_trans = [col['name'] for col in cols_trans] if cols_trans else []
        if 'recorrente' not in col_names_trans:
            self.db.executar_query("ALTER TABLE transacoes ADD COLUMN recorrente INTEGER DEFAULT 0")
        self.db.executar_query("""
            CREATE TABLE IF NOT EXISTS ativos_catalogo (
                ticker TEXT PRIMARY KEY,
                classe TEXT,
                setor TEXT
            )
        """)
        
        cols_cat = self.db.buscar_dados("PRAGMA table_info(ativos_catalogo)")
        col_names_cat = [col['name'] for col in cols_cat] if cols_cat else []
        if 'preco_teto' not in col_names_cat:
            self.db.executar_query("ALTER TABLE ativos_catalogo ADD COLUMN preco_teto REAL DEFAULT 0.0")
        self.db.executar_query("""
            CREATE TABLE IF NOT EXISTS cache_mercado (
                ticker_id TEXT PRIMARY KEY,
                ultima_atualizacao TEXT,
                preco_atual REAL,
                dy_atual REAL,
                p_vp REAL,
                p_l REAL,
                FOREIGN KEY(ticker_id) REFERENCES ativos_catalogo(ticker)
            )
        """)
        self.db.executar_query("""
            CREATE TABLE IF NOT EXISTS carteira_atual (
                ticker_id TEXT PRIMARY KEY,
                quantidade_total REAL,
                preco_medio REAL,
                FOREIGN KEY(ticker_id) REFERENCES ativos_catalogo(ticker)
            )
        """)
        self.db.executar_query("""
            CREATE TABLE IF NOT EXISTS rendimentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker_id TEXT NOT NULL,
                data_pagamento TEXT NOT NULL,
                tipo_provento TEXT NOT NULL,
                qtd_cotas_base REAL NOT NULL,
                valor_liquido_total REAL NOT NULL,
                FOREIGN KEY(ticker_id) REFERENCES ativos_catalogo(ticker)
            )
        """)
        self.db.executar_query("""
            CREATE TABLE IF NOT EXISTS configuracoes (
                chave TEXT PRIMARY KEY,
                valor TEXT
            )
        """)
        
        # Popula os catálogos inteligentes se estiverem vazios
        try:
            cats = self.db.buscar_dados("SELECT COUNT(id) as total FROM categorias")
            if not cats or cats[0]['total'] == 0:
                padroes = [
                    ("Salário", "Receita", "Receita"), ("Freelas", "Receita", "Receita"), ("Outros", "Receita", "Receita"),
                    ("Mercado Básico", "Despesa", "Necessidades"), 
                    ("Moradia (Aluguel/Condomínio)", "Despesa", "Necessidades"),
                    ("Contas Fixas (Água/Luz/Internet)", "Despesa", "Necessidades"),
                    ("Saúde (Plano/Farmácia)", "Despesa", "Necessidades"),
                    ("Transporte", "Despesa", "Necessidades"),
                    ("Restaurantes e Delivery", "Despesa", "Desejos"),
                    ("Assinaturas (Streaming/Jogos)", "Despesa", "Desejos"),
                    ("Lazer e Passeios", "Despesa", "Desejos"),
                    ("Compras Pessoais (Roupas/Mimos)", "Despesa", "Desejos"),
                    ("Aportes em Investimentos", "Despesa", "Construção de Riqueza"),
                    ("Reserva de Emergência", "Despesa", "Construção de Riqueza")
                ]
                for nome, tipo, grupo in padroes:
                    self.db.executar_query("INSERT INTO categorias (nome, tipo, grupo_regra) VALUES (?, ?, ?)", (nome, tipo, grupo))
        except Exception as e:
            pass

    def reset_banco_dados(self):
        self.inicializar_banco_dados()
        self.pagina_resumo.carregar_dados()
        self.pagina_carteira.carregar_dados()
        self.pagina_rendimentos.carregar_dados()
        self.pagina_financas.carregar_dados()
        self.abrir_tela_resumo()

    def abrir_tela_resumo(self):
        self.pagina_resumo.carregar_dados()
        self.stack.setCurrentIndex(0)

    def abrir_tela_carteira(self):
        self.pagina_carteira.carregar_dados()
        self.stack.setCurrentIndex(1)

    def abrir_tela_rendimentos(self):
        self.pagina_rendimentos.carregar_dados()
        self.stack.setCurrentIndex(3)

    def abrir_tela_financas(self):
        self.pagina_financas.carregar_dados()
        self.stack.setCurrentIndex(4)

    def aplicar_estilos(self):
        estilo_qss = """
        QWidget {
            font-family: "Consolas", "Courier New", monospace;
        }

        QMainWindow, QDialog {         
            background-color: #1e1e2e;        
        }

        QDialog {
            color: #cdd6f4;
            font-size: 14px;
        }

        QDialog QLabel {
            color: #cdd6f4;
            font-size: 14px;
        }

        #menuLateral { 
            background-color: #050505; 
            border-right: 1px solid #313244;
        }
        
        #rodape {
            background-color: #050505;
            color: #D4AF37;
            font-size: 12px;
            font-weight: bold;
            border-top: 1px solid #313244;
        }

        #logo { 
            color: #D4AF37; 
            font-size: 24px; 
            font-weight: bold; 
            margin-bottom: 5px; 
            }
        
        QPushButton { 
            background-color: transparent; 
            color: #6c6c6c; 
            font-size: 16px; 
            font-weight: bold; 
            text-align: left; 
            padding: 12px 15px; 
            border: none; 
            border-bottom: 1px solid transparent;
            }
        
        QPushButton:hover { 
            background-color: #11111b; 
            color: #E2E2E2; 
            }
            
        QPushButton[selecionado="true"] {
            color: #D4AF37;
            border-bottom: 1px solid #D4AF37;
            }
        
        #areaConteudo { 
            background-color: #1e1e2e; 
            padding: 30px; 
            }
        
        #tituloPagina { 
            color: #cdd6f4; 
            font-size: 28px; 
            font-weight: bold; 
            }

        /* Estilos da Área de Busca */
        #inputBusca {
            padding: 12px; 
            font-size: 16px; 
            border-radius: 8px;
            background-color: #313244; 
            color: #cdd6f4; 
            border: 1px solid #45475a;
        }
        #btnBuscar {
            background-color: #a6e3a1; 
            color: #11111b; 
            font-size: 16px; 
            font-weight: bold;
            border-radius: 8px; 
            padding: 12px 20px; 
            text-align: center;
        }
        #btnBuscar:hover {
            background-color: #94e285;
        }
        #resultadoAnalise {
            color: #cdd6f4; 
            font-size: 18px; 
            margin-top: 20px;
        }

        #btnSalvar {
            background-color: #fab387; 
            color: #11111b; 
            font-size: 16px; 
            font-weight: bold;
            border-radius: 8px; 
            padding: 12px 20px; 
            text-align: center; 
            margin-top: 15px; 
            width: 250px;
        }
        #btnSalvar:hover {
            background-color: #f9e2af;
        }

        /* Estilos da Tabela */
        QTableWidget {
            background-color: #1e1e2e; 
            color: #cdd6f4;
            gridline-color: #313244; 
            border: 1px solid #313244;
            font-size: 14px; 
            border-radius: 8px;
        }
        QHeaderView::section {
            background-color: #181825;
            color: #bac2de;
            padding: 10px; 
            border: 1px solid #313244;
            font-size: 14px; 
            font-weight: bold;
        }
        QTableWidget::item { padding: 5px; }

        /* Estilo unificado para arrumar o cursor e os botões dos SpinBoxes (Máquina do tempo, etc) */
        QAbstractSpinBox {
            padding: 5px;
            padding-right: 25px; /* Libera espaço para que as setas não fiquem debaixo do texto */
            background-color: #313244; 
            color: #cdd6f4;
            border-radius: 4px;
            border: 1px solid #45475a;
        }
        
        QAbstractSpinBox::up-button {
            subcontrol-origin: border;
            subcontrol-position: top right;
            width: 20px;
            background-color: #1e1e2e;
            border-left: 1px solid #45475a;
            border-top-right-radius: 4px;
        }
        
        QAbstractSpinBox::down-button {
            subcontrol-origin: border;
            subcontrol-position: bottom right;
            width: 20px;
            background-color: #1e1e2e;
            border-left: 1px solid #45475a;
            border-bottom-right-radius: 4px;
        }
        
        QAbstractSpinBox::up-button:hover, QAbstractSpinBox::down-button:hover {
            background-color: #45475a;
        }
        
        QAbstractSpinBox::up-arrow {
            image: url("assets/up_arrow.svg");
            width: 12px;
            height: 12px;
        }
        
        QAbstractSpinBox::down-arrow {
            image: url("assets/down_arrow.svg");
            width: 12px;
            height: 12px;
        }

        """
        base_dir = obter_diretorio_base().replace('\\', '/')
        estilo_qss = estilo_qss.replace('url("assets/', f'url("{base_dir}/assets/')
        
        app_inst = QApplication.instance()
        if app_inst:
            app_inst.setStyleSheet(estilo_qss)
        self.setStyleSheet(estilo_qss)

    def verificar_contas_recorrentes(self, silencioso_se_vazio=True):
        """
        Fase 3: Motor Detetive de Contas Recorrentes (Cross-Month).
        Verifica despesas com recorrente = 1 no mês passado e identifica se
        já foram lançadas no mês atual. Se houver pendências, abre o Pop-up de Boas-Vindas.
        """
        from PyQt6.QtCore import QDate
        from PyQt6.QtWidgets import QMessageBox, QDialog
        
        hoje = QDate.currentDate()
        mes_atual_str = hoje.toString("yyyy-MM")
        mes_passado_str = hoje.addMonths(-1).toString("yyyy-MM")
        
        # 1. Buscar transações marcadas como recorrentes no mês passado
        query_passado = """
            SELECT t.id, t.data, t.descricao, t.valor, t.categoria_id, c.nome as categoria, c.tipo, c.grupo_regra
            FROM transacoes t
            JOIN categorias c ON t.categoria_id = c.id
            WHERE t.recorrente = 1 AND t.data LIKE ?
            ORDER BY t.data ASC
        """
        recorrentes_passado = self.db.buscar_dados(query_passado, (f"{mes_passado_str}-%",))
        if not recorrentes_passado:
            if not silencioso_se_vazio:
                QMessageBox.information(
                    self,
                    "Contas Recorrentes",
                    f"Nenhuma conta marcada como recorrente no mês anterior ({mes_passado_str})."
                )
            return
            
        # 2. Filtrar apenas as contas que AINDA NÃO FORAM lançadas no mês atual
        contas_pendentes = []
        for rec in recorrentes_passado:
            desc_limpa = rec['descricao'].replace('🔁', '').strip()
            query_verif = """
                SELECT id FROM transacoes 
                WHERE data LIKE ? AND (
                    LOWER(TRIM(descricao)) = LOWER(TRIM(?))
                    OR LOWER(TRIM(descricao)) = LOWER(TRIM(?))
                )
            """
            ja_existe = self.db.buscar_dados(query_verif, (f"{mes_atual_str}-%", desc_limpa, f"🔁 {desc_limpa}"))
            if not ja_existe:
                contas_pendentes.append(rec)
                
        if not contas_pendentes:
            if not silencioso_se_vazio:
                QMessageBox.information(
                    self,
                    "Contas Recorrentes",
                    f"Todas as suas contas recorrentes já foram lançadas no mês atual ({mes_atual_str})!"
                )
            return
            
        # 3. Dispara o Pop-up de Boas-Vindas (Fase 4: Atrito Positivo & Loop Autolimpante)
        from pagina_financas import DialogBoasVindasRecorrentes
        dialog = DialogBoasVindasRecorrentes(contas_pendentes, mes_atual_str, mes_passado_str, self.db, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if hasattr(self, 'pagina_financas'):
                self.pagina_financas.carregar_meses(mes_foco=mes_atual_str)
                self.pagina_financas.carregar_dados()
            if hasattr(self, 'pagina_resumo'):
                self.pagina_resumo.carregar_dados()

    def iniciar_radar_dividendos_background(self):
        """
        OBS 1: O Gatilho em Segundo Plano (QThread).
        Inicia uma thread paralela invisível para varrer a B3 em busca de proventos recentes
        dos ativos que você possui na carteira_atual sem travar a interface.
        """
        try:
            holdings = self.db.buscar_dados("SELECT ticker_id, quantidade_total FROM carteira_atual WHERE quantidade_total > 0")
            if not holdings:
                return

            rendimentos_existentes = self.db.buscar_dados("SELECT ticker_id, data_pagamento FROM rendimentos")
            from pagina_rendimentos import WorkerRadarDividendos
            self.worker_radar = WorkerRadarDividendos(self.api, holdings, rendimentos_existentes, parent=self)
            self.worker_radar.dividendos_detectados.connect(self.ao_detectar_dividendos_background)
            self.worker_radar.start()
        except Exception as e:
            print(f"Aviso Radar Background: {e}")

    def ao_detectar_dividendos_background(self, novos_dividendos):
        """
        OBS 2 & Fase 3: A Notificação de Boas-Vindas & Pop-up de Validação (Atrito Positivo).
        Abre o diálogo de confirmação apenas se houver proventos novos encontrados.
        """
        if not novos_dividendos:
            return
        from pagina_rendimentos import DialogRadarDividendos
        dialog = DialogRadarDividendos(
            novos_dividendos,
            self.db,
            fn_atualizar_rendimentos=self.pagina_rendimentos.carregar_dados,
            fn_atualizar_resumo=self.pagina_resumo.carregar_dados,
            parent=self
        )
        dialog.exec()

    def iniciar_verificacao_updates(self):
        """
        Dispara a checagem assíncrona de releases no GitHub em segundo plano (QThread).
        """
        try:
            self.worker_update = WorkerVerificadorUpdates(versao_atual=VERSAO_ATUAL, parent=self)
            self.worker_update.nova_versao_detectada.connect(self.ao_detectar_nova_versao)
            self.worker_update.start()
        except Exception as e:
            print(f"Aviso Update Checker: {e}")

    def ao_detectar_nova_versao(self, dados_update):
        """
        UI/UX Opção A: Exibe a pílula sutil no rodapé do menu lateral.
        """
        self.dados_update_disponivel = dados_update
        versao = dados_update.get("versao", "")
        self.btn_update.setText(f"🚀 Atualização v{versao} Disponível!")
        self.btn_update.setToolTip(f"Clique para ver as novidades e baixar a versão {versao} no GitHub")
        self.btn_update.show()

    def abrir_dialogo_update(self):
        if not self.dados_update_disponivel:
            return
        dialog = DialogAtualizacao(self.dados_update_disponivel, parent=self)
        dialog.exec()

    def closeEvent(self, event):
        SecurityManager.trancar_cofre(self.senha_mestra)
        event.accept()

class Launcher:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.login_window = LoginWindow(self.iniciar_app)
        self.login_window.show()

    def iniciar_app(self, senha, token_brapi=None, nome_usuario=None):
        self.login_window.close()
        self.main_window = DevenWealthWindow(senha, token_brapi, nome_usuario)
        self.main_window.show()

if __name__ == "__main__":
    launcher = Launcher()
    sys.exit(launcher.app.exec())