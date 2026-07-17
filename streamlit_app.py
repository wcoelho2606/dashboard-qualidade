import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from supabase import create_client

# Configuração da página
st.set_page_config(
    page_title="Gestão de Alertas de Qualidade",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS
st.markdown("""
    <style>
        .reportview-container { background-color: #F4F6F9; }
        h1, h2, h3 { font-family: 'Segoe UI', sans-serif; color: #1E3A8A; }
        .kpi-card { border-radius: 8px; padding: 15px; color: white; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .kpi-title { font-size: 11px; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; opacity: 0.9; }
        .kpi-value { font-size: 28px; font-weight: 800; margin-bottom: 2px; }
    </style>
""", unsafe_allow_html=True)

# 1. Conexão Supabase
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
except:
    st.error("Erro na conexão com o banco.")
    st.stop()

# 2. Carregar dados
def carregar_dados():
    try:
        resposta = supabase.table("alertas").select("*").execute()
        df = pd.DataFrame(resposta.data)
        if df.empty: return pd.DataFrame(), {}, {}, {}, pd.DataFrame()
        df['prazo'] = pd.to_datetime(df['prazo']).dt.date
        return df, df["area"].value_counts().to_dict(), df["status"].value_counts().to_dict(), df["defeito"].value_counts().to_dict(), pd.DataFrame()
    except:
        return pd.DataFrame(), {}, {}, {}, pd.DataFrame()

df_alertas, area_dist, status_dist, defeito_dist, df_tempo = carregar_dados()

# --- MENU LATERAL ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield-with-growth-chart.png", width=80)
    menu_opcao = st.radio(
        "Navegação",
        [
            "🏠 Visão Geral", 
            "Inserir Tratativa", 
            "➕ Novo Alerta",
            "🔔 Alertas Abertos", 
            "⏰ Alertas Vencidos", 
            "✔️ Encerrados", 
            "📊 Indicadores", 
            "📈 Análises", 
            "📄 Relatórios"
        ]
    )

if df_alertas.empty:
    st.warning("Sem dados.")
    st.stop()

# --- TELAS ---
if menu_opcao == "🏠 Visão Geral":
    st.title("GESTÃO DE ALERTAS")
    # (KPIs mantidos aqui...)
    st.write("Bem-vindo ao painel.")

elif menu_opcao == "Inserir Tratativa":
    st.title("➕ INSERIR TRATATIVA DO ALERTA")
    st.markdown("---")
    
    lista_aqs = df_alertas["id"].tolist()
    aq_selecionada = st.selectbox("Escolha o Nº da AQ para preencher:", lista_aqs)
    item_aq = df_alertas[df_alertas['id'] == aq_selecionada].iloc[0]
    
    st.info(f"📋 **AQ:** {item_aq['id']} | **Produto:** {item_aq['produto']} | **Defeito:** {item_aq['defeito']}")
    
    # --- PASSO 1 ---
    st.markdown("### 1️⃣ Passo: Análise Técnica")
    with st.container(border=True):
        st.markdown(f"👤 **Responsável pela Análise:** `{item_aq['responsavel']}`")
        with st.form("form_passo1"):
            analise_ok = st.checkbox("✅ Confirmo que a análise técnica foi realizada.")
            obs_analise = st.text_area("Observações da Análise:")
            if st.form_submit_button("Confirmar Passo 1"):
                if analise_ok:
                    st.success(f"Passo 1 finalizado por {item_aq['responsavel']}!")
                    st.balloons()
                else:
                    st.warning("Marque o checkbox para confirmar.")

elif menu_opcao == "➕ Novo Alerta":
    st.title("➕ CADASTRAR NOVO ALERTA")
    # (Seu código de cadastro aqui...)

# (Manter o restante das opções elif...)
