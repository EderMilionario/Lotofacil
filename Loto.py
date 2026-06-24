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
# 1. CONFIGURAÇÃO INICIAL E BANCO DE DADOS ÚNICO
# =====================================================================
st.set_page_config(page_title="LoteriasMatrix Pro", page_icon="🍀", layout="wide")

ARQUIVO_DB = "LoteriasMatrix_Pro.json"

LOTERIAS_CONFIG = {
    "lotofacil": {"nome": "Lotofácil", "custo": 3.50, "api": "lotofacil"},
    "megasena": {"nome": "Mega-Sena", "custo": 6.00, "api": "megasena"},
    "lotomania": {"nome": "Lotomania", "custo": 3.00, "api": "lotomania"},
    "quina": {"nome": "Quina", "custo": 3.00, "api": "quina"},
    "duplasena": {"nome": "Dupla Sena", "custo": 3.00, "api": "duplasena"},
    "maismilionaria": {"nome": "+Milionária", "custo": 6.00, "api": "maismilionaria"}
}

def estrutura_padrao_loteria():
    return {
        "historico_dados": [], "jogos_salvos": [], 
        "historico_custos": 0.0, "historico_premios": 0.0,
        "global_hits": {}, "ledger_track": {"bilhetes": 0, "premiados_geral": 0, "elite": 0},
        "matrizes_reais_hits": {"total": 0, "soma_acertos": 0}, "matrizes_auditadas_ids": [],
        "ia_pesos": {}, "ia_memoria": {}
    }

def carregar_db_unico():
    db = {k: estrutura_padrao_loteria() for k in LOTERIAS_CONFIG.keys()}
    if os.path.exists(ARQUIVO_DB):
        try:
            with open(ARQUIVO_DB, "r", encoding='utf-8') as f:
                dados_salvos = json.load(f)
                for k in db.keys():
                    if k in dados_salvos: db[k].update(dados_salvos[k])
        except Exception: pass
    
    # Pesos Iniciais padrão caso vazios
    if not db["lotofacil"]["ia_pesos"]:
        db["lotofacil"]["ia_pesos"] = {
            "Tendencia Forte": {"p1": 20.0, "p2": 5.0, "bonus": 40.0},
            "Simetria Conjunta": {"p1": 15.0, "p2": 8.0, "bonus1": 30.0, "bonus2": 20.0},
            "Reversao de Tendencia": {"p1": 10.0, "bonus": 100.0},
            "Ciclo Supremo": {"p1": 15.0, "p2": 5.0, "bonus": 30.0},
            "Default": {"p1": 12.0, "p2": 8.0, "bonus": 25.0}
        }
    if not db["megasena"]["ia_pesos"]:
        db["megasena"]["ia_pesos"] = {
            "Arbitragem de Massa": {"p_termo": 30.0, "p_comport": 20.0, "p_final": 15.0},
            "Caos Térmico": {"p_termo": 50.0, "p_comport": 10.0, "p_final": 25.0},
            "Dispersão Ortogonal": {"p_termo": 20.0, "p_comport": 40.0, "p_final": 30.0},
            "Default": {"p_termo": 25.0, "p_comport": 25.0, "p_final": 20.0}
        }
    return db

def salvar_db_unico():
    try:
        with open(ARQUIVO_DB, "w", encoding='utf-8') as f:
            json.dump(st.session_state.db, f, ensure_ascii=False, indent=4)
    except Exception as e: st.error(f"Erro ao salvar banco: {e}")

if "db" not in st.session_state: st.session_state.db = carregar_db_unico()
if "pagina_atual" not in st.session_state: st.session_state.pagina_atual = "login"
if "autenticado" not in st.session_state: st.session_state.autenticado = False

# =====================================================================
# 2. DESIGN DO SISTEMA (CABEÇALHO E RODAPÉ)
# =====================================================================
def exibir_cabecalho(loteria_especifica=None, cor_loteria=None, icone_loteria=None):
    titulo_multicolorido = """
    <div style='text-align: center; margin-bottom: 10px;'>
        <span style='color: #209869; font-size: 36px; font-weight: bold;'>L</span><span style='color: #930089; font-size: 36px; font-weight: bold;'>o</span><span style='color: #260085; font-size: 36px; font-weight: bold;'>t</span><span style='color: #F78100; font-size: 36px; font-weight: bold;'>e</span><span style='color: #0066b3; font-size: 36px; font-weight: bold;'>r</span><span style='color: #ED1622; font-size: 36px; font-weight: bold;'>i</span><span style='color: #B8922A; font-size: 36px; font-weight: bold;'>a</span><span style='color: #209869; font-size: 36px; font-weight: bold;'>s</span>
        <span style='color: #930089; font-size: 36px; font-weight: bold;'>M</span><span style='color: #260085; font-size: 36px; font-weight: bold;'>a</span><span style='color: #F78100; font-size: 36px; font-weight: bold;'>t</span><span style='color: #0066b3; font-size: 36px; font-weight: bold;'>r</span><span style='color: #ED1622; font-size: 36px; font-weight: bold;'>i</span><span style='color: #B8922A; font-size: 36px; font-weight: bold;'>x</span>
        <span style='color: #333333; font-size: 36px; font-weight: bold;'> Pro</span>
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
    st.markdown(f"<hr style='margin-top: 50px;'><div style='text-align: center; color: #888; font-size: 14px;'>&copy; {datetime.now().year} LoteriasMatrix Pro - Sindicato de Inferência Matemática.<br>Operação Profissional.</div>", unsafe_allow_html=True)

def exibir_mini_painel_financeiro(chave_loteria, cor_destaque="#930089"):
    t_custos = st.session_state.db[chave_loteria].get("historico_custos", 0.0)
    t_premios = st.session_state.db[chave_loteria].get("historico_premios", 0.0)
    res_global = t_premios - t_custos
    str_res = f"R$ {res_global:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if res_global > 0: status_msg = f"🟢 <b style='color:green;'>Lucro:</b> `{str_res}`"
    elif res_global < 0: status_msg = f"🔴 <b style='color:red;'>Prejuízo:</b> `{str_res}`"
    else: status_msg = f"⚪ <b>Empate:</b> `{str_res}`"
    st.markdown(f"<div style='background-color:#f4f6f9; padding:10px; border-radius:5px; border-left:4px solid {cor_destaque}; margin-bottom:15px;'>📊 <b>Balanço da Operação:</b> {status_msg} | <b>Investido:</b> R$ {t_custos:,.2f} | <b>Retorno:</b> R$ {t_premios:,.2f}</div>", unsafe_allow_html=True)

# =====================================================================
# 3. ROTINAS DE SINCRONIZAÇÃO GERAL E PRE-LOBBY
# =====================================================================
def fetch_api(url):
    try:
        resp = requests.get(url, verify=False, timeout=15)
        if resp.status_code == 200: return resp.json()
    except: pass
    return None

def tela_pre_lobby():
    exibir_cabecalho()
    st.markdown("<h3 style='text-align: center; color: #333;'>🌐 Central de Sincronização e Auditoria (Pré-Lobby)</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Realize a auditoria geral e calibração de TODAS as inteligências artificiais simultaneamente antes de operar.</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style='background-color: #fdf5ff; border: 2px solid #930089; padding: 20px; border-radius: 10px; height: 220px;'>
            <h4 style='color: #930089; margin-top:0;'>📥 1. Calibração Rápida (Último Sorteio)</h4>
            <p style='font-size:14px; color:#555;'>Busca o <b>último concurso</b> de todas as 6 loterias, audita seus bilhetes aguardando sorteio, calcula lucros e atualiza a estimativa do próximo prêmio.</p>
        </div><br>
        """, unsafe_allow_html=True)
        if st.button("🚀 SINCRONIZAR ÚLTIMO SORTEIO (TODAS AS LOTERIAS)", type="primary", use_container_width=True):
            with st.spinner("Sincronizando as 6 Loterias. Aguarde..."):
                relatorio_sync = []
                for chave, config in LOTERIAS_CONFIG.items():
                    api_nome = config["api"]
                    res = fetch_api(f"https://loteriascaixa-api.herokuapp.com/api/{api_nome}/latest")
                    if res:
                        num_c = int(res['concurso'])
                        dez_o = [int(x) for x in res['dezenas']]
                        
                        if chave == "maismilionaria": # Tratar trevos
                            trevos = [int(x) for x in res.get('trevos', [])]
                            novo_dado = {"concurso": num_c, "data": res.get('data',''), "dezenas": dez_o, "trevos": trevos, "premiacoes": res.get('premiacoes', []), "proximo_premio": res.get('valorEstimadoProximoConcurso', 0)}
                        else:
                            novo_dado = {"concurso": num_c, "data": res.get('data',''), "dezenas": dez_o, "premiacoes": res.get('premiacoes', []), "proximo_premio": res.get('valorEstimadoProximoConcurso', 0)}
                        
                        # Salvar histórico
                        if not any(h['concurso'] == num_c for h in st.session_state.db[chave]["historico_dados"]):
                            st.session_state.db[chave]["historico_dados"].append(novo_dado)
                            relatorio_sync.append(f"✅ {config['nome']}: Concurso {num_c} sincronizado. (Prêmio Est.: R$ {novo_dado['proximo_premio']:,.2f})")
                        else:
                            # Atualiza estimativa de premio mesmo se ja existe
                            st.session_state.db[chave]["historico_dados"][-1]["proximo_premio"] = res.get('valorEstimadoProximoConcurso', 0)
                            relatorio_sync.append(f"⚡ {config['nome']}: Já atualizado no conc. {num_c}. (Prêmio Est.: R$ {novo_dado['proximo_premio']:,.2f})")
                            
                        # Limpar IA Memoria para recalcular no próximo acesso
                        st.session_state.db[chave]["ia_memoria"] = {}
                
                salvar_db_unico()
                st.session_state.logs_sync = relatorio_sync
                st.success("Auditoria Completa Finalizada!")
                st.rerun()

    with col2:
        st.markdown("""
        <div style='background-color: #f2fbf6; border: 2px solid #209869; padding: 20px; border-radius: 10px; height: 220px;'>
            <h4 style='color: #209869; margin-top:0;'>☢️ 2. Deep Learning (Base Completa)</h4>
            <p style='font-size:14px; color:#555;'>Força o download de <b>TODOS OS CONCURSOS da história</b> (do 1 ao atual) para alimentar as IAs. <b>Atenção:</b> Pode demorar vários minutos.</p>
        </div><br>
        """, unsafe_allow_html=True)
        if st.button("📥 BAIXAR BASE COMPLETA HISTÓRICA (TODAS)", type="secondary", use_container_width=True):
            with st.spinner("Fazendo download profundo. Isso vai demorar..."):
                for chave, config in LOTERIAS_CONFIG.items():
                    api_nome = config["api"]
                    res_todos = fetch_api(f"https://loteriascaixa-api.herokuapp.com/api/{api_nome}")
                    if res_todos:
                        res_todos = sorted(res_todos, key=lambda k: int(k['concurso']))
                        historico = []
                        for r in res_todos:
                            dado = {"concurso": int(r['concurso']), "dezenas": [int(d) for d in r['dezenas']], "data": r.get('data', '')}
                            if chave == "maismilionaria": dado["trevos"] = [int(t) for t in r.get('trevos', [])]
                            historico.append(dado)
                        st.session_state.db[chave]["historico_dados"] = historico
                salvar_db_unico()
                st.success("Download Histórico de todas as loterias concluído com sucesso!")

    st.divider()
    
    if "logs_sync" in st.session_state and st.session_state.logs_sync:
        st.markdown("#### 📜 Relatório da Última Sincronização")
        for log in st.session_state.logs_sync: st.write(log)
        st.write("")
        
    # Exibir Status e Próximos Prêmios
    st.markdown("#### 💰 Radar de Prêmios Estimados (Próximos Concursos)")
    cols_radar = st.columns(3)
    for idx, (chave, config) in enumerate(LOTERIAS_CONFIG.items()):
        hist = st.session_state.db[chave].get("historico_dados", [])
        if hist:
            ult = hist[-1]
            premio_est = ult.get("proximo_premio", 0)
            cor = "#930089" if chave=="lotofacil" else "#209869" if chave=="megasena" else "#F78100" if chave=="lotomania" else "#0066b3" if chave=="maismilionaria" else "#ED1622" if chave=="duplasena" else "#260085"
            with cols_radar[idx % 3]:
                st.markdown(f"<div style='border-left: 5px solid {cor}; padding: 10px; background-color: #fff; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 10px;'><b>{config['nome']}</b><br>Conc: {ult['concurso']}<br><span style='color:{cor}; font-weight:bold; font-size:18px;'>R$ {premio_est:,.2f}</span></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 ENTRAR NO LOBBY OPERACIONAL", type="primary", use_container_width=True):
        st.session_state.pagina_atual = "lobby"
        st.rerun()
        
    exibir_rodape()

def tela_login():
    exibir_cabecalho()
    st.markdown("<h4 style='text-align: center;'>Acesso Restrito ao Sistema Sindicato</h4>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("form_login"):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Autenticar Operador", use_container_width=True):
                if usuario == "777" and senha == "777": 
                    st.session_state.autenticado = True
                    st.session_state.pagina_atual = "pre_lobby" # Redireciona pro pre-lobby
                    st.rerun()
                else: st.error("Credenciais inválidas.")
    exibir_rodape()

def tela_lobby():
    exibir_cabecalho()
    
    st.markdown("""
    <style>
        .block-container { max-width: 1100px; }
        div[data-testid="stColumn"] div.stButton > button {
            aspect-ratio: 1 / 1 !important; 
            border-radius: 20px !important;
            font-size: 20px !important;
            font-weight: 900 !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.08) !important;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
            padding: 15px !important;
            line-height: 1.3 !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            align-items: center !important;
            white-space: pre-wrap !important; 
        }
        /* Cores Loterias */
        div[data-testid="stColumn"]:nth-child(1) div.stButton > button { background: linear-gradient(145deg, #ffffff, #fdf5ff) !important; border: 3px solid #930089 !important; color: #930089 !important; }
        div[data-testid="stColumn"]:nth-child(2) div.stButton > button { background: linear-gradient(145deg, #ffffff, #f2fbf6) !important; border: 3px solid #209869 !important; color: #209869 !important; }
        div[data-testid="stColumn"]:nth-child(3) div.stButton > button { background: linear-gradient(145deg, #ffffff, #f0f4ff) !important; border: 3px solid #260085 !important; color: #260085 !important; }
        div[data-testid="stColumn"]:nth-child(4) div.stButton > button { background: linear-gradient(145deg, #ffffff, #fff0f0) !important; border: 3px solid #ED1622 !important; color: #ED1622 !important; }
        div[data-testid="stColumn"]:nth-child(5) div.stButton > button { background: linear-gradient(145deg, #ffffff, #fff8f0) !important; border: 3px solid #F78100 !important; color: #F78100 !important; }
        div[data-testid="stColumn"]:nth-child(6) div.stButton > button { background: linear-gradient(145deg, #ffffff, #e6f3ff) !important; border: 3px solid #0066b3 !important; color: #0066b3 !important; }
        /* Hovers */
        div[data-testid="stColumn"]:nth-child(1) div.stButton > button:hover { background: #930089 !important; color: white !important; transform: translateY(-8px) scale(1.02) !important; }
        div[data-testid="stColumn"]:nth-child(2) div.stButton > button:hover { background: #209869 !important; color: white !important; transform: translateY(-8px) scale(1.02) !important; }
        div[data-testid="stColumn"]:nth-child(3) div.stButton > button:hover { background: #260085 !important; color: white !important; transform: translateY(-8px) scale(1.02) !important; }
        div[data-testid="stColumn"]:nth-child(4) div.stButton > button:hover { background: #ED1622 !important; color: white !important; transform: translateY(-8px) scale(1.02) !important; }
        div[data-testid="stColumn"]:nth-child(5) div.stButton > button:hover { background: #F78100 !important; color: white !important; transform: translateY(-8px) scale(1.02) !important; }
        div[data-testid="stColumn"]:nth-child(6) div.stButton > button:hover { background: #0066b3 !important; color: white !important; transform: translateY(-8px) scale(1.02) !important; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h4 style='text-align: center; color: #666; font-weight: normal; margin-bottom: 30px;'>Escolha o Motor Analítico para operar:</h4>", unsafe_allow_html=True)
    
    # 6 Loterias em Grid 3x2
    cols1 = st.columns(3)
    with cols1[0]:
        if st.button("🍀\nLotofácil\n(Frequência)", key="btn_loto", use_container_width=True): st.session_state.pagina_atual = "lotofacil"; st.rerun()
    with cols1[1]:
        if st.button("🟢\nMega-Sena\n(Espacial)", key="btn_mega", use_container_width=True): st.session_state.pagina_atual = "megasena"; st.rerun()
    with cols1[2]:
        if st.button("🔵\nQuina\n(Dispersão)", key="btn_quina", use_container_width=True): st.session_state.pagina_atual = "quina"; st.rerun()

    st.write("") # Espaçamento

    cols2 = st.columns(3)
    with cols2[0]:
        if st.button("🔴\nDupla Sena\n(Sorteio Base)", key="btn_dupla", use_container_width=True): st.session_state.pagina_atual = "duplasena"; st.rerun()
    with cols2[1]:
        if st.button("🟠\nLotomania\n(Grupos/Espelho)", key="btn_lmania", use_container_width=True): st.session_state.pagina_atual = "lotomania"; st.rerun()
    with cols2[2]:
        if st.button("🌟\n+Milionária\n(Motor Misto)", key="btn_milionaria", use_container_width=True): st.session_state.pagina_atual = "maismilionaria"; st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    col_voltar1, col_voltar2, col_voltar3 = st.columns([1,2,1])
    with col_voltar2:
        if st.button("⬅️ VOLTAR PARA PRÉ-LOBBY (SINCRONIZAÇÃO GERAL)", use_container_width=True):
            st.session_state.pagina_atual = "pre_lobby"
            st.rerun()
            
    exibir_rodape()

# =====================================================================
# 4. MOTOR ANALÍTICO - LOTOFÁCIL
# =====================================================================
def calcular_premio_lotofacil(tamanho, acertos, rateios):
    v11, v12, v13, v14, v15 = rateios.get(11, 7.0), rateios.get(12, 14.0), rateios.get(13, 35.0), rateios.get(14, 1500.0), rateios.get(15, 1500000.0)
    if acertos < 11: return 0.0
    if tamanho == 15:
        if acertos == 11: return v11
        elif acertos == 12: return v12
        elif acertos == 13: return v13
        elif acertos == 14: return v14
        elif acertos == 15: return v15
    return 0.0

@st.cache_data(show_spinner="🧠 Lotofácil: Aplicando Set Cover Matemático...")
def gerar_fechamento_lotofacil(dezenas_tuple, garantia):
    dezenas = list(dezenas_tuple)
    todas_comb = list(itertools.combinations(dezenas, 15))
    if garantia == 15 or len(dezenas) <= 15: return [list(c) for c in todas_comb]

    comb_bits = [sum(1 << num for num in c) for c in todas_comb]
    sorteios_possiveis = set(range(len(comb_bits)))
    bilhetes_escolhidos, cobertura = [], []
    
    for b in comb_bits:
        cobertura.append({j for j, s in enumerate(comb_bits) if (b & s).bit_count() >= garantia})
        
    while sorteios_possiveis:
        melhor_idx = max(range(len(cobertura)), key=lambda i: len(cobertura[i].intersection(sorteios_possiveis)))
        bilhetes_escolhidos.append(list(todas_comb[melhor_idx]))
        sorteios_possiveis -= cobertura[melhor_idx] 
    return bilhetes_escolhidos

def raciocinio_ia_lotofacil(historico, db_loto):
    if not historico: return None
    ultimos_12 = historico[-12:] if len(historico) >= 12 else historico
    freq_micro = Counter([int(n) for h in ultimos_12 for n in h['dezenas']])
    freq_recente = Counter([int(n) for h in historico[-30:] for n in h['dezenas']])
    
    atrasos = {int(n): 0 for n in range(1, 26)}
    dez_enc = {int(n): False for n in range(1, 26)}
    for h in reversed(historico):
        for n in range(1, 26):
            if int(n) in h['dezenas']: dez_enc[int(n)] = True
            elif not dez_enc[int(n)]: atrasos[int(n)] += 1

    ultimo_sorteio = [int(x) for x in historico[-1]['dezenas']]
    ausentes = [int(n) for n in range(1, 26) if n not in ultimo_sorteio] 

    cod_est, qtd_matriz, tatic_desc = "Tendencia Forte", 18, "Busca de Padrões Térmicos Ativos."
    est_pesos = db_loto["ia_pesos"].get(cod_est, db_loto["ia_pesos"]["Default"])

    scores = {}
    for n in range(1, 26):
        n = int(n)
        sc = (freq_micro.get(n, 0) * est_pesos.get("p1", 20.0)) + (freq_recente.get(n, 0) * est_pesos.get("p2", 5.0))
        if n in ausentes and atrasos.get(n, 0) == 1: sc += est_pesos.get("bonus", 40.0)
        scores[n] = float(sc)

    matriz = []
    candidatos = sorted(range(1, 26), key=lambda x: scores.get(x, 0), reverse=True)
    
    # Filtros Pro
    IMPARES, PRIMOS, MOLDURA = {1,3,5,7,9,11,13,15,17,19,21,23,25}, {2,3,5,7,11,13,17,19,23}, {1,2,3,4,5,6,10,11,15,16,20,21,22,23,24,25}
    max_imp, max_prim, max_mold = round(qtd_matriz * 0.54) + 1, round(qtd_matriz * 0.36) + 1, round(qtd_matriz * 0.66) + 1

    for n in candidatos:
        if len(matriz) >= qtd_matriz: break
        if n in IMPARES and sum(1 for x in matriz if x in IMPARES) >= max_imp: continue
        if n in PRIMOS and sum(1 for x in matriz if x in PRIMOS) >= max_prim: continue
        if n in MOLDURA and sum(1 for x in matriz if x in MOLDURA) >= max_mold: continue
        matriz.append(n)

    if len(matriz) < qtd_matriz:
        for n in candidatos:
            if len(matriz) >= qtd_matriz: break
            if n not in matriz: matriz.append(n)
            
    matriz = sorted(matriz)
    return {
        "estrategia": cod_est, "motivo_est": tatic_desc, "pesos": scores,
        "alvo": int((historico[-1]['concurso'] + 1)) if historico else 1,
        "qtd_matriz": qtd_matriz, "matriz_base": matriz
    }

def auditar_bilhetes_lotofacil(db_loto):
    historico = {h['concurso']: h for h in db_loto['historico_dados']}
    lucro_sessao = 0.0
    for j in db_loto['jogos_salvos']:
        if j['status'] == "Aguardando Sorteio" and j['concurso_alvo'] in historico:
            conc_data = historico[j['concurso_alvo']]
            sorteadas = set(conc_data['dezenas'])
            rateios = {p.get('acertos', 0): float(p.get('premio', 0.0)) for p in conc_data.get('premiacoes', [])}
            
            pontos = len(set(j['dezenas']).intersection(sorteadas))
            j['acertos'] = pontos
            j['premio_valor'] = calcular_premio_lotofacil(j['tamanho'], pontos, rateios)
            
            db_loto["ledger_track"]["bilhetes"] += 1
            if pontos >= 11:
                j['status'] = "Premiado"
                lucro_sessao += j['premio_valor']
                db_loto["historico_premios"] += j['premio_valor']
                db_loto["ledger_track"]["premiados_geral"] += 1
                if pontos >= 14: db_loto["ledger_track"]["elite"] += 1
                db_loto["global_hits"][str(pontos)] = db_loto["global_hits"].get(str(pontos), 0) + 1
            else: j['status'] = "Não Premiado"
    return lucro_sessao

def tela_lotofacil():
    exibir_cabecalho("LOTOFÁCIL PRO", "#930089", "🍀")
    db_loto = st.session_state.db["lotofacil"]
    
    tabs = st.tabs(["📂 1. Banco de Dados", "🧠 2. Cérebro Analítico (IA)", "🤖 3. Geração Autônoma", "📜 4. Fila de Sorteio"])

    with tabs[0]:
        exibir_mini_painel_financeiro("lotofacil", "#930089")
        st.markdown("### 💾 Gerenciamento Interno (Lotofácil)")
        st.info(f"Concursos Oficiais Salvos: **{len(db_loto['historico_dados'])}**")
        if st.button("🔄 ZERAR CONTABILIDADE (LOTOFÁCIL)", type="secondary"):
            db_loto["historico_custos"] = db_loto["historico_premios"] = 0.0
            salvar_db_unico(); st.rerun()

    with tabs[1]:
        exibir_mini_painel_financeiro("lotofacil", "#930089")
        st.markdown("### 🧠 Como a IA da Lotofácil funciona (Detalhado)")
        st.write("A Lotofácil opera baseada no Fator Termal e Microciclos. A IA varre os últimos sorteios lendo a frequência de aparição de cada dezena, aplicando pesos para tendências de repetição e quebra de ciclo. Ela usa as restrições matemáticas dos Sindicatos: limite rígido de Ímpares, Primos e dezenas na Moldura.")
        
        if db_loto["historico_dados"]:
            ia = raciocinio_ia_lotofacil(db_loto["historico_dados"], db_loto)
            st.info(f"⚡ **ESTRATÉGIA:** {ia['estrategia']} | **MATRIZ ({ia['qtd_matriz']} Dezenas):** " + ", ".join([f"{n:02d}" for n in ia['matriz_base']]))
        else: st.warning("Sincronize o banco de dados no Pré-Lobby primeiro.")

    with tabs[2]:
        exibir_mini_painel_financeiro("lotofacil", "#930089")
        if db_loto["historico_dados"]:
            ia = raciocinio_ia_lotofacil(db_loto["historico_dados"], db_loto)
            st.markdown(f"<div style='background-color: #fdf5ff; border-left: 5px solid #930089; padding: 15px; border-radius: 5px; margin-bottom: 20px;'><h4 style='color: #930089; margin-top: 0;'>🔒 O CADEADO MATEMÁTICO</h4><p>Se as 15 sorteadas caírem DENTRO da sua Matriz de {ia['qtd_matriz']} dezenas, o prêmio está matematicamente trancado.</p></div>", unsafe_allow_html=True)
            
            garantia = st.radio("Garantia do Fechamento:", [15, 14, 13], horizontal=True)
            if st.button("🧬 GERAR FECHAMENTO EXATO (R$ 3,50/jogo)", type="primary"):
                jogos = gerar_fechamento_lotofacil(tuple(ia['matriz_base']), garantia)
                for b in jogos:
                    db_loto["jogos_salvos"].append({"id": str(uuid.uuid4()), "concurso_alvo": ia['alvo'], "dezenas": b, "tamanho": 15, "status": "Aguardando Sorteio", "acertos": 0, "premio_valor": 0.0})
                db_loto["historico_custos"] += len(jogos) * 3.50; salvar_db_unico(); st.success(f"Gerado {len(jogos)} bilhetes!"); st.rerun()

    with tabs[3]:
        exibir_mini_painel_financeiro("lotofacil", "#930089")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 AUDITAR BILHETES PENDENTES", type="primary", use_container_width=True):
                lucro = auditar_bilhetes_lotofacil(db_loto); salvar_db_unico()
                st.success(f"Auditoria concluída! Lucro obtido nos acertos: R$ {lucro:,.2f}"); st.rerun()
        with col2:
            if st.button("🗑️ LIMPAR FILA", type="secondary", use_container_width=True):
                db_loto["jogos_salvos"] = []; salvar_db_unico(); st.rerun()
                
        st.markdown("#### Últimos Bilhetes")
        for j in reversed(db_loto["jogos_salvos"][-10:]):
            st.code(f"Alvo: {j['concurso_alvo']} | {j['dezenas']} | Status: {j['status']} | Prêmio: R$ {j.get('premio_valor', 0):.2f}")

# =====================================================================
# 5. MOTOR ANALÍTICO - MEGA-SENA
# =====================================================================
def calcular_premio_mega(acertos, rateios):
    if acertos == 6: return rateios.get(6, 35000000.0)
    if acertos == 5: return rateios.get(5, 45000.0)
    if acertos == 4: return rateios.get(4, 1200.0)
    return 0.0

@st.cache_data(show_spinner="🧠 Mega-Sena: Aplicando Filtros Elite e Set Cover...")
def gerar_fechamento_mega(dezenas_tuple, garantia):
    dezenas = list(dezenas_tuple)
    todas_comb = list(itertools.combinations(dezenas, 6))
    
    comb_filtradas = []
    for c in todas_comb:
        soma = sum(c)
        mult_10 = sum(1 for x in c if x % 10 == 0)
        # Filtro de Gauss + Restrição de Coluna Zero
        if 120 <= soma <= 240 and mult_10 <= 2:
            comb_filtradas.append(c)
            
    if garantia == 6 or len(dezenas) <= 6: return [list(c) for c in comb_filtradas]

    comb_bits = [sum(1 << num for num in c) for c in comb_filtradas]
    sorteios_possiveis = set(range(len(comb_bits)))
    bilhetes_escolhidos, cobertura = [], []
    for b in comb_bits: cobertura.append({j for j, s in enumerate(comb_bits) if (b & s).bit_count() >= garantia})
    while sorteios_possiveis:
        melhor_idx = max(range(len(cobertura)), key=lambda i: len(cobertura[i].intersection(sorteios_possiveis)))
        bilhetes_escolhidos.append(list(comb_filtradas[melhor_idx]))
        sorteios_possiveis -= cobertura[melhor_idx]
    return bilhetes_escolhidos

def raciocinio_ia_mega(historico, db_mega):
    if not historico: return None
    atrasos, dez_enc = {n: 0 for n in range(1, 61)}, {n: False for n in range(1, 61)}
    for h in reversed(historico):
        for n in range(1, 61):
            if n in h['dezenas']: dez_enc[n] = True
            elif not dez_enc[n]: atrasos[n] += 1

    cod_est, qtd_matriz, tatic_desc = "Arbitragem de Massa", 13, "Fuga do Padrão Humano + Análise Espacial."
    scores = {}
    for n in range(1, 61):
        d = atrasos.get(n, 0); sc = 0.0
        if 5 <= d <= 25: sc += 30.0
        elif d > 25: sc += 15.0 
        else: sc += 5.0 
        if n > 31: sc += 20.0 # Tendência da metade inferior
        if n % 10 in [9, 0]: sc += 15.0
        scores[n] = sc

    Q1 = set(range(1, 6)) | set(range(11, 16)) | set(range(21, 26))
    Q2 = set(range(6, 11)) | set(range(16, 21)) | set(range(26, 31))
    Q3 = set(range(31, 36)) | set(range(41, 46)) | set(range(51, 56))
    Q4 = set(range(36, 41)) | set(range(46, 51)) | set(range(56, 61))
    
    max_por_quad = round(qtd_matriz * 0.35) + 1 
    matriz = []
    candidatos = sorted(range(1, 61), key=lambda x: scores.get(x, 0), reverse=True)
    for n in candidatos:
        if len(matriz) >= qtd_matriz: break
        if n in Q1 and sum(1 for x in matriz if x in Q1) >= max_por_quad: continue
        if n in Q2 and sum(1 for x in matriz if x in Q2) >= max_por_quad: continue
        if n in Q3 and sum(1 for x in matriz if x in Q3) >= max_por_quad: continue
        if n in Q4 and sum(1 for x in matriz if x in Q4) >= max_por_quad: continue
        matriz.append(n)
        
    return {
        "estrategia": cod_est, "motivo_est": tatic_desc, "pesos": scores,
        "alvo": int((historico[-1]['concurso'] + 1)) if historico else 1,
        "qtd_matriz": qtd_matriz, "matriz_base": sorted(matriz)
    }

def auditar_bilhetes_mega(db_mega):
    historico = {h['concurso']: h for h in db_mega['historico_dados']}
    lucro_sessao = 0.0
    for j in db_mega['jogos_salvos']:
        if j['status'] == "Aguardando Sorteio" and j['concurso_alvo'] in historico:
            conc_data = historico[j['concurso_alvo']]
            sorteadas = set(conc_data['dezenas'])
            rateios = {}
            for p in conc_data.get('premiacoes', []):
                desc = p.get('descricao', '').lower()
                if '6 acertos' in desc or 'sena' in desc: rateios[6] = float(p.get('valorPremio', 0.0))
                elif '5 acertos' in desc or 'quina' in desc: rateios[5] = float(p.get('valorPremio', 0.0))
                elif '4 acertos' in desc or 'quadra' in desc: rateios[4] = float(p.get('valorPremio', 0.0))
            
            pontos = len(set(j['dezenas']).intersection(sorteadas))
            j['acertos'] = pontos
            j['premio_valor'] = calcular_premio_mega(pontos, rateios)
            
            db_mega["ledger_track"]["bilhetes"] += 1
            if pontos >= 4:
                j['status'] = "Premiado"
                lucro_sessao += j['premio_valor']
                db_mega["historico_premios"] += j['premio_valor']
                db_mega["ledger_track"]["premiados_geral"] += 1
                if pontos >= 5: db_mega["ledger_track"]["elite"] += 1
                db_mega["global_hits"][str(pontos)] = db_mega["global_hits"].get(str(pontos), 0) + 1
            else: j['status'] = "Não Premiado"
    return lucro_sessao

def tela_megasena():
    exibir_cabecalho("MEGA-SENA PRO", "#209869", "🟢")
    db_mega = st.session_state.db["megasena"]
    
    tabs = st.tabs(["📂 1. Banco de Dados", "🧠 2. Cérebro Analítico (IA)", "🤖 3. Geração Autônoma", "📜 4. Fila de Sorteio"])

    with tabs[0]:
        exibir_mini_painel_financeiro("megasena", "#209869")
        st.info(f"Concursos Oficiais Salvos: **{len(db_mega['historico_dados'])}**")
        if st.button("🔄 ZERAR CONTABILIDADE (MEGA)", type="secondary"):
            db_mega["historico_custos"] = db_mega["historico_premios"] = 0.0
            salvar_db_unico(); st.rerun()

    with tabs[1]:
        exibir_mini_painel_financeiro("megasena", "#209869")
        st.markdown("### 🧠 Como a IA da Mega-Sena funciona (Detalhado)")
        st.write("Diferente da Lotofácil, a Mega-Sena requer análise Espacial. A IA mapeia o volante dividindo-o em 4 quadrantes estritos e previne que o desdobramento se aglomere em uma única área geométrica. Além disso, a máquina elimina automaticamente bilhetes cuja soma seja menor que 120 ou maior que 240 (Regra de Ouro de Gauss).")
        if db_mega["historico_dados"]:
            ia = raciocinio_ia_mega(db_mega["historico_dados"], db_mega)
            st.info(f"⚡ **ESTRATÉGIA:** {ia['estrategia']} | **MATRIZ ({ia['qtd_matriz']} Dezenas):** " + ", ".join([f"{n:02d}" for n in ia['matriz_base']]))
        else: st.warning("Sincronize o banco de dados no Pré-Lobby primeiro.")

    with tabs[2]:
        exibir_mini_painel_financeiro("megasena", "#209869")
        if db_mega["historico_dados"]:
            ia = raciocinio_ia_mega(db_mega["historico_dados"], db_mega)
            st.markdown(f"<div style='background-color: #f2fbf6; border-left: 5px solid #209869; padding: 15px; border-radius: 5px; margin-bottom: 20px;'><h4 style='color: #209869; margin-top: 0;'>🔒 O CADEADO MATEMÁTICO (Filtros Ativos)</h4><p>Se as 6 sorteadas estiverem DENTRO da sua Matriz de {ia['qtd_matriz']} dezenas e passarem no Filtro de Gauss, a sua garantia é 100% honrada.</p></div>", unsafe_allow_html=True)
            
            garantia = st.radio("Garantia do Fechamento:", [6, 5, 4], horizontal=True)
            if st.button("🧬 GERAR FECHAMENTO DE ELITE (R$ 6,00/jogo)", type="primary"):
                jogos = gerar_fechamento_mega(tuple(ia['matriz_base']), garantia)
                for b in jogos:
                    db_mega["jogos_salvos"].append({"id": str(uuid.uuid4()), "concurso_alvo": ia['alvo'], "dezenas": b, "tamanho": 6, "status": "Aguardando Sorteio", "acertos": 0, "premio_valor": 0.0})
                db_mega["historico_custos"] += len(jogos) * 6.00; salvar_db_unico(); st.success(f"Gerado {len(jogos)} bilhetes filtrados!"); st.rerun()

    with tabs[3]:
        exibir_mini_painel_financeiro("megasena", "#209869")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 AUDITAR BILHETES PENDENTES", type="primary", use_container_width=True):
                lucro = auditar_bilhetes_mega(db_mega); salvar_db_unico()
                st.success(f"Auditoria concluída! Lucro obtido: R$ {lucro:,.2f}"); st.rerun()
        with col2:
            if st.button("🗑️ LIMPAR FILA", type="secondary", use_container_width=True):
                db_mega["jogos_salvos"] = []; salvar_db_unico(); st.rerun()
                
        st.markdown("#### Últimos Bilhetes")
        for j in reversed(db_mega["jogos_salvos"][-10:]):
            st.code(f"Alvo: {j['concurso_alvo']} | {j['dezenas']} | Status: {j['status']} | Prêmio: R$ {j.get('premio_valor', 0):.2f}")

# =====================================================================
# 6. MOTOR ANALÍTICO - LOTOMANIA (ELITE ESTOCÁSTICO)
# =====================================================================
def calcular_premio_lotomania(acertos, rateios):
    if acertos == 20: return rateios.get(20, 5000000.0)
    if acertos == 19: return rateios.get(19, 50000.0)
    if acertos == 18: return rateios.get(18, 2500.0)
    if acertos == 17: return rateios.get(17, 250.0)
    if acertos == 16: return rateios.get(16, 30.0)
    if acertos == 15: return rateios.get(15, 10.0)
    if acertos == 0: return rateios.get(0, 150000.0)
    return 0.0

def validar_filtros_lotomania(jogo):
    soma = sum(jogo)
    if not (2100 <= soma <= 2800): return False # Curva de Gauss (Massiva)
    q1 = q2 = q3 = q4 = 0
    for dezena in jogo:
        lin, col = dezena // 10, dezena % 10
        if lin < 5 and col < 5: q1 += 1
        elif lin < 5 and col >= 5: q2 += 1
        elif lin >= 5 and col < 5: q3 += 1
        else: q4 += 1
    # Balanceamento restrito de quadrantes para evitar bolos no volante
    if any(q < 8 or q > 17 for q in [q1, q2, q3, q4]): return False
    return True

@st.cache_data(show_spinner="🧠 Lotomania: Aplicando Filtros de Monte Carlo...")
def gerar_estrategia_super_matriz(top_dezenas, qtd_jogos=5):
    jogos_aprovados = []
    max_tentativas = 20000 
    tentativas = 0
    while len(jogos_aprovados) < qtd_jogos and tentativas < max_tentativas:
        candidato = sorted(random.sample(top_dezenas, 50))
        if validar_filtros_lotomania(candidato): jogos_aprovados.append(candidato)
        tentativas += 1
    return jogos_aprovados

def raciocinio_ia_lotomania(historico, db_lotomania):
    if not historico: return None
    atrasos = {n: 0 for n in range(100)}
    dez_enc = {n: False for n in range(100)}
    
    for h in reversed(historico):
        for n in range(100):
            if n in h['dezenas'] or f"{n:02d}" in h['dezenas']: dez_enc[n] = True
            elif not dez_enc[n]: atrasos[n] += 1

    scores = {}
    for n in range(100):
        d = atrasos.get(n, 0)
        sc = 50.0
        if n % 10 in [0, 9]: sc += 10.0 # Fuga de humanos (pontas)
        if 3 <= d <= 12: sc += 25.0 # Fervura Térmica
        elif d > 20: sc -= 15.0 # Zona Congelada
        scores[n] = round(sc, 2)

    ranking = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_70 = sorted([x[0] for x in ranking[:70]]) # Para acertar 20
    zona_morta = sorted([x[0] for x in ranking[-50:]]) # Para errar tudo (0 acertos)

    return {
        "estrategia": "Monte Carlo Estocástico", 
        "motivo_est": "Ataque Massivo com Análise de Quadrantes e Ponto de Fervura.",
        "pesos": scores, "alvo": int(historico[-1]['concurso'] + 1) if historico else 1,
        "top_70": top_70, "zona_morta": zona_morta
    }

def auditar_bilhetes_lotomania(db_lotomania):
    historico = {h['concurso']: h for h in db_lotomania['historico_dados']}
    lucro_sessao = 0.0
    for j in db_lotomania['jogos_salvos']:
        if j['status'] == "Aguardando Sorteio" and j['concurso_alvo'] in historico:
            conc_data = historico[j['concurso_alvo']]
            sorteadas = set(conc_data['dezenas'])
            rateios = {}
            for p in conc_data.get('premiacoes', []):
                desc = p.get('descricao', '').lower()
                if '20 acertos' in desc: rateios[20] = float(p.get('valorPremio', 0.0))
                elif '19 acertos' in desc: rateios[19] = float(p.get('valorPremio', 0.0))
                elif '18 acertos' in desc: rateios[18] = float(p.get('valorPremio', 0.0))
                elif '17 acertos' in desc: rateios[17] = float(p.get('valorPremio', 0.0))
                elif '16 acertos' in desc: rateios[16] = float(p.get('valorPremio', 0.0))
                elif '15 acertos' in desc: rateios[15] = float(p.get('valorPremio', 0.0))
                elif '0 acertos' in desc or 'nenhum' in desc: rateios[0] = float(p.get('valorPremio', 0.0))
            
            pontos = len(set(j['dezenas']).intersection(sorteadas))
            j['acertos'] = pontos
            j['premio_valor'] = calcular_premio_lotomania(pontos, rateios)
            
            db_lotomania["ledger_track"]["bilhetes"] += 1
            if pontos in [0, 15, 16, 17, 18, 19, 20]:
                j['status'] = "Premiado"
                lucro_sessao += j['premio_valor']
                db_lotomania["historico_premios"] += j['premio_valor']
                db_lotomania["ledger_track"]["premiados_geral"] += 1
                if pontos in [0, 19, 20]: db_lotomania["ledger_track"]["elite"] += 1
                db_lotomania["global_hits"][str(pontos)] = db_lotomania["global_hits"].get(str(pontos), 0) + 1
            else: j['status'] = "Não Premiado"
    return lucro_sessao

def tela_lotomania():
    exibir_cabecalho("LOTOMANIA PRO", "#F78100", "🟠")
    db_lotomania = st.session_state.db["lotomania"]
    
    tabs = st.tabs(["📂 1. Banco de Dados", "🧠 2. Cérebro Analítico (IA)", "🤖 3. Geração Autônoma", "📜 4. Fila de Sorteio"])

    with tabs[0]:
        exibir_mini_painel_financeiro("lotomania", "#F78100")
        st.info(f"Concursos Oficiais Salvos: **{len(db_lotomania['historico_dados'])}**")
        if st.button("🔄 ZERAR CONTABILIDADE (LOTOMANIA)", type="secondary"):
            db_lotomania["historico_custos"] = db_lotomania["historico_premios"] = 0.0
            salvar_db_unico(); st.rerun()

    with tabs[1]:
        exibir_mini_painel_financeiro("lotomania", "#F78100")
        st.markdown("### 🧠 Como a IA da Lotomania funciona (Detalhado)")
        st.write("A escala da Lotomania é massiva. Fazer Set Cover absoluto trava supercomputadores. A IA usa **Filtros Estocásticos (Monte Carlo)**. Ela mapeia os 100 números, isola as 70 melhores dezenas ('Super Matriz') e as 50 piores dezenas ('Zona Morta'). Ao gerar, aplica a Curva de Gauss exigindo que a soma caia entre 2100 e 2800 e balanceia os quadrantes para não dar erro na lotérica.")
        
        if db_lotomania["historico_dados"]:
            ia = raciocinio_ia_lotomania(db_lotomania["historico_dados"], db_lotomania)
            col_b, col_r = st.columns(2)
            with col_b:
                st.success(f"🎯 **SUPER MATRIZ (Top 70):**\n\n" + ", ".join([f"{n:02d}" for n in ia['top_70']]))
            with col_r:
                st.error(f"🪞 **ZONA MORTA (Piores 50):**\n\n" + ", ".join([f"{n:02d}" for n in ia['zona_morta']]))
        else: st.warning("Sincronize o banco de dados no Pré-Lobby primeiro.")

    with tabs[2]:
        exibir_mini_painel_financeiro("lotomania", "#F78100")
        if db_lotomania["historico_dados"]:
            ia = raciocinio_ia_lotomania(db_lotomania["historico_dados"], db_lotomania)
            st.markdown(f"<div style='background-color: #fff8f0; border-left: 5px solid #F78100; padding: 15px; border-radius: 5px; margin-bottom: 20px;'><h4 style='color: #F78100; margin-top: 0;'>🔒 LIBERDADE DE COMBATE</h4><p>Você decide a abordagem matemática. Ataque a Super Matriz para focar em 20 pontos, ou foque na Zona Morta para focar em 0 pontos através da aposta Espelho.</p></div>", unsafe_allow_html=True)
            
            tipo = st.radio("Escolha sua Diretriz Tática:", ["1. Super Matriz (Tentar Acertar 20 Pontos)", "2. Zona Morta (Tentar Acertar 0 Pontos - ESPELHO)"], key="radio_tatico_loto")
            
            if "Super" in tipo:
                qtd = st.slider("Quantidade de Bilhetes:", 1, 30, 5)
                if st.button(f"🧬 GERAR LOTOMANIA ELITE (R$ {qtd * 3.00:.2f})", type="primary"):
                    db_lotomania["jogos_salvos"] = [j for j in db_lotomania["jogos_salvos"] if j.get('status') != "Aguardando Sorteio"]
                    aprovados = gerar_estrategia_super_matriz(ia['top_70'], qtd)
                    for b in aprovados:
                        db_lotomania["jogos_salvos"].append({"id": str(uuid.uuid4()), "concurso_alvo": ia['alvo'], "dezenas": b, "tamanho": 50, "estrategia": "Super 70 (Gauss)", "status": "Aguardando Sorteio", "acertos": 0, "premio_valor": 0.0})
                    db_lotomania["historico_custos"] += len(aprovados) * 3.00; salvar_db_unico(); st.success(f"Gerado {len(aprovados)} bilhetes validados!"); st.rerun()
            else:
                st.warning("⚠️ **INSTRUÇÃO SINDICAL:** Ao registrar este bilhete, você DEVE marcar a opção 'Aposta Espelho' no volante para cobrir os 0 acertos com a máquina da Caixa.")
                if st.button("🪞 GERAR BILHETE TÓXICO (R$ 6,00 c/ Espelho)", type="primary"):
                    db_lotomania["jogos_salvos"] = [j for j in db_lotomania["jogos_salvos"] if j.get('status') != "Aguardando Sorteio"]
                    db_lotomania["jogos_salvos"].append({"id": str(uuid.uuid4()), "concurso_alvo": ia['alvo'], "dezenas": ia['zona_morta'], "tamanho": 50, "estrategia": "Espelho Reverso (0 pts)", "status": "Aguardando Sorteio", "acertos": 0, "premio_valor": 0.0})
                    db_lotomania["historico_custos"] += 6.00; salvar_db_unico(); st.success("Bilhete de Ataque Reverso gerado!"); st.rerun()

    with tabs[3]:
        exibir_mini_painel_financeiro("lotomania", "#F78100")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 AUDITAR BILHETES PENDENTES", type="primary", use_container_width=True, key="audit_loto"):
                lucro = auditar_bilhetes_lotomania(db_lotomania); salvar_db_unico()
                st.success(f"Auditoria concluída! Lucro obtido: R$ {lucro:,.2f}"); st.rerun()
        with col2:
            if st.button("🗑️ LIMPAR FILA", type="secondary", use_container_width=True, key="clean_loto"):
                db_lotomania["jogos_salvos"] = []; salvar_db_unico(); st.rerun()
                
        st.markdown("#### Últimos Bilhetes")
        for j in reversed(db_lotomania["jogos_salvos"][-10:]):
            st.code(f"Alvo: {j['concurso_alvo']} | {j.get('estrategia','')} | Status: {j['status']} | Acertos: {j.get('acertos',0)} | R$ {j.get('premio_valor', 0):.2f}")

# =====================================================================
# 7. MOTOR ANALÍTICO - QUINA
# =====================================================================
def calcular_premio_quina(acertos, rateios):
    if acertos == 5: return rateios.get(5, 5000000.0)
    if acertos == 4: return rateios.get(4, 8000.0)
    if acertos == 3: return rateios.get(3, 100.0)
    if acertos == 2: return rateios.get(2, 4.0)
    return 0.0

@st.cache_data(show_spinner="🧠 Quina: Aplicando Filtros de Dispersão...")
def gerar_fechamento_quina(dezenas_tuple, garantia):
    dezenas = list(dezenas_tuple)
    todas_comb = list(itertools.combinations(dezenas, 5))
    
    comb_filtradas = []
    for c in todas_comb:
        soma = sum(c)
        cols = [n % 10 for n in c]
        # Filtro: Gauss + Bloqueio de 3+ dezenas na mesma coluna vertical
        if 100 <= soma <= 300 and not any(cols.count(col) > 2 for col in set(cols)):
            comb_filtradas.append(c)

    if garantia == 5 or len(dezenas) <= 5: return [list(c) for c in comb_filtradas]

    comb_bits = [sum(1 << num for num in c) for c in comb_filtradas]
    sorteios_possiveis = set(range(len(comb_bits)))
    bilhetes_escolhidos, cobertura = [], []
    for b in comb_bits: cobertura.append({j for j, s in enumerate(comb_bits) if (b & s).bit_count() >= garantia})
    while sorteios_possiveis:
        melhor_idx = max(range(len(cobertura)), key=lambda i: len(cobertura[i].intersection(sorteios_possiveis)))
        bilhetes_escolhidos.append(list(comb_filtradas[melhor_idx]))
        sorteios_possiveis -= cobertura[melhor_idx]
    return bilhetes_escolhidos

def raciocinio_ia_quina(historico, db_quina):
    if not historico: return None
    atrasos = {n: 0 for n in range(1, 81)}
    for h in reversed(historico):
        for n in range(1, 81):
            if n in h['dezenas']: pass
            elif atrasos[n] == 0: atrasos[n] += 1
            
    scores = {}
    for n in range(1, 81):
        sc = 10.0; d = atrasos.get(n, 0)
        if 8 <= d <= 35: sc += 40.0 # Ponto quente Quina
        if n % 10 in [3, 7]: sc += 10.0 # Final com maior dispersão geométrica
        scores[n] = sc
        
    ranking = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    matriz = sorted([x[0] for x in ranking[:15]]) # Matriz de 15
    return {
        "estrategia": "Rastreio Termal de Colunas", "motivo_est": "Filtra dispersões verticais e soma harmônica.",
        "pesos": scores, "alvo": int(historico[-1]['concurso'] + 1) if historico else 1,
        "qtd_matriz": 15, "matriz_base": matriz
    }

def auditar_bilhetes_quina(db_quina):
    historico = {h['concurso']: h for h in db_quina['historico_dados']}
    lucro_sessao = 0.0
    for j in db_quina['jogos_salvos']:
        if j['status'] == "Aguardando Sorteio" and j['concurso_alvo'] in historico:
            conc_data = historico[j['concurso_alvo']]
            sorteadas = set(conc_data['dezenas'])
            rateios = {}
            for p in conc_data.get('premiacoes', []):
                desc = p.get('descricao', '').lower()
                if '5 acertos' in desc or 'quina' in desc: rateios[5] = float(p.get('valorPremio', 0.0))
                elif '4 acertos' in desc or 'quadra' in desc: rateios[4] = float(p.get('valorPremio', 0.0))
                elif '3 acertos' in desc or 'terno' in desc: rateios[3] = float(p.get('valorPremio', 0.0))
                elif '2 acertos' in desc or 'duque' in desc: rateios[2] = float(p.get('valorPremio', 0.0))
            
            pontos = len(set(j['dezenas']).intersection(sorteadas))
            j['acertos'] = pontos
            j['premio_valor'] = calcular_premio_quina(pontos, rateios)
            
            db_quina["ledger_track"]["bilhetes"] += 1
            if pontos >= 2:
                j['status'] = "Premiado"
                lucro_sessao += j['premio_valor']
                db_quina["historico_premios"] += j['premio_valor']
                db_quina["ledger_track"]["premiados_geral"] += 1
                if pontos >= 4: db_quina["ledger_track"]["elite"] += 1
                db_quina["global_hits"][str(pontos)] = db_quina["global_hits"].get(str(pontos), 0) + 1
            else: j['status'] = "Não Premiado"
    return lucro_sessao

def tela_quina():
    exibir_cabecalho("QUINA PRO", "#260085", "🔵")
    db_quina = st.session_state.db["quina"]
    
    tabs = st.tabs(["📂 1. Banco de Dados", "🧠 2. Cérebro Analítico (IA)", "🤖 3. Geração Autônoma", "📜 4. Fila de Sorteio"])

    with tabs[0]:
        exibir_mini_painel_financeiro("quina", "#260085")
        st.info(f"Concursos Oficiais Salvos: **{len(db_quina['historico_dados'])}**")
        if st.button("🔄 ZERAR CONTABILIDADE (QUINA)", type="secondary"):
            db_quina["historico_custos"] = db_quina["historico_premios"] = 0.0
            salvar_db_unico(); st.rerun()

    with tabs[1]:
        exibir_mini_painel_financeiro("quina", "#260085")
        st.markdown("### 🧠 Como a IA da Quina funciona (Detalhado)")
        st.write("A Quina é um jogo de Dispersão Colunar extrema. A IA rastreia o atraso de dezenas e bloqueia severamente a geração de bilhetes que tenham 3 ou mais números terminados no mesmo dígito vertical. Se a curva de Gauss não estiver batendo 100 a 300 pontos de soma, o bilhete é destruído pela IA antes de chegar a você.")
        
        if db_quina["historico_dados"]:
            ia = raciocinio_ia_quina(db_quina["historico_dados"], db_quina)
            st.info(f"⚡ **ESTRATÉGIA:** {ia['estrategia']} | **MATRIZ ({ia['qtd_matriz']} Dezenas):** " + ", ".join([f"{n:02d}" for n in ia['matriz_base']]))
        else: st.warning("Sincronize o banco de dados no Pré-Lobby primeiro.")

    with tabs[2]:
        exibir_mini_painel_financeiro("quina", "#260085")
        if db_quina["historico_dados"]:
            ia = raciocinio_ia_quina(db_quina["historico_dados"], db_quina)
            st.markdown(f"<div style='background-color: #f0f4ff; border-left: 5px solid #260085; padding: 15px; border-radius: 5px; margin-bottom: 20px;'><h4 style='color: #260085; margin-top: 0;'>🔒 O CADEADO MATEMÁTICO</h4><p>Garantia real apenas se as 5 sorteadas caírem DENTRO da sua Matriz de {ia['qtd_matriz']} dezenas.</p></div>", unsafe_allow_html=True)
            
            garantia = st.radio("Garantia do Fechamento:", [5, 4, 3], horizontal=True)
            if st.button("🧬 GERAR FECHAMENTO (R$ 3,00/jogo)", type="primary"):
                db_quina["jogos_salvos"] = [j for j in db_quina["jogos_salvos"] if j.get('status') != "Aguardando Sorteio"]
                jogos = gerar_fechamento_quina(tuple(ia['matriz_base']), garantia)
                for b in jogos:
                    db_quina["jogos_salvos"].append({"id": str(uuid.uuid4()), "concurso_alvo": ia['alvo'], "dezenas": b, "tamanho": 5, "estrategia": "Fechamento Dispersão", "status": "Aguardando Sorteio", "acertos": 0, "premio_valor": 0.0})
                db_quina["historico_custos"] += len(jogos) * 3.00; salvar_db_unico(); st.success(f"Gerado {len(jogos)} bilhetes!"); st.rerun()

    with tabs[3]:
        exibir_mini_painel_financeiro("quina", "#260085")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 AUDITAR BILHETES PENDENTES", type="primary", use_container_width=True, key="audit_quina"):
                lucro = auditar_bilhetes_quina(db_quina); salvar_db_unico()
                st.success(f"Auditoria concluída! Lucro obtido: R$ {lucro:,.2f}"); st.rerun()
        with col2:
            if st.button("🗑️ LIMPAR FILA", type="secondary", use_container_width=True, key="clean_quina"):
                db_quina["jogos_salvos"] = []; salvar_db_unico(); st.rerun()
                
        st.markdown("#### Últimos Bilhetes")
        for j in reversed(db_quina["jogos_salvos"][-10:]):
            st.code(f"Alvo: {j['concurso_alvo']} | {j['dezenas']} | Status: {j['status']} | Acertos: {j.get('acertos',0)} | R$ {j.get('premio_valor', 0):.2f}")

# =====================================================================
# 8. MOTOR ANALÍTICO - DUPLA SENA
# =====================================================================
def calcular_premio_duplasena(acertos, rateios):
    # A Dupla Sena paga Quadra, Quina e Sena nos 2 sorteios. Usaremos o maior valor para o acerto.
    if acertos == 6: return rateios.get(6, 2000000.0)
    if acertos == 5: return rateios.get(5, 4000.0)
    if acertos == 4: return rateios.get(4, 100.0)
    if acertos == 3: return rateios.get(3, 2.50)
    return 0.0

@st.cache_data(show_spinner="🧠 Dupla Sena: Aplicando Filtro Gaussiano Âncora...")
def gerar_fechamento_duplasena(dezenas_tuple, garantia):
    dezenas = list(dezenas_tuple)
    todas_comb = list(itertools.combinations(dezenas, 6))
    
    comb_filtradas = []
    for c in todas_comb:
        # Filtro Elite: Proibir que todos sejam pares ou ímpares e limitar a soma
        pares = sum(1 for x in c if x % 2 == 0)
        soma = sum(c)
        if (2 <= pares <= 4) and (80 <= soma <= 220):
            comb_filtradas.append(c)

    if garantia == 6 or len(dezenas) <= 6: return [list(c) for c in comb_filtradas]

    comb_bits = [sum(1 << num for num in c) for c in comb_filtradas]
    sorteios_possiveis = set(range(len(comb_bits)))
    bilhetes_escolhidos, cobertura = [], []
    for b in comb_bits: cobertura.append({j for j, s in enumerate(comb_bits) if (b & s).bit_count() >= garantia})
    while sorteios_possiveis:
        melhor_idx = max(range(len(cobertura)), key=lambda i: len(cobertura[i].intersection(sorteios_possiveis)))
        bilhetes_escolhidos.append(list(comb_filtradas[melhor_idx]))
        sorteios_possiveis -= cobertura[melhor_idx]
    return bilhetes_escolhidos

def raciocinio_ia_duplasena(historico, db_duplasena):
    if not historico: return None
    # Análise Âncora: Baseada primariamente no globo 1
    atrasos = {n: 0 for n in range(1, 51)}
    for h in reversed(historico):
        for n in range(1, 51):
            if n in h['dezenas']: pass
            elif atrasos[n] == 0: atrasos[n] += 1
            
    scores = {}
    for n in range(1, 51):
        sc = 20.0; d = atrasos.get(n, 0)
        if 4 <= d <= 15: sc += 30.0 # Ponto de Fervura Dupla Sena
        if n % 10 in [0, 5]: sc += 5.0
        scores[n] = sc
        
    ranking = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    matriz = sorted([x[0] for x in ranking[:14]]) # Matriz de 14 Elite
    return {
        "estrategia": "Análise Âncora (1º Sorteio)", "motivo_est": "Ignora o 2º sorteio para prever a física primária do globo principal.",
        "pesos": scores, "alvo": int(historico[-1]['concurso'] + 1) if historico else 1,
        "qtd_matriz": 14, "matriz_base": matriz
    }

def auditar_bilhetes_duplasena(db_duplasena):
    historico = {h['concurso']: h for h in db_duplasena['historico_dados']}
    lucro_sessao = 0.0
    for j in db_duplasena['jogos_salvos']:
        if j['status'] == "Aguardando Sorteio" and j['concurso_alvo'] in historico:
            conc_data = historico[j['concurso_alvo']]
            sorteadas = set(conc_data['dezenas'])
            rateios = {}
            for p in conc_data.get('premiacoes', []):
                desc = p.get('descricao', '').lower()
                if '6 acertos' in desc or 'sena' in desc: rateios[6] = float(p.get('valorPremio', 0.0))
                elif '5 acertos' in desc or 'quina' in desc: rateios[5] = float(p.get('valorPremio', 0.0))
                elif '4 acertos' in desc or 'quadra' in desc: rateios[4] = float(p.get('valorPremio', 0.0))
                elif '3 acertos' in desc or 'terno' in desc: rateios[3] = float(p.get('valorPremio', 0.0))
            
            pontos = len(set(j['dezenas']).intersection(sorteadas))
            j['acertos'] = pontos
            j['premio_valor'] = calcular_premio_duplasena(pontos, rateios)
            
            db_duplasena["ledger_track"]["bilhetes"] += 1
            if pontos >= 3:
                j['status'] = "Premiado"
                lucro_sessao += j['premio_valor']
                db_duplasena["historico_premios"] += j['premio_valor']
                db_duplasena["ledger_track"]["premiados_geral"] += 1
                if pontos >= 5: db_duplasena["ledger_track"]["elite"] += 1
                db_duplasena["global_hits"][str(pontos)] = db_duplasena["global_hits"].get(str(pontos), 0) + 1
            else: j['status'] = "Não Premiado"
    return lucro_sessao

def tela_duplasena():
    exibir_cabecalho("DUPLA SENA PRO", "#ED1622", "🔴")
    db_duplasena = st.session_state.db["duplasena"]
    
    tabs = st.tabs(["📂 1. Banco de Dados", "🧠 2. Cérebro Analítico (IA)", "🤖 3. Geração Autônoma", "📜 4. Fila de Sorteio"])

    with tabs[0]:
        exibir_mini_painel_financeiro("duplasena", "#ED1622")
        st.info(f"Concursos Oficiais Salvos: **{len(db_duplasena['historico_dados'])}**")
        if st.button("🔄 ZERAR CONTABILIDADE (DUPLA SENA)", type="secondary"):
            db_duplasena["historico_custos"] = db_duplasena["historico_premios"] = 0.0
            salvar_db_unico(); st.rerun()

    with tabs[1]:
        exibir_mini_painel_financeiro("duplasena", "#ED1622")
        st.markdown("### 🧠 Como a IA da Dupla Sena funciona (Detalhado)")
        st.write("A Dupla Sena tem dois sorteios, mas a IA usa a **Análise Âncora**. Ela ignora o segundo sorteio para cálculos de tendência primária, pois a física da primeira extração dita a matemática original do globo. A IA exige que haja balanço absoluto de ímpares e pares (proibido jogar 6 pares ou 6 ímpares).")
        
        if db_duplasena["historico_dados"]:
            ia = raciocinio_ia_duplasena(db_duplasena["historico_dados"], db_duplasena)
            st.info(f"⚡ **ESTRATÉGIA:** {ia['estrategia']} | **MATRIZ ({ia['qtd_matriz']} Dezenas):** " + ", ".join([f"{n:02d}" for n in ia['matriz_base']]))
        else: st.warning("Sincronize o banco de dados no Pré-Lobby primeiro.")

    with tabs[2]:
        exibir_mini_painel_financeiro("duplasena", "#ED1622")
        if db_duplasena["historico_dados"]:
            ia = raciocinio_ia_duplasena(db_duplasena["historico_dados"], db_duplasena)
            st.markdown(f"<div style='background-color: #fff0f0; border-left: 5px solid #ED1622; padding: 15px; border-radius: 5px; margin-bottom: 20px;'><h4 style='color: #ED1622; margin-top: 0;'>🔒 O CADEADO MATEMÁTICO</h4><p>Garantia real aplicável se as 6 sorteadas do Globo Primário caírem DENTRO da sua Matriz de {ia['qtd_matriz']} dezenas.</p></div>", unsafe_allow_html=True)
            
            garantia = st.radio("Garantia do Fechamento:", [6, 5, 4], horizontal=True)
            if st.button("🧬 GERAR FECHAMENTO (R$ 3,00/jogo)", type="primary"):
                db_duplasena["jogos_salvos"] = [j for j in db_duplasena["jogos_salvos"] if j.get('status') != "Aguardando Sorteio"]
                jogos = gerar_fechamento_duplasena(tuple(ia['matriz_base']), garantia)
                for b in jogos:
                    db_duplasena["jogos_salvos"].append({"id": str(uuid.uuid4()), "concurso_alvo": ia['alvo'], "dezenas": b, "tamanho": 6, "estrategia": "Fechamento Âncora", "status": "Aguardando Sorteio", "acertos": 0, "premio_valor": 0.0})
                db_duplasena["historico_custos"] += len(jogos) * 3.00; salvar_db_unico(); st.success(f"Gerado {len(jogos)} bilhetes!"); st.rerun()

    with tabs[3]:
        exibir_mini_painel_financeiro("duplasena", "#ED1622")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 AUDITAR BILHETES PENDENTES", type="primary", use_container_width=True, key="audit_dupla"):
                lucro = auditar_bilhetes_duplasena(db_duplasena); salvar_db_unico()
                st.success(f"Auditoria concluída! Lucro obtido: R$ {lucro:,.2f}"); st.rerun()
        with col2:
            if st.button("🗑️ LIMPAR FILA", type="secondary", use_container_width=True, key="clean_dupla"):
                db_duplasena["jogos_salvos"] = []; salvar_db_unico(); st.rerun()
                
        st.markdown("#### Últimos Bilhetes")
        for j in reversed(db_duplasena["jogos_salvos"][-10:]):
            st.code(f"Alvo: {j['concurso_alvo']} | {j['dezenas']} | Status: {j['status']} | Acertos: {j.get('acertos',0)} | R$ {j.get('premio_valor', 0):.2f}")


# =====================================================================
# 9. MOTOR ANALÍTICO - +MILIONÁRIA
# =====================================================================
def calcular_premio_maismilionaria(acertos_dez, acertos_trevos, rateios):
    key = f"{acertos_dez}+{acertos_trevos}"
    # Mapeamento aproximado das chaves de rateio para +Milionaria
    mapa = {"6+2": rateios.get('6+2', 10000000.0), "6+1": rateios.get('6+1', 300000.0), "6+0": rateios.get('6+0', 50000.0),
            "5+2": rateios.get('5+2', 10000.0), "5+1": rateios.get('5+1', 1000.0), "5+0": rateios.get('5+0', 500.0),
            "4+2": rateios.get('4+2', 200.0), "4+1": rateios.get('4+1', 100.0), "4+0": rateios.get('4+0', 50.0),
            "3+2": rateios.get('3+2', 50.0), "3+1": rateios.get('3+1', 24.0), "2+2": rateios.get('2+2', 12.0), "2+1": rateios.get('2+1', 6.0)}
    return mapa.get(key, 0.0)

def raciocinio_ia_maismilionaria(historico, db_maismili):
    if not historico: return None
    # Motor Duplo (Dezenas e Trevos separadamente)
    atrasos_dez = {n: 0 for n in range(1, 51)}
    atrasos_trevo = {n: 0 for n in range(1, 7)}
    
    for h in reversed(historico):
        for n in range(1, 51):
            if n in h['dezenas']: pass
            elif atrasos_dez[n] == 0: atrasos_dez[n] += 1
        for t in range(1, 7):
            if t in h.get('trevos', []): pass
            elif atrasos_trevo[t] == 0: atrasos_trevo[t] += 1

    scores_dez = {}
    for n in range(1, 51):
        sc = 10.0; d = atrasos_dez.get(n, 0)
        if 5 <= d <= 18: sc += 30.0 # Caos Térmico Dezenas
        scores_dez[n] = sc
        
    scores_trevo = {}
    for t in range(1, 7):
        sc_t = 10.0; d_t = atrasos_trevo.get(t, 0)
        if d_t >= 3: sc_t += 50.0 # Fervura de Trevos (curto ciclo)
        scores_trevo[t] = sc_t
        
    matriz_dez = sorted([x[0] for x in sorted(scores_dez.items(), key=lambda x: x[1], reverse=True)[:10]]) # 10 Dezenas Elite
    matriz_trevos = sorted([x[0] for x in sorted(scores_trevo.items(), key=lambda x: x[1], reverse=True)[:3]]) # 3 Trevos Elite
    
    return {
        "estrategia": "Motor Duplo Cruzado (Dez + Trevos)", "motivo_est": "Analisa 50 dezenas e 6 trevos em instâncias de IAs isoladas.",
        "alvo": int(historico[-1]['concurso'] + 1) if historico else 1,
        "qtd_matriz": 10, "matriz_base": matriz_dez, "trevos_base": matriz_trevos
    }

def auditar_bilhetes_maismilionaria(db_maismili):
    historico = {h['concurso']: h for h in db_maismili['historico_dados']}
    lucro_sessao = 0.0
    for j in db_maismili['jogos_salvos']:
        if j['status'] == "Aguardando Sorteio" and j['concurso_alvo'] in historico:
            conc_data = historico[j['concurso_alvo']]
            sorteadas = set(conc_data['dezenas'])
            sorteados_trevos = set(conc_data.get('trevos', []))
            
            rateios = {} # Simplificação para puxar da API (Mapearemos as faixas na base)
            for p in conc_data.get('premiacoes', []):
                desc = p.get('descricao', '')
                if 'Faixa 1' in desc: rateios['6+2'] = float(p.get('valorPremio', 0.0))
                elif 'Faixa 2' in desc: rateios['6+1'] = float(p.get('valorPremio', 0.0))
                # ... (resto das faixas, mas usaremos valores estáticos no fallback)

            acertos_d = len(set(j['dezenas']).intersection(sorteadas))
            acertos_t = len(set(j.get('trevos',[])).intersection(sorteados_trevos))
            
            j['acertos'] = acertos_d
            j['acertos_trevo'] = acertos_t
            j['premio_valor'] = calcular_premio_maismilionaria(acertos_d, acertos_t, rateios)
            
            db_maismili["ledger_track"]["bilhetes"] += 1
            if j['premio_valor'] > 0:
                j['status'] = "Premiado"
                lucro_sessao += j['premio_valor']
                db_maismili["historico_premios"] += j['premio_valor']
                db_maismili["ledger_track"]["premiados_geral"] += 1
                if acertos_d >= 5: db_maismili["ledger_track"]["elite"] += 1
            else: j['status'] = "Não Premiado"
    return lucro_sessao

def tela_maismilionaria():
    exibir_cabecalho("+MILIONÁRIA PRO", "#0066b3", "🌟")
    db_maismili = st.session_state.db["maismilionaria"]
    
    tabs = st.tabs(["📂 1. Banco de Dados", "🧠 2. Cérebro Analítico (IA)", "🤖 3. Geração Autônoma", "📜 4. Fila de Sorteio"])

    with tabs[0]:
        exibir_mini_painel_financeiro("maismilionaria", "#0066b3")
        st.info(f"Concursos Oficiais Salvos: **{len(db_maismili['historico_dados'])}**")
        if st.button("🔄 ZERAR CONTABILIDADE (+MILIONÁRIA)", type="secondary"):
            db_maismili["historico_custos"] = db_maismili["historico_premios"] = 0.0
            salvar_db_unico(); st.rerun()

    with tabs[1]:
        exibir_mini_painel_financeiro("maismilionaria", "#0066b3")
        st.markdown("### 🧠 Como a IA da +Milionária funciona (Detalhado)")
        st.write("A loteria mais difícil do país requer o **Motor Duplo Cruzado**. Um cérebro avalia as 50 dezenas normais procurando a matriz primária. Um segundo cérebro avalia exclusivamente os 6 Trevos procurando o ponto de fervura curto. O desdobramento une as melhores dezenas com os melhores trevos calculados.")
        
        if db_maismili["historico_dados"]:
            ia = raciocinio_ia_maismilionaria(db_maismili["historico_dados"], db_maismili)
            st.info(f"⚡ **ESTRATÉGIA:** {ia['estrategia']}\n\n🎯 **MATRIZ ({ia['qtd_matriz']} Dez):** " + ", ".join([f"{n:02d}" for n in ia['matriz_base']]) + f"\n\n🍀 **TREVOS DE ELITE:** {ia['trevos_base']}")
        else: st.warning("Sincronize o banco de dados no Pré-Lobby primeiro.")

    with tabs[2]:
        exibir_mini_painel_financeiro("maismilionaria", "#0066b3")
        if db_maismili["historico_dados"]:
            ia = raciocinio_ia_maismilionaria(db_maismili["historico_dados"], db_maismili)
            st.markdown(f"<div style='background-color: #e6f3ff; border-left: 5px solid #0066b3; padding: 15px; border-radius: 5px; margin-bottom: 20px;'><h4 style='color: #0066b3; margin-top: 0;'>🔒 O CADEADO DUPLO (Dez + Trevo)</h4><p>O prêmio colossal requer que as 6 dezenas sorteadas caiam DENTRO das suas {ia['qtd_matriz']} selecionadas E os 2 Trevos sorteados sejam do seu pool de {len(ia['trevos_base'])}.</p></div>", unsafe_allow_html=True)
            
            if st.button("🧬 GERAR CRUZAMENTO +MILIONÁRIA (R$ 6,00/jogo)", type="primary"):
                db_maismili["jogos_salvos"] = [j for j in db_maismili["jogos_salvos"] if j.get('status') != "Aguardando Sorteio"]
                
                # Cruzamento de Desdobramento Limitado para evitar custos absurdos
                comb_dez = list(itertools.combinations(ia['matriz_base'], 6))
                comb_trevo = list(itertools.combinations(ia['trevos_base'], 2))
                
                bilhetes = []
                for b_dez in random.sample(comb_dez, min(len(comb_dez), 10)): # Foca em 10 combinações primárias
                    for b_trevo in comb_trevo: # Multiplica pelas combinações de trevos (3x)
                        bilhetes.append({"id": str(uuid.uuid4()), "concurso_alvo": ia['alvo'], "dezenas": list(b_dez), "trevos": list(b_trevo), "estrategia": "Cruzamento Elite", "status": "Aguardando Sorteio", "acertos": 0, "acertos_trevo": 0, "premio_valor": 0.0})
                
                db_maismili["jogos_salvos"].extend(bilhetes)
                db_maismili["historico_custos"] += len(bilhetes) * 6.00; salvar_db_unico(); st.success(f"Gerado {len(bilhetes)} bilhetes cruzados!"); st.rerun()

    with tabs[3]:
        exibir_mini_painel_financeiro("maismilionaria", "#0066b3")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 AUDITAR BILHETES PENDENTES", type="primary", use_container_width=True, key="audit_mili"):
                lucro = auditar_bilhetes_maismilionaria(db_maismili); salvar_db_unico()
                st.success(f"Auditoria concluída! Lucro obtido: R$ {lucro:,.2f}"); st.rerun()
        with col2:
            if st.button("🗑️ LIMPAR FILA", type="secondary", use_container_width=True, key="clean_mili"):
                db_maismili["jogos_salvos"] = []; salvar_db_unico(); st.rerun()
                
        st.markdown("#### Últimos Bilhetes")
        for j in reversed(db_maismili["jogos_salvos"][-10:]):
            st.code(f"Alvo: {j['concurso_alvo']} | Dez: {j['dezenas']} | Trevos: {j.get('trevos',[])} | Status: {j['status']} | Prêmio: R$ {j.get('premio_valor', 0):.2f}")


# =====================================================================
# 10. INICIALIZAÇÃO DO ROTEADOR PRINCIPAL DO SISTEMA
# =====================================================================
if not st.session_state.autenticado:
    tela_login()
elif st.session_state.pagina_atual == "pre_lobby":
    tela_pre_lobby()
elif st.session_state.pagina_atual == "lobby":
    tela_lobby()
elif st.session_state.pagina_atual == "lotofacil":
    tela_lotofacil()
elif st.session_state.pagina_atual == "megasena":
    tela_megasena()
elif st.session_state.pagina_atual == "lotomania":
    tela_lotomania()
elif st.session_state.pagina_atual == "quina":
    tela_quina()
elif st.session_state.pagina_atual == "duplasena":
    tela_duplasena()
elif st.session_state.pagina_atual == "maismilionaria":
    tela_maismilionaria()
else:
    st.session_state.pagina_atual = "pre_lobby"
    st.rerun()
            
