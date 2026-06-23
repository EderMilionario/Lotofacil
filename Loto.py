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
# 3. FUNÇÕES GLOBAIS DA LOTOFÁCIL (INTACTAS)
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

def obter_garantia_lotofacil(tamanho_matriz):
    garantias = {
        15: "Para fazer 15 pontos, as 15 sorteadas precisam ser exatamente as suas 15.",
        16: "Se as 15 sorteadas estiverem DENTRO das suas 16, você tem 100% de garantia dos prêmios múltiplos e chance alta de 15 pontos.",
        17: "Se as 15 sorteadas caírem DENTRO das suas 17, a garantia base é ativada (prêmios gordos trancados).",
        18: "Se as 15 sorteadas caírem DENTRO das suas 18 escolhidas, o cadeado matemático garante no mínimo 14 pontos (dependendo da redução).",
        19: "Acertando as 15 DENTRO das 19, o cadeado tranca 100% o prêmio da garantia escolhida.",
        20: "Acertando as 15 DENTRO das 20, você blinda o prêmio do fechamento."
    }
    msg = garantias.get(tamanho_matriz, f"Lembre-se: as 15 sorteadas precisam obrigatoriamente estar dentro do seu grupo de {tamanho_matriz}.")
    return f"""
<div style='background-color: #fdf5ff; border-left: 5px solid #930089; padding: 15px; border-radius: 5px; margin-bottom: 20px;'>
    <h4 style='color: #930089; margin-top: 0;'>🔒 O CADEADO MATEMÁTICO (LOTOFÁCIL)</h4>
    <p style='margin-bottom: 5px;'>Você está gerando um desdobramento para uma matriz de <b>{tamanho_matriz} dezenas</b>.</p>
    <p style='font-weight: bold; color: #333;'>CONDIÇÃO PARA O PRÊMIO: {msg}</p>
    <p style='font-size: 12px; color: #666; margin-bottom: 0;'>O sistema não faz mágica, ele aplica matemática inquebrável. Se a IA colocar as 15 sorteadas dentro da sua matriz base, o prêmio não escapa.</p>
</div>
"""

# =====================================================================
# 4. FUNÇÕES GLOBAIS DA MEGA-SENA (INTACTAS COM ELITE FILTERS)
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

@st.cache_data(show_spinner="🧠 Processando Matriz e Aplicando Filtros Elite Mega-Sena...")
def gerar_fechamento_matematico_mega(dezenas_tuple, garantia):
    dezenas = list(dezenas_tuple)
    todas_comb_6 = list(itertools.combinations(dezenas, 6))
    
    comb_filtradas = []
    for c in todas_comb_6:
        soma = sum(c)
        mult_10 = sum(1 for x in c if x % 10 == 0)
        if 120 <= soma <= 240 and mult_10 <= 2:
            comb_filtradas.append(c)
            
    todas_comb_6 = comb_filtradas

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

def obter_garantia_megasena(tamanho_matriz):
    return f"""
<div style='background-color: #f2fbf6; border-left: 5px solid #209869; padding: 15px; border-radius: 5px; margin-bottom: 20px;'>
    <h4 style='color: #209869; margin-top: 0;'>🔒 O CADEADO MATEMÁTICO (MEGA-SENA)</h4>
    <p style='margin-bottom: 5px;'>Sua Matriz de Jogo: <b>{tamanho_matriz} dezenas</b>.</p>
    <p style='font-weight: bold; color: #333;'>CONDIÇÃO INQUEBRÁVEL PARA O PRÊMIO:</p>
    <p style='color: #444;'>Para o fechamento garantir a Sena, Quina ou Quadra escolhida, <b>as 6 dezenas sorteadas pela Caixa PRECISAM obrigatoriamente estar DENTRO do seu grupo de {tamanho_matriz} números.</b></p>
    <p style='font-size: 12px; color: #666; margin-bottom: 0;'><b>Filtro Elite Ativado:</b> O sistema varre automaticamente a Curva de Gauss (Soma 120 a 240) e remove colunas viciadas (múltiplos de 10) para maximizar o seu prêmio caso acerte. As garantias matemáticas se aplicam aos bilhetes que passaram nesse filtro de elite.</p>
</div>
"""

# =====================================================================
# 5. FUNÇÕES GLOBAIS DA LOTOMANIA (MÓDULO NOVO - ELITE)
# =====================================================================
def sanitizar_dados_lotomania(d):
    if not isinstance(d, dict): d = {}
    if "historico_dados" not in d: d["historico_dados"] = []
    if "jogos_salvos" not in d: d["jogos_salvos"] = []
    if "historico_custos" not in d: d["historico_custos"] = 0.0
    if "historico_premios" not in d: d["historico_premios"] = 0.0
    if "ledger_track" not in d: d["ledger_track"] = {"bilhetes": 0, "premiados_geral": 0, "elite": 0}
    if "global_hits" not in d: d["global_hits"] = {0:0, 15:0, 16:0, 17:0, 18:0, 19:0, 20:0}
    return d

def salvar_dados_lotomania(dados):
    try:
        with open("Cofre_Lotomania.json", "w", encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
    except Exception as e: pass

def cb_carregar_cofre_lotomania():
    file = st.session_state.uploader_cofre_lotomania
    if file:
        try:
            st.session_state.data_loto_mania = sanitizar_dados_lotomania(json.load(file))
            st.toast("Cofre Lotomania sincronizado!", icon="✅")
        except Exception as e: st.error(f"Erro: {e}")

def cb_excluir_jogo_lotomania(jogo_id):
    st.session_state.data_loto_mania['jogos_salvos'] = [j for j in st.session_state.data_loto_mania['jogos_salvos'] if j.get('id') != jogo_id]
    st.toast("Bilhete deletado.", icon="🗑️")

def cb_excluir_todos_lotomania():
    st.session_state.data_loto_mania['jogos_salvos'] = []
    st.toast("Fila limpa.", icon="🧹")

def extrair_rateios_api_lotomania(premiacoes):
    # Valores default caso a API falhe na descrição exata
    rateios = {0: 150000.0, 15: 10.0, 16: 30.0, 17: 250.0, 18: 2500.0, 19: 50000.0, 20: 5000000.0}
    if premiacoes:
        for p in premiacoes:
            desc = p.get('descricao', '').lower()
            val = float(p.get('valorPremio', 0.0))
            if '20 acertos' in desc: rateios[20] = val
            elif '19 acertos' in desc: rateios[19] = val
            elif '18 acertos' in desc: rateios[18] = val
            elif '17 acertos' in desc: rateios[17] = val
            elif '16 acertos' in desc: rateios[16] = val
            elif '15 acertos' in desc: rateios[15] = val
            elif '0 acertos' in desc or 'nenhum' in desc: rateios[0] = val
    return rateios

def calcular_premio_lotomania(pontos, rateios):
    if pontos in rateios: return rateios[pontos]
    return 0.0

def exibir_mini_painel_financeiro_lotomania():
    c = st.session_state.data_loto_mania.get("historico_custos", 0.0)
    p = st.session_state.data_loto_mania.get("historico_premios", 0.0)
    roi = p - c
    cor_roi = "#F78100" if roi >= 0 else "red"
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("💸 Investimento Total", f"R$ {c:,.2f}")
    with col2: st.metric("💰 Prêmios Recuperados", f"R$ {p:,.2f}")
    with col3: st.markdown(f"<div style='background-color:white; padding:10px; border-radius:12px; border-left:6px solid {('#F78100' if roi>=0 else '#dd3333')}; box-shadow: 0 4px 6px rgba(0,0,0,0.04);'><p style='margin:0; font-size:14px; color:#666; font-weight:bold;'>📈 ROI Líquido</p><h3 style='margin:0; color:{cor_roi};'>R$ {roi:,.2f}</h3></div>", unsafe_allow_html=True)
    st.write("")

def analisar_frequencia_lotomania(historico_sorteios):
    # Analisa 100 números (0 a 99)
    atrasos = {n: 0 for n in range(100)}
    dez_enc = {n: False for n in range(100)}
    
    for h in reversed(historico_sorteios):
        for n in range(100):
            # API da caixa retorna 00 como 0 ou string "00"
            if n in h['dezenas'] or f"{n:02d}" in h['dezenas']: dez_enc[n] = True
            elif not dez_enc[n]: atrasos[n] += 1

    unified_scores = {}
    for n in range(100):
        delay = atrasos.get(n, 0)
        score = 50.0
        # Fuga de humanos (0 e 9 nas pontas)
        if n % 10 in [0, 9]: score += 10.0 
        # Ponto termal de fervura (atrasado médio é bom)
        if 3 <= delay <= 12: score += 25.0
        elif delay > 20: score -= 15.0 # Congelado
        unified_scores[n] = round(score, 2)

    return sorted(unified_scores.items(), key=lambda x: x[1], reverse=True)

def validar_filtros_lotomania(jogo):
    # Soma de Gauss (2100 a 2800)
    soma = sum(jogo)
    if not (2100 <= soma <= 2800): return False
    # Quadrantes Balanceados (10x10)
    q = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}
    for dezena in jogo:
        lin, col = dezena // 10, dezena % 10
        if lin < 5 and col < 5: q["Q1"] += 1
        elif lin < 5 and col >= 5: q["Q2"] += 1
        elif lin >= 5 and col < 5: q["Q3"] += 1
        else: q["Q4"] += 1
    # Balanceamento estrito para evitar bolos no volante
    for qtd in q.values():
        if qtd < 8 or qtd > 17: return False
    return True

@st.cache_data(show_spinner="🧠 Processando Matriz Lotomania (Monte Carlo Estocástico)...")
def gerar_estrategia_super_matriz(top_dezenas, qtd_jogos=5):
    jogos_aprovados = []
    max_tentativas = 15000 # Fail-safe
    tentativas = 0
    while len(jogos_aprovados) < qtd_jogos and tentativas < max_tentativas:
        candidato = sorted(random.sample(top_dezenas, 50))
        if validar_filtros_lotomania(candidato): jogos_aprovados.append(candidato)
        tentativas += 1
    # Se estourar as tentativas sem achar o total (raro), retorna o que conseguiu
    return jogos_aprovados

def exibir_card_volante_lotomania(jogo, numero_jogo, sorteio_real=None):
    dezenas = jogo.get('dezenas', [])
    alvo = jogo.get('concurso_alvo', 'N/A')
    estrategia = jogo.get('estrategia', 'Lotomania Elite')
    justificativa = jogo.get('justificativa', 'Fechamento Lotomania')
    sorteio_set = set(sorteio_real) if sorteio_real else set()

    grid_html = "<div style='display: grid; grid-template-columns: repeat(10, 1fr); gap: 2px; margin-bottom: 12px; justify-items: center; background-color: #fafafa; padding: 5px; border-radius: 5px;'>"
    for num in range(100):
        # A Lotomania exibe do 00 ao 99
        if num in dezenas: bg_color, txt_color, border, shadow = ("#28a745", "white", "none", "box-shadow: 0 0 3px #28a745;") if num in sorteio_set else ("#F78100", "white", "none", "box-shadow: 0 1px 2px rgba(247,129,0,0.3);")
        else: bg_color, txt_color, border, shadow = "transparent", "#e0e0e0", "1px solid #f0f0f0", ""
        grid_html += f"<div style='background-color: {bg_color}; color: {txt_color}; border: {border}; {shadow} text-align: center; border-radius: 50%; width: 18px; height: 18px; display: flex; align-items: center; justify-content: center; font-size: 8px; font-weight: bold;'>{num:02d}</div>"
    grid_html += "</div>"
    
    html_card = f"<div style='background-color: #ffffff; border: 1px solid #e0e0e0; padding: 15px; border-radius: 8px; margin-bottom: 15px; box-shadow: 2px 2px 8px rgba(0,0,0,0.05);'><div style='display: flex; justify-content: space-between; border-bottom: 1px solid #eee; padding-bottom: 8px; margin-bottom: 12px;'><span style='font-size: 15px; font-weight: bold; color: #F78100;'>🎫 JOGO {numero_jogo:02d}</span><span style='font-size: 12px; font-weight: bold; color: #666;'>Alvo: {alvo}</span></div><div style='font-size: 11px; color: #555; margin-bottom: 12px; font-weight: bold; text-transform: uppercase;'>ESTRATÉGIA: {estrategia}</div>{grid_html}<div style='text-align: center; font-size: 10px; font-weight: bold; color: #F78100; background: rgba(247, 129, 0, 0.08); padding: 6px; border-radius: 4px; margin-top: 5px;'>{justificativa}</div></div>"
    st.markdown(html_card, unsafe_allow_html=True)

def auditar_e_aprender_lotomania(concurso, dezenas_sorteadas, rateios):
    lucro_total = 0.0
    relatorio = []
    sorteio_set = set(dezenas_sorteadas)
    jogos_processados, premiados = 0, 0
    
    ledger = st.session_state.data_loto_mania["ledger_track"]
    hits_bilhetes = st.session_state.data_loto_mania["global_hits"]
    
    for j in st.session_state.data_loto_mania.get("jogos_salvos", []):
        alvo = j.get('concurso_alvo')
        pode = str(alvo) == str(concurso) or (isinstance(alvo, int) and alvo <= concurso) or str(alvo) == "Legado"
                
        if j.get('status') == "Aguardando Sorteio" and pode:
            jogos_processados += 1
            ledger["bilhetes"] += 1
            pontos = len(set(j.get('dezenas', [])).intersection(sorteio_set))
            j['acertos'] = pontos
            j['premio_valor'] = calcular_premio_lotomania(pontos, rateios)
            
            if pontos in [0, 15, 16, 17, 18, 19, 20]:
                j['status'] = "Premiado"
                lucro_total += j['premio_valor']
                st.session_state.data_loto_mania["historico_premios"] += j['premio_valor']
                premiados += 1
                ledger["premiados_geral"] += 1
                if pontos in [0, 19, 20]: ledger["elite"] += 1
                hits_bilhetes[pontos] = hits_bilhetes.get(pontos, 0) + 1
            else: j['status'] = "Não Premiado"

    st.session_state.data_loto_mania["global_hits"] = hits_bilhetes
    st.session_state.data_loto_mania["ledger_track"] = ledger
    
    if jogos_processados > 0: relatorio.append(f"Auditoria Lotomania {concurso}: {premiados}/{jogos_processados} bilhetes premiados.")
    return lucro_total, relatorio

def gerar_pdf_jogos_lotomania(jogos, dezenas_anteriores=None):
    if dezenas_anteriores is None: dezenas_anteriores = []
    def limpar_latin1(t): return str(t).replace("🧬", "").replace("🍀", "").replace("🎫", "").replace("⚠️", "").encode('latin-1', 'ignore').decode('latin-1')
    pdf = FPDF()
    pdf.set_auto_page_break(auto=False)
    margem_x, margem_y, largura_card, altura_card, espaco_x, espaco_y = 10, 35, 90, 80, 5, 5
    sorteio_set = set(dezenas_anteriores)

    for i, j in enumerate(jogos):
        if i % 6 == 0:
            pdf.add_page()
            pdf.set_text_color(247, 129, 0)
            pdf.set_font('Arial', 'B', 16)
            pdf.set_xy(10, 12)
            pdf.cell(0, 10, "Loterias PRO - Relatorio Lotomania", ln=0)
            pdf.set_font('Arial', '', 9)
            pdf.set_text_color(100, 100, 100)
            pdf.set_xy(10, 20)
            pdf.cell(0, 8, f"TOTAL: {len(jogos)} BILHETES  |  Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=0)
            pdf.line(10, 28, 200, 28)

        coluna, linha = (i % 6) % 2, (i % 6) // 2
        x_start, y_start = margem_x + (coluna * (largura_card + espaco_x)), margem_y + (linha * (altura_card + espaco_y))
        estrategia, dezenas, alvo = limpar_latin1(str(j.get('estrategia', 'Lotomania Elite'))), j.get('dezenas', []), limpar_latin1(str(j.get('concurso_alvo', 'N/A')))
        
        pdf.set_fill_color(255, 248, 240) 
        pdf.rect(x_start, y_start, largura_card, altura_card, 'F')
        pdf.set_fill_color(247, 129, 0) 
        pdf.rect(x_start, y_start, 2, altura_card, 'F')

        pdf.set_text_color(40, 40, 40)
        pdf.set_font('Arial', 'B', 10)
        pdf.set_xy(x_start + 5, y_start + 4)
        pdf.cell(50, 6, f"JOGO {(i+1):02d}", ln=0)
        pdf.set_font('Arial', '', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.set_xy(x_start + 40, y_start + 4)
        pdf.cell(45, 6, f"Alvo: {alvo}", ln=0, align='R')
        pdf.set_text_color(247, 129, 0) 
        pdf.set_font('Arial', 'B', 7)
        pdf.set_xy(x_start + 5, y_start + 9)
        pdf.cell(80, 5, f"{estrategia[:35]}", ln=0)

        bolinha_x_start, bolinha_y_start, passo_x, passo_y = x_start + 7, y_start + 17, 7.5, 5.5 
        for num in range(100):
            lin, col = num // 10, num % 10
            cx, cy = bolinha_x_start + (col * passo_x), bolinha_y_start + (lin * passo_y)
            if num in dezenas:
                if num in sorteio_set: pdf.set_fill_color(40, 167, 69)
                else: pdf.set_fill_color(247, 129, 0)
                pdf.set_text_color(255, 255, 255)
            else:
                pdf.set_fill_color(235, 235, 235)
                pdf.set_text_color(160, 160, 160)
            pdf.ellipse(cx, cy, 4, 4, 'F')
            pdf.set_xy(cx, cy)
            pdf.set_font('Arial', 'B', 4)
            pdf.cell(4, 4, f"{num:02d}", align='C')

        pdf.set_text_color(120, 120, 120)
        pdf.set_font('Arial', 'B', 7)
        pdf.set_xy(x_start + 5, y_start + altura_card - 6)
        pdf.cell(80, 5, "Fechamento Lotomania Institucional", ln=0, align='C')

    resultado = pdf.output(dest='S')
    if isinstance(resultado, str): return resultado.encode('latin-1', 'ignore')
    return bytes(resultado)


# =====================================================================
# 6. CONSTRUÇÃO DAS TELAS (PÁGINAS DO SISTEMA)
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
    
    st.markdown("""
    <style>
        .block-container { max-width: 1000px; }
        div[data-testid="stColumn"] div.stButton > button {
            aspect-ratio: 1 / 1 !important; 
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
            white-space: pre-wrap !important; 
        }
        div[data-testid="stColumn"]:nth-child(1) div.stButton > button {
            background: linear-gradient(145deg, #ffffff, #fdf5ff) !important;
            border: 3px solid #930089 !important;
            color: #930089 !important;
        }
        div[data-testid="stColumn"]:nth-child(1) div.stButton > button:hover {
            background: #930089 !important;
            color: white !important;
            transform: translateY(-8px) scale(1.02) !important;
            box-shadow: 0 15px 35px rgba(147,0,137,0.3) !important;
        }
        div[data-testid="stColumn"]:nth-child(2) div.stButton > button {
            background: linear-gradient(145deg, #ffffff, #f2fbf6) !important;
            border: 3px solid #209869 !important;
            color: #209869 !important;
        }
        div[data-testid="stColumn"]:nth-child(2) div.stButton > button:hover {
            background: #209869 !important;
            color: white !important;
            transform: translateY(-8px) scale(1.02) !important;
            box-shadow: 0 15px 35px rgba(32,152,105,0.3) !important;
        }
        div[data-testid="stColumn"]:nth-child(3) div.stButton > button {
            background: linear-gradient(145deg, #ffffff, #fff8f0) !important;
            border: 3px solid #F78100 !important;
            color: #F78100 !important;
        }
        div[data-testid="stColumn"]:nth-child(3) div.stButton > button:hover {
            background: #F78100 !important;
            color: white !important;
            transform: translateY(-8px) scale(1.02) !important;
            box-shadow: 0 15px 35px rgba(247,129,0,0.3) !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h4 style='text-align: center; color: #666; font-weight: normal; margin-bottom: 50px;'>Escolha o Motor Analítico para iniciar a sessão:</h4>", unsafe_allow_html=True)
    
    cols = st.columns([1, 1, 1]) 
    
    with cols[0]:
        if st.button("🍀\nLotofácil\nIA de Frequência", key="btn_loto", use_container_width=True):
            st.session_state.pagina_atual = "lotofacil"
            st.rerun()
            
    with cols[1]:
        if st.button("🍀\nMega-Sena\nIA Espacial", key="btn_mega", use_container_width=True):
            st.session_state.pagina_atual = "megasena"
            st.rerun()
            
    with cols[2]:
        if st.button("🍀\nLotomania\nIA de Grupo", key="btn_lotomania", use_container_width=True):
            st.session_state.pagina_atual = "lotomania"
            st.rerun()
            
    exibir_rodape()

# --- TELA LOTOFÁCIL (Ocultada para não inflar o código desnecessariamente se idêntica, mas como pedida inteira, aqui está completa) ---
def tela_lotofacil():
    exibir_cabecalho(loteria_especifica="LOTOFÁCIL PRO", cor_loteria="#930089", icone_loteria="🍀")
    st.markdown("""<style>:root { --roxo: #930089; --roxo-hover: #7a0072; } .stApp { background-color: #f4f6f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; } .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: #ffffff; padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); } .stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 10px 20px; background-color: #f8f9fa; border: 1px solid #e9ecef; transition: all 0.3s ease; } .stTabs [aria-selected="true"] { background-color: var(--roxo) !important; color: white !important; border: none; box-shadow: 0 4px 10px rgba(147,0,137,0.3); } div[data-testid="stMetric"] { background-color: white; padding: 20px; border-radius: 12px; border-left: 6px solid var(--roxo); box-shadow: 0 4px 6px rgba(0,0,0,0.04); } div[data-testid="stAlert"] { background-color: #fdf5ff !important; border-left: 5px solid var(--roxo) !important; color: #333 !important; border-radius: 8px !important; } button[kind="primary"] { background-color: var(--roxo) !important; border: none !important; border-radius: 8px !important; font-weight: bold !important; color: white !important; box-shadow: 0 4px 10px rgba(147,0,137,0.4) !important; transition: all 0.3s ease !important; } button[kind="primary"]:hover { background-color: var(--roxo-hover) !important; transform: translateY(-2px); }</style>""", unsafe_allow_html=True)
    if "data" not in st.session_state: st.session_state.data = sanitizar_dados({})
    tabs = st.tabs(["📂 1. Banco de Dados", "🧠 2. Cérebro Analítico (IA)", "🤖 3. Geração Autônoma", "📜 4. Fila de Sorteio", "🏆 5. Sincronização"])

    with tabs[0]:
        t_custos, t_premios = st.session_state.data["historico_custos"], st.session_state.data["historico_premios"]
        resultado_global = t_premios - t_custos
        with st.container(border=True):
            ind1, ind2, ind3 = st.columns(3)
            ind1.metric("📥 Total Investido", f"R$ {t_custos:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            ind2.metric("📤 Total Retornado", f"R$ {t_premios:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            str_res = f"R$ {resultado_global:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            ind3.metric("📊 Balanço do Projeto", str_res)
        c1, c2 = st.columns(2)
        with c1:
            st.file_uploader("📥 Carregar Arquivo Cofre.json", type="json", key="uploader_cofre", on_change=cb_carregar_cofre)
            st.download_button("📤 Baixar Backup Consolidado", json.dumps(st.session_state.data), "Cofre.json", type="primary", use_container_width=True)
        with c2:
            valor_mov = st.number_input("Valor (R$):", min_value=0.0, step=10.0, key="input_movimentacao")
            if st.button("➕ Gasto Extra", use_container_width=True) and valor_mov > 0: st.session_state.data["historico_custos"] += valor_mov; salvar_dados(st.session_state.data); st.rerun()
            if st.button("✅ Prêmio Extra", use_container_width=True) and valor_mov > 0: st.session_state.data["historico_premios"] += valor_mov; salvar_dados(st.session_state.data); st.rerun()
            if st.button("🔄 ZERAR ROI", use_container_width=True): st.session_state.data["historico_custos"] = st.session_state.data["historico_premios"] = 0.0; salvar_dados(st.session_state.data); st.rerun()

    with tabs[1]:
        exibir_mini_painel_financeiro()
        track = st.session_state.data.get("ledger_track", {"bilhetes": 0, "premiados_geral": 0, "elite": 0})
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            c1.metric("🎟️ Bilhetes Operados", track.get('bilhetes', 0))
            c2.metric("🎯 Win Rate", f"{(track['premiados_geral'] / track['bilhetes'] * 100) if track.get('bilhetes', 0) > 0 else 0.0:.1f}%")
            c3.metric("💎 Elite (14/15 pts)", f"{(track.get('elite', 0) / track.get('premiados_geral', 1) * 100) if track.get('premiados_geral', 0) > 0 else 0.0:.1f}%")
        historico_painel = st.session_state.data.get("historico_dados", [])
        if historico_painel:
            ia = raciocinio_total_ia(historico_painel, st.session_state.data.get("ia_memoria", {}))
            if ia:
                st.info(f"⚡ **ESTRATÉGIA ATIVA:** {ia['estrategia']} | **MATRIZ:** {ia['qtd_matriz']} dezenas\n\n🎯 **DEZENAS:** " + ", ".join([f"{n:02d}" for n in ia['matriz_base']]))

    with tabs[2]:
        exibir_mini_painel_financeiro()
        if st.session_state.data["historico_dados"]:
            ia = raciocinio_total_ia(st.session_state.data["historico_dados"], st.session_state.data.get("ia_memoria", {}))
            st.markdown(obter_garantia_lotofacil(ia['qtd_matriz']), unsafe_allow_html=True)
            garantia_alvo = st.radio("Garantia:", options=[15, 14, 13], horizontal=True)
            jogos_exatos, custo_exato = obter_dados_fechamento(ia['matriz_base'], garantia_alvo)
            st.info(f"📊 {jogos_exatos} Bilhetes | 💸 R$ {custo_exato:.2f}")
            if st.button("🧬 GERAR FECHAMENTO EXATO", type="primary", use_container_width=True):
                st.session_state.data["jogos_salvos"] = [j for j in st.session_state.data["jogos_salvos"] if j.get('status') != "Aguardando Sorteio"]
                matriz_reduzida = gerar_fechamento_matematico(tuple(ia['matriz_base']), garantia_alvo)
                for dezenas_jogo in matriz_reduzida:
                    st.session_state.data["jogos_salvos"].append({"id": str(uuid.uuid4()), "concurso_alvo": ia['alvo'], "dezenas": sorted(list(dezenas_jogo)), "tamanho": len(dezenas_jogo), "estrategia": ia['cod_estrategia'], "justificativa": f"Garantia 100% de {garantia_alvo} pts.", "status": "Aguardando Sorteio", "acertos": 0, "premio_valor": 0.0, "matriz_origem": ia['matriz_base']})
                st.session_state.data['historico_custos'] += len(matriz_reduzida) * 3.50; salvar_dados(st.session_state.data); st.rerun()

    with tabs[3]:
        exibir_mini_painel_financeiro()
        col1, col2 = st.columns(2)
        with col1: st.button("🗑️ LIMPAR TODOS", on_click=cb_excluir_todos, use_container_width=True)
        with col2: st.download_button("📤 EXPORTAR RELATÓRIO (PDF)", data=gerar_pdf_jogos(st.session_state.data["jogos_salvos"]), file_name="Lotofacil.pdf", mime="application/pdf", type="primary", use_container_width=True)
        jogos = st.session_state.data.get("jogos_salvos", [])
        for j in jogos[:15]: exibir_card_volante(j, 1)

    with tabs[4]:
        exibir_mini_painel_financeiro()
        if st.button("🔄 Sincronizar Último Sorteio Oficial (Caixa)", type="primary", use_container_width=True):
            try:
                res = requests.get("https://loteriascaixa-api.herokuapp.com/api/lotofacil/latest", verify=False, timeout=15).json()
                num_c, dez_o = int(res['concurso']), [int(x) for x in res['dezenas']]
                if not any(h['concurso'] == num_c for h in st.session_state.data["historico_dados"]): st.session_state.data["historico_dados"].append({"concurso": num_c, "dezenas": dez_o})
                lucro_total, rel = auditar_e_aprender_unificado(num_c, dez_o, extrair_rateios_api(res.get('premiacoes', [])))
                salvar_dados(st.session_state.data)
                st.success(f"✅ Sincronizado! Prêmios Auditados: R$ {lucro_total:.2f}"); st.rerun()
            except Exception as e: st.error(f"Erro API: {e}")
        if st.button("📥 Baixar Base Completa (Demorado)"):
            res_todos = sorted(requests.get("https://loteriascaixa-api.herokuapp.com/api/lotofacil", verify=False, timeout=60).json(), key=lambda k: int(k['concurso']))
            st.session_state.data["historico_dados"] = [{"concurso": int(r['concurso']), "dezenas": sorted([int(d) for d in r['dezenas']])} for r in res_todos]
            salvar_dados(st.session_state.data); st.success("Download Concluído")
    exibir_rodape()

# --- TELA MEGA-SENA ---
def tela_megasena():
    exibir_cabecalho(loteria_especifica="MEGA-SENA PRO", cor_loteria="#209869", icone_loteria="🍀")
    st.markdown("""<style>:root { --verde: #209869; --verde-hover: #16704d; } .stApp { background-color: #f4f6f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; } .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: #ffffff; padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); } .stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 10px 20px; background-color: #f8f9fa; border: 1px solid #e9ecef; transition: all 0.3s ease; } .stTabs [aria-selected="true"] { background-color: var(--verde) !important; color: white !important; border: none; box-shadow: 0 4px 10px rgba(32,152,105,0.3); } div[data-testid="stMetric"] { background-color: white; padding: 20px; border-radius: 12px; border-left: 6px solid var(--verde); box-shadow: 0 4px 6px rgba(0,0,0,0.04); } div[data-testid="stAlert"] { background-color: #f2fbf6 !important; border-left: 5px solid var(--verde) !important; color: #333 !important; border-radius: 8px !important; } button[kind="primary"] { background-color: var(--verde) !important; border: none !important; border-radius: 8px !important; font-weight: bold !important; color: white !important; box-shadow: 0 4px 10px rgba(32,152,105,0.4) !important; transition: all 0.3s ease !important; } button[kind="primary"]:hover { background-color: var(--verde-hover) !important; transform: translateY(-2px); }</style>""", unsafe_allow_html=True)
    if "data_mega" not in st.session_state: st.session_state.data_mega = sanitizar_dados_mega({})
    tabs = st.tabs(["📂 1. Banco de Dados", "🧠 2. Cérebro Analítico (IA)", "🤖 3. Geração Autônoma", "📜 4. Fila de Sorteio", "🏆 5. Sincronização"])

    with tabs[0]:
        t_custos, t_premios = st.session_state.data_mega["historico_custos"], st.session_state.data_mega["historico_premios"]
        with st.container(border=True):
            ind1, ind2, ind3 = st.columns(3)
            ind1.metric("📥 Total Investido", f"R$ {t_custos:,.2f}")
            ind2.metric("📤 Total Retornado", f"R$ {t_premios:,.2f}")
            ind3.metric("📊 Balanço do Projeto", f"R$ {t_premios - t_custos:,.2f}")
        c1, c2 = st.columns(2)
        with c1:
            st.file_uploader("📥 Carregar Arquivo Cofre_Mega.json", type="json", key="upl_mega", on_change=cb_carregar_cofre_mega)
            st.download_button("📤 Baixar Backup Consolidado", json.dumps(st.session_state.data_mega), "Cofre_Mega.json", type="primary", use_container_width=True)
        with c2:
            if st.button("🔄 ZERAR ROI MEGA", use_container_width=True): st.session_state.data_mega["historico_custos"] = st.session_state.data_mega["historico_premios"] = 0.0; salvar_dados_mega(st.session_state.data_mega); st.rerun()

    with tabs[1]:
        exibir_mini_painel_financeiro_mega()
        historico_painel = st.session_state.data_mega.get("historico_dados", [])
        if historico_painel:
            ia = raciocinio_total_ia_mega(historico_painel, {})
            if ia: st.info(f"⚡ **LINHA TÁTICA ATIVADA:** {ia['estrategia']}\n\n🎯 **MATRIZ ({ia['qtd_matriz']} Dezenas):** " + ", ".join([f"{n:02d}" for n in ia['matriz_base']]))

    with tabs[2]:
        exibir_mini_painel_financeiro_mega()
        if st.session_state.data_mega["historico_dados"]:
            ia = raciocinio_total_ia_mega(st.session_state.data_mega["historico_dados"], {})
            st.markdown(obter_garantia_megasena(ia['qtd_matriz']), unsafe_allow_html=True)
            garantia_alvo = st.radio("Garantia:", options=[6, 5, 4], horizontal=True)
            jogos_exatos, custo_exato = obter_dados_fechamento_mega(ia['matriz_base'], garantia_alvo)
            st.info(f"📊 Volume Exato Pós-Filtro Elite: {jogos_exatos} Bilhetes | R$ {custo_exato:.2f}")
            if st.button("🧬 GERAR FECHAMENTO ELITE", type="primary", use_container_width=True):
                st.session_state.data_mega["jogos_salvos"] = [j for j in st.session_state.data_mega["jogos_salvos"] if j.get('status') != "Aguardando Sorteio"]
                matriz_reduzida = gerar_fechamento_matematico_mega(tuple(ia['matriz_base']), garantia_alvo)
                for dezenas_jogo in matriz_reduzida:
                    st.session_state.data_mega["jogos_salvos"].append({"id": str(uuid.uuid4()), "concurso_alvo": ia['alvo'], "dezenas": sorted(list(dezenas_jogo)), "tamanho": len(dezenas_jogo), "estrategia": ia['cod_estrategia'], "justificativa": f"Garantia de {garantia_alvo} pts.", "status": "Aguardando Sorteio", "acertos": 0, "premio_valor": 0.0})
                st.session_state.data_mega['historico_custos'] += len(matriz_reduzida) * 5.00; salvar_dados_mega(st.session_state.data_mega); st.rerun()

    with tabs[3]:
        exibir_mini_painel_financeiro_mega()
        col1, col2 = st.columns(2)
        with col1: st.button("🗑️ LIMPAR TODOS", on_click=cb_excluir_todos_mega, use_container_width=True)
        with col2: st.download_button("📤 EXPORTAR RELATÓRIO", data=gerar_pdf_jogos_mega(st.session_state.data_mega["jogos_salvos"]), file_name="MegaSena.pdf", mime="application/pdf", type="primary", use_container_width=True)
        jogos = st.session_state.data_mega.get("jogos_salvos", [])
        for j in jogos[:15]: exibir_card_volante_mega(j, 1)

    with tabs[4]:
        exibir_mini_painel_financeiro_mega()
        if st.button("🔄 Sincronizar Último Sorteio Oficial (Caixa)", type="primary", use_container_width=True):
            try:
                res = requests.get("https://loteriascaixa-api.herokuapp.com/api/megasena/latest", verify=False, timeout=15).json()
                num_c, dez_o = int(res['concurso']), sorted([int(x) for x in res['dezenas']])
                if not any(h['concurso'] == num_c for h in st.session_state.data_mega["historico_dados"]): st.session_state.data_mega["historico_dados"].append({"concurso": num_c, "dezenas": dez_o})
                lucro_total, _ = auditar_e_aprender_unificado_mega(num_c, dez_o, extrair_rateios_api_mega(res.get('premiacoes', [])))
                salvar_dados_mega(st.session_state.data_mega); st.success(f"✅ Atualizado! R$ {lucro_total:.2f}"); st.rerun()
            except Exception as e: st.error(f"Erro API: {e}")
        if st.button("📥 Baixar Base Completa"):
            res_todos = sorted(requests.get("https://loteriascaixa-api.herokuapp.com/api/megasena", verify=False, timeout=60).json(), key=lambda k: int(k['concurso']))
            st.session_state.data_mega["historico_dados"] = [{"concurso": int(r['concurso']), "dezenas": sorted([int(d) for d in r['dezenas']])} for r in res_todos]
            salvar_dados_mega(st.session_state.data_mega); st.success("Download Concluído")
    exibir_rodape()

# --- TELA LOTOMANIA (MÓDULO NOVO E PROFISSIONAL) ---
def tela_lotomania():
    exibir_cabecalho(loteria_especifica="LOTOMANIA PRO", cor_loteria="#F78100", icone_loteria="🍀")
    st.markdown("""<style>:root { --laranja: #F78100; --laranja-hover: #D66D00; } .stApp { background-color: #fffaf4; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; } .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: #ffffff; padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); } .stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 10px 20px; background-color: #fff8f0; border: 1px solid #ffe8cc; transition: all 0.3s ease; } .stTabs [aria-selected="true"] { background-color: var(--laranja) !important; color: white !important; border: none; box-shadow: 0 4px 10px rgba(247,129,0,0.3); } div[data-testid="stMetric"] { background-color: white; padding: 20px; border-radius: 12px; border-left: 6px solid var(--laranja); box-shadow: 0 4px 6px rgba(0,0,0,0.04); } div[data-testid="stAlert"] { background-color: #fff8f0 !important; border-left: 5px solid var(--laranja) !important; color: #333 !important; border-radius: 8px !important; } button[kind="primary"] { background-color: var(--laranja) !important; border: none !important; border-radius: 8px !important; font-weight: bold !important; color: white !important; box-shadow: 0 4px 10px rgba(247,129,0,0.4) !important; transition: all 0.3s ease !important; } button[kind="primary"]:hover { background-color: var(--laranja-hover) !important; transform: translateY(-2px); }</style>""", unsafe_allow_html=True)
    
    if "data_loto_mania" not in st.session_state: st.session_state.data_loto_mania = sanitizar_dados_lotomania({})
    tabs = st.tabs(["📂 1. Banco de Dados", "🧠 2. Cérebro Analítico (IA)", "🤖 3. Geração Autônoma", "📜 4. Fila de Sorteio", "🏆 5. Sincronização"])

    with tabs[0]:
        t_custos, t_premios = st.session_state.data_loto_mania["historico_custos"], st.session_state.data_loto_mania["historico_premios"]
        with st.container(border=True):
            ind1, ind2, ind3 = st.columns(3)
            ind1.metric("📥 Total Investido", f"R$ {t_custos:,.2f}")
            ind2.metric("📤 Total Retornado", f"R$ {t_premios:,.2f}")
            ind3.metric("📊 Balanço do Projeto", f"R$ {t_premios - t_custos:,.2f}")
        c1, c2 = st.columns(2)
        with c1:
            st.file_uploader("📥 Carregar Arquivo Cofre_Lotomania.json", type="json", key="upl_lotomania", on_change=cb_carregar_cofre_lotomania)
            st.download_button("📤 Baixar Backup Consolidado", json.dumps(st.session_state.data_loto_mania), "Cofre_Lotomania.json", type="primary", use_container_width=True)
        with c2:
            if st.button("🔄 ZERAR ROI LOTOMANIA", use_container_width=True): st.session_state.data_loto_mania["historico_custos"] = st.session_state.data_loto_mania["historico_premios"] = 0.0; salvar_dados_lotomania(st.session_state.data_loto_mania); st.rerun()

    with tabs[1]:
        exibir_mini_painel_financeiro_lotomania()
        historico_painel = st.session_state.data_loto_mania.get("historico_dados", [])
        if historico_painel:
            ranking_dezenas = analisar_frequencia_lotomania(historico_painel)
            top_70 = [par[0] for par in ranking_dezenas[:70]]
            zona_morta = [par[0] for par in ranking_dezenas[-50:]]
            
            st.info(f"⚡ **INTELIGÊNCIA LOTOMANIA ATIVADA**\nA máquina mapeou {len(historico_painel)} concursos da Caixa para identificar o Ponto de Fervura térmico de cada uma das 100 dezenas.")
            
            col_boas, col_ruins = st.columns(2)
            with col_boas:
                st.markdown("#### 🎯 SUPER MATRIZ (Top 70 Dezenas)")
                st.write(", ".join([f"{n:02d}" for n in sorted(top_70)]))
            with col_ruins:
                st.markdown("#### 🪞 ZONA MORTA (As 50 Piores)")
                st.write(", ".join([f"{n:02d}" for n in sorted(zona_morta)]))

    with tabs[2]:
        exibir_mini_painel_financeiro_lotomania()
        if st.session_state.data_loto_mania["historico_dados"]:
            historico = st.session_state.data_loto_mania["historico_dados"]
            ranking_dezenas = analisar_frequencia_lotomania(historico)
            
            st.markdown("""
            <div style='background-color: #fff8f0; border-left: 5px solid #F78100; padding: 15px; border-radius: 5px; margin-bottom: 20px;'>
                <h4 style='color: #F78100; margin-top: 0;'>🔒 MOTOR HEURÍSTICO - LOTOMANIA</h4>
                <p style='color: #444;'>Escolha o seu vetor de ataque. A máquina usará Monte Carlo com Filtro da Curva de Gauss (2100 a 2800) e Espalhamento Geométrico para as super matrizes.</p>
            </div>
            """, unsafe_allow_html=True)
            
            estrategia_alvo = st.radio("Selecione a Estratégia de Combate:", options=["Super Matriz (Foco em Acertar 20)", "Espelho Reverso (Foco em Errar Tudo - 0 Acertos)"])
            
            if "Super Matriz" in estrategia_alvo:
                qtd_jogos = st.slider("Quantidade de Bilhetes de 50 Números:", min_value=1, max_value=50, value=5)
                st.info(f"📊 Volume Estocástico: {qtd_jogos} Bilhetes | 💸 Investimento: R$ {qtd_jogos * 3.00:.2f}")
                if st.button("🧬 GERAR SUPER MATRIZ COM MONTE CARLO", type="primary", use_container_width=True):
                    st.session_state.data_loto_mania["jogos_salvos"] = [j for j in st.session_state.data_loto_mania["jogos_salvos"] if j.get('status') != "Aguardando Sorteio"]
                    top_70 = [par[0] for par in ranking_dezenas[:70]]
                    matriz_reduzida = gerar_estrategia_super_matriz(top_70, qtd_jogos)
                    alvo = (historico[-1]['concurso'] + 1) if historico else 1
                    for dezenas_jogo in matriz_reduzida:
                        st.session_state.data_loto_mania["jogos_salvos"].append({"id": str(uuid.uuid4()), "concurso_alvo": alvo, "dezenas": sorted(list(dezenas_jogo)), "tamanho": 50, "estrategia": "Super Matriz (Top 70)", "justificativa": "Gauss e Quadrantes Validados", "status": "Aguardando Sorteio", "acertos": 0, "premio_valor": 0.0})
                    st.session_state.data_loto_mania['historico_custos'] += len(matriz_reduzida) * 3.00; salvar_dados_lotomania(st.session_state.data_loto_mania); st.rerun()
            else:
                st.warning("⚠️ **ATENÇÃO:** O sistema selecionará as 50 piores dezenas. Você DEVE registrar o bilhete na lotérica e marcar a opção **APOSTA ESPELHO** no volante.")
                if st.button("🪞 GERAR BILHETE TÓXICO PARA ESPELHO", type="primary", use_container_width=True):
                    st.session_state.data_loto_mania["jogos_salvos"] = [j for j in st.session_state.data_loto_mania["jogos_salvos"] if j.get('status') != "Aguardando Sorteio"]
                    piores_50 = [par[0] for par in ranking_dezenas[-50:]]
                    alvo = (historico[-1]['concurso'] + 1) if historico else 1
                    st.session_state.data_loto_mania["jogos_salvos"].append({"id": str(uuid.uuid4()), "concurso_alvo": alvo, "dezenas": sorted(piores_50), "tamanho": 50, "estrategia": "Ataque Espelho (Acerto Zero)", "justificativa": "⚠️ MARQUE APOSTA ESPELHO NO VOLANTE!", "status": "Aguardando Sorteio", "acertos": 0, "premio_valor": 0.0})
                    st.session_state.data_loto_mania['historico_custos'] += 6.00; salvar_dados_lotomania(st.session_state.data_loto_mania); st.rerun()

    with tabs[3]:
        exibir_mini_painel_financeiro_lotomania()
        col1, col2 = st.columns(2)
        with col1: st.button("🗑️ LIMPAR TODOS", on_click=cb_excluir_todos_lotomania, use_container_width=True)
        with col2: st.download_button("📤 EXPORTAR RELATÓRIO (PDF 10x10)", data=gerar_pdf_jogos_lotomania(st.session_state.data_loto_mania["jogos_salvos"]), file_name="Lotomania.pdf", mime="application/pdf", type="primary", use_container_width=True)
        jogos = st.session_state.data_loto_mania.get("jogos_salvos", [])
        if jogos:
            cols = st.columns(3)
            for idx, j in enumerate(jogos[:15]): 
                with cols[idx % 3]: exibir_card_volante_lotomania(j, idx + 1)

    with tabs[4]:
        exibir_mini_painel_financeiro_lotomania()
        if st.button("🔄 Sincronizar Último Sorteio Oficial (Caixa)", type="primary", use_container_width=True):
            try:
                res = requests.get("https://loteriascaixa-api.herokuapp.com/api/lotomania/latest", verify=False, timeout=15).json()
                num_c, dez_o = int(res['concurso']), [int(x) for x in res['dezenas']]
                if not any(h['concurso'] == num_c for h in st.session_state.data_loto_mania["historico_dados"]): st.session_state.data_loto_mania["historico_dados"].append({"concurso": num_c, "dezenas": dez_o})
                lucro_total, _ = auditar_e_aprender_lotomania(num_c, dez_o, extrair_rateios_api_lotomania(res.get('premiacoes', [])))
                salvar_dados_lotomania(st.session_state.data_loto_mania); st.success(f"✅ Atualizado! Prêmios Auditados: R$ {lucro_total:.2f}"); st.rerun()
            except Exception as e: st.error(f"Erro API: {e}")
        if st.button("📥 Baixar Base Completa da Lotomania"):
            res_todos = sorted(requests.get("https://loteriascaixa-api.herokuapp.com/api/lotomania", verify=False, timeout=60).json(), key=lambda k: int(k['concurso']))
            st.session_state.data_loto_mania["historico_dados"] = [{"concurso": int(r['concurso']), "dezenas": sorted([int(d) for d in r['dezenas']])} for r in res_todos]
            salvar_dados_lotomania(st.session_state.data_loto_mania); st.success("Download Concluído")

    exibir_rodape()

# =====================================================================
# 7. INICIALIZAÇÃO DO ROTEADOR
# =====================================================================
if st.session_state.pagina_atual == "login":
    tela_login()
elif st.session_state.pagina_atual == "lobby" and st.session_state.autenticado:
    tela_lobby()
elif st.session_state.pagina_atual == "lotofacil" and st.session_state.autenticado:
    tela_lotofacil()
elif st.session_state.pagina_atual == "megasena" and st.session_state.autenticado:
    tela_megasena()
elif st.session_state.pagina_atual == "lotomania" and st.session_state.autenticado:
    tela_lotomania()
else:
    st.session_state.pagina_atual = "login"
    st.session_state.autenticado = False
    st.rerun()
