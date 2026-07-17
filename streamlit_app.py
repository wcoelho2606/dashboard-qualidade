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

# Estilização CSS customizada corporativa (Layout e KPIs)
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
        
        /* Estilos do Fluxo de Tratativas */
        .fluxo-step {
            text-align: center;
            padding: 10px;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            line-height: 30px;
            margin: 0 auto 5px auto;
            font-size: 18px;
            font-weight: bold;
            border: 3px solid #E5E7EB;
        }
        .step-active { background-color: #3B82F6; color: white; border-color: #2563EB; }
        .step-done { background-color: #10B981; color: white; border-color: #059669; }
        .step-todo { background-color: #F3F4F6; color: #9CA3AF; border-color: #E5E7EB; }
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

# 2. Carregar e processar dados
def carregar_dados():
    try:
        resposta = supabase.table("alertas").select("*").execute()
        df = pd.DataFrame(resposta.data)
        if df.empty:
            return pd.DataFrame(), {}, {}, {}, pd.DataFrame()
        
        hoje = date.today()
        df['prazo'] = pd.to_datetime(df['prazo']).dt.date
        
        # Mantém cálculo de dias restantes dinâmicos para controle interno
        for index, row in df.iterrows():
            if row['status'] == '6. Encerramento':
                df.at[index, 'dias_restantes'] = 0
            else:
                df.at[index, 'dias_restantes'] = (row['prazo'] - hoje).days
        
        area_dist = df["area"].value_counts().to_dict()
        status_dist = df["status"].value_counts().to_dict()
        defeito_dist = df["defeito"].value_counts().to_dict()
        
        df_tempo = pd.DataFrame({
            "Mês": ["Fev/26", "Mar/26", "Abr/26", "Mai/26", "Jun/26", "Jul/26"],
            "Dias": [18.7, 15.2, 12.8, 14.2, 13.9, 14.2]
        })
        
        return df, area_dist, status_dist, defeito_dist, df_tempo
    except Exception as e:
        st.error(f"Erro ao consultar a tabela: {e}")
        return pd.DataFrame(), {}, {}, {}, pd.DataFrame()

df_alertas, area_dist, status_dist, defeito_dist, df_tempo = carregar_dados()

def colorir_status(val):
    if "Encerramento" in str(val): return 'background-color: #D1FAE5; color: #065F46; font-weight: bold; text-align: center;'
    elif "Emitido" in str(val): return 'background-color: #EFF6FF; color: #1E40AF; font-weight: bold; text-align: center;'
    return 'background-color: #FEF3C7; color: #92400E; font-weight: bold; text-align: center;'

# --- MENU LATERAL DE NAVEGAÇÃO COMPLETO ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield-with-growth-chart.png", width=80)
    st.markdown("### GESTÃO DE ALERTAS")
    st.markdown("Supabase + Streamlit Cloud")
    st.markdown("---")
    menu_opcao = st.radio("Navegação", ["🏠 Visão Geral", "➕ Novo Alerta", "🔔 Em Andamento", "📄 Relatórios"])

if df_alertas.empty:
    st.warning("Aguardando carregamento ou sem dados cadastrados no Supabase.")
    st.stop()

# --- TELA: VISÃO GERAL ---
if menu_opcao == "🏠 Visão Geral":
    st.title("GESTÃO DE ALERTAS DE QUALIDADE")
    st.markdown("---")

    # KPIs
    total_alertas = len(df_alertas)
    abertos = len(df_alertas[df_alertas['status'] != '6. Encerramento'])
    encerrados = len(df_alertas[df_alertas['status'] == '6. Encerramento'])
    
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.markdown(f'<div class="kpi-card" style="background-color: #0E4687;"><div class="kpi-title">TOTAL DE ALERTAS</div><div class="kpi-value">{total_alertas}</div></div>', unsafe_allow_html=True)
    with kpi2:
        st.markdown(f'<div class="kpi-card" style="background-color: #F59E0B;"><div class="kpi-title">ALERTAS EM TRATATIVA</div><div class="kpi-value">{abertos}</div></div>', unsafe_allow_html=True)
    with kpi3:
        st.markdown(f'<div class="kpi-card" style="background-color: #10B981;"><div class="kpi-title">ALERTAS ENCERRADOS</div><div class="kpi-value">{encerrados}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Seleção Dinâmica do Alerta para a Tratativa
    st.markdown("### 📋 SELEÇÃO E FLUXO DE TRATATIVAS")
    lista_aqs = df_alertas["id"].tolist()
    alerta_selecionado = st.selectbox("Selecione qual Ocorrência / AQ deseja analisar e avançar no fluxo:", lista_aqs)
    
    item_aq = df_alertas[df_alertas['id'] == alerta_selecionado].iloc[0]
    status_atual = item_aq['status']

    # ====== PIPELINE VISUAL DO FLUXO (IDÊNTICO À FOTO) ======
    with st.container(border=True):
        st.markdown("<h5 style='text-align: center; color: #1E3A8A;'>FLUXO DE TRATATIVAS VIGENTE</h5>", unsafe_allow_html=True)
        
        # Mapeamento interno numérico das fases
        fases = {
            "1. Alerta Emitido": 1, "2. Em Análise": 2, "3. Ação Definida": 3,
            "4. Em Implementação": 4, "5. Aguardando Validação": 5, "6. Encerramento": 6
        }
        num_fase_atual = fases.get(status_atual, 1)

        def get_classe(passo):
            if num_fase_atual == passo: return "step-active"
            return "step-done" if num_fase_atual > passo else "step-todo"

        c1, s1, c2, s2, c3, s3, c4, s4, c5, s5, c6 = st.columns([1, 0.2, 1, 0.2, 1, 0.2, 1, 0.2, 1, 0.2, 1])
        
        with c1:
            st.markdown(f'<div class="fluxo-step {get_classe(1)}">1</div><p style="font-size:11px; text-align:center; font-weight:bold; margin:0;">Alerta Emitido<br><small>Qualidade</small></p>', unsafe_allow_html=True)
        with s1: st.markdown("<h3 style='text-align:center; color:gray; margin-top:5px;'>➔</h3>", unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="fluxo-step {get_classe(2)}">2</div><p style="font-size:11px; text-align:center; font-weight:bold; margin:0;">Em Análise<br><small>Responsável</small></p>', unsafe_allow_html=True)
        with s2: st.markdown("<h3 style='text-align:center; color:gray; margin-top:5px;'>➔</h3>", unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="fluxo-step {get_classe(3)}">3</div><p style="font-size:11px; text-align:center; font-weight:bold; margin:0;">Ação Definida<br><small>Responsável</small></p>', unsafe_allow_html=True)
        with s3: st.markdown("<h3 style='text-align:center; color:gray; margin-top:5px;'>➔</h3>", unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="fluxo-step {get_classe(4)}">4</div><p style="font-size:11px; text-align:center; font-weight:bold; margin:0;">Em Implementação<br><small>Responsável</small></p>', unsafe_allow_html=True)
        with s4: st.markdown("<h3 style='text-align:center; color:gray; margin-top:5px;'>➔</h3>", unsafe_allow_html=True)
        with c5:
            st.markdown(f'<div class="fluxo-step {get_classe(5)}">5</div><p style="font-size:11px; text-align:center; font-weight:bold; margin:0;">Aguardando Validação<br><small>Qualidade</small></p>', unsafe_allow_html=True)
        with s5: st.markdown("<h3 style='text-align:center; color:gray; margin-top:5px;'>➔</h3>", unsafe_allow_html=True)
        with c6:
            st.markdown(f'<div class="fluxo-step {get_classe(6)}">6</div><p style="font-size:11px; text-align:center; font-weight:bold; margin:0;">Encerrado<br><small>Qualidade</small></p>', unsafe_allow_html=True)

    # ====== PAINEL DE AÇÃO E ENTRADA DE DADOS DO OPERADOR ======
    st.markdown("<br>", unsafe_allow_html=True)
    col_tab, col_interacao = st.columns([2.5, 1.8])

    with col_tab:
        st.markdown("##### Todos os Alertas Registrados no Sistema")
        df_display = df_alertas[["id", "produto", "lote", "defeito", "area", "responsavel", "status"]].copy()
        df_display.columns = ["Nº AQ", "Produto", "Lote", "Defeito", "Área", "Responsável", "Status da Tratativa"]
        st.dataframe(df_display.style.map(colorir_status, subset=["Status da Tratativa"]), use_container_width=True, hide_index=True)

    with col_interacao:
        with st.container(border=True):
            st.markdown(f"<h5 style='color:#0E4687; margin:0;'>🛠️ INTERAÇÃO DA AQ: {alerta_selecionado}</h5>", unsafe_allow_html=True)
            st.markdown(f"**Defeito Original:** {item_aq['defeito']} | **Responsável Atual:** {item_aq['responsavel']}")
            st.markdown(f"**Status Vigente:** `{status_atual}`")
            st.divider()

            # Lógica interativa dinâmica baseada em qual bolinha o processo se encontra
            if status_atual == "1. Alerta Emitido":
                st.info("ℹ️ Aguardando o Responsável Técnico dar o OK de recebimento para iniciar a análise.")
                if st.button("✔️ [RESPONSÁVEL] Dar OK e Iniciar Análise", use_container_width=True, type="primary"):
                    supabase.table("alertas").update({"status": "2. Em Análise"}).eq("id", alerta_selecionado).execute()
                    st.success("Status atualizado para 'Em Análise' com sucesso!")
                    st.cache_data.clear()
                    st.rerun()

            elif status_atual == "2. Em Análise":
                st.warning("📝 Etapa de Análise. Por favor, adicione as ações corretivas e preventivas necessárias abaixo.")
                nova_acao = st.text_area("Descreva a Ação Definida para correção do problema:")
                responsavel_implementar = st.text_input("Nome de quem vai implementar essa ação:")
                
                if st.button("💾 Gravar Ação e Avançar Status", use_container_width=True, type="primary"):
                    if not nova_acao or not responsavel_implementar:
                        st.error("Por favor, preencha a descrição da ação e defina o responsável!")
                    else:
                        obs_atualizada = f"AÇÃO DEFINIDA: {nova_acao}. Responsável da Ação: {responsavel_implementar}."
                        supabase.table("alertas").update({
                            "status": "3. Ação Definida",
                            "observacoes": obs_atualizada
                        }).eq("id", alerta_selecionado).execute()
                        st.success("Ação salva! Status avançado para 'Ação Definida'.")
                        st.cache_data.clear()
                        st.rerun()

            elif status_atual == "3. Ação Definida":
                st.info("ℹ️ Ação mapeada no sistema. O responsável deve dar o OK assim que iniciar a execução física no chão de fábrica.")
                if st.button("🚀 Iniciar Implementação da Ação", use_container_width=True, type="primary"):
                    supabase.table("alertas").update({"status": "4. Em Implementação"}).eq("id", alerta_selecionado).execute()
                    st.cache_data.clear()
                    st.rerun()

            elif status_atual == "4. Em Implementação":
                st.warning("⚡ Ação em andamento na produção. Assim que concluir a correção, envie para a validação da Qualidade.")
                if st.button("✔️ Concluir Execução e Enviar para Validação da Qualidade", use_container_width=True, type="primary"):
                    supabase.table("alertas").update({"status": "5. Aguardando Validação"}).eq("id", alerta_selecionado).execute()
                    st.cache_data.clear()
                    st.rerun()

            elif status_atual == "5. Aguardando Validação":
                st.subheader("🛡️ Área Exclusiva da Qualidade")
                st.caption("Verifique no chão de fábrica se a não-conformidade foi corrigida de forma eficaz e dê o veredito.")
                
                if st.button("🔒 Ação Corrigida com Eficácia - ENCERRAR ALERTA", use_container_width=True, type="primary"):
                    supabase.table("alertas").update({"status": "6. Encerramento"}).eq("id", alerta_selecionado).execute()
                    st.success("🎉 Alerta validado e Encerrado com Sucesso pela Qualidade!")
                    st.cache_data.clear()
                    st.rerun()

            elif status_atual == "6. Encerramento":
                st.success("✅ Este alerta já passou por todo o fluxo regulamentar e foi devidamente Encerrado pela Engenharia da Qualidade.")

    # ------ MANTÉM OS 4 GRÁFICOS REESTRUTURADOS ABAIXO ------
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### INDICADORES E ANÁLISES GRÁFICAS")
    g_col1, g_col2, g_col3, g_col4 = st.columns(4)

    with g_col1:
        with st.container(border=True):
            if area_dist:
                fig1 = go.Figure(data=[go.Pie(labels=list(area_dist.keys()), values=list(area_dist.values()), hole=0.5, textinfo='label+value+percent', textposition='outside', showlegend=False)])
                fig1.update_layout(title=dict(text="<b>ALERTAS POR ÁREA</b>", x=0.5, y=0.95, font=dict(size=13, color="#1E3A8A")), margin=dict(l=30, r=30, t=50, b=30), height=250, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})

    with g_col2:
        with st.container(border=True):
            if status_dist:
                total_status = sum(status_dist.values())
                legenda_formatada = [f"{lbl}<br>{val} ({val/total_status*100:.1f}%)" for lbl, val in zip(status_dist.keys(), status_dist.values())]
                fig2 = go.Figure(data=[go.Pie(labels=legenda_formatada, values=list(status_dist.values()), hole=0.5, textinfo='none', showlegend=True)])
                fig2.update_layout(title=dict(text="<b>ALERTAS POR STATUS</b>", x=0.5, y=0.95, font=dict(size=13, color="#1E3A8A")), margin=dict(l=10, r=10, t=50, b=10), height=250, legend=dict(orientation="v", valign="middle", x=0.85, y=0.5, font=dict(size=9)), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

    with g_col3:
        with st.container(border=True):
            if defeito_dist:
                df_def = pd.DataFrame(list(defeito_dist.items()), columns=['Defeito', 'Qtd']).sort_values(by='Qtd', ascending=True)
                fig3 = go.Figure(go.Bar(x=df_def['Qtd'], y=df_def['Defeito'], orientation='h', marker_color='#0E4687', text=df_def['Qtd'], textposition='outside', textfont=dict(size=11, color='#374151', weight='bold')))
                fig3.update_layout(title=dict(text="<b>ALERTAS POR TIPO DE DEFEITO</b>", x=0.5, y=0.95, font=dict(size=13, color="#1E3A8A")), margin=dict(l=10, r=30, t=50, b=10), height=250, xaxis=dict(showgrid=False, visible=False), yaxis=dict(showgrid=False, tickfont=dict(size=11)), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})

    with g_col4:
        with st.container(border=True):
            if not df_tempo.empty:
                fig4 = go.Figure()
                fig4.add_trace(go.Scatter(x=df_tempo["Mês"], y=df_tempo["Dias"], mode='lines+markers+text', text=df_tempo["Dias"], textposition='top center', textfont=dict(size=11, color='#374151', weight='bold'), line=dict(color='#0284C7', width=2.5), marker=dict(size=7, color='#0284C7')))
                fig4.update_layout(title=dict(text="<b>TEMPO MÉDIO DE FECHAMENTO (DIAS)</b>", x=0.5, y=0.95, font=dict(size=13, color="#1E3A8A")), margin=dict(l=20, r=20, t=50, b=10), height=250, xaxis=dict(showgrid=False), yaxis=dict(showgrid=False, range=[0, 35], tickfont=dict(size=10)), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar': False})

# --- 2. TELA: NOVO ALERTA (CADASTRO) ---
elif menu_opcao == "➕ Novo Alerta":
    st.title("➕ CADASTRAR NOVO ALERTA")
    st.markdown("---")
    with st.form("form_novo_alerta", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            id_alerta = st.text_input("Nº do Alerta (ID)", placeholder="Ex: AQ-2026-032")
            produto = st.text_input("Código do Produto", placeholder="Ex: 41.6830.010")
            lote = st.text_input("Lote", placeholder="Ex: 474950")
            defeito = st.text_input("Defeito Detectado", placeholder="Ex: Rebarba excessiva")
        with col2:
            area = st.selectbox("Área Responsável", ["Produção", "Ferramentaria", "Processo", "Injeção", "Qualidade"])
            responsavel = st.text_input("Nome do Responsável", placeholder="Ex: João Silva")
            prazo = st.date_input("Prazo para Ação", value=date.today())
            
        submetido = st.form_submit_button("Gravar Ocorrência no Banco")
        if submetido:
            if not id_alerta or not produto or not lote or not defeito or not responsavel:
                st.warning("⚠️ Preencha todos os campos obrigatórios!")
            else:
                novo_registro = {
                    "id": id_alerta, "produto": produto, "lote": lote, "defeito": defeito,
                    "area": area, "responsavel": responsavel, "prazo": prazo.strftime("%Y-%m-%d"),
                    "dias_restantes": 5, "status": "1. Alerta Emitido" # Começa na bolinha 1
                }
                try:
                    supabase.table("alertas").insert(novo_registro).execute()
                    st.success(f"🎉 Alerta {id_alerta} salvo com sucesso no fluxo!")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# --- Restante das páginas mantido apenas para conformidade estrutural ---
elif menu_opcao == "🔔 Em Andamento":
    st.title("🔔 ALERTAS EM ANDAMENTO")
    st.dataframe(df_alertas[df_alertas['status'] != '6. Encerramento'], use_container_width=True, hide_index=True)

elif menu_opcao == "📄 Relatórios":
    st.title("📄 RELATÓRIOS")
    st.dataframe(df_alertas, use_container_width=True, hide_index=True)
