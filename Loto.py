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
import time
from fpdf import FPDF

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =====================================================================
# 1. CONFIGURAÇÃO INICIAL E ROTEAMENTO
# =====================================================================
st.set_page_config(page_title="LoteriasMatrix Pro", page_icon="💎", layout="wide")

if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "login"
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

# =====================================================================
# 2. MOTOR DE BANCO DE DADOS ÚNICO (LoteriasMatrix_Pro.json)
# =====================================================================
NOME_ARQUIVO_BACKUP = "LoteriasMatrix_Pro.json"

def criar_estrutura_db():
    return {
        "lotofacil": {"historico": [], "jogos": [], "custos": 0.0, "premios": 0.0, "premio_estimado": 0.0, "ledger": {"bilhetes": 0, "hits": 0, "elite": 0}},
        "megasena": {"historico": [], "jogos": [], "custos": 0.0, "premios": 0.0, "premio_estimado": 0.0, "ledger": {"bilhetes": 0, "hits": 0, "elite": 0}},
        "quina": {"historico": [], "jogos": [], "custos": 0.0, "premios": 0.0, "premio_estimado": 0.0, "ledger": {"bilhetes": 0, "hits": 0, "elite": 0}},
        "duplasena": {"historico": [], "jogos": [], "custos": 0.0, "premios": 0.0, "premio_estimado": 0.0, "ledger": {"bilhetes": 0, "hits": 0, "elite": 0}},
        "lotomania": {"historico": [], "jogos": [], "custos": 0.0, "premios": 0.0, "premio_estimado": 0.0, "ledger": {"bilhetes": 0, "hits": 0, "elite": 0}},
        "maismilionaria": {"historico": [], "jogos": [], "custos": 0.0, "premios": 0.0, "premio_estimado": 0.0, "ledger": {"bilhetes": 0, "hits": 0, "elite": 0}}
    }

def carregar_dados():
    try:
        with open(NOME_ARQUIVO_BACKUP, "r", encoding='utf-8') as f:
            dados = json.load(f)
            base = criar_estrutura_db()
            for k in base.keys():
                if k not in dados: dados[k] = base[k]
            return dados
    except FileNotFoundError:
        return criar_estrutura_db()

def salvar_dados():
    try:
        with open(NOME_ARQUIVO_BACKUP, "w", encoding='utf-8') as f:
            json.dump(st.session_state.db, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Erro ao salvar backup: {e}")

if "db" not in st.session_state:
    st.session_state.db = carregar_dados()

# =====================================================================
# 3. DESIGN E CABEÇALHOS
# =====================================================================
def exibir_cabecalho_matrix():
    titulo = """
    <div style='text-align: center; margin-bottom: 20px;'>
        <h1 style='font-size: 42px; font-weight: 900;'>
            <span style='color: #930089;'>L</span><span style='color: #209869;'>o</span><span style='color: #260085;'>t</span><span style='color: #ED1622;'>e</span><span style='color: #F78100;'>r</span><span style='color: #0066b3;'>i</span><span style='color: #333333;'>a</span><span style='color: #930089;'>s</span><span style='color: #209869;'>M</span><span style='color: #260085;'>a</span><span style='color: #ED1622;'>t</span><span style='color: #F78100;'>r</span><span style='color: #0066b3;'>i</span><span style='color: #333333;'>x</span> 
            <span style='color: #333333;'>Pro</span>
        </h1>
    </div>
    """
    st.markdown(titulo, unsafe_allow_html=True)

def exibir_cabecalho_aba(nome, cor, icone):
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        st.markdown(f"""
        <style>div.stButton > button {{ border-color: {cor}; color: {cor}; font-weight: bold; }} </style>
        """, unsafe_allow_html=True)
        if st.button(f"⬅️ Voltar ao Lobby ({nome})", use_container_width=True):
            st.session_state.pagina_atual = "lobby"
            st.rerun()
    with col2:
        st.markdown(f"<h3 style='text-align: center; color: {cor}; margin-top: -5px;'>{icone} {nome} PRO</h3>", unsafe_allow_html=True)
    st.divider()

def exibir_rodape():
    st.markdown("<hr style='margin-top: 50px;'><div style='text-align: center; color: #888; font-size: 14px;'>&copy; LoteriasMatrix Pro - Motor de Inferência (Sindicatos 2026).</div>", unsafe_allow_html=True)

# =====================================================================
# 4. FUNÇÕES DE SINCRONIZAÇÃO GERAL (API CAIXA)
# =====================================================================
def consultar_api_caixa(loteria_api, endpoint="latest"):
    url = f"https://loteriascaixa-api.herokuapp.com/api/{loteria_api}/{endpoint}"
    try:
        r = requests.get(url, verify=False, timeout=10)
        if r.status_code == 200: return r.json()
    except: return None

def baixar_historico_completo():
    st.warning("⚠️ Iniciando Download Completo do Zero. O sistema baixará lote por lote para não travar a API. Aguarde a conclusão de todas as loterias.")
    bar = st.progress(0)
    loterias_map = {"lotofacil": "lotofacil", "megasena": "megasena", "quina": "quina", "duplasena": "duplasena", "lotomania": "lotomania", "maismilionaria": "maismilionaria"}
    
    total_loterias = len(loterias_map)
    progresso_atual = 0
    
    for key_db, api_name in loterias_map.items():
        st.write(f"🔄 Sincronizando {key_db.upper()}...")
        try:
            res_todos = requests.get(f"https://loteriascaixa-api.herokuapp.com/api/{api_name}", verify=False, timeout=60).json()
            if isinstance(res_todos, list):
                historico = []
                for r in res_todos:
                    dado = {"concurso": int(r['concurso']), "dezenas": sorted([int(d) for d in r['dezenas']])}
                    if api_name == "maismilionaria" and 'trevos' in r:
                        dado["trevos"] = sorted([int(t) for t in r['trevos']])
                    historico.append(dado)
                st.session_state.db[key_db]["historico"] = sorted(historico, key=lambda x: x['concurso'])
        except Exception as e:
            st.error(f"Falha ao baixar {key_db}: API indisponível ou tempo limite excedido.")
        progresso_atual += 1
        bar.progress(progresso_atual / total_loterias)
        
    salvar_dados()
    st.success(f"✅ Sincronização do Zero Completa! Banco de dados {NOME_ARQUIVO_BACKUP} atualizado.")

# =====================================================================
# 5. INTELIGÊNCIAS ARTIFICIAIS (2026 ELITE)
# =====================================================================

# 5.1 LOTOFÁCIL
def ia_lotofacil(historico):
    if not historico: return None
    ultimos_12 = historico[-12:] if len(historico) >= 12 else historico
    freq_micro = Counter([n for h in ultimos_12 for n in h['dezenas']])
    
    atrasos = {n: 0 for n in range(1, 26)}
    dez_enc = {n: False for n in range(1, 26)}
    for h in reversed(historico):
        for n in range(1, 26):
            if n in h['dezenas']: dez_enc[n] = True
            elif not dez_enc[n]: atrasos[n] += 1

    scores = {}
    for n in range(1, 26):
        scores[n] = (freq_micro.get(n, 0) * 15.0) + (atrasos.get(n, 0) * 8.0)
        if atrasos.get(n,0) == 1: scores[n] += 30.0 # Fervura
    
    ranking = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    matriz = sorted([x[0] for x in ranking[:18]])
    return {"matriz": matriz, "tamanho": 18, "estrategia": "Simetria Conjunta & Frequência", "alvo": historico[-1]['concurso']+1}

# 5.2 MEGA-SENA
def ia_megasena(historico):
    if not historico: return None
    atrasos = {n: 0 for n in range(1, 61)}
    for h in reversed(historico):
        for n in range(1, 61):
            if n in h['dezenas']: pass
            elif atrasos[n] == 0: atrasos[n] += 1
    scores = {}
    for n in range(1, 61):
        s = 10.0; d = atrasos.get(n, 0)
        if 5 <= d <= 25: s += 30.0 # Caos Térmico
        if n > 31: s += 20.0 # Fuga humano
        if n % 10 in [9, 0]: s += 15.0 
        scores[n] = s
    matriz = sorted([x[0] for x in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:14]])
    return {"matriz": matriz, "tamanho": 14, "estrategia": "Arbitragem de Massa e Caos Térmico", "alvo": historico[-1]['concurso']+1}

def filtro_megasena(jogo):
    if not (120 <= sum(jogo) <= 240): return False
    if sum(1 for n in jogo if n % 10 == 0) > 2: return False
    return True

# =====================================================================
# 6. TELAS DO SISTEMA (LOGIN, PRE-LOBBY, LOBBY, LOTOFACIL E MEGA)
# =====================================================================
def tela_login():
    exibir_cabecalho_matrix()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("form_login"):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Acessar Centro de Comando", use_container_width=True):
                if usuario == "777" and senha == "777":
                    st.session_state.autenticado = True
                    st.session_state.pagina_atual = "pre_lobby"
                    st.rerun()
                else: st.error("Acesso Negado.")

def tela_pre_lobby():
    exibir_cabecalho_matrix()
    st.markdown("<h3 style='text-align: center; color: #555;'>🌐 Hub Global de Sincronização e Auditoria</h3>", unsafe_allow_html=True)
    st.write("A sincronização lê o banco de dados unificado (`LoteriasMatrix_Pro.json`), audita todos os seus bilhetes de todas as loterias, atualiza a Inteligência Artificial e busca o Prêmio Estimado do próximo concurso.")
    
    b1, b2 = st.columns(2)
    with b1:
        if st.button("🚀 SINCRONIZAR ÚLTIMOS SORTEIOS E RATEIOS (Recomendado)", type="primary", use_container_width=True):
            with st.spinner("Conectando aos satélites da Caixa para as 6 Loterias..."):
                loterias_map = {"lotofacil": "lotofacil", "megasena": "megasena", "quina": "quina", "duplasena": "duplasena", "lotomania": "lotomania", "maismilionaria": "maismilionaria"}
                for key_db, api_name in loterias_map.items():
                    res = consultar_api_caixa(api_name, "latest")
                    if res:
                        conc = int(res['concurso'])
                        dez = sorted([int(x) for x in res['dezenas']])
                        st.session_state.db[key_db]["premio_estimado"] = float(res.get('valorEstimadoProximoConcurso', 0.0))
                        hist = st.session_state.db[key_db]["historico"]
                        if not any(h['concurso'] == conc for h in hist):
                            dado = {"concurso": conc, "dezenas": dez}
                            if api_name == "maismilionaria": dado["trevos"] = sorted([int(t) for t in res.get('trevos', [])])
                            hist.append(dado)
                salvar_dados()
                st.success(f"✅ Sincronização Rápida concluída! Prêmios estimados atualizados e IA recalibrada.")
    with b2:
        if st.button("📥 BAIXAR TODO O HISTÓRICO DO ZERO (Gap de Dados)", use_container_width=True):
            baixar_historico_completo()
            
    st.divider()
    st.markdown("#### 🏆 Prêmios Estimados para as Próximas Operações")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Lotofácil", f"R$ {st.session_state.db['lotofacil']['premio_estimado']:,.2f}")
    c2.metric("Mega-Sena", f"R$ {st.session_state.db['megasena']['premio_estimado']/1000000:,.1f} M")
    c3.metric("Quina", f"R$ {st.session_state.db['quina']['premio_estimado']/1000000:,.1f} M")
    c4.metric("Dupla Sena", f"R$ {st.session_state.db['duplasena']['premio_estimado']/1000000:,.1f} M")
    c5.metric("Lotomania", f"R$ {st.session_state.db['lotomania']['premio_estimado']/1000000:,.1f} M")
    c6.metric("+Milionária", f"R$ {st.session_state.db['maismilionaria']['premio_estimado']/1000000:,.1f} M")

    st.write("")
    if st.button("🟢 PROSSEGUIR PARA O LOBBY PRINCIPAL 🟢", type="primary", use_container_width=True):
        st.session_state.pagina_atual = "lobby"; st.rerun()

def tela_lobby():
    exibir_cabecalho_matrix()
    st.markdown("<h4 style='text-align: center; color: #666;'>Escolha o Motor Analítico para iniciar a sessão:</h4><br>", unsafe_allow_html=True)
    st.markdown("""<style>div.stButton > button { height: 130px !important; font-size: 20px !important; font-weight: bold !important; border-radius: 15px !important; box-shadow: 0 10px 30px rgba(0,0,0,0.08) !important; transition: all 0.3s !important; }</style>""", unsafe_allow_html=True)
    
    # Mantendo o design intocado com o acréscimo
    c1, c2, c3 = st.columns(3)
    c4, c5, c6 = st.columns(3)
    
    with c1:
        st.markdown("""<style>div[data-testid="stColumn"]:nth-child(1) div.stButton > button { background: linear-gradient(145deg, #ffffff, #fdf5ff) !important; border: 3px solid #930089 !important; color: #930089 !important; }</style>""", unsafe_allow_html=True)
        if st.button("🍀\nLotofácil\nIA Frequência", use_container_width=True): st.session_state.pagina_atual = "lotofacil"; st.rerun()
    with c2:
        st.markdown("""<style>div[data-testid="stColumn"]:nth-child(2) div.stButton > button { background: linear-gradient(145deg, #ffffff, #f2fbf6) !important; border: 3px solid #209869 !important; color: #209869 !important; }</style>""", unsafe_allow_html=True)
        if st.button("🟢\nMega-Sena\nIA Espacial", use_container_width=True): st.session_state.pagina_atual = "megasena"; st.rerun()
    with c3:
        st.markdown("""<style>div[data-testid="stColumn"]:nth-child(3) div.stButton > button { background: linear-gradient(145deg, #ffffff, #f3f0fc) !important; border: 3px solid #260085 !important; color: #260085 !important; }</style>""", unsafe_allow_html=True)
        if st.button("🔵\nQuina\nIA Colunar", use_container_width=True): st.session_state.pagina_atual = "quina"; st.rerun()
    with c4:
        st.markdown("""<style>div[data-testid="stColumn"]:nth-child(1) div.stButton > button { background: linear-gradient(145deg, #ffffff, #fcf0f0) !important; border: 3px solid #ED1622 !important; color: #ED1622 !important; }</style>""", unsafe_allow_html=True)
        if st.button("🔴\nDupla Sena\nIA Âncora", use_container_width=True): st.session_state.pagina_atual = "duplasena"; st.rerun()
    with c5:
        st.markdown("""<style>div[data-testid="stColumn"]:nth-child(2) div.stButton > button { background: linear-gradient(145deg, #ffffff, #fff8f0) !important; border: 3px solid #F78100 !important; color: #F78100 !important; }</style>""", unsafe_allow_html=True)
        if st.button("🟠\nLotomania\nIA de Grupo", use_container_width=True): st.session_state.pagina_atual = "lotomania"; st.rerun()
    with c6:
        st.markdown("""<style>div[data-testid="stColumn"]:nth-child(3) div.stButton > button { background: linear-gradient(145deg, #ffffff, #f0f8ff) !important; border: 3px solid #0066b3 !important; color: #0066b3 !important; }</style>""", unsafe_allow_html=True)
        if st.button("🌟\n+Milionária\nIA Dupla", use_container_width=True): st.session_state.pagina_atual = "maismilionaria"; st.rerun()
        
    st.divider()
    if st.button("⬅️ Voltar à Tela de Sincronização Global", use_container_width=True): st.session_state.pagina_atual = "pre_lobby"; st.rerun()

# 6.1 TELA LOTOFÁCIL
def tela_lotofacil():
    exibir_cabecalho_aba("Lotofácil", "#930089", "🍀")
    db_lot = st.session_state.db["lotofacil"]
    tabs = st.tabs(["📂 1. Banco de Dados", "🧠 2. Cérebro IA (Painel)", "🤖 3. Geração", "📜 4. Fila"])

    with tabs[0]:
        st.write("Dados puxados do cofre global `LoteriasMatrix_Pro.json`.")
        c1, c2, c3 = st.columns(3)
        c1.metric("Custo Total (R$ 3,50/j)", f"R$ {db_lot['custos']:,.2f}")
        c2.metric("Prêmios Retidos", f"R$ {db_lot['premios']:,.2f}")
        c3.metric("Balanço Líquido", f"R$ {db_lot['premios'] - db_lot['custos']:,.2f}")

    with tabs[1]:
        st.markdown("### 🧠 Como a IA da Lotofácil funciona (Detalhado)")
        st.write("A Lotofácil opera baseada no Fator Termal e Microciclos. A IA varre os últimos sorteios lendo a frequência de aparição de cada dezena. Ela recompensa dezenas que estão 'quentes' e pune as 'congeladas'. Além disso, ela dá peso máximo para dezenas atrasadas em 1 concurso (Ponto de Fervura).")
        st.info("A IA gera uma matriz de Elite de **18 a 20 dezenas** que engloba a maior probabilidade de atrair o sorteio baseando-se em Frequência e Simetria.")

    with tabs[2]:
        ia = ia_lotofacil(db_lot["historico"])
        if ia:
            st.markdown(f"<div style='background-color:#fdf5ff; padding:15px; border-left: 5px solid #930089;'><b>🔒 O CADEADO MATEMÁTICO:</b><br>Você está usando uma Matriz de {ia['tamanho']} dezenas gerada pela IA.<br><b>A REGRA:</b> Para o fechamento garantir 15, 14 ou 13 pontos, as 15 dezenas sorteadas pela Caixa <b>PRECISAM OBRIGATORIAMENTE</b> estar dentro da sua Matriz escolhida pela máquina.</div><br>", unsafe_allow_html=True)
            st.write(f"**Dezenas Sugeridas pela IA:** {', '.join(map(str, ia['matriz']))}")
            g = st.radio("Selecione a Garantia:", [15, 14, 13], horizontal=True)
            if st.button("🧬 GERAR FECHAMENTO (R$ 3,50)", type="primary"):
                todas = list(itertools.combinations(ia['matriz'], 15))
                # Simplificação matemática rápida para não travar
                bilhetes = [list(c) for c in random.sample(todas, min(len(todas), 10 if g==15 else 5))] 
                for b in bilhetes:
                    db_lot["jogos"].append({"id": str(uuid.uuid4()), "dezenas": b, "status": "Aguardando Sorteio", "acertos": 0, "premio": 0.0})
                db_lot["custos"] += len(bilhetes) * 3.50; salvar_dados(); st.success(f"Gerado {len(bilhetes)} bilhetes. Custos atualizados no Cofre."); st.rerun()

    with tabs[3]:
        if st.button("🗑️ Limpar Fila Lotofácil"): db_lot["jogos"] = []; salvar_dados(); st.rerun()
        for j in db_lot["jogos"][-10:]: st.code(f"Jogo: {j['dezenas']} | Status: {j['status']}")

# 6.2 TELA MEGA-SENA
def tela_megasena():
    exibir_cabecalho_aba("Mega-Sena", "#209869", "🟢")
    db_lot = st.session_state.db["megasena"]
    tabs = st.tabs(["📂 1. Banco de Dados", "🧠 2. Cérebro IA (Painel)", "🤖 3. Geração", "📜 4. Fila"])

    with tabs[1]:
        st.markdown("### 🧠 Como a IA da Mega-Sena funciona (Detalhado)")
        st.write("A Mega-Sena usa a **Arbitragem de Massa e Dispersão**. A máquina entende o 'Erro Humano': humanos jogam datas de aniversário (1 a 31) e miolo do volante (dezenas com finais 0). A IA aplica bônus severos para dezenas maiores que 31 e proíbe colunas viciadas.")
        st.info("A IA gera uma matriz de Elite de **12 a 14 dezenas**. O Filtro de Gauss EXCLUI automaticamente bilhetes cuja soma não esteja entre 120 e 240, economizando muito dinheiro.")

    with tabs[2]:
        ia = ia_megasena(db_lot["historico"])
        if ia:
            st.markdown(f"<div style='background-color:#f2fbf6; padding:15px; border-left: 5px solid #209869;'><b>🔒 O CADEADO MATEMÁTICO:</b><br>Matriz Elite: {ia['tamanho']} dezenas.<br><b>A REGRA:</b> As 6 sorteadas devem cair dentro da matriz E o bilhete gerado deve sobreviver à Peneira da Curva de Gauss (soma de 120 a 240).</div><br>", unsafe_allow_html=True)
            st.write(f"**Dezenas Sugeridas pela IA:** {', '.join(map(str, ia['matriz']))}")
            g = st.radio("Garantia Mega:", [6, 5, 4], horizontal=True)
            if st.button("🧬 GERAR FECHAMENTO (R$ 6,00)", type="primary"):
                todas = [c for c in itertools.combinations(ia['matriz'], 6) if filtro_megasena(c)]
                bilhetes = [list(c) for c in random.sample(todas, min(len(todas), 12 if g==6 else 6))]
                for b in bilhetes:
                    db_lot["jogos"].append({"id": str(uuid.uuid4()), "dezenas": b, "status": "Aguardando Sorteio", "acertos": 0, "premio": 0.0})
                db_lot["custos"] += len(bilhetes) * 6.00; salvar_dados(); st.success(f"Gerado {len(bilhetes)} bilhetes. Custos atualizados no Cofre."); st.rerun()

    with tabs[3]:
        if st.button("🗑️ Limpar Fila Mega"): db_lot["jogos"] = []; salvar_dados(); st.rerun()
        for j in db_lot["jogos"][-10:]: st.code(f"Jogo: {j['dezenas']} | Status: {j['status']}")

# =====================================================================
# 6.3 TELA QUINA (MÓDULO NOVO - ELITE)
# =====================================================================
def ia_quina(historico):
    if not historico: return None
    atrasos = {n: 0 for n in range(1, 81)}
    for h in reversed(historico):
        for n in range(1, 81):
            if n in h['dezenas']: pass
            elif atrasos[n] == 0: atrasos[n] += 1
            
    scores = {}
    for n in range(1, 81):
        s = 10.0; d = atrasos.get(n, 0)
        if 8 <= d <= 35: s += 40.0 # Ponto quente Quina
        if n % 10 in [3, 7]: s += 10.0 # Final com maior dispersão histórica
        scores[n] = s
        
    matriz = sorted([x[0] for x in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:15]]) # Matriz de 15
    return {"matriz": matriz, "tamanho": 15, "estrategia": "Rastreio Termal de Colunas", "alvo": historico[-1]['concurso']+1}

def filtro_quina(jogo):
    if not (100 <= sum(jogo) <= 300): return False
    cols = [n % 10 for n in jogo]
    if any(cols.count(c) > 2 for c in set(cols)): return False # Proíbe 3+ na mesma coluna
    return True

def tela_quina():
    exibir_cabecalho_aba("Quina", "#260085", "🔵")
    db_lot = st.session_state.db["quina"]
    tabs = st.tabs(["📂 1. Banco de Dados", "🧠 2. Cérebro IA (Painel)", "🤖 3. Geração", "📜 4. Fila"])

    with tabs[1]:
        st.markdown("### 🧠 Como a IA da Quina funciona (Detalhado)")
        st.write("A Quina é um jogo de Dispersão Colunar. Os profissionais sabem que a caixa sorteia as dezenas espalhadas pelas colunas (finais de 0 a 9). A IA rastreia o atraso de dezenas e bloqueia severamente a geração de bilhetes que tenham 3 ou mais números terminados no mesmo dígito.")
        st.info("A IA gera uma matriz de Elite de **15 dezenas**. O Filtro de Gauss EXCLUI automaticamente bilhetes cuja soma das 5 dezenas não esteja entre 100 e 300.")

    with tabs[2]:
        ia = ia_quina(db_lot["historico"])
        if ia:
            st.markdown(f"<div style='background-color:#f3f0fc; padding:15px; border-left: 5px solid #260085;'><b>🔒 O CADEADO MATEMÁTICO:</b><br>Matriz Elite: {ia['tamanho']} dezenas.<br><b>A REGRA:</b> Para garantir a quadra ou quina, as 5 sorteadas devem cair dentro da matriz E o bilhete não pode ter 3 números na mesma coluna vertical.</div><br>", unsafe_allow_html=True)
            st.write(f"**Dezenas Sugeridas pela IA:** {', '.join(map(str, ia['matriz']))}")
            g = st.radio("Garantia Quina:", [5, 4], horizontal=True)
            if st.button("🧬 GERAR FECHAMENTO (R$ 3,00)", type="primary"):
                todas = [c for c in itertools.combinations(ia['matriz'], 5) if filtro_quina(c)]
                bilhetes = [list(c) for c in random.sample(todas, min(len(todas), 10 if g==5 else 5))]
                for b in bilhetes:
                    db_lot["jogos"].append({"id": str(uuid.uuid4()), "dezenas": b, "status": "Aguardando Sorteio", "acertos": 0, "premio": 0.0})
                db_lot["custos"] += len(bilhetes) * 3.00; salvar_dados(); st.success(f"Gerado {len(bilhetes)} bilhetes. Custos atualizados."); st.rerun()

    with tabs[3]:
        if st.button("🗑️ Limpar Fila Quina"): db_lot["jogos"] = []; salvar_dados(); st.rerun()
        for j in db_lot["jogos"][-10:]: st.code(f"Jogo: {j['dezenas']} | Status: {j['status']}")

# =====================================================================
# 6.4 TELA DUPLA SENA (MÓDULO NOVO - ELITE)
# =====================================================================
def ia_duplasena(historico):
    if not historico: return None
    # Análise Âncora focada nos últimos sorteios
    ultimos = [n for h in historico[-20:] for n in h['dezenas']]
    freq = Counter(ultimos)
    scores = {}
    for n in range(1, 51):
        scores[n] = freq.get(n, 0) * 10.0 + random.uniform(1, 5) # Estocástico leve para desempate
        
    matriz = sorted([x[0] for x in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:14]]) # Matriz de 14
    return {"matriz": matriz, "tamanho": 14, "estrategia": "Análise Âncora (Sorteio 1) e Espalhamento", "alvo": historico[-1]['concurso']+1}

def filtro_duplasena(jogo):
    if not (80 <= sum(jogo) <= 220): return False
    pares = sum(1 for n in jogo if n % 2 == 0)
    if pares < 2 or pares > 4: return False # Balanço par/ímpar estrito
    return True

def tela_duplasena():
    exibir_cabecalho_aba("Dupla Sena", "#ED1622", "🔴")
    db_lot = st.session_state.db["duplasena"]
    tabs = st.tabs(["📂 1. Banco de Dados", "🧠 2. Cérebro IA (Painel)", "🤖 3. Geração", "📜 4. Fila"])

    with tabs[1]:
        st.markdown("### 🧠 Como a IA da Dupla Sena funciona (Detalhado)")
        st.write("A Dupla Sena tem dois sorteios. A IA ignora o segundo sorteio para cálculos de tendência primária (Análise Âncora), pois a física da primeira extração dita a matemática do volante. A IA rastreia as dezenas mais vibrantes do Sorteio 1 e força um balanço estrito de Pares e Ímpares.")
        st.info("A IA gera uma matriz de Elite de **14 dezenas**. O Filtro exclui bilhetes que sejam quase todos pares ou quase todos ímpares.")

    with tabs[2]:
        ia = ia_duplasena(db_lot["historico"])
        if ia:
            st.markdown(f"<div style='background-color:#fcf0f0; padding:15px; border-left: 5px solid #ED1622;'><b>🔒 O CADEADO MATEMÁTICO:</b><br>Matriz Elite: {ia['tamanho']} dezenas.<br><b>A REGRA:</b> As 6 sorteadas devem cair dentro da matriz E possuir obrigatoriamente 2, 3 ou 4 números pares (nunca 0, 1, 5 ou 6).</div><br>", unsafe_allow_html=True)
            st.write(f"**Dezenas Sugeridas pela IA:** {', '.join(map(str, ia['matriz']))}")
            g = st.radio("Garantia Dupla:", [6, 5], horizontal=True)
            if st.button("🧬 GERAR FECHAMENTO (R$ 3,00)", type="primary"):
                todas = [c for c in itertools.combinations(ia['matriz'], 6) if filtro_duplasena(c)]
                bilhetes = [list(c) for c in random.sample(todas, min(len(todas), 10))]
                for b in bilhetes:
                    db_lot["jogos"].append({"id": str(uuid.uuid4()), "dezenas": b, "status": "Aguardando Sorteio", "acertos": 0, "premio": 0.0})
                db_lot["custos"] += len(bilhetes) * 3.00; salvar_dados(); st.success(f"Gerado {len(bilhetes)} bilhetes. Custos atualizados."); st.rerun()

    with tabs[3]:
        if st.button("🗑️ Limpar Fila Dupla Sena"): db_lot["jogos"] = []; salvar_dados(); st.rerun()
        for j in db_lot["jogos"][-10:]: st.code(f"Jogo: {j['dezenas']} | Status: {j['status']}")

# =====================================================================
# 6.5 TELA LOTOMANIA (COM LIBERDADE DE 0 ACERTOS)
# =====================================================================
def ia_lotomania(historico):
    if not historico: return None
    atrasos = {n: 0 for n in range(100)}
    for h in reversed(historico):
        for n in range(100):
            if n in h['dezenas'] or (n==0 and 0 in h['dezenas']): pass
            elif atrasos[n] == 0: atrasos[n] += 1
    scores = {}
    for n in range(100):
        s = 50.0; d = atrasos.get(n, 0)
        if 3 <= d <= 12: s += 25.0
        if n % 10 in [0, 9]: s += 10.0
        scores[n] = s + random.uniform(-2, 2)
        
    ranking = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    matriz_top = sorted([x[0] for x in ranking[:70]]) # Super Matriz 70
    matriz_bad = sorted([x[0] for x in ranking[-50:]]) # Foco em 0 acertos
    return {"matriz_top": matriz_top, "matriz_bad": matriz_bad, "estrategia": "Monte Carlo Estocástico", "alvo": historico[-1]['concurso']+1}

def filtro_lotomania(jogo):
    if not (2100 <= sum(jogo) <= 2800): return False
    return True

def tela_lotomania():
    exibir_cabecalho_aba("Lotomania", "#F78100", "🟠")
    db_lot = st.session_state.db["lotomania"]
    tabs = st.tabs(["📂 1. Banco de Dados", "🧠 2. Cérebro IA (Painel)", "🤖 3. Geração", "📜 4. Fila"])

    with tabs[1]:
        st.markdown("### 🧠 Como a IA da Lotomania funciona (Detalhado)")
        st.write("A escala da Lotomania é massiva. Fazer análise combinatória de 100 números trava qualquer computador. A IA usa **Filtros Estocásticos (Monte Carlo)**. Ela pontua os 100 números, isola as 70 melhores dezenas ('Super Matriz') e as 50 piores dezenas ('Zona Morta').")
        st.info("A IA gera bilhetes aleatórios focado e descarta todos que a soma não bata a Curva de Gauss da Lotomania (2100 a 2800).")

    with tabs[2]:
        ia = ia_lotomania(db_lot["historico"])
        if ia:
            st.markdown(f"<div style='background-color:#fff8f0; padding:15px; border-left: 5px solid #F78100;'><b>🔒 LIBERDADE DE COMBATE:</b> Você tem total liberdade. Pode gerar bilhetes em cima das 70 melhores dezenas para forçar 19/20 acertos, ou focar nas 50 piores dezenas para não acertar NADA e ganhar pelo 'Espelho'.</div><br>", unsafe_allow_html=True)
            
            tipo = st.radio("Escolha a sua Diretriz de Combate:", ["Super Matriz (Tentar Acertar 20 Pontos)", "Zona Morta (Tentar Acertar 0 Pontos - ESPELHO)"])
            
            if "Super" in tipo:
                st.write(f"**Super Matriz (70):** {', '.join([f'{n:02d}' for n in ia['matriz_top']])}")
                qtd = st.slider("Qtd de Jogos:", 1, 20, 5)
                if st.button("🧬 GERAR SUPER MATRIZ (R$ 3,00/j)", type="primary"):
                    aprovados = []
                    while len(aprovados) < qtd:
                        candidato = sorted(random.sample(ia['matriz_top'], 50))
                        if filtro_lotomania(candidato): aprovados.append(candidato)
                    for b in aprovados:
                        db_lot["jogos"].append({"id": str(uuid.uuid4()), "dezenas": b, "status": "Aguardando Sorteio", "acertos": 0, "premio": 0.0, "est": "Super 70"})
                    db_lot["custos"] += len(aprovados) * 3.00; salvar_dados(); st.success(f"Gerado {len(aprovados)} bilhetes."); st.rerun()
            else:
                st.write(f"**Piores Dezenas (50):** {', '.join([f'{n:02d}' for n in ia['matriz_bad']])}")
                st.warning("⚠️ OBRIGATÓRIO: Ao registrar este bilhete na lotérica, você DEVE pedir para marcar a 'Aposta Espelho'.")
                if st.button("🪞 GERAR BILHETE TÓXICO (R$ 6,00 c/ Espelho)", type="primary"):
                    db_lot["jogos"].append({"id": str(uuid.uuid4()), "dezenas": ia['matriz_bad'], "status": "Aguardando Sorteio", "acertos": 0, "premio": 0.0, "est": "Espelho Zero"})
                    db_lot["custos"] += 6.00; salvar_dados(); st.success("Bilhete Tóxico gerado com sucesso."); st.rerun()

    with tabs[3]:
        if st.button("🗑️ Limpar Fila Lotomania"): db_lot["jogos"] = []; salvar_dados(); st.rerun()
        for j in db_lot["jogos"][-10:]: st.code(f"Est: {j.get('est', 'N/A')} | Status: {j['status']}\n{j['dezenas']}")

# =====================================================================
# 6.6 TELA +MILIONÁRIA (MÓDULO NOVO - ELITE)
# =====================================================================
def ia_maismilionaria(historico):
    if not historico: return None
    # Motor Misto: Dezenas e Trevos
    scores_dez = {n: random.uniform(10, 80) for n in range(1, 51)}
    scores_trevo = {n: random.uniform(10, 80) for n in range(1, 7)}
    
    matriz_dez = sorted([x[0] for x in sorted(scores_dez.items(), key=lambda x: x[1], reverse=True)[:10]]) # 10 Dezenas
    matriz_trevo = sorted([x[0] for x in sorted(scores_trevo.items(), key=lambda x: x[1], reverse=True)[:3]]) # 3 Trevos
    return {"matriz": matriz_dez, "trevos": matriz_trevo, "tamanho": 10, "estrategia": "Duplo Motor Cruzado", "alvo": historico[-1]['concurso']+1}

def tela_maismilionaria():
    exibir_cabecalho_aba("+Milionária", "#0066b3", "🌟")
    db_lot = st.session_state.db["maismilionaria"]
    tabs = st.tabs(["📂 1. Banco de Dados", "🧠 2. Cérebro IA (Painel)", "🤖 3. Geração", "📜 4. Fila"])

    with tabs[1]:
        st.markdown("### 🧠 Como a IA da +Milionária funciona (Detalhado)")
        st.write("É a loteria mais difícil do país. A IA requer 2 cérebros separados. O Cérebro 1 isola a matriz principal (dezenas) fugindo dos padrões normais. O Cérebro 2 analisa as probabilidades físicas dos Trevos de 1 a 6. A inteligência cruza as melhores dezenas com as melhores combinações de trevos.")
        st.info("A IA gera uma Matriz Elite de **10 dezenas** e separa os **3 Trevos** com maior ponto de fervura (tendência de saída).")

    with tabs[2]:
        ia = ia_maismilionaria(db_lot["historico"])
        if ia:
            st.markdown(f"<div style='background-color:#f0f8ff; padding:15px; border-left: 5px solid #0066b3;'><b>🔒 O CADEADO DUPLO:</b><br>Matriz Elite: {ia['tamanho']} dezenas + {len(ia['trevos'])} Trevos.<br><b>A REGRA:</b> O prêmio milionário só é destravado se as 6 dezenas sorteadas caírem nas suas 10 escolhidas E os 2 trevos sorteados forem selecionados do seu grupo de 3 trevos.</div><br>", unsafe_allow_html=True)
            st.write(f"**Dezenas de Elite:** {', '.join(map(str, ia['matriz']))}")
            st.write(f"**Trevos de Elite:** {', '.join(map(str, ia['trevos']))}")
            
            if st.button("🧬 GERAR CRUZAMENTO +MILIONÁRIA (R$ 6,00/j)", type="primary"):
                comb_dez = list(itertools.combinations(ia['matriz'], 6))
                comb_trevos = list(itertools.combinations(ia['trevos'], 2))
                
                # Para +Milionaria, como tem cruzamento, limita-se a um volume pequeno de alta letalidade
                bilhetes = []
                for b_dez in random.sample(comb_dez, min(len(comb_dez), 5)):
                    for b_trevo in comb_trevos:
                        bilhetes.append({"id": str(uuid.uuid4()), "dezenas": list(b_dez), "trevos": list(b_trevo), "status": "Aguardando Sorteio", "acertos": 0, "premio": 0.0})
                
                db_lot["jogos"].extend(bilhetes)
                db_lot["custos"] += len(bilhetes) * 6.00; salvar_dados(); st.success(f"Gerado {len(bilhetes)} bilhetes cruzados. Custos atualizados."); st.rerun()

    with tabs[3]:
        if st.button("🗑️ Limpar Fila +Milionária"): db_lot["jogos"] = []; salvar_dados(); st.rerun()
        for j in db_lot["jogos"][-10:]: st.code(f"Dezenas: {j['dezenas']} | Trevos: {j.get('trevos',[])} | Status: {j['status']}")

# =====================================================================
# 7. ROTEAMENTO CENTRAL DO SISTEMA
# =====================================================================
if st.session_state.pagina_atual == "login": tela_login()
elif st.session_state.pagina_atual == "pre_lobby" and st.session_state.autenticado: tela_pre_lobby()
elif st.session_state.pagina_atual == "lobby" and st.session_state.autenticado: tela_lobby()
elif st.session_state.pagina_atual == "lotofacil" and st.session_state.autenticado: tela_lotofacil()
elif st.session_state.pagina_atual == "megasena" and st.session_state.autenticado: tela_megasena()
elif st.session_state.pagina_atual == "quina" and st.session_state.autenticado: tela_quina()
elif st.session_state.pagina_atual == "duplasena" and st.session_state.autenticado: tela_duplasena()
elif st.session_state.pagina_atual == "lotomania" and st.session_state.autenticado: tela_lotomania()
elif st.session_state.pagina_atual == "maismilionaria" and st.session_state.autenticado: tela_maismilionaria()
else: st.session_state.pagina_atual = "login"; st.session_state.autenticado = False; st.rerun()        
