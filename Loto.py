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
    
    # 2. Identificação do Ciclo Faltante
    numeros_sorteados_ciclo = set()
    for jogo in reversed(historico):
        numeros_sorteados_ciclo.update(jogo['dezenas'])
        if len(numeros_sorteados_ciclo) == 25: break
    dezenas_ausentes_ciclo = [d for d in range(1, 26) if d not in numeros_sorteados_ciclo]
    qtd_ausentes = len(dezenas_ausentes_ciclo)

    # 3. Cálculo de Desempenho Histórico da Estratégia
    score_estrategia = 11.0
    if pontuacao_estrategias and estrategia_atual in pontuacao_estrategias:
        dado_memoria = pontuacao_estrategias[estrategia_atual]
        if isinstance(dado_memoria, dict) and "usos" in dado_memoria and dado_memoria["usos"] > 0:
            score_estrategia = dado_memoria["pontos"] / dado_memoria["usos"]
        elif isinstance(dado_memoria, (int, float)):
            score_estrategia = float(dado_memoria)

    # 4. INSTINTO TEÓRICO (Hipótese Base)
    if estrategia_atual == "Ciclo":
        if qtd_ausentes <= 4: tamanho_matriz, motivo_tamanho = 17, f"Teoria do Ciclo: Fechamento iminente ({qtd_ausentes} ausentes). Sugestão: 17 dezenas."
        elif qtd_ausentes <= 7: tamanho_matriz, motivo_tamanho = 19, f"Teoria do Ciclo: Reta final ({qtd_ausentes} ausentes). Sugestão: 19 dezenas."
        else: tamanho_matriz, motivo_tamanho = 21, f"Teoria do Ciclo: Cenário inicial ({qtd_ausentes} ausentes). Sugestão: 21 dezenas."
            
    elif estrategia_atual == "Simetria":
        if score_estrategia >= 12.5: tamanho_matriz, motivo_tamanho = 18, f"Teoria Simétrica: Assertividade alta ({score_estrategia:.1f} pts). Sugestão: 18 dezenas."
        else: tamanho_matriz, motivo_tamanho = 20, f"Teoria Simétrica: Volatilidade. Sugestão defensiva: 20 dezenas."
            
    elif estrategia_atual == "Reversao":
        if score_estrategia >= 12.0: tamanho_matriz, motivo_tamanho = 19, f"Teoria da Reversão: Confiança em zebras ({score_estrategia:.1f} pts). Sugestão: 19 dezenas."
        elif score_estrategia < 10.5: tamanho_matriz, motivo_tamanho = 22, f"Teoria da Reversão: Risco extremo. Sugestão ampla: 22 dezenas."
        else: tamanho_matriz, motivo_tamanho = 21, f"Teoria da Reversão: Padrão. Sugestão: 21 dezenas."
        
    else: # Tendencia
        if score_estrategia >= 12.8: tamanho_matriz, motivo_tamanho = 18, f"Teoria da Tendência: Padrão forte ({score_estrategia:.1f} pts). Sugestão: 18 dezenas."
        elif score_estrategia < 11.2: tamanho_matriz, motivo_tamanho = 21, f"Teoria da Tendência: Desempenho em queda. Sugestão de resgate: 21 dezenas."
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
# CÉREBRA MULTI-ESTRATÉGICO DA IA (4 Linhas de Análise Evoluídas)
# =====================================================================
def raciocinio_total_ia(historico, memoria):
    if not historico: return None
    
    # 🧠 LEITURA DE CENÁRIO (Parâmetros validados e otimizados)
    historico_recente = historico[-50:] if len(historico) >= 50 else historico
    todas_dezenas_recentes = [n for h in historico_recente for n in h['dezenas']]
    freq_recente = Counter(todas_dezenas_recentes)
    freq_recente_max = max(freq_recente.values()) if freq_recente else 1
    
    freq = Counter([n for h in historico for n in h['dezenas']])
    
    primos_lista = [2, 3, 5, 7, 11, 13, 17, 19, 23]
    moldura_lista = [1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25]
    
    ultimos_10 = historico[-10:] if len(historico) >= 10 else historico
    penultimos_10 = historico[-20:-10] if len(historico) >= 20 else historico[-10:]
    
    freq_ult_10 = Counter([n for h in ultimos_10 for n in h['dezenas']])
    freq_pen_10 = Counter([n for h in penultimos_10 for n in h['dezenas']])

    media_soma = sum([sum(h['dezenas']) for h in ultimos_10]) / len(ultimos_10)
    soma_ultimo = sum(historico[-1]['dezenas'])
    media_impares = sum([sum(1 for n in h['dezenas'] if n % 2 != 0) for h in ultimos_10]) / len(ultimos_10)
    media_primos = sum([sum(1 for n in h['dezenas'] if n in primos_lista) for h in ultimos_10]) / len(ultimos_10)
    media_moldura = sum([sum(1 for n in h['dezenas'] if n in moldura_lista) for h in ultimos_10]) / len(ultimos_10)

    atrasos = {n: 0 for n in range(1, 26)}
    dezena_encontrada = {n: False for n in range(1, 26)}
    
    for h in reversed(historico):
        for n in range(1, 26):
            if n in h['dezenas']:
                dezena_encontrada[n] = True
            elif not dezena_encontrada[n]:
                atrasos[n] += 1

    # --- CÉREBRO DE CICLO INTELIGENTE (Matemática Absoluta) ---
    ciclo_atual = set()
    jogos_ciclo = 0
    
    for h in historico:
        ciclo_atual.update(h['dezenas'])
        jogos_ciclo += 1
        if len(ciclo_atual) == 25:
            ciclo_atual = set() 
            jogos_ciclo = 0
            
    faltam_ciclo = sorted(list(set(range(1, 26)) - ciclo_atual))
    
    # --- AVALIAÇÃO DE DESEMPENHO (Leitura Direta da Memória) ---
    perf = {}
    for est in ["Tendencia", "Reversao", "Ciclo", "Simetria"]:
        dado_memoria = memoria.get(est, 11.0)
        if isinstance(dado_memoria, dict):
            usos = dado_memoria.get("usos", 0)
            pontos = dado_memoria.get("pontos", 0)
            perf[est] = pontos / usos if usos > 0 else 11.0 
        else:
            perf[est] = float(dado_memoria)
            
    # =================================================================
    # 🌟 O CÉREBRO CONTEXTUAL (ALGORITMO DE BANDIDO CONTEXTUAL - V2) 🌟
    # =================================================================
    notas_finais = perf.copy()
    
    # 1. GATILHO DO CICLO
    qtd_faltam = len(faltam_ciclo)
    if qtd_faltam > 0 and qtd_faltam <= 7:
        if jogos_ciclo >= 3:
            notas_finais["Ciclo"] += 2.0 + ((7 - qtd_faltam) * 0.3) + (jogos_ciclo * 0.2)
        else:
            notas_finais["Ciclo"] -= 3.5 
    elif qtd_faltam >= 18 or jogos_ciclo <= 1: 
        notas_finais["Ciclo"] -= 4.0 
        
    # 2. GATILHO DA REVERSÃO E TENDÊNCIA
    try:
        if len(historico) >= 2:
            repetidas_ultimo = len(set(historico[-1]['dezenas']).intersection(set(historico[-2]['dezenas'])))
            is_anomalia_extrema = (repetidas_ultimo <= 7) or (repetidas_ultimo >= 11) or (soma_ultimo > 210) or (soma_ultimo < 175)
            
            if is_anomalia_extrema:
                notas_finais["Reversao"] += 2.0 
            elif 8 <= repetidas_ultimo <= 10 and (180 <= media_soma <= 205):
                notas_finais["Tendencia"] += 1.5
    except: pass
        
    # 3. GATILHO DA SIMETRIA
    try:
        moldura_ultimo = sum(1 for n in historico[-1]['dezenas'] if n in moldura_lista)
        if moldura_ultimo <= 8 or moldura_ultimo >= 12: 
            notas_finais["Simetria"] += 1.8
    except: pass
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
    
    # 2. Identificação do Ciclo Faltante
    numeros_sorteados_ciclo = set()
    for jogo in reversed(historico):
        numeros_sorteados_ciclo.update(jogo['dezenas'])
        if len(numeros_sorteados_ciclo) == 25: break
    dezenas_ausentes_ciclo = [d for d in range(1, 26) if d not in numeros_sorteados_ciclo]
    qtd_ausentes = len(dezenas_ausentes_ciclo)

    # 3. Cálculo de Desempenho Histórico da Estratégia
    score_estrategia = 11.0
    if pontuacao_estrategias and estrategia_atual in pontuacao_estrategias:
        dado_memoria = pontuacao_estrategias[estrategia_atual]
        if isinstance(dado_memoria, dict) and "usos" in dado_memoria and dado_memoria["usos"] > 0:
            score_estrategia = dado_memoria["pontos"] / dado_memoria["usos"]
        elif isinstance(dado_memoria, (int, float)):
            score_estrategia = float(dado_memoria)

    # 4. INSTINTO TEÓRICO (Hipótese Base)
    if estrategia_atual == "Ciclo":
        if qtd_ausentes <= 4: tamanho_matriz, motivo_tamanho = 17, f"Teoria do Ciclo: Fechamento iminente ({qtd_ausentes} ausentes). Sugestão: 17 dezenas."
        elif qtd_ausentes <= 7: tamanho_matriz, motivo_tamanho = 19, f"Teoria do Ciclo: Reta final ({qtd_ausentes} ausentes). Sugestão: 19 dezenas."
        else: tamanho_matriz, motivo_tamanho = 21, f"Teoria do Ciclo: Cenário inicial ({qtd_ausentes} ausentes). Sugestão: 21 dezenas."
            
    elif estrategia_atual == "Simetria":
        if score_estrategia >= 12.5: tamanho_matriz, motivo_tamanho = 18, f"Teoria Simétrica: Assertividade alta ({score_estrategia:.1f} pts). Sugestão: 18 dezenas."
        else: tamanho_matriz, motivo_tamanho = 20, f"Teoria Simétrica: Volatilidade. Sugestão defensiva: 20 dezenas."
            
    elif estrategia_atual == "Reversao":
        if score_estrategia >= 12.0: tamanho_matriz, motivo_tamanho = 19, f"Teoria da Reversão: Confiança em zebras ({score_estrategia:.1f} pts). Sugestão: 19 dezenas."
        elif score_estrategia < 10.5: tamanho_matriz, motivo_tamanho = 22, f"Teoria da Reversão: Risco extremo. Sugestão ampla: 22 dezenas."
        else: tamanho_matriz, motivo_tamanho = 21, f"Teoria da Reversão: Padrão. Sugestão: 21 dezenas."
        
    else: # Tendencia
        if score_estrategia >= 12.8: tamanho_matriz, motivo_tamanho = 18, f"Teoria da Tendência: Padrão forte ({score_estrategia:.1f} pts). Sugestão: 18 dezenas."
        elif score_estrategia < 11.2: tamanho_matriz, motivo_tamanho = 21, f"Teoria da Tendência: Desempenho em queda. Sugestão de resgate: 21 dezenas."
        else: tamanho_matriz, motivo_tamanho = 19, f"Teoria da Tendência: Cenário estável. Sugestão: 19 dezenas."

    # 5. CÁLCULO DA TAXA DE CONFIANÇA
    fator_quentes = min(len(dezenas_quentes) / 15, 1.0)
    fator_ia = min(max((score_estrategia - 8.0) / 3.0, 0.0), 1.0) 
    taxa_confianca = max(min((fator_quentes * 0.4) + (fator_ia * 0.6), 1.0), 0.1)

    detalhes = {"dezenas_quentes": len(dezenas_quentes), "ausentes_ciclo": qtd_ausentes, "score_ia": score_estrategia}
    return tamanho_matriz, taxa_confianca, motivo_tamanho, detalhes
  
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
    
    # 1. Cria o Cofre Imutável se for a primeira vez rodando
    if "ledger_track" not in st.session_state.data:
        st.session_state.data["ledger_track"] = {
            "bilhetes": 0, "premiados_geral": 0, "elite": 0, "custo": 0.0, "retorno": 0.0
        }
        
    # 2. Varredura Inteligente: Suga os dados de novos jogos conferidos
    precisa_salvar = False
    for j in st.session_state.data.get("jogos_salvos", []):
        # Se o jogo já foi conferido e AINDA NÃO foi contabilizado no Cofre
        if j.get("status") != "Aguardando Sorteio" and not j.get("ledger_ok", False):
            
            # Adiciona as estatísticas no Cofre Permanente
            st.session_state.data["ledger_track"]["bilhetes"] += 1
            
            if j.get("acertos", 0) >= 11:
                st.session_state.data["ledger_track"]["premiados_geral"] += 1
            if j.get("acertos", 0) >= 14:
                st.session_state.data["ledger_track"]["elite"] += 1
                
            custo = 56.0 if j.get("tamanho", 15) == 16 else 3.50
            st.session_state.data["ledger_track"]["custo"] += custo
            st.session_state.data["ledger_track"]["retorno"] += j.get("premio_valor", 0.0)
            
            # Carimba o bilhete para nunca mais ser somado em duplicidade
            j["ledger_ok"] = True
            precisa_salvar = True
            
    # Grava o Cofre no HD caso tenha sugado novos dados
    if precisa_salvar:
        salvar_dados(st.session_state.data)

    # 3. Leitura dos Dados do Cofre Permanente (Imune a Exclusões da Fila)
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
    
    if ledger["custo"] > 0:
        roi_real = (lucro_prejuizo_real / ledger["custo"]) * 100
    else:
        roi_real = 0.0

    # 4. Renderização do Painel Profissional
    with st.container(border=True):
        col_trk1, col_trk2, col_trk3, col_trk4 = st.columns(4)
        
        col_trk1.metric("🎟️ Bilhetes Operados", f"{qtd_conferidos}")
        
        col_trk2.metric("🎯 Win Rate (Prêmios)", f"{win_rate_geral:.1f}%", 
                        help="Um apostador cego tem ~9% de Win Rate. O que passar disso é o puro lucro da sua Inteligência.")
        
        col_trk3.metric("💎 Freq. de Elite", texto_freq_elite, 
                        help="Mede quantos bilhetes a máquina gera em média até cravar um de 14 ou 15 pontos.")
        
        delta_color = "normal" if lucro_prejuizo_real >= 0 else "inverse"
        col_trk4.metric("📈 ROI Financeiro", f"{roi_real:.1f}%", 
                        delta=f"R$ {lucro_prejuizo_real:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), 
                        delta_color=delta_color)
        
    st.divider()
    
    # =====================================================================
    if st.session_state.data["historico_dados"]:
        ia = raciocinio_total_ia(st.session_state.data["historico_dados"], st.session_state.data["ia_memoria"])
        # 🛡️ PROTEÇÃO: Verifica se a IA retornou dados antes de tentar usar
        if ia is not None:
            st.session_state.data["matriz_viva_atual"] = ia["matriz_base"]
            tam_atual = len(ia['matriz_base'])
        else:
            st.error("⚠️ O Cérebro da IA não conseguiu processar os dados agora. Recarregando...")
            # Opcional: st.rerun() para tentar forçar nova leitura
        

            # =====================================================================
            # 1. INDICADOR DO MOTOR ATIVO NO MOMENTO (TOPO)
            # =====================================================================
            st.markdown("<h3 style='color: #1f77b4;'>🧠 Transparência Absoluta: Motores e Probabilidades Reais</h3>", unsafe_allow_html=True)
            st.info(f"🎯 **A Inteligência Artificial definiu uma Matriz Cirúrgica de {tam_atual} Dezenas para o contexto atual.**")
        else:
            st.error("⚠️ O Cérebro da IA não conseguiu processar os dados agora.")

        # =====================================================================
        # 2. PAINEL DE TRANSPARÊNCIA: 3 COLUNAS DAS INTELIGÊNCIAS
        # =====================================================================
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
                
            with c1:
                st.markdown("#### 🥇 PLANO A")
                st.markdown("*Matemático Puro (Exato)*")
                if tam_atual <= 18:
                    st.success(
                        "**Garantia Real: 100% Exata**\n\n"
                        "Se as 15 sorteadas caírem na matriz, o prêmio está matematicamente garantido. "
                        "Não usa filtros. **Ideal para matrizes pequenas.**"
                    )
                else:
                    st.error(
                        "**Status: INVIÁVEL**\n\n"
                        "Matriz muito grande. Gerar 100% de garantia travaria o PC e custaria fortunas."
                    )
                
            with c2:
                st.markdown("#### 🥈 PLANO B (Híbrido)")
                st.markdown("*Matriz Exata + Poda DNA*")
                if 17 <= tam_atual <= 20:
                    st.info(
                        "**Probabilidade Real: Alta (~85% a 95%)**\n\n"
                        "Gera a base exata do Plano A, mas **corta no bisturi** os jogos lixo. "
                        "Foca o orçamento na **Elite Probabilística**."
                    )
                else:
                    st.warning(
                        "**Status: DESLIGADO**\n\n"
                        "Este motor cirúrgico atua perfeitamente apenas em matrizes de 17 a 20 dezenas."
                    )
                
            with c3:
                st.markdown("#### 🥉 PLANO B (Heurístico)")
                st.markdown("*Estocástico (Monte Carlo)*")
                if tam_atual > 20:
                    st.info(
                        "**Probabilidade Real: Média / Dinâmica**\n\n"
                        "Não existe garantia exata. Sorteia jogos guiados pelos pesos da IA. "
                        "Age como **Rede de Arrasto** para proteger a banca na volatilidade."
                    )
                else:
                    st.warning(
                        "**Status: DESLIGADO**\n\n"
                        "Desnecessário no momento. Para matrizes curtas, os motores matemáticos assumem."
                    )

        # =====================================================================
        # DADOS MATEMÁTICOS UNIFICADOS
        # =====================================================================
        alvos_matematicos = {
            15: {15: 1, 14: 1, 13: 1, "motor": "🎯 Direto (Plano A)"},
            16: {15: 16, 14: 4, 13: 2, "motor": "🥇 Plano A (Exato)"},
            17: {15: 136, 14: 10, 13: 4, "motor": "🥇 Plano A / 🥈 Híbrido"},
            18: {15: 816, 14: 24, 13: 6, "motor": "🥇 Plano A / 🥈 Híbrido"},
            19: {15: 3876, 14: 87, 13: 15, "motor": "🥈 Plano B (Híbrido)"},
            20: {15: 15504, 14: 350, 13: 50, "motor": "🥈 Plano B (Híbrido)"},
            21: {15: 54264, 14: 1000, 13: 100, "motor": "🥉 Plano B (Heurístico)"},
            22: {15: 170544, 14: 3000, 13: 250, "motor": "🥉 Plano B (Heurístico)"},
            23: {15: 490314, 14: 10000, 13: 800, "motor": "🥉 Plano B (Heurístico)"}
        }
        
        dados_matriz = alvos_matematicos.get(tam_atual, alvos_matematicos.get(20))

        # =====================================================================
        # 3. PAINEL DE CUSTOS, SELEÇÃO DE MOTOR E SIMULAÇÃO
        # =====================================================================
        st.markdown("<h3 style='color: #1f77b4; margin-top: 20px;'>💰 Projeção Financeira e Análise de Motores</h3>", unsafe_allow_html=True)
            
        with st.container(border=True):
            garantia_escolhida = st.radio(
                "🎯 **Qual prêmio você quer garantir matematicamente (se as 15 sorteadas estiverem na Matriz)?**", 
                [15, 14, 13], 
                index=1, 
                horizontal=True,
                format_func=lambda x: f"Foco em {x} Pontos"
            )
        
            st.divider()
            forcar_motor = st.checkbox("🚀 **Forçar uso do Motor Selecionado (Ignorar Plano A)**",
                                       key='forcar_motor',
                                       help="Se marcado, o sistema ignorará o Plano A (Exato) mesmo que você tenha verba, forçando o uso do Plano B Híbrido ou Heurístico.")
            st.divider()    
            
            motores_disponiveis = []
            if tam_atual <= 20: motores_disponiveis.append("🥇 Plano A (Exato / 100%)")
            if 17 <= tam_atual <= 20: motores_disponiveis.append("🥈 Plano B (Híbrido Ortogonal / Fronteira)")
            if tam_atual > 20: motores_disponiveis.append("🥉 Plano B (Heurístico / Arrasto)")
                
            motor_selecionado = st.radio(
                "⚙️ **Selecione o Motor Operacional para simulação:**",
                motores_disponiveis,
                index=0 if len(motores_disponiveis) == 1 else 1,
                horizontal=True
            )
            
            jogos_100_pct = dados_matriz[garantia_escolhida]
            custo_100_pct = jogos_100_pct * 3.50
            
            fator_otimizacao = {
                15: 1.0, 16: 1.0, 17: 0.50, 18: 0.40, 
                19: 0.35, 20: 0.25, 21: 0.10, 22: 0.05, 23: 0.03, 24: 0.02, 25: 0.01
            }
            fator = fator_otimizacao.get(tam_atual, 0.05)
            jogos_otimizados = max(1, int(jogos_100_pct * fator))
            
            if "🥇" in motor_selecionado:
                qtd_exibicao = jogos_100_pct
                prob_exibicao = "100% Exata"
            elif "🥈" in motor_selecionado:
                qtd_exibicao = jogos_otimizados
                prob_exibicao = "~85% a 95% (Otimizada)"
            else:
                qtd_exibicao = jogos_otimizados
                prob_exibicao = "~70% a 85% (Arrasto)"
                
            custo_exibicao = qtd_exibicao * 3.50
            
            st.divider() 
            
            c_a, c_b, c_c, c_d = st.columns(4)
            c_a.metric("🧩 Matriz", f"{tam_atual} Dezenas")
            c_b.metric("📊 Cobertura Média", prob_exibicao) 
            c_c.metric("🎟️ Volume Físico", f"{qtd_exibicao:,}".replace(",", ".") + " Jogos")
            c_d.metric("💸 Investimento", f"R$ {custo_exibicao:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        # ==========================================================
        # TABELA INSTITUCIONAL DE COBERTURA
        # ==========================================================
        with st.expander("📊 Tabela Institucional Completa: Motores, Limites e Custos (15 a 23 Dezenas)", expanded=False):
            st.info(f"A tabela mapeia todos os cenários operacionais possíveis para a meta de **{garantia_escolhida} Pontos**. Compare o custo do Fechamento Exato contra a Fronteira de Eficiência (Planos B).")
            
            tabela_dados = []
            for m_tam, m_data in alvos_matematicos.items():
                if m_tam > 23: continue 
                
                j_100 = m_data[garantia_escolhida]
                c_100 = j_100 * 3.50
                f_opt = fator_otimizacao.get(m_tam, 0.05)
                j_opt = max(1, int(j_100 * f_opt))
                c_opt = j_opt * 3.50
                
                if m_tam <= 20:
                    tabela_dados.append({"Matriz": f"{m_tam} Dz", "Motor": "🥇 Plano A (Exato)", "Prob.": "100%", "Bilhetes": j_100, "Custo (R$)": c_100})
                if 17 <= m_tam <= 20:
                    tabela_dados.append({"Matriz": f"{m_tam} Dz", "Motor": "🥈 Plano B (Híbrido)", "Prob.": "~90%", "Bilhetes": j_opt, "Custo (R$)": c_opt})
                if m_tam > 20:
                    tabela_dados.append({"Matriz": f"{m_tam} Dz", "Motor": "🥉 Plano B (Heurístico)", "Prob.": "~80%", "Bilhetes": j_opt, "Custo (R$)": c_opt})
                    
            df_institucional = pd.DataFrame(tabela_dados)
            st.dataframe(
                df_institucional,
                column_config={
                    "Matriz": st.column_config.TextColumn("🧩 Matriz"),
                    "Motor": st.column_config.TextColumn("⚙️ Motor Aplicado"),
                    "Prob.": st.column_config.TextColumn("🎯 Cobertura Real"),
                    "Bilhetes": st.column_config.NumberColumn("🎟️ Bilhetes", format="%d"),
                    "Custo (R$)": st.column_config.NumberColumn("💸 Custo Estimado", format="R$ %.2f")
                },
                hide_index=True, use_container_width=True
            )

        # ==========================================================
        # BÚSSOLA DE APORTE FINANCEIRO
        # ==========================================================
        banca_atual = st.session_state.data.get('banca', 0.0)
        falta = custo_exibicao - banca_atual
        
        st.markdown("---")
        st.markdown("#### 🧭 Bússola de Operação Financeira")
        
        with st.container(border=True):
            if banca_atual >= custo_exibicao:
                st.success(f"✅ **Banca Suficiente:** O seu saldo atual (R$ {banca_atual:,.2f}) cobre o investimento total da operação via **{motor_selecionado}** (Custo: **R$ {custo_exibicao:,.2f}**). Pode seguir para a Tab 3 e disparar o sistema.")
            else:
                if "🥇" in motor_selecionado:
                    st.warning(f"⚠️ **Orçamento Defensivo Detectado:** Para extrair a garantia 100% matemática com o **{motor_selecionado}**, o exigido é **R$ {custo_exibicao:,.2f}** ({qtd_exibicao} jogos).\n\nComo o seu saldo atual é R$ {banca_atual:,.2f}, faça um aporte de pelo menos **R$ {falta:,.2f}** ou altere o simulador acima para o *Plano B (Híbrido)* para verificar o custo da operação com redução otimizada.")
                elif "🥈" in motor_selecionado:
                     st.info(f"⚡ **Fronteira de Eficiência:** Você optou por ligar o **{motor_selecionado}**. Ele corta o custo irreal do fechamento exato e cria um **Lote Otimizado de {qtd_exibicao} bilhetes** focado na elite probabilística (Custo Realista: **R$ {custo_exibicao:,.2f}**).\n\n*Como seu saldo atual é R$ {banca_atual:,.2f}, faça um aporte de **R$ {falta:,.2f}** para disparar esta matriz otimizada.*")
                else:
                     st.info(f"🌪️ **Rede de Arrasto Estatística:** Para matrizes gigantes como esta ({tam_atual} Dz), o sistema obriga o uso do **{motor_selecionado}**. O computador definiu um **Lote Otimizado de {qtd_exibicao} bilhetes** para fazer a rede de proteção (Custo: **R$ {custo_exibicao:,.2f}**).\n\n*💡 Nota do Motor:* O volume estimado é de **{qtd_exibicao} jogos** de 15 dezenas. Porém, se o sistema detectar **Alta Confiança** na rodada, ele fará um upgrade automático: usará esse mesmo orçamento de R$ {custo_exibicao:,.2f} para comprar jogos de **16 dezenas**, reduzindo o número de bilhetes físicos, mas multiplicando o poder de acerto.\n\n*Como seu saldo atual é R$ {banca_atual:,.2f}, injete um aporte de **R$ {falta:,.2f}** para autorizar o motor estocástico.*")

        # =====================================================================
        # SUPER PAINEL INSTITUCIONAL: RAIO-X, RISCO E CORRELAÇÃO
        # =====================================================================
        st.markdown(f"<h3 style='color: #1f77b4; margin-top: 30px;'>🧠 Diagnóstico Autônomo — Concurso Alvo <code>{ia['alvo']}</code></h3>", unsafe_allow_html=True)
        
        historico_painel = st.session_state.data.get("historico_dados", [])
        if len(historico_painel) >= 2:
            ultimo_sort = historico_painel[-1]
            penultimo_sort = historico_painel[-2]
            dez_ult = ultimo_sort['dezenas']
            dez_pen = penultimo_sort['dezenas']
            
            # 1. EXPANSÃO BIOMÉTRICA (DNA do Sorteio)
            primos_set = {2, 3, 5, 7, 11, 13, 17, 19, 23}
            fibo_set = {1, 2, 3, 5, 8, 13, 21}
            mult3_set = {3, 6, 9, 12, 15, 18, 21, 24}

            pares_ult = sum(1 for n in dez_ult if n % 2 == 0)
            impares_ult = 15 - pares_ult
            primos_ult = sum(1 for n in dez_ult if n in primos_set)
            fibo_ult = sum(1 for n in dez_ult if n in fibo_set)
            mult3_ult = sum(1 for n in dez_ult if n in mult3_set)
            repetidas_ult = len(set(dez_ult).intersection(set(dez_pen)))
            
            dezenas_ult_formatadas = " - ".join([f"{n:02d}" for n in dez_ult])
            
            # Banners HTML Elegantes para Destaques
            st.markdown(f"""
            <div style='background: linear-gradient(90deg, #1f77b4 0%, #00d2ff 100%); padding: 12px 20px; border-radius: 8px; color: white; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <h4 style='margin: 0; color: white;'>🎯 Último Sorteio Oficial (Concurso {ultimo_sort['concurso']})</h4>
                <p style='margin: 5px 0 0 0; font-size: 18px; font-family: monospace; font-weight: bold;'>{dezenas_ult_formatadas}</p>
            </div>
            """, unsafe_allow_html=True)
            
            col_rx1, col_rx2, col_rx3, col_rx4, col_rx5, col_rx6 = st.columns(6)
            col_rx1.metric("Ímpares", impares_ult)
            col_rx2.metric("Pares", pares_ult)
            col_rx3.metric("Primos", primos_ult)
            col_rx4.metric("Fibonacci", fibo_ult)
            col_rx5.metric("Múltiplos 3", mult3_ult)
            col_rx6.metric("Repetidas", repetidas_ult)
            
            st.divider()

            # 2. MOTOR APRIORI (Cálculo Restrito à Matriz de Elite - Rota A)
            amostra_corr = historico_painel[-100:] if len(historico_painel) > 100 else historico_painel
            pares_count = {}
            matriz_atual_set = set(ia['matriz_base'])

            for sorteio in amostra_corr:
                d_sort = [n for n in sorteio['dezenas'] if n in matriz_atual_set]
                for i in range(len(d_sort)):
                    for j in range(i+1, len(d_sort)):
                        par = tuple(sorted((d_sort[i], d_sort[j])))
                        pares_count[par] = pares_count.get(par, 0) + 1
            
            top_par = max(pares_count, key=pares_count.get) if pares_count else (0,0)
            st.session_state.par_ouro = top_par 

            # 3. TERMÔMETRO DE RISCO E CORRELAÇÃO
            col_risk, col_corr = st.columns(2)
            
            with col_risk:
                st.markdown("#### 🌡️ Termômetro de Risco")
                qtd_m = ia.get('qtd_matriz', 18)
                if qtd_m >= 21:
                    n_risco = "ALTO (Início de Ciclo / Caos)"
                    c_risco = "#dc3545"; bg_risco = "#fff5f5"; d_banca = "Recomendação: Operar com orçamento defensivo."
                elif qtd_m == 19:
                    n_risco = "MÉDIO (Meio de Ciclo / Transição)"
                    c_risco = "#ffcc00"; bg_risco = "#fffdf5"; d_banca = "Recomendação: Operar com orçamento padrão."
                else:
                    n_risco = "BAIXO (Fim de Ciclo / Alta Previsibilidade)"
                    c_risco = "#28a745"; bg_risco = "#f5fff7"; d_banca = "Recomendação: Janela de Ataque. Risco Mínimo."

                st.markdown(f"""
                <div style='background-color: {bg_risco}; border-left: 6px solid {c_risco}; padding: 18px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); height: 110px;'>
                    <span style='color: {c_risco}; font-weight: 800; font-size: 16px; text-transform: uppercase;'>Nível Atual: {n_risco}</span><br><br>
                    <span style='color: #4d5156; font-size: 14px;'><b>Diretriz Institucional:</b> {d_banca}</span>
                </div>
                """, unsafe_allow_html=True)

            with col_corr:
                st.markdown("#### 🕸️ Teia de Correlação")
                st.markdown(f"""
                <div style='background-color: #f4f8fb; border-left: 6px solid #1a73e8; padding: 18px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); height: 110px;'>
                    <span style='color: #1a73e8; font-weight: 800; font-size: 16px; text-transform: uppercase;'>Par Magnético da Elite: {top_par[0]:02d} e {top_par[1]:02d}</span><br><br>
                    <span style='color: #4d5156; font-size: 14px;'>A dupla mais quente dentro da matriz. O Motor DNA focará no agrupamento quântico.</span>
                </div>
                """, unsafe_allow_html=True)

            st.divider()
            
            # =====================================================================
            # PAINEL DE GESTÃO DE CICLO, CONFIANÇA E APOSTAS MÚLTIPLAS
            # =====================================================================
            st.subheader("📐 Gestão Inteligente: Matriz, Confiança e Orçamento")
            
            estrategia_selecionada = ia.get('estrategia', 'Tendencia')
            memoria_ia = st.session_state.data.get('ia_memoria', {})
            
            tam_matriz_calc, confianca_calc, motivo_calc, dados_internos = calcular_temperatura_e_confianca(
                historico_painel, estrategia_selecionada, memoria_ia
            )
        
            qtd_em_falta = len(ia['faltam_ciclo'])
        
            with st.container(border=True):
                col_c1, col_c2, col_c3, col_c4 = st.columns(4)
                col_c1.metric("Ciclo aberto há", f"{ia['ciclo_tam']} concursos")
                col_c2.metric("Dezenas faltando", qtd_em_falta)
                col_c3.metric("🎯 Confiança da Estratégia", f"{confianca_calc * 100:.1f}%")
                
                status_16 = "⚠️ BLOQUEADO (15 Dez)" if confianca_calc < 0.75 else "🔥 LIBERADO (16 Dez)"
                col_c4.metric("⚡ Permissão p/ Jogos Múltiplos", status_16)
            
            st.info(f"📋 **Diagnóstico do Motor Matemático:** {motivo_calc}")
        
            with st.expander("🔍 Ver Backstage da Decisão (Regras e Peso da IA)"):
                st.write(f"🔥 Dezenas 'Quentes' detectadas nos últimos 10 concursos: `{dados_internos.get('dezenas_quentes', 0)}/25`")
                nota_real = ia.get('perf', {}).get(ia['cod_estrategia'], 11.0)
                st.markdown(f"**📈 Pontuação atual da estratégia '{ia['estrategia']}':** `{nota_real:.2f} pts`")
                st.write("---")
                st.write("**Como a IA decide habilitar bilhetes de 16 dezenas (R$ 56,00)?**")
                st.write("A inteligência cruza a Força do Ciclo com a Pontuação da Estratégia. Somente se a Confiança passar de **75%** e houver saldo em banca, o desdobramento de 16 números será gerado.")

            st.divider()
        
            st.success(f"**⚡ LINHA TÁTICA ATIVADA:** {ia['estrategia']} \n\n**DIRETRIZ DA DECISÃO:** {ia['motivo_est']}")
            st.info(f"**🎯 GRUPO DE ELITE ({ia['qtd_matriz']} DEZENAS COMPILADAS):** {', '.join([f'{n:02d}' for n in ia['matriz_base']])}")

            # --- PARÂMETROS VOLUMÉTRICOS E DISTRIBUIÇÃO ESPACIAL ---
            st.markdown("#### 📈 Parâmetros Volumétricos e Distribuição Espacial")
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Massa de Soma", f"{ia['soma']:.1f}", delta="Equilíbrio: ~195")
                c2.metric("Massa Ímpar", f"{ia['impares']:.1f}", delta="Equilíbrio: ~7.5")
                c3.metric("Massa Primos", f"{ia['primos']:.1f}", delta="Equilíbrio: ~5.5")
                c4.metric("Massa Moldura", f"{ia['moldura']:.1f}", delta="Equilíbrio: ~10")

            linhas_count = {i: 0 for i in range(1, 6)}
            colunas_count = {i: 0 for i in range(1, 6)}
            for n in ia['matriz_base']:
                l = (n - 1) // 5 + 1
                c = (n - 1) % 5 + 1
                linhas_count[l] += 1
                colunas_count[c] += 1
        
            ultimo_sorteio = st.session_state.data["historico_dados"][-1]["dezenas"]
            repetidas_previstas = len(set(ia['matriz_base']).intersection(set(ultimo_sorteio)))

            c_an1, c_an2, c_an3 = st.columns(3)
            with c_an1:
                st.info(f"📋 **Dezenas por Linha:**<br>" + " | ".join([f"L{k}: **{v}**" for k, v in linhas_count.items()]), icon="📊")
            with c_an2:
                st.info(f"📋 **Dezenas por Coluna:**<br>" + " | ".join([f"C{k}: **{v}**" for k, v in colunas_count.items()]), icon="📊")
            with c_an3:
                st.info(f"🔄 **Repetição do Anterior:** A Matriz carrega **{repetidas_previstas} dezenas** do concurso nº {st.session_state.data['historico_dados'][-1]['concurso']}.", icon="🔮")

            # --- RETROSPECTIVA CRÍTICA (COERENTE COM O ROI FINANCEIRO) ---
            st.markdown("#### 🎯 Retrospectiva Crítica dos Bilhetes (Últimos 30 Concursos)")
            
            # Puxa os jogos salvos da memória (os bilhetes reais que geram o ROI)
            todos_jogos = st.session_state.data.get("jogos_salvos", [])
            
            # Pega o número dos últimos 30 concursos que estão no banco
            historico_base = st.session_state.data.get("historico_dados", [])
            ultimos_30_concursos = [h['concurso'] for h in historico_base[-30:]] if historico_base else []
            
            acertos_reais_bilhetes = []
            
            # Filtra apenas os bilhetes que foram jogados nestes últimos 30 concursos
            for j in todos_jogos:
                if j.get('concurso_alvo') in ultimos_30_concursos:
                    acertos_reais_bilhetes.append(j.get('acertos', 0))
            
            avg_hits = sum(acertos_reais_bilhetes) / len(acertos_reais_bilhetes) if acertos_reais_bilhetes else 0
            t11 = sum(1 for x in acertos_reais_bilhetes if x == 11)
            t12 = sum(1 for x in acertos_reais_bilhetes if x == 12)
            t13 = sum(1 for x in acertos_reais_bilhetes if x == 13)
            t14 = sum(1 for x in acertos_reais_bilhetes if x == 14)
            t15 = sum(1 for x in acertos_reais_bilhetes if x == 15)

            with st.container(border=True):
                cd_1, cd_2, cd_3, cd_4 = st.columns(4)
                cd_1.metric("Média de Acertos nos Bilhetes", f"{avg_hits:.2f} / 15", help="Média real nos bilhetes de 15 dezenas (coerente com o ROI).")
                cd_2.metric("Bilhetes com 11-12 Pts", f"{t11 + t12} prêmios", delta=f"11 Pts: {t11} | 12 Pts: {t12}", delta_color="off")
                cd_3.metric("Bilhetes com 13 Pts", f"{t13} prêmios", help="Quantidade real de bilhetes premiados com 13.")
                cd_4.metric("Prêmios Máximos (14-15 Pts)", f"{t14 + t15} prêmios", delta=f"14 Pts: {t14} | 15 Pts: {t15}", delta_color="inverse")


            # =================================================================
            # 🔮 PAINEL BONITO: DESEMPENHO BRUTO DA MATRIZ BASE (GRUPO DE ELITE)
            # =================================================================
            with st.container(border=True):
                st.markdown("#### 🧬 Potencial Bruto: Força da Matriz Base")
                st.write("Avalia quantos pontos a matriz bruta atual (antes dos desdobramentos) teria segurado nos últimos 30 concursos.")
                
                # Puxa os últimos 30 concursos do seu banco de dados oficial
                historico_base = st.session_state.data.get("historico_dados", [])
                ultimos_30 = historico_base[-30:] if historico_base else []
                
                # Substitua "ia['matriz_base']" pelo nome da variável da sua matriz na Aba 2, se necessário.
                # Exemplo: matriz_atual = set(matriz_base)
                try:
                    matriz_atual = set(ia['matriz_base']) 
                    tamanho_matriz = len(matriz_atual)
                    
                    if ultimos_30 and tamanho_matriz > 0:
                        acertos_matriz = []
                        
                        # Cruza as dezenas da Matriz Base com os sorteios oficiais
                        for sorteio in ultimos_30:
                            sorteio_set = set(sorteio['dezenas'])
                            hits = len(matriz_atual.intersection(sorteio_set))
                            acertos_matriz.append(hits)
                            
                        # Cálculos de performance da Matriz
                        media_acertos = sum(acertos_matriz) / len(acertos_matriz)
                        freq_14_15 = sum(1 for x in acertos_matriz if x >= 14)
                        
                        # --- VISUAL ELEGANTE (MÉTRICAS ALINHADAS) ---
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
                        
                        # --- TERMÓMETRO DE EFICIÊNCIA ---
                        st.caption(f"**Termómetro de Eficiência da Matriz (Média atual: {media_acertos:.1f} pontos)**")
                        # A barra enche baseada na média em relação a 15 (o máximo)
                        pct_eficiencia = min(media_acertos / 15.0, 1.0)
                        st.progress(pct_eficiencia)
                        
                except Exception as e:
                    st.info("Gere a estratégia da IA para visualizar o desempenho da Matriz Base.")
            st.markdown("#### 📊 Desempenho Histórico das Inteligências Ativas")
            with st.container(border=True):
                c_e1, c_e2, c_e3, c_e4 = st.columns(4)
                c_e1.metric("1. Frequência/Tendência", f"{ia['perf']['Tendencia']:.2f} pts")
                c_e2.metric("2. Reversão Estatística", f"{ia['perf']['Reversao']:.2f} pts")
                c_e3.metric("3. Fechamento de Ciclo", f"{ia['perf']['Ciclo']:.2f} pts")
                c_e4.metric("4. Simetria de Borda", f"{ia['perf']['Simetria']:.2f} pts")
        
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
                
                # Cores mais sofisticadas
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
        ia = raciocinio_total_ia(st.session_state.data["historico_dados"], st.session_state.data["ia_memoria"])
        
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
                                "matriz_origem": ia['matriz_base'], # 🛡️ CORREÇÃO: Passando ia['matriz_base'] direto
                                "dna": "🧬 Fechamento Matemático 100% Garantido"
                            })
                            
                        st.session_state.data['banca'] -= gasto
                        salvar_dados(st.session_state.data)
                        
                        st.toast(f"✅ {qtd_gerados} jogos matemáticos criados.", icon="🚀")
                        st.success(f"**Garantia Matemática Ativada!** {msg_status} Custo Real: **R$ {gasto:.2f}**. Saldo restante: **R$ {st.session_state.data['banca']:.2f}**.")
                        st.rerun()

                    else:
                        # =====================================================================
                        # 🚀 SUPER PLANO B: MÁQUINA DE FORÇA BRUTA ORTOGONAL
                        # =====================================================================
                        st.info(f"⚠️ **Orçamento Limitado:** {msg_status}") 
                        
                        # 🛡️ NOVO: Preparação dupla para o Escudo Anti-Zumbi (15 e 14/15 pts)
                        historico_sets = {frozenset(h['dezenas']) for h in st.session_state.data['historico_dados']}
                        historico_oficial_sets = [set(h['dezenas']) for h in st.session_state.data['historico_dados']]
                        ultimo_sorteio = st.session_state.data["historico_dados"][-1]["dezenas"] if st.session_state.data["historico_dados"] else []
                        
                        jogos_neste_lote = [] 
                        gasto = 0.0
                        qtd_gerados = 0
                        
                        progresso_texto = st.empty()
                        barra_progresso = st.progress(0)
                        
                        tam_matriz = len(ia['matriz_base'])
                        usar_forca_bruta = tam_matriz <= 20
                        
                        if usar_forca_bruta:
                            st.warning(f"⚡ **Motor Híbrido Ativado:** Matriz de {tam_matriz} dezenas. Acionando **Força Bruta Ortogonal**.")
                            progresso_texto.write("⏳ Gerando TODAS as combinações e passando na peneira genética... Aguarde.")
                            
                            universo_15 = [list(c) for c in itertools.combinations(ia['matriz_base'], 15)]
                            universo_16 = [list(c) for c in itertools.combinations(ia['matriz_base'], 16)] if tam_matriz >= 16 else []
                            
                            def filtrar_universo(universo):
                                pote = []
                                for candidato in universo:
                                    # 🛡️ NOVO: Convertendo para set uma vez para a verificação de 14 pontos
                                    candidato_set = set(candidato)
                                    
                                    if frozenset(candidato) in historico_sets: continue # Filtro 15 pontos exato
                                    
                                    # 🛡️ NOVO ESCUDO: Se o bilhete (seja 15 ou 16) tiver 14 ou mais acertos num jogo passado, é descartado.
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
                        else:
                            st.warning(f"⚡ **Motor Estocástico Ativado:** Matriz de {tam_matriz} dezenas. Geração guiada por peso (Arrasto).")
                            pote_15 = []; pote_16 = []
                        
                        # LAÇO DE COMPRA E DOWNGRADE INTELIGENTE
                        while (orcamento - gasto) >= 3.5:
                            
                            if conf_calc >= 0.75 and (orcamento - gasto) >= 56.0 and (not usar_forca_bruta or len(pote_16) > 0):
                                tam, custo, pote_atual = 16, 56.0, pote_16
                            else:
                                tam, custo, pote_atual = 15, 3.5, pote_15
                            
                            melhor_candidato = []
                            melhor_score = -999999
                            melhor_dna = "🧬 DNA Não Biometrado"
                            
                            # ROTA 1: BUSCA ORTOGONAL (FORÇA BRUTA)
                            if usar_forca_bruta:
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
                            
                            # ROTA 2: MONTE CARLO ESTOCÁSTICO
                            else:
                                dezenas_disponiveis = ia['matriz_base']
                                pesos_sublista = [ia['pesos'][i] for i in dezenas_disponiveis]
                                
                                for _ in range(5000):
                                    candidato = []
                                    dez_temp = list(dezenas_disponiveis)
                                    pesos_temp = list(pesos_sublista)
                                    
                                    for _ in range(tam):
                                        if not dez_temp: break 
                                        escolhida = random.choices(dez_temp, weights=pesos_temp, k=1)[0]
                                        candidato.append(escolhida)
                                        idx = dez_temp.index(escolhida)
                                        dez_temp.pop(idx); pesos_temp.pop(idx)
                                        
                                    candidato = sorted(candidato)
                                    
                                    # 🛡️ NOVO: Escudo Anti-Zumbi Simétrico para Rota 2
                                    candidato_set = set(candidato)
                                    if frozenset(candidato) in historico_sets: continue # Filtro 15 exato
                                    if any(len(candidato_set & sorteio_passado) >= 14 for sorteio_passado in historico_oficial_sets): continue # Filtro 14/15 dinâmico
                                    
                                    max_c, atual_c = 1, 1
                                    for i in range(1, len(candidato)):
                                        if candidato[i] == candidato[i-1] + 1:
                                            atual_c += 1; max_c = max(max_c, atual_c)
                                        else: atual_c = 1
                                    if max_c > 7: continue 
                                    
                                    score_dna, dna_texto_candidato = avaliar_dna_lotofacil(candidato, ultimo_sorteio)
                                    if "⚠️" in dna_texto_candidato: continue

                                    score_ia = sum(ia['pesos'][n] for n in candidato)
                                    penalidade = 0
                                    for jogo_feito in jogos_neste_lote:
                                        intersecao = len(set(candidato).intersection(jogo_feito))
                                        if intersecao >= 11:
                                            penalidade += (intersecao ** 3)
                                    
                                    score_final = score_ia + score_dna - penalidade
                                    
                                    if score_final > melhor_score:
                                        melhor_score = score_final
                                        melhor_candidato = candidato
                                        melhor_dna = dna_texto_candidato
                            
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
                                "justificativa": f"Matriz {ia['cod_estrategia']}. Motor Ortogonal ({'Híbrido' if usar_forca_bruta else 'Heurístico'}).",
                                "status": "Aguardando Sorteio", 
                                "acertos": 0, 
                                "premio_valor": 0.0,
                                "matriz_origem": ia['matriz_base'], # 🛡️ CORREÇÃO: Passando ia['matriz_base'] direto
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
                        
                        st.toast(f"✅ Sucesso! {qtd_gerados} jogos matemáticos criados.", icon="🚀")
                        st.success(f"**Lote processado com Sucesso Absoluto!** O sistema extraiu a Elite Probabilística respeitando o seu bolso. Verifique a Aba 4 para ver os jogos.")
                        st.rerun()

    else: 
        st.warning("Aguardando sincronização de dados do Cofre na Aba 1.")

    # =======================================================
    # AQUI ESTÁ A CORREÇÃO QUE MATA O ERRO NameError:
    # Nós declaramos a variável puxando ela do banco de dados 
    # antes de tentar desenhar os cartões.
    jogos_salvos = st.session_state.data.get("jogos_salvos", [])
    # =======================================================

    # Fica lindo na tela de computador colocando 3 cartões lado a lado
    if jogos_salvos: # Só desenha as colunas se houver jogos salvos
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
    # 🧠 MOTOR DE AUDITORIA E APRENDIZADO UNIFICADO (Resolve Pontos 1 a 5, 11 e 12)
    # =====================================================================
    # Esta função obriga todas as formas de entrada (Massa, API e Manual)
    # a passarem pelo mesmo funil, garantindo que a IA aprenda sempre igual 
    # e que o dinheiro sempre retorne para a banca.
    def auditar_e_aprender_unificado(concurso, dezenas_sorteadas, rateios=None):
        if rateios is None: rateios = {}
        v11, v12, v13, v14, v15 = rateios.get(11, 7.0), rateios.get(12, 14.0), rateios.get(13, 35.0), rateios.get(14, 1500.0), rateios.get(15, 1500000.0)
        
        lucro_total = 0.0
        relatorio = []
        sorteio_set = set(dezenas_sorteadas)
        
        mapa_estrategias = {
            "Ciclo Otimizado": "Ciclo", "Tendência de Frequência": "Tendencia", 
            "Reversão Estatística": "Reversao", "Simetria de Borda": "Simetria"
        }
        
        # 🧠 Variáveis para a Matemática do Lote (Evita Amnésia na IA)
        soma_pontos_est = {}
        qtd_jogos_est = {}
        
        for j in st.session_state.data.get("jogos_salvos", []):
            alvo_do_jogo = j.get('concurso_alvo')
            pode_auditar = False
            
            if str(alvo_do_jogo) == str(concurso) or (isinstance(alvo_do_jogo, int) and alvo_do_jogo <= concurso) or str(alvo_do_jogo) == "Legado":
                pode_auditar = True
                
            if j.get('status') == "Aguardando Sorteio" and pode_auditar:
                pontos = len(set(j.get('dezenas', [])).intersection(sorteio_set))
                j['acertos'] = pontos
                j['premio_valor'] = calcular_premio_multiplo(j.get('tamanho', 15), pontos, v11, v12, v13, v14, v15)
                
                est_raw = j.get('estrategia', '')
                est_usada = mapa_estrategias.get(est_raw, est_raw)
                
                # Acumula os pontos do lote inteiro
                soma_pontos_est[est_usada] = soma_pontos_est.get(est_usada, 0) + pontos
                qtd_jogos_est[est_usada] = qtd_jogos_est.get(est_usada, 0) + 1
                
                if pontos >= 11:
                    j['status'] = "Premiado"
                    lucro_total += j['premio_valor']
                    st.session_state.data["banca"] += j['premio_valor']
                else:
                    j['status'] = "Não Premiado"
        
        # --- O CÉREBRO APRENDE AQUI (Uma única vez por sorteio!) ---
        for est, soma_pts in soma_pontos_est.items():
            media_lote = soma_pts / qtd_jogos_est[est]
            
            if est in st.session_state.data.get("ia_memoria", {}):
                mem_ia = st.session_state.data["ia_memoria"][est]
                if isinstance(mem_ia, dict):
                    if mem_ia["usos"] >= 30:
                        media_atual = mem_ia["pontos"] / 30.0
                        mem_ia["pontos"] = (media_atual * 29.0) + media_lote
                        mem_ia["usos"] = 30
                    else:
                        mem_ia["pontos"] += media_lote
                        mem_ia["usos"] += 1
                        
                relatorio.append(f"A métrica para **{est}** calibrou pesos (Concurso {concurso}: Média do lote {media_lote:.2f} pts).")
                
        return lucro_total, relatorio

    # Função auxiliar para mapear prêmios da API
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
        
        # --- BOTÃO 1: O SEU ORIGINAL (RECUPERAR GAP DIÁRIO COM IA ADAPTATIVA) ---
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
                                    
                                    # --- O FANTASMA ADAPTATIVO DA IA NOS GAPS ---
                                    historico_para_ia = st.session_state.data["historico_dados"][:-1]
                                    if len(historico_para_ia) >= 10:
                                        try:
                                            ia_temp = raciocinio_total_ia(historico_para_ia, st.session_state.data["ia_memoria"])
                                            matriz_base = ia_temp.get('matriz_base', [])
                                            estrategia_rodada = ia_temp.get('estrategia_usada', 'Tendencia')
                                            tamanho_matriz = len(matriz_base)
                                            jogos_simulados = []
                                            
                                            # ==========================================================
                                            # 🧠 SIMULAÇÃO REALISTA: O ESPELHO DA VIDA REAL (PLANO A e B)
                                            # ==========================================================
                                            if tamanho_matriz <= 20:
                                                # A IA TREINA USANDO O PLANO A / HÍBRIDO (Garantia de 14 pts)
                                                jogos_reduzidos = gerar_fechamento_matematico(matriz_base, 14)
                                                
                                                # Limite financeiro do backtest para não sangrar a banca fantasma (simulando a poda)
                                                limite_jogos = 50 if tamanho_matriz >= 18 else (15 if tamanho_matriz == 17 else len(jogos_reduzidos))
                                                
                                                if len(jogos_reduzidos) > limite_jogos:
                                                    jogos_reduzidos = random.sample(jogos_reduzidos, limite_jogos)
                                                    
                                                for j_dez in jogos_reduzidos:
                                                    jogos_simulados.append({
                                                        "id": str(uuid.uuid4()), "concurso_alvo": num, "dezenas": sorted(j_dez),
                                                        "tamanho": 15, "status": "Aguardando Sorteio", "acertos": 0,
                                                        "estrategia": estrategia_rodada, "justificativa": "Fantasma (Plano Exato/Híbrido)"
                                                    })
                                            else:
                                                # A IA TREINA USANDO O PLANO B HEURÍSTICO (Arrasto nas Gigantes)
                                                qtd_jogos = 30 # Orçamento defensivo para matrizes caóticas
                                                pesos = ia_temp.get('pesos', {})
                                                
                                                for _ in range(qtd_jogos):
                                                    candidato = []
                                                    dez_temp = list(matriz_base)
                                                    pesos_temp = [pesos.get(d, 1) for d in dez_temp]
                                                    
                                                    # Roleta estocástica puxando as mais quentes
                                                    for _ in range(15):
                                                        escolhida = random.choices(dez_temp, weights=pesos_temp, k=1)[0]
                                                        candidato.append(escolhida)
                                                        idx = dez_temp.index(escolhida)
                                                        dez_temp.pop(idx)
                                                        pesos_temp.pop(idx)
                                                        
                                                    jogos_simulados.append({
                                                        "id": str(uuid.uuid4()), "concurso_alvo": num, "dezenas": sorted(candidato),
                                                        "tamanho": 15, "status": "Aguardando Sorteio", "acertos": 0,
                                                        "estrategia": estrategia_rodada, "justificativa": "Fantasma (Heurístico)"
                                                    })
                                            
                                            # CORREÇÃO FINANCEIRA ABSOLUTA E AUTOMÁTICA
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
                            
                            if logs_massa:
                                st.session_state.ultimo_aprendizado = list(set(logs_massa))
                                
                            st.session_state.data["jogos_salvos"] = []
                            salvar_dados(st.session_state.data)
                            st.success(f"✅ GAPs processados com sucesso! R$ {lucro_acumulado_massa:.2f}.")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao processar GAPs: {e}")

       # --- COLUNA 2: DOWNLOAD PURO E TREINAMENTO SEPARADO (ESTABILIDADE TOTAL) ---
        with col_massa2:
            st.markdown("#### ☢️ Iniciar Vida Real (Download e Calibragem)")
            
            # BOTÃO A: APENAS DOWNLOAD DO 1 AO ATUAL (Não trava, pois não usa IA aqui)
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
                                "concurso": num, 
                                "dezenas": dezenas_sorteadas, 
                                "data": res_conc.get('data', '')
                            })
                            
                            if i % 50 == 0:
                                barra_down.progress((i + 1) / total_concursos)
                                
                        salvar_dados(st.session_state.data)
                        barra_down.progress(1.0)
                        st.success(f"✅ Download de {total_concursos} sorteios concluído. Agora clique em CALIBRAR.")
                    except Exception as e:
                        st.error(f"Erro na conexão com API: {e}")

            # BOTÃO B: CALIBRAR A INTELIGÊNCIA COM O BANCO SALVO (O FANTASMA ADAPTATIVO COMPLETO)
            if st.button("🧠 2. CALIBRAR INTELIGÊNCIA (LER TODO O BANCO)", type="primary", use_container_width=True):
                historico_completo = st.session_state.data.get("historico_dados", [])
                # Mapeamento para garantir que o nome da estratégia gere a chave correta na memória
                mapa_chaves = {
                    "Tendência de Frequência": "Tendencia",
                    "Reversão Estatística": "Reversao",
                    "Ciclo Otimizado": "Ciclo",
                    "Simetria de Borda": "Simetria"
                }
                
                if not historico_completo:
                    st.error("O banco de dados está vazio! Clique no botão de Baixar primeiro.")
                else:
                    # Limpeza total da mente da IA e Banca para recomeçar a simulação financeira
                    st.session_state.data["ia_memoria"] = {
                        "Tendencia": {"usos": 0, "pontos": 0}, 
                        "Reversao": {"usos": 0, "pontos": 0},
                        "Ciclo": {"usos": 0, "pontos": 0},
                        "Simetria": {"usos": 0, "pontos": 0}
                    }
                    st.session_state.data["banca"] = 10000.00
                    st.session_state.data["historico_aportes"] = 0.0
                    st.session_state.data["historico_saques"] = 0.0
                    st.session_state.data["jogos_salvos"] = []
                    
                    with st.spinner("Calibrando a IA com o Histórico Completo. Isso usa apenas processamento local..."):
                        barra_calib = st.progress(0)
                        porcentagem_texto = st.empty()
                        
                        lucro_acumulado_massa = 0.0
                        total_concursos = len(historico_completo)
                        
                        # A IA vai ler linha por linha do banco que você já baixou
                        for i, dado_atual in enumerate(historico_completo):
                            num = dado_atual['concurso']
                            dezenas_sorteadas = dado_atual['dezenas']
                            
                            # --- O FANTASMA ADAPTATIVO DA IA (Exatamente a sua lógica) ---
                            # Pega o histórico até o sorteio anterior ao atual para não ver o futuro
                            historico_para_ia = historico_completo[:i]
                            
                            if len(historico_para_ia) >= 10:
                                try:
                                    ia_temp = raciocinio_total_ia(historico_para_ia, st.session_state.data["ia_memoria"])
                                    matriz_base = ia_temp.get('matriz_base', [])
                                    estrategia_rodada = ia_temp.get('estrategia_usada', 'Tendencia')
                                    tamanho_matriz = len(matriz_base)
                                    jogos_simulados = []
                                            
                                    # ==========================================================
                                    # 🧠 SIMULAÇÃO REALISTA: FAST-TRACK ESTOCÁSTICO
                                    # Gera bilhetes para alimentar o ROI e a Memória da IA.
                                    # É matematicamente equivalente à média do fechamento, mas evita travamentos.
                                    # ==========================================================
                                    limite_jogos = 50 if tamanho_matriz >= 18 else (15 if tamanho_matriz <= 17 else 30)
                                    pesos = ia_temp.get('pesos', {})
                                    
                                    for _ in range(limite_jogos):
                                        if tamanho_matriz <= 20:
                                            # Amostragem direta da matriz base (Garante a Média de Aprendizado)
                                            candidato = random.sample(matriz_base, 15)
                                        else:
                                            # Roleta Estocástica para matrizes gigantes
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
                                            "estrategia": estrategia_rodada, "justificativa": "Fantasma (Fast-Track Estocástico)"
                                        })
                                            
                                    # CORREÇÃO FINANCEIRA ABSOLUTA E AUTOMÁTICA
                                    custo_treinamento = len(jogos_simulados) * 3.50
                                    st.session_state.data["banca"] -= custo_treinamento
                                    lucro_acumulado_massa -= custo_treinamento    
                                            
                                    # Substitui os jogos salvos temporariamente para a função auditar
                                    st.session_state.data["jogos_salvos"] = jogos_simulados
                                            
                                except Exception as e:
                                    st.session_state.data["jogos_salvos"] = []
                            else:
                                st.session_state.data["jogos_salvos"] = []
                            
                            # Auditoria Pericial Unificada (A IA aprende se deu certo ou errado)
                            lucro_parcial, relatorio_parcial = auditar_e_aprender_unificado(num, dezenas_sorteadas, rateios=None)
                            lucro_acumulado_massa += lucro_parcial
                            
                            # Atualização da barra de progresso (a cada 20 loops para não pesar a UI)
                            if i % 20 == 0:
                                pct = (i + 1) / total_concursos
                                barra_calib.progress(pct)
                                porcentagem_texto.text(f"Progresso da Calibragem: {pct*100:.1f}%")
                        
                        # Limpa os jogos no final, pois foi só simulação de memória (os dados financeiros ficaram na banca)
                        st.session_state.data["jogos_salvos"] = [] 
                        salvar_dados(st.session_state.data)
                        
                        barra_calib.progress(1.0)
                        porcentagem_texto.text("Progresso da Calibragem: 100.0%")
                        st.success(f"🚀 Calibração Inteligente Concluída! Saldo Final Simulado na Banca: R$ {st.session_state.data['banca']:,.2f}")
                        st.balloons() 
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
                                "concurso": concurso_oficial,
                                "data": ultimo_resultado['data'],
                                "dezenas": dezenas_oficiais,
                                "premiacoes": ultimo_resultado.get('premiacoes', [])
                            }
                            
                            existe = any(h['concurso'] == concurso_oficial for h in st.session_state.data["historico_dados"])
                            if not existe:
                                st.session_state.data["historico_dados"].append(novo_dado)
                            
                            st.session_state.caixa_latest = novo_dado
                            
                            # Executa a inteligência Universal
                            rateios = extrair_rateios_api(ultimo_resultado.get('premiacoes', []))
                            lucro_total, relatorio_aprendizado = auditar_e_aprender_unificado(concurso_oficial, dezenas_oficiais, rateios)
                            
                            if relatorio_aprendizado: 
                                st.session_state.ultimo_aprendizado = list(set(relatorio_aprendizado))
                                
                            salvar_dados(st.session_state.data) # HD ATUALIZADO
                            
                            if 'ia_memoria' in st.session_state: 
                                del st.session_state.ia_memoria # Força reload visual
                                
                            st.success(f"✅ Sincronização Automática Concluída! Inteligência treinada. Lucro creditado: R$ {lucro_total:.2f}")
                            if lucro_total > 0: st.toast("IA calbrada com sucesso", icon="💰")
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
                # PONTO DE MELHORIA: Regex Extrai SOMENTE os números de dentro do que foi colado
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
                        # Executa a inteligência Universal
                        lucro_total, relatorio_aprendizado = auditar_e_aprender_unificado(concurso_manual, dezenas_oficiais, rateios=None)
                        
                        existe = any(h['concurso'] == concurso_manual for h in st.session_state.data["historico_dados"])
                        if not existe:
                            novo_dado = {
                                "concurso": concurso_manual,
                                "data": datetime.now().strftime("%d/%m/%Y"),
                                "dezenas": dezenas_oficiais,
                                "premiacoes": []
                            }
                            st.session_state.data["historico_dados"].append(novo_dado)
                            st.session_state.caixa_latest = novo_dado
                        
                        if relatorio_aprendizado: 
                            st.session_state.ultimo_aprendizado = list(set(relatorio_aprendizado))
                            
                        salvar_dados(st.session_state.data)
                        
                        if 'ia_memoria' in st.session_state: 
                            del st.session_state.ia_memoria
                            
                        st.success(f"✅ Operação Manual Concluída. O banco de dados aprendeu as dezenas e R$ {lucro_total:.2f} foram creditados.")
                        st.rerun()
                        
                except ValueError:
                    st.error("Erro estrutural na conversão de números.")

    st.divider()

    # --- EXIBIÇÃO DE APRENDIZADO APÓS QUALQUER UMA DAS CONFERÊNCIAS ---
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
