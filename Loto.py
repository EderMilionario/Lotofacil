import streamlit as st
import pandas as pd
import requests
import json
import random
import uuid
import re
import itertools
from datetime import datetime
from collections import Counter
import urllib3
from fpdf import FPDF
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =====================================================================
# 1. CONFIGURAÇÃO INICIAL E ROTEAMENTO
# =====================================================================
st.set_page_config(page_title="Loterias Pro", page_icon="🍀", layout="wide")

if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "login"
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

# =====================================================================
# 2. DESIGN DO SISTEMA (CABEÇALHO E RODAPÉ)
# =====================================================================
def exibir_cabecalho(loteria_especifica=None, cor_loteria=None, icone_loteria=None):
    titulo_multicolorido = """
    <div style='text-align: center; margin-bottom: 10px;'>
        <span style='color: #209869; font-size: 36px; font-weight: bold;'>L</span>
        <span style='color: #930089; font-size: 36px; font-weight: bold;'>o</span>
        <span style='color: #260085; font-size: 36px; font-weight: bold;'>t</span>
        <span style='color: #F78100; font-size: 36px; font-weight: bold;'>e</span>
        <span style='color: #0066b3; font-size: 36px; font-weight: bold;'>r</span>
        <span style='color: #ED1622; font-size: 36px; font-weight: bold;'>i</span>
        <span style='color: #B8922A; font-size: 36px; font-weight: bold;'>a</span>
        <span style='color: #209869; font-size: 36px; font-weight: bold;'>s</span>
        <span style='color: #333333; font-size: 36px; font-weight: bold;'> </span>
        <span style='color: #930089; font-size: 36px; font-weight: bold;'>P</span>
        <span style='color: #260085; font-size: 36px; font-weight: bold;'>r</span>
        <span style='color: #F78100; font-size: 36px; font-weight: bold;'>o</span>
    </div>
    """
    st.markdown(titulo_multicolorido, unsafe_allow_html=True)
    
    if loteria_especifica:
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            if st.button("⬅️ Voltar ao Lobby", use_container_width=True):
                st.session_state.pagina_atual = "lobby"
                st.rerun()
        with col2:
            st.markdown(f"<h3 style='text-align: center; color: {cor_loteria}; margin-top: -5px;'>{icone_loteria} {loteria_especifica}</h3>", unsafe_allow_html=True)
        st.divider()

def exibir_rodape():
    ano_atual = datetime.now().year
    rodape_html = f"""
    <hr style='margin-top: 50px;'>
    <div style='text-align: center; color: #888; font-size: 14px;'>
        &copy; {ano_atual} Loterias Pro - Motor de Inferência Matemática e Algorítmica.<br>
        Todos os direitos reservados.
    </div>
    """
    st.markdown(rodape_html, unsafe_allow_html=True)


# =====================================================================
# 3. FUNÇÕES GLOBAIS DA LOTOFÁCIL
# =====================================================================
def sanitizar_dados(d):
    if "historico_dados" not in d: d["historico_dados"] = []
    if "jogos_salvos" not in d: d["jogos_salvos"] = []
    if "historico_custos" not in d: d["historico_custos"] = 0.0
    if "historico_premios" not in d: d["historico_premios"] = 0.0
    
    if "ia_pesos" not in d:
        d["ia_pesos"] = {
            "Tendencia Forte": {"p1": 20.0, "p2": 5.0, "bonus": 40.0},
            "Simetria Conjunta": {"p1": 15.0, "p2": 8.0, "bonus1": 30.0, "bonus2": 20.0},
            "Reversao de Tendencia": {"p1": 10.0, "bonus": 100.0},
            "Ciclo Supremo": {"p1": 15.0, "p2": 5.0, "bonus": 30.0},
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

def ajustar_ia(cod_est, acertos_matriz):
    ia_pesos = st.session_state.data["ia_pesos"]
    est_key = cod_est if cod_est in ia_pesos else "Default"
    pesos_atuais = ia_pesos[est_key]
    
    if acertos_matriz == 15: fator = 1.20       
    elif acertos_matriz == 14: fator = 1.10     
    elif acertos_matriz == 13: fator = 1.05     
    elif acertos_matriz == 12: fator = 0.95     
    else: fator = 0.90                          
    
    for k in pesos_atuais:
        novo_peso = pesos_atuais[k] * fator
        ia_pesos[est_key][k] = round(max(2.0, min(novo_peso, 500.0)), 2)
            
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
    if rateios is None: rateios = {}
    v11, v12, v13, v14, v15 = rateios.get(11, 7.0), rateios.get(12, 14.0), rateios.get(13, 35.0), rateios.get(14, 1500.0), rateios.get(15, 1500000.0)
    
    lucro_total = 0.0
    relatorio = []
    sorteio_set = set(dezenas_sorteadas)
    
    jogos_processados = 0
    premiados = 0
    max_pts = 0
    
    if "global_hits" not in st.session_state.data: st.session_state.data["global_hits"] = {11: 0, 12: 0, 13: 0, 14: 0, 15: 0}
    if "ledger_track" not in st.session_state.data: st.session_state.data["ledger_track"] = {"bilhetes": 0, "premiados_geral": 0, "elite": 0}
    if "matrizes_reais_hits" not in st.session_state.data: st.session_state.data["matrizes_reais_hits"] = {11: 0, 12: 0, 13: 0, 14: 0, 15: 0, "total": 0, "soma_acertos": 0}
    if "matrizes_auditadas_ids" not in st.session_state.data: st.session_state.data["matrizes_auditadas_ids"] = []
        
    ledger = st.session_state.data["ledger_track"]
    hits_bilhetes = st.session_state.data["global_hits"]
    matriz_usada_neste_concurso = None
    
    for j in st.session_state.data.get("jogos_salvos", []):
        alvo_do_jogo = j.get('concurso_alvo')
        pode_auditar = False
        if str(alvo_do_jogo) == str(concurso) or (isinstance(alvo_do_jogo, int) and alvo_do_jogo <= concurso) or str(alvo_do_jogo) == "Legado":
            pode_auditar = True
            if j.get("matriz_origem"): matriz_usada_neste_concurso = j["matriz_origem"]
        
        if j.get('status') == "Aguardando Sorteio" and pode_auditar:
            jogos_processados += 1
            ledger["bilhetes"] += 1
            pontos = len(set(j.get('dezenas', [])).intersection(sorteio_set))
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
            else: j['status'] = "Não Premiado"

    matrizes_hits = st.session_state.data["matrizes_reais_hits"]
    matrizes_auditadas = st.session_state.data["matrizes_auditadas_ids"]
    selo_matriz = f"conc_{concurso}"
    
    if matriz_usada_neste_concurso and selo_matriz not in matrizes_auditadas:
        acertos_matriz = len(set(matriz_usada_neste_concurso).intersection(sorteio_set))
        matrizes_auditadas.append(selo_matriz)
        matrizes_hits["total"] = matrizes_hits.get("total", 0) + 1
        matrizes_hits["soma_acertos"] = matrizes_hits.get("soma_acertos", 0) + acertos_matriz
        est_da_matriz = "Default"
        for j in st.session_state.data.get("jogos_salvos", []):
            if j.get("matriz_origem") == matriz_usada_neste_concurso:
                est_da_matriz = j.get("estrategia", "Default")
                break
        ajustar_ia(est_da_matriz, acertos_matriz)
        if acertos_matriz >= 11:
            chave = int(min(acertos_matriz, 15)) 
            matrizes_hits[chave] = matrizes_hits.get(chave, 0) + 1 
                
    st.session_state.data["matrizes_reais_hits"] = matrizes_hits
    st.session_state.data["matrizes_auditadas_ids"] = matrizes_auditadas
    st.session_state.data["global_hits"] = hits_bilhetes
    st.session_state.data["ledger_track"] = ledger
    
    if jogos_processados > 0: relatorio.append(f"Auditoria Concurso {concurso}: {premiados}/{jogos_processados} bilhetes premiados. Pico: {max_pts} pts.")
    return lucro_total, relatorio

@st.cache_data(show_spinner="🧠 Processando Matriz (Fechamento Matemático)...")
def gerar_fechamento_matematico(dezenas_tuple, garantia):
    dezenas = list(dezenas_tuple)
    todas_comb_15 = list(itertools.combinations(dezenas, 15))
    if garantia == 15 or len(dezenas) <= 15: return [list(c) for c in todas_comb_15]

    comb_bits = [sum(1 << num for num in c) for c in todas_comb_15]
    sorteios_possiveis = set(range(len(comb_bits)))
    bilhetes_escolhidos, cobertura = [], []
    
    for b in comb_bits:
        cobertura.append({j for j, s in enumerate(comb_bits) if (b & s).bit_count() >= garantia})
        
    while sorteios_possiveis:
        melhor_idx = max(range(len(cobertura)), key=lambda i: len(cobertura[i].intersection(sorteios_possiveis)))
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

    ciclo_atual, jogos_ciclo = set(), 0
    for h in historico:
        ciclo_atual.update(h['dezenas'])
        jogos_ciclo += 1
        if len(ciclo_atual) == 25: ciclo_atual, jogos_ciclo = set(), 0
            
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
    except: media_volatilidade = 9.0

    if qtd_faltam <= 2: cod_est, qtd_matriz, tatic_desc = "Ciclo Supremo", 18, "Cerco Fim de Ciclo."
    elif media_volatilidade < 8.0: cod_est, qtd_matriz, tatic_desc = "Reversao de Tendencia", 20, "Caos/Reversão."
    elif media_volatilidade > 9.5: cod_est, qtd_matriz, tatic_desc = "Tendencia Forte", 17, "Tendência Absoluta."
    else: cod_est, qtd_matriz, tatic_desc = "Simetria Conjunta", 19, "Padrão de Equilíbrio."

    est_pesos = st.session_state.data["ia_pesos"].get(cod_est, st.session_state.data["ia_pesos"]["Default"])

    unified_scores = {}
    for n in range(1, 26):
        n = int(n)
        aparicoes_curtas, aparicoes_longas, delay = freq_micro.get(n, 0), freq_recente.get(n, 0), atrasos.get(n, 0)
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

        if qtd_faltam <= 3 and n in faltam_ciclo: score_calc += 5000.0
        unified_scores[n] = float(score_calc)

    IMPARES_SET = {1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25}
    PRIMOS_SET = {2, 3, 5, 7, 11, 13, 17, 19, 23}
    MOLDURA_SET = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
    FIBO_SET = {1, 2, 3, 5, 8, 13, 21}
    MULT3_SET = {3, 6, 9, 12, 15, 18, 21, 24}
    ULT_SORT_SET, AUSENTES_SET = set(ultimo_sorteio), set(range(1, 26)) - set(ultimo_sorteio)
    
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
        "motivo_est": justificativa, "pesos": {int(x): round(float(unified_scores.get(x, 0.0)), 2) for x in range(1, 26)},
        "freq": dict(freq_recente), "atrasos": dict(atrasos), "ciclo_tam": int(jogos_ciclo), 
        "faltam_ciclo": faltam_ciclo, "soma": media_soma, "impares": c_imp, "primos": c_prim, "moldura": c_mold,
        "repetidas": c_rep, "ausentes": len(matriz_final)-c_rep, "fibo": c_fibo, "mult3": c_mult3,
        "alvo": int((historico[-1]['concurso'] + 1)) if historico else 1, "qtd_matriz": int(qtd_matriz), 
        "matriz_base": matriz_final, "perf": {}, "volatilidade": media_volatilidade
    }

def gerar_pdf_jogos(jogos, dezenas_anteriores=None):
    if dezenas_anteriores is None: dezenas_anteriores = []
    def limpar_latin1(texto): return str(texto).replace("🧬", "").replace("🍀", "").replace("🎫", "").replace("⚠️", "").encode('latin-1', 'ignore').decode('latin-1')
    pdf = FPDF()
    pdf.set_auto_page_break(auto=False)
    margem_x, margem_y, largura_card, altura_card, espaco_x, espaco_y = 10, 35, 90, 80, 5, 5
    sorteio_set = set(dezenas_anteriores)

    for i, j in enumerate(jogos):
        if i % 6 == 0:
            pdf.add_page()
            pdf.set_text_color(147, 0, 137)
            pdf.set_font('Arial', 'B', 16)
            pdf.set_xy(10, 12)
            pdf.cell(0, 10, "LotoMatrix PRO - Relatorio Oficial", ln=0)
            pdf.set_font('Arial', '', 9)
            pdf.set_text_color(100, 100, 100)
            pdf.set_xy(10, 20)
            pdf.cell(0, 8, f"TOTAL: {len(jogos)} BILHETES  |  Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=0)
            pdf.line(10, 28, 200, 28)

        coluna, linha = (i % 6) % 2, (i % 6) // 2
        x_start = margem_x + (coluna * (largura_card + espaco_x))
        y_start = margem_y + (linha * (altura_card + espaco_y))

        estrategia = limpar_latin1(str(j.get('estrategia', 'Padrao')))
        dezenas = j.get('dezenas', [])
        alvo = limpar_latin1(str(j.get('concurso_alvo', 'N/A')))
        
        pdf.set_fill_color(252, 245, 255)
        pdf.rect(x_start, y_start, largura_card, altura_card, 'F')
        pdf.set_fill_color(147, 0, 137)
        pdf.rect(x_start, y_start, 2, altura_card, 'F')

        pdf.set_text_color(40, 40, 40)
        pdf.set_font('Arial', 'B', 10)
        pdf.set_xy(x_start + 5, y_start + 4)
        pdf.cell(50, 6, f"JOGO {(i+1):02d}", ln=0)
        
        pdf.set_font('Arial', '', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.set_xy(x_start + 40, y_start + 4)
        pdf.cell(45, 6, f"Alvo: {alvo}", ln=0, align='R')

        pdf.set_text_color(147, 0, 137) 
        pdf.set_font('Arial', 'B', 7)
        pdf.set_xy(x_start + 5, y_start + 9)
        pdf.cell(80, 5, f"{estrategia[:35]}", ln=0)

        bolinha_x_start, bolinha_y_start, passo_x, passo_y = x_start + 18, y_start + 22, 11, 9
        for num in range(1, 26):
            lin, col = (num - 1) // 5, (num - 1) % 5
            cx, cy = bolinha_x_start + (col * passo_x), bolinha_y_start + (lin * passo_y)
            if num in dezenas:
                if num in sorteio_set: pdf.set_fill_color(40, 167, 69)
                else: pdf.set_fill_color(147, 0, 137)
                pdf.set_text_color(255, 255, 255)
            else:
                pdf.set_fill_color(235, 235, 235)
                pdf.set_text_color(150, 150, 150)
            pdf.ellipse(cx, cy, 7, 7, 'F')
            pdf.set_xy(cx, cy)
            pdf.set_font('Arial', 'B', 7)
            pdf.cell(7, 7, f"{num:02d}", align='C')

        justificativa_texto = str(j.get('justificativa', ''))
        match = re.search(r'(\d+) pts', justificativa_texto)
        texto_rodape = f"Garantia: {match.group(1)} Pontos" if match else "Fechamento Absoluto"
        pdf.set_text_color(120, 120, 120)
        pdf.set_font('Arial', 'B', 7)
        pdf.set_xy(x_start + 5, y_start + altura_card - 8)
        pdf.cell(80, 5, texto_rodape, ln=0, align='C')

    resultado = pdf.output(dest='S')
    if isinstance(resultado, str): return resultado.encode('latin-1', 'ignore')
    return bytes(resultado)

def exibir_card_volante(jogo, numero_jogo, sorteio_real=None):
    dezenas, alvo, estrategia = jogo.get('dezenas', []), jogo.get('concurso_alvo', 'N/A'), jogo.get('estrategia', 'Padrão')
    match = re.search(r'(\d+) pts', str(jogo.get('justificativa', '')))
    texto_rodape = f"Fechamento 100% Matemático - Garantia de {match.group(1)} Pontos" if match else "Fechamento Matemático Absoluto"
    sorteio_set = set(sorteio_real) if sorteio_real else set()

    grid_html = "<div style='display: grid; grid-template-columns: repeat(5, 1fr); gap: 6px; margin-bottom: 12px; justify-items: center;'>"
    for num in range(1, 26):
        if num in dezenas:
            bg_color, txt_color, border, shadow = ("#28a745", "white", "none", "box-shadow: 0 0 5px #28a745;") if num in sorteio_set else ("#930089", "white", "none", "box-shadow: 0 2px 4px rgba(147,0,137,0.3);")
        else: bg_color, txt_color, border, shadow = "#f4f6f9", "#bbb", "1px solid #ddd", ""
        grid_html += f"<div style='background-color: {bg_color}; color: {txt_color}; border: {border}; {shadow} text-align: center; border-radius: 50%; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: bold;'>{num:02d}</div>"
    grid_html += "</div>"
    
    html_card = f"<div style='background-color: #ffffff; border: 1px solid #e0e0e0; padding: 15px; border-radius: 8px; margin-bottom: 15px; box-shadow: 2px 2px 8px rgba(0,0,0,0.05);'><div style='display: flex; justify-content: space-between; border-bottom: 1px solid #eee; padding-bottom: 8px; margin-bottom: 12px;'><span style='font-size: 15px; font-weight: bold; color: #930089;'>🎫 JOGO {numero_jogo:02d}</span><span style='font-size: 12px; font-weight: bold; color: #666;'>Alvo: {alvo}</span></div><div style='font-size: 11px; color: #555; margin-bottom: 12px; font-weight: bold; text-transform: uppercase;'>ESTRATÉGIA: {estrategia}</div>{grid_html}<div style='text-align: center; font-size: 10px; font-weight: bold; color: #930089; background: rgba(147, 0, 137, 0.08); padding: 6px; border-radius: 4px; margin-top: 5px;'>{texto_rodape}</div></div>"
    st.markdown(html_card, unsafe_allow_html=True)

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
# 4. FUNÇÕES GLOBAIS DA MEGA-SENA
# =====================================================================
def sanitizar_dados_mega(d):
    if not isinstance(d, dict): d = {}
    if "historico_dados" not in d: d["historico_dados"] = []
    if "jogos_salvos" not in d: d["jogos_salvos"] = []
    if "historico_custos" not in d: d["historico_custos"] = 0.0
    if "historico_premios" not in d: d["historico_premios"] = 0.0
    if "ia_pesos" not in d:
        d["ia_pesos"] = {
            "Arbitragem de Massa": {"p_termo": 30.0, "p_comport": 20.0, "p_final": 15.0},
            "Caos Térmico": {"p_termo": 50.0, "p_comport": 10.0, "p_final": 25.0},
            "Dispersão Ortogonal": {"p_termo": 20.0, "p_comport": 40.0, "p_final": 30.0},
            "Default": {"p_termo": 25.0, "p_comport": 25.0, "p_final": 20.0}
        }
    return d

def salvar_dados_mega(dados):
    try:
        with open("Cofre_Mega.json", "w", encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
    except Exception as e: pass

def cb_carregar_cofre_mega():
    file = st.session_state.uploader_cofre_mega
    if file:
        try:
            st.session_state.data_mega = sanitizar_dados_mega(json.load(file))
            st.toast("Cofre Mega-Sena sincronizado!", icon="✅")
        except Exception as e: st.error(f"Erro: {e}")

def cb_excluir_jogo_mega(jogo_id):
    st.session_state.data_mega['jogos_salvos'] = [j for j in st.session_state.data_mega['jogos_salvos'] if j.get('id') != jogo_id]
    st.toast("Bilhete deletado.", icon="🗑️")

def cb_excluir_todos_mega():
    st.session_state.data_mega['jogos_salvos'] = []
    st.toast("Fila limpa.", icon="🧹")

def extrair_rateios_api_mega(premiacoes):
    rateios = {4: 1200.0, 5: 45000.0, 6: 35000000.0}
    for p in premiacoes:
        descricao = p.get('descricao', '').lower()
        if '6 acertos' in descricao or 'sena' in descricao: rateios[6] = float(p.get('valorPremio', 35000000.0))
        elif '5 acertos' in descricao or 'quina' in descricao: rateios[5] = float(p.get('valorPremio', 45000.0))
        elif '4 acertos' in descricao or 'quadra' in descricao: rateios[4] = float(p.get('valorPremio', 1200.0))
    return rateios

def calcular_premio_multiplo_mega(pontos, v4, v5, v6):
    if pontos == 6: return v6
    if pontos == 5: return v5
    if pontos == 4: return v4
    return 0.0

def exibir_mini_painel_financeiro_mega():
    c = st.session_state.data_mega.get("historico_custos", 0.0)
    p = st.session_state.data_mega.get("historico_premios", 0.0)
    roi = p - c
    cor_roi = "green" if roi >= 0 else "red"
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("💸 Investimento Total", f"R$ {c:,.2f}")
    with col2: st.metric("💰 Prêmios Recuperados", f"R$ {p:,.2f}")
    with col3: st.markdown(f"<div style='background-color:white; padding:10px; border-radius:12px; border-left:6px solid {('#209869' if roi>=0 else '#dd3333')}; box-shadow: 0 4px 6px rgba(0,0,0,0.04);'><p style='margin:0; font-size:14px; color:#666; font-weight:bold;'>📈 ROI Líquido</p><h3 style='margin:0; color:{cor_roi};'>R$ {roi:,.2f}</h3></div>", unsafe_allow_html=True)
    st.write("")

def ajustar_ia_mega(cod_est, acertos_matriz):
    ia_pesos = st.session_state.data_mega["ia_pesos"]
    est_key = cod_est if cod_est in ia_pesos else "Default"
    pesos_atuais = ia_pesos[est_key]
    
    if acertos_matriz == 6: fator = 1.25
    elif acertos_matriz == 5: fator = 1.15
    elif acertos_matriz == 4: fator = 1.05
    else: fator = 0.95 
    
    for k in pesos_atuais:
        ia_pesos[est_key][k] = round(max(2.0, min(pesos_atuais[k] * fator, 500.0)), 2)
    st.session_state.data_mega["ia_pesos"] = ia_pesos

@st.cache_data(show_spinner="🧠 Processando Matriz Mega-Sena...")
def gerar_fechamento_matematico_mega(dezenas_tuple, garantia):
    dezenas = list(dezenas_tuple)
    todas_comb_6 = list(itertools.combinations(dezenas, 6))
    if garantia == 6 or len(dezenas) <= 6: return [list(c) for c in todas_comb_6]

    comb_bits = [sum(1 << num for num in c) for c in todas_comb_6]
    sorteios_possiveis = set(range(len(comb_bits)))
    bilhetes_escolhidos, cobertura = [], []
    
    for b in comb_bits:
        cobertura.append({j for j, s in enumerate(comb_bits) if (b & s).bit_count() >= garantia})
        
    while sorteios_possiveis:
        melhor_idx = max(range(len(cobertura)), key=lambda i: len(cobertura[i].intersection(sorteios_possiveis)))
        bilhetes_escolhidos.append(list(todas_comb_6[melhor_idx]))
        sorteios_possiveis -= cobertura[melhor_idx]
    return bilhetes_escolhidos

def obter_dados_fechamento_mega(matriz_base, garantia):
    jogos = gerar_fechamento_matematico_mega(tuple(matriz_base), garantia)
    return len(jogos), len(jogos) * 5.00

def auditar_e_aprender_unificado_mega(concurso, dezenas_sorteadas, rateios=None):
    if rateios is None: rateios = {4: 1200.0, 5: 45000.0, 6: 35000000.0}
    v4, v5, v6 = rateios.get(4, 1200.0), rateios.get(5, 45000.0), rateios.get(6, 35000000.0)
    lucro_total = 0.0
    relatorio = []
    sorteio_set = set(dezenas_sorteadas)
    jogos_processados, premiados, max_pts = 0, 0, 0
    
    if "global_hits" not in st.session_state.data_mega: st.session_state.data_mega["global_hits"] = {4: 0, 5: 0, 6: 0}
    if "ledger_track" not in st.session_state.data_mega: st.session_state.data_mega["ledger_track"] = {"bilhetes": 0, "premiados_geral": 0, "elite": 0}
    if "matrizes_reais_hits" not in st.session_state.data_mega: st.session_state.data_mega["matrizes_reais_hits"] = {4: 0, 5: 0, 6: 0, "total": 0, "soma_acertos": 0}
    if "matrizes_auditadas_ids" not in st.session_state.data_mega: st.session_state.data_mega["matrizes_auditadas_ids"] = []
    
    ledger = st.session_state.data_mega["ledger_track"]
    hits_bilhetes = st.session_state.data_mega["global_hits"]
    matriz_usada = None
    
    for j in st.session_state.data_mega.get("jogos_salvos", []):
        alvo = j.get('concurso_alvo')
        pode = str(alvo) == str(concurso) or (isinstance(alvo, int) and alvo <= concurso) or str(alvo) == "Legado"
        if pode and j.get("matriz_origem"): matriz_usada = j["matriz_origem"]
                
        if j.get('status') == "Aguardando Sorteio" and pode:
            jogos_processados += 1
            ledger["bilhetes"] += 1
            pontos = len(set(j.get('dezenas', [])).intersection(sorteio_set))
            j['acertos'], j['premio_valor'] = pontos, calcular_premio_multiplo_mega(pontos, v4, v5, v6)
            max_pts = max(max_pts, pontos)
            
            if pontos >= 4:
                j['status'] = "Premiado"
                lucro_total += j['premio_valor']
                st.session_state.data_mega["historico_premios"] += j['premio_valor']
                premiados += 1
                ledger["premiados_geral"] += 1
                if pontos >= 5: ledger["elite"] += 1
                hits_bilhetes[pontos] = hits_bilhetes.get(pontos, 0) + 1
            else: j['status'] = "Não Premiado"

    m_hits = st.session_state.data_mega["matrizes_reais_hits"]
    m_ids = st.session_state.data_mega["matrizes_auditadas_ids"]
    selo = f"conc_{concurso}"
    
    if matriz_usada and selo not in m_ids:
        acertos_matriz = len(set(matriz_usada).intersection(sorteio_set))
        m_ids.append(selo)
        m_hits["total"] = m_hits.get("total", 0) + 1
        m_hits["soma_acertos"] = m_hits.get("soma_acertos", 0) + acertos_matriz
        
        est_da_matriz = next((j.get("estrategia", "Default") for j in st.session_state.data_mega.get("jogos_salvos", []) if j.get("matriz_origem") == matriz_usada), "Default")
        ajustar_ia_mega(est_da_matriz, acertos_matriz)
        if acertos_matriz >= 4: m_hits[int(min(acertos_matriz, 6))] = m_hits.get(int(min(acertos_matriz, 6)), 0) + 1
            
    st.session_state.data_mega["matrizes_reais_hits"] = m_hits
    st.session_state.data_mega["matrizes_auditadas_ids"] = m_ids
    st.session_state.data_mega["global_hits"] = hits_bilhetes
    st.session_state.data_mega["ledger_track"] = ledger
    
    if jogos_processados > 0: relatorio.append(f"Auditoria Mega {concurso}: {premiados}/{jogos_processados} bilhetes premiados.")
    return lucro_total, relatorio

def raciocinio_total_ia_mega(historico, memoria):
    if not historico: return None
    atrasos, dez_enc = {n: 0 for n in range(1, 61)}, {n: False for n in range(1, 61)}
    
    for h in reversed(historico):
        for n in range(1, 61):
            if n in h['dezenas']: dez_enc[n] = True
            elif not dez_enc[n]: atrasos[n] += 1

    ultimo_sorteio = [int(x) for x in historico[-1]['dezenas']]
    reps = len(set(ultimo_sorteio) & set(historico[-2]['dezenas'])) if len(historico) > 1 else 0
    
    if reps >= 2: cod_est, qtd_matriz, tatic_desc = "Dispersão Ortogonal", 12, "Quebra de Repetição."
    elif sum(atrasos.values()) / 60 > 15.0: cod_est, qtd_matriz, tatic_desc = "Caos Térmico", 14, "Caça a Dezenas Adormecidas."
    else: cod_est, qtd_matriz, tatic_desc = "Arbitragem de Massa", 13, "Fuga do Padrão Humano."

    unified_scores = {}
    for n in range(1, 61):
        delay, score_calc = atrasos.get(n, 0), 0.0
        if 5 <= delay <= 25: score_calc += 30.0
        elif delay > 25: score_calc += 15.0 
        else: score_calc += 5.0 
        if n > 31: score_calc += 20.0
        if n % 10 in [9, 0]: score_calc += 15.0
        unified_scores[n] = float(score_calc)

    Q1 = set(range(1, 6)) | set(range(11, 16)) | set(range(21, 26))
    Q2 = set(range(6, 11)) | set(range(16, 21)) | set(range(26, 31))
    Q3 = set(range(31, 36)) | set(range(41, 46)) | set(range(51, 56))
    Q4 = set(range(36, 41)) | set(range(46, 51)) | set(range(56, 61))
    
    max_por_quad = round(qtd_matriz * 0.35) + 1 
    matriz_final = []
    candidatos = sorted(range(1, 61), key=lambda x: unified_scores.get(x, 0), reverse=True)
    
    for n in candidatos:
        if len(matriz_final) >= qtd_matriz: break
        if n in Q1 and sum(1 for x in matriz_final if x in Q1) >= max_por_quad: continue
        if n in Q2 and sum(1 for x in matriz_final if x in Q2) >= max_por_quad: continue
        if n in Q3 and sum(1 for x in matriz_final if x in Q3) >= max_por_quad: continue
        if n in Q4 and sum(1 for x in matriz_final if x in Q4) >= max_por_quad: continue
        matriz_final.append(n)
        
    matriz_final = sorted(matriz_final)
    justificativa = f"DIRETRIZ: {tatic_desc} | ESPAÇAMENTO: Q1({sum(1 for x in matriz_final if x in Q1)}) Q2({sum(1 for x in matriz_final if x in Q2)}) Q3({sum(1 for x in matriz_final if x in Q3)}) Q4({sum(1 for x in matriz_final if x in Q4)})"
    
    return {
        "estrategia": str(cod_est), "cod_estrategia": str(cod_est), "motivo_est": justificativa, "atrasos": dict(atrasos),
        "pesos": {n: round(float(unified_scores.get(n, 0.0)), 2) for n in range(1, 61)},
        "alvo": int((historico[-1]['concurso'] + 1)) if historico else 1, "qtd_matriz": int(qtd_matriz), "matriz_base": matriz_final
    }

def exibir_card_volante_mega(jogo, numero_jogo, sorteio_real=None):
    dezenas, alvo, estrategia = jogo.get('dezenas', []), jogo.get('concurso_alvo', 'N/A'), jogo.get('estrategia', 'Padrão Mega')
    match = re.search(r'Garantia de (\d+)', str(jogo.get('justificativa', '')))
    texto_rodape = f"Fechamento Matemático - Garantia de {match.group(1)} Pontos" if match else "Fechamento Mega-Sena"
    sorteio_set = set(sorteio_real) if sorteio_real else set()

    grid_html = "<div style='display: grid; grid-template-columns: repeat(10, 1fr); gap: 4px; margin-bottom: 12px; justify-items: center;'>"
    for num in range(1, 61):
        if num in dezenas: bg_color, txt_color, border, shadow = ("#28a745", "white", "none", "box-shadow: 0 0 5px #28a745;") if num in sorteio_set else ("#209869", "white", "none", "box-shadow: 0 2px 4px rgba(32,152,105,0.3);")
        else: bg_color, txt_color, border, shadow = "#f4f6f9", "#ccc", "1px solid #eee", ""
        grid_html += f"<div style='background-color: {bg_color}; color: {txt_color}; border: {border}; {shadow} text-align: center; border-radius: 50%; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold;'>{num:02d}</div>"
    grid_html += "</div>"
    
    html_card = f"<div style='background-color: #ffffff; border: 1px solid #e0e0e0; padding: 15px; border-radius: 8px; margin-bottom: 15px; box-shadow: 2px 2px 8px rgba(0,0,0,0.05);'><div style='display: flex; justify-content: space-between; border-bottom: 1px solid #eee; padding-bottom: 8px; margin-bottom: 12px;'><span style='font-size: 15px; font-weight: bold; color: #209869;'>🎫 JOGO {numero_jogo:02d}</span><span style='font-size: 12px; font-weight: bold; color: #666;'>Alvo: {alvo}</span></div><div style='font-size: 11px; color: #555; margin-bottom: 12px; font-weight: bold; text-transform: uppercase;'>ESTRATÉGIA: {estrategia}</div>{grid_html}<div style='text-align: center; font-size: 10px; font-weight: bold; color: #209869; background: rgba(32, 152, 105, 0.08); padding: 6px; border-radius: 4px; margin-top: 5px;'>{texto_rodape}</div></div>"
    st.markdown(html_card, unsafe_allow_html=True)

def gerar_pdf_jogos_mega(jogos, dezenas_anteriores=None):
    if dezenas_anteriores is None: dezenas_anteriores = []
    def limpar_latin1(t): return str(t).replace("🧬", "").replace("🍀", "").replace("🎫", "").replace("⚠️", "").encode('latin-1', 'ignore').decode('latin-1')
    pdf = FPDF()
    pdf.set_auto_page_break(auto=False)
    margem_x, margem_y, largura_card, altura_card, espaco_x, espaco_y = 10, 35, 90, 80, 5, 5
    sorteio_set = set(dezenas_anteriores)

    for i, j in enumerate(jogos):
        if i % 6 == 0:
            pdf.add_page()
            pdf.set_text_color(32, 152, 105)
            pdf.set_font('Arial', 'B', 16)
            pdf.set_xy(10, 12)
            pdf.cell(0, 10, "Loterias PRO - Relatorio Mega-Sena", ln=0)
            pdf.set_font('Arial', '', 9)
            pdf.set_text_color(100, 100, 100)
            pdf.set_xy(10, 20)
            pdf.cell(0, 8, f"TOTAL: {len(jogos)} BILHETES  |  Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=0)
            pdf.line(10, 28, 200, 28)

        coluna, linha = (i % 6) % 2, (i % 6) // 2
        x_start, y_start = margem_x + (coluna * (largura_card + espaco_x)), margem_y + (linha * (altura_card + espaco_y))
        estrategia, dezenas, alvo = limpar_latin1(str(j.get('estrategia', 'Mega Padrão'))), j.get('dezenas', []), limpar_latin1(str(j.get('concurso_alvo', 'N/A')))
        
        pdf.set_fill_color(242, 251, 246) 
        pdf.rect(x_start, y_start, largura_card, altura_card, 'F')
        pdf.set_fill_color(32, 152, 105) 
        pdf.rect(x_start, y_start, 2, altura_card, 'F')

        pdf.set_text_color(40, 40, 40)
        pdf.set_font('Arial', 'B', 10)
        pdf.set_xy(x_start + 5, y_start + 4)
        pdf.cell(50, 6, f"JOGO {(i+1):02d}", ln=0)
        pdf.set_font('Arial', '', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.set_xy(x_start + 40, y_start + 4)
        pdf.cell(45, 6, f"Alvo: {alvo}", ln=0, align='R')
        pdf.set_text_color(32, 152, 105) 
        pdf.set_font('Arial', 'B', 7)
        pdf.set_xy(x_start + 5, y_start + 9)
        pdf.cell(80, 5, f"{estrategia[:35]}", ln=0)

        bolinha_x_start, bolinha_y_start, passo_x, passo_y = x_start + 8, y_start + 18, 8, 8 
        for num in range(1, 61):
            lin, col = (num - 1) // 10, (num - 1) % 10
            cx, cy = bolinha_x_start + (col * passo_x), bolinha_y_start + (lin * passo_y)
            if num in dezenas:
                if num in sorteio_set: pdf.set_fill_color(40, 167, 69)
                else: pdf.set_fill_color(32, 152, 105)
                pdf.set_text_color(255, 255, 255)
            else:
                pdf.set_fill_color(235, 235, 235)
                pdf.set_text_color(160, 160, 160)
            pdf.ellipse(cx, cy, 5.5, 5.5, 'F')
            pdf.set_xy(cx, cy)
            pdf.set_font('Arial', 'B', 5)
            pdf.cell(5.5, 5.5, f"{num:02d}", align='C')

        pdf.set_text_color(120, 120, 120)
        pdf.set_font('Arial', 'B', 7)
        pdf.set_xy(x_start + 5, y_start + altura_card - 8)
        pdf.cell(80, 5, "Fechamento Mega-Sena Institucional", ln=0, align='C')

    resultado = pdf.output(dest='S')
    if isinstance(resultado, str): return resultado.encode('latin-1', 'ignore')
    return bytes(resultado)


# =====================================================================
# 5. CONSTRUÇÃO DAS TELAS (PÁGINAS DO SISTEMA)
# =====================================================================
def tela_login():
    exibir_cabecalho()
    st.markdown("<h4 style='text-align: center;'>Acesso Restrito ao Sistema</h4>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("form_login"):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Autenticar Operador", use_container_width=True):
                if usuario == "777" and senha == "777": 
                    st.session_state.autenticado = True
                    st.session_state.pagina_atual = "lobby"
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")
    exibir_rodape()

def tela_lobby():
    exibir_cabecalho()
    
    # CSS avançado para tornar os botões do Streamlit perfeitamente quadrados, centralizados e responsivos.
    st.markdown("""
    <style>
        /* Container centralizado para alinhar dinamicamente as colunas */
        .block-container { max-width: 1000px; }
        
        /* Modifica o botão nativo para ser quadrado e bonito */
        div[data-testid="stColumn"] div.stButton > button {
            aspect-ratio: 1 / 1 !important; /* FORÇA O FORMATO QUADRADO */
            border-radius: 20px !important;
            font-size: 24px !important;
            font-weight: 900 !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.08) !important;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
            padding: 20px !important;
            line-height: 1.4 !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            align-items: center !important;
            white-space: pre-wrap !important; /* Permite quebra de linha no texto */
        }
        
        /* Botão 1: Lotofácil (Roxo) */
        div[data-testid="stColumn"]:nth-child(2) div.stButton > button {
            background: linear-gradient(145deg, #ffffff, #fdf5ff) !important;
            border: 3px solid #930089 !important;
            color: #930089 !important;
        }
        div[data-testid="stColumn"]:nth-child(2) div.stButton > button:hover {
            background: #930089 !important;
            color: white !important;
            transform: translateY(-8px) scale(1.02) !important;
            box-shadow: 0 15px 35px rgba(147,0,137,0.3) !important;
        }

        /* Botão 2: Mega-Sena (Verde) */
        div[data-testid="stColumn"]:nth-child(3) div.stButton > button {
            background: linear-gradient(145deg, #ffffff, #f2fbf6) !important;
            border: 3px solid #209869 !important;
            color: #209869 !important;
        }
        div[data-testid="stColumn"]:nth-child(3) div.stButton > button:hover {
            background: #209869 !important;
            color: white !important;
            transform: translateY(-8px) scale(1.02) !important;
            box-shadow: 0 15px 35px rgba(32,152,105,0.3) !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h4 style='text-align: center; color: #666; font-weight: normal; margin-bottom: 50px;'>Escolha o Motor Analítico para iniciar a sessão:</h4>", unsafe_allow_html=True)
    
    # Truque de Layout: Usar 4 colunas, mas colocar os botões apenas nas colunas do meio.
    # Se quiseres adicionar mais, mudas as proporções. Assim fica perfeitamente centrado.
    cols = st.columns([1, 2, 2, 1]) 
    
    with cols[1]:
        if st.button("🍀\nLotofácil\nIA de Frequência", key="btn_loto", use_container_width=True):
            st.session_state.pagina_atual = "lotofacil"
            st.rerun()
            
    with cols[2]:
        if st.button("🍀\nMega-Sena\nIA Espacial", key="btn_mega", use_container_width=True):
            st.session_state.pagina_atual = "megasena"
            st.rerun()
            
    exibir_rodape()

def tela_lotofacil():
    exibir_cabecalho(loteria_especifica="LOTOFÁCIL PRO", cor_loteria="#930089", icone_loteria="🍀")
    st.markdown("""<style>:root { --roxo: #930089; --roxo-hover: #7a0072; } .stApp { background-color: #f4f6f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; } .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: #ffffff; padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); } .stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 10px 20px; background-color: #f8f9fa; border: 1px solid #e9ecef; transition: all 0.3s ease; } .stTabs [aria-selected="true"] { background-color: var(--roxo) !important; color: white !important; border: none; box-shadow: 0 4px 10px rgba(147,0,137,0.3); } div[data-testid="stMetric"] { background-color: white; padding: 20px; border-radius: 12px; border-left: 6px solid var(--roxo); box-shadow: 0 4px 6px rgba(0,0,0,0.04); } div[data-testid="stAlert"] { background-color: #fdf5ff !important; border-left: 5px solid var(--roxo) !important; color: #333 !important; border-radius: 8px !important; } button[kind="primary"] { background-color: var(--roxo) !important; border: none !important; border-radius: 8px !important; font-weight: bold !important; color: white !important; box-shadow: 0 4px 10px rgba(147,0,137,0.4) !important; transition: all 0.3s ease !important; } button[kind="primary"]:hover { background-color: var(--roxo-hover) !important; transform: translateY(-2px); }</style>""", unsafe_allow_html=True)
    if "data" not in st.session_state: st.session_state.data = sanitizar_dados({})
    if 'auth' not in st.session_state: st.session_state.auth = False
    tabs = st.tabs(["📂 1. Banco de Dados", "🧠 2. Cérebro Analítico (IA)", "🤖 3. Geração Autônoma", "📜 4. Fila de Sorteio", "🏆 5. Sincronização e Entrada"])

    with tabs[0]:
        st.markdown("### 💾 Central de Dados e Livro-Caixa da Operação")
        t_custos, t_premios = st.session_state.data["historico_custos"], st.session_state.data["historico_premios"]
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
                valor_mov = st.number_input("Digite o Valor (R$):", min_value=0.0, step=10.0, key="input_movimentacao")
                col_dep, col_sac = st.columns(2)
                with col_dep:
                    if st.button("➕ Adicionar Gasto Extra", use_container_width=True) and valor_mov > 0:
                        st.session_state.data["historico_custos"] += valor_mov
                        salvar_dados(st.session_state.data)
                        st.rerun()
                with col_sac:
                    if st.button("✅ Adicionar Prêmio Extra", use_container_width=True) and valor_mov > 0:
                        st.session_state.data["historico_premios"] += valor_mov
                        salvar_dados(st.session_state.data)
                        st.rerun()
                st.divider()
                if st.button("🔄 ZERAR CONTABILIDADE E ROI (MANTER IA)", use_container_width=True, type="secondary"):
                    st.session_state.data["historico_custos"] = st.session_state.data["historico_premios"] = 0.0
                    st.session_state.data["ledger_track"] = {"bilhetes": 0, "premiados_geral": 0, "elite": 0, "custo": 0.0, "retorno": 0.0}
                    salvar_dados(st.session_state.data)
                    st.rerun()

    with tabs[1]:
        exibir_mini_painel_financeiro()
        st.markdown("### 🧠 Diagnóstico da Inteligência Artificial")
        track = st.session_state.data.get("ledger_track", {"bilhetes": 0, "premiados_geral": 0, "elite": 0})
        custo_real, retorno_real = st.session_state.data.get("historico_custos", 0.0), st.session_state.data.get("historico_premios", 0.0)
        win_rate = (track['premiados_geral'] / track['bilhetes'] * 100) if track.get('bilhetes', 0) > 0 else 0.0
        roi_val, roi_pct = retorno_real - custo_real, ((retorno_real - custo_real) / custo_real * 100) if custo_real > 0 else 0.0

        with st.container(border=True):
            st.markdown("#### 📈 Track Record: A Máquina em Ação (Dados Reais)")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("🎟️ Bilhetes Operados", track.get('bilhetes', 0))
            c2.metric("🎯 Win Rate (Prêmios)", f"{win_rate:.1f}%")
            elite_rate = (track.get('elite', 0) / track.get('premiados_geral', 1) * 100) if track.get('premiados_geral', 0) > 0 else 0.0
            c3.metric("💎 Freq. de Elite (14/15 nos Bilhetes)", f"{elite_rate:.1f}%" if elite_rate > 0 else "0.0%")
            c4.metric("📈 ROI Financeiro", f"{roi_pct:.1f}%", f"R$ {roi_val:.2f}")

        st.markdown("### 🏆 Performance Oficial (Pós-Auditoria Vida Real)")
        hits_matriz = st.session_state.data.get("matrizes_reais_hits", {})
        tm_total = hits_matriz.get("total", 0)
        media_acertos_matriz = hits_matriz.get("soma_acertos", 0) / tm_total if tm_total > 0 else 0.0

        with st.container(border=True):
            st.markdown("#### 🎯 Força da Matriz da IA")
            st.metric("Média de Acertos da Matriz", f"{media_acertos_matriz:.2f} / 15")
            cm1, cm2, cm3, cm4, cm5 = st.columns(5)
            cm1.metric("Matriz Acertou 11", hits_matriz.get(11, hits_matriz.get("11", 0)))
            cm2.metric("Matriz Acertou 12", hits_matriz.get(12, hits_matriz.get("12", 0)))
            cm3.metric("Matriz Acertou 13", hits_matriz.get(13, hits_matriz.get("13", 0)))
            cm4.metric("Matriz Acertou 14", hits_matriz.get(14, hits_matriz.get("14", 0)))
            cm5.metric("Matriz Acertou 15", hits_matriz.get(15, hits_matriz.get("15", 0)))

        hits_bilhetes = st.session_state.data.get("global_hits", {})
        with st.container(border=True):
            st.markdown("#### 🎫 Prêmios Retidos nos Bilhetes")
            cb1, cb2, cb3, cb4, cb5 = st.columns(5)
            cb1.metric("Bilhetes com 11", hits_bilhetes.get(11, hits_bilhetes.get("11", 0)))
            cb2.metric("Bilhetes com 12", hits_bilhetes.get(12, hits_bilhetes.get("12", 0)))
            cb3.metric("Bilhetes com 13", hits_bilhetes.get(13, hits_bilhetes.get("13", 0)))
            cb4.metric("Bilhetes com 14", hits_bilhetes.get(14, hits_bilhetes.get("14", 0)))
            cb5.metric("Bilhetes com 15", hits_bilhetes.get(15, hits_bilhetes.get("15", 0)))

        st.markdown("#### 🧬 Raio-X da Evolução Neural (Pesos Dinâmicos)")
        pesos_ia = st.session_state.data.get("ia_pesos", {})
        if pesos_ia:
            cols_pesos = st.columns(len(pesos_ia))
            for idx, (nome_est, parametros) in enumerate(pesos_ia.items()):
                with cols_pesos[idx]:
                    html_card = f"<div style='background-color: white; padding: 15px; border-radius: 10px; border-top: 5px solid #930089; box-shadow: 0px 4px 10px rgba(0,0,0,0.06); height: 100%;'><div style='font-size: 14px; font-weight: 900; color: #333; text-align: center; margin-bottom: 5px;'>{nome_est.upper()}</div><hr style='margin: 10px 0; border: none; border-top: 1px solid #f0f0f0;'>"
                    for chave, valor in parametros.items(): html_card += f"<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;'><span style='font-size: 12px; color: #777; font-weight: 700;'>{chave.upper()}</span><span style='font-size: 15px; font-weight: 900; color: #930089;'>{valor:.2f}</span></div>"
                    html_card += "</div>"
                    st.markdown(html_card, unsafe_allow_html=True)
                
        historico_painel = st.session_state.data.get("historico_dados", [])
        if historico_painel:
            ia = raciocinio_total_ia(historico_painel, st.session_state.data.get("ia_memoria", {}))
            if ia:
                tamanho_m = ia['qtd_matriz']
                st.markdown(f"### 🎯 Matriz Cirúrgica Atual — {tamanho_m} Dezenas")
                with st.container(border=True):
                    garantia_alvo = st.radio("Alvo do Fechamento:", options=[15, 14, 13], format_func=lambda x: f"Garantia Absoluta de {x} Pontos", horizontal=True, key="radio_garantia_aba2")
                    jogos_exatos, custo_exato = obter_dados_fechamento(ia['matriz_base'], garantia_alvo)
                    st.success(f"**Diagnóstico Matemático:** Para garantir **{garantia_alvo} pontos**, o sistema vai desdobrar **{jogos_exatos} bilhetes**.\n💸 **Custo Fixo Total: R$ {custo_exato:.2f}**")

                st.markdown(f"#### 🧠 Diagnóstico Autônomo — Concurso Alvo {ia['alvo']}")
                st.info(f"⚡ **LINHA TÁTICA ATIVADA:** {ia['estrategia']}\n\n**DIRETRIZ DA DECISÃO:** {ia['motivo_est']}\n\n🎯 **GRUPO DE ELITE:** " + ", ".join([f"{n:02d}" for n in ia['matriz_base']]))

                pesos_ordenados = sorted(ia['pesos'].items(), key=lambda x: x[0])
                cols = st.columns(5)
                for idx, (dez, peso) in enumerate(pesos_ordenados):
                    with cols[idx % 5]:
                        is_elite = dez in ia['matriz_base']
                        bg_color, txt_color, border = ("#930089", "white", "none") if is_elite else ("#f4f6f9", "#333", "1px solid #ddd")
                        st.markdown(f"<div style='background-color: {bg_color}; color: {txt_color}; padding: 10px; border-radius: 8px; border: {border}; text-align: center; margin-bottom: 10px;'><div style='font-size: 20px; font-weight: 900;'>{dez:02d}</div><div style='font-size: 11px; opacity: 0.9;'>Peso: {peso:.1f}</div>{f'<div style=\"font-size: 10px; font-weight: bold; margin-top: 5px; background: rgba(0,0,0,0.2); border-radius: 4px;\">ELITE</div>' if is_elite else ''}</div>", unsafe_allow_html=True)
        else: st.warning("⚠️ Carregue o Cofre.json na Aba 1 para ativar a Inteligência Artificial.")

    with tabs[2]:
        exibir_mini_painel_financeiro()
        st.markdown("### 🚀 Engenharia Combinatória (100% Exato)")
        if st.session_state.data["historico_dados"]:
            ia = raciocinio_total_ia(st.session_state.data["historico_dados"], st.session_state.data.get("ia_memoria", {}))
            with st.container(border=True):
                st.markdown("#### 🎯 Alvo da Garantia Matemática")
                garantia_alvo = st.radio("Garantia:", options=[15, 14, 13], format_func=lambda x: f"Garantia Absoluta de {x} Pontos", horizontal=True, key="radio_garantia_aba3")
                jogos_exatos, custo_exato = obter_dados_fechamento(ia['matriz_base'], garantia_alvo)
                st.info(f"📊 **Volume Exato:** {jogos_exatos} Bilhetes\n\n💸 **Investimento Cravado:** R$ {custo_exato:.2f}")
                if st.button("🧬 GERAR FECHAMENTO EXATO", type="primary", use_container_width=True):
                    st.session_state.data["jogos_salvos"] = [j for j in st.session_state.data["jogos_salvos"] if j.get('status') != "Aguardando Sorteio"]
                    matriz_reduzida = gerar_fechamento_matematico(tuple(ia['matriz_base']), garantia_alvo)
                    prog_a = st.progress(0)
                    for i, dezenas_jogo in enumerate(matriz_reduzida):
                        st.session_state.data["jogos_salvos"].append({"id": str(uuid.uuid4()), "concurso_alvo": ia['alvo'], "dezenas": sorted(list(dezenas_jogo)), "tamanho": len(dezenas_jogo), "estrategia": ia['cod_estrategia'], "justificativa": f"Matriz {ia['cod_estrategia']}. Garantia 100% de {garantia_alvo} pts.", "status": "Aguardando Sorteio", "acertos": 0, "premio_valor": 0.0, "matriz_origem": ia['matriz_base']})
                        if i % max(1, (len(matriz_reduzida) // 10)) == 0: prog_a.progress(min((i+1)/len(matriz_reduzida), 1.0))
                    st.session_state.data['historico_custos'] += len(matriz_reduzida) * 3.50
                    salvar_dados(st.session_state.data)
                    st.success(f"**🥇 FECHAMENTO CONCLUÍDO!** {len(matriz_reduzida)} bilhetes gerados exatos.")
                    st.rerun()

        jogos_espera = [j for j in st.session_state.data.get("jogos_salvos", []) if j.get('status') == "Aguardando Sorteio"]
        if jogos_espera:
            st.markdown("#### 👀 Pré-visualização dos Bilhetes Gerados")
            bilhetes_por_pagina = 30
            total_paginas = (len(jogos_espera) // bilhetes_por_pagina) + (1 if len(jogos_espera) % bilhetes_por_pagina > 0 else 0)
            pagina_atual = st.selectbox("Página (Aba 3)", range(1, total_paginas + 1), label_visibility="collapsed", key="pag_aba3") if total_paginas > 1 else 1
            inicio, fim = (pagina_atual - 1) * bilhetes_por_pagina, ((pagina_atual - 1) * bilhetes_por_pagina) + bilhetes_por_pagina
            cols = st.columns(3)
            for idx, jogo in enumerate(jogos_espera[inicio:fim]):
                with cols[idx % 3]: exibir_card_volante(jogo, inicio + idx + 1)

    with tabs[3]:
        exibir_mini_painel_financeiro()
        jogos_em_espera = [j for j in st.session_state.data["jogos_salvos"] if j.get('status') == "Aguardando Sorteio"]
        total_premio = sum(j.get("premio_valor", 0) for j in st.session_state.data["jogos_salvos"] if j.get('status') == "Premiado")
        c1, c2, c3 = st.columns(3)
        c1.metric("🎫 Jogos em Espera", len(jogos_em_espera))
        c2.metric("💰 Premiação Acumulada", f"R$ {total_premio:.2f}")
        c3.metric("📊 Bilhetes Auditados", len([j for j in st.session_state.data["jogos_salvos"] if j.get('status') != "Aguardando Sorteio"]))
        st.markdown("---")
        if st.session_state.data.get("jogos_salvos") and st.session_state.data.get("historico_dados"):
            ultimo_jogo_criado = st.session_state.data["jogos_salvos"][-1]
            alvo_foco = ultimo_jogo_criado.get("concurso_alvo")
            if ultimo_jogo_criado.get("matriz_origem"):
                st.write(f"**Matriz de {len(ultimo_jogo_criado['matriz_origem'])} dezenas usada para o Concurso {alvo_foco}:**")
                st.code(", ".join([f"{n:02d}" for n in sorted(list(ultimo_jogo_criado['matriz_origem']))]))
        
        if st.session_state.data["jogos_salvos"]:
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1: st.button("🗑️ LIMPAR TODOS", on_click=cb_excluir_todos, type="secondary", use_container_width=True)
            with col_btn2:
                ultimas_dezenas = st.session_state.caixa_latest['dezenas'] if 'caixa_latest' in st.session_state and 'dezenas' in st.session_state.caixa_latest else []
                pdf_bytes = gerar_pdf_jogos(st.session_state.data["jogos_salvos"], ultimas_dezenas)
                st.download_button("📤 EXPORTAR RELATÓRIO (PDF)", data=pdf_bytes, file_name="Relatorio_LotoMatrix.pdf", mime="application/pdf", type="primary", use_container_width=True)

        jogos = st.session_state.data.get("jogos_salvos", [])
        if jogos:
            bilhetes_por_pagina, total_paginas = 30, (len(jogos) // 30) + (1 if len(jogos) % 30 > 0 else 0)
            pagina_atual = st.selectbox("Navegação de Páginas", range(1, total_paginas + 1), label_visibility="collapsed", key="pag_aba4") if total_paginas > 1 else 1
            inicio, fim = (pagina_atual - 1) * bilhetes_por_pagina, ((pagina_atual - 1) * bilhetes_por_pagina) + bilhetes_por_pagina
            cols = st.columns(3)
            for idx, j in enumerate(jogos[inicio:fim]):
                with cols[idx % 3]:
                    exibir_card_volante(j, inicio + idx + 1)
                    if j.get('status') == "Premiado": st.success(f"✅ PREMIADO ({j.get('acertos', 0)} pts)\n💰 R$ {j.get('premio_valor', 0):.2f}")
                    elif j.get('status') == "Não Premiado": st.error(f"❌ NÃO PREMIADO ({j.get('acertos', 0)} pts)")
                    else: st.info("⏳ AGUARDANDO")
                    st.button("🗑️ Apagar", key=f"del_{j.get('id', uuid.uuid4())}", on_click=cb_excluir_jogo, args=(j.get('id'),), use_container_width=True)
        else: st.info("Nenhum bilhete registrado na fila.")

    with tabs[4]:
        exibir_mini_painel_financeiro()
        with st.container(border=True):
            col_massa1, col_massa2 = st.columns(2)
            with col_massa1:
                if st.button("🛸 BUSCAR FALTANTES E AUDITAR (GAP)", type="primary", use_container_width=True):
                    historico = st.session_state.data.get("historico_dados", [])
                    if historico:
                        try:
                            res_latest = requests.get("https://loteriascaixa-api.herokuapp.com/api/lotofacil/latest", verify=False, timeout=10).json()
                            ultimo_salvo, ultimo_oficial = int(historico[-1]["concurso"]), int(res_latest['concurso'])
                            if ultimo_salvo >= ultimo_oficial: st.info("O sistema já está atualizado.")
                            else:
                                barra, lucro_acumulado_massa, logs_massa = st.progress(0), 0.0, []
                                for i, num in enumerate(list(range(ultimo_salvo + 1, ultimo_oficial + 1))):
                                    res_conc = requests.get(f"https://loteriascaixa-api.herokuapp.com/api/lotofacil/{num}", verify=False, timeout=10).json()
                                    if 'concurso' in res_conc:
                                        dezenas_sorteadas = sorted([int(d) for d in res_conc['dezenas']])
                                        st.session_state.data["historico_dados"].append({"concurso": num, "dezenas": dezenas_sorteadas, "data": res_conc.get('data', '')})
                                        lucro_parcial, relatorio_parcial = auditar_e_aprender_unificado(num, dezenas_sorteadas, extrair_rateios_api(res_conc.get('premiacoes', [])))
                                        lucro_acumulado_massa += lucro_parcial
                                        logs_massa.extend(relatorio_parcial)
                                    barra.progress((i + 1) / (ultimo_oficial - ultimo_salvo))
                                st.session_state.ultimo_aprendizado = list(set(logs_massa))
                                salvar_dados(st.session_state.data)
                                st.success(f"✅ GAPs processados com sucesso! R$ {lucro_acumulado_massa:.2f} creditados.")
                                st.rerun()
                        except Exception as e: st.error(f"Erro: {e}")
            with col_massa2:
                if st.button("📥 1. BAIXAR SORTEIOS (DO 1 AO ATUAL)", type="secondary", use_container_width=True):
                    with st.spinner("Baixando base de dados da Caixa..."):
                        try:
                            res_todos = sorted(requests.get("https://loteriascaixa-api.herokuapp.com/api/lotofacil", verify=False, timeout=60).json(), key=lambda k: int(k['concurso']))
                            st.session_state.data["historico_dados"] = [{"concurso": int(r['concurso']), "dezenas": sorted([int(d) for d in r['dezenas']]), "data": r.get('data', '')} for r in res_todos]
                            salvar_dados(st.session_state.data)
                            st.success(f"✅ Download de {len(res_todos)} sorteios concluído.")
                        except Exception as e: st.error(f"Erro na conexão com API: {e}")

        col_sync1, col_sync2 = st.columns(2)
        with col_sync1:
            with st.container(border=True):
                st.markdown("#### 🌐 Sincronização Automática (API Caixa)")
                if st.button("🔄 Buscar Último Resultado Oficial", type="primary", use_container_width=True):
                    with st.spinner("Conectando à API da Caixa..."):
                        try:
                            resp = requests.get("https://loteriascaixa-api.herokuapp.com/api/lotofacil/latest", verify=False, timeout=15)
                            if resp.status_code == 200:
                                res = resp.json()
                                num_c, dez_o = int(res['concurso']), [int(x) for x in res['dezenas']]
                                novo_dado = {"concurso": num_c, "data": res['data'], "dezenas": dez_o, "premiacoes": res.get('premiacoes', [])}
                                if not any(h['concurso'] == num_c for h in st.session_state.data["historico_dados"]): st.session_state.data["historico_dados"].append(novo_dado)
                                st.session_state.caixa_latest = novo_dado
                                lucro_total, rel = auditar_e_aprender_unificado(num_c, dez_o, extrair_rateios_api(res.get('premiacoes', [])))
                                if rel: st.session_state.ultimo_aprendizado = list(set(rel))
                                salvar_dados(st.session_state.data)
                                st.success(f"✅ Sincronização Automática Concluída! Prêmios Auditados: R$ {lucro_total:.2f}")
                                st.rerun()
                        except Exception as e: st.error(f"Falha de conexão com a API: {e}")
        with col_sync2:
            with st.container(border=True):
                st.markdown("#### 🛠️ Inserção e Conferência Manual")
                concurso_manual = st.number_input("Número do Concurso:", min_value=1, step=1, key="num_conc_manual")
                dezenas_texto = st.text_input("Cole as 15 Dezenas Sorteadas:", key="dez_manual_input")
                if st.button("✅ Confirmar e Auditar Manualmente", use_container_width=True):
                    try:
                        dezenas_oficiais = sorted([int(n) for n in re.findall(r'\d+', dezenas_texto)])
                        if len(dezenas_oficiais) != 15: st.error(f"Insira exatamente 15. Identificados: {len(dezenas_oficiais)}.")
                        else:
                            lucro_total, rel = auditar_e_aprender_unificado(concurso_manual, dezenas_oficiais, rateios=None)
                            if not any(h['concurso'] == concurso_manual for h in st.session_state.data["historico_dados"]):
                                st.session_state.data["historico_dados"].append({"concurso": concurso_manual, "data": datetime.now().strftime("%d/%m/%Y"), "dezenas": dezenas_oficiais, "premiacoes": []})
                            if rel: st.session_state.ultimo_aprendizado = list(set(rel))
                            salvar_dados(st.session_state.data)
                            st.success(f"✅ Operação Manual Concluída. Prêmios auditados no ROI: R$ {lucro_total:.2f}.")
                            st.rerun()
                    except ValueError: st.error("Erro na conversão.")

        with st.container(border=True):
            st.markdown("#### 🧠 Forçar Reprocessamento da Inteligência Artificial")
            if st.button("🔄 ATUALIZAR E FORÇAR LEITURA PARA O PRÓXIMO SORTEIO", type="primary", use_container_width=True):
                st.session_state.data["ia_memoria"] = {}
                if 'ultimo_aprendizado' in st.session_state: st.session_state.ultimo_aprendizado = []
                salvar_dados(st.session_state.data)
                st.success("✅ Memória Cache zerada! A IA recalculará a matriz no próximo acesso.")
                st.rerun()            

        if 'caixa_latest' in st.session_state:
            r = st.session_state.caixa_latest
            st.markdown(f"#### 🏛️ Último Extrato Salvo da Caixa: Concurso {r['concurso']}")
            if r.get('premiacoes'): st.table(pd.DataFrame(r['premiacoes']))
    exibir_rodape()

def tela_megasena():
    exibir_cabecalho(loteria_especifica="MEGA-SENA PRO", cor_loteria="#209869", icone_loteria="🍀")
    st.markdown("""<style>:root { --verde: #209869; --verde-hover: #16704d; } .stApp { background-color: #f4f6f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; } .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: #ffffff; padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); } .stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 10px 20px; background-color: #f8f9fa; border: 1px solid #e9ecef; transition: all 0.3s ease; } .stTabs [aria-selected="true"] { background-color: var(--verde) !important; color: white !important; border: none; box-shadow: 0 4px 10px rgba(32,152,105,0.3); } div[data-testid="stMetric"] { background-color: white; padding: 20px; border-radius: 12px; border-left: 6px solid var(--verde); box-shadow: 0 4px 6px rgba(0,0,0,0.04); } div[data-testid="stAlert"] { background-color: #f2fbf6 !important; border-left: 5px solid var(--verde) !important; color: #333 !important; border-radius: 8px !important; } button[kind="primary"] { background-color: var(--verde) !important; border: none !important; border-radius: 8px !important; font-weight: bold !important; color: white !important; box-shadow: 0 4px 10px rgba(32,152,105,0.4) !important; transition: all 0.3s ease !important; } button[kind="primary"]:hover { background-color: var(--verde-hover) !important; transform: translateY(-2px); }</style>""", unsafe_allow_html=True)
    
    if "data_mega" not in st.session_state: st.session_state.data_mega = sanitizar_dados_mega({})

    tabs = st.tabs(["📂 1. Banco de Dados", "🧠 2. Cérebro Analítico (IA)", "🤖 3. Geração Autônoma", "📜 4. Fila de Sorteio", "🏆 5. Sincronização e Entrada"])

    with tabs[0]:
        st.markdown("### 💾 Central de Dados e Livro-Caixa da Mega-Sena")
        t_custos, t_premios = st.session_state.data_mega["historico_custos"], st.session_state.data_mega["historico_premios"]
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
                st.markdown("**📂 Gerenciamento do Cofre Mega-Sena**")
                st.file_uploader("📥 Carregar Arquivo Cofre_Mega.json", type="json", key="uploader_cofre_mega", on_change=cb_carregar_cofre_mega)
                st.info(f"📊 **Concursos Oficiais Salvos:** {len(st.session_state.data_mega.get('historico_dados', []))}.")
                st.download_button("📤 Baixar Backup Consolidado", json.dumps(st.session_state.data_mega), "Cofre_Mega.json", type="primary", use_container_width=True)
        with c2:
            with st.container(border=True):
                st.markdown("**💸 Correção Manual de Livro-Caixa**")
                valor_mov = st.number_input("Digite o Valor (R$):", min_value=0.0, step=10.0, key="input_mov_mega")
                col_dep, col_sac = st.columns(2)
                with col_dep:
                    if st.button("➕ Adicionar Gasto Extra", key="btn_gasto_mega", use_container_width=True) and valor_mov > 0:
                        st.session_state.data_mega["historico_custos"] += valor_mov
                        salvar_dados_mega(st.session_state.data_mega)
                        st.rerun()
                with col_sac:
                    if st.button("✅ Adicionar Prêmio Extra", key="btn_premio_mega", use_container_width=True) and valor_mov > 0:
                        st.session_state.data_mega["historico_premios"] += valor_mov
                        salvar_dados_mega(st.session_state.data_mega)
                        st.rerun()
                st.divider()
                if st.button("🔄 ZERAR CONTABILIDADE", key="btn_zerar_mega", use_container_width=True, type="secondary"):
                    st.session_state.data_mega["historico_custos"] = st.session_state.data_mega["historico_premios"] = 0.0
                    st.session_state.data_mega["ledger_track"] = {"bilhetes": 0, "premiados_geral": 0, "elite": 0}
                    salvar_dados_mega(st.session_state.data_mega)
                    st.rerun()

    with tabs[1]:
        exibir_mini_painel_financeiro_mega()
        st.markdown("### 🧠 Diagnóstico da Inteligência Artificial (Mega-Sena)")
        track = st.session_state.data_mega.get("ledger_track", {"bilhetes": 0, "premiados_geral": 0, "elite": 0})
        custo_real, retorno_real = st.session_state.data_mega.get("historico_custos", 0.0), st.session_state.data_mega.get("historico_premios", 0.0)
        win_rate = (track['premiados_geral'] / track['bilhetes'] * 100) if track.get('bilhetes', 0) > 0 else 0.0
        roi_val, roi_pct = retorno_real - custo_real, ((retorno_real - custo_real) / custo_real * 100) if custo_real > 0 else 0.0

        with st.container(border=True):
            st.markdown("#### 📈 Track Record: A Máquina em Ação")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("🎟️ Bilhetes Operados", track.get('bilhetes', 0))
            c2.metric("🎯 Win Rate (Prêmios)", f"{win_rate:.1f}%")
            elite_rate = (track.get('elite', 0) / track.get('premiados_geral', 1) * 100) if track.get('premiados_geral', 0) > 0 else 0.0
            c3.metric("💎 Freq. Quina/Sena", f"{elite_rate:.1f}%" if elite_rate > 0 else "0.0%")
            c4.metric("📈 ROI Financeiro", f"{roi_pct:.1f}%", f"R$ {roi_val:.2f}")

        hits_matriz = st.session_state.data_mega.get("matrizes_reais_hits", {})
        with st.container(border=True):
            st.markdown("#### 🎯 Força da Matriz da IA")
            cm1, cm2, cm3 = st.columns(3)
            cm1.metric("Matriz Acertou Quadra", hits_matriz.get(4, hits_matriz.get("4", 0)))
            cm2.metric("Matriz Acertou Quina", hits_matriz.get(5, hits_matriz.get("5", 0)))
            cm3.metric("Matriz Acertou Sena", hits_matriz.get(6, hits_matriz.get("6", 0)))

        hits_bilhetes = st.session_state.data_mega.get("global_hits", {})
        with st.container(border=True):
            st.markdown("#### 🎫 Prêmios Retidos nos Bilhetes")
            cb1, cb2, cb3 = st.columns(3)
            cb1.metric("Bilhetes com Quadra", hits_bilhetes.get(4, hits_bilhetes.get("4", 0)))
            cb2.metric("Bilhetes com Quina", hits_bilhetes.get(5, hits_bilhetes.get("5", 0)))
            cb3.metric("Bilhetes com Sena", hits_bilhetes.get(6, hits_bilhetes.get("6", 0)))

        st.markdown("#### 🧬 Raio-X da Evolução Neural (Pesos Dinâmicos)")
        pesos_ia = st.session_state.data_mega.get("ia_pesos", {})
        if pesos_ia:
            cols_pesos = st.columns(len(pesos_ia))
            for idx, (nome_est, parametros) in enumerate(pesos_ia.items()):
                with cols_pesos[idx]:
                    html_card = f"<div style='background-color: white; padding: 15px; border-radius: 10px; border-top: 5px solid #209869; box-shadow: 0px 4px 10px rgba(0,0,0,0.06); height: 100%;'><div style='font-size: 14px; font-weight: 900; color: #333; text-align: center; margin-bottom: 5px;'>{nome_est.upper()}</div><hr style='margin: 10px 0; border: none; border-top: 1px solid #f0f0f0;'>"
                    for chave, valor in parametros.items(): html_card += f"<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;'><span style='font-size: 12px; color: #777; font-weight: 700;'>{chave.upper()}</span><span style='font-size: 15px; font-weight: 900; color: #209869;'>{valor:.2f}</span></div>"
                    html_card += "</div>"
                    st.markdown(html_card, unsafe_allow_html=True)
                
        historico_painel = st.session_state.data_mega.get("historico_dados", [])
        if historico_painel:
            ia = raciocinio_total_ia_mega(historico_painel, {})
            if ia:
                tamanho_m = ia['qtd_matriz']
                st.markdown(f"### 🎯 Matriz Cirúrgica Atual — {tamanho_m} Dezenas")
                with st.container(border=True):
                    st.info(f"⚡ **LINHA TÁTICA ATIVADA:** {ia['estrategia']}\n\n**DIRETRIZ DA DECISÃO:** {ia['motivo_est']}\n\n🎯 **GRUPO DE ELITE:** " + ", ".join([f"{n:02d}" for n in ia['matriz_base']]))
                    st.markdown("#### 🗺️ Heatmap Espacial de 60 Dezenas")
                    pesos_ordenados = sorted(ia['pesos'].items(), key=lambda x: x[0])
                    cols = st.columns(10)
                    for idx, (dez, peso) in enumerate(pesos_ordenados):
                        with cols[idx % 10]:
                            is_elite = dez in ia['matriz_base']
                            bg_color, tx_color, border = ("#209869", "white", "none") if is_elite else ("#f4f6f9", "#333", "1px solid #ddd")
                            st.markdown(f"<div style='background-color:{bg_color}; color:{tx_color}; width:100%; aspect-ratio:1; border-radius:8px; border:{border}; display:flex; flex-direction:column; align-items:center; justify-content:center; margin-bottom:8px;'><div style='font-size:16px; font-weight:900;'>{dez:02d}</div><div style='font-size:9px;'>{peso:.1f}</div></div>", unsafe_allow_html=True)
        else: st.warning("⚠️ Carregue o Cofre_Mega.json na Aba 1.")

    with tabs[2]:
        exibir_mini_painel_financeiro_mega()
        st.markdown("### 🚀 Engenharia Combinatória Mega-Sena")
        if st.session_state.data_mega["historico_dados"]:
            ia = raciocinio_total_ia_mega(st.session_state.data_mega["historico_dados"], {})
            with st.container(border=True):
                garantia_alvo = st.radio("Garantia:", options=[6, 5, 4], format_func=lambda x: f"Garantia Absoluta de {x} Pontos", horizontal=True, key="radio_garantia_mega_aba3")
                jogos_exatos, custo_exato = obter_dados_fechamento_mega(ia['matriz_base'], garantia_alvo)
                st.info(f"📊 **Volume Exato:** {jogos_exatos} Bilhetes\n\n💸 **Investimento:** R$ {custo_exato:.2f}")

                if st.button("🧬 GERAR FECHAMENTO EXATO", type="primary", use_container_width=True, key="btn_gerar_mega"):
                    st.session_state.data_mega["jogos_salvos"] = [j for j in st.session_state.data_mega["jogos_salvos"] if j.get('status') != "Aguardando Sorteio"]
                    matriz_reduzida = gerar_fechamento_matematico_mega(tuple(ia['matriz_base']), garantia_alvo)
                    prog_a = st.progress(0)
                    for i, dezenas_jogo in enumerate(matriz_reduzida):
                        st.session_state.data_mega["jogos_salvos"].append({"id": str(uuid.uuid4()), "concurso_alvo": ia['alvo'], "dezenas": sorted(list(dezenas_jogo)), "tamanho": len(dezenas_jogo), "estrategia": ia['cod_estrategia'], "justificativa": f"Garantia 100% de {garantia_alvo} pts.", "status": "Aguardando Sorteio", "acertos": 0, "premio_valor": 0.0, "matriz_origem": ia['matriz_base']})
                        if i % max(1, (len(matriz_reduzida) // 10)) == 0: prog_a.progress(min((i+1)/len(matriz_reduzida), 1.0))
                    st.session_state.data_mega['historico_custos'] += len(matriz_reduzida) * 5.00
                    salvar_dados_mega(st.session_state.data_mega)
                    st.success(f"**🥇 FECHAMENTO CONCLUÍDO!** {len(matriz_reduzida)} bilhetes.")
                    st.rerun()

        jogos_espera = [j for j in st.session_state.data_mega.get("jogos_salvos", []) if j.get('status') == "Aguardando Sorteio"]
        if jogos_espera:
            st.markdown("#### 👀 Pré-visualização")
            bilhetes_por_pagina, total_paginas = 30, (len(jogos_espera) // 30) + (1 if len(jogos_espera) % 30 > 0 else 0)
            pagina_atual = st.selectbox("Página", range(1, total_paginas + 1), label_visibility="collapsed", key="pag_mega_aba3") if total_paginas > 1 else 1
            inicio, fim = (pagina_atual - 1) * bilhetes_por_pagina, ((pagina_atual - 1) * bilhetes_por_pagina) + bilhetes_por_pagina
            cols = st.columns(3)
            for idx, jogo in enumerate(jogos_espera[inicio:fim]):
                with cols[idx % 3]: exibir_card_volante_mega(jogo, inicio + idx + 1)

    with tabs[3]:
        exibir_mini_painel_financeiro_mega()
        jogos_em_espera = [j for j in st.session_state.data_mega.get("jogos_salvos", []) if j.get('status') == "Aguardando Sorteio"]
        total_premio = sum(j.get("premio_valor", 0) for j in st.session_state.data_mega.get("jogos_salvos", []) if j.get('status') == "Premiado")
        c1, c2, c3 = st.columns(3)
        c1.metric("🎫 Jogos em Espera", len(jogos_em_espera))
        c2.metric("💰 Premiação Total", f"R$ {total_premio:.2f}")
        c3.metric("📊 Bilhetes Auditados", len([j for j in st.session_state.data_mega.get("jogos_salvos", []) if j.get('status') != "Aguardando Sorteio"]))
    
        if st.session_state.data_mega.get("jogos_salvos") and st.session_state.data_mega.get("historico_dados"):
            ultimo_jogo_criado = st.session_state.data_mega["jogos_salvos"][-1]
            if ultimo_jogo_criado.get("matriz_origem"):
                st.write(f"**Matriz Usada (Alvo {ultimo_jogo_criado.get('concurso_alvo')}):**")
                st.code(", ".join([f"{n:02d}" for n in sorted(list(set(ultimo_jogo_criado.get("matriz_origem"))))]))
        
        if st.session_state.data_mega.get("jogos_salvos"):
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1: st.button("🗑️ LIMPAR TODOS", on_click=cb_excluir_todos_mega, type="secondary", use_container_width=True, key="btn_limpar_todos_mega")
            with col_btn2:
                ultimas_dezenas = st.session_state.data_mega["historico_dados"][-1]['dezenas'] if st.session_state.data_mega.get("historico_dados") else []
                pdf_bytes = gerar_pdf_jogos_mega(st.session_state.data_mega["jogos_salvos"], ultimas_dezenas)
                st.download_button("📤 EXPORTAR RELATÓRIO", data=pdf_bytes, file_name="Relatorio_Mega.pdf", mime="application/pdf", type="primary", use_container_width=True)

        jogos = st.session_state.data_mega.get("jogos_salvos", [])
        if jogos:
            bilhetes_por_pagina, total_paginas = 30, (len(jogos) // 30) + (1 if len(jogos) % 30 > 0 else 0)
            pagina_atual = st.selectbox("Navegação", range(1, total_paginas + 1), key="pag_mega_aba4") if total_paginas > 1 else 1
            inicio, fim = (pagina_atual - 1) * bilhetes_por_pagina, ((pagina_atual - 1) * bilhetes_por_pagina) + bilhetes_por_pagina
            cols = st.columns(3)
            for idx, j in enumerate(jogos[inicio:fim]):
                with cols[idx % 3]:
                    exibir_card_volante_mega(j, inicio + idx + 1)
                    if j.get('status') == "Premiado": st.success(f"✅ PREMIADO ({j.get('acertos', 0)} pts)\n💰 R$ {j.get('premio_valor', 0):.2f}")
                    elif j.get('status') == "Não Premiado": st.error(f"❌ NÃO PREMIADO ({j.get('acertos', 0)} pts)")
                    else: st.info("⏳ AGUARDANDO")
                    st.button("🗑️ Apagar", key=f"del_mega_{j.get('id', uuid.uuid4())}", on_click=cb_excluir_jogo_mega, args=(j.get('id'),), use_container_width=True)

    with tabs[4]:
        exibir_mini_painel_financeiro_mega()
        with st.container(border=True):
            col_massa1, col_massa2 = st.columns(2)
            with col_massa1:
                st.markdown("#### 🛸 Buscar Faltantes (API)")
                if st.button("🛸 AUDITAR GAPs MEGA-SENA", type="primary", use_container_width=True, key="btn_gap_mega"):
                    historico = st.session_state.data_mega.get("historico_dados", [])
                    if historico:
                        try:
                            res_latest = requests.get("https://loteriascaixa-api.herokuapp.com/api/megasena/latest", verify=False, timeout=10).json()
                            ultimo_salvo, ultimo_oficial = int(historico[-1]["concurso"]), int(res_latest['concurso'])
                            if ultimo_salvo >= ultimo_oficial: st.info("O sistema já está atualizado.")
                            else:
                                barra, lucro_acumulado_massa = st.progress(0), 0.0
                                for i, num in enumerate(list(range(ultimo_salvo + 1, ultimo_oficial + 1))):
                                    res_conc = requests.get(f"https://loteriascaixa-api.herokuapp.com/api/megasena/{num}", verify=False, timeout=10).json()
                                    if 'concurso' in res_conc:
                                        dezenas_sorteadas = sorted([int(d) for d in res_conc['dezenas']])
                                        st.session_state.data_mega["historico_dados"].append({"concurso": num, "dezenas": dezenas_sorteadas, "data": res_conc.get('data', '')})
                                        lucro_parcial, _ = auditar_e_aprender_unificado_mega(num, dezenas_sorteadas, extrair_rateios_api_mega(res_conc.get('premiacoes', [])))
                                        lucro_acumulado_massa += lucro_parcial
                                    barra.progress((i + 1) / (ultimo_oficial - ultimo_salvo))
                                salvar_dados_mega(st.session_state.data_mega)
                                st.success(f"✅ GAPs processados. R$ {lucro_acumulado_massa:.2f} creditados.")
                                st.rerun()
                        except Exception as e: st.error(f"Erro: {e}")
            with col_massa2:
                st.markdown("#### ☢️ Iniciar Operação (Download Base)")
                if st.button("📥 BAIXAR TODOS OS SORTEIOS", type="secondary", use_container_width=True, key="btn_down_mega"):
                    with st.spinner("Baixando base de dados da Mega-Sena..."):
                        try:
                            res_todos = sorted(requests.get("https://loteriascaixa-api.herokuapp.com/api/megasena", verify=False, timeout=60).json(), key=lambda k: int(k['concurso']))
                            st.session_state.data_mega["historico_dados"] = [{"concurso": int(r['concurso']), "dezenas": sorted([int(d) for d in r['dezenas']]), "data": r.get('data', '')} for r in res_todos]
                            salvar_dados_mega(st.session_state.data_mega)
                            st.success("✅ Download concluído.")
                        except Exception as e: st.error(f"Erro na conexão com API: {e}")

        col_sync1, col_sync2 = st.columns(2)
        with col_sync1:
            with st.container(border=True):
                st.markdown("#### 🌐 Sincronização Automática")
                if st.button("🔄 Buscar Último Resultado Oficial", type="primary", use_container_width=True, key="btn_sync_mega"):
                    with st.spinner("Conectando à API..."):
                        try:
                            resp = requests.get("https://loteriascaixa-api.herokuapp.com/api/megasena/latest", verify=False, timeout=15)
                            if resp.status_code == 200:
                                res = resp.json()
                                num_c, dez_o = int(res['concurso']), sorted([int(x) for x in res['dezenas']])
                                novo_dado = {"concurso": num_c, "data": res.get('data',''), "dezenas": dez_o, "premiacoes": res.get('premiacoes', [])}
                                if not any(h['concurso'] == num_c for h in st.session_state.data_mega["historico_dados"]): st.session_state.data_mega["historico_dados"].append(novo_dado)
                                st.session_state.caixa_latest_mega = novo_dado
                                lucro_total, _ = auditar_e_aprender_unificado_mega(num_c, dez_o, extrair_rateios_api_mega(res.get('premiacoes', [])))
                                salvar_dados_mega(st.session_state.data_mega)
                                st.success(f"✅ Atualizado! R$ {lucro_total:.2f} contabilizados.")
                                st.rerun()
                        except Exception as e: st.error(f"Erro: {e}")
        with col_sync2:
            with st.container(border=True):
                st.markdown("#### 🛠️ Inserção Manual")
                concurso_manual = st.number_input("Número do Concurso:", min_value=1, step=1, key="num_conc_manual_mega")
                dezenas_texto = st.text_input("Cole 6 Dezenas Sorteadas:", key="dez_manual_input_mega")
                if st.button("✅ Confirmar e Auditar", use_container_width=True, key="btn_man_mega"):
                    try:
                        dezenas_oficiais = sorted([int(n) for n in re.findall(r'\d+', dezenas_texto)])
                        if len(dezenas_oficiais) != 6: st.error("Insira exatamente 6 números.")
                        else:
                            lucro_total, _ = auditar_e_aprender_unificado_mega(concurso_manual, dezenas_oficiais, rateios=None)
                            if not any(h['concurso'] == concurso_manual for h in st.session_state.data_mega["historico_dados"]):
                                novo_dado = {"concurso": concurso_manual, "data": datetime.now().strftime("%d/%m/%Y"), "dezenas": dezenas_oficiais, "premiacoes": []}
                                st.session_state.data_mega["historico_dados"].append(novo_dado)
                                st.session_state.caixa_latest_mega = novo_dado
                            salvar_dados_mega(st.session_state.data_mega)
                            st.success(f"✅ Sucesso. Prêmios: R$ {lucro_total:.2f}.")
                            st.rerun()
                    except ValueError: st.error("Erro na conversão.")

        with st.container(border=True):
            st.markdown("#### 🧠 Forçar Reprocessamento da Inteligência Artificial")
            if st.button("🔄 ATUALIZAR E FORÇAR LEITURA PARA O PRÓXIMO SORTEIO", type="primary", use_container_width=True, key="btn_force_mega"):
                st.session_state.data_mega["ia_memoria"] = {}
                salvar_dados_mega(st.session_state.data_mega)
                st.success("✅ Memória Cache zerada! A IA recalculará a matriz no próximo acesso.")
                st.rerun() 

        if 'caixa_latest_mega' in st.session_state:
            r = st.session_state.caixa_latest_mega
            st.markdown(f"#### 🏛️ Último Extrato Salvo da Caixa: Concurso {r['concurso']}")
            if r.get('premiacoes'): st.table(pd.DataFrame(r['premiacoes']))

    exibir_rodape()

# =====================================================================
# 5. INICIALIZAÇÃO DO ROTEADOR
# =====================================================================
if st.session_state.pagina_atual == "login":
    tela_login()
elif st.session_state.pagina_atual == "lobby" and st.session_state.autenticado:
    tela_lobby()
elif st.session_state.pagina_atual == "lotofacil" and st.session_state.autenticado:
    tela_lotofacil()
elif st.session_state.pagina_atual == "megasena" and st.session_state.autenticado:
    tela_megasena()
else:
    st.session_state.pagina_atual = "login"
    st.session_state.autenticado = False
    st.rerun()
