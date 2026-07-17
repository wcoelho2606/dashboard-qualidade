import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from supabase import create_client

# Configuração da página
st.set_page_config(page_title="Gestão de Alertas", layout="wide", initial_sidebar_state="expanded")

# CSS Corporativo
st.markdown("""
    <style>
        .kpi-card { border-radius: 8px; padding: 15px; color: white; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .kpi-title { font-size: 11px; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; opacity: 0.9; }
        .kpi-value { font-size: 28px; font-weight: 800; margin-bottom: 2px; }
    </style>
""", unsafe_allow_html=True)

# Conexão e Dados
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

@st.cache_data(ttl=60)
def carregar_dados():
    resposta = supabase.table("alertas").select("*").execute()
    df = pd.DataFrame(resposta.data)
    df['prazo'] = pd.to_datetime(df['prazo']).dt.date
    hoje = date.today()
    
    for index, row in df.iterrows():
        if row['status'] == 'ENCERRADO': df.at[index, 'dias_restantes'] = 0
        else:
            dias = (row['prazo'] - hoje).days
            df.at[index, 'dias_restantes'] = dias
            if dias < 0: df.at[index, 'status'] = 'VENCIDO'
            elif dias <= 5: df.at[index, 'status'] = 'PRÓX. DO PRAZO'
            else: df.at[index, 'status'] = 'EM DIA'
    return df

df_alertas = carregar_dados()

# Menu Lateral (Sem emojis nos nomes de navegação para evitar erro de sintaxe)
with st.sidebar:
    menu_opcao = st.radio("Navegação", [
        "Visão Geral", 
        "Inserir Tratativa", 
        "Novo Alerta",
        "Alertas Abertos", 
        "Alertas Vencidos", 
        "Encerrados", 
        "Indicadores"
    ])

# --- TELA: VISÃO GERAL ---
if menu_opcao == "Visão Geral":
    st.title("GESTÃO DE ALERTAS DE QUALIDADE")
    
    total = len(df_alertas)
    abertos = len(df_alertas[df_alertas['status'] != 'ENCERRADO'])
    vencidos = len(df_alertas[df_alertas['status'] == 'VENCIDO'])
    encerrados = len(df_alertas[df_alertas['status'] == 'ENCERRADO'])
    
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="kpi-card" style="background-color: #0E4687;"><div class="kpi-title">TOTAL</div><div class="kpi-value">{total}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi-card" style="background-color: #F59E0B;"><div class="kpi-title">ABERTOS</div><div class="kpi-value">{abertos}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi-card" style="background-color: #EF4444;"><div class="kpi-title">VENCIDOS</div><div class="kpi-value">{vencidos}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="kpi-card" style="background-color: #10B981;"><div class="kpi-title">ENCERRADOS</div><div class="kpi-value">{encerrados}</div></div>', unsafe_allow_html=True)

    st.markdown("### ALERTAS EM ABERTO")
    st.dataframe(df_alertas[df_alertas['status'] != 'ENCERRADO'], use_container_width=True)

# --- TELA: INSERIR TRATATIVA (PASSO 1) ---
elif menu_opcao == "Inserir Tratativa":
    st.title("➕ INSERIR TRATATIVA DO ALERTA")
    lista_aqs = df_alertas["id"].tolist()
    aq_selecionada = st.selectbox("Escolha a AQ:", lista_aqs)
    item = df_alertas[df_alertas['id'] == aq_selecionada].iloc[0]
    
    st.info(f"AQ: {item['id']} | Produto: {item['produto']}")
    
    st.markdown("### 1️⃣ Passo: Análise Técnica")
    with st.container(border=True):
        st.markdown(f"👤 **Responsável:** `{item['responsavel']}`")
        with st.form("form_passo1"):
            analise_ok = st.checkbox("Confirmo que a análise técnica foi realizada.")
            obs = st.text_area("Observações:")
            if st.form_submit_button("Confirmar Passo 1"):
                if analise_ok: st.success("Passo 1 finalizado!")
                else: st.warning("Marque o checkbox.")

# Adicione aqui os outros elif para as outras telas (Novo Alerta, etc)
