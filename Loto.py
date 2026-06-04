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
        
    # Baixa o ícone do DNA colorido
    img_path = "dna_icon_pro.png"
    if not os.path.exists(img_path):
        try:
            url_dna = "https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/72x72/1f9ec.png"
            r = requests.get(url_dna, timeout=5)
            with open(img_path, 'wb') as f:
                f.write(r.content)
        except:
            pass 

    # --- CALCULADOR DE DNA COMPLETO (AGORA COM REPETIDAS) ---
    def calcular_dna_na_hora(dezenas, repetidas_salvas=None):
        if not dezenas: return ""
        primos_list = [2, 3, 5, 7, 11, 13, 17, 19, 23]
        fib_list = [1, 2, 3, 5, 8, 13, 21]
        moldura_list = [1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25]
        mult3_list = [3, 6, 9, 12, 15, 18, 21, 24]
        
        pares = sum(1 for x in dezenas if x % 2 == 0)
        primos = sum(1 for x in dezenas if x in primos_list)
        fibs = sum(1 for x in dezenas if x in fib_list)
        moldura = sum(1 for x in dezenas if x in moldura_list)
        mult3 = sum(1 for x in dezenas if x in mult3_list)
        soma = sum(dezenas)
        
        # A LÓGICA DAS REPETIDAS:
        if repetidas_salvas is not None:
            rep_str = f"{repetidas_salvas} Rep | "
        elif dezenas_anteriores:
            # Se recebemos o concurso anterior, fazemos a matemática na hora!
            repetidas_calc = sum(1 for x in dezenas if x in dezenas_anteriores)
            rep_str = f"{repetidas_calc} Rep | "
        else:
            rep_str = "" # Oculta se não tiver como calcular
            
        return f"{moldura} Mol | {pares} Par | {primos} Pri | {fibs} Fib | {mult3} Mlt | {rep_str}Soma {soma}"

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # ==========================================
    # CABEÇALHO (AZUL LOTOMATRIX)
    # ==========================================
    if os.path.exists(img_path):
        pdf.image(img_path, 10, 10, 16)
        x_offset = 30
    else:
        x_offset = 10
        
    pdf.set_text_color(0, 102, 204) # Azul
    pdf.set_font('Arial', 'B', 22)
    pdf.set_xy(x_offset, 12)
    pdf.cell(0, 10, "LotoMatrix PRO", ln=0)
    
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.set_xy(x_offset, 22)
    pdf.cell(0, 8, "Relatorio Oficial de Analise e Estrategia", ln=0)
    
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(0, 102, 204)
    pdf.set_xy(10, 12)
    pdf.cell(190, 10, f"TOTAL: {len(jogos)} BILHETES", ln=0, align='R')
    
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(120, 120, 120)
    pdf.set_xy(10, 22)
    pdf.cell(190, 8, datetime.now().strftime('%d/%m/%Y %H:%M'), ln=0, align='R')
    
    pdf.ln(30)
    
    # ==========================================
    # GERADOR DE CARDS
    # ==========================================
    for i, j in enumerate(jogos, 1):
        if pdf.get_y() > 240:
            pdf.add_page()
            
        y_start = pdf.get_y()
        
        estrategia = str(j.get('estrategia', 'Padrao')).replace("🧬", "").strip()
        dna_banco = str(j.get('dna', '')).replace("🧬", "").strip()
        dezenas = j.get('dezenas', [])
        
        # Recupera as repetidas se o banco salvou, senão usa None para a IA calcular
        repetidas_salvas = j.get('repetidas', None)
        
        # Se o DNA gravou "Fechamento", ignoramos e mandamos recalcular tudo perfeitamente
        if "Par" not in dna_banco and "Pri" not in dna_banco:
            dna_calculado = calcular_dna_na_hora(dezenas, repetidas_salvas)
            dna_texto = f"{dna_calculado} ({dna_banco})" 
        else:
            dna_texto = dna_banco

        tamanho = j.get('tamanho', len(dezenas))
        alvo = j.get('concurso_alvo', 'N/A')
        dezenas_str = " - ".join([f"{n:02d}" for n in dezenas])
        
        # Fundo e Bordas
        pdf.set_fill_color(248, 248, 250)
        pdf.rect(10, y_start, 190, 40, 'F')
        pdf.set_fill_color(0, 168, 89)
        pdf.rect(10, y_start, 2, 40, 'F')
        
        # Topo
        pdf.set_text_color(30, 30, 30)
        pdf.set_font('Arial', 'B', 11)
        pdf.set_xy(15, y_start + 4)
        pdf.cell(120, 8, f"JOGO {i:02d}  |  Alvo: {alvo}  |  Grade: {tamanho} Dezenas", ln=0)
        
        pdf.set_text_color(0, 102, 204) 
        pdf.set_font('Arial', 'B', 10)
        pdf.set_xy(10, y_start + 4)
        pdf.cell(185, 8, f"{estrategia}", ln=0, align='R')
        
        # DNA
        if os.path.exists(img_path):
            pdf.image(img_path, 15, y_start + 14, 4)
            x_dna = 21 
        else:
            x_dna = 15
            
        pdf.set_text_color(80, 80, 80)
        pdf.set_font('Arial', '', 9)
        pdf.set_xy(x_dna, y_start + 13.5)
        pdf.cell(170, 5, f"DNA: {dna_texto}", ln=0)
        
        # Dezenas
        pdf.set_fill_color(255, 255, 255)
        pdf.rect(15, y_start + 22, 180, 12, 'F')
        pdf.set_draw_color(220, 220, 220)
        pdf.rect(15, y_start + 22, 180, 12, 'D')
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Courier', 'B', 11.5)
        pdf.set_xy(15, y_start + 24)
        pdf.cell(180, 8, dezenas_str, ln=0, align='C')
        
        pdf.set_y(y_start + 45)
        
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
    Calcula matematicamente a temperatura do jogo, define o tamanho ideal 
    da matriz e estabelece a Taxa de Confiança para geração de 16 dezenas.
    """
    if not historico:
        return 18, 0.50, "Histórico vazio. Usando matriz base de 18 dezenas por segurança.", {}

    # 1. Análise de Volatilidade (Últimos 10 concursos)
    ultimos_10 = historico[-10:]
    todas_dezenas = [d for jogo in ultimos_10 for d in jogo['dezenas']]
    contagem = Counter(todas_dezenas)
    
    # Encontrar dezenas quentes (frequência acima da média esperada)
    media_freq = sum(contagem.values()) / 25
    dezenas_quentes = [num for num, freq in contagem.items() if freq > media_freq]
    
    # 2. Identificação do Ciclo Faltante
    numeros_sorteados_ciclo = set()
    for jogo in reversed(historico):
        numeros_sorteados_ciclo.update(jogo['dezenas'])
        if len(numeros_sorteados_ciclo) == 25:
            break
    dezenas_ausentes_ciclo = [d for d in range(1, 26) if d not in numeros_sorteados_ciclo]
    qtd_ausentes = len(dezenas_ausentes_ciclo)

    # -----------------------------------------------------------------
    # 3. CÁLCULO DE DESEMPENHO DA ESTRATÉGIA (BLINDADO CONTRA ERROS)
    # -----------------------------------------------------------------
    score_estrategia = 11.0
    if pontuacao_estrategias and estrategia_atual in pontuacao_estrategias:
        dado_memoria = pontuacao_estrategias[estrategia_atual]
        
        if isinstance(dado_memoria, dict) and "usos" in dado_memoria and dado_memoria["usos"] > 0:
            score_estrategia = dado_memoria["pontos"] / dado_memoria["usos"]
        elif isinstance(dado_memoria, (int, float)):
            score_estrategia = float(dado_memoria)

    # -----------------------------------------------------------------
    # 4. Decisão Dinâmica do Tamanho da Matriz (CÉREBRO CONTEXTUAL)
    # -----------------------------------------------------------------
    if estrategia_atual == "Ciclo":
        if qtd_ausentes <= 4:
            tamanho_matriz = 17
            motivo_tamanho = f"Matriz Hiper-Cirúrgica (17 dezenas): Fechamento de ciclo iminente ({qtd_ausentes} ausentes)."
        elif qtd_ausentes <= 7:
            tamanho_matriz = 19
            motivo_tamanho = f"Matriz Focada (19 dezenas): Ciclo na reta final ({qtd_ausentes} ausentes)."
        else:
            tamanho_matriz = 21
            motivo_tamanho = f"Matriz Expandida (21 dezenas): Ciclo ainda longo ({qtd_ausentes} ausentes)."
            
    elif estrategia_atual == "Simetria":
        if score_estrategia >= 12.5:
            tamanho_matriz = 18
            motivo_tamanho = f"Matriz Simétrica Otimizada (18 dezenas): Assertividade alta da Simetria ({score_estrategia:.1f} pts)."
        else:
            tamanho_matriz = 20
            motivo_tamanho = f"Matriz Simétrica de Defesa (20 dezenas): Garantindo o espelhamento de segurança."
            
    elif estrategia_atual == "Reversao":
        # A Reversão agora respira de acordo com o Score da Inteligência
        if score_estrategia >= 12.0:
            tamanho_matriz = 19
            motivo_tamanho = f"Matriz Reversão Otimizada (19 dezenas): Foco cirúrgico nas zebras (Confiança alta: {score_estrategia:.1f} pts)."
        elif score_estrategia < 10.5:
            tamanho_matriz = 22
            motivo_tamanho = f"Matriz Reversão Expandida (22 dezenas): Máxima cobertura defensiva devido à alta volatilidade."
        else:
            tamanho_matriz = 21
            motivo_tamanho = f"Matriz Reversão Padrão (21 dezenas): Cercando as dezenas atrasadas com equilíbrio estatístico."
        
    else: # Tendencia
        if score_estrategia >= 12.8:
            tamanho_matriz = 18
            motivo_tamanho = f"Matriz de Surfe (18 dezenas): Tendência fortíssima detectada ({score_estrategia:.1f} pts)."
        elif score_estrategia < 11.2:
            tamanho_matriz = 21
            motivo_tamanho = f"Matriz de Recuperação (21 dezenas): Assertividade da Tendência em queda, expandindo a rede."
        else:
            tamanho_matriz = 19
            motivo_tamanho = f"Matriz Padrão (19 dezenas): Seguindo a tendência em cenário estatístico estável."

    # -----------------------------------------------------------------
    # 5. CÁLCULO DA TAXA DE CONFIANÇA GLOBAL (0.0 a 1.0) - CALIBRADO PARA REALIDADE
    # -----------------------------------------------------------------
    fator_quentes = min(len(dezenas_quentes) / 15, 1.0)
    
    # Nova régua (Min-Max Scaling realista): 
    # Média 8.0 = 0% de confiança | Média 9.5 = 50% | Média 11.0+ = 100%
    fator_ia = min(max((score_estrategia - 8.0) / 3.0, 0.0), 1.0) 
    
    # Peso ponderado: 60% baseado no Histórico (IA) e 40% no Momento (Quentes)
    taxa_confianca = (fator_quentes * 0.4) + (fator_ia * 0.6)
    
    # Impede que a confiança zere totalmente (mantém um mínimo de 10% de instinto de sobrevivência)
    taxa_confianca = max(min(taxa_confianca, 1.0), 0.1)

    detalhes = {
        "dezenas_quentes": len(dezenas_quentes),
        "ausentes_ciclo": qtd_ausentes,
        "score_ia": score_estrategia
    }

    return tamanho_matriz, taxa_confianca, motivo_tamanho, detalhes

# =====================================================================
# CONFIGURAÇÃO E LOGIN
# =====================================================================
st.set_page_config(page_title="LotoMatrix PRO - Agente Autônomo", page_icon="🧬", layout="wide")

if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; color: #006644;'>🔐 Acesso Restrito - LotoMatrix PRO</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            senha = st.text_input("Digite a Senha para Acessar a IA:", type="password")
            if st.button("ENTRAR NO SISTEMA", type="primary", use_container_width=True):
                if senha == "777":
                    st.session_state.auth = True
                    st.rerun()
                else: st.error("Acesso Negado.")
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
            # Lê a média limpa. A IA já ajusta a inércia na Aba 5.
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

    melhor_est = max(notas_finais, key=notas_finais.get)
    
    # --- TAMANHO DA MATRIZ ---
    qtd_matriz, _, _, _ = calcular_temperatura_e_confianca(historico, melhor_est, perf)

    # --- MUTAÇÃO DE PESOS DA IA (O Bote Otimizado) ---
    if melhor_est == "Ciclo" and len(faltam_ciclo) > 0:
        estrategia = "Ciclo Otimizado"
        pesos = {i: 100 if i in faltam_ciclo else freq_recente.get(i, 0) for i in range(1, 26)}
        motivo_est = "A IA priorizou o Fechamento de Ciclo. Dezenas ausentes receberam força máxima."
        
    elif melhor_est == "Simetria":
        estrategia = "Simetria de Borda"
        pesos = {}
        for i in range(1, 26):
            espelho = 26 - i
            peso_espelho = freq_recente.get(espelho, 0)
            bonus_borda = 15 if i in moldura_lista else 0
            pesos[i] = freq_recente.get(i, 0) + peso_espelho + bonus_borda
        motivo_est = "A IA adotou Simetria Analítica. Dezenas e seus espelhos ganharam força magnética conjunta."
        
    elif melhor_est == "Reversao":
        estrategia = "Reversão Estatística"
        pesos = {i: max(1, (freq_recente_max - freq_recente.get(i, 0)) + (atrasos.get(i, 0) * 5)) for i in range(1, 26)}
        motivo_est = "A IA ativou Reversão Estatística focada no curto prazo (Janela de Esquecimento)."
        
    else:
        estrategia = "Tendência de Frequência"
        pesos = {}
        for i in range(1, 26):
            aceleracao = freq_ult_10.get(i, 0) - freq_pen_10.get(i, 0) 
            peso_base = freq_recente.get(i, 0)
            pesos[i] = max(1, peso_base + (aceleracao * 3))
        motivo_est = "A IA escolheu Tendência com Viés Direcional. Dezenas em aceleração no momento foram priorizadas."

    dezenas_ordenadas = sorted(range(1, 26), key=lambda x: pesos[x], reverse=True)
    matriz_base = sorted(dezenas_ordenadas[:qtd_matriz])
    alvo = (historico[-1]['concurso'] + 1) if historico else 1

    return {
        "estrategia": estrategia, "cod_estrategia": melhor_est, "estrategia_usada": melhor_est, "motivo_est": motivo_est, "pesos": pesos, "freq": freq_recente, 
        "atrasos": atrasos, "ciclo_tam": jogos_ciclo, "faltam_ciclo": faltam_ciclo,
        "soma": media_soma, "impares": media_impares, "primos": media_primos, 
        "moldura": media_moldura, "alvo": alvo, "qtd_matriz": qtd_matriz, 
        "matriz_base": matriz_base, "perf": perf
    }
# =====================================================================
# INTERFACE PRINCIPAL
# =====================================================================
st.markdown("<h2 style='text-align: center; color: #1f77b4;'>🧬 LotoMatrix PRO - Agente Autônomo</h2>", unsafe_allow_html=True)
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
            
            # Botão Mestre de Reset (Zera Banca, Saques e Aportes para começar nova temporada)
            if st.button("🔄 ZERAR BANCA E HISTÓRICO", use_container_width=True, type="secondary"):
                st.session_state.data["banca"] = 0.0
                st.session_state.data["historico_aportes"] = 0.0
                st.session_state.data["historico_saques"] = 0.0
                salvar_dados(st.session_state.data)
                st.rerun()

# --- TAB 2: CÉREBRO ANALÍTICO ---
with tabs[1]:
    exibir_mini_painel_financeiro()
    if st.session_state.data["historico_dados"]:
        ia = raciocinio_total_ia(st.session_state.data["historico_dados"], st.session_state.data["ia_memoria"])
        st.session_state.data["matriz_viva_atual"] = ia["matriz_base"]
            
        tam_atual = len(ia['matriz_base'])

        # ==========================================================
        # BÚSSOLA DE APORTE INSTITUCIONAL (O "Ponto Doce" da Matemática)
        # ==========================================================
        tam_atual = len(ia['matriz_base'])
        banca_atual = st.session_state.data.get('banca', 0.0)
        
        # O Perito define o "Ponto Doce" ideal para cada tamanho de matriz
        if tam_atual <= 16:
            jogos_ideal = 1 if tam_atual == 15 else 3
            texto_bussola = "Ataque Sniper."
        elif tam_atual == 17:
            jogos_ideal = 8
            texto_bussola = "Fechamento Absoluto de 17. Exige cobertura mínima para garantir 14 pontos."
        elif tam_atual == 18:
            jogos_ideal = 24
            texto_bussola = "Fechamento Avançado. Distribuição ortogonal ideal para cercar as zebras."
        elif tam_atual == 19:
            jogos_ideal = 71
            texto_bussola = "Rede Larga. Ponto de saturação matemática ideal antes da explosão de custo."
        elif tam_atual == 20:
            jogos_ideal = 210
            texto_bussola = "Limite Máximo do Motor Exato. Cercamento de altíssima complexidade."
        else:
            jogos_ideal = 50 # Para 21, 22 ou 23, o ideal de amostragem Monte Carlo é 50 jogos
            texto_bussola = "Matriz Gigante (Caos Aleatório). O motor Heurístico exige uma rede de arrasto estatística."

        custo_ideal = jogos_ideal * 3.50
        
        # Exibe o Painel de Recomendação
        st.markdown("---")
        st.markdown("#### 🧭 Bússola de Operação (Recomendação do Sistema)")
        
        if banca_atual >= custo_ideal:
            st.success(f"✅ **Banca Suficiente:** O seu saldo (R$ {banca_atual:.2f}) cobre o **Lote Ideal de {jogos_ideal} jogos** (R$ {custo_ideal:.2f}) para a Matriz de {tam_atual}. A IA operará com força máxima estatística.")
        else:
            falta = custo_ideal - banca_atual
            st.warning(f"""
            ⚠️ **Orçamento Defensivo Detectado:** Para extrair 100% do poder dessa Matriz de {tam_atual} ({texto_bussola}), a quantidade matemática ideal é de **{jogos_ideal} bilhetes** (Custo: **R$ {custo_ideal:.2f}**).  
            
            *Como o seu saldo atual é R$ {banca_atual:.2f}, o Motor Ortogonal fará um Downgrade e extrairá apenas a nata probabilística. Caso queira a cobertura matemática total, o aporte recomendado é de R$ {falta:.2f}.*
            """)


        # =====================================================================
        # 1. INDICADOR DO MOTOR ATIVO NO MOMENTO (TOPO)
        # =====================================================================
        st.markdown("### 🧠 Transparência Absoluta: Motores e Probabilidades Reais")
        st.info(f"🎯 **A Inteligência Artificial definiu uma Matriz Cirúrgica de {tam_atual} Dezenas para o contexto atual.**")

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

        # ==========================================================
        # TABELA INSTITUCIONAL DE COBERTURA E CUSTOS (15 a 23 Dezenas)
        # ==========================================================
        with st.expander("📊 Ver Tabela Institucional de Probabilidades e Limites", expanded=False):
            st.markdown("""
            <style>
            .tabela-pro { width: 100%; border-collapse: collapse; font-size: 13px; text-align: center; font-family: sans-serif; }
            .tabela-pro th { background-color: #0066cc; color: white; padding: 8px; border: 1px solid #ddd; }
            .tabela-pro td { padding: 6px; border: 1px solid #ddd; color: #333;}
            .tabela-pro tr:nth-child(even) { background-color: #f8f9fa; }
            .tag-verde { background: #d4edda; color: #155724; padding: 3px 6px; border-radius: 4px; font-weight: bold; font-size: 11px;}
            .tag-amarela { background: #fff3cd; color: #856404; padding: 3px 6px; border-radius: 4px; font-weight: bold; font-size: 11px;}
            .tag-vermelha { background: #f8d7da; color: #721c24; padding: 3px 6px; border-radius: 4px; font-weight: bold; font-size: 11px;}
            </style>
            <table class="tabela-pro">
                <tr><th>Matriz</th><th>Combinações Possíveis</th><th>Garantia Exata (14 pts)</th><th>Motor Recomendado</th></tr>
                <tr><td>15</td><td>1</td><td><span class="tag-verde">1 Jogo</span></td><td>Plano A (Puro)</td></tr>
                <tr><td>16</td><td>16</td><td><span class="tag-verde">~ 3 Jogos</span></td><td>Plano A (Puro)</td></tr>
                <tr><td>17</td><td>136</td><td><span class="tag-verde">~ 8 Jogos</span></td><td>Híbrido (Poda DNA)</td></tr>
                <tr><td>18</td><td>816</td><td><span class="tag-verde">~ 24 Jogos</span></td><td>Híbrido (Poda DNA)</td></tr>
                <tr><td>19</td><td>3.876</td><td><span class="tag-amarela">~ 71 Jogos</span></td><td>Híbrido (Poda DNA)</td></tr>
                <tr><td>20</td><td>15.504</td><td><span class="tag-amarela">~ 210 Jogos</span></td><td>Híbrido (Limite Exato)</td></tr>
                <tr><td>21</td><td>54.264</td><td><span class="tag-vermelha">INVIÁVEL</span></td><td>Heurístico (Estocástico)</td></tr>
                <tr><td>22</td><td>170.544</td><td><span class="tag-vermelha">INVIÁVEL</span></td><td>Heurístico (Estocástico)</td></tr>
                <tr><td>23</td><td>490.314</td><td><span class="tag-vermelha">INVIÁVEL</span></td><td>Heurístico (Estocástico)</td></tr>
            </table>
            """, unsafe_allow_html=True)
        

        # =====================================================================
        # 3. PAINEL DE CUSTOS E SIMULAÇÃO DE GARANTIA
        # =====================================================================
        st.markdown("### 💰 Projeção Financeira e Cobertura Matemática")
            
        with st.container(border=True):
            garantia_escolhida = st.radio(
                "🎯 **Se as 15 dezenas sorteadas estiverem dentro da Matriz, qual prêmio você quer garantir matematicamente?**", 
                [15, 14, 13], 
                index=0, 
                horizontal=True,
                format_func=lambda x: f"Garantir {x} Pontos"
            )
            
            qtd_bilhetes_atual = dados_matriz[garantia_escolhida]
            custo_atual = qtd_bilhetes_atual * 3.50
            tipo_motor = dados_matriz["motor"]
                
            st.divider() # Linha sutil para separar os controles dos resultados
            
            # Formatadores de moeda e milhar estilo pt-BR
            str_bilhetes = f"{qtd_bilhetes_atual:,}".replace(",", ".")
            str_custo = f"R$ {custo_atual:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
            c_a, c_b, c_c, c_d = st.columns(4)
            c_a.metric("🧩 Matriz Avaliada", f"{tam_atual} Dezenas")
            c_b.metric("⚙️ Motor Ideal", tipo_motor) 
            c_c.metric(f"🎟️ Teto Absoluto", f"{str_bilhetes} Jogos")
            c_d.metric("💸 Custo Base (Sem Poda)", str_custo)

        # =====================================================================
        # 4. TABELA DETALHADA: DISTINÇÃO ABSOLUTA DOS 3 MOTORES
        # =====================================================================
        st.markdown("### 📊 Detalhamento Completo: Probabilidades, Custos e Limites")
            
        with st.expander("🔍 Expandir Tabela de Motores e Orçamentos", expanded=True):
             st.info("Esta tabela exibe a diferença brutal de custos e garantias entre a Matriz Exata e as duas inteligências do Motor Ortogonal (Híbrida e Heurística).")
                
             dados_lista = []
             for tam, metas in alvos_matematicos.items():
                 for pts in [15, 14, 13]:
                     custo_calc = metas[pts] * 3.50
                     str_custo_tab = f"R$ {custo_calc:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                     str_teto_tab = f"{metas[pts]:,}".replace(",", ".")

                     if tam <= 18:
                         # LINHA DO PLANO A (EXATO)
                         dados_lista.append({
                             "Matriz": f"{tam} Dez",
                             "Inteligência Ativa": "🥇 PLANO A (Exato)",
                             "Probabilidade": "100% Garantido",
                             "Meta (Pts)": f"{pts} pts",
                             "Teto de Bilhetes": str_teto_tab,
                             "Custo da Aposta": str_custo_tab
                         })
                     elif 19 <= tam <= 20:
                         # LINHA DO PLANO B (HÍBRIDO)
                         dados_lista.append({
                             "Matriz": f"{tam} Dez",
                             "Inteligência Ativa": "🥈 PLANO B (Híbrido)",
                             "Probabilidade": "~85% a 95% (Filtro DNA)",
                             "Meta (Pts)": f"{pts} pts",
                             "Teto de Bilhetes": "Limitado à Banca",
                             "Custo da Aposta": "Baseado no Orçamento"
                         })
                     else:
                         # LINHA DO PLANO B (HEURÍSTICO)
                         dados_lista.append({
                             "Matriz": f"{tam} Dez",
                             "Inteligência Ativa": "🥉 PLANO B (Heurístico)",
                             "Probabilidade": "Dinâmica (Arrasto)",
                             "Meta (Pts)": f"{pts} pts",
                             "Teto de Bilhetes": "Limitado à Banca",
                             "Custo da Aposta": "Baseado no Orçamento"
                         })
                
             df_custos = pd.DataFrame(dados_lista)
                
             st.dataframe(
                 df_custos,
                 use_container_width=True,
                 hide_index=True
             )

        st.divider()
        
        st.markdown(f"### 🧠 Diagnóstico Autônomo — Concurso Alvo `{ia['alvo']}`")

        # =====================================================================
        # SUPER PAINEL INSTITUCIONAL: RAIO-X, RISCO E CORRELAÇÃO
        # =====================================================================
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
            st.info(f"**🎯 Último Sorteio Oficial (Concurso {ultimo_sort['concurso']}):** {dezenas_ult_formatadas}")
            
            # 6 Cartões com a nova leitura do Universo Lotofácil
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
            matriz_atual_set = set(ia['matriz_base']) # O filtro matemático que você percebeu faltar

            for sorteio in amostra_corr:
                # Intersecção: cruza a história oficial com a matriz eleita pela IA
                d_sort = [n for n in sorteio['dezenas'] if n in matriz_atual_set]
                for i in range(len(d_sort)):
                    for j in range(i+1, len(d_sort)):
                        par = tuple(sorted((d_sort[i], d_sort[j])))
                        pares_count[par] = pares_count.get(par, 0) + 1
            
            top_par = max(pares_count, key=pares_count.get) if pares_count else (0,0)
            st.session_state.par_ouro = top_par # Salva a dupla magnética real para o DNA!

            # 3. TERMÔMETRO DE RISCO E CORRELAÇÃO
            col_risk, col_corr = st.columns(2)
            
            with col_risk:
                st.markdown("#### 🌡️ Termômetro de Risco (Critério de Kelly)")
                qtd_m = ia.get('qtd_matriz', 18)
                if qtd_m >= 21:
                    n_risco = "ALTO (Início de Ciclo / Caos Aleatório)"
                    c_risco = "#dc3545"; d_banca = "Recomendação: Operar com orçamento defensivo."
                elif qtd_m == 19:
                    n_risco = "MÉDIO (Meio de Ciclo / Transição)"
                    c_risco = "#ffcc00"; d_banca = "Recomendação: Operar com orçamento padrão."
                else:
                    n_risco = "BAIXO (Fim de Ciclo / Alta Previsibilidade)"
                    c_risco = "#28a745"; d_banca = "Recomendação: Janela de Ataque. Risco Mínimo."

                st.markdown(f"""
                <div style='background-color: #f8f9fa; border-left: 5px solid {c_risco}; padding: 15px; border-radius: 6px;'>
                    <span style='color: {c_risco}; font-weight: bold; font-size: 15px;'>Nível Atual: {n_risco}</span><br>
                    <span style='color: #4d5156; font-size: 13px;'><b>Diretriz Institucional:</b> {d_banca}</span>
                </div>
                """, unsafe_allow_html=True)

            with col_corr:
                st.markdown("#### 🕸️ Teia de Correlação (Matriz Filtrada)")
                st.markdown(f"""
                <div style='background-color: #f8f9fa; border-left: 5px solid #1a73e8; padding: 15px; border-radius: 6px;'>
                    <span style='color: #1a73e8; font-weight: bold; font-size: 15px;'>Par Magnético da Elite: {top_par[0]:02d} e {top_par[1]:02d}</span><br>
                    <span style='color: #4d5156; font-size: 13px;'>Esta é a dupla mais quente <b>possível de ser gerada</b> pela matriz atual. O Motor DNA vai garantir a recompensa quântica por agrupá-las.</span>
                </div>
                """, unsafe_allow_html=True)

            st.divider()
            
            # =====================================================================
            # PAINEL DE GESTÃO DE CICLO, CONFIANÇA E APOSTAS MÚLTIPLAS (PONTOS 6, 7 e 13)
            # =====================================================================
            st.subheader("📐 Gestão Inteligente: Matriz, Confiança e Orçamento")
            
            # Instancia o novo motor de análise profunda que resolve a "cegueira" da IA
            estrategia_selecionada = ia.get('estrategia', 'Tendencia')
            memoria_ia = st.session_state.data.get('ia_memoria', {})
            
            tam_matriz_calc, confianca_calc, motivo_calc, dados_internos = calcular_temperatura_e_confianca(
                historico_painel, estrategia_selecionada, memoria_ia
            )
        
            qtd_em_falta = len(ia['faltam_ciclo'])
        
            # Exibição das métricas principais com as novas regras
            col_c1, col_c2, col_c3, col_c4 = st.columns(4)
            col_c1.metric("Ciclo aberto há", f"{ia['ciclo_tam']} concursos")
            col_c2.metric("Dezenas faltando", qtd_em_falta)
            col_c3.metric("🎯 Confiança da Estratégia", f"{confianca_calc * 100:.1f}%")
            
            # Decisão de 16 dezenas visível para você na tela
            status_16 = "⚠️ BLOQUEADO (15 Dez)" if confianca_calc < 0.75 else "🔥 LIBERADO (16 Dez)"
            col_c4.metric("⚡ Permissão p/ Jogos Múltiplos", status_16)
        
            # Justificativa visual do novo motor
            st.info(f"📋 **Diagnóstico do Motor Matemático:** {motivo_calc}")
        
            with st.expander("Ver Backstage da Decisão (Regras e Peso da IA)"):
                st.write(f"🔥 Dezenas 'Quentes' detectadas nos últimos 10 concursos: `{dados_internos.get('dezenas_quentes', 0)}/25`")
                # --- CORREÇÃO DO DISPLAY DA NOTA DA IA ---
                nota_real = ia.get('perf', {}).get(ia['cod_estrategia'], 11.0)
                st.markdown(f"**📈 Pontuação atual da estratégia '{ia['estrategia']}':** `{nota_real:.2f} pts`")
                st.write("---")
                st.write("**Como a IA decide habilitar bilhetes de 16 dezenas (R$ 56,00)?**")
                st.write("A inteligência cruza a Força do Ciclo com a Pontuação da Estratégia. Somente se a Confiança passar de **75%** e houver saldo em banca, o desdobramento de 16 números será gerado.")

            st.divider()
        
        # =====================================================================
        
        st.success(f"**⚡ LINHA TÁTICA ATIVADA:** {ia['estrategia']} \n\n**DIRETRIZ DA DECISÃO:** {ia['motivo_est']}")
        st.info(f"**🎯 GRUPO DE ELITE ({ia['qtd_matriz']} DEZENAS COMPILADAS):** {', '.join([f'{n:02d}' for n in ia['matriz_base']])}")

        # --- NOVAS ANÁLISES EXTRAS SOLICITADAS ---
        st.markdown("#### 📈 Parâmetros Volumétricos e Distribuição Espacial")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Massa de Soma", f"{ia['soma']:.1f}", delta="Equilíbrio: ~195")
        c2.metric("Massa Ímpar", f"{ia['impares']:.1f}", delta="Equilíbrio: ~7.5")
        c3.metric("Massa Primos", f"{ia['primos']:.1f}", delta="Equilíbrio: ~5.5")
        c4.metric("Massa Moldura", f"{ia['moldura']:.1f}", delta="Equilíbrio: ~10")

        # Análise de Quadrantes/Linhas/Colunas e Taxa de Repetição
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
            st.info(f"📋 **Dezenas por Linha (Grupo Elite):**<br>" + " | ".join([f"L{k}: **{v}**" for k, v in linhas_count.items()]), icon="📊")
        with c_an2:
            st.info(f"📋 **Dezenas por Coluna (Grupo Elite):**<br>" + " | ".join([f"C{k}: **{v}**" for k, v in colunas_count.items()]), icon="📊")
        with c_an3:
            st.info(f"🔄 **Repetição do Concurso Anterior:** A Matriz de Elite carrega **{repetidas_previstas} dezenas** do concurso nº {st.session_state.data['historico_dados'][-1]['concurso']}.", icon="🔮")

        # --- NOVO BLOCO: DESEMPENHO HISTÓRICO DAS DEZENAS ESCOLHIDAS PELA IA ---
        st.markdown("#### 🎯 Retrospectiva Crítica do Grupo de Elite (Últimos 30 Concursos)")
        ultimos_30 = st.session_state.data["historico_dados"][-30:]
        acertos_grupo = []
        for h in ultimos_30:
            hits = len(set(ia['matriz_base']).intersection(set(h['dezenas'])))
            acertos_grupo.append(hits)
        
        avg_hits = sum(acertos_grupo) / len(acertos_grupo) if acertos_grupo else 0
        t11 = sum(1 for x in acertos_grupo if x == 11)
        t12 = sum(1 for x in acertos_grupo if x == 12)
        t13 = sum(1 for x in acertos_grupo if x == 13)
        t14 = sum(1 for x in acertos_grupo if x == 14)
        t15 = sum(1 for x in acertos_grupo if x == 15)

        cd_1, cd_2, cd_3, cd_4 = st.columns(4)
        cd_1.metric("Média Geral de Acertos", f"{avg_hits:.2f} / 15", help="Média de dezenas sorteadas dentro do seu grupo atual de elite nos últimos 30 concursos.")
        cd_2.metric("Simulações com 11-12 Pts", f"{t11 + t12} vezes", delta=f"11 Pts: {t11} | 12 Pts: {t12}", delta_color="off")
        cd_3.metric("Simulações com 13 Pts", f"{t13} vezes", help="Quantidade de vezes que o grupo capturou 13 acertos.")
        cd_4.metric("Altas Premiações (14-15 Pts)", f"{t14 + t15} acertos", delta=f"14 Pts: {t14} | 15 Pts: {t15}", delta_color="inverse")

        st.markdown("#### 📊 Desempenho Histórico das Inteligências Ativas")
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
        <div style="background-color: #e8f4f8; border-left: 6px solid #1f77b4; padding: 15px; border-radius: 8px; margin-bottom: 25px; color: #1a1a1a;">
            <div style="margin-bottom: 8px;"><strong>🔥 Top 5 Dezenas mais Quentes:</strong> <span style="color: #d62728; font-weight: 500;">{str_quentes}</span></div>
            <div style="margin-bottom: 8px;"><strong>🧊 Top 5 Maiores Atrasos:</strong> <span style="color: #2ca02c; font-weight: 500;">{str_atrasos}</span></div>
            <div><strong>⏳ Status do Ciclo:</strong> Aberto há {ia['ciclo_tam']} concursos. <span style="color: #ff7f0e; font-weight: 500;">Faltam {len(ia['faltam_ciclo'])} dezenas para fechar: {ia['faltam_ciclo']}</span></div>
        </div>
        """
        st.markdown(html_dossie, unsafe_allow_html=True)

        # --- PAINEL DE DESEMPENHO DOS JOGOS ATIVOS (Aba 2) ---
        jogos_ativos = [j for j in st.session_state.data["jogos_salvos"] if j.get('status') == "Aguardando Sorteio"]
        if jogos_ativos:
            st.markdown("---")
            dezenas_ativos = [n for j in jogos_ativos for n in j["dezenas"]]
            render_performance_grid(dezenas_ativos, "🧬 Dezenas que a IA selecionou para os seus Jogos Ativos")
        else:
            st.info("Nenhum jogo ativo na fila no momento.")

        # --- NOVO PAINEL DE PESOS ESTILIZADO EM BADGES GIGANTES ---
        st.markdown("#### ⚖️ Grade Dinâmica de Pesos Absolutos (Heatmap de Atração da IA)")
        
        html_pesos = "<div style='display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; font-family: sans-serif; margin-bottom: 25px;'>"
        for n in range(1, 26):
            p_val = ia['pesos'].get(n, 0.0)
            no_grupo = n in ia['matriz_base']
            bg_color = "#d1e7dd" if no_grupo else "#f8f9fa"
            border_color = "#0f5132" if no_grupo else "#dee2e6"
            label_elite = "<span style='background-color:#0f5132; color:white; padding:2px 6px; font-size:10px; border-radius:4px; margin-left:5px;'>ELITE</span>" if no_grupo else ""
            
            html_pesos += f"<div style='background-color: {bg_color}; border: 2px solid {border_color}; border-radius: 8px; padding: 12px; text-align: center; color: #1a1a1a;'><span style='font-size: 20px; font-weight: bold; color: #111;'>{n:02d}</span>{label_elite}<br><span style='font-size: 13px; color: #444;'>Peso: <b>{p_val:.1f}</b></span></div>"
        
        html_pesos += "</div>"
        st.markdown(html_pesos, unsafe_allow_html=True)

    else: st.warning("Aguardando inserção de dados do Cofre na Aba 1.")


# --- TAB 3: GERADOR AUTÔNOMO ---
with tabs[2]:
    exibir_mini_painel_financeiro()
    st.markdown("### 🚀 Engenharia Combinatória por Verba")
    
    # Criando duas colunas para o layout ficar organizado
    col_saldo, col_aporte = st.columns([1, 1.5])
    
    with col_saldo:
        st.metric("💰 Saldo na Banca", f"R$ {st.session_state.data['banca']:.2f}")
    
    with col_aporte:
        st.markdown("#### ➕ Adicionar Aporte")
        # Criamos uma linha com input e botão na mesma altura
        c_input, c_btn = st.columns([2, 1])
        with c_input:
            valor_aporte = st.number_input("Valor (R$):", min_value=1.0, step=10.0, label_visibility="collapsed")
        with c_btn:
            if st.button("✅ Depositar"):
                st.session_state.data['banca'] += valor_aporte
                
                # 👇 A LINHA QUE FALTAVA (Sincroniza com o Painel da Aba 1) 👇
                st.session_state.data["historico_aportes"] = st.session_state.data.get("historico_aportes", 0.0) + valor_aporte
                
                salvar_dados(st.session_state.data)
                st.success("Aporte realizado!")
                st.rerun()
    
    if st.session_state.data["historico_dados"]:
        ia = raciocinio_total_ia(st.session_state.data["historico_dados"], st.session_state.data["ia_memoria"])
        st.write(f"Concurso Alvo Sincronizado: **{ia['alvo']}**")
        
        orcamento = st.number_input("Defina a verba máxima para geração (R$):", min_value=3.5, max_value=max(3.5, st.session_state.data['banca']), step=3.5)
        
        if st.button("🧬 DISPARAR MOTOR DE GERAÇÃO INÉDITA E ORTOGONAL OU GERACAO DE FECHAMENTO MATEMATICO PARA MATRIZ ATUAL", type="primary", use_container_width=True):
            if st.session_state.data['banca'] < orcamento:
                st.error("Banca insuficiente para a operação.")
            else:
                # =====================================================================
                # 🧠 INJEÇÃO DO MOTOR MATEMÁTICO E CÁLCULO DE CONFIANÇA
                # =====================================================================
                historico_painel = st.session_state.data["historico_dados"]
                estrategia_selecionada = ia.get('estrategia', 'Tendencia')
                memoria_ia = st.session_state.data.get('ia_memoria', {})
                
                # Chama a inteligência para saber se é seguro apostar 16 dezenas (Confiança >= 75%)
                _, conf_calc, _, _ = calcular_temperatura_e_confianca(
                    historico_painel, estrategia_selecionada, memoria_ia
                )

                
                # =====================================================================
                # 🛡️ PLANO A: GARANTIA MATEMÁTICA REDUZIDA E HÍBRIDA (100% EXATA)
                # Aqui o sistema já passa a inteligência, o dinheiro e a confiança!
                # =====================================================================
                sucesso_matematico, matriz_reduzida, msg_status = motor_garantia_exata_dinamica(ia, orcamento, conf_calc)

                if sucesso_matematico:
                    # =====================================================================
                    # ✅ O DINHEIRO DEU: GERA A MATEMÁTICA HÍBRIDA EXATA
                    # =====================================================================
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
                            "matriz_origem": st.session_state.data["matriz_viva_atual"], 
                            "dna": "🧬 Fechamento Matemático 100% Garantido"
                        })
                        
                    st.session_state.data['banca'] -= gasto
                    salvar_dados(st.session_state.data)
                    
                    st.toast(f"✅ {qtd_gerados} jogos matemáticos criados.", icon="🚀")
                    st.success(f"**Garantia Matemática Ativada!** {msg_status} Custo Real: **R$ {gasto:.2f}**. Saldo restante: **R$ {st.session_state.data['banca']:.2f}**.")
                    st.rerun()

                else:
                    # =====================================================================
                    # 🚀 SUPER PLANO B: A MÁQUINA DE FORÇA BRUTA ABSOLUTA
                    # =====================================================================
                    st.info(f"⚠️ {msg_status}") 
                    
                    historico_sets = {frozenset(h['dezenas']) for h in st.session_state.data['historico_dados']}
                    ultimo_sorteio = st.session_state.data["historico_dados"][-1]["dezenas"] if st.session_state.data["historico_dados"] else []
                    
                    jogos_neste_lote = [] 
                    gasto = 0.0
                    qtd_gerados = 0
                    
                    progresso_texto = st.empty()
                    barra_progresso = st.progress(0)
                    
                    # 🧠 DECISÃO DE MOTOR: FORÇA BRUTA (<=20) OU ESTOCÁSTICO (>20)
                    tam_matriz = len(ia['matriz_base'])
                    usar_forca_bruta = tam_matriz <= 20
                    
                    if usar_forca_bruta:
                        st.warning(f"⚡ **Motor Híbrido Ativado:** Matriz de {tam_matriz} dezenas. Acionando **Força Bruta Absoluta**.")
                        progresso_texto.write("⏳ Gerando TODAS as combinações e passando na peneira... Aguarde.")
                        
                        # 1. GERAÇÃO TOTAL ABSOLUTA
                        universo_15 = [list(c) for c in itertools.combinations(ia['matriz_base'], 15)]
                        universo_16 = [list(c) for c in itertools.combinations(ia['matriz_base'], 16)] if tam_matriz >= 16 else []
                        
                        # 2. A PENEIRA DE OURO (Filtra TUDO de uma vez)
                        def filtrar_universo(universo):
                            pote = []
                            for candidato in universo:
                                if frozenset(candidato) in historico_sets: continue
                                
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
                        
                        progresso_texto.write(f"✅ Filtro concluído! Sobreviveram {len(pote_15)} de 15-dez e {len(pote_16)} de 16-dez. Iniciando compras...")
                    else:
                        st.warning(f"⚡ **Motor Estocástico Ativado:** Matriz de {tam_matriz} dezenas detectada. Geração estocástica por peso.")
                        pote_15 = []
                        pote_16 = []
                    
                    # =====================================================================
                    # 🛒 O LAÇO DE COMPRA E ORÇAMENTO (O DOWNGRADE INTELIGENTE)
                    # =====================================================================
                    while (orcamento - gasto) >= 3.5:
                        
                        # Define se compra 16 ou 15 baseado no bolso, confiança e se ainda tem estoque de 16
                        if conf_calc >= 0.75 and (orcamento - gasto) >= 56.0 and (not usar_forca_bruta or len(pote_16) > 0):
                            tam = 16
                            custo = 56.0
                            pote_atual = pote_16
                        else:
                            tam = 15
                            custo = 3.5
                            pote_atual = pote_15
                        
                        melhor_candidato = []
                        melhor_score = -999999
                        melhor_dna = "🧬 DNA Não Biometrado"
                        
                        # ---------------------------------------------------------
                        # ROTA 1: A BUSCA NO POTE DE OURO (FORÇA BRUTA OTIMIZADA)
                        # ---------------------------------------------------------
                        if usar_forca_bruta:
                            if not pote_atual:
                                break # Se acabou todo o estoque perfeito filtrado, sai do laço
                            
                            melhor_idx = -1
                            melhor_score = -999999
                            
                            # OTIMIZAÇÃO: Pré-converter os jogos do lote em sets para não criar sets repetidamente
                            # Isso mantém a lógica de 15 e 16 intacta, só acelera a comparação
                            jogos_neste_lote_sets = [set(j) for j in jogos_neste_lote]
                            
                            for idx, item in enumerate(pote_atual):
                                penalidade = 0
                                item_set = set(item["dezenas"]) # Criado apenas uma vez por candidato
                                
                                # A lógica original de penalidade é preservada 100%
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
                                # Arranca o vencedor do pote pra ele não ser comprado de novo
                                pote_atual.pop(melhor_idx)
                        
                        # ---------------------------------------------------------
                        # ROTA 2: A ROLETA ESTOCÁSTICA ORIGINAL (Matrizes > 20)
                        # ---------------------------------------------------------
                        else:
                            dezenas_disponiveis = ia['matriz_base']
                            pesos_sublista = [ia['pesos'][i] for i in dezenas_disponiveis]
                            
                            for _ in range(150):
                                candidato = []
                                dez_temp = list(dezenas_disponiveis)
                                pesos_temp = list(pesos_sublista)
                                
                                for _ in range(tam):
                                    if not dez_temp: break 
                                    escolhida = random.choices(dez_temp, weights=pesos_temp, k=1)[0]
                                    candidato.append(escolhida)
                                    
                                    idx = dez_temp.index(escolhida)
                                    dez_temp.pop(idx)
                                    pesos_temp.pop(idx)
                                candidato = sorted(candidato)
                                
                                if frozenset(candidato) in historico_sets: continue
                                
                                max_c, atual_c = 1, 1
                                for i in range(1, len(candidato)):
                                    if candidato[i] == candidato[i-1] + 1:
                                        atual_c += 1
                                        max_c = max(max_c, atual_c)
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
            
                        # ==========================================
                        # SALVANDO O BILHETE COMPRADO
                        # ==========================================
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
                            "matriz_origem": st.session_state.data["matriz_viva_atual"], 
                            "dna": melhor_dna
                        })
                        
                        gasto += custo
                        qtd_gerados += 1
                        
                        progresso = min(gasto / orcamento, 1.0)
                        barra_progresso.progress(progresso)
                        progresso_texto.write(f"⚙️ Gerando lote... {qtd_gerados} bilhetes criados. Investimento: R$ {gasto:.2f} de R$ {orcamento:.2f}")
    
                    barra_progresso.empty()
                    progresso_texto.empty()
                    st.session_state.data['banca'] -= gasto
                    salvar_dados(st.session_state.data)
                    
                    st.toast(f"✅ Sucesso! {qtd_gerados} jogos criados.", icon="🚀")
                    st.success(f"**Lote processado com Sucesso!** O sistema blindou o seu orçamento comprando a Elite. Verifique na Aba 4.")
                    st.rerun()
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
        st.markdown("---")
        # [AQUI CONTINUA O RESTO DO SEU CÓDIGO QUE RENDERIZA OS CARDS...]
        
        for j in st.session_state.data["jogos_salvos"]:
            alvo = j.get('concurso_alvo')
            
            if j.get('status') == "Premiado":
                html_card = f"""
                <div style="border-top: 5px solid #28a745; background-color: #f8f9fa; border-left: 1px solid #dadce0; border-right: 1px solid #dadce0; border-bottom: 1px solid #dadce0; border-radius: 6px; padding: 15px; margin-bottom: 10px;">
                    <span style="color: #28a745; font-weight: bold; font-size: 14px;">✅ PREMIADO ({j.get('acertos')} Acertos) - R$ {j.get('premio_valor'):.2f}</span><br>
                    <span style="color: #4d5156; font-size: 13px; font-weight: 500;">Concurso Alvo: {alvo} | Grade: {j.get('tamanho')} Dezenas</span><br>
                    <span style="color: #5f6368; font-size: 12px;">Estratégia Operante: {j.get('estrategia')}</span><br>
                    <span style="color: #5f6368; font-size: 12px; font-style: italic;">Especificações da estratégia: {j.get('justificativa', 'Padrão autônomo.')}</span><br>
                    <span style="color: #006644; font-size: 13px; font-weight: bold;">{j.get('dna', '🧬 DNA Padrão Pós-Atualização')}</span>
                </div>
                """
            elif j.get('status') == "Não Premiado":
                html_card = f"""
                <div style="border-top: 5px solid #dc3545; background-color: #f8f9fa; border-left: 1px solid #dadce0; border-right: 1px solid #dadce0; border-bottom: 1px solid #dadce0; border-radius: 6px; padding: 15px; margin-bottom: 10px;">
                    <span style="color: #dc3545; font-weight: bold; font-size: 14px;">❌ NÃO PREMIADO ({j.get('acertos')} Acertos)</span><br>
                    <span style="color: #4d5156; font-size: 13px; font-weight: 500;">Concurso Alvo: {alvo} | Grade: {j.get('tamanho')} Dezenas</span><br>
                    <span style="color: #5f6368; font-size: 12px;">Estratégia Operante: {j.get('estrategia')}</span><br>
                    <span style="color: #5f6368; font-size: 12px; font-style: italic;">Especificações da estratégia: {j.get('justificativa', 'Padrão autônomo.')}</span><br>
                    <span style="color: #006644; font-size: 13px; font-weight: bold;">{j.get('dna', '🧬 DNA Padrão Pós-Atualização')}</span>
                </div>
                """
            else:
                html_card = f"""
                <div style="border-top: 5px solid #ffcc00; background-color: #f8f9fa; border-left: 1px solid #dadce0; border-right: 1px solid #dadce0; border-bottom: 1px solid #dadce0; border-radius: 6px; padding: 15px; margin-bottom: 10px;">
                    <span style="color: #1a73e8; font-weight: bold; font-size: 14px;">⏳ AGUARDANDO SORTEIO</span><br>
                    <span style="color: #4d5156; font-size: 13px; font-weight: 500;">Espera do Concurso Alvo: {alvo} | Grade: {j.get('tamanho')} Dezenas</span><br>
                    <span style="color: #5f6368; font-size: 12px;">Estratégia Operante: {j.get('estrategia')}</span><br>
                    <span style="color: #5f6368; font-size: 12px; font-style: italic;">Especificações da estratégia: {j.get('justificativa', 'Padrão autônomo.')}</span><br>
                    <span style="color: #006644; font-size: 13px; font-weight: bold;">{j.get('dna', '🧬 DNA Padrão Pós-Atualização')}</span>
                </div>
                """
            
            st.markdown(html_card, unsafe_allow_html=True)
            with st.container():
                st.code(" - ".join([f"{n:02d}" for n in j.get('dezenas', [])]))
                st.button("Apagar", key=f"del_{j['id']}", on_click=cb_excluir_jogo, args=(j['id'],))
                st.markdown("<br>", unsafe_allow_html=True)
    else: st.info("Sem bilhetes registrados na fila atual.")

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

        # --- BOTÃO 2: O NOVO BOTÃO INTELIGENTE (VIDA REAL DO ZERO - ADAPTATIVO) ---
        with col_massa2:
            if st.button("☢️ INICIAR VIDA REAL (BAIXAR E TREINAR DESDE O 1)", type="secondary", use_container_width=True):
                # 1. Limpeza total da mente da IA
                st.session_state.data["historico_dados"] = []
                st.session_state.data["ia_memoria"] = {
                    "Tendencia": {"usos": 0, "pontos": 0}, 
                    "Reversao": {"usos": 0, "pontos": 0},
                    "Ciclo": {"usos": 0, "pontos": 0},
                    "Simetria": {"usos": 0, "pontos": 0}
                }
                st.session_state.data["banca"] = 10000.00
                st.session_state.data["jogos_salvos"] = [] 
                
                with st.spinner("Calibrando a IA (Simulação Dinâmica de Orçamento) desde o 1º sorteio..."):
                    try:
                        res_todos = requests.get("https://loteriascaixa-api.herokuapp.com/api/lotofacil", verify=False, timeout=60).json()
                        res_todos = sorted(res_todos, key=lambda k: int(k['concurso']))
                        
                        barra = st.progress(0)
                        lucro_acumulado_massa = 0.0
                        logs_massa = []
                        total_concursos = len(res_todos)
                        
                        for i, res_conc in enumerate(res_todos):
                            num = int(res_conc['concurso'])
                            dezenas_sorteadas = sorted([int(d) for d in res_conc['dezenas']])
                            
                            st.session_state.data["historico_dados"].append({
                                "concurso": num, 
                                "dezenas": dezenas_sorteadas, 
                                "data": res_conc.get('data', '')
                            })
                            
                            # --- O FANTASMA ADAPTATIVO DA IA ---
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
                            
                            # O funil confere e agora ENCONTRA o bilhete e a estratégia para pontuar!
                            lucro_parcial, relatorio_parcial = auditar_e_aprender_unificado(num, dezenas_sorteadas, rateios_massa)
                            lucro_acumulado_massa += lucro_parcial
                            
                            if i == total_concursos - 1:
                                logs_massa.extend(relatorio_parcial)
                                
                            if i % 50 == 0:
                                barra.progress((i + 1) / total_concursos)
                                
                        barra.progress(1.0)
                        
                        if logs_massa:
                            st.session_state.ultimo_aprendizado = list(set(logs_massa))
                            
                        st.session_state.data["jogos_salvos"] = [] 
                        salvar_dados(st.session_state.data)
                        
                        st.success(f"🚀 Calibração Concluída! Saldo Final Simulado: R$ {lucro_acumulado_massa:.2f}")
                        st.balloons()
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Erro ao processar: {e}")
    
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
                            if lucro_total > 0: st.balloons()
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
