"""
Simulador GRASP - Posicionamento de Radares
A lógica do algoritmo (heurística construtiva, busca local Swap, lista Tabu e cálculo de cobertura)
"""
import os
import time
import random
import math
import datetime
from tkinter import filedialog, messagebox

import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.widgets.scrolled import ScrolledFrame

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg



class Config:
    """Constantes de configuração da aplicação"""

    TEMA = "flatly"
    TITULO_JANELA = "Simulador GRASP - MCLP | Posicionamento de Radares"
    TAMANHO_JANELA = "1580x960"
    TAMANHO_MINIMO = (1280, 780)

    CANVAS_LARGURA = 700
    CANVAS_ALTURA = 700
    CANVAS_ESPACAMENTO_GRID = 40

    LARGURA_SIDEBAR = 400
    TABU_MAX = 4


    RANGE_DEMANDA = (20, 300)
    RANGE_CANDIDATOS = (10, 100)
    RANGE_RADARES = (1, 20)
    RANGE_RAIO = (40, 200)

    PADRAO_DEMANDA = 120
    PADRAO_CANDIDATOS = 40
    PADRAO_RADARES = 6
    PADRAO_RAIO = 110

    FRAME_MS = 28  # intervalo entre quadros das animações
    PASSOS_ANIMACAO = 6

    AUTOR = "GRASP / MCLP · IFMG"


class Cores:

    COBERTO = "#22c55e"
    NAO_COBERTO = "#ef4444"
    CANDIDATO = "#94a3b8"
    CANDIDATO_BORDA = "#64748b"
    RADAR = "#065f46"
    RADAR_CLARO = "#34d399"
    TABU = "#7c3aed"

    FUNDO_MAPA = "#f8fafc"
    GRADE = "#e2e8f0"
    GRADE_FORTE = "#cbd5e1"
    BRANCO = "#ffffff"

    TEXTO_MUTED = "#64748b"


class Fontes:
    TITULO = ("Segoe UI", 19, "bold")
    SUBTITULO = ("Segoe UI", 10)
    SECAO = ("Segoe UI Semibold", 11)
    TEXTO = ("Segoe UI", 9)
    TEXTO_BOLD = ("Segoe UI", 9, "bold")
    VALOR_GRANDE = ("Segoe UI", 24, "bold")
    VALOR_MEDIO = ("Segoe UI", 15, "bold")
    STATUS = ("Segoe UI", 9)


class GraspRadarSimulator(tb.Window):
    """algoritmo GRASP aplicado ao MCLP."""


    def __init__(self):
        super().__init__(title=Config.TITULO_JANELA, themename=Config.TEMA)
        self.geometry(Config.TAMANHO_JANELA)
        self.minsize(*Config.TAMANHO_MINIMO)

        # ---- Variáveis de controle ----
        self.var_demanda = tb.IntVar(value=Config.PADRAO_DEMANDA)
        self.var_candidatos = tb.IntVar(value=Config.PADRAO_CANDIDATOS)
        self.var_p_radares = tb.IntVar(value=Config.PADRAO_RADARES)
        self.var_raio = tb.IntVar(value=Config.PADRAO_RAIO)

        # ----Estruturas de dados do problema----
        self.I_demanda = []
        self.J_candidatos = []
        self.S_solucao = []
        self.lista_tabu = []
        self.fase_atual = "Aguardando início..."

        # ---- Estado auxiliar de interface
        self.iteracao = 0
        self.historico_iteracao = []
        self.historico_cobertura = []
        self.historico_tempo = []
        self._cobertos_atual = set()
        self._t0 = time.perf_counter()
        self._anim_token = 0


        self.labels_cards = {}
        self.labels_stats = {}
        self.status_labels = {}
        self.botoes_acao = []

        self.setup_ui()
        self.gerar_mapa()


    # MONTAGEM DA INTERFACE
    def setup_ui(self):
        self.setup_header()

        corpo = tb.Frame(self)
        corpo.pack(fill=BOTH, expand=YES)

        self.setup_canvas(corpo)
        self.setup_sidebar(corpo)

        self.setup_statusbar()

    def setup_header(self):
        header = tb.Frame(self, bootstyle="dark", padding=(24, 14))
        header.pack(fill=X, side=TOP)

        bloco_titulo = tb.Frame(header, bootstyle="dark")
        bloco_titulo.pack(side=LEFT)

        tb.Label(
            bloco_titulo, text="📡", font=("Segoe UI Emoji", 26),
            bootstyle="inverse-dark",
        ).pack(side=LEFT, padx=(0, 12))

        bloco_texto = tb.Frame(bloco_titulo, bootstyle="dark")
        bloco_texto.pack(side=LEFT)

        tb.Label(
            bloco_texto, text="Simulador GRASP", font=Fontes.TITULO,
            bootstyle="inverse-dark",
        ).pack(anchor=W)
        tb.Label(
            bloco_texto, text="Problema de Localização de Máxima Cobertura (MCLP)",
            font=Fontes.SUBTITULO, bootstyle="inverse-dark",
        ).pack(anchor=W)

        bloco_badges = tb.Frame(header, bootstyle="dark")
        bloco_badges.pack(side=RIGHT)

        for texto, estilo in (("Heurística Construtiva", "success"), ("Busca Local · Swap", "info"),
                               ("Lista Tabu", "warning")):
            tb.Label(
                bloco_badges, text=f"  {texto}  ", font=Fontes.TEXTO_BOLD,
                bootstyle=f"inverse-{estilo}", padding=(6, 4),
            ).pack(side=LEFT, padx=4)

    def setup_canvas(self, parent):
        moldura = tb.Frame(parent, padding=18)
        moldura.pack(side=LEFT, fill=BOTH, expand=YES)

        cartao = tb.Frame(moldura, bootstyle="light", padding=3)
        cartao.pack(fill=BOTH, expand=YES)

        cabecalho = tb.Frame(cartao)
        cabecalho.pack(fill=X, padx=12, pady=(10, 4))
        tb.Label(cabecalho, text="🗺  Mapa de Cobertura", font=Fontes.SECAO).pack(side=LEFT)
        self.lbl_fase_canvas = tb.Label(cabecalho, text=self.fase_atual, font=Fontes.TEXTO,
                                         bootstyle="secondary")
        self.lbl_fase_canvas.pack(side=RIGHT)

        tb.Separator(cartao).pack(fill=X, padx=10)

        area = tb.Frame(cartao, padding=10)
        area.pack(fill=BOTH, expand=YES)

        self.canvas = tb.Canvas(
            area, width=Config.CANVAS_LARGURA, height=Config.CANVAS_ALTURA,
            bg=Cores.FUNDO_MAPA, highlightthickness=1, highlightbackground=Cores.GRADE_FORTE,
        )
        self.canvas.pack(expand=YES)

    def setup_sidebar(self, parent):
        painel = tb.Frame(parent, width=Config.LARGURA_SIDEBAR)
        painel.pack(side=RIGHT, fill=Y)
        painel.pack_propagate(False)

        scroll = ScrolledFrame(painel, autohide=True, padding=(16, 16))
        scroll.pack(fill=BOTH, expand=YES)

        tb.Label(scroll, text="Painel de Controle", font=Fontes.SECAO).pack(anchor=W)
        tb.Label(scroll, text="Ajuste os parâmetros e execute as fases do GRASP",
                 font=Fontes.TEXTO, bootstyle="secondary").pack(anchor=W, pady=(0, 12))

        self._setup_parametros(scroll)
        self._setup_cobertura_hero(scroll)
        self._setup_cards_metricas(scroll)
        self._setup_botoes(scroll)
        self._setup_estatisticas(scroll)
        self._setup_grafico(scroll)
        self._setup_legenda(scroll)

    # Seções da sidebar
    def _setup_parametros(self, parent):
        card = self._criar_card(parent, "⚙  Parâmetros do Problema")
        self._criar_slider(card, "Pontos de demanda (I)", self.var_demanda, *Config.RANGE_DEMANDA)
        self._criar_slider(card, "Pontos candidatos (J)", self.var_candidatos, *Config.RANGE_CANDIDATOS)
        self._criar_slider(card, "Radares a instalar (p)", self.var_p_radares, *Config.RANGE_RADARES)
        self._criar_slider(card, "Raio de cobertura (R)", self.var_raio, *Config.RANGE_RAIO)

    def _setup_cobertura_hero(self, parent):
        card = self._criar_card(parent, "📊  Cobertura Atual")

        linha = tb.Frame(card)
        linha.pack(fill=X, pady=(4, 6))

        self.meter_cobertura = tb.Meter(
            linha, metersize=132, amounttotal=100, amountused=0,
            subtext="cobertura", textright="%", bootstyle="success",
            stripethickness=10, interactive=False,
        )
        self.meter_cobertura.pack(side=LEFT, padx=(4, 16))

        bloco = tb.Frame(linha)
        bloco.pack(side=LEFT, fill=X, expand=YES)

        self.lbl_cobertura_abs = tb.Label(bloco, text="0 / 0 pontos", font=Fontes.TEXTO_BOLD)
        self.lbl_cobertura_abs.pack(anchor=W, pady=(2, 8))

        self.progress_cobertura = tb.Progressbar(
            bloco, orient=HORIZONTAL, mode="determinate", maximum=100,
            bootstyle="success-striped",
        )
        self.progress_cobertura.pack(fill=X)

        self.lbl_descobertos = tb.Label(bloco, text="0 pontos não atendidos", font=Fontes.TEXTO,
                                         bootstyle="secondary")
        self.lbl_descobertos.pack(anchor=W, pady=(6, 0))

    def _setup_cards_metricas(self, parent):
        grid = tb.Frame(parent)
        grid.pack(fill=X, pady=(4, 14))
        grid.columnconfigure((0, 1), weight=1, uniform="card")

        specs = [
            ("radares", "🛰", "Radares Instalados", "success"),
            ("tempo", "⏱", "Tempo de Execução", "info"),
            ("iteracoes", "🔁", "Iterações", "warning"),
            ("tabu", "🚫", "Lista Tabu", "danger"),
        ]
        for idx, (chave, icone, titulo, estilo) in enumerate(specs):
            linha, coluna = divmod(idx, 2)
            self._criar_card_metrica(grid, chave, icone, titulo, estilo, linha, coluna)

    def _criar_card_metrica(self, parent, chave, icone, titulo, estilo, linha, coluna):
        card = tb.Frame(parent, bootstyle="light", padding=12)
        card.grid(row=linha, column=coluna, sticky="nsew", padx=4, pady=4)

        topo = tb.Frame(card, bootstyle="light")
        topo.pack(fill=X)
        tb.Label(topo, text=icone, font=("Segoe UI Emoji", 13), bootstyle=f"{estilo}").pack(side=LEFT)
        tb.Label(topo, text=titulo, font=Fontes.TEXTO, bootstyle="secondary").pack(side=LEFT, padx=(6, 0))

        valor = tb.Label(card, text="--", font=Fontes.VALOR_MEDIO)
        valor.pack(anchor=W, pady=(6, 0))
        self.labels_cards[chave] = valor

    def _setup_botoes(self, parent):
        card = self._criar_card(parent, "🎛  Ações do GRASP")

        botoes = [
            ("⚙  Gerar Solução Inicial", "success", self.on_gerar_solucao_inicial),
            ("🔄  Executar Busca Local", "info", self.on_executar_busca_local),
            ("🗺  Novo Cenário", "secondary", self.on_novo_cenario),
            ("💾  Exportar Resultado", "secondary-outline", self.exportar_resultado),
            ("📷  Salvar Imagem", "secondary-outline", self.salvar_imagem),
        ]
        for texto, estilo, comando in botoes:
            btn = tb.Button(card, text=texto, bootstyle=estilo, command=comando, padding=(10, 9))
            btn.pack(fill=X, pady=4)
            self.botoes_acao.append(btn)

    def _setup_estatisticas(self, parent):
        card = self._criar_card(parent, "📈  Estatísticas Detalhadas")

        campos = [
            ("demandas", "Nº de pontos de demanda"),
            ("candidatos", "Nº de pontos candidatos"),
            ("radares_inst", "Radares instalados"),
            ("cobertura_pct", "Cobertura"),
            ("descobertos", "Pontos não cobertos"),
            ("tabu_tam", "Tamanho da lista Tabu"),
            ("raio", "Raio de cobertura"),
        ]
        for chave, rotulo in campos:
            linha = tb.Frame(card)
            linha.pack(fill=X, pady=2)
            tb.Label(linha, text=rotulo, font=Fontes.TEXTO, bootstyle="secondary").pack(side=LEFT)
            valor = tb.Label(linha, text="--", font=Fontes.TEXTO_BOLD)
            valor.pack(side=RIGHT)
            self.labels_stats[chave] = valor

    def _setup_grafico(self, parent):
        card = self._criar_card(parent, "📉  Cobertura x Iteração")

        self.fig = Figure(figsize=(3.9, 2.3), dpi=100, facecolor="#ffffff")
        self.ax = self.fig.add_subplot(111)
        self._estilizar_eixo()

        self.canvas_grafico = FigureCanvasTkAgg(self.fig, master=card)
        self.canvas_grafico.get_tk_widget().pack(fill=BOTH, expand=YES)

    def _setup_legenda(self, parent):
        card = self._criar_card(parent, "📍  Legenda do Mapa")

        itens = [
            ("●", Cores.COBERTO, "Demanda coberta"),
            ("●", Cores.NAO_COBERTO, "Demanda não coberta"),
            ("■", Cores.CANDIDATO, "Ponto candidato"),
            ("■", Cores.RADAR, "Radar instalado"),
            ("■", Cores.TABU, "Radar na lista Tabu"),
        ]
        for simbolo, cor, texto in itens:
            linha = tb.Frame(card)
            linha.pack(anchor=W, pady=2)
            tb.Label(linha, text=simbolo, font=("Segoe UI", 12), foreground=cor).pack(side=LEFT)
            tb.Label(linha, text=texto, font=Fontes.TEXTO).pack(side=LEFT, padx=(6, 0))

    def setup_statusbar(self):
        barra = tb.Frame(self, bootstyle="secondary", padding=(16, 6))
        barra.pack(fill=X, side=BOTTOM)

        campos = [("estado", "Estado"), ("tempo", "Tempo"), ("cobertura", "Cobertura"),
                  ("radares", "Radares"), ("iteracao", "Iteração")]
        for chave, rotulo in campos:
            bloco = tb.Frame(barra, bootstyle="secondary")
            bloco.pack(side=LEFT, padx=(0, 22))
            tb.Label(bloco, text=f"{rotulo}:", font=Fontes.STATUS,
                     bootstyle="inverse-secondary").pack(side=LEFT)
            valor = tb.Label(bloco, text="--", font=("Segoe UI", 9, "bold"),
                              bootstyle="inverse-secondary")
            valor.pack(side=LEFT, padx=(4, 0))
            self.status_labels[chave] = valor

        tb.Label(barra, text=f"Autor: {Config.AUTOR}", font=Fontes.STATUS,
                 bootstyle="inverse-secondary").pack(side=RIGHT)

    def _criar_card(self, parent, titulo):
        card = tb.Frame(parent, bootstyle="light", padding=14)
        card.pack(fill=X, pady=(0, 14))
        tb.Label(card, text=titulo, font=Fontes.SECAO).pack(anchor=W, pady=(0, 8))
        return card

    def _criar_slider(self, parent, texto, variavel, minimo, maximo):
        linha = tb.Frame(parent)
        linha.pack(fill=X, pady=(6, 0))
        tb.Label(linha, text=texto, font=Fontes.TEXTO).pack(side=LEFT)
        tb.Label(linha, textvariable=variavel, font=Fontes.TEXTO_BOLD,
                 bootstyle="success").pack(side=RIGHT)
        tb.Scale(parent, from_=minimo, to=maximo, variable=variavel,
                  orient=HORIZONTAL, bootstyle="success").pack(fill=X, pady=(2, 6))

    def _estilizar_eixo(self):
        self.ax.clear()
        self.ax.set_facecolor("#ffffff")
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)
        self.ax.spines["left"].set_color(Cores.GRADE_FORTE)
        self.ax.spines["bottom"].set_color(Cores.GRADE_FORTE)
        self.ax.tick_params(colors=Cores.TEXTO_MUTED, labelsize=7)
        self.ax.set_xlabel("Iteração", fontsize=8, color=Cores.TEXTO_MUTED)
        self.ax.set_ylabel("Cobertura (%)", fontsize=8, color=Cores.TEXTO_MUTED)
        self.ax.set_ylim(0, 100)
        self.ax.grid(True, linestyle="--", linewidth=0.6, color=Cores.GRADE, alpha=0.8)
        self.fig.tight_layout()

    def gerar_mapa(self):
        margem = 40
        self.I_demanda = [
            (random.randint(margem, Config.CANVAS_LARGURA - margem),
             random.randint(margem, Config.CANVAS_ALTURA - margem))
            for _ in range(self.var_demanda.get())
        ]
        self.J_candidatos = [
            (random.randint(margem, Config.CANVAS_LARGURA - margem),
             random.randint(margem, Config.CANVAS_ALTURA - margem))
            for _ in range(self.var_candidatos.get())
        ]

        self.S_solucao = []
        self.lista_tabu = []
        self.fase_atual = "Novo cenário gerado"

        self.iteracao = 0
        self.historico_iteracao = []
        self.historico_cobertura = []
        self.historico_tempo = []
        self._t0 = time.perf_counter()
        self._anim_token += 1

        self.atualizar_tela()

    def distancia(self, p1, p2):
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    def calcular_cobertura(self, solucao):
        """Retorna a quantidade de pontos de demanda cobertos por uma solução."""
        pontos_cobertos = set()
        raio = self.var_raio.get()
        for radar_idx in solucao:
            if radar_idx >= len(self.J_candidatos):
                continue
            radar_pos = self.J_candidatos[radar_idx]
            for i, demanda_pos in enumerate(self.I_demanda):
                if self.distancia(radar_pos, demanda_pos) <= raio:
                    pontos_cobertos.add(i)
        return len(pontos_cobertos)


    # ALGORITMO GRASP
    def fase_construtiva(self):
        p = min(self.var_p_radares.get(), len(self.J_candidatos))
        self.S_solucao = random.sample(range(len(self.J_candidatos)), p)
        self.lista_tabu = []
        self.fase_atual = "Solução inicial gerada (heurística construtiva)"

        self._registrar_historico(reiniciar=True)
        self._animar_aparecer_radares(list(self.S_solucao))

    def movimento_swap(self):
        if not self.S_solucao:
            return

        pior_radar = None
        menor_perda = float('inf')

        for radar in self.S_solucao:
            solucao_temporaria = self.S_solucao.copy()
            solucao_temporaria.remove(radar)
            cobertura_sem_ele = self.calcular_cobertura(solucao_temporaria)

            if cobertura_sem_ele < menor_perda:
                menor_perda = cobertura_sem_ele
                pior_radar = radar

        posicao_removida = None
        if pior_radar is not None:
            posicao_removida = self.J_candidatos[pior_radar]
            self.S_solucao.remove(pior_radar)
            self.lista_tabu.append(pior_radar)
            if len(self.lista_tabu) > Config.TABU_MAX:
                self.lista_tabu.pop(0)

        melhor_candidato = None
        maior_ganho = -1

        for candidato in range(len(self.J_candidatos)):
            if candidato not in self.S_solucao and candidato not in self.lista_tabu:
                solucao_temporaria = self.S_solucao.copy()
                solucao_temporaria.append(candidato)
                nova_cobertura = self.calcular_cobertura(solucao_temporaria)

                if nova_cobertura > maior_ganho:
                    maior_ganho = nova_cobertura
                    melhor_candidato = candidato

        posicao_adicionada = None
        if melhor_candidato is not None and len(self.S_solucao) < self.var_p_radares.get():
            self.S_solucao.append(melhor_candidato)
            posicao_adicionada = self.J_candidatos[melhor_candidato]

        self.fase_atual = "Busca local (Swap) executada"

        self.iteracao += 1
        self._registrar_historico(reiniciar=False)
        self._animar_swap(posicao_removida, posicao_adicionada)

    # TELEMETRIA
    def _registrar_historico(self, reiniciar):
        total = len(self.I_demanda)
        cobertura_pct = (self.calcular_cobertura(self.S_solucao) / total * 100) if total else 0.0
        tempo = self._tempo_decorrido()

        if reiniciar:
            self.iteracao = 0
            self.historico_iteracao = [0]
            self.historico_cobertura = [cobertura_pct]
            self.historico_tempo = [tempo]
        else:
            self.historico_iteracao.append(self.iteracao)
            self.historico_cobertura.append(cobertura_pct)
            self.historico_tempo.append(tempo)

    def _tempo_decorrido(self):
        return time.perf_counter() - self._t0

    def _formatar_tempo(self, segundos):
        minutos = int(segundos // 60)
        resto = segundos % 60
        return f"{minutos:02d}:{resto:05.2f}"

    # DESENHO DO MAPA
    def atualizar_tela(self):
        self.canvas.delete("all")
        self.desenhar_grid()
        cobertos = self.desenhar_radares()
        self.desenhar_demandas(cobertos)
        self.desenhar_marcadores()
        self._cobertos_atual = cobertos

        self.atualizar_cards()
        self.atualizar_estatisticas()
        self.atualizar_grafico()
        self.atualizar_status_bar()
        self._definir_botoes_ativos(True)

    def desenhar_grid(self):
        largura, altura = Config.CANVAS_LARGURA, Config.CANVAS_ALTURA
        espacamento = Config.CANVAS_ESPACAMENTO_GRID

        self.canvas.create_rectangle(0, 0, largura, altura, fill=Cores.FUNDO_MAPA, outline="")
        for x in range(0, largura + 1, espacamento):
            self.canvas.create_line(x, 0, x, altura, fill=Cores.GRADE, width=1)
        for y in range(0, altura + 1, espacamento):
            self.canvas.create_line(0, y, largura, y, fill=Cores.GRADE, width=1)
        self.canvas.create_rectangle(1, 1, largura - 1, altura - 1, outline=Cores.GRADE_FORTE, width=1)

    def desenhar_radares(self):
        raio = self.var_raio.get()
        cobertos = set()

        for radar_idx in self.S_solucao:
            if radar_idx >= len(self.J_candidatos):
                continue
            rx, ry = self.J_candidatos[radar_idx]

            self.canvas.create_oval(rx - raio, ry - raio, rx + raio, ry + raio,
                                     outline=Cores.RADAR, width=1.4, dash=(5, 3))
            self.canvas.create_oval(rx - raio * 0.62, ry - raio * 0.62, rx + raio * 0.62, ry + raio * 0.62,
                                     outline=Cores.RADAR_CLARO, width=1, dash=(3, 3))
            self.canvas.create_oval(rx - raio * 0.28, ry - raio * 0.28, rx + raio * 0.28, ry + raio * 0.28,
                                     outline=Cores.RADAR_CLARO, width=1, dash=(2, 2))

            for i, d_pos in enumerate(self.I_demanda):
                if self.distancia((rx, ry), d_pos) <= raio:
                    cobertos.add(i)

        return cobertos

    def desenhar_demandas(self, cobertos):
        for i, (x, y) in enumerate(self.I_demanda):
            cor = Cores.COBERTO if i in cobertos else Cores.NAO_COBERTO
            self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill=cor, outline=Cores.BRANCO, width=1)

    def desenhar_marcadores(self):
        for j, (x, y) in enumerate(self.J_candidatos):
            if j in self.S_solucao:
                self.canvas.create_rectangle(x - 7, y - 7, x + 7, y + 7,
                                              fill=Cores.RADAR, outline=Cores.BRANCO, width=2)
                self.canvas.create_oval(x - 2, y - 2, x + 2, y + 2, fill=Cores.BRANCO, outline="")
            elif j in self.lista_tabu:
                self.canvas.create_rectangle(x - 6, y - 6, x + 6, y + 6,
                                              fill=Cores.TABU, outline=Cores.BRANCO, width=1.5)
            else:
                self.canvas.create_rectangle(x - 5, y - 5, x + 5, y + 5,
                                              fill=Cores.CANDIDATO, outline=Cores.CANDIDATO_BORDA, width=1)


    def _novo_token_animacao(self):
        self._anim_token += 1
        self._definir_botoes_ativos(False)
        return self._anim_token

    def _definir_botoes_ativos(self, ativo):
        estado = NORMAL if ativo else DISABLED
        for botao in self.botoes_acao:
            botao.configure(state=estado)

    def _animar_aparecer_radares(self, indices):
        token = self._novo_token_animacao()
        posicoes = [self.J_candidatos[i] for i in indices if i < len(self.J_candidatos)]

        def quadro(passo):
            if token != self._anim_token:
                return
            self.canvas.delete("all")
            self.desenhar_grid()
            cobertos = self.desenhar_radares()
            self.desenhar_demandas(cobertos)
            self.desenhar_marcadores()

            raio_pulso = 6 + passo * 5
            for (x, y) in posicoes:
                self.canvas.create_oval(x - raio_pulso, y - raio_pulso, x + raio_pulso, y + raio_pulso,
                                         outline=Cores.RADAR, width=2, dash=(2, 2))

            if passo < Config.PASSOS_ANIMACAO:
                self.after(Config.FRAME_MS, lambda: quadro(passo + 1))
            else:
                self.atualizar_tela()

        quadro(0)

    def _animar_swap(self, posicao_removida, posicao_adicionada):
        token = self._novo_token_animacao()

        def quadro(passo):
            if token != self._anim_token:
                return
            self.canvas.delete("all")
            self.desenhar_grid()
            cobertos = self.desenhar_radares()
            self.desenhar_demandas(cobertos)
            self.desenhar_marcadores()

            if posicao_removida:
                x, y = posicao_removida
                raio = 12 - passo * 1.8
                if raio > 0:
                    self.canvas.create_oval(x - raio, y - raio, x + raio, y + raio,
                                             outline=Cores.NAO_COBERTO, width=2)
            if posicao_adicionada:
                x, y = posicao_adicionada
                raio = 4 + passo * 3
                self.canvas.create_oval(x - raio, y - raio, x + raio, y + raio,
                                         outline=Cores.RADAR, width=2, dash=(2, 2))

            if passo < Config.PASSOS_ANIMACAO:
                self.after(Config.FRAME_MS, lambda: quadro(passo + 1))
            else:
                self.atualizar_tela()

        quadro(0)


    def atualizar_cards(self):
        total = len(self.I_demanda)
        cobertos = len(self._cobertos_atual)
        pct = (cobertos / total * 100) if total else 0.0
        p_alvo = self.var_p_radares.get()
        tempo = self._tempo_decorrido()

        self.meter_cobertura.configure(amountused=round(pct, 1))
        self.progress_cobertura.configure(value=pct)
        self.lbl_cobertura_abs.configure(text=f"{cobertos} / {total} pontos atendidos ({pct:.1f}%)")
        self.lbl_descobertos.configure(text=f"{total - cobertos} pontos não atendidos")

        self.labels_cards["radares"].configure(text=f"{len(self.S_solucao)} / {p_alvo}")
        self.labels_cards["tempo"].configure(text=self._formatar_tempo(tempo))
        self.labels_cards["iteracoes"].configure(text=str(self.iteracao))
        self.labels_cards["tabu"].configure(text=f"{len(self.lista_tabu)} / {Config.TABU_MAX}")

    def atualizar_estatisticas(self):
        total = len(self.I_demanda)
        cobertos = len(self._cobertos_atual)
        pct = (cobertos / total * 100) if total else 0.0

        self.labels_stats["demandas"].configure(text=str(total))
        self.labels_stats["candidatos"].configure(text=str(len(self.J_candidatos)))
        self.labels_stats["radares_inst"].configure(text=f"{len(self.S_solucao)} / {self.var_p_radares.get()}")
        self.labels_stats["cobertura_pct"].configure(text=f"{pct:.1f}%")
        self.labels_stats["descobertos"].configure(text=str(total - cobertos))
        self.labels_stats["tabu_tam"].configure(text=f"{len(self.lista_tabu)} / {Config.TABU_MAX}")
        self.labels_stats["raio"].configure(text=f"{self.var_raio.get()} px")

    def atualizar_grafico(self):
        self._estilizar_eixo()
        if self.historico_iteracao:
            self.ax.plot(self.historico_iteracao, self.historico_cobertura,
                         color=Cores.RADAR, marker="o", markersize=3.5, linewidth=1.8)
            self.ax.fill_between(self.historico_iteracao, self.historico_cobertura,
                                  color=Cores.RADAR_CLARO, alpha=0.18)
        self.canvas_grafico.draw_idle()

    def atualizar_status_bar(self):
        total = len(self.I_demanda)
        pct = (len(self._cobertos_atual) / total * 100) if total else 0.0

        self.lbl_fase_canvas.configure(text=self.fase_atual)
        self.status_labels["estado"].configure(text=self.fase_atual)
        self.status_labels["tempo"].configure(text=self._formatar_tempo(self._tempo_decorrido()))
        self.status_labels["cobertura"].configure(text=f"{pct:.1f}%")
        self.status_labels["radares"].configure(text=f"{len(self.S_solucao)} / {self.var_p_radares.get()}")
        self.status_labels["iteracao"].configure(text=str(self.iteracao))


    def on_gerar_solucao_inicial(self):
        if not self.J_candidatos:
            return
        self.fase_construtiva()

    def on_executar_busca_local(self):
        if not self.S_solucao:
            messagebox.showwarning(
                "Busca local indisponível",
                "Gere uma solução inicial antes de executar a busca local (Swap).",
            )
            return
        self.movimento_swap()

    def on_novo_cenario(self):
        self.gerar_mapa()

    def exportar_resultado(self):
        caminho = filedialog.asksaveasfilename(
            title="Exportar Resultado da Simulação",
            defaultextension=".txt",
            filetypes=[("Arquivo de texto", "*.txt"), ("Todos os arquivos", "*.*")],
        )
        if not caminho:
            return

        try:
            with open(caminho, "w", encoding="utf-8") as arquivo:
                arquivo.write(self._montar_relatorio())
            self.fase_atual = f"Resultado exportado ({os.path.basename(caminho)})"
            self.atualizar_status_bar()
            messagebox.showinfo("Exportar Resultado", "Relatório exportado com sucesso.")
        except OSError as erro:
            messagebox.showerror("Erro ao exportar", str(erro))

    def _montar_relatorio(self):
        total = len(self.I_demanda)
        cobertos = len(self._cobertos_atual)
        pct = (cobertos / total * 100) if total else 0.0
        agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        linhas = [
            "=== Relatório de Simulação — GRASP / MCLP ===",
            f"Gerado em: {agora}",
            "",
            "Parâmetros do problema",
            f"  Pontos de demanda (I): {total}",
            f"  Pontos candidatos (J): {len(self.J_candidatos)}",
            f"  Radares a instalar (p): {self.var_p_radares.get()}",
            f"  Raio de cobertura (R): {self.var_raio.get()}",
            "",
            "Resultado atual",
            f"  Fase: {self.fase_atual}",
            f"  Iteração: {self.iteracao}",
            f"  Tempo decorrido: {self._formatar_tempo(self._tempo_decorrido())}",
            f"  Radares instalados (índices): {sorted(self.S_solucao)}",
            f"  Lista Tabu (índices): {list(self.lista_tabu)}",
            f"  Cobertura: {pct:.2f}% ({cobertos} de {total} pontos)",
            f"  Pontos não cobertos: {total - cobertos}",
            "",
            "Histórico (iteração, cobertura %, tempo s)",
        ]
        for it, cob, tmp in zip(self.historico_iteracao, self.historico_cobertura, self.historico_tempo):
            linhas.append(f"  {it}, {cob:.2f}, {tmp:.2f}")

        return "\n".join(linhas)

    def salvar_imagem(self):
        caminho = filedialog.asksaveasfilename(
            title="Salvar Imagem do Mapa",
            defaultextension=".png",
            filetypes=[("Imagem PNG", "*.png"), ("Todos os arquivos", "*.*")],
        )
        if not caminho:
            return

        try:
            from PIL import ImageGrab
            x = self.canvas.winfo_rootx()
            y = self.canvas.winfo_rooty()
            largura = self.canvas.winfo_width()
            altura = self.canvas.winfo_height()
            imagem = ImageGrab.grab(bbox=(x, y, x + largura, y + altura))
            imagem.save(caminho)
        except Exception:
            caminho = os.path.splitext(caminho)[0] + ".ps"
            self.canvas.postscript(file=caminho, colormode="color")

        self.fase_atual = f"Imagem salva ({os.path.basename(caminho)})"
        self.atualizar_status_bar()
        messagebox.showinfo("Salvar Imagem", f"Imagem salva em:\n{caminho}")


if __name__ == "__main__":
    app = GraspRadarSimulator()
    app.mainloop()
