import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from supabase import create_client

# Configuração da página executiva
st.set_page_config(page_title="Gestão de Alertas de Qualidade", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

# Estilização CSS original
st.markdown("""
    <style>
        .reportview-container { background-color: #F4F6F9; }
        h1, h2, h3 { font-family: 'Segoe UI', sans-serif; color: #1E3A8A; }
        .kpi-card { border-radius: 8px; padding: 15px; color: white; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .kpi-title { font-size: 11px; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; opacity: 0.9; }
        .kpi-value { font-size: 28px; font-weight: 800; margin-bottom: 2px; }
    </style>
""", unsafe_allow_html=True)

# Conexão e Carregamento (Otimizado)
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

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

# Funções de Estilização
def colorir_status(val):
    if val == "VENCIDO": return 'background-color: #FEE2E2; color: #991B1B;'
    elif val == "PRÓX. DO PRAZO": return 'background-color: #FEF3C7; color: #92400E;'
    return ''

# Menu Lateral
with st.sidebar:
    menu_opcao = st.radio("Navegação", [
        "Visão Geral", "Inserir Tratativa", "Novo Alerta", "Alertas Abertos", 
        "Alertas Vencidos", "Encerrados", "Indicadores", "Análises", "Relatórios"
    ])

# --- TELA: VISÃO GERAL ---
if menu_opcao == "Visão Geral":
    st.title("GESTÃO DE ALERTAS DE QUALIDADE")
    total, abertos, vencidos, encerrados = len(df_alertas), len(df_alertas[df_alertas['status'] != 'ENCERRADO']), len(df_alertas[df_alertas['status'] == 'VENCIDO']), len(df_alertas[df_alertas['status'] == 'ENCERRADO'])
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="kpi-card" style="background-color: #0E4687;"><div class="kpi-title">TOTAL</div><div class="kpi-value">{total}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi-card" style="background-color: #F59E0B;"><div class="kpi-title">ABERTOS</div><div class="kpi-value">{abertos}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi-card" style="background-color: #EF4444;"><div class="kpi-title">VENCIDOS</div><div class="kpi-value">{vencidos}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="kpi-card" style="background-color: #10B981;"><div class="kpi-title">ENCERRADOS</div><div class="kpi-value">{encerrados}</div></div>', unsafe_allow_html=True)
    st.markdown("### ALERTAS EM ABERTO")
    st.dataframe(df_alertas, use_container_width=True)

# --- TELA: INSERIR TRATATIVA (PASSO 1) ---
elif menu_opcao == "Inserir Tratativa":
    st.title("➕ INSERIR TRATATIVA DO ALERTA")
    aq_selecionada = st.selectbox("Escolha o Nº da AQ:", df_alertas["id"].tolist())
    item = df_alertas[df_alertas['id'] == aq_selecionada].iloc[0]
    st.info(f"📋 **AQ:** {item['id']} | **Produto:** {item['produto']} | **Defeito:** {item['defeito']}")
    
    st.markdown("### 1️⃣ Passo: Análise Técnica")
    with st.container(border=True):
        st.write(f"Responsável pela Análise: **{item['responsavel']}**")
        with st.form("form_passo1"):
            analise_ok = st.checkbox("✅ Confirmo que a análise foi realizada e os dados estão corretos (Status: EM ANÁLISE)")
            obs = st.text_area("Observações da Análise:")
            if st.form_submit_button("Confirmar Passo 1"):
                if analise_ok:
                    st.success("Análise confirmada com sucesso!")
                    st.balloons()
                else:
                    st.warning("Por favor, marque o checkbox para confirmar a análise.")

# --- DEMAIS TELAS (Mantendo sua estrutura original) ---
elif menu_opcao == "Novo Alerta":
    st.title("CADASTRAR NOVO ALERTA")
    # ... aqui entra o seu código de cadastro de alertas ...

elif menu_opcao == "Alertas Abertos":
    st.title("ALERTAS ABERTOS")
    st.dataframe(df_alertas[df_alertas['status'] != 'ENCERRADO'], use_container_width=True)

elif menu_opcao == "Relatórios":
    st.title("RELATÓRIOS")
    st.dataframe(df_alertas, use_container_width=True)
