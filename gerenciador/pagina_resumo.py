import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QDoubleSpinBox, QPushButton
from PyQt6.QtCore import Qt
from datetime import datetime

class PaginaResumo(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setup_ui()

    def setup_ui(self):
        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout_principal.setSpacing(25)

        titulo = QLabel("Dashboard")
        titulo.setObjectName("tituloPagina")
        titulo.setStyleSheet("font-size: 28px; font-weight: bold; color: #ffffff;")
        self.layout_principal.addWidget(titulo)

        # 1. Os Cards (KPIs)
        self.layout_kpis = QHBoxLayout()
        self.layout_kpis.setSpacing(20)

        self.card_patrimonio = self.criar_card("Patrimônio Líquido", "R$ 0,00", "#4c6fff")
        self.card_poupanca = self.criar_card("Taxa de Poupança", "0%", "#ff9a3c")
        self.card_renda = self.criar_card("Renda Passiva (Mês)", "R$ 0,00", "#ff4b82")

        self.layout_kpis.addWidget(self.card_patrimonio)
        self.layout_kpis.addWidget(self.card_poupanca)
        self.layout_kpis.addWidget(self.card_renda)

        self.layout_principal.addLayout(self.layout_kpis)

        # 2. Gráficos
        self.layout_graficos = QHBoxLayout()
        self.layout_graficos.setSpacing(20)

        # Gráfico Raio-X 50/30/20 (Esquerda)
        self.frame_rosca = QFrame()
        self.frame_rosca.setStyleSheet("background-color: #262939; border-radius: 15px;")
        layout_rosca = QVBoxLayout(self.frame_rosca)
        titulo_rosca = QLabel("Raio-X 50/30/20 (Mês Atual)")
        titulo_rosca.setStyleSheet("color: #8c8e9b; font-size: 14px; font-weight: bold; margin-left: 10px; margin-top: 10px;")
        layout_rosca.addWidget(titulo_rosca)

        self.fig_rosca = Figure(figsize=(5, 4), dpi=100)
        self.fig_rosca.patch.set_facecolor('#262939')
        self.canvas_rosca = FigureCanvas(self.fig_rosca)
        layout_rosca.addWidget(self.canvas_rosca)
        
        self.layout_graficos.addWidget(self.frame_rosca, 1)

        # Gráfico Bola de Neve (Direita)
        self.frame_barras = QFrame()
        self.frame_barras.setStyleSheet("background-color: #262939; border-radius: 15px;")
        layout_barras = QVBoxLayout(self.frame_barras)
        
        titulo_barras = QLabel("Evolução de Dividendos")
        titulo_barras.setStyleSheet("color: #8c8e9b; font-size: 14px; font-weight: bold; margin-left: 10px; margin-top: 10px;")
        layout_barras.addWidget(titulo_barras)

        self.fig_barras = Figure(figsize=(5, 4), dpi=100)
        self.fig_barras.patch.set_facecolor('#262939')
        self.canvas_barras = FigureCanvas(self.fig_barras)
        layout_barras.addWidget(self.canvas_barras)

        self.layout_graficos.addWidget(self.frame_barras, 1)

        self.layout_principal.addLayout(self.layout_graficos)
        
        # 3. Simulador Máquina do Tempo
        self.frame_simulador = QFrame()
        self.frame_simulador.setStyleSheet("background-color: #262939; border-radius: 15px;")
        layout_sim = QHBoxLayout(self.frame_simulador)
        
        # Esquerda: Inputs
        layout_sim_inputs = QVBoxLayout()
        layout_sim_inputs.setSpacing(8)
        
        titulo_sim = QLabel("⏳ Máquina do Tempo (Simulador de Riqueza)")
        titulo_sim.setStyleSheet("color: #a6e3a1; font-size: 16px; font-weight: bold; margin-bottom: 5px;")
        
        lbl_meta = QLabel("Sua Meta Patrimonial:")
        lbl_meta.setStyleSheet("color: #8c8e9b;")
        self.spin_meta = QDoubleSpinBox()
        self.spin_meta.setGroupSeparatorShown(True)
        self.spin_meta.setRange(1000, 1000000000)
        self.spin_meta.setPrefix("R$ ")
        self.spin_meta.setValue(1000000.0) # 1 Milhão Padrão
        self.spin_meta.setDecimals(2)
        self.spin_meta.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        lbl_taxa = QLabel("Rentabilidade Anual Esperada:")
        lbl_taxa.setStyleSheet("color: #8c8e9b;")
        self.spin_taxa = QDoubleSpinBox()
        self.spin_taxa.setGroupSeparatorShown(True)
        self.spin_taxa.setRange(1, 100)
        self.spin_taxa.setSuffix("% a.a.")
        self.spin_taxa.setValue(10.0)
        self.spin_taxa.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        btn_simular = QPushButton("Simular Futuro")
        btn_simular.setStyleSheet("background-color: #89b4fa; color: #11111b; font-weight: bold; padding: 10px; margin-top: 10px; border-radius: 5px;")
        btn_simular.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_simular.clicked.connect(self.calcular_maquina_tempo)
        
        layout_sim_inputs.addWidget(titulo_sim)
        layout_sim_inputs.addWidget(lbl_meta)
        layout_sim_inputs.addWidget(self.spin_meta)
        layout_sim_inputs.addWidget(lbl_taxa)
        layout_sim_inputs.addWidget(self.spin_taxa)
        layout_sim_inputs.addWidget(btn_simular)
        layout_sim_inputs.addStretch()
        
        # Direita: Resultado
        self.lbl_resultado_sim = QLabel("Preencha a meta e clique em Simular para descobrir em qual data você alcançará seu objetivo financeiro usando o poder dos juros compostos.")
        self.lbl_resultado_sim.setWordWrap(True)
        self.lbl_resultado_sim.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_resultado_sim.setStyleSheet("color: #cdd6f4; font-size: 16px; font-weight: bold; padding: 20px;")
        
        layout_sim.addLayout(layout_sim_inputs, 1)
        layout_sim.addWidget(self.lbl_resultado_sim, 2)
        
        self.layout_principal.addWidget(self.frame_simulador)
        
        self.layout_principal.addStretch()

    def criar_card(self, titulo, valor, cor_destaque):
        card = QFrame()
        card.setStyleSheet("background-color: #262939; border-radius: 15px;")
        card.setFixedHeight(130)
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.setContentsMargins(25, 20, 25, 20)
        
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet("color: #8c8e9b; font-size: 15px; font-weight: bold;")
        
        lbl_valor = QLabel(valor)
        card.lbl_valor = lbl_valor 
        lbl_valor.setStyleSheet(f"color: #ffffff; font-size: 32px; font-weight: bold; margin-top: 5px;")
        
        lbl_destaque = QLabel("●")
        lbl_destaque.setStyleSheet(f"color: {cor_destaque}; font-size: 20px;")
        
        header = QHBoxLayout()
        header.setContentsMargins(0,0,0,0)
        header.addWidget(lbl_titulo)
        header.addStretch()
        header.addWidget(lbl_destaque)
        
        layout.addLayout(header)
        layout.addWidget(lbl_valor)
        
        return card

    def carregar_dados(self):
        mes_atual = datetime.now().strftime('%Y-%m')
        
        # 1. Patrimônio Líquido
        query_saldo = "SELECT SUM(CASE WHEN c.tipo='Receita' THEN t.valor ELSE -t.valor END) as saldo FROM transacoes t JOIN categorias c ON t.categoria_id = c.id"
        res_saldo = self.db.buscar_dados(query_saldo)
        saldo_conta = res_saldo[0]['saldo'] if res_saldo and res_saldo[0]['saldo'] else 0
        
        query_carteira = "SELECT SUM(cart.quantidade_total * cm.preco_atual) as total_carteira FROM carteira_atual cart JOIN cache_mercado cm ON cart.ticker_id = cm.ticker_id"
        res_carteira = self.db.buscar_dados(query_carteira)
        total_carteira = res_carteira[0]['total_carteira'] if res_carteira and res_carteira[0]['total_carteira'] else 0
        
        patrimonio_liquido = saldo_conta + total_carteira
        self.patrimonio_liquido = patrimonio_liquido
        self.card_patrimonio.lbl_valor.setText(f"R$ {patrimonio_liquido:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        query_media_aportes = """
            SELECT SUM(t.valor) / COUNT(DISTINCT strftime('%Y-%m', t.data)) as media 
            FROM transacoes t 
            JOIN categorias c ON t.categoria_id = c.id 
            WHERE c.grupo_regra = 'Construção de Riqueza'
        """
        res_media = self.db.buscar_dados(query_media_aportes)
        self.media_aportes = res_media[0]['media'] if res_media and res_media[0]['media'] else 0.0
        
        # 2. Taxa de Poupança (Mês Atual)
        query_receitas = f"SELECT SUM(t.valor) as rec FROM transacoes t JOIN categorias c ON t.categoria_id = c.id WHERE c.tipo = 'Receita' AND strftime('%Y-%m', t.data) = '{mes_atual}'"
        res_receitas = self.db.buscar_dados(query_receitas)
        receitas_mes = res_receitas[0]['rec'] if res_receitas and res_receitas[0]['rec'] else 0
        
        query_aportes = f"SELECT SUM(t.valor) as ap FROM transacoes t JOIN categorias c ON t.categoria_id = c.id WHERE c.grupo_regra = 'Construção de Riqueza' AND strftime('%Y-%m', t.data) = '{mes_atual}'"
        res_aportes = self.db.buscar_dados(query_aportes)
        aportes_mes = res_aportes[0]['ap'] if res_aportes and res_aportes[0]['ap'] else 0
        
        taxa_poupanca = (aportes_mes / receitas_mes * 100) if receitas_mes > 0 else 0
        cor_taxa = "#00e676" if taxa_poupanca >= 20 else "#ff9a3c" # Verde vibrante se >= 20%, senão laranja
        self.card_poupanca.lbl_valor.setText(f"{taxa_poupanca:.1f}%")
        self.card_poupanca.lbl_valor.setStyleSheet(f"color: {cor_taxa}; font-size: 32px; font-weight: bold; margin-top: 5px;")
        
        # 3. Renda Passiva do Mês
        query_renda = f"SELECT SUM(valor_liquido_total) as renda FROM rendimentos WHERE strftime('%Y-%m', data_pagamento) = '{mes_atual}'"
        res_renda = self.db.buscar_dados(query_renda)
        renda_mes = res_renda[0]['renda'] if res_renda and res_renda[0]['renda'] else 0
        self.card_renda.lbl_valor.setText(f"R$ {renda_mes:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        self.atualizar_grafico_rosca(mes_atual)
        self.atualizar_grafico_barras()

    def atualizar_grafico_rosca(self, mes_atual):
        self.fig_rosca.clear()
        ax = self.fig_rosca.add_subplot(111)
        
        query = f"SELECT c.grupo_regra, SUM(t.valor) as total FROM transacoes t JOIN categorias c ON t.categoria_id = c.id WHERE c.tipo = 'Despesa' AND strftime('%Y-%m', t.data) = '{mes_atual}' GROUP BY c.grupo_regra"
        dados = self.db.buscar_dados(query)
        
        if not dados:
            ax.text(0.5, 0.5, "Sem despesas registradas", color="#8c8e9b", ha="center", va="center", fontsize=12)
            ax.axis('off')
            self.canvas_rosca.draw()
            return

        grupos = [d['grupo_regra'] for d in dados]
        valores = [d['total'] for d in dados]
        total_despesas = sum(valores)
        
        # Paleta inspirada na imagem de referência (Doughnut chart)
        paleta = {
            'Necessidades': '#4c6fff', 
            'Desejos': '#ff4b82', 
            'Construção de Riqueza': '#a55eea', 
            'Sem Grupo': '#ff9a3c'
        }
        cores = [paleta.get(g, '#a6e3a1') for g in grupos]
        
        wedges, texts = ax.pie(
            valores, 
            colors=cores, 
            startangle=90, 
            wedgeprops=dict(width=0.35, edgecolor='#262939', linewidth=3)
        )
        
        # Centro vazio com texto do Total de Gastos
        ax.text(0, 0, f"R$\n{total_despesas:,.0f}".replace(",", "."), ha='center', va='center', fontsize=22, fontweight='bold', color='#ffffff')
        
        # Legenda posicionada ao lado
        ax.legend(wedges, grupos, loc="center left", bbox_to_anchor=(0.9, 0, 0.5, 1), frameon=False, labelcolor='#8c8e9b', fontsize=11)
        
        self.fig_rosca.tight_layout()
        self.canvas_rosca.draw()

    def atualizar_grafico_barras(self):
        self.fig_barras.clear()
        ax = self.fig_barras.add_subplot(111)
        
        query = "SELECT strftime('%Y-%m', data_pagamento) as mes, SUM(valor_liquido_total) as total FROM rendimentos GROUP BY mes ORDER BY mes ASC LIMIT 6"
        dados = self.db.buscar_dados(query)
        
        if not dados:
            ax.text(0.5, 0.5, "Nenhum rendimento registrado", color="#8c8e9b", ha="center", va="center", fontsize=12)
            ax.axis('off')
            self.canvas_barras.draw()
            return
            
        # Pega as iniciais do mes pra ficar bonito (ex: 2026-09 -> Set)
        meses_nomes = {'01':'Jan', '02':'Fev', '03':'Mar', '04':'Abr', '05':'Mai', '06':'Jun', '07':'Jul', '08':'Ago', '09':'Set', '10':'Out', '11':'Nov', '12':'Dez'}
        meses = [meses_nomes.get(d['mes'][-2:], d['mes'][-2:]) for d in dados]
        totais = [d['total'] for d in dados]
        
        # Barras verdes vibrantes conforme solicitado "A cor da barra pode ser um verde vibrante."
        barras = ax.bar(meses, totais, color='#00e676', width=0.45, edgecolor='none')
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('#313244')
        ax.tick_params(colors='#8c8e9b', left=False)
        ax.grid(axis='y', color='#313244', linestyle='-', alpha=0.3)
        
        # Coloca o valor formatado em cima de cada barra
        for barra in barras:
            altura = barra.get_height()
            ax.annotate(f'{altura:.0f}',
                        xy=(barra.get_x() + barra.get_width() / 2, altura),
                        xytext=(0, 5),  
                        textcoords="offset points",
                        ha='center', va='bottom', color='#ffffff', fontsize=11, fontweight='bold')
                        
        self.fig_barras.tight_layout()
        self.canvas_barras.draw()

    def calcular_maquina_tempo(self):
        meta = self.spin_meta.value()
        taxa_anual = self.spin_taxa.value() / 100.0
        taxa_mensal = (1 + taxa_anual) ** (1/12) - 1
        
        if getattr(self, 'patrimonio_liquido', 0) >= meta:
            self.lbl_resultado_sim.setText("🎉 Você já atingiu essa meta! Sonhe maior!")
            return
            
        aportes = getattr(self, 'media_aportes', 0)
        patrimonio = getattr(self, 'patrimonio_liquido', 0)
            
        if aportes <= 0 and patrimonio <= 0:
            self.lbl_resultado_sim.setText("Você precisa começar a investir (Patrimônio > 0 ou Histórico de Aportes > 0) para a mágica acontecer!")
            return
            
        meses = 0
        
        while patrimonio < meta and meses < 1200: # Max 100 anos
            patrimonio += (patrimonio * taxa_mensal)
            patrimonio += aportes
            meses += 1
            
        if meses >= 1200:
            self.lbl_resultado_sim.setText(f"Com sua média histórica de aportes (R$ {aportes:,.2f}/mês), levaria mais de 100 anos para atingir a meta. Aumente sua Taxa de Poupança!")
        else:
            anos = meses // 12
            meses_resto = meses % 12
            
            ano_atual = datetime.now().year
            mes_atual = datetime.now().month
            ano_futuro = ano_atual + anos
            mes_futuro = mes_atual + meses_resto
            if mes_futuro > 12:
                ano_futuro += 1
                mes_futuro -= 12
            
            meses_nomes = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
            nome_mes = meses_nomes[mes_futuro - 1]
            
            meta_str = f"R$ {meta:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            aportes_str = f"R$ {aportes:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
            texto = f"Usando sua média histórica de investimentos (<b>{aportes_str}/mês</b>), você alcançará a meta em:<br><br>"
            texto += f"<span style='font-size: 28px; color: #a6e3a1;'>{anos} anos e {meses_resto} meses</span><br><br>"
            texto += f"Prepare-se: em <b>{nome_mes} de {ano_futuro}</b>, você terá <b>{meta_str}</b>!"
            
            self.lbl_resultado_sim.setText(texto)
