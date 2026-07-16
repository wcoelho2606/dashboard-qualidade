import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, date
from supabase import create_client

# Configuração da página
st.set_page_config(
    page_title="Gestão de Alertas de Qualidade",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS customizada
st.markdown("""
    <style>
        .reportview-container { background-color: #F4F6F9; }
        h1, h2, h3 { font-family: 'Segoe UI', sans-serif; color: #1E3A8A; }
        .kpi-card {
            border-radius: 8px; padding: 15px; color: white; text-align: center;
            font-family: 'Segoe UI', sans-serif; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
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
    st.error("Erro ao conectar ao banco de dados. Verifique as credenciais.")
    st.stop()

# 2. Carregar dados reais do Supabase
def carregar_dados():
    try:
        # Forçamos a limpeza do cache para que novos cadastros apareçam na hora
        resposta = supabase.table("alertas").select("*").execute()
        df = pd.DataFrame(resposta.data)
        if df.empty:
            return pd.DataFrame(), {}, {}, {}, pd.DataFrame()
        
        # Converter datas de string para o tipo date
        df['prazo'] = pd.to_datetime(df['prazo']).dt.date
        
        # Agregações para os gráficos
        area_dist = df["area"].value_counts().to_dict()
        status_dist = df["status"].value_counts().to_dict()
        defeito_dist = df["defeito"].value_counts().to_dict()
        
        # Histórico estático de tempo de fechamento
        df_tempo = pd.DataFrame({
            "Mês": ["Fev/26", "Mar/26", "Abr/26", "Mai/26", "Jun/26", "Jul/26"],
            "Dias": [18.7, 15.2, 12.8, 14.2, 13.9, 14.2]
        })
        
        return df, area_dist, status_dist, defeito_dist, df_tempo
    except Exception as e:
        st.error(f"Erro ao consultar a tabela: {e}")
        return pd.DataFrame(), {}, {}, {}, pd.DataFrame()

df_alertas, area_dist, status_dist, defeito_dist, df_tempo = carregar_dados()

# Sidebar de navegação
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield-with-growth-chart.png", width=80)
    st.markdown("### GESTÃO DE ALERTAS")
    st.markdown("Supabase + Streamlit Cloud")
    st.markdown("---")
    
    menu_opcao = st.radio(
        "Navegação",
        ["🏠 Visão Geral", "➕ Novo Alerta", "🔔 Alertas Abertos", "✔️ Encerrados"],
        index=0
    )
    st.markdown("---")
    st.markdown("<small style='color: gray;'>Sincronizado em tempo real</small>", unsafe_allow_html=True)

# --- TELA 1: VISÃO GERAL ---
if "Visão Geral" in menu_opcao:
    if not df_alertas.empty:
        st.title("GESTÃO DE ALERTAS DE QUALIDADE")
        st.markdown("##### Monitoramento integrado de não-conformidades em tempo real")
        st.markdown("---")

        # KPIs dinâmicos
        total_alertas = len(df_alertas)
        abertos = len(df_alertas[df_alertas['status'] != 'ENCERRADO'])
        vencidos = len(df_alertas[df_alertas['status'] == 'VENCIDO'])
        encerrados = len(df_alertas[df_alertas['status'] == 'ENCERRADO'])
        no_prazo = "82.1%"

        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        with kpi1:
            st.markdown(f'<div class="kpi-card" style="background-color: #0E4687;"><div class="kpi-title">TOTAL DE ALERTAS</div><div class="kpi-value">{total_alertas}</div><div class="kpi-subtitle">Registrados</div></div>', unsafe_allow_html=True)
        with kpi2:
            st.markdown(f'<div class="kpi-card" style="background-color: #F59E0B;"><div class="kpi-title">ALERTAS ABERTOS</div><div class="kpi-value">{abertos}</div><div class="kpi-subtitle">Em andamento</div></div>', unsafe_allow_html=True)
        with kpi3:
            st.markdown(f'<div class="kpi-card" style="background-color: #EF4444;"><div class="kpi-title">ALERTAS VENCIDOS</div><div class="kpi-value">{vencidos}</div><div class="kpi-subtitle">Ações atrasadas</div></div>', unsafe_allow_html=True)
        with kpi4:
            st.markdown(f'<div class="kpi-card" style="background-color: #10B981;"><div class="kpi-title">ALERTAS ENCERRADOS</div><div class="kpi-value">{encerrados}</div><div class="kpi-subtitle">Concluídos</div></div>', unsafe_allow_html=True)
        with kpi5:
            st.markdown(f'<div class="kpi-card" style="background-color: #F3F4F6; color: #1F2937; border: 1px solid #D1D5DB;"><div class="kpi-title" style="color: #4B5563;">% NO PRAZO</div><div class="kpi-value" style="color: #111827;">{no_prazo}</div><div class="kpi-subtitle" style="color: #6B7280;">Meta: 80%</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Tabela e detalhes
        st.markdown("### ALERTAS EM ABERTO")
        col_tabela, col_detalhes = st.columns([3, 1.2])

        with col_tabela:
            def colorir_status(val):
                if val == "VENCIDO": return 'background-color: #FEE2E2; color: #991B1B; font-weight: bold; text-align: center;'
                elif val == "PRÓX. DO PRAZO": return 'background-color: #FEF3C7; color: #92400E; font-weight: bold; text-align: center;'
                return 'background-color: #D1FAE5; color: #065F46; font-weight: bold; text-align: center;'

            def colorir_dias(val):
                if val <= 2: return 'color: #EF4444; font-weight: bold;'
                elif val <= 5: return 'color: #F59E0B; font-weight: bold;'
                return 'color: #10B981; font-weight: bold;'

            df_abertos = df_alertas[df_alertas['status'] != 'ENCERRADO'].copy()
            df_abertos.columns = ["Nº AQ", "Produto", "Lote", "Defeito", "Área Responsável", "Responsável", "Prazo", "Dias Restantes", "Status"]
            
            # Correção com .map() para Pandas modernos
            styler = df_abertos.style.map(colorir_status, subset=["Status"]).map(colorir_dias, subset=["Dias Restantes"])
            st.dataframe(styler, use_container_width=True, hide_index=True)

        with col_detalhes:
            primeiro = df_alertas.iloc[0]
            st.markdown(f"""
                <div style="background-color: #FFFFFF; padding: 20px; border-radius: 8px; border: 1px solid #E5E7EB; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <h4 style="color: #EF4444; margin-top: 0;">DETALHES DO SELECIONADO</h4>
                    <h3 style="margin: 5px 0 15px 0;">{primeiro['id']}</h3>
                    <p style="font-weight: bold; color: #4B5563; margin-bottom: 15px;">{primeiro['defeito']}</p>
                    <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                        <tr style="border-bottom: 1px solid #F3F4F6;"><td style="padding: 6px 0; color: #6B7280;">Produto:</td><td style="font-weight: 500; text-align: right;">{primeiro['produto']}</td></tr>
                        <tr style="border-bottom: 1px solid #F3F4F6;"><td style="padding: 6px 0; color: #6B7280;">Lote:</td><td style="font-weight: 500; text-align: right;">{primeiro['lote']}</td></tr>
                        <tr style="border-bottom: 1px solid #F3F4F6;"><td style="padding: 6px 0; color: #6B7280;">Responsável:</td><td style="font-weight: 500; text-align: right;">{primeiro['responsavel']}</td></tr>
                        <tr style="border-bottom: 1px solid #F3F4F6;"><td style="padding: 6px 0; color: #6B7280;">Prazo Ação:</td><td style="font-weight: bold; color: #EF4444; text-align: right;">{primeiro['prazo']}</td></tr>
                    </table>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Gráficos
        st.markdown("### INDICADORES E ANÁLISES GRÁFICAS")
        g_col1, g_col2, g_col3, g_col4 = st.columns(4)

        with g_col1:
            if area_dist:
                fig1 = px.pie(names=list(area_dist.keys()), values=list(area_dist.values()), hole=0.5, title="ALERTAS POR ÁREA", color_discrete_sequence=px.colors.qualitative.Pastel)
                fig1.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=230, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5))
                st.plotly_chart(fig1, use_container_width=True)
        with g_col2:
            if status_dist:
                fig2 = px.pie(names=list(status_dist.keys()), values=list(status_dist.values()), hole=0.5, title="ALERTAS POR STATUS", color_discrete_sequence=px.colors.qualitative.Safe)
                fig2.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=230, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5))
                st.plotly_chart(fig2, use_container_width=True)
        with g_col3:
            if defeito_dist:
                fig3 = px.bar(x=list(defeito_dist.values()), y=list(defeito_dist.keys()), orientation='h', title="ALERTAS POR DEFEITO", color_discrete_sequence=['#0E4687'])
                fig3.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=230, xaxis_title=None, yaxis_title=None)
                st.plotly_chart(fig3, use_container_width=True)
        with g_col4:
            if not df_tempo.empty:
                fig4 = px.line(df_tempo, x="Mês", y="Dias", markers=True, title="MÉDIA DE FECHAMENTO", color_discrete_sequence=['#0284C7'])
                fig4.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=230, xaxis_title=None, yaxis_title=None)
                st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("Nenhum dado encontrado no Supabase ou carregando...")

# --- TELA 2: FORMULÁRIO DE CADASTRO ---
elif "Novo Alerta" in menu_opcao:
    st.title("➕ CADASTRAR NOVO ALERTA")
    st.markdown("Insira as informações abaixo para abrir uma nova ocorrência no Supabase")
    st.markdown("---")
    
    with st.form("form_novo_alerta", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            id_alerta = st.text_input("Nº do Alerta (ID)", placeholder="Ex: AQ-2026-031")
            produto = st.text_input("Código do Produto", placeholder="Ex: 41.6830.050")
            lote = st.text_input("Lote", placeholder="Ex: 475310")
            defeito = st.text_input("Defeito Detectado", placeholder="Ex: Trinca superficial")
            
        with col2:
            area = st.selectbox("Área Responsável", ["Produção", "Ferramentaria", "Processo", "Injeção", "Qualidade"])
            responsavel = st.text_input("Nome do Responsável", placeholder="Ex: Marcelo Oliveira")
            prazo = st.date_input("Prazo para Ação", value=date.today())
            status = st.selectbox("Status Inicial", ["EM DIA", "PRÓX. DO PRAZO", "VENCIDO"])
            
        # Botão de envio
        submetido = st.form_submit_button("Gravar Ocorrência no Banco")
        
        if submetido:
            if not id_alerta or not produto or not lote or not defeito or not responsavel:
                st.warning("⚠️ Por favor, preencha todos os campos obrigatórios!")
            else:
                # Calcula os dias restantes baseado no prazo escolhido
                dias_restantes = (prazo - date.today()).days
                
                # Monta os dados para enviar ao Supabase
                novo_registro = {
                    "id": id_alerta,
                    "produto": produto,
                    "lote": lote,
                    "defeito": defeito,
                    "area": area,
                    "responsavel": responsavel,
                    "prazo": prazo.strftime("%Y-%m-%d"),
                    "dias_restantes": int(dias_restantes),
                    "status": status
                }
                
                try:
                    # Envia os dados reais para o banco Supabase
                    supabase.table("alertas").insert(novo_registro).execute()
                    st.success(f"🎉 Alerta {id_alerta} cadastrado com sucesso no Supabase!")
                    
                    # Força a atualização dos dados globais
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Erro ao salvar no banco de dados: {e}")

# --- TELAS ADICIONAIS (FILTROS) ---
elif "Alertas Abertos" in menu_opcao:
    st.title("🔔 ALERTAS EM ANDAMENTO")
    df_filtrado = df_alertas[df_alertas['status'] != 'ENCERRADO']
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

elif "Encerrados" in menu_opcao:
    st.title("✔️ ALERTAS ENCERRADOS")
    df_filtrado = df_alertas[df_alertas['status'] == 'ENCERRADO']
    if df_filtrado.empty:
        st.info("Nenhum alerta foi encerrado até o momento.")
    else:
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
