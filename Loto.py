import streamlit as st
import pandas as pd
import requests
import json
import random
import uuid
import re
from collections import Counter
from datetime import datetime
import urllib3
from fpdf import FPDF
from datetime import datetime
import requests
import os

def gerar_pdf_jogos(jogos, dezenas_anteriores=None):
    if dezenas_anteriores is None:
        dezenas_anteriores = []
        
    def limpar_latin1(texto):
        return str(texto).encode('latin-1', 'ignore').decode('latin-1')

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # CABEÇALHO DO PDF (Roxo Lotofácil)
    pdf.set_text_color(147, 0, 137) # #930089 Loto Color
    pdf.set_font('Arial', 'B', 22)
    pdf.set_xy(10, 12)
    pdf.cell(0, 10, "LotoMatrix PRO - Volantes de Aposta", ln=0)
    
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.set_xy(10, 22)
    pdf.cell(0, 8, "Relatorio Oficial Pericial", ln=0)
    
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(147, 0, 137)
    pdf.set_xy(10, 12)
    pdf.cell(190, 10, f"TOTAL: {len(jogos)} BILHETES", ln=0, align='R')
    
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(120, 120, 120)
    pdf.set_xy(10, 22)
    pdf.cell(190, 8, datetime.now().strftime('%d/%m/%Y %H:%M'), ln=0, align='R')
    
    pdf.ln(30)
    
    # GERADOR DE CARDS NO PDF
    for i, j in enumerate(jogos, 1):
        if pdf.get_y() > 220:
            pdf.add_page()
            
        y_start = pdf.get_y()
        
        estrategia = limpar_latin1(str(j.get('estrategia', 'Padrao')).replace("🧬", "").replace("🍀", "").strip())
        dna_banco = limpar_latin1(str(j.get('dna', '')).replace("🧬", "").replace("🍀", "").strip())
        dezenas = j.get('dezenas', [])
        alvo = limpar_latin1(str(j.get('concurso_alvo', 'N/A')))
        
        # Fundo e Bordas do Cartão
        pdf.set_fill_color(252, 245, 255) # Fundo levemente roxo
        pdf.rect(10, y_start, 190, 65, 'F')
        pdf.set_fill_color(147, 0, 137)
        pdf.rect(10, y_start, 3, 65, 'F')
        
        # Topo do Cartão
        pdf.set_text_color(40, 40, 40)
        pdf.set_font('Arial', 'B', 12)
        pdf.set_xy(18, y_start + 5)
        pdf.cell(100, 8, f"JOGO {i:02d}  |  Alvo: {alvo}  |  {len(dezenas)} Dezenas", ln=0)
        
        pdf.set_text_color(147, 0, 137) 
        pdf.set_font('Arial', 'B', 10)
        pdf.set_xy(10, y_start + 5)
        pdf.cell(185, 8, f"{estrategia}", ln=0, align='R')
        
        # DESENHO DO VOLANTE
        start_x = 75
        start_y = y_start + 18
        espaco_x = 10
        espaco_y = 8 
        
        for num in range(1, 26):
            linha = (num - 1) // 5
            coluna = (num - 1) % 5
            cx = start_x + (coluna * espaco_x)
            cy = start_y + (linha * espaco_y)
            
            if num in dezenas:
                pdf.set_fill_color(147, 0, 137) # Bola roxa
                pdf.set_text_color(255, 255, 255)
            else:
                pdf.set_fill_color(235, 235, 235) # Bola cinza
                pdf.set_text_color(160, 160, 160)
                
            pdf.ellipse(cx, cy, 6, 6, 'F')
            pdf.set_xy(cx, cy)
            pdf.set_font('Arial', 'B', 7)
            pdf.cell(6, 6, f"{num:02d}", align='C')
            
        # Rodapé
        pdf.set_text_color(147, 0, 137)
        pdf.set_font('Arial', 'I', 8)
        pdf.set_xy(18, y_start + 58)
        pdf.cell(170, 5, f"DNA LotoMatrix: {dna_banco}", ln=0, align='C')
        
        pdf.set_y(y_start + 70)
        
    resultado = pdf.output(dest='S')
    if isinstance(resultado, str):
        return resultado.encode('latin-1', 'ignore')
    return bytes(resultado)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
def exibir_mini_painel_financeiro():
    b_atual = st.session_state.data.get("banca", 0.0)
    t_aportes = st.session_state.data.get("historico_aportes", 0.0)
    t_saques = st.session_state.data.get("historico_saques", 0.0)
    res_global = (b_atual + t_saques) - t_aportes

    str_banca = f"R$ {b_atual:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    str_res = f"R$ {res_global:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    if res_global > 0:
        status_msg = f"🟢 **Lucro Global:** `{str_res}`"
    elif res_global < 0:
        status_msg = f"🔴 **Prejuízo Global:** `{str_res}`"
    else:
        status_msg = f"⚪ **Empate Global:** `{str_res}`"

    st.markdown(f"> 🏦 **Banca Disponível:** `{str_banca}` &nbsp;&nbsp;|&nbsp;&nbsp; {status_msg}")
    st.write("")
def salvar_dados(dados):
    """Força a gravação silenciosa da memória da IA no arquivo local do PC"""
    try:
        import json
        with open("Cofre.json", "w", encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
    except Exception as e:
        pass

def render_performance_grid(dezenas_lista, titulo):
    contagem = Counter(dezenas_lista)
    # Criar DataFrame para visualizar melhor
    df = pd.DataFrame.from_dict(contagem, orient='index', columns=['Frequência']).sort_index()
    st.markdown(f"#### {titulo}")
    # Usar um gráfico de barras simples e elegante
    st.bar_chart(df)

# =====================================================================
# MOTOR DE INTELIGÊNCIA MATEMÁTICA - ADAPTATIVE MATRIX & CONFIDENCE
# =====================================================================
import itertools

@st.cache_data(show_spinner="🧠 Calculando Geometria do Fechamento (Motor Bitwise Ultra-Rápido)...")
def gerar_fechamento_matematico(dezenas, garantia):
    """
    Mantém a lógica original de Compressão Máxima (Set Cover) para não estourar o orçamento do Plano B.
    Troca a lentidão das operações de intersecção de conjuntos (set) por Matemática de Bits (Bitwise), 
    acelerando o processamento massivamente.
    """
    todas_comb_15 = list(itertools.combinations(dezenas, 15))
    
    if garantia == 15:
        return [list(c) for c in todas_comb_15]
        
    # 🌟 INOVAÇÃO: Transformação Quântica - Converte as dezenas em Máscaras de Bits
    comb_bits = []
    for c in todas_comb_15:
        bits = 0
        for num in c:
            bits |= (1 << num)
        comb_bits.append(bits)
        
    sorteios_possiveis = set(range(len(comb_bits)))
    bilhetes_escolhidos = []
    
    # Pré-cálculo de Cobertura usando Bitwise 
    cobertura = []
    for b in comb_bits:
        cobre = set()
        for j, s in enumerate(comb_bits):
            if (b & s).bit_count() >= garantia:
                cobre.add(j)
        cobertura.append(cobre)
        
    # Otimização Gulosa
    while sorteios_possiveis:
        melhor_idx = -1
        max_cobertos = -1
        
        for i, cobre_set in enumerate(cobertura):
            qtd_coberta = len(cobre_set.intersection(sorteios_possiveis))
            if qtd_coberta > max_cobertos:
                max_cobertos = qtd_coberta
                melhor_idx = i
                
        bilhetes_escolhidos.append(list(todas_comb_15[melhor_idx]))
        sorteios_possiveis -= cobertura[melhor_idx] 
        
    return bilhetes_escolhidos
def motor_garantia_exata_dinamica(ia, orcamento, conf_calc):
    """
    Versão Absoluta: Usa Teoria dos Conjuntos para 100% de Garantia.
    Testa a verba em cascata (15 -> 14 -> 13) e gera a matriz inquebrável.
    """
    dezenas_ia = sorted(ia['matriz_base'])
    qtd_dezenas = len(dezenas_ia)
    
    if qtd_dezenas <= 15:
        return False, [], "Matriz muito pequena para redução matemática."
        
    # Trava de Segurança: Calcular matrizes gigantes (21+ dezenas) ao vivo trava servidores.
    # O limite de 20 dezenas garante que o Streamlit rode liso.
    if qtd_dezenas > 20:
        return False, [], f"Matriz de {qtd_dezenas} dezenas exige hardware avançado para garantir 100%. Acionando Plano B (Ortogonal)."

    # 🚀 A CASCATA DE VERBA
    for garantia_alvo in [15, 14, 13]:
        
        # Gera a teia matemática 100% garantida (A função acima faz o trabalho pesado)
        jogos_reduzidos = gerar_fechamento_matematico(dezenas_ia, garantia_alvo)
        custo_fechamento = len(jogos_reduzidos) * 3.50
        
        # Se a verba bater, ele aprova o lote e envia para a fila
        if custo_fechamento <= orcamento and custo_fechamento > 0:
            msg = f"Matemática Reduzida: Garantia 100% INQUEBRÁVEL de {garantia_alvo} pts. ({len(jogos_reduzidos)} jogos cirúrgicos de 15 dezenas)."
            return True, jogos_reduzidos, msg
            
    return False, [], "Verba insuficiente para o Fechamento 100% Exato. Acionando Plano B (Ortogonal)."

def calcular_temperatura_e_confianca(historico, estrategia_atual, pontuacao_estrategias=None):
    """
    Calcula a temperatura do jogo. Gera o laudo TEÓRICO (Instinto Inicial).
    Este laudo será auditado e pode ser sobreposto pelo Córtex Estratégico.
    """
    if not historico:
        return 18, 0.50, "Histórico vazio. Usando matriz base de 18 dezenas por segurança.", {}

    # 1. Análise de Volatilidade e Quentes
    ultimos_10 = historico[-10:]
    todas_dezenas = [d for jogo in ultimos_10 for d in jogo['dezenas']]
    contagem = Counter(todas_dezenas)
    media_freq = sum(contagem.values()) / 25
    dezenas_quentes = [num for num, freq in contagem.items() if freq > media_freq]
    
    # 2. Identificação do Ciclo Faltante (CORRIGIDO: Leitura para frente)
    ciclo_atual = set()
    for jogo in historico:
        # Atualiza o ciclo com as dezenas do concurso
        ciclo_atual.update(jogo['dezenas'])
        # Se bater 25, o ciclo fecha e reinicia no próximo concurso
        if len(ciclo_atual) == 25:
            ciclo_atual = set()
            
    # As ausentes são as que não estão no ciclo atual
    dezenas_ausentes_ciclo = [d for d in range(1, 26) if d not in ciclo_atual]
    qtd_ausentes = len(dezenas_ausentes_ciclo)
    
    # IMPORTANTE: Se o ciclo acabou de fechar (0 ausentes), significa que no próximo
    # concurso teremos um ciclo NOVO (25 ausentes). 
    if qtd_ausentes == 0:
        qtd_ausentes = 25

    # 3. Cálculo de Desempenho Histórico da Estratégia
    score_estrategia = 11.0
    if pontuacao_estrategias and estrategia_atual in pontuacao_estrategias:
        dado_memoria = pontuacao_estrategias[estrategia_atual]
        if isinstance(dado_memoria, dict) and "usos" in dado_memoria and dado_memoria["usos"] > 0:
            score_estrategia = dado_memoria["pontos"] / dado_memoria["usos"]
        elif isinstance(dado_memoria, (int, float)):
            score_estrategia = float(dado_memoria)

    # 4. INSTINTO TEÓRICO (Hipótese Base) - SINCRONIZADO COM O CÓRTEX
    # Se faltam 3 dezenas ou menos, a IA ignora a seleção do painel e FORÇA a teoria do Ciclo.
    if qtd_ausentes <= 3:
        estrategia_atual = "Ciclo"
        tamanho_matriz = 20 # Proteção máxima de interface (NUNCA acima de 20 para evitar erro removeChild)
        motivo_tamanho = f"Alerta Máximo: Fechamento iminente ({qtd_ausentes} ausentes). A IA ativou o Gatilho de Adrenalina para o Ciclo. Sugestão: 20 dezenas."
        
    elif estrategia_atual == "Ciclo":
        if qtd_ausentes <= 7: tamanho_matriz, motivo_tamanho = 19, f"Teoria do Ciclo: Reta final ({qtd_ausentes} ausentes). Sugestão: 19 dezenas."
        else: tamanho_matriz, motivo_tamanho = 18, f"Teoria do Ciclo: Cenário inicial ({qtd_ausentes} ausentes). Sugestão enxuta: 18 dezenas."
            
    elif estrategia_atual == "Simetria":
        if score_estrategia >= 12.5: tamanho_matriz, motivo_tamanho = 18, f"Teoria Simétrica: Assertividade alta ({score_estrategia:.1f} pts). Sugestão: 18 dezenas."
        else: tamanho_matriz, motivo_tamanho = 20, f"Teoria Simétrica: Volatilidade. Sugestão defensiva: 20 dezenas."
            
    elif estrategia_atual == "Reversao":
        if score_estrategia >= 12.0: tamanho_matriz, motivo_tamanho = 19, f"Teoria da Reversão: Confiança em zebras ({score_estrategia:.1f} pts). Sugestão: 19 dezenas."
        elif score_estrategia < 10.5: tamanho_matriz, motivo_tamanho = 20, f"Teoria da Reversão: Risco extremo. Sugestão de defesa: 20 dezenas." 
        else: tamanho_matriz, motivo_tamanho = 20, f"Teoria da Reversão: Padrão. Sugestão: 20 dezenas." 
        
    else: # Tendencia
        if score_estrategia >= 12.8: tamanho_matriz, motivo_tamanho = 18, f"Teoria da Tendência: Padrão forte ({score_estrategia:.1f} pts). Sugestão: 18 dezenas."
        elif score_estrategia < 11.2: tamanho_matriz, motivo_tamanho = 20, f"Teoria da Tendência: Desempenho em queda. Sugestão de resgate: 20 dezenas." 
        else: tamanho_matriz, motivo_tamanho = 19, f"Teoria da Tendência: Cenário estável. Sugestão: 19 dezenas."
    # 5. CÁLCULO DA TAXA DE CONFIANÇA
    fator_quentes = min(len(dezenas_quentes) / 15, 1.0)
    fator_ia = min(max((score_estrategia - 8.0) / 3.0, 0.0), 1.0) 
    taxa_confianca = max(min((fator_quentes * 0.4) + (fator_ia * 0.6), 1.0), 0.1)

    detalhes = {"dezenas_quentes": len(dezenas_quentes), "ausentes_ciclo": qtd_ausentes, "score_ia": score_estrategia}
    return tamanho_matriz, taxa_confianca, motivo_tamanho, detalhes
def exibir_card_volante(jogo, indice):
    dezenas = jogo.get('dezenas', [])
    estrategia = jogo.get('estrategia', 'Padrão').replace("🧬", "🍀")
    alvo = jogo.get('concurso_alvo', 'N/A')
    dna = jogo.get('dna', 'DNA não calculado').replace("🧬", "🍀")
    
    html = f"""
    <div style="background-color: #ffffff; border-radius: 12px; padding: 20px; box-shadow: 0 4px 10px rgba(147,0,137,0.1); margin-bottom: 20px; border-left: 8px solid #930089; font-family: sans-serif;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f0f0f0; padding-bottom: 10px; margin-bottom: 15px;">
            <div style="font-weight: 900; color: #930089; font-size: 18px;">🎫 JOGO {indice:02d}</div>
            <div style="background-color: #930089; color: white; padding: 5px 12px; border-radius: 20px; font-size: 13px; font-weight: bold; letter-spacing: 0.5px;">{len(dezenas)} DEZENAS</div>
        </div>
        <div style="font-size: 13px; color: #7f8c8d; margin-bottom: 20px; display: flex; justify-content: space-between;">
            <span><strong style="color: #930089;">Alvo:</strong> {alvo}</span>
            <span><strong style="color: #930089;">Tática:</strong> {estrategia}</span>
        </div>
        <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; max-width: 260px; margin: 0 auto; background-color: #fdf5ff; padding: 15px; border-radius: 10px; border: 1px solid #eccbff;">
    """
    
    for i in range(1, 26):
        if i in dezenas:
            html += f'<div style="width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; border-radius: 50%; font-size: 16px; font-weight: bold; color: #ffffff; background-color: #930089; box-shadow: 0 2px 5px rgba(147,0,137,0.4);">{i:02d}</div>'
        else:
            html += f'<div style="width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; border-radius: 50%; font-size: 16px; font-weight: 600; color: #b2bec3; background-color: #ffffff; border: 1px solid #dfe6e9;">{i:02d}</div>'
            
    html += f"""
        </div>
        <div style="margin-top: 15px; font-size: 11px; color: #930089; text-align: center; font-weight: bold;">{dna}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# =====================================================================
# CONFIGURAÇÃO E LOGIN (100% ROXO LOTOFÁCIL)
# =====================================================================
st.set_page_config(page_title="LotoMatrix PRO", page_icon="🍀", layout="wide")

st.markdown("""
<style>
    :root { --roxo: #930089; --roxo-hover: #7a0072; }
    
    /* FUNDO GERAL */
    .stApp { background-color: #f4f6f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* ABAS FLUTUANTES 100% ROXAS */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: #ffffff; padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 10px 20px; background-color: #f8f9fa; border: 1px solid #e9ecef; transition: all 0.3s ease; }
    .stTabs [aria-selected="true"] { background-color: var(--roxo) !important; color: white !important; border: none; box-shadow: 0 4px 10px rgba(147,0,137,0.3); }
    
    /* PAINÉIS, MÉTRICAS E ALERTAS ROXOS */
    div[data-testid="stMetric"] { background-color: white; padding: 20px; border-radius: 12px; border-left: 6px solid var(--roxo); box-shadow: 0 4px 6px rgba(0,0,0,0.04); }
    div[data-testid="stAlert"] { background-color: #fdf5ff !important; border-left: 5px solid var(--roxo) !important; color: #333 !important; border-radius: 8px !important; }
    
    /* BOTÕES (GERAR, SALVAR) */
    button[kind="primary"] { background-color: var(--roxo) !important; border: none !important; border-radius: 8px !important; font-weight: bold !important; color: white !important; box-shadow: 0 4px 10px rgba(147,0,137,0.4) !important; transition: all 0.3s ease !important; }
    button[kind="primary"]:hover { background-color: var(--roxo-hover) !important; transform: translateY(-2px); }
    
    /* TELA DE LOGIN PREMIUM */
    .login-box { max-width: 420px; margin: 80px auto; padding: 40px; background: white; border-radius: 16px; border-top: 6px solid var(--roxo); box-shadow: 0 10px 30px rgba(147,0,137,0.15); text-align: center; }
    .login-title { color: var(--roxo); font-weight: 900; font-size: 26px; margin-bottom: 5px; }
    .login-sub { color: #666; font-size: 14px; margin-bottom: 25px; }
</style>
""", unsafe_allow_html=True)

if 'auth' not in st.session_state: 
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("""
    <div class='login-box'>
        <div class='login-title'>🍀 LotoMatrix PRO</div>
        <div class='login-sub'>Autenticação de Segurança</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        senha = st.text_input("Senha de Acesso", type="password", placeholder="Digite sua senha...", label_visibility="collapsed")
        if st.button("ENTRAR NO SISTEMA", type="primary", use_container_width=True):
            if senha == "777": # Trocque pela sua senha real
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Acesso Negado! Senha incorreta.")
    st.stop()

# =====================================================================
# MÓDULO MATEMÁTICO: PREMIAÇÃO MÚLTIPLA DA CAIXA
# =====================================================================
def calcular_premio_multiplo(tamanho, acertos, v11=7.0, v12=14.0, v13=35.0, v14=1500.0, v15=1500000.0):
    """Calcula o rateio exato para apostas simples e múltiplas com os novos valores base."""
    if acertos < 11: return 0.0
    premio = 0.0
    
    # Regra oficial da Caixa Econômica
    if tamanho == 15:
        if acertos == 11: premio = v11
        elif acertos == 12: premio = v12
        elif acertos == 13: premio = v13
        elif acertos == 14: premio = v14
        elif acertos == 15: premio = v15
    elif tamanho == 16:
        if acertos == 11: premio = 5 * v11
        elif acertos == 12: premio = (4 * v12) + (12 * v11)
        elif acertos == 13: premio = (3 * v13) + (13 * v12)
        elif acertos == 14: premio = (2 * v14) + (14 * v13)
        elif acertos == 15: premio = (1 * v15) + (15 * v14)
    
    return premio
# =====================================================================
# SENSOR DE DNA QUÂNTICO DA LOTOFÁCIL (FUNÇÃO DE APTIDÃO)
# =====================================================================
# =====================================================================
# SENSOR DE DNA QUÂNTICO DA LOTOFÁCIL (FUNÇÃO DE APTIDÃO)
# =====================================================================
def avaliar_dna_lotofacil(dezenas_geradas, dezenas_ultimo_sorteio):
    primos_set = {2, 3, 5, 7, 11, 13, 17, 19, 23}
    fibo_set = {1, 2, 3, 5, 8, 13, 21}
    mult3_set = {3, 6, 9, 12, 15, 18, 21, 24}

    pares = sum(1 for n in dezenas_geradas if n % 2 == 0)
    impares = len(dezenas_geradas) - pares
    primos = sum(1 for n in dezenas_geradas if n in primos_set)
    fibos = sum(1 for n in dezenas_geradas if n in fibo_set)
    mult3 = sum(1 for n in dezenas_geradas if n in mult3_set)
    repetidas = len(set(dezenas_geradas).intersection(set(dezenas_ultimo_sorteio)))

    tamanho = len(dezenas_geradas)
    score_padrao = 0

    # 🎯 1. ALVOS DINÂMICOS (Estrutura Base)
    if tamanho == 15:
        if impares in [7, 8]: score_padrao += 10
        if primos in [4, 5, 6]: score_padrao += 10
        if fibos in [4, 5]: score_padrao += 10
        if mult3 in [4, 5, 6]: score_padrao += 10
        if repetidas in [8, 9, 10]: score_padrao += 15 
    elif tamanho >= 16:
        if impares in [7, 8, 9]: score_padrao += 10
        if primos in [5, 6, 7]: score_padrao += 10
        if fibos in [4, 5, 6]: score_padrao += 10
        if mult3 in [5, 6, 7]: score_padrao += 10
        if repetidas in [9, 10, 11]: score_padrao += 15

    # 🕸️ 2. TEIA DE CORRELAÇÃO (Bônus Magnético Apriori)
    par_ouro = st.session_state.get('par_ouro', None)
    if par_ouro and par_ouro[0] in dezenas_geradas and par_ouro[1] in dezenas_geradas:
        score_padrao += 25 

    # 🚫 3. VAZIOS DE LINHA E COLUNA (Filtro Cartesiano)
    # Lapeia o volante de 5x5 e identifica anomalias geométricas de abismos.
    linhas = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    colunas = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for n in dezenas_geradas:
        linhas[(n - 1) // 5 + 1] += 1
        colunas[(n - 1) % 5 + 1] += 1
    
    linhas_vazias = sum(1 for v in linhas.values() if v == 0)
    colunas_vazias = sum(1 for v in colunas.values() if v == 0)
    # Punição matemática letal: a IA vai expurgar jogos que deixam corredores vazios
    if linhas_vazias > 0: score_padrao -= (linhas_vazias * 80)
    if colunas_vazias > 0: score_padrao -= (colunas_vazias * 80)

    # 🚫 4. BLOQUEIO DE SEQUENCIAMENTO EXTREMO (Filtro Anti-Escadinha)
    maior_seq = 1
    seq_atual = 1
    dezenas_ordenadas = sorted(dezenas_geradas)
    for i in range(1, len(dezenas_ordenadas)):
        if dezenas_ordenadas[i] == dezenas_ordenadas[i-1] + 1:
            seq_atual += 1
            if seq_atual > maior_seq: maior_seq = seq_atual
        else:
            seq_atual = 1
    # Punição severa se o bilhete formar uma "cobra" de 7 ou mais números grudados
    if maior_seq >= 7: score_padrao -= 100

    # ⚖️ 5. MASSA GRAVITACIONAL (Curva de Gauss da Soma)
    soma_total = sum(dezenas_geradas)
    media_soma = soma_total / tamanho
    # Normalizamos o intervalo Gaussiano: se 180~215 é o ideal para 15 dezenas, 
    # a média perfeita por dezena é de 12.0 a 14.33. Isso faz a IA funcionar perfeitamente
    # mesmo se você decidir gerar bilhetes múltiplos (16+ dezenas).
    if 12.0 <= media_soma <= 14.33:
        score_padrao += 15
    else:
        # Se a soma estourar a normalidade estatística, corta a força do bilhete
        score_padrao -= 30

    # 🏷️ CARIMBO VISUAL DO DNA (Agora mostrando Soma Total e Alertas)
    dna_texto = f"🧬 {impares} Ímp • {pares} Par • {primos} Pri • {fibos} Fib • {mult3} Múlt • {repetidas} Rep • Σ {soma_total}"
    
    # Flags visuais inseridas no bilhete gerado, caso a IA (num caso extremo sem saída) seja obrigada a usar um desses padrões.
    if maior_seq >= 7: 
        dna_texto += " ⚠️ SeqExtrema"
    if linhas_vazias > 0 or colunas_vazias > 0: 
        dna_texto += " ⚠️ VaziosNoVolante"

    return score_padrao, dna_texto
# =====================================================================
# BLINDAGEM DE MEMÓRIA E SANITIZAÇÃO ABSOLUTA
# =====================================================================
def sanitizar_dados(d):
    if "banca" not in d: d["banca"] = 0.0
    if "historico_dados" not in d: d["historico_dados"] = []
    if "jogos_salvos" not in d: d["jogos_salvos"] = []
    if "matriz_viva_atual" not in d: d["matriz_viva_atual"] = []
    if "ia_memoria" not in d: 
        d["ia_memoria"] = {
            "Tendencia": {"usos": 0, "pontos": 0}, 
            "Reversao": {"usos": 0, "pontos": 0},
            "Ciclo": {"usos": 0, "pontos": 0},
            "Simetria": {"usos": 0, "pontos": 0}
        }
    
    for j in d["jogos_salvos"]:
        if "id" not in j: j["id"] = str(uuid.uuid4())
        if "concurso_alvo" not in j: j["concurso_alvo"] = "Legado"
        if "tamanho" not in j: j["tamanho"] = len(j.get("dezenas", []))
        if "status" not in j: j["status"] = "Aguardando Sorteio"
        if "acertos" not in j: j["acertos"] = 0
        if "estrategia" not in j: j["estrategia"] = "Tendencia"
        if "justificativa" not in j: j["justificativa"] = "Jogo recuperado."
    return d

if 'data' not in st.session_state:
    st.session_state.data = sanitizar_dados({})

# =====================================================================
# FUNÇÕES DE CALLBACK (Ações Dinâmicas)
# =====================================================================
def cb_depositar():
    valor = st.session_state.get("input_aporte", 0.0)
    if valor > 0:
        st.session_state.data['banca'] += valor
        st.toast(f"R$ {valor:.2f} creditados na banca!", icon="💰")

def cb_excluir_jogo(jogo_id):
    st.session_state.data['jogos_salvos'] = [j for j in st.session_state.data['jogos_salvos'] if j.get('id') != jogo_id]
    st.toast("Bilhete deletado.", icon="🗑️")

def cb_excluir_todos():
    st.session_state.data['jogos_salvos'] = []
    st.toast("Fila de espera limpa.", icon="🧹")

def cb_carregar_cofre():
    file = st.session_state.uploader_cofre
    if file:
        try:
            st.session_state.data = sanitizar_dados(json.load(file))
            st.toast("Cofre sincronizado com sucesso!", icon="✅")
        except Exception as e: st.error(f"Erro ao ler JSON: {e}")

# =====================================================================
# CÉREBRO PREDITIVO (Score Composto Profissional - Correção de Pesos)
# =====================================================================
from collections import Counter

def raciocinio_total_ia(historico, memoria, estrategia_instinto="Tendencia", tamanho_instinto=18):
    if not historico: return None
    
    # 🧠 1. DADOS DE BASE DA LOTOFÁCIL
    historico_recente = historico[-50:] if len(historico) >= 50 else historico
    freq_recente = Counter([n for h in historico_recente for n in h['dezenas']])
    
    ultimos_10 = historico[-10:] if len(historico) >= 10 else historico
    media_soma = sum([sum(h['dezenas']) for h in ultimos_10]) / len(ultimos_10) if ultimos_10 else 190
    
    primos_lista = [2, 3, 5, 7, 11, 13, 17, 19, 23]
    moldura_lista = [1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25]
    media_impares = sum([sum(1 for n in h['dezenas'] if n % 2 != 0) for h in ultimos_10]) / len(ultimos_10) if ultimos_10 else 8
    media_primos = sum([sum(1 for n in h['dezenas'] if n in primos_lista) for h in ultimos_10]) / len(ultimos_10) if ultimos_10 else 5
    media_moldura = sum([sum(1 for n in h['dezenas'] if n in moldura_lista) for h in ultimos_10]) / len(ultimos_10) if ultimos_10 else 10

    # 🧠 2. MAPEAMENTO DE ATRASOS E CICLO
    atrasos = {n: 0 for n in range(1, 26)}
    dezena_encontrada = {n: False for n in range(1, 26)}
    for h in reversed(historico):
        for n in range(1, 26):
            if n in h['dezenas']: dezena_encontrada[n] = True
            elif not dezena_encontrada[n]: atrasos[n] += 1

    ciclo_atual = set()
    jogos_ciclo = 0
    for h in historico:
        ciclo_atual.update(h['dezenas'])
        jogos_ciclo += 1
        if len(ciclo_atual) == 25:
            ciclo_atual = set() 
            jogos_ciclo = 0
    faltam_ciclo = sorted(list(set(range(1, 26)) - ciclo_atual))

    # 🧠 3. MOTOR DE TAMANHO (VOLATILIDADE E DINÂMICA DE CICLO)
    # A IA analisa o nível de anomalia dos últimos 5 concursos (Mantido para o texto do painel não quebrar)
    repeticoes_recentes = []
    try:
        for j in range(1, min(6, len(historico))):
            rep = len(set(historico[-j]['dezenas']) & set(historico[-(j+1)]['dezenas']))
            repeticoes_recentes.append(rep)
        media_volatilidade = sum(repeticoes_recentes) / len(repeticoes_recentes) if repeticoes_recentes else 9.0
    except:
        media_volatilidade = 9.0

    # === NOVA DECISÃO DE TAMANHO (DESTRAVADA BASEADA NO CICLO) ===
    qtd_faltam = len(faltam_ciclo)
    
    if qtd_faltam <= 3:
        qtd_matriz = 17  # Fim de ciclo, muita previsibilidade, matriz cirúrgica
    elif 4 <= qtd_faltam <= 6:
        qtd_matriz = 18  # Meio de ciclo, padrão
    elif 7 <= qtd_faltam <= 9:
        qtd_matriz = 19  # Início de ciclo, precisa de mais margem
    else:
        qtd_matriz = 20  # Caos total, abre a rede no máximo permitido
        
    # Override de emergência se você forçar um tamanho manual na interface
    if tamanho_instinto and (qtd_matriz < 17 or qtd_matriz > 20):
        qtd_matriz = max(17, min(tamanho_instinto, 20))
        
    # Override de emergência se o usuário forçar algo fora do padrão
    if tamanho_instinto and (qtd_matriz < 17 or qtd_matriz > 20):
        qtd_matriz = max(17, min(tamanho_instinto, 20))

    # 🧠 4. SCORE COMPOSTO PROFISSIONAL (A Fórmula Universal)
    pesos_reais = {}
    for x in range(1, 26):
        # Peso 1: Frequência Básica (Quentes)
        forca_frequencia = freq_recente.get(x, 0)
        
        # Peso 2: Atraso (Zebras). Multiplicado por 3 para equiparar à frequência
        forca_atraso = atrasos.get(x, 0) * 3 
        
        # Peso 3: Prioridade de Ciclo (Sniper)
        forca_ciclo = 500 if x in faltam_ciclo and len(faltam_ciclo) <= 5 else 0
        
        # Score Absoluto da Dezena
        pesos_reais[x] = forca_frequencia + forca_atraso + forca_ciclo

    # 🧠 5. SELEÇÃO DA MATRIZ BASE
    # O ranking absoluto seleciona a elite baseada na fórmula universal matemática
    dezenas_ordenadas = sorted(range(1, 26), key=lambda n: pesos_reais[n], reverse=True)
    matriz_base = sorted(dezenas_ordenadas[:qtd_matriz])

    # 🧠 6. NOMECLATURAS E NARRATIVA DO PAINEL
    estrategia_ativa = "Score Composto"
    if len(faltam_ciclo) <= 5: 
        tatic_desc = "Prioridade Máxima: Fechamento de Ciclo."
        cod_est = "Ciclo"
    elif media_volatilidade < 8.0 or media_volatilidade > 10.0:
        tatic_desc = "Alta Volatilidade: Pesos de Reversão priorizados."
        cod_est = "Reversao"
    else:
        tatic_desc = "Cenário Normal: Tendência Absoluta em vigor."
        cod_est = "Tendencia"

    texto_tamanho = f"Avaliando a volatilidade de {media_volatilidade:.1f} repetições, a malha foi cravada em {qtd_matriz} dezenas."
    motivo_est = f"DIRETRIZ: {tatic_desc} ANÁLISE: Carga de pesos distribuída matematicamente. GEOMETRIA: {texto_tamanho}"
    alvo = (historico[-1]['concurso'] + 1) if historico else 1

    # RECUPERANDO A VARIÁVEL 'pesos_reais' INTACTA PARA OS SEUS GERADORES VOLTAREM A FUNCIONAR
    return {
        "estrategia": estrategia_ativa, "cod_estrategia": cod_est, "estrategia_usada": cod_est, "motivo_est": motivo_est, 
        "pesos": pesos_reais, "freq": freq_recente, "atrasos": atrasos, "ciclo_tam": jogos_ciclo, "faltam_ciclo": faltam_ciclo,
        "soma": media_soma, "impares": media_impares, "primos": media_primos, "moldura": media_moldura, 
        "alvo": alvo, "qtd_matriz": qtd_matriz, "matriz_base": matriz_base, "perf": {}, "volatilidade": media_volatilidade
    }
# =====================================================================
# INTERFACE PRINCIPAL
# =====================================================================
st.markdown("<h2 style='text-align: center; color: #930089; font-weight: 900;'>🍀 LotoMatrix PRO - Agente Autônomo</h2>", unsafe_allow_html=True)
tabs = st.tabs(["📂 1. Banco de Dados", "🧠 2. Cérebro Analítico (IA)", "🤖 3. Geração Autônoma", "📜 4. Fila de Sorteio", "🏆 5. Sincronização e Entrada"])
# --- TAB 1: BANCO DE DADOS E BANCA ---
with tabs[0]:
    st.markdown("### 💾 Central de Dados e Ajuste Financeiro")

    # =====================================================================
    # 1. INICIALIZAÇÃO DE SEGURANÇA (Garante que as variáveis existam no JSON)
    # =====================================================================
    if "historico_aportes" not in st.session_state.data: 
        st.session_state.data["historico_aportes"] = 0.0
    if "historico_saques" not in st.session_state.data: 
        st.session_state.data["historico_saques"] = 0.0

    # Lógica de Cálculo da Fórmula de Ouro
    banca_atual = st.session_state.data.get("banca", 0.0)
    t_aportes = st.session_state.data["historico_aportes"]
    t_saques = st.session_state.data["historico_saques"]
    resultado_global = (banca_atual + t_saques) - t_aportes

    # =====================================================================
    # 2. PAINEL DE RESUMO HISTÓRICO (O GRANDE RAIO-X)
    # =====================================================================
    with st.container(border=True):
        st.markdown("#### 📈 Balanço Financeiro Global (ROI)")
        ind1, ind2, ind3, ind4 = st.columns(4)
        
        ind1.metric("💰 Banca Atual", f"R$ {banca_atual:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        ind2.metric("📥 Total Aportado", f"R$ {t_aportes:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        ind3.metric("📤 Total Sacado", f"R$ {t_saques:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        # Indicador visual de Lucro/Prejuízo
        str_res = f"R$ {resultado_global:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        if resultado_global > 0:
            ind4.metric("📊 Resultado do Projeto", str_res, "Lucro Histórico")
        elif resultado_global < 0:
            ind4.metric("📊 Resultado do Projeto", str_res, "Prejuízo Histórico")
        else:
            ind4.metric("📊 Resultado do Projeto", "R$ 0,00", "Empate / Ponto Zero")

    # =====================================================================
    # 3. CONTROLES OPERACIONAIS E BANCO DE DADOS
    # =====================================================================
    c1, c2 = st.columns(2)
    
    with c1:
        with st.container(border=True):
            st.markdown("**📂 Gerenciamento do Cofre (Backup)**")
            st.file_uploader("📥 Carregar Arquivo Cofre.json", type="json", key="uploader_cofre", on_change=cb_carregar_cofre)
            st.info(f"📊 **Concursos Oficiais Salvos:** {len(st.session_state.data.get('historico_dados', []))}.")
            st.download_button("📤 Baixar Backup Consolidado", json.dumps(st.session_state.data), "Cofre.json", type="primary", use_container_width=True)
            
    with c2:
        with st.container(border=True):
            st.markdown("**💸 Movimentação de Caixa**")
            
            # Um único campo de valor para facilitar
            valor_mov = st.number_input("Digite o Valor (R$):", min_value=0.0, step=10.0, key="input_movimentacao")
            
            col_dep, col_sac = st.columns(2)
            
            with col_dep:
                if st.button("📥 DEPOSITAR", use_container_width=True, type="primary"):
                    if valor_mov > 0:
                        st.session_state.data["banca"] = st.session_state.data.get("banca", 0.0) + valor_mov
                        st.session_state.data["historico_aportes"] += valor_mov
                        salvar_dados(st.session_state.data)
                        st.rerun()
                        
            with col_sac:
                if st.button("📤 SACAR", use_container_width=True):
                    if valor_mov > 0:
                        if valor_mov <= st.session_state.data.get("banca", 0.0):
                            st.session_state.data["banca"] -= valor_mov
                            st.session_state.data["historico_saques"] += valor_mov
                            salvar_dados(st.session_state.data)
                            st.rerun()
                        else:
                            st.error("❌ Saldo insuficiente na banca para este saque.")
            
            st.divider()
            
            # --- BOTÃO DE RESET EXCLUSIVAMENTE FINANCEIRO ---
            # Este botão zera o ROI e o Financeiro, mas NÃO toca na IA nem nos dados.
            if st.button("🔄 ZERAR FINANCEIRO E ROI (MANTER IA)", use_container_width=True, type="secondary"):
    
                # 1. Reset da Banca e Fluxo de Caixa
                st.session_state.data["banca"] = 0.0
                st.session_state.data["historico_aportes"] = 0.0
                st.session_state.data["historico_saques"] = 0.0
    
                # 2. Reset do Track Record (A contabilidade que alimenta a Aba 2)
                st.session_state.data["ledger_track"] = {
                    "bilhetes": 0, "premiados_geral": 0, "elite": 0, "custo": 0.0, "retorno": 0.0
                }
    
                # 3. Reseta a flag 'ledger_ok' para que a Aba 2 entenda que o histórico de contagem foi zerado
                for j in st.session_state.data.get("jogos_salvos", []):
                    j["ledger_ok"] = False
        
                # 4. Salva apenas as alterações financeiras
                salvar_dados(st.session_state.data)
    
                st.success("Financeiro e ROI zerados com sucesso. A IA e os dados históricos permanecem intactos.")
                st.rerun()

# --- TAB 2: CÉREBRO ANALÍTICO ---
with tabs[1]:
    exibir_mini_painel_financeiro()
    
    # =====================================================================
    # 🏆 PAINEL DE PERFORMANCE REAL (TRACK RECORD PERMANENTE)
    # =====================================================================
    st.markdown("<h3 style='color: #1f77b4;'>📈 Track Record: Performance Histórica da Máquina</h3>", unsafe_allow_html=True)
    
    # 1. Cria o Cofre Imutável com contadores individuais para a Retrospectiva
    if "ledger_track" not in st.session_state.data:
        st.session_state.data["ledger_track"] = {
            "bilhetes": 0, "premiados_geral": 0, "elite": 0, "custo": 0.0, "retorno": 0.0,
            "pts_11": 0, "pts_12": 0, "pts_13": 0, "pts_14": 0, "pts_15": 0, "soma_total_acertos": 0
        }
        
    # 2. Varredura Inteligente: Suga os dados e joga no Cofre
    precisa_salvar = False
    for j in st.session_state.data.get("jogos_salvos", []):
        if j.get("status") != "Aguardando Sorteio" and not j.get("ledger_ok", False):
            
            # Atualiza financeiros e volumetria
            st.session_state.data["ledger_track"]["bilhetes"] += 1
            pts = j.get("acertos", 0)
            
            st.session_state.data["ledger_track"]["soma_total_acertos"] += pts
            
            if pts == 11: st.session_state.data["ledger_track"]["pts_11"] += 1
            if pts == 12: st.session_state.data["ledger_track"]["pts_12"] += 1
            if pts == 13: st.session_state.data["ledger_track"]["pts_13"] += 1
            if pts == 14: 
                st.session_state.data["ledger_track"]["pts_14"] += 1
                st.session_state.data["ledger_track"]["elite"] += 1
            if pts == 15: 
                st.session_state.data["ledger_track"]["pts_15"] += 1
                st.session_state.data["ledger_track"]["elite"] += 1
                
            if pts >= 11:
                st.session_state.data["ledger_track"]["premiados_geral"] += 1
                
            custo = 56.0 if j.get("tamanho", 15) == 16 else 3.50
            st.session_state.data["ledger_track"]["custo"] += custo
            st.session_state.data["ledger_track"]["retorno"] += j.get("premio_valor", 0.0)
            
            # Carimba para não duplicar
            j["ledger_ok"] = True
            precisa_salvar = True
            
    if precisa_salvar:
        salvar_dados(st.session_state.data)

    # 3. Leitura dos Dados do Cofre Permanente
    ledger = st.session_state.data["ledger_track"]
    qtd_conferidos = ledger["bilhetes"]
    
    if qtd_conferidos > 0:
        win_rate_geral = (ledger["premiados_geral"] / qtd_conferidos) * 100
        if ledger["elite"] > 0:
            frequencia_elite = int(qtd_conferidos / ledger["elite"])
            texto_freq_elite = f"1 a cada {frequencia_elite} bilhetes"
        else:
            texto_freq_elite = "Caçando a Elite..."
    else:
        win_rate_geral = 0.0
        texto_freq_elite = "Aguardando Sorteios"

    lucro_prejuizo_real = ledger["retorno"] - ledger["custo"]
    roi_real = (lucro_prejuizo_real / ledger["custo"]) * 100 if ledger["custo"] > 0 else 0.0

    # 4. Renderização do Painel de Track Record
    with st.container(border=True):
        col_trk1, col_trk2, col_trk3, col_trk4 = st.columns(4)
        col_trk1.metric("🎟️ Bilhetes Operados", f"{qtd_conferidos}")
        col_trk2.metric("🎯 Win Rate (Prêmios)", f"{win_rate_geral:.1f}%")
        col_trk3.metric("💎 Freq. de Elite", texto_freq_elite)
        
        delta_color = "normal" if lucro_prejuizo_real >= 0 else "inverse"
        col_trk4.metric("📈 ROI Financeiro", f"{roi_real:.1f}%", 
                        delta=f"R$ {lucro_prejuizo_real:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), 
                        delta_color=delta_color)
        
    st.divider()

    # =====================================================================
    # --- RETROSPECTIVA CRÍTICA PERMANENTE (IMUNE A EXCLUSÕES) ---
    # =====================================================================
    st.markdown("#### 🎯 Retrospectiva Crítica dos Bilhetes (Cofre Histórico Absoluto)")
    
    avg_hits = ledger["soma_total_acertos"] / qtd_conferidos if qtd_conferidos > 0 else 0.0
    t11 = ledger["pts_11"]
    t12 = ledger["pts_12"]
    t13 = ledger["pts_13"]
    t14 = ledger["pts_14"]
    t15 = ledger["pts_15"]

    with st.container(border=True):
        cd_1, cd_2, cd_3, cd_4 = st.columns(4)
        cd_1.metric("Média de Acertos nos Bilhetes", f"{avg_hits:.2f} / 15", help="Média real nos bilhetes operados. A linha base aleatória é 9.00.")
        cd_2.metric("Bilhetes com 11-12 Pts", f"{t11 + t12} prêmios", delta=f"11 Pts: {t11} | 12 Pts: {t12}", delta_color="off")
        cd_3.metric("Bilhetes com 13 Pts", f"{t13} prêmios", help="Quantidade real de bilhetes premiados com 13 gravados no cofre.")
        cd_4.metric("Prêmios Máximos (14-15 Pts)", f"{t14 + t15} prêmios", delta=f"14 Pts: {t14} | 15 Pts: {t15}", delta_color="inverse")

    st.divider()
    
    # Daqui para baixo, você mantém o resto da sua Aba 2 intacta (Motores, Projeção Financeira, Matriz, etc).

    # =================================================================
    # 🔮 PAINEL BONITO: DESEMPENHO BRUTO DA MATRIZ BASE (GRUPO DE ELITE)
    # =================================================================
    with st.container(border=True):
        st.markdown("#### 🧬 Potencial Bruto: Força da Matriz Base")
        st.write("Avalia quantos pontos a matriz bruta atual (antes dos desdobramentos) teria segurado nos últimos 30 concursos.")
                
        historico_base = st.session_state.data.get("historico_dados", [])
        ultimos_30 = historico_base[-30:] if historico_base else []
                
        try:
            matriz_atual = set(ia['matriz_base']) 
            tamanho_matriz = len(matriz_atual)
                    
            if ultimos_30 and tamanho_matriz > 0:
                acertos_matriz = []
                        
                for sorteio in ultimos_30:
                    sorteio_set = set(sorteio['dezenas'])
                    hits = len(matriz_atual.intersection(sorteio_set))
                    acertos_matriz.append(hits)
                            
                media_acertos = sum(acertos_matriz) / len(acertos_matriz)
                freq_14_15 = sum(1 for x in acertos_matriz if x >= 14)
                        
                col_m1, col_m2, col_m3 = st.columns(3)
                        
                col_m1.metric(
                    label="Tamanho da Matriz", 
                    value=f"{tamanho_matriz} Dezenas", 
                    delta="Matriz Ativa"
                )
                col_m2.metric(
                    label="Média de Retenção", 
                    value=f"{media_acertos:.2f} / 15", 
                    help="Média de dezenas sorteadas que caíram DENTRO da matriz."
                )
                col_m3.metric(
                    label="Frequência de 14-15 Pts", 
                    value=f"{freq_14_15} vezes", 
                    delta="Nos últimos 30 concursos", 
                    delta_color="normal"
                )
                        
                st.caption(f"**Termómetro de Eficiência da Matriz (Média atual: {media_acertos:.1f} pontos)**")
                pct_eficiencia = min(media_acertos / 15.0, 1.0)
                st.progress(pct_eficiencia)
                        
        except Exception as e:
            st.info("Gere a estratégia da IA para visualizar o desempenho da Matriz Base.")
            
    # --- PAINEL DE CALIBRAÇÃO DO SCORE COMPOSTO ---
    st.markdown("#### ⚙️ Calibração Atual do Motor (Score Composto Profissional)")
    with st.container(border=True):
        c_e1, c_e2, c_e3, c_e4 = st.columns(4)
        c_e1.metric("🔥 Peso: Frequência", "x1.0", help="Multiplicador base para as dezenas mais quentes do momento.")
        c_e2.metric("🦓 Peso: Atraso (Zebra)", "x3.0", help="Multiplicador agressivo para forçar a entrada de zebras reais.")
                
        status_ciclo = "🚨 MÁXIMA" if len(ia['faltam_ciclo']) <= 5 else "Aguardando"
        c_e3.metric("🎯 Prioridade de Ciclo", status_ciclo, help="Ganha peso 500 caso o ciclo esteja a 5 dezenas ou menos do fim.")
        c_e4.metric("🌪️ Risco / Volatilidade", f"{ia.get('volatilidade', 9.0):.1f}", help="Define o tamanho da matriz baseada no caos dos últimos 5 sorteios.")
        
    st.markdown("#### 🔍 Dossiê Completo da Inteligência Artificial")
    top5_quentes = sorted(ia['freq'].items(), key=lambda x: x[1], reverse=True)[:5]
    str_quentes = ", ".join([f"{k:02d} ({v}x)" for k, v in top5_quentes])
        
    top5_atrasos = sorted(ia['atrasos'].items(), key=lambda x: x[1], reverse=True)[:5]
    str_atrasos = ", ".join([f"{k:02d} ({v} conc.)" for k, v in top5_atrasos])
        
    html_dossie = f"""
    <div style="background: linear-gradient(145deg, #ffffff, #f0f4f8); border-left: 6px solid #1f77b4; padding: 20px; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 4px 10px rgba(0,0,0,0.06); color: #2c3e50; font-family: sans-serif;">
        <div style="margin-bottom: 12px; font-size: 15px;"><strong>🔥 Top 5 Dezenas mais Quentes:</strong> <span style="color: #d32f2f; font-weight: 700; background: #ffebee; padding: 3px 8px; border-radius: 5px;">{str_quentes}</span></div>
        <div style="margin-bottom: 12px; font-size: 15px;"><strong>🧊 Top 5 Maiores Atrasos:</strong> <span style="color: #2e7d32; font-weight: 700; background: #e8f5e9; padding: 3px 8px; border-radius: 5px;">{str_atrasos}</span></div>
        <div style="font-size: 15px;"><strong>⏳ Status do Ciclo:</strong> Aberto há {ia['ciclo_tam']} concursos. <span style="color: #f57c00; font-weight: 700; background: #fff3e0; padding: 3px 8px; border-radius: 5px;">Faltam {len(ia['faltam_ciclo'])} dezenas para fechar: {ia['faltam_ciclo']}</span></div>
    </div>
    """
    st.markdown(html_dossie, unsafe_allow_html=True)

    # --- PAINEL DE DESEMPENHO DOS JOGOS ATIVOS ---
    jogos_ativos = [j for j in st.session_state.data["jogos_salvos"] if j.get('status') == "Aguardando Sorteio"]
    if jogos_ativos:
        st.markdown("---")
        dezenas_ativos = [n for j in jogos_ativos for n in j["dezenas"]]
        render_performance_grid(dezenas_ativos, "🧬 Dezenas que a IA selecionou para os seus Jogos Ativos")
    else:
        st.info("Nenhum jogo ativo na fila no momento.")

    # --- NOVO PAINEL DE PESOS ESTILIZADO ---
    st.markdown("#### ⚖️ Grade Dinâmica de Pesos Absolutos (Heatmap da IA)")
        
    html_pesos = "<div style='display: grid; grid-template-columns: repeat(5, 1fr); gap: 15px; font-family: sans-serif; margin-bottom: 30px;'>"
    for n in range(1, 26):
        p_val = ia['pesos'].get(n, 0.0)
        no_grupo = n in ia['matriz_base']
                
        bg_color = "linear-gradient(135deg, #d1e7dd 0%, #b3dac6 100%)" if no_grupo else "#fdfdfd"
        border_color = "#0f5132" if no_grupo else "#e2e8f0"
        text_color = "#0f5132" if no_grupo else "#475569"
        shadow = "box-shadow: 0 4px 6px rgba(0,0,0,0.08);" if no_grupo else "box-shadow: 0 2px 4px rgba(0,0,0,0.03);"
                
        label_elite = "<div style='background-color:#0f5132; color:white; font-size:10px; font-weight:bold; letter-spacing: 0.5px; padding:3px 0; border-radius:0 0 8px 8px; margin-top: 8px;'>ELITE</div>" if no_grupo else "<div style='height: 20px; margin-top: 8px;'></div>"
            
        html_pesos += f"<div style='background: {bg_color}; border: 1px solid {border_color}; {shadow} border-radius: 10px; text-align: center; color: {text_color}; display: flex; flex-direction: column; justify-content: space-between; overflow: hidden;'><div style='padding: 12px 10px 0 10px;'><span style='font-size: 24px; font-weight: 800;'>{n:02d}</span><br><span style='font-size: 13px; font-weight: 500; opacity: 0.9;'>Peso: {p_val:.1f}</span></div>{label_elite}</div>"
        
    html_pesos += "</div>"
    st.markdown(html_pesos, unsafe_allow_html=True)

else: st.warning("Aguardando inserção de dados do Cofre na Aba 1.")

# --- TAB 3: GERADOR AUTÔNOMO ---
with tabs[2]:
    exibir_mini_painel_financeiro()
    
    st.markdown("### 🚀 Engenharia Combinatória por Verba")
    
    # PAINEL DE GESTÃO DE BANCA
    with st.container(border=True):
        col_saldo, col_div, col_aporte = st.columns([1.5, 0.2, 2])
        
        with col_saldo:
            st.metric("💰 Saldo Disponível na Banca", f"R$ {st.session_state.data['banca']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        with col_aporte:
            st.markdown("#### ➕ Injetar Aporte na Operação")
            c_input, c_btn = st.columns([2, 1])
            with c_input:
                valor_aporte = st.number_input("Valor (R$):", min_value=1.0, step=10.0, label_visibility="collapsed", format="%.2f")
            with c_btn:
                if st.button("✅ Depositar", use_container_width=True):
                    st.session_state.data['banca'] += valor_aporte
                    st.session_state.data["historico_aportes"] = st.session_state.data.get("historico_aportes", 0.0) + valor_aporte
                    salvar_dados(st.session_state.data)
                    st.toast(f"Aporte de R$ {valor_aporte:.2f} realizado!", icon="💸")
                    st.rerun()

    if st.session_state.data["historico_dados"]:
        ia = raciocinio_total_ia(st.session_state.data["historico_dados"], st.session_state.data.get("ia_memoria", {}))
        
        st.markdown(f"#### 🎯 Setup de Disparo — Concurso Alvo: `{ia['alvo']}`")
        
        with st.container(border=True):
            orcamento = st.number_input("Defina o Teto Orçamentário para esta Geração (R$):", 
                                        min_value=3.5, 
                                        max_value=max(3.5, st.session_state.data['banca']), 
                                        step=3.5,
                                        help="O sistema tentará montar a melhor rede matemática possível sem ultrapassar este valor.")
            
            if st.button("🧬 DISPARAR MOTOR ORTOGONAL DE GERAÇÃO E FECHAMENTO", type="primary", use_container_width=True):
                if st.session_state.data['banca'] < orcamento:
                    st.error("Banca insuficiente para a operação. Faça um aporte.")
                else:
                    # =====================================================================
                    # 🧠 INJEÇÃO DO MOTOR MATEMÁTICO E CÁLCULO DE CONFIANÇA
                    # =====================================================================
                    historico_painel = st.session_state.data["historico_dados"]
                    estrategia_selecionada = ia.get('estrategia', 'Tendencia')
                    memoria_ia = st.session_state.data.get('ia_memoria', {})
                    
                    _, conf_calc, _, _ = calcular_temperatura_e_confianca(
                        historico_painel, estrategia_selecionada, memoria_ia
                    )

                    # =====================================================================
                    # 🛡️ PLANO A: GARANTIA MATEMÁTICA ABSOLUTA
                    # =====================================================================                   
                    # CHAVE DE FORÇAR: Se a chave estiver ligada, pulamos o Plano A
                    if st.session_state.get('forcar_motor', False):
                        sucesso_matematico = False
                        msg_status = "Modo Forçado: Motor Exato (Plano A) ignorado pelo usuário."
                    else:
                        sucesso_matematico, matriz_reduzida, msg_status = motor_garantia_exata_dinamica(ia, orcamento, conf_calc)
                

                    if sucesso_matematico:
                        gasto = 0.0
                        qtd_gerados = len(matriz_reduzida)
                        
                        for dezenas_jogo in matriz_reduzida:
                            tamanho_bilhete = len(dezenas_jogo)
                            custo_deste_bilhete = 56.0 if tamanho_bilhete == 16 else 3.50
                            gasto += custo_deste_bilhete
                            
                            st.session_state.data["jogos_salvos"].append({
                                "id": str(uuid.uuid4()), 
                                "concurso_alvo": ia['alvo'], 
                                "dezenas": sorted(list(dezenas_jogo)),
                                "tamanho": tamanho_bilhete, 
                                "estrategia": ia['cod_estrategia'], 
                                "justificativa": f"Matriz {ia['cod_estrategia']}. {msg_status}",
                                "status": "Aguardando Sorteio", 
                                "acertos": 0, 
                                "premio_valor": 0.0,
                                "matriz_origem": ia['matriz_base'],
                                "dna": "🧬 Fechamento Matemático 100% Garantido"
                            })
                            
                        st.session_state.data['banca'] -= gasto
                        salvar_dados(st.session_state.data)
                        
                        st.toast(f"✅ {qtd_gerados} jogos matemáticos criados.", icon="🚀")
                        st.success(f"**Garantia Matemática Ativada!** {msg_status} Custo Real: **R$ {gasto:.2f}**. Saldo restante: **R$ {st.session_state.data['banca']:.2f}**.")
                        st.rerun()

                    else:
                        # =====================================================================
                        # 🚀 SUPER PLANO B: MÁQUINA DE FORÇA BRUTA ORTOGONAL (SEM MONTE CARLO)
                        # =====================================================================
                        st.info(f"⚠️ **Orçamento Limitado:** {msg_status}") 
                        
                        historico_sets = {frozenset(h['dezenas']) for h in st.session_state.data['historico_dados']}
                        historico_oficial_sets = [set(h['dezenas']) for h in st.session_state.data['historico_dados']]
                        ultimo_sorteio = st.session_state.data["historico_dados"][-1]["dezenas"] if st.session_state.data["historico_dados"] else []
                        
                        jogos_neste_lote = [] 
                        gasto = 0.0
                        qtd_gerados = 0
                        
                        progresso_texto = st.empty()
                        barra_progresso = st.progress(0)
                        
                        tam_matriz = len(ia['matriz_base'])
                        
                        st.warning(f"⚡ **Motor Híbrido Ativado:** Matriz de {tam_matriz} dezenas. Acionando **Força Bruta Ortogonal**.")
                        progresso_texto.write("⏳ Gerando TODAS as combinações e passando na peneira genética... Aguarde.")
                        
                        universo_15 = [list(c) for c in itertools.combinations(ia['matriz_base'], 15)]
                        universo_16 = [list(c) for c in itertools.combinations(ia['matriz_base'], 16)] if tam_matriz >= 16 else []
                        
                        def filtrar_universo(universo):
                            pote = []
                            for candidato in universo:
                                candidato_set = set(candidato)
                                
                                if frozenset(candidato) in historico_sets: continue # Filtro 15 pontos exato
                                if any(len(candidato_set & sorteio_passado) >= 14 for sorteio_passado in historico_oficial_sets): continue
                                
                                max_c, atual_c = 1, 1
                                for i in range(1, len(candidato)):
                                    if candidato[i] == candidato[i-1] + 1:
                                        atual_c += 1
                                        max_c = max(max_c, atual_c)
                                    else: atual_c = 1
                                if max_c > 7: continue
                                
                                score_dna, dna_texto = avaliar_dna_lotofacil(candidato, ultimo_sorteio)
                                if "⚠️" in dna_texto: continue
                                
                                score_ia_base = sum(ia['pesos'][n] for n in candidato)
                                
                                pote.append({
                                    "dezenas": candidato,
                                    "score_base": score_ia_base + score_dna,
                                    "dna": dna_texto
                                })
                            return pote

                        pote_15 = filtrar_universo(universo_15)
                        pote_16 = filtrar_universo(universo_16)
                        
                        progresso_texto.write(f"✅ Filtro concluído! Sobreviveram {len(pote_15)} (15-dez) e {len(pote_16)} (16-dez). Iniciando alocação...")
                        
                        # LAÇO DE COMPRA E DOWNGRADE INTELIGENTE (Somente Força Bruta Ortogonal)
                        while (orcamento - gasto) >= 3.5:
                            
                            if conf_calc >= 0.75 and (orcamento - gasto) >= 56.0 and len(pote_16) > 0:
                                tam, custo, pote_atual = 16, 56.0, pote_16
                            else:
                                tam, custo, pote_atual = 15, 3.5, pote_15
                            
                            melhor_candidato = []
                            melhor_score = -999999
                            melhor_dna = "🧬 DNA Não Biometrado"
                            
                            if not pote_atual: break 
                            
                            melhor_idx = -1
                            jogos_neste_lote_sets = [set(j) for j in jogos_neste_lote]
                            
                            for idx, item in enumerate(pote_atual):
                                penalidade = 0
                                item_set = set(item["dezenas"]) 
                                
                                for jogo_feito_set in jogos_neste_lote_sets:
                                    intersecao = len(item_set & jogo_feito_set) 
                                    if intersecao >= 11:
                                        penalidade += (intersecao ** 3)
                                
                                score_final = item["score_base"] - penalidade
                                
                                if score_final > melhor_score:
                                    melhor_score = score_final
                                    melhor_candidato = item["dezenas"]
                                    melhor_dna = item["dna"]
                                    melhor_idx = idx
                            
                            if melhor_idx != -1:
                                pote_atual.pop(melhor_idx)
                            
                            # FALLBACK & SALVAMENTO
                            if not melhor_candidato: 
                                dezenas_finais_fallback = sorted(ia['matriz_base'], key=lambda x: ia['pesos'].get(x, 0), reverse=True)[:tam+3]
                                melhor_candidato = sorted(random.sample(dezenas_finais_fallback, tam))
                                melhor_dna = "🧬 DNA Mutação Emergencial"
                                
                            jogos_neste_lote.append(set(melhor_candidato))
                                
                            st.session_state.data["jogos_salvos"].append({
                                "id": str(uuid.uuid4()), 
                                "concurso_alvo": ia['alvo'], 
                                "dezenas": melhor_candidato,
                                "tamanho": tam, 
                                "estrategia": ia['cod_estrategia'], 
                                "justificativa": f"Matriz {ia['cod_estrategia']}. Motor Ortogonal (Híbrido).",
                                "status": "Aguardando Sorteio", 
                                "acertos": 0, 
                                "premio_valor": 0.0,
                                "matriz_origem": ia['matriz_base'],
                                "dna": melhor_dna
                            })
                            
                            gasto += custo
                            qtd_gerados += 1
                            
                            progresso = min(gasto / orcamento, 1.0)
                            barra_progresso.progress(progresso)
                            progresso_texto.write(f"⚙️ Compilando lote... {qtd_gerados} bilhetes injetados. Investimento: R$ {gasto:.2f} de R$ {orcamento:.2f}")
        
                        barra_progresso.empty()
                        progresso_texto.empty()
                        st.session_state.data['banca'] -= gasto
                        salvar_dados(st.session_state.data)
                        
                        st.toast(f"✅ Sucesso! {qtd_gerados} jogos ortogonais criados.", icon="🚀")
                        st.success(f"**Lote processado com Sucesso Absoluto!** O sistema extraiu a Elite Probabilística respeitando o seu bolso. Verifique a Aba 4 para ver os jogos.")
                        st.rerun()

    else: 
        st.warning("Aguardando sincronização de dados do Cofre na Aba 1.")

    jogos_salvos = st.session_state.data.get("jogos_salvos", [])

    if jogos_salvos:
        cols = st.columns(3)
        for idx, jogo in enumerate(jogos_salvos, 1):
            with cols[(idx-1) % 3]:
                exibir_card_volante(jogo, idx)
# --- TAB 4: FILA DE SORTEIO ---
with tabs[3]:
    exibir_mini_painel_financeiro()
    st.markdown("### 🎫 Cartões Ativos e Auditados")
    
    # --- MÉTRICAS DE RESUMO DA FILA ---
    jogos_em_espera = [j for j in st.session_state.data["jogos_salvos"] if j.get('status') == "Aguardando Sorteio"]
    total_premio = sum(j.get("premio_valor", 0) for j in st.session_state.data["jogos_salvos"] if j.get('status') == "Premiado")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("🎫 Jogos em Espera", len(jogos_em_espera))
    c2.metric("💰 Premiação Total Acumulada", f"R$ {total_premio:.2f}")
    c3.metric("📊 Bilhetes Auditados", len([j for j in st.session_state.data["jogos_salvos"] if j.get('status') != "Aguardando Sorteio"]))
    
    # =====================================================================
    # MATRIZ QUE GEROU OS JOGOS (SEM GRÁFICOS, MOSTRA O RESULTADO REAL)
    # =====================================================================
    st.markdown("---")
    st.markdown("#### 🎯 A Matriz de Origem vs Sorteio Alvo")
    
    if st.session_state.data.get("jogos_salvos") and st.session_state.data.get("historico_dados"):
        num_ultimo_oficial = int(st.session_state.data["historico_dados"][-1]["concurso"])
        
        # Pega o alvo do ÚLTIMO jogo salvo na base (esteja ele em espera ou já auditado)
        ultimo_jogo_criado = st.session_state.data["jogos_salvos"][-1]
        alvo_foco = ultimo_jogo_criado.get("concurso_alvo")
        matriz_usada = ultimo_jogo_criado.get("matriz_origem")
        
        if matriz_usada:
            elite_group = set(matriz_usada)
            tamanho_matriz = len(elite_group)
            
            col_a1, col_a2 = st.columns([1, 2])
            
            # SE O SORTEIO ALVO JÁ ACONTECEU (E VOCÊ JÁ AUDITOU)
            if alvo_foco <= num_ultimo_oficial:
                resultado_oficial = next((h for h in st.session_state.data["historico_dados"] if int(h["concurso"]) == int(alvo_foco)), None)
                
                if resultado_oficial:
                    sorteio_real = set(resultado_oficial["dezenas"])
                    acertos_elite = len(elite_group.intersection(sorteio_real))
                    
                    with col_a1:
                        st.metric(label=f"Acertos da Matriz (Sorteio {alvo_foco})", value=f"{acertos_elite} / {tamanho_matriz}")
                    with col_a2:
                        st.write(f"**Matriz de {tamanho_matriz} dezenas usada para gerar os jogos:**")
                        st.code(", ".join([f"{n:02d}" for n in sorted(list(elite_group))]))
                    
                    if acertos_elite >= 11:
                        st.success(f"🎯 A Matriz de {tamanho_matriz} dezenas acertou {acertos_elite} pontos no concurso {alvo_foco}!")
                    else:
                        st.warning(f"A Matriz de {tamanho_matriz} dezenas não atingiu 11 pontos no concurso {alvo_foco}.")
            
            # SE O SORTEIO ALVO AINDA NÃO ACONTECEU (ESTÁ ESPERANDO)
            else:
                with col_a1:
                    st.metric(label=f"Sorteio Alvo", value=f"{alvo_foco}", delta="Aguardando Resultado...", delta_color="off")
                with col_a2:
                    st.write(f"**Matriz de {tamanho_matriz} dezenas que gerou seus jogos:**")
                    st.code(", ".join([f"{n:02d}" for n in sorted(list(elite_group))]))
        else:
            st.info("Os jogos atuais são antigos e não têm a Matriz salva.")
    else:
        st.info("Gere jogos na Aba 3 para visualizar a matriz de origem.")

    # =====================================================================
    # BOTÕES DE LIMPAR E EXPORTAR (VERSÃO PRO PDF)
    # =====================================================================
    if st.session_state.data["jogos_salvos"]:
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            st.button("🗑️ LIMPAR TODOS", on_click=cb_excluir_todos, type="secondary", use_container_width=True)
            
        with col_btn2:
            # 1. Buscamos as dezenas do concurso anterior da memória do seu sistema
            ultimas_dezenas = []
            if 'caixa_latest' in st.session_state and 'dezenas' in st.session_state.caixa_latest:
                ultimas_dezenas = st.session_state.caixa_latest['dezenas']
            
            # 2. Injetamos as últimas dezenas na função para ela calcular as Repetidas!
            pdf_bytes = gerar_pdf_jogos(st.session_state.data["jogos_salvos"], ultimas_dezenas)
        
            st.download_button(
                label="📤 EXPORTAR RELATÓRIO (PDF)",
                data=pdf_bytes,
                file_name="Relatorio_LotoMatrix.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
        # --- ABA 4: FILA DE SORTEIO (COM PAGINAÇÃO ANTI-TRAVAMENTO) ---
    st.markdown("---")
    st.markdown("### 🎫 Visualização de Jogos")
    
    # Busca os dados reais
    jogos = st.session_state.data.get("jogos_salvos", [])
    
    if jogos:
        # =======================================================
        # SISTEMA DE PAGINAÇÃO (Mostra 30 bilhetes por tela)
        # =======================================================
        bilhetes_por_pagina = 30
        total_paginas = (len(jogos) // bilhetes_por_pagina) + (1 if len(jogos) % bilhetes_por_pagina > 0 else 0)
        
        # Se tiver muitos bilhetes, cria o seletor de páginas roxo
        if total_paginas > 1:
            st.markdown(f"<div style='color: #930089; font-weight: bold; margin-bottom: 5px;'>Total: {len(jogos)} bilhetes | Escolha a página:</div>", unsafe_allow_html=True)
            pagina_atual = st.selectbox("Navegação de Páginas", range(1, total_paginas + 1), label_visibility="collapsed")
        else:
            pagina_atual = 1
            st.markdown(f"<div style='color: #930089; font-weight: bold; margin-bottom: 15px;'>Total: {len(jogos)} bilhetes</div>", unsafe_allow_html=True)
            
        # Calcula onde começa e onde termina a lista dessa página
        inicio = (pagina_atual - 1) * bilhetes_por_pagina
        fim = inicio + bilhetes_por_pagina
        jogos_pagina = jogos[inicio:fim]
        # =======================================================

        cols = st.columns(3)
        # Agora ele faz o loop apenas nos bilhetes DESTA página (jogos_pagina)
        for idx, j in enumerate(jogos_pagina):
            
            # Trava de segurança contra backup corrompido
            if not isinstance(j, dict):
                continue
                
            # O número real do jogo (Ex: se está na pág 2, começa do jogo 31)
            numero_real_jogo = inicio + idx + 1
            
            with cols[idx % 3]:
                # Desenha o volante roxo premium
                exibir_card_volante(j, numero_real_jogo)
                
                # Exibe status e prêmios
                status = j.get('status', 'Aguardando Sorteio')
                if status == "Premiado":
                    st.success(f"✅ PREMIADO ({j.get('acertos', 0)} Acertos)\n💰 R$ {j.get('premio_valor', 0):.2f}")
                elif status == "Não Premiado":
                    st.error(f"❌ NÃO PREMIADO ({j.get('acertos', 0)} Acertos)")
                else:
                    st.info("⏳ AGUARDANDO SORTEIO")
                
                # Botão de apagar com a cor primária (Roxo)
                id_jogo = j.get('id', str(uuid.uuid4()))
                st.button("🗑️ Apagar", key=f"del_{id_jogo}", on_click=cb_excluir_jogo, args=(id_jogo,), use_container_width=True)
                st.markdown("<br><br>", unsafe_allow_html=True)
    else:
        st.info("Nenhum bilhete registrado na fila.")

# --- TAB 5: SINCRONIZAÇÃO E ENTRADA ---
with tabs[4]:
    exibir_mini_painel_financeiro()
    st.markdown("### 🏆 Sincronização Oficial e Auditoria Pericial")
    
    # =====================================================================
    # 🧠 MOTOR DE AUDITORIA FINANCEIRA PURA
    # =====================================================================
    def auditar_e_aprender_unificado(concurso, dezenas_sorteadas, rateios=None):
        if rateios is None: rateios = {}
        v11, v12, v13, v14, v15 = rateios.get(11, 7.0), rateios.get(12, 14.0), rateios.get(13, 35.0), rateios.get(14, 1500.0), rateios.get(15, 1500000.0)
        
        lucro_total = 0.0
        relatorio = []
        sorteio_set = set(dezenas_sorteadas)
        
        jogos_processados = 0
        premiados = 0
        max_pts = 0
        
        for j in st.session_state.data.get("jogos_salvos", []):
            alvo_do_jogo = j.get('concurso_alvo')
            pode_auditar = False
            
            if str(alvo_do_jogo) == str(concurso) or (isinstance(alvo_do_jogo, int) and alvo_do_jogo <= concurso) or str(alvo_do_jogo) == "Legado":
                pode_auditar = True
                
            if j.get('status') == "Aguardando Sorteio" and pode_auditar:
                jogos_processados += 1
                pontos = len(set(j.get('dezenas', [])).intersection(sorteio_set))
                j['acertos'] = pontos
                j['premio_valor'] = calcular_premio_multiplo(j.get('tamanho', 15), pontos, v11, v12, v13, v14, v15)
                
                max_pts = max(max_pts, pontos)
                
                if pontos >= 11:
                    j['status'] = "Premiado"
                    lucro_total += j['premio_valor']
                    st.session_state.data["banca"] += j['premio_valor']
                    premiados += 1
                else:
                    j['status'] = "Não Premiado"
        
        if jogos_processados > 0:
            relatorio.append(f"Auditoria Concurso {concurso}: {premiados}/{jogos_processados} bilhetes premiados. Pico: {max_pts} pts.")
            
        return lucro_total, relatorio

    def extrair_rateios_api(premiacoes):
        rateios = {}
        if premiacoes:
            for p in premiacoes:
                rateios[p.get('acertos', 0)] = float(p.get('premio', 0.0))
        return rateios

    # -----------------------------------------------------------------
    # MÓDULO: SINCRONIZAÇÃO EM MASSA E RECRIAR BANCO (VIDA REAL)
    # -----------------------------------------------------------------
    with st.container(border=True):
        st.markdown("#### 🛸 Gerenciamento de Banco de Dados e Sincronização")
        st.write("Detecta sorteios faltantes ou recria o banco de dados do ZERO para iniciar a operação na Vida Real.")
        
        col_massa1, col_massa2 = st.columns(2)
        
        with col_massa1:
            if st.button("🛸 BUSCAR FALTANTES E APOSTAR (GAP)", type="primary", use_container_width=True):
                historico = st.session_state.data.get("historico_dados", [])
                if not historico:
                    st.error("Banco vazio. Use o botão ao lado para baixar tudo do zero.")
                else:
                    ultimo_salvo = int(historico[-1]["concurso"])
                    try:
                        res_latest = requests.get("https://loteriascaixa-api.herokuapp.com/api/lotofacil/latest", verify=False, timeout=10).json()
                        ultimo_oficial = int(res_latest['concurso'])
                        
                        if ultimo_salvo >= ultimo_oficial:
                            st.info("O sistema já está atualizado com o último sorteio.")
                        else:
                            concursos_faltantes = list(range(ultimo_salvo + 1, ultimo_oficial + 1))
                            barra = st.progress(0)
                            lucro_acumulado_massa = 0.0
                            logs_massa = []
                            
                            for i, num in enumerate(concursos_faltantes):
                                res_conc = requests.get(f"https://loteriascaixa-api.herokuapp.com/api/lotofacil/{num}", verify=False, timeout=10).json()
                                if 'concurso' in res_conc:
                                    dezenas_sorteadas = sorted([int(d) for d in res_conc['dezenas']])
                                    
                                    st.session_state.data["historico_dados"].append({
                                        "concurso": num, 
                                        "dezenas": dezenas_sorteadas, 
                                        "data": res_conc.get('data', '')
                                    })
                                    
                                    historico_para_ia = st.session_state.data["historico_dados"][:-1]
                                    if len(historico_para_ia) >= 10:
                                        try:
                                            ia_temp = raciocinio_total_ia(historico_para_ia, st.session_state.data.get("ia_memoria", {}))
                                            matriz_base = ia_temp.get('matriz_base', [])
                                            tamanho_matriz = len(matriz_base)
                                            jogos_simulados = []
                                            
                                            if tamanho_matriz <= 20:
                                                jogos_reduzidos = gerar_fechamento_matematico(matriz_base, 14)
                                                limite_jogos = 50 if tamanho_matriz >= 18 else (15 if tamanho_matriz == 17 else len(jogos_reduzidos))
                                                if len(jogos_reduzidos) > limite_jogos:
                                                    jogos_reduzidos = random.sample(jogos_reduzidos, limite_jogos)
                                                
                                                for j_dez in jogos_reduzidos:
                                                    jogos_simulados.append({
                                                        "id": str(uuid.uuid4()), "concurso_alvo": num, "dezenas": sorted(j_dez),
                                                        "tamanho": 15, "status": "Aguardando Sorteio", "acertos": 0,
                                                        "estrategia": "Score Composto", "justificativa": "Fantasma (Plano Exato/Híbrido)"
                                                    })
                                            else:
                                                qtd_jogos = 30
                                                pesos = ia_temp.get('pesos', {})
                                                for _ in range(qtd_jogos):
                                                    candidato = []
                                                    dez_temp = list(matriz_base)
                                                    pesos_temp = [pesos.get(d, 1) for d in dez_temp]
                                                    for _ in range(15):
                                                        escolhida = random.choices(dez_temp, weights=pesos_temp, k=1)[0]
                                                        candidato.append(escolhida)
                                                        idx = dez_temp.index(escolhida)
                                                        dez_temp.pop(idx)
                                                        pesos_temp.pop(idx)
                                                    
                                                    jogos_simulados.append({
                                                        "id": str(uuid.uuid4()), "concurso_alvo": num, "dezenas": sorted(candidato),
                                                        "tamanho": 15, "status": "Aguardando Sorteio", "acertos": 0,
                                                        "estrategia": "Score Composto", "justificativa": "Fantasma (Heurístico)"
                                                    })
                                            
                                            custo_treinamento = len(jogos_simulados) * 3.50
                                            st.session_state.data["banca"] -= custo_treinamento
                                            lucro_acumulado_massa -= custo_treinamento    
                                            st.session_state.data["jogos_salvos"] = jogos_simulados
                                        except Exception as e:
                                            st.session_state.data["jogos_salvos"] = []
                                    else:
                                        st.session_state.data["jogos_salvos"] = []
                                    
                                    rateios_massa = extrair_rateios_api(res_conc.get('premiacoes', []))
                                    lucro_parcial, relatorio_parcial = auditar_e_aprender_unificado(num, dezenas_sorteadas, rateios_massa)
                                    
                                    lucro_acumulado_massa += lucro_parcial
                                    logs_massa.extend(relatorio_parcial)
                                    
                                barra.progress((i + 1) / len(concursos_faltantes))
                            
                            if logs_massa: st.session_state.ultimo_aprendizado = list(set(logs_massa))
                            st.session_state.data["jogos_salvos"] = []
                            salvar_dados(st.session_state.data)
                            st.success(f"✅ GAPs processados com sucesso! R$ {lucro_acumulado_massa:.2f}.")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao processar GAPs: {e}")

        with col_massa2:
            st.markdown("#### ☢️ Iniciar Vida Real (Download e Calibragem)")
            
            if st.button("📥 1. BAIXAR SORTEIOS (DO 1 AO ATUAL)", type="secondary", use_container_width=True):
                st.session_state.data["historico_dados"] = []
                st.session_state.data["jogos_salvos"] = []
                with st.spinner("Baixando base de dados da Caixa do 1º sorteio em diante..."):
                    try:
                        res_todos = requests.get("https://loteriascaixa-api.herokuapp.com/api/lotofacil", verify=False, timeout=60).json()
                        res_todos = sorted(res_todos, key=lambda k: int(k['concurso']))
                        barra_down = st.progress(0)
                        total_concursos = len(res_todos)
                        for i, res_conc in enumerate(res_todos):
                            num = int(res_conc['concurso'])
                            dezenas_sorteadas = sorted([int(d) for d in res_conc['dezenas']])
                            st.session_state.data["historico_dados"].append({
                                "concurso": num, "dezenas": dezenas_sorteadas, "data": res_conc.get('data', '')
                            })
                            if i % 50 == 0: barra_down.progress((i + 1) / total_concursos)
                        salvar_dados(st.session_state.data)
                        barra_down.progress(1.0)
                        st.success(f"✅ Download de {total_concursos} sorteios concluído. Agora clique em CALIBRAR.")
                    except Exception as e:
                        st.error(f"Erro na conexão com API: {e}")

            with st.expander("⚙️ Configurar Sincronização Seletiva"):
                limite_concurso = st.number_input("Limite do Concurso (até onde baixar):", min_value=1, step=1, value=3000)
                concurso_especifico = st.number_input("Concurso Específico (apenas um):", min_value=1, step=1)

            if st.button("📥 2. BAIXAR ATÉ O CONCURSO X", type="secondary", use_container_width=True):
                with st.spinner(f"Baixando base de dados até o concurso {limite_concurso}..."):
                    try:
                        res_todos = requests.get("https://loteriascaixa-api.herokuapp.com/api/lotofacil", verify=False, timeout=60).json()
                        res_filtrado = [r for r in res_todos if int(r['concurso']) <= limite_concurso]
                        res_filtrado = sorted(res_filtrado, key=lambda k: int(k['concurso']))
                        st.session_state.data["historico_dados"] = []
                        for res_conc in res_filtrado:
                            st.session_state.data["historico_dados"].append({
                                "concurso": int(res_conc['concurso']), "dezenas": sorted([int(d) for d in res_conc['dezenas']]), "data": res_conc.get('data', '')
                            })
                        salvar_dados(st.session_state.data)
                        st.success(f"✅ Download até {limite_concurso} concluído!")
                    except Exception as e:
                        st.error(f"Erro na sincronização: {e}")

            if st.button("📥 3. BAIXAR CONCURSO ESPECÍFICO", type="secondary", use_container_width=True):
                with st.spinner(f"Buscando concurso {concurso_especifico}..."):
                    try:
                        res_todos = requests.get("https://loteriascaixa-api.herokuapp.com/api/lotofacil", verify=False, timeout=60).json()
                        res_unico = [r for r in res_todos if int(r['concurso']) == concurso_especifico]
                        if res_unico:
                            res_conc = res_unico[0]
                            novo_dado = {
                                "concurso": int(res_conc['concurso']), "dezenas": sorted([int(d) for d in res_conc['dezenas']]), "data": res_conc.get('data', '')
                            }
                            concursos_existentes = [h['concurso'] for h in st.session_state.data["historico_dados"]]
                            if novo_dado['concurso'] not in concursos_existentes:
                                st.session_state.data["historico_dados"].append(novo_dado)
                                st.session_state.data["historico_dados"] = sorted(st.session_state.data["historico_dados"], key=lambda k: k['concurso'])
                                salvar_dados(st.session_state.data)
                                st.success(f"✅ Concurso {concurso_especifico} adicionado com sucesso!")
                            else:
                                st.warning("Este concurso já consta na base.")
                        else:
                            st.error("Concurso não encontrado na API.")
                    except Exception as e:
                        st.error(f"Erro na sincronização: {e}")            

            if st.button("🧠 2. CALIBRAR INTELIGÊNCIA (LER TODO O BANCO)", type="primary", use_container_width=True):
                historico_completo = st.session_state.data.get("historico_dados", [])
                if not historico_completo:
                    st.error("O banco de dados está vazio! Clique no botão de Baixar primeiro.")
                else:
                    bilhetes_reais = st.session_state.data.get("jogos_salvos", [])
                    st.session_state.data["ia_memoria"] = {"motor_calibrado": True}
                    st.session_state.data["banca"] = 10000.00
                    st.session_state.data["historico_aportes"] = 0.0
                    st.session_state.data["historico_saques"] = 0.0
                    
                    with st.spinner("Calibrando os multiplicadores universais. Processamento em andamento..."):
                        barra_calib = st.progress(0)
                        porcentagem_texto = st.empty()
                        total_concursos = len(historico_completo)
                        
                        for i, dado_atual in enumerate(historico_completo):
                            num = dado_atual['concurso']
                            dezenas_sorteadas = dado_atual['dezenas']
                            historico_para_ia = historico_completo[:i]
                            jogos_simulados = []
                            
                            if len(historico_para_ia) >= 10:
                                try:
                                    ia_temp = raciocinio_total_ia(historico_para_ia, st.session_state.data.get("ia_memoria", {}))
                                    matriz_base = ia_temp.get('matriz_base', [])
                                    tamanho_matriz = len(matriz_base)
                                            
                                    limite_jogos = 50 if tamanho_matriz >= 18 else (15 if tamanho_matriz <= 17 else 30)
                                    pesos = ia_temp.get('pesos', {})
                                    
                                    for _ in range(limite_jogos):
                                        if tamanho_matriz <= 20:
                                            candidato = random.sample(matriz_base, 15)
                                        else:
                                            candidato = []
                                            dez_temp = list(matriz_base)
                                            pesos_temp = [pesos.get(d, 1) for d in dez_temp]
                                            for _ in range(15):
                                                escolhida = random.choices(dez_temp, weights=pesos_temp, k=1)[0]
                                                candidato.append(escolhida)
                                                idx = dez_temp.index(escolhida)
                                                dez_temp.pop(idx)
                                                pesos_temp.pop(idx)
                                                
                                        jogos_simulados.append({
                                            "id": str(uuid.uuid4()), "concurso_alvo": num, "dezenas": sorted(candidato),
                                            "tamanho": 15, "status": "Aguardando Sorteio", "acertos": 0,
                                            "estrategia": "Score Composto", "justificativa": "Fantasma"
                                        })
                                            
                                    custo_treinamento = len(jogos_simulados) * 3.50
                                    st.session_state.data["banca"] -= custo_treinamento
                                except Exception as e:
                                    pass
                            
                            st.session_state.data["jogos_salvos"] = jogos_simulados + bilhetes_reais
                            lucro_parcial, relatorio_parcial = auditar_e_aprender_unificado(num, dezenas_sorteadas, rateios=None)
                            
                            if i % 20 == 0:
                                pct = (i + 1) / total_concursos
                                barra_calib.progress(pct)
                                porcentagem_texto.text(f"Progresso da Calibração: {pct*100:.1f}%")
                        
                        st.session_state.data["jogos_salvos"] = bilhetes_reais 
                        salvar_dados(st.session_state.data)
                        barra_calib.progress(1.0)
                        porcentagem_texto.text("Progresso da Calibração: 100.0%")
                        
                        st.success(f"TERMINAL: Calibração Finalizada. Multiplicadores fixados. Saldo Final Simulado: R$ {st.session_state.data['banca']:,.2f}")

    col_sync1, col_sync2 = st.columns(2)
    
    with col_sync1:
        with st.container(border=True):
            st.markdown("#### 🌐 Sincronização Automática (API Caixa)")
            st.write("Conecta aos servidores da Caixa para baixar o último sorteio, atualizar o banco de dados e conferir todos os bilhetes na fila.")
            
            if st.button("🔄 Buscar Resultado e Auditar Bilhetes", type="primary", use_container_width=True):
                with st.spinner("Conectando à API da Caixa..."):
                    try:
                        resp = requests.get("https://loteriascaixa-api.herokuapp.com/api/lotofacil/latest", verify=False, timeout=15)
                        if resp.status_code == 200:
                            ultimo_resultado = resp.json()
                            dezenas_oficiais = [int(x) for x in ultimo_resultado['dezenas']]
                            concurso_oficial = int(ultimo_resultado['concurso'])
                            
                            novo_dado = {
                                "concurso": concurso_oficial, "data": ultimo_resultado['data'],
                                "dezenas": dezenas_oficiais, "premiacoes": ultimo_resultado.get('premiacoes', [])
                            }
                            
                            existe = any(h['concurso'] == concurso_oficial for h in st.session_state.data["historico_dados"])
                            if not existe: st.session_state.data["historico_dados"].append(novo_dado)
                            
                            st.session_state.caixa_latest = novo_dado
                            rateios = extrair_rateios_api(ultimo_resultado.get('premiacoes', []))
                            lucro_total, relatorio_aprendizado = auditar_e_aprender_unificado(concurso_oficial, dezenas_oficiais, rateios)
                            
                            if relatorio_aprendizado: st.session_state.ultimo_aprendizado = list(set(relatorio_aprendizado))
                            salvar_dados(st.session_state.data)
                            
                            if 'ia_memoria' in st.session_state: del st.session_state.ia_memoria
                            st.success(f"✅ Sincronização Automática Concluída! Lucro creditado: R$ {lucro_total:.2f}")
                            if lucro_total > 0: st.toast("Lucro Creditado", icon="💰")
                            st.rerun()
                        else:
                            st.error("Erro na API da Caixa. Tente a inserção manual ao lado.")
                    except Exception as e:
                        st.error(f"Falha de conexão com a API: {e}")

    with col_sync2:
        with st.container(border=True):
            st.markdown("#### 🛠️ Inserção e Conferência Manual")
            st.write("Insira os dados do sorteio em qualquer formato (ex: 01.02.03, 01-02-03, ou 01 02 03). O sistema vai filtrar automaticamente.")
            
            concurso_manual = st.number_input("Número do Concurso:", min_value=1, step=1, key="num_conc_manual")
            dezenas_texto = st.text_input("Cole as Dezenas Sorteadas (qualquer formato):", key="dez_manual_input")
            
            if st.button("✅ Confirmar e Processar Conferência Manual", use_container_width=True):
                nums_str = re.findall(r'\d+', dezenas_texto)
                try:
                    dezenas_oficiais = sorted([int(n) for n in nums_str])
                    if len(dezenas_oficiais) != 15:
                        st.error(f"Erro: O sistema identificou {len(dezenas_oficiais)} números. É obrigatório inserir exatamente 15 dezenas.")
                    elif len(set(dezenas_oficiais)) != 15:
                        st.error("Erro: Existem dezenas repetidas. Verifique sua digitação ou o texto colado.")
                    elif not all(1 <= n <= 25 for n in dezenas_oficiais):
                        st.error("Erro: As dezenas devem estar entre 01 e 25.")
                    else:
                        lucro_total, relatorio_aprendizado = auditar_e_aprender_unificado(concurso_manual, dezenas_oficiais, rateios=None)
                        
                        existe = any(h['concurso'] == concurso_manual for h in st.session_state.data["historico_dados"])
                        if not existe:
                            novo_dado = {
                                "concurso": concurso_manual, "data": datetime.now().strftime("%d/%m/%Y"),
                                "dezenas": dezenas_oficiais, "premiacoes": []
                            }
                            st.session_state.data["historico_dados"].append(novo_dado)
                            st.session_state.caixa_latest = novo_dado
                        
                        if relatorio_aprendizado: st.session_state.ultimo_aprendizado = list(set(relatorio_aprendizado))
                        salvar_dados(st.session_state.data)
                        
                        if 'ia_memoria' in st.session_state: del st.session_state.ia_memoria
                        st.success(f"✅ Operação Manual Concluída. Banco atualizado e R$ {lucro_total:.2f} creditados.")
                        st.rerun()
                except ValueError:
                    st.error("Erro estrutural na conversão de números.")

    st.divider()

    if 'ultimo_aprendizado' in st.session_state and st.session_state.ultimo_aprendizado:
        st.markdown("#### 🧠 Informações absorvidas pela IA com o último resultado:")
        for aprendizado in st.session_state.ultimo_aprendizado:
            st.info(f"🧬 {aprendizado}")

    if 'caixa_latest' in st.session_state:
        r = st.session_state.caixa_latest
        st.markdown(f"#### 🏛️ Último Extrato Salvo da Caixa: Concurso {r['concurso']} ({r.get('data', '')})")
        st.code(" - ".join([f"{n:02d}" for n in r['dezenas']]))
        if r.get('premiacoes'):
            st.markdown("#### 💰 Tabela do Rateio Registrada")
            st.table(pd.DataFrame(r['premiacoes']))
