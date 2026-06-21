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
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =====================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E CSS (DEVE SER O PRIMEIRO COMANDO ST)
# =====================================================================
st.set_page_config(page_title="LotoMatrix PRO", page_icon="🍀", layout="wide")

st.markdown("""
<style>
    :root { --roxo: #930089; --roxo-hover: #7a0072; }
    .stApp { background-color: #f4f6f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: #ffffff; padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 10px 20px; background-color: #f8f9fa; border: 1px solid #e9ecef; transition: all 0.3s ease; }
    .stTabs [aria-selected="true"] { background-color: var(--roxo) !important; color: white !important; border: none; box-shadow: 0 4px 10px rgba(147,0,137,0.3); }
    div[data-testid="stMetric"] { background-color: white; padding: 20px; border-radius: 12px; border-left: 6px solid var(--roxo); box-shadow: 0 4px 6px rgba(0,0,0,0.04); }
    div[data-testid="stAlert"] { background-color: #fdf5ff !important; border-left: 5px solid var(--roxo) !important; color: #333 !important; border-radius: 8px !important; }
    button[kind="primary"] { background-color: var(--roxo) !important; border: none !important; border-radius: 8px !important; font-weight: bold !important; color: white !important; box-shadow: 0 4px 10px rgba(147,0,137,0.4) !important; transition: all 0.3s ease !important; }
    button[kind="primary"]:hover { background-color: var(--roxo-hover) !important; transform: translateY(-2px); }
    .login-box { max-width: 420px; margin: 80px auto; padding: 40px; background: white; border-radius: 16px; border-top: 6px solid var(--roxo); box-shadow: 0 10px 30px rgba(147,0,137,0.15); text-align: center; }
    .login-title { color: var(--roxo); font-weight: 900; font-size: 26px; margin-bottom: 5px; }
    .login-sub { color: #666; font-size: 14px; margin-bottom: 25px; }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# 2. TODAS AS FUNÇÕES GLOBAIS DO SISTEMA (NÚCLEO LÓGICO)
# =====================================================================

def sanitizar_dados(d):
    if "historico_dados" not in d: d["historico_dados"] = []
    if "jogos_salvos" not in d: d["jogos_salvos"] = []
    if "historico_custos" not in d: d["historico_custos"] = 0.0
    if "historico_premios" not in d: d["historico_premios"] = 0.0
    
    # GARANTIA DA IA EXISTIR DESDE O MILISSEGUNDO ZERO
    if "ia_pesos" not in d:
        d["ia_pesos"] = {
            "Tendencia Forte": {"p1": 20.0, "p2": 5.0, "bonus": 40.0},
            "Simetria Conjunta": {"p1": 15.0, "p2": 8.0, "bonus1": 30.0, "bonus2": 20.0},
            "Reversao de Tendencia": {"p1": 10.0, "bonus": 100.0},
            "Default": {"p1": 12.0, "p2": 8.0, "bonus": 25.0}
        }
        
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
        if "estrategia" not in j: j["estrategia"] = "Plano A Exato"
        if "justificativa" not in j: j["justificativa"] = "Jogo recuperado."
    return d

def ajustar_ia(cod_est, acertos):
    """Função de Aprendizado: Recompensa acertos altos, pune acertos baixos."""
    fator = 1.02 if acertos >= 12 else 0.98 
    ia_pesos = st.session_state.data["ia_pesos"]
    est_key = cod_est if cod_est in ia_pesos else "Default"
    
    for k in ia_pesos[est_key]:
        ia_pesos[est_key][k] = round(ia_pesos[est_key][k] * fator, 2)
    st.session_state.data["ia_pesos"] = ia_pesos

def salvar_dados(dados):
    try:
        with open("Cofre.json", "w", encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
    except Exception as e:
        pass

def exibir_mini_painel_financeiro():
    t_custos = st.session_state.data.get("historico_custos", 0.0)
    t_premios = st.session_state.data.get("historico_premios", 0.0)
    res_global = t_premios - t_custos
    str_res = f"R$ {res_global:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if res_global > 0: status_msg = f"🟢 **Lucro Global:** `{str_res}`"
    elif res_global < 0: status_msg = f"🔴 **Prejuízo Global:** `{str_res}`"
    else: status_msg = f"⚪ **Empate Global:** `{str_res}`"
    st.markdown(f"> 📊 **Balanço da Operação Institucional:** {status_msg}")
    st.write("")

def calcular_premio_multiplo(tamanho, acertos, v11=7.0, v12=14.0, v13=35.0, v14=1500.0, v15=1500000.0):
    if acertos < 11: return 0.0
    premio = 0.0
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

def extrair_rateios_api(premiacoes):
    rateios = {}
    if premiacoes:
        for p in premiacoes:
            rateios[p.get('acertos', 0)] = float(p.get('premio', 0.0))
    return rateios

def auditar_e_aprender_unificado(concurso, dezenas_sorteadas, rateios=None):
    """Auditoria de caixa + Auto-Ajuste da IA"""
    if rateios is None: rateios = {}
    v11, v12, v13, v14, v15 = rateios.get(11, 7.0), rateios.get(12, 14.0), rateios.get(13, 35.0), rateios.get(14, 1500.0), rateios.get(15, 1500000.0)
    
    lucro_total = 0.0
    relatorio = []
    sorteio_set = set(dezenas_sorteadas)
    
    jogos_processados = 0
    premiados = 0
    max_pts = 0
    
    if "global_hits" not in st.session_state.data:
        st.session_state.data["global_hits"] = {11: 0, 12: 0, 13: 0, 14: 0, 15: 0}
    if "ledger_track" not in st.session_state.data:
        st.session_state.data["ledger_track"] = {"bilhetes": 0, "premiados_geral": 0, "elite": 0}
    if "matrizes_reais_hits" not in st.session_state.data:
        st.session_state.data["matrizes_reais_hits"] = {11: 0, 12: 0, 13: 0, 14: 0, 15: 0, "total": 0, "soma_acertos": 0}
    if "matrizes_auditadas_ids" not in st.session_state.data:
        st.session_state.data["matrizes_auditadas_ids"] = []
        
    ledger = st.session_state.data["ledger_track"]
    hits_bilhetes = st.session_state.data["global_hits"]
    matriz_usada_neste_concurso = None
    
    for j in st.session_state.data.get("jogos_salvos", []):
        alvo_do_jogo = j.get('concurso_alvo')
        pode_auditar = False
        
        if str(alvo_do_jogo) == str(concurso) or (isinstance(alvo_do_jogo, int) and alvo_do_jogo <= concurso) or str(alvo_do_jogo) == "Legado":
            pode_auditar = True
            if j.get("matriz_origem"):
                matriz_usada_neste_concurso = j["matriz_origem"]
        
        if j.get('status') == "Aguardando Sorteio" and pode_auditar:
            jogos_processados += 1
            ledger["bilhetes"] += 1
            
            pontos = len(set(j.get('dezenas', [])).intersection(sorteio_set))
            
            # --- AUTO-APRENDIZADO DA IA ---
            ajustar_ia(j.get("estrategia", "Default"), pontos)
            
            j['acertos'] = pontos
            j['premio_valor'] = calcular_premio_multiplo(j.get('tamanho', 15), pontos, v11, v12, v13, v14, v15)
            
            max_pts = max(max_pts, pontos)
            
            if pontos >= 11:
                j['status'] = "Premiado"
                lucro_total += j['premio_valor']
                st.session_state.data["historico_premios"] += j['premio_valor']
                premiados += 1
                ledger["premiados_geral"] += 1
                if pontos >= 14: ledger["elite"] += 1    
                hits_bilhetes[pontos] = hits_bilhetes.get(pontos, 0) + 1
            else:
                j['status'] = "Não Premiado"

    matrizes_hits = st.session_state.data["matrizes_reais_hits"]
    matrizes_auditadas = st.session_state.data["matrizes_auditadas_ids"]
    selo_matriz = f"conc_{concurso}"
    
    if matriz_usada_neste_concurso and selo_matriz not in matrizes_auditadas:
        acertos_matriz = len(set(matriz_usada_neste_concurso).intersection(sorteio_set))
        matrizes_auditadas.append(selo_matriz)
        matrizes_hits["total"] = matrizes_hits.get("total", 0) + 1
        matrizes_hits["soma_acertos"] = matrizes_hits.get("soma_acertos", 0) + acertos_matriz
        
        if acertos_matriz >= 11:
            chave = int(min(acertos_matriz, 15)) 
            matrizes_hits[chave] = matrizes_hits.get(chave, 0) + 1
        
    st.session_state.data["matrizes_reais_hits"] = matrizes_hits
    st.session_state.data["matrizes_auditadas_ids"] = matrizes_auditadas
    st.session_state.data["global_hits"] = hits_bilhetes
    st.session_state.data["ledger_track"] = ledger
    
    if jogos_processados > 0:
        relatorio.append(f"Auditoria Concurso {concurso}: {premiados}/{jogos_processados} bilhetes premiados. Pico: {max_pts} pts.")
        
    return lucro_total, relatorio

@st.cache_data(show_spinner="🧠 Processando Matriz (Fechamento 100% Matemático)...")
def gerar_fechamento_matematico(dezenas_tuple, garantia):
    import itertools
    dezenas = list(dezenas_tuple)
    todas_comb_15 = list(itertools.combinations(dezenas, 15))
    qtd_dezenas = len(dezenas)
    
    if garantia == 15 or qtd_dezenas <= 15:
        return [list(c) for c in todas_comb_15]

    comb_bits = []
    for c in todas_comb_15:
        bits = 0
        for num in c: bits |= (1 << num)
        comb_bits.append(bits)
        
    sorteios_possiveis = set(range(len(comb_bits)))
    bilhetes_escolhidos = []
    cobertura = []
    for b in comb_bits:
        cobre = set()
        for j, s in enumerate(comb_bits):
            if (b & s).bit_count() >= garantia:
                cobre.add(j)
        cobertura.append(cobre)
        
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

def obter_dados_fechamento(matriz_base, garantia):
    jogos = gerar_fechamento_matematico(tuple(matriz_base), garantia)
    return len(jogos), len(jogos) * 3.50

def raciocinio_total_ia(historico, memoria, estrategia_instinto="Tendencia", tamanho_instinto=18):
    if not historico: return None
    
    ultimos_12 = historico[-12:] if len(historico) >= 12 else historico
    media_soma = float(sum([sum(h['dezenas']) for h in ultimos_12]) / len(ultimos_12)) if ultimos_12 else 190.0
    
    freq_micro = Counter([int(n) for h in ultimos_12 for n in h['dezenas']])
    freq_recente = Counter([int(n) for h in historico[-30:] for n in h['dezenas']])
    
    atrasos = {int(n): 0 for n in range(1, 26)}
    dezena_encontrada = {int(n): False for n in range(1, 26)}
    for h in reversed(historico):
        for n in range(1, 26):
            if int(n) in h['dezenas']: dezena_encontrada[int(n)] = True
            elif not dezena_encontrada[int(n)]: atrasos[int(n)] += 1

    ciclo_atual = set()
    jogos_ciclo = 0
    for h in historico:
        ciclo_atual.update(h['dezenas'])
        jogos_ciclo += 1
        if len(ciclo_atual) == 25:
            ciclo_atual = set() 
            jogos_ciclo = 0
            
    faltam_ciclo = sorted([int(x) for x in list(set(range(1, 26)) - ciclo_atual)])
    qtd_faltam = len(faltam_ciclo)
    ultimo_sorteio = [int(x) for x in historico[-1]['dezenas']]
    ausentes = [int(n) for n in range(1, 26) if n not in ultimo_sorteio] 

    repeticoes_recentes = []
    try:
        for j in range(1, min(6, len(historico))):
            rep = len(set(historico[-j]['dezenas']) & set(historico[-(j+1)]['dezenas']))
            repeticoes_recentes.append(rep)
        media_volatilidade = float(sum(repeticoes_recentes) / len(repeticoes_recentes)) if repeticoes_recentes else 9.0
    except:
        media_volatilidade = 9.0

    if qtd_faltam <= 2:
        cod_est, qtd_matriz, tatic_desc = "Ciclo Supremo", 18, "Cerco Fim de Ciclo."
    elif media_volatilidade < 8.0:
        cod_est, qtd_matriz, tatic_desc = "Reversao de Tendencia", 20, "Caos/Reversão."
    elif media_volatilidade > 9.5:
        cod_est, qtd_matriz, tatic_desc = "Tendencia Forte", 17, "Tendência Absoluta."
    else:
        cod_est, qtd_matriz, tatic_desc = "Simetria Conjunta", 19, "Padrão de Equilíbrio."

    est_pesos = st.session_state.data["ia_pesos"].get(cod_est, st.session_state.data["ia_pesos"]["Default"])

    unified_scores = {}
    for n in range(1, 26):
        n = int(n)
        aparicoes_curtas = freq_micro.get(n, 0)
        aparicoes_longas = freq_recente.get(n, 0)
        delay = atrasos.get(n, 0)
        score_calc = 0.0

        if cod_est == "Tendencia Forte":
            score_calc = (aparicoes_curtas * est_pesos.get("p1", 20.0)) + (aparicoes_longas * est_pesos.get("p2", 5.0))
            if n in ausentes and delay == 1: score_calc += est_pesos.get("bonus", 40.0)
            
        elif cod_est == "Simetria Conjunta":
            score_calc = (aparicoes_longas * est_pesos.get("p1", 15.0)) + (aparicoes_curtas * est_pesos.get("p2", 8.0))
            if n in ausentes:
                if delay == 1: score_calc += est_pesos.get("bonus1", 30.0)
                elif delay == 2: score_calc += est_pesos.get("bonus2", 20.0)

        elif cod_est == "Reversao de Tendencia":
            score_calc = (aparicoes_longas * est_pesos.get("p1", 10.0))
            if n in ausentes and delay >= 3: score_calc += est_pesos.get("bonus", 100.0)

        else: 
            score_calc = (aparicoes_curtas * est_pesos.get("p1", 12.0)) + (aparicoes_longas * est_pesos.get("p2", 8.0))
            if n in ausentes and delay <= 2: score_calc += est_pesos.get("bonus", 25.0)

        if qtd_faltam <= 3 and n in faltam_ciclo:
            score_calc += 5000.0
            
        unified_scores[n] = float(score_calc)

    IMPARES_SET = {1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25}
    PRIMOS_SET = {2, 3, 5, 7, 11, 13, 17, 19, 23}
    MOLDURA_SET = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
    FIBO_SET = {1, 2, 3, 5, 8, 13, 21}
    MULT3_SET = {3, 6, 9, 12, 15, 18, 21, 24}
    ULT_SORT_SET = set(ultimo_sorteio)
    AUSENTES_SET = set(range(1, 26)) - ULT_SORT_SET
    
    max_rep = round(qtd_matriz * 0.60)
    max_aus = qtd_matriz - max_rep
    max_imp = round(qtd_matriz * 0.54) + 1
    max_prim = round(qtd_matriz * 0.36) + 1
    max_mold = round(qtd_matriz * 0.66) + 1
    max_fibo = round(qtd_matriz * 0.30) + 1
    max_mult3 = round(qtd_matriz * 0.33) + 1

    matriz_final = []
    candidatos = sorted(range(1, 26), key=lambda x: unified_scores.get(x, 0), reverse=True)
    
    for n in candidatos:
        if len(matriz_final) >= qtd_matriz: break
        if n in IMPARES_SET and sum(1 for x in matriz_final if x in IMPARES_SET) >= max_imp: continue
        if n in PRIMOS_SET and sum(1 for x in matriz_final if x in PRIMOS_SET) >= max_prim: continue
        if n in MOLDURA_SET and sum(1 for x in matriz_final if x in MOLDURA_SET) >= max_mold: continue
        if n in FIBO_SET and sum(1 for x in matriz_final if x in FIBO_SET) >= max_fibo: continue
        if n in MULT3_SET and sum(1 for x in matriz_final if x in MULT3_SET) >= max_mult3: continue
        if n in ULT_SORT_SET and sum(1 for x in matriz_final if x in ULT_SORT_SET) >= max_rep: continue
        if n in AUSENTES_SET and sum(1 for x in matriz_final if x in AUSENTES_SET) >= max_aus: continue
        matriz_final.append(n)

    if len(matriz_final) < qtd_matriz:
        for n in candidatos:
            if len(matriz_final) >= qtd_matriz: break
            if n not in matriz_final:
                if n in ULT_SORT_SET and sum(1 for x in matriz_final if x in ULT_SORT_SET) >= max_rep: continue
                if n in AUSENTES_SET and sum(1 for x in matriz_final if x in AUSENTES_SET) >= max_aus: continue
                matriz_final.append(n)
        
    matriz_final = sorted(matriz_final)

    c_imp = sum(1 for n in matriz_final if n in IMPARES_SET)
    c_prim = sum(1 for n in matriz_final if n in PRIMOS_SET)
    c_mold = sum(1 for n in matriz_final if n in MOLDURA_SET)
    c_fibo = sum(1 for n in matriz_final if n in FIBO_SET)
    c_mult3 = sum(1 for n in matriz_final if n in MULT3_SET)
    c_rep = len(set(matriz_final).intersection(ULT_SORT_SET))
    
    justificativa = f"DIRETRIZ: {tatic_desc} (Matriz: {qtd_matriz}) | COMPOSIÇÃO: {c_imp} Ímpares, {len(matriz_final)-c_imp} Pares, {c_prim} Primos, {c_mold} Moldura, {c_fibo} Fibonacci, {c_mult3} Múltiplos de 3 | STATUS: {c_rep} Repetidas, {len(matriz_final)-c_rep} Ausentes."
    
    return {
        "estrategia": str(cod_est), "cod_estrategia": str(cod_est), "estrategia_usada": str(cod_est), 
        "motivo_est": justificativa,
        "pesos": {int(x): round(float(unified_scores.get(x, 0.0)), 2) for x in range(1, 26)},
        "freq": dict(freq_recente), "atrasos": dict(atrasos), "ciclo_tam": int(jogos_ciclo), 
        "faltam_ciclo": faltam_ciclo, "soma": media_soma, 
        "impares": c_imp, "primos": c_prim, "moldura": c_mold,
        "repetidas": c_rep, "ausentes": len(matriz_final)-c_rep,
        "fibo": c_fibo, "mult3": c_mult3,
        "alvo": int((historico[-1]['concurso'] + 1)) if historico else 1, 
        "qtd_matriz": int(qtd_matriz), 
        "matriz_base": matriz_final, "perf": {}, "volatilidade": media_volatilidade
    }

def gerar_pdf_jogos(jogos, dezenas_anteriores=None):
    if dezenas_anteriores is None: dezenas_anteriores = []
    def limpar_latin1(texto):
        texto = str(texto).replace("🧬", "").replace("🍀", "").replace("🎫", "").replace("⚠️", "")
        return texto.encode('latin-1', 'ignore').decode('latin-1')
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_text_color(147, 0, 137)
    pdf.set_font('Arial', 'B', 22)
    pdf.set_xy(10, 12)
    pdf.cell(0, 10, "LotoMatrix PRO - Volantes de Aposta", ln=0)
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.set_xy(10, 22)
    pdf.cell(0, 8, "Relatorio Oficial Pericial (Fechamento Exato)", ln=0)
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(147, 0, 137)
    pdf.set_xy(10, 12)
    pdf.cell(190, 10, f"TOTAL: {len(jogos)} BILHETES", ln=0, align='R')
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(120, 120, 120)
    pdf.set_xy(10, 22)
    pdf.cell(190, 8, datetime.now().strftime('%d/%m/%Y %H:%M'), ln=0, align='R')
    pdf.ln(30)
    for i, j in enumerate(jogos, 1):
        if pdf.get_y() > 220: pdf.add_page()
        y_start = pdf.get_y()
        estrategia = limpar_latin1(str(j.get('estrategia', 'Padrao')))
        dezenas = j.get('dezenas', [])
        alvo = limpar_latin1(str(j.get('concurso_alvo', 'N/A')))
        pdf.set_fill_color(252, 245, 255)
        pdf.rect(10, y_start, 190, 65, 'F')
        pdf.set_fill_color(147, 0, 137)
        pdf.rect(10, y_start, 3, 65, 'F')
        pdf.set_text_color(40, 40, 40)
        pdf.set_font('Arial', 'B', 12)
        pdf.set_xy(18, y_start + 5)
        pdf.cell(100, 8, f"JOGO {i:02d}  |  Alvo: {alvo}  |  {len(dezenas)} Dezenas", ln=0)
        pdf.set_text_color(147, 0, 137) 
        pdf.set_font('Arial', 'B', 10)
        pdf.set_xy(10, y_start + 5)
        pdf.cell(185, 8, f"{estrategia}", ln=0, align='R')
        start_x, start_y, espaco_x, espaco_y = 75, y_start + 18, 10, 8 
        for num in range(1, 26):
            linha = (num - 1) // 5
            coluna = (num - 1) % 5
            cx = start_x + (coluna * espaco_x)
            cy = start_y + (linha * espaco_y)
            if num in dezenas:
                pdf.set_fill_color(147, 0, 137)
                pdf.set_text_color(255, 255, 255)
            else:
                pdf.set_fill_color(235, 235, 235)
                pdf.set_text_color(160, 160, 160)
            pdf.ellipse(cx, cy, 6, 6, 'F')
            pdf.set_xy(cx, cy)
            pdf.set_font('Arial', 'B', 7)
            pdf.cell(6, 6, f"{num:02d}", align='C')
        justificativa_texto = str(j.get('justificativa', ''))
        match = re.search(r'(\d+) pts', justificativa_texto)
        if match:
            pontos = match.group(1)
            texto_rodape = f"Fechamento 100% Matematico - Garantia de {pontos} Pontos"
        else:
            texto_rodape = "Fechamento 100% Matematico Absoluto"
        pdf.set_text_color(147, 0, 137)
        pdf.set_font('Arial', 'B', 8)
        pdf.set_xy(18, y_start + 58)
        pdf.cell(170, 5, texto_rodape, ln=0, align='C')
        pdf.set_y(y_start + 70)
    resultado = pdf.output(dest='S')
    if isinstance(resultado, str): return resultado.encode('latin-1', 'ignore')
    return bytes(resultado)

def exibir_card_volante(jogo, numero_jogo):
    dezenas = jogo.get('dezenas', [])
    alvo = jogo.get('concurso_alvo', 'N/A')
    estrategia = jogo.get('estrategia', 'Padrão')
    justificativa = str(jogo.get('justificativa', ''))
    match = re.search(r'(\d+) pts', justificativa)
    if match:
        pontos = match.group(1)
        texto_rodape = f"Fechamento 100% Matemático - Garantia de {pontos} Pontos"
    else:
        texto_rodape = "Fechamento 100% Matemático Absoluto"
    grid_html = "<div style='display: grid; grid-template-columns: repeat(5, 1fr); gap: 4px; margin-bottom: 10px;'>"
    for num in range(1, 26):
        if num in dezenas:
            bg_color, txt_color, border = "#930089", "white", "none"
        else:
            bg_color, txt_color, border = "#f4f6f9", "#ccc", "1px solid #eee"
        grid_html += f"<div style='background-color: {bg_color}; color: {txt_color}; border: {border}; text-align: center; border-radius: 50%; width: 28px; height: 28px; line-height: 28px; font-size: 12px; font-weight: bold; margin: auto;'>{num:02d}</div>"
    grid_html += "</div>"
    html_card = f"""
    <div style='background-color: #fcf5ff; border-left: 4px solid #930089; padding: 10px; border-radius: 5px; margin-bottom: 15px; box-shadow: 1px 1px 5px rgba(0,0,0,0.05);'>
        <div style='font-size: 14px; font-weight: bold; color: #333;'>JOGO {numero_jogo:02d} <span style='font-size: 11px; font-weight: normal; color: #777; float: right;'>Alvo: {alvo}</span></div>
        <div style='font-size: 11px; color: #930089; margin-bottom: 10px; font-weight: bold;'>{estrategia}</div>
        {grid_html}
        <div style='text-align: center; font-size: 10px; font-weight: bold; color: #930089; background: rgba(147, 0, 137, 0.1); padding: 4px; border-radius: 4px; margin-top: 5px;'>
            {texto_rodape}
        </div>
    </div>
    """
    st.markdown(html_card, unsafe_allow_html=True)

# Callbacks
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
# 3. INICIALIZAÇÃO DE ESTADO
# =====================================================================
if "data" not in st.session_state:
    st.session_state.data = sanitizar_dados({})

if 'auth' not in st.session_state: 
    st.session_state.auth = False

# =====================================================================
# 4. SISTEMA DE LOGIN
# =====================================================================
if not st.session_state.auth:
    st.markdown("""
    <div class='login-box'>
        <div class='login-title'>🍀 LotoMatrix PRO</div>
        <div class='login-sub'>Autenticação de Segurança - Acesso Restrito</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        senha = st.text_input("Senha de Acesso", type="password", placeholder="Digite sua senha...", label_visibility="collapsed")
        if st.button("ENTRAR NO SISTEMA", type="primary", use_container_width=True):
            if senha == "777": # Troque pela sua senha real
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Acesso Negado! Senha incorreta.")
    st.stop()

# =====================================================================
# 5. INTERFACE PRINCIPAL (TABS)
# =====================================================================
st.markdown("<h2 style='text-align: center; color: #930089; font-weight: 900;'>🍀 LotoMatrix PRO - Agente Autônomo</h2>", unsafe_allow_html=True)
tabs = st.tabs(["📂 1. Banco de Dados", "🧠 2. Cérebro Analítico (IA)", "🤖 3. Geração Autônoma", "📜 4. Fila de Sorteio", "🏆 5. Sincronização e Entrada"])

# --- TAB 1: BANCO DE DADOS E BALANÇO FINANCEIRO ---
with tabs[0]:
    st.markdown("### 💾 Central de Dados e Livro-Caixa da Operação")

    t_custos = st.session_state.data["historico_custos"]
    t_premios = st.session_state.data["historico_premios"]
    resultado_global = t_premios - t_custos

    with st.container(border=True):
        st.markdown("#### 📈 Balanço Financeiro Global (ROI)")
        ind1, ind2, ind3 = st.columns(3)
        
        ind1.metric("📥 Total Investido (Gastos)", f"R$ {t_custos:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        ind2.metric("📤 Total Retornado (Prêmios)", f"R$ {t_premios:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        str_res = f"R$ {resultado_global:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        if resultado_global > 0: ind3.metric("📊 Lucro Real do Projeto", str_res, "A Máquina está Paga")
        elif resultado_global < 0: ind3.metric("📊 Prejuízo Real do Projeto", str_res, "Buscando Recuperação")
        else: ind3.metric("📊 Balanço do Projeto", "R$ 0,00", "Empate / Ponto Zero")

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("**📂 Gerenciamento do Cofre (Backup)**")
            st.file_uploader("📥 Carregar Arquivo Cofre.json", type="json", key="uploader_cofre", on_change=cb_carregar_cofre)
            st.info(f"📊 **Concursos Oficiais Salvos:** {len(st.session_state.data.get('historico_dados', []))}.")
            st.download_button("📤 Baixar Backup Consolidado", json.dumps(st.session_state.data), "Cofre.json", type="primary", use_container_width=True)
            
    with c2:
        with st.container(border=True):
            st.markdown("**💸 Correção Manual de Livro-Caixa**")
            st.caption("A IA atualiza os gastos e ganhos automaticamente ao gerar/conferir os jogos. Use aqui apenas para ajustes manuais pontuais.")
            
            valor_mov = st.number_input("Digite o Valor (R$):", min_value=0.0, step=10.0, key="input_movimentacao")
            col_dep, col_sac = st.columns(2)
            
            with col_dep:
                if st.button("➕ Adicionar Gasto Extra", use_container_width=True):
                    if valor_mov > 0:
                        st.session_state.data["historico_custos"] += valor_mov
                        salvar_dados(st.session_state.data)
                        st.toast("Custo extra adicionado.", icon="📉")
                        st.rerun()
                        
            with col_sac:
                if st.button("✅ Adicionar Prêmio Extra", use_container_width=True):
                    if valor_mov > 0:
                        st.session_state.data["historico_premios"] += valor_mov
                        salvar_dados(st.session_state.data)
                        st.toast("Prêmio extra contabilizado.", icon="🎉")
                        st.rerun()
            
            st.divider()
            if st.button("🔄 ZERAR CONTABILIDADE E ROI (MANTER IA)", use_container_width=True, type="secondary"):
                st.session_state.data["historico_custos"] = 0.0
                st.session_state.data["historico_premios"] = 0.0
                st.session_state.data["ledger_track"] = {"bilhetes": 0, "premiados_geral": 0, "elite": 0, "custo": 0.0, "retorno": 0.0}
                for j in st.session_state.data.get("jogos_salvos", []): j["ledger_ok"] = False
                salvar_dados(st.session_state.data)
                st.success("Livro-caixa zerado com sucesso. A IA e os dados históricos permanecem intactos.")
                st.rerun()

# --- TAB 2: CÉREBRO ANALÍTICO (IA) ---
with tabs[1]:
    exibir_mini_painel_financeiro()
    
    st.markdown("### 🧠 Diagnóstico da Inteligência Artificial")
    
    track = st.session_state.data.get("ledger_track", {"bilhetes": 0, "premiados_geral": 0, "elite": 0})
    custo_real = st.session_state.data.get("historico_custos", 0.0)
    retorno_real = st.session_state.data.get("historico_premios", 0.0)
    
    win_rate = (track['premiados_geral'] / track['bilhetes'] * 100) if track.get('bilhetes', 0) > 0 else 0.0
    roi_val = retorno_real - custo_real
    roi_pct = (roi_val / custo_real * 100) if custo_real > 0 else 0.0

    with st.container(border=True):
        st.markdown("#### 📈 Track Record: A Máquina em Ação (Dados Reais)")
        st.caption("Estatísticas baseadas APENAS nos seus jogos apostados e auditados.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🎟️ Bilhetes Operados", track.get('bilhetes', 0))
        c2.metric("🎯 Win Rate (Prêmios)", f"{win_rate:.1f}%")
        elite_rate = (track.get('elite', 0) / track.get('premiados_geral', 1) * 100) if track.get('premiados_geral', 0) > 0 else 0.0
        c3.metric("💎 Freq. de Elite (14/15 nos Bilhetes)", f"{elite_rate:.1f}%" if elite_rate > 0 else "0.0%")
        c4.metric("📈 ROI Financeiro", f"{roi_pct:.1f}%", f"R$ {roi_val:.2f}")

    st.markdown("### 🏆 Performance Oficial (Pós-Auditoria Vida Real)")
    hits_matriz = st.session_state.data.get("matrizes_reais_hits", {})
    
    tm_11, tm_12, tm_13, tm_14, tm_15 = hits_matriz.get(11, 0), hits_matriz.get(12, 0), hits_matriz.get(13, 0), hits_matriz.get(14, 0), hits_matriz.get(15, 0)
    tm_total = hits_matriz.get("total", 0)
    soma_real_acertos = hits_matriz.get("soma_acertos", 0)
    media_acertos_matriz = soma_real_acertos / tm_total if tm_total > 0 else 0.0

    with st.container(border=True):
        st.markdown("#### 🎯 Força da Matriz da IA")
        st.caption(f"Total de Matrizes Auditadas: **{tm_total}**.")
        st.metric("Média de Acertos da Matriz", f"{media_acertos_matriz:.2f} / 15")
        st.markdown("---")
        cm1, cm2, cm3, cm4, cm5 = st.columns(5)
        cm1.metric("Matriz Acertou 11", tm_11)
        cm2.metric("Matriz Acertou 12", tm_12)
        cm3.metric("Matriz Acertou 13", tm_13)
        cm4.metric("Matriz Acertou 14", tm_14)
        cm5.metric("Matriz Acertou 15", tm_15)

    hits_bilhetes = st.session_state.data.get("global_hits", {})
    tb_11, tb_12, tb_13, tb_14, tb_15 = hits_bilhetes.get(11, 0), hits_bilhetes.get(12, 0), hits_bilhetes.get(13, 0), hits_bilhetes.get(14, 0), hits_bilhetes.get(15, 0)

    with st.container(border=True):
        st.markdown("#### 🎫 Prêmios Retidos nos Bilhetes")
        cb1, cb2, cb3, cb4, cb5 = st.columns(5)
        cb1.metric("Bilhetes com 11", tb_11)
        cb2.metric("Bilhetes com 12", tb_12)
        cb3.metric("Bilhetes com 13", tb_13)
        cb4.metric("Bilhetes com 14", tb_14)
        cb5.metric("Bilhetes com 15", tb_15)

    # =======================================================
    # NOVO PAINEL: RAIO-X DO APRENDIZADO NEURAL (PESOS DA IA)
    # =======================================================
    st.markdown("#### 🧬 Raio-X da Evolução Neural (Pesos Dinâmicos)")
    st.caption("Acompanhe em tempo real como o 'Cérebro' está recalibrando a força de cada estratégia após as auditorias.")
    
    pesos_ia = st.session_state.data.get("ia_pesos", {})
    if pesos_ia:
        cols_pesos = st.columns(len(pesos_ia))
        
        for idx, (nome_est, parametros) in enumerate(pesos_ia.items()):
            with cols_pesos[idx]:
                # Montando o HTML numa string blindada (sem espaços de quebra de linha que confundem o markdown)
                html_card = "<div style='background-color: white; padding: 15px; border-radius: 10px; border-top: 5px solid #930089; box-shadow: 0px 4px 10px rgba(0,0,0,0.06); height: 100%;'>"
                html_card += f"<div style='font-size: 14px; font-weight: 900; color: #333; text-align: center; margin-bottom: 5px;'>{nome_est.upper()}</div>"
                html_card += "<hr style='margin: 10px 0; border: none; border-top: 1px solid #f0f0f0;'>"
                
                for chave, valor in parametros.items():
                    html_card += f"<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;'><span style='font-size: 12px; color: #777; font-weight: 700;'>{chave.upper()}</span><span style='font-size: 15px; font-weight: 900; color: #930089;'>{valor:.2f}</span></div>"
                
                html_card += "</div>"
                
                # Renderiza o visual perfeito
                st.markdown(html_card, unsafe_allow_html=True)
                
    st.write("") # Espaçamento
    # =======================================================
        
    historico_painel = st.session_state.data.get("historico_dados", [])
    
    if historico_painel:
        ia = raciocinio_total_ia(historico_painel, st.session_state.data.get("ia_memoria", {}))
        if ia:
            tamanho_m = ia['qtd_matriz']
            st.markdown(f"### 🎯 Matriz Cirúrgica Atual — {tamanho_m} Dezenas")
            
            with st.container(border=True):
                st.markdown(f"#### 💰 Simulação de Custo do Fechamento (Matriz de {tamanho_m} dezenas)")
                garantia_alvo = st.radio("Alvo do Fechamento:", options=[15, 14, 13], format_func=lambda x: f"Garantia Absoluta de {x} Pontos", horizontal=True, key="radio_garantia_aba2")
                jogos_exatos, custo_exato = obter_dados_fechamento(ia['matriz_base'], garantia_alvo)
                st.success(
                    f"**Diagnóstico Matemático (100% Exato):**\n"
                    f"Para garantir **{garantia_alvo} pontos**, o sistema vai desdobrar exatamente **{jogos_exatos} bilhetes**.\n\n"
                    f"💸 **Custo Fixo Total ({jogos_exatos} x R$ 3,50): R$ {custo_exato:.2f}**"
                )

            st.markdown(f"#### 🧠 Diagnóstico Autônomo — Concurso Alvo {ia['alvo']}")
            ultimo_sorteio_str = " - ".join([f"{n:02d}" for n in historico_painel[-1]['dezenas']])
            st.markdown(f"**🎯 Último Sorteio Oficial (Concurso {historico_painel[-1]['concurso']})**")
            st.code(ultimo_sorteio_str)
            st.info(f"⚡ **LINHA TÁTICA ATIVADA:** {ia['estrategia']}\n\n**DIRETRIZ DA DECISÃO:** {ia['motivo_est']}\n\n🎯 **GRUPO DE ELITE ({tamanho_m} DEZENAS COMPILADAS):** " + ", ".join([f"{n:02d}" for n in ia['matriz_base']]))

            col_quentes, col_frias = st.columns(2)
            top_quentes = sorted(ia['freq'].items(), key=lambda x: x[1], reverse=True)[:5]
            top_atrasos = sorted(ia['atrasos'].items(), key=lambda x: x[1], reverse=True)[:5]
            
            with col_quentes:
                st.markdown("🔥 **Top 5 Dezenas mais Quentes:**")
                st.write(", ".join([f"{k:02d} ({v}x)" for k, v in top_quentes]))
            with col_frias:
                st.markdown("🧊 **Top 5 Maiores Atrasos:**")
                st.write(", ".join([f"{k:02d} ({v} conc.)" for k, v in top_atrasos]))

            st.markdown(f"⏳ **Status do Ciclo:** Aberto há {ia['ciclo_tam']} concursos. Faltam {len(ia['faltam_ciclo'])} dezenas: {ia['faltam_ciclo']}")

            st.markdown("#### ⚖️ Grade Dinâmica de Pesos Absolutos (Heatmap da IA)")
            pesos_ordenados = sorted(ia['pesos'].items(), key=lambda x: x[0])
            cols = st.columns(5)
            for idx, (dez, peso) in enumerate(pesos_ordenados):
                with cols[idx % 5]:
                    is_elite = dez in ia['matriz_base']
                    bg_color = "#930089" if is_elite else "#f4f6f9"
                    txt_color = "white" if is_elite else "#333"
                    border = "none" if is_elite else "1px solid #ddd"
                    st.markdown(f"""
                    <div style='background-color: {bg_color}; color: {txt_color}; padding: 10px; border-radius: 8px; border: {border}; text-align: center; margin-bottom: 10px;'>
                        <div style='font-size: 20px; font-weight: 900;'>{dez:02d}</div>
                        <div style='font-size: 11px; opacity: 0.9;'>Peso: {peso:.1f}</div>
                        {f"<div style='font-size: 10px; font-weight: bold; margin-top: 5px; background: rgba(0,0,0,0.2); border-radius: 4px;'>ELITE</div>" if is_elite else ""}
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Carregue o Cofre.json na Aba 1 para ativar a Inteligência Artificial.")

# --- TAB 3: GERADOR AUTÔNOMO ---
with tabs[2]:
    exibir_mini_painel_financeiro()
    st.markdown("### 🚀 Engenharia Combinatória (100% Exato)")

    if st.session_state.data["historico_dados"]:
        ia = raciocinio_total_ia(st.session_state.data["historico_dados"], st.session_state.data.get("ia_memoria", {}))
        tamanho_m = ia['qtd_matriz']
        st.markdown(f"#### ⚙️ Setup de Disparo — Alvo: `Concurso {ia['alvo']}` | 🎯 **Matriz Usada: {tamanho_m} Dezenas**")
        
        with st.container(border=True):
            st.markdown("#### 🎯 Alvo da Garantia Matemática")
            garantia_alvo = st.radio("Garantia:", options=[15, 14, 13], format_func=lambda x: f"Garantia Absoluta de {x} Pontos", horizontal=True, key="radio_garantia_aba3")
            jogos_exatos, custo_exato = obter_dados_fechamento(ia['matriz_base'], garantia_alvo)
            st.info(f"📊 **Volume Exato a Ser Gerado:** {jogos_exatos} Bilhetes\n\n💸 **Investimento Cravado:** R$ {custo_exato:.2f}")

            st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
            
            if st.button("🧬 GERAR FECHAMENTO EXATO", type="primary", use_container_width=True):
                st.info("⚙️ **Acionando MOTOR EXATO:** Desdobrando matriz...")
                
                st.session_state.data["jogos_salvos"] = [j for j in st.session_state.data["jogos_salvos"] if j.get('status') != "Aguardando Sorteio"]
                matriz_reduzida = gerar_fechamento_matematico(tuple(ia['matriz_base']), garantia_alvo)
                qtd_gerados = len(matriz_reduzida)
                gasto = qtd_gerados * 3.50
                prog_a = st.progress(0)
                
                for i, dezenas_jogo in enumerate(matriz_reduzida):
                    st.session_state.data["jogos_salvos"].append({
                        "id": str(uuid.uuid4()), "concurso_alvo": ia['alvo'], "dezenas": sorted(list(dezenas_jogo)),
                        "tamanho": len(dezenas_jogo), "estrategia": ia['cod_estrategia'], 
                        "justificativa": f"Matriz {ia['cod_estrategia']}. Garantia 100% de {garantia_alvo} pts.",
                        "status": "Aguardando Sorteio", "acertos": 0, "premio_valor": 0.0,
                        "matriz_origem": ia['matriz_base'], "dna": "🧬 Fechamento Matemático 100%"
                    })
                    if i % max(1, (qtd_gerados // 10)) == 0: prog_a.progress(min((i+1)/qtd_gerados, 1.0))
                        
                st.session_state.data['historico_custos'] += gasto
                salvar_dados(st.session_state.data)
                st.success(f"**🥇 FECHAMENTO CONCLUÍDO!** {qtd_gerados} bilhetes gerados exatos.")
                st.rerun()
    else: 
        st.warning("Aguardando sincronização de dados do Cofre na Aba 1.")

    jogos_espera = [j for j in st.session_state.data.get("jogos_salvos", []) if j.get('status') == "Aguardando Sorteio"]
    if jogos_espera:
        st.markdown("---")
        st.markdown("#### 👀 Pré-visualização dos Bilhetes Gerados")
        bilhetes_por_pagina = 30
        total_paginas = (len(jogos_espera) // bilhetes_por_pagina) + (1 if len(jogos_espera) % bilhetes_por_pagina > 0 else 0)
        if total_paginas > 1: pagina_atual = st.selectbox("Página (Aba 3)", range(1, total_paginas + 1), label_visibility="collapsed", key="pag_aba3")
        else: pagina_atual = 1
        inicio = (pagina_atual - 1) * bilhetes_por_pagina
        fim = inicio + bilhetes_por_pagina
        cols = st.columns(3)
        for idx, jogo in enumerate(jogos_espera[inicio:fim]):
            with cols[idx % 3]: exibir_card_volante(jogo, inicio + idx + 1)

# --- TAB 4: FILA DE SORTEIO ---
with tabs[3]:
    exibir_mini_painel_financeiro()
    st.markdown("### 🎫 Cartões Ativos e Auditados")
    
    jogos_em_espera = [j for j in st.session_state.data["jogos_salvos"] if j.get('status') == "Aguardando Sorteio"]
    total_premio = sum(j.get("premio_valor", 0) for j in st.session_state.data["jogos_salvos"] if j.get('status') == "Premiado")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("🎫 Jogos em Espera", len(jogos_em_espera))
    c2.metric("💰 Premiação Total Acumulada", f"R$ {total_premio:.2f}")
    c3.metric("📊 Bilhetes Auditados", len([j for j in st.session_state.data["jogos_salvos"] if j.get('status') != "Aguardando Sorteio"]))
    
    st.markdown("---")
    st.markdown("#### 🎯 A Matriz de Origem vs Sorteio Alvo")
    if st.session_state.data.get("jogos_salvos") and st.session_state.data.get("historico_dados"):
        num_ultimo_oficial = int(st.session_state.data["historico_dados"][-1]["concurso"])
        ultimo_jogo_criado = st.session_state.data["jogos_salvos"][-1]
        alvo_foco = ultimo_jogo_criado.get("concurso_alvo")
        matriz_usada = ultimo_jogo_criado.get("matriz_origem")
        
        if matriz_usada:
            elite_group = set(matriz_usada)
            tamanho_matriz = len(elite_group)
            col_a1, col_a2 = st.columns([1, 2])
            
            if alvo_foco <= num_ultimo_oficial:
                resultado_oficial = next((h for h in st.session_state.data["historico_dados"] if int(h["concurso"]) == int(alvo_foco)), None)
                if resultado_oficial:
                    sorteio_real = set(resultado_oficial["dezenas"])
                    acertos_elite = len(elite_group.intersection(sorteio_real))
                    
                    if "matrizes_computadas" not in st.session_state.data: st.session_state.data["matrizes_computadas"] = []
                    selo_concurso = f"matriz_alvo_{alvo_foco}"
                    if selo_concurso not in st.session_state.data["matrizes_computadas"]:
                        st.session_state.data["matrizes_computadas"].append(selo_concurso)
                        ledger = st.session_state.data["ledger_track"]
                        ledger["qtd_matrizes_conferidas"] = ledger.get("qtd_matrizes_conferidas", 0) + 1
                        ledger["soma_acertos_matriz"] = ledger.get("soma_acertos_matriz", 0) + acertos_elite
                        salvar_dados(st.session_state.data)
                    
                    with col_a1: st.metric(label=f"Acertos da Matriz (Sorteio {alvo_foco})", value=f"{acertos_elite} / {tamanho_matriz}")
                    with col_a2:
                        st.write(f"**Matriz de {tamanho_matriz} dezenas usada para gerar os jogos:**")
                        st.code(", ".join([f"{n:02d}" for n in sorted(list(elite_group))]))
                    if acertos_elite >= 11: st.success(f"🎯 A Matriz de {tamanho_matriz} dezenas acertou {acertos_elite} pontos no concurso {alvo_foco}!")
                    else: st.warning(f"A Matriz de {tamanho_matriz} dezenas não atingiu 11 pontos no concurso {alvo_foco}.")
            else:
                with col_a1: st.metric(label=f"Sorteio Alvo", value=f"{alvo_foco}", delta="Aguardando Resultado...", delta_color="off")
                with col_a2:
                    st.write(f"**Matriz de {tamanho_matriz} dezenas que gerou seus jogos:**")
                    st.code(", ".join([f"{n:02d}" for n in sorted(list(elite_group))]))
        else: st.info("Os jogos atuais são antigos e não têm a Matriz salva.")
    else: st.info("Gere jogos na Aba 3 para visualizar a matriz de origem.")

    if st.session_state.data["jogos_salvos"]:
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1: st.button("🗑️ LIMPAR TODOS", on_click=cb_excluir_todos, type="secondary", use_container_width=True)
        with col_btn2:
            ultimas_dezenas = []
            if 'caixa_latest' in st.session_state and 'dezenas' in st.session_state.caixa_latest: ultimas_dezenas = st.session_state.caixa_latest['dezenas']
            pdf_bytes = gerar_pdf_jogos(st.session_state.data["jogos_salvos"], ultimas_dezenas)
            st.download_button(label="📤 EXPORTAR RELATÓRIO (PDF)", data=pdf_bytes, file_name="Relatorio_LotoMatrix.pdf", mime="application/pdf", type="primary", use_container_width=True)

    st.markdown("---")
    st.markdown("### 🎫 Fila de Visualização")
    jogos = st.session_state.data.get("jogos_salvos", [])
    if jogos:
        bilhetes_por_pagina = 30
        total_paginas = (len(jogos) // bilhetes_por_pagina) + (1 if len(jogos) % bilhetes_por_pagina > 0 else 0)
        if total_paginas > 1:
            st.markdown(f"<div style='color: #930089; font-weight: bold; margin-bottom: 5px;'>Total: {len(jogos)} bilhetes | Escolha a página:</div>", unsafe_allow_html=True)
            pagina_atual = st.selectbox("Navegação de Páginas", range(1, total_paginas + 1), label_visibility="collapsed", key="pag_aba4")
        else:
            pagina_atual = 1
            st.markdown(f"<div style='color: #930089; font-weight: bold; margin-bottom: 15px;'>Total: {len(jogos)} bilhetes</div>", unsafe_allow_html=True)
            
        inicio = (pagina_atual - 1) * bilhetes_por_pagina
        fim = inicio + bilhetes_por_pagina
        cols = st.columns(3)
        for idx, j in enumerate(jogos[inicio:fim]):
            if not isinstance(j, dict): continue
            numero_real_jogo = inicio + idx + 1
            with cols[idx % 3]:
                exibir_card_volante(j, numero_real_jogo)
                status = j.get('status', 'Aguardando Sorteio')
                if status == "Premiado": st.success(f"✅ PREMIADO ({j.get('acertos', 0)} Acertos)\n💰 R$ {j.get('premio_valor', 0):.2f}")
                elif status == "Não Premiado": st.error(f"❌ NÃO PREMIADO ({j.get('acertos', 0)} Acertos)")
                else: st.info("⏳ AGUARDANDO SORTEIO")
                id_jogo = j.get('id', str(uuid.uuid4()))
                st.button("🗑️ Apagar", key=f"del_{id_jogo}", on_click=cb_excluir_jogo, args=(id_jogo,), use_container_width=True)
                st.markdown("<br><br>", unsafe_allow_html=True)
    else: st.info("Nenhum bilhete registrado na fila.")

# --- TAB 5: SINCRONIZAÇÃO E AUDITORIA (LIVRO-CAIXA REAL) ---
with tabs[4]:
    exibir_mini_painel_financeiro()
    st.markdown("### 🏆 Sincronização Oficial e Auditoria Pericial")

    with st.container(border=True):
        st.markdown("#### 🛸 Gerenciamento de Banco de Dados Oficial")
        st.write("Detecta sorteios faltantes ou recria o banco de dados do ZERO para iniciar a operação.")
        col_massa1, col_massa2 = st.columns(2)
        
        with col_massa1:
            if st.button("🛸 BUSCAR FALTANTES E AUDITAR (GAP)", type="primary", use_container_width=True):
                historico = st.session_state.data.get("historico_dados", [])
                if not historico: st.error("Banco vazio. Use o botão ao lado para baixar tudo do zero.")
                else:
                    ultimo_salvo = int(historico[-1]["concurso"])
                    try:
                        res_latest = requests.get("https://loteriascaixa-api.herokuapp.com/api/lotofacil/latest", verify=False, timeout=10).json()
                        ultimo_oficial = int(res_latest['concurso'])
                        if ultimo_salvo >= ultimo_oficial: st.info("O sistema já está atualizado com o último sorteio.")
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
                                        "concurso": num, "dezenas": dezenas_sorteadas, "data": res_conc.get('data', '')
                                    })
                                    rateios_massa = extrair_rateios_api(res_conc.get('premiacoes', []))
                                    lucro_parcial, relatorio_parcial = auditar_e_aprender_unificado(num, dezenas_sorteadas, rateios_massa)
                                    lucro_acumulado_massa += lucro_parcial
                                    logs_massa.extend(relatorio_parcial)
                                barra.progress((i + 1) / len(concursos_faltantes))
                            if logs_massa: st.session_state.ultimo_aprendizado = list(set(logs_massa))
                            salvar_dados(st.session_state.data)
                            st.success(f"✅ GAPs processados com sucesso! Banco atualizado. R$ {lucro_acumulado_massa:.2f} creditados.")
                            st.rerun()
                    except Exception as e: st.error(f"Erro ao processar GAPs: {e}")

        with col_massa2:
            st.markdown("#### ☢️ Iniciar Operação (Download Base)")
            if st.button("📥 1. BAIXAR SORTEIOS (DO 1 AO ATUAL)", type="secondary", use_container_width=True):
                st.session_state.data["historico_dados"] = []
                with st.spinner("Baixando base de dados da Caixa do 1º sorteio em diante..."):
                    try:
                        res_todos = requests.get("https://loteriascaixa-api.herokuapp.com/api/lotofacil", verify=False, timeout=60).json()
                        res_todos = sorted(res_todos, key=lambda k: int(k['concurso']))
                        barra_down = st.progress(0)
                        total_concursos = len(res_todos)
                        for i, res_conc in enumerate(res_todos):
                            st.session_state.data["historico_dados"].append({
                                "concurso": int(res_conc['concurso']), "dezenas": sorted([int(d) for d in res_conc['dezenas']]), "data": res_conc.get('data', '')
                            })
                            if i % 50 == 0: barra_down.progress((i + 1) / total_concursos)
                        salvar_dados(st.session_state.data)
                        barra_down.progress(1.0)
                        st.success(f"✅ Download de {total_concursos} sorteios concluído. O Banco está apto.")
                    except Exception as e: st.error(f"Erro na conexão com API: {e}")

            with st.expander("⚙️ Configurar Sincronização Seletiva"):
                limite_concurso = st.number_input("Limite do Concurso (até onde baixar):", min_value=1, step=1, value=3000)
                concurso_especifico = st.number_input("Concurso Específico (apenas um):", min_value=1, step=1)

            if st.button("📥 2. BAIXAR ATÉ O CONCURSO X", type="secondary", use_container_width=True):
                with st.spinner(f"Baixando base de dados até o concurso {limite_concurso}..."):
                    try:
                        res_todos = requests.get("https://loteriascaixa-api.herokuapp.com/api/lotofacil", verify=False, timeout=60).json()
                        res_filtrado = sorted([r for r in res_todos if int(r['concurso']) <= limite_concurso], key=lambda k: int(k['concurso']))
                        st.session_state.data["historico_dados"] = []
                        for res_conc in res_filtrado:
                            st.session_state.data["historico_dados"].append({
                                "concurso": int(res_conc['concurso']), "dezenas": sorted([int(d) for d in res_conc['dezenas']]), "data": res_conc.get('data', '')
                            })
                        salvar_dados(st.session_state.data)
                        st.success(f"✅ Download até {limite_concurso} concluído!")
                    except Exception as e: st.error(f"Erro na sincronização: {e}")

            if st.button("📥 3. BAIXAR CONCURSO ESPECÍFICO", type="secondary", use_container_width=True):
                with st.spinner(f"Buscando concurso {concurso_especifico}..."):
                    try:
                        res_todos = requests.get("https://loteriascaixa-api.herokuapp.com/api/lotofacil", verify=False, timeout=60).json()
                        res_unico = [r for r in res_todos if int(r['concurso']) == concurso_especifico]
                        if res_unico:
                            res_conc = res_unico[0]
                            novo_dado = {"concurso": int(res_conc['concurso']), "dezenas": sorted([int(d) for d in res_conc['dezenas']]), "data": res_conc.get('data', '')}
                            concursos_existentes = [h['concurso'] for h in st.session_state.data["historico_dados"]]
                            if novo_dado['concurso'] not in concursos_existentes:
                                st.session_state.data["historico_dados"].append(novo_dado)
                                st.session_state.data["historico_dados"] = sorted(st.session_state.data["historico_dados"], key=lambda k: k['concurso'])
                                salvar_dados(st.session_state.data)
                                st.success(f"✅ Concurso {concurso_especifico} adicionado com sucesso!")
                            else: st.warning("Este concurso já consta na base.")
                        else: st.error("Concurso não encontrado na API.")
                    except Exception as e: st.error(f"Erro na sincronização: {e}")            

    col_sync1, col_sync2 = st.columns(2)
    with col_sync1:
        with st.container(border=True):
            st.markdown("#### 🌐 Sincronização Automática (API Caixa)")
            st.write("Conecta aos servidores para baixar o último sorteio, atualizar o banco e auditar a fila da Aba 4.")
            
            if st.button("🔄 Buscar Último Resultado Oficial", type="primary", use_container_width=True):
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
                            
                            st.success(f"✅ Sincronização Automática Concluída! Prêmios Auditados: R$ {lucro_total:.2f}")
                            if lucro_total > 0: st.toast("Lucro Creditado no ROI", icon="💰")
                            st.rerun()
                        else: st.error("Erro na API da Caixa. Tente a inserção manual ao lado.")
                    except Exception as e: st.error(f"Falha de conexão com a API: {e}")

    with col_sync2:
        with st.container(border=True):
            st.markdown("#### 🛠️ Inserção e Conferência Manual")
            st.write("Insira o resultado em qualquer formato (ex: 01.02.03, ou 01 02). O sistema auditará a fila.")
            
            concurso_manual = st.number_input("Número do Concurso:", min_value=1, step=1, key="num_conc_manual")
            dezenas_texto = st.text_input("Cole as Dezenas Sorteadas (qualquer formato):", key="dez_manual_input")
            
            if st.button("✅ Confirmar e Auditar Fila Manualmente", use_container_width=True):
                nums_str = re.findall(r'\d+', dezenas_texto)
                try:
                    dezenas_oficiais = sorted([int(n) for n in nums_str])
                    if len(dezenas_oficiais) != 15: st.error(f"Erro: O sistema identificou {len(dezenas_oficiais)} números. Insira exatamente 15.")
                    elif len(set(dezenas_oficiais)) != 15: st.error("Erro: Existem dezenas repetidas. Verifique sua digitação.")
                    elif not all(1 <= n <= 25 for n in dezenas_oficiais): st.error("Erro: As dezenas devem estar entre 01 e 25.")
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
                        st.success(f"✅ Operação Manual Concluída. Banco atualizado e prêmios auditados no ROI: R$ {lucro_total:.2f}.")
                        st.rerun()
                except ValueError:
                    st.error("Erro estrutural na conversão de números.")

    with st.container(border=True):
        st.markdown("#### 🧠 Forçar Reprocessamento da Inteligência Artificial")
        st.write("Antes de gerar novos jogos, clique aqui para obrigar a IA a reler o histórico inteiro e recalcular todas as tendências, ciclos e pesos para o concurso que está por vir.")
        if st.button("🔄 ATUALIZAR E FORÇAR LEITURA PARA O PRÓXIMO SORTEIO", type="primary", use_container_width=True):
            st.session_state.data["ia_memoria"] = {}
            if 'ultimo_aprendizado' in st.session_state: st.session_state.ultimo_aprendizado = []
            salvar_dados(st.session_state.data)
            st.success("✅ Memória Cache zerada! A IA recalculará a matriz com base 100% no histórico atualizado.")
            st.rerun()            

    st.divider()

    if 'ultimo_aprendizado' in st.session_state and st.session_state.ultimo_aprendizado:
        st.markdown("#### 📋 Relatório da Última Auditoria Realizada:")
        for aprendizado in st.session_state.ultimo_aprendizado:
            st.info(f"✔️ {aprendizado}")

    if 'caixa_latest' in st.session_state:
        r = st.session_state.caixa_latest
        st.markdown(f"#### 🏛️ Último Extrato Salvo da Caixa: Concurso {r['concurso']} ({r.get('data', '')})")
        st.code(" - ".join([f"{n:02d}" for n in r['dezenas']]))
        if r.get('premiacoes'):
            st.markdown("#### 💰 Tabela do Rateio Registrada")
            st.table(pd.DataFrame(r['premiacoes']))
