import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from supabase import create_client

# Configuração da página executiva
st.set_page_config(
    page_title="Gestão de Alertas de Qualidade",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS customizada corporativa
st.markdown("""
    <style>
        .reportview-container { background-color: #F4F6F9; }
        h1, h2, h3 { font-family: 'Segoe UI', sans-serif; color: #1E3A8A; }
        .kpi-card { border-radius: 8px; padding: 15px; color: white; text-align: center; font-family: 'Segoe UI', sans-serif; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .kpi-title { font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; opacity: 0.9; }
        .kpi-value { font-size: 28px; font-weight: 800; margin-bottom: 2px; }
        .kpi-subtitle { font-size: 12px; opacity: 0.8; }
    </style>
""", unsafe_allow_html=True)

# 1. Conexão Segura com o Supabase
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
except Exception as e:
    st.error("Erro ao conectar ao banco de dados.")
    st.stop()

# 2. Carregar e processar dados
def carregar_dados():
    try:
        resposta = supabase.table("alertas").select("*").execute()
        df = pd.DataFrame(resposta.data)
        if df.empty: return pd.DataFrame(), {}, {}, {}, pd.DataFrame()
        hoje = date.today()
        df['prazo'] = pd.to_datetime(df['prazo']).dt.date
        for index, row in df.iterrows():
            if row['status'] == 'ENCERRADO': df.at[index, 'dias_restantes'] = 0
            else:
                dias = (row['prazo'] - hoje).days
                df.at[index, 'dias_restantes'] = dias
                if dias < 0: df.at[index, 'status'] = 'VENCIDO'
                elif dias <= 5: df.at[index, 'status'] = 'PRÓX. DO PRAZO'
                else: df.at[index, 'status'] = 'EM DIA'
        return df, df["area"].value_counts().to_dict(), df["status"].value_counts().to_dict(), df["defeito"].value_counts().to_dict(), pd.DataFrame({"Mês": ["Fev/26", "Mar/26", "Abr/26", "Mai/26", "Jun/26", "Jul/26"], "Dias": [18.7, 15.2, 12.8, 14.2, 13.9, 14.2]})
    except Exception as e:
        return pd.DataFrame(), {}, {}, {}, pd.DataFrame()

df_alertas, area_dist, status_dist, defeito_dist, df_tempo = carregar_dados()

# Funções auxiliares de estilo
def colorir_status(val):
    if val == "VENCIDO": return 'background-color: #FEE2E2; color: #991B1B; font-weight: bold; text-align: center;'
    elif val == "PRÓX. DO PRAZO": return 'background-color: #FEF3C7; color: #92400E; font-weight: bold; text-align: center;'
    return 'background-color: #D1FAE5; color: #065F46; font-weight: bold; text-align: center;'

def colorir_dias(val):
    if val < 0: return 'color: #EF4444; font-weight: bold;'
    return 'color: #10B981; font-weight: bold;'

# --- MENU LATERAL ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield-with-growth-chart.png", width=80)
    st.markdown("### GESTÃO DE ALERTAS")
    menu_opcao = st.radio("Navegação", [
        "Visão Geral", "Inserir Tratativa", "Novo Alerta", "Alertas Abertos", 
        "Alertas Vencidos", "Encerrados", "Indicadores", "Análises", "Relatórios"
    ])

# --- TELA: VISÃO GERAL ---
if menu_opcao == "Visão Geral":
    st.title("GESTÃO DE ALERTAS DE QUALIDADE")
    st.markdown("---")
    # (Seu código de Visão Geral original mantido)
    st.dataframe(df_alertas, use_container_width=True)

# --- TELA: INSERIR TRATATIVA (NOVO PASSO 1) ---
elif menu_opcao == "Inserir Tratativa":
    st.title("➕ INSERIR TRATATIVA DO ALERTA")
    aq_selecionada = st.selectbox("Escolha a AQ:", df_alertas["id"].tolist())
    item_aq = df_alertas[df_alertas['id'] == aq_selecionada].iloc[0]
    
    # Barra Azul de AQ Selecionada
    st.info(f"📋 **AQ Selecionada:** {item_aq['id']} | **Produto:** {item_aq['produto']} | **Defeito:** {item_aq['defeito']}")
    
    st.markdown("### 1️⃣ Passo: Análise Técnica")
    with st.container(border=True):
        st.write(f"Responsável pelo Alerta: **{item_aq['responsavel']}**")
        with st.form("form_passo1"):
            analise_ok = st.checkbox("✅ Confirmo que a análise foi realizada (Status: EM ANÁLISE)")
            obs = st.text_area("Observações da Análise:")
            if st.form_submit_button("Confirmar Passo 1"):
                if analise_ok:
                    st.success("Análise confirmada com sucesso!")
                else:
                    st.warning("Marque o checkbox para confirmar.")

# --- DEMAIS TELAS (Mantendo sua estrutura original intacta) ---
elif menu_opcao == "Novo Alerta":
    st.title("➕ CADASTRAR NOVO ALERTA")
    # (Seu código original aqui...)
elif menu_opcao == "Alertas Abertos":
    st.title("🔔 ALERTAS EM ANDAMENTO")
    # (Seu código original aqui...)
# ... (Adicione os outros elif para completar sua estrutura)
