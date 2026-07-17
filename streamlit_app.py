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
    </style>
""", unsafe_allow_html=True)
 
# 1. Conexão Secura com o Supabase
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
 
# 2. Carregar e processar dados de forma dinâmica e em tempo real
def carregar_dados():
    try:
        resposta = supabase.table("alertas").select("*").execute()
        df = pd.DataFrame(resposta.data)
        if df.empty:
            return pd.DataFrame(), {}, {}, {}, pd.DataFrame()
        
        hoje = date.today()
        df['prazo'] = pd.to_datetime(df['prazo']).dt.date
        
        # ====== RECALCULO DINÂMICO DE PRAZOS E STATUS ======
        for index, row in df.iterrows():
            if row['status'] == 'ENCERRADO':
                df.at[index, 'dias_restantes'] = 0
            else:
                dias = (row['prazo'] - hoje).days
                df.at[index, 'dias_restantes'] = dias
                if dias < 0:
                    df.at[index, 'status'] = 'VENCIDO'
                elif dias <= 5:
                    df.at[index, 'status'] = 'PRÓX. DO PRAZO'
                else:
                    df.at[index, 'status'] = 'EM DIA'
        
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
 
# Funções auxiliares para estilização visual de tabelas
def colorir_status(val):
    if val == "VENCIDO": return 'background-color: #FEE2E2; color: #991B1B; font-weight: bold; text-align: center;'
    elif val == "PRÓX. DO PRAZO": return 'background-color: #FEF3C7; color: #92400E; font-weight: bold; text-align: center;'
    elif val == "EM DIA": return 'background-color: #D1FAE5; color: #065F46; font-weight: bold; text-align: center;'
    return 'background-color: #F3F4F6; color: #374151; text-align: center;'
 
def colorir_dias(val):
    if val < 0: return 'color: #EF4444; font-weight: bold;'
    elif val <= 5: return 'color: #F59E0B; font-weight: bold;'
    return 'color: #10B981; font-weight: bold;'
 
# --- MENU LATERAL DE NAVEGAÇÃO COMPLETO ---
with st.sidebar:
   st.image("https://img.icons8.com/fluency/96/shield-with-growth-chart.png", width=80)
   st.markdown("### GESTÃO DE ALERTAS")
   st.markdown("Supabase + Streamlit Cloud")
   st.markdown("---")
    
   menu_opcao = st.radio(
       "Navegação",
        [
            "🏠 Visão Geral", 
            "➕ Inserir Tratativa", # Nova opção adicionada aqui
            "➕ Novo Alerta",
            "🔔 Alertas Abertos", 
            "⏰ Alertas Vencidos", 
            "✔️ Encerrados", 
            "📊 Indicadores", 
            "📈 Análises", 
            "📄 Relatórios"
        ],
        index=0
   )
   st.markdown("---")
   st.markdown("<small style='color: gray;'>Painel Sincronizado</small>", unsafe_allow_html=True)
 
if df_alertas.empty:
   st.warning("Aguardando carregamento ou sem dados cadastrados no Supabase.")
   st.stop()
 
# --- 1. TELA: VISÃO GERAL ---
if menu_opcao == "🏠 Visão Geral":
   st.title("GESTÃO DE ALERTAS DE QUALIDADE")
   st.markdown("##### Monitoramento integrado de não-conformidades em tempo real")
   st.markdown("---")
 
    # KPIs dinâmicos
   total_alertas = len(df_alertas)
   abertos = len(df_alertas[df_alertas['status'] != 'ENCERRADO'])
   vencidos = len(df_alertas[df_alertas['status'] == 'VENCIDO'])
   encerrados = len(df_alertas[df_alertas['status'] == 'ENCERRADO'])
    
   total_no_prazo_abertos = len(df_alertas[(df_alertas['status'] != 'ENCERRADO') & (df_alertas['status'] != 'VENCIDO')])
   percentual_prazo = (total_no_prazo_abertos / abertos * 100) if abertos > 0 else 100.0
   no_prazo_str = f"{percentual_prazo:.1f}%"
 
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
       st.markdown(f'<div class="kpi-card" style="background-color: #F3F4F6; color: #1F2937; border: 1px solid #D1D5DB;"><div class="kpi-title" style="color: #4B5563;">% NO PRAZO</div><div class="kpi-value" style="color: #111827;">{no_prazo_str}</div><div class="kpi-subtitle" style="color: #6B7280;">Meta: 80%</div></div>', unsafe_allow_html=True)
 
   st.markdown("<br>", unsafe_allow_html=True)
 
   st.markdown("### ALERTAS EM ABERTO")
   col_tabela, col_detalhes = st.columns([3, 1.4])
 
   with col_tabela:
        df_abertos = df_alertas[df_alertas['status'] != 'ENCERRADO'].copy()
        if not df_abertos.empty:
            df_display = df_abertos[["id", "produto", "lote", "defeito", "area", "responsavel", "prazo", "dias_restantes", "status"]].copy()
           df_display.columns = ["Nº AQ", "Produto", "Lote", "Defeito", "Área Responsável", "Responsável", "Prazo", "Dias Restantes", "Status"]
            styler = df_display.style.map(colorir_status, subset=["Status"]).map(colorir_dias, subset=["Dias Restantes"])
           st.dataframe(styler, use_container_width=True, hide_index=True)
        else:
           st.success("Nenhum alerta em aberto no momento!")
 
   with col_detalhes:
       df_vencidos_detalhe = df_alertas[df_alertas['status'] == 'VENCIDO'].copy()
        if not df_vencidos_detalhe.empty:
           alerta_vencido_selecionado = st.selectbox("⚠️ Selecione a AQ Vencida para auditar:", df_vencidos_detalhe["id"].tolist())
            item = df_vencidos_detalhe[df_vencidos_detalhe['id'] == alerta_vencido_selecionado].iloc[0]
           data_emissao = item.get('data_emissao', '08/07/2026')
            contencao = item.get('acao_contencao', 'Ajuste no processo produtivo (Bloqueio preventivo de lote)')
           observacoes = item.get('observacoes', 'Alerta ultrapassou o prazo limite de tratativa. Necessário plano de ação imediato junto à engenharia.')
            status_cor = "#EF4444"
            
           st.markdown(f"""
            <div style="background-color: #FEE2E2; padding: 15px; border-radius: 12px 12px 0px 0px; border: 1px solid #FCA5A5; border-bottom: none; font-family: 'Segoe UI', sans-serif;">
               <div style="color: #991B1B; text-align: center; font-size: 13px; font-weight: 700; letter-spacing: 0.5px; margin-bottom: 2px;">DETALHES DO ALERTA VENCIDO</div>
               <div style="color: #EF4444; text-align: center; font-size: 26px; font-weight: 800; margin-bottom: 1px;">{item['id']}</div>
               <div style="text-align: center; font-weight: bold; color: #991B1B; font-size: 13.5px; margin-bottom: 0px;">{item['defeito']}</div>
            </div>
           """, unsafe_allow_html=True)
            
            with st.container(border=True):
               st.markdown(f"📁 **Produto:** &nbsp;&nbsp; `{item['produto']}`")
               st.markdown(f"📦 **Lote:** &nbsp;&nbsp; `{item['lote']}`")
               st.markdown(f"🏢 **Área Responsável:** &nbsp;&nbsp; `{item['area']}`")
               st.markdown(f"👤 **Responsável:** &nbsp;&nbsp; `{item['responsavel']}`")
               st.markdown(f"📅 **Data de Emissão:** &nbsp;&nbsp; `{data_emissao}`")
               st.markdown(f"🕒 **Prazo para Ação:** &nbsp;&nbsp; <span style='color: #EF4444; font-weight: bold;'>{item['prazo'].strftime('%d/%m/%Y')}</span>", unsafe_allow_html=True)
               st.markdown(f"🕒 **Dias Restantes:** &nbsp;&nbsp; <span style='color: {status_cor}; font-weight: bold;'>{item['dias_restantes']} (Atrasado)</span>", unsafe_allow_html=True)
               st.markdown(f"🛡️ **Status Atual:** <span style='background-color: {status_cor}; color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 11px;'>VENCIDO</span>", unsafe_allow_html=True)
               st.divider()
               st.markdown("⚠️ **Ação de Contenção Exigida:**")
               st.caption(contencao)
               st.markdown("🚨 **Histórico / Observações de Atraso:**")
               st.error(observacoes)
                if st.button("VER HISTÓRICO COMPLETO", use_container_width=True, type="primary"):
                   st.info("💡 Redirecionando para aba 'Relatórios' para visualização do histórico de atrasos.")
        else:
           st.markdown("""
            <div style="background-color: #D1FAE5; padding: 25px; border-radius: 12px; border: 1px solid #34D399; text-align: center; font-family: 'Segoe UI', sans-serif;">
               <span style="font-size: 40px;">🎉</span>
                <h4 style="color: #065F46; margin-top: 10px;">OPERACIONAL 100%</h4>
                <p style="color: #047857; font-size: 13px;">Nenhum alerta de qualidade está vencido ou em atraso hoje!</p>
            </div>
           """, unsafe_allow_html=True)
 
   st.markdown("<br>", unsafe_allow_html=True)
   st.markdown("### INDICADORES E ANÁLISES GRÁFICAS")
    g_col1, g_col2, g_col3, g_col4 = st.columns(4)
 
   with g_col1:
       with st.container(border=True):
            if area_dist:
               labels_area = list(area_dist.keys())
               values_area = list(area_dist.values())
                
                fig1 = go.Figure(data=[go.Pie(
                   labels=labels_area, 
                   values=values_area, 
                   hole=0.5,
                   textinfo='label+value+percent',
                   textposition='outside',
                   insidetextorientation='radial',
                   showlegend=False
                )])
               fig1.update_layout(
                   title=dict(text="<b>ALERTAS POR ÁREA</b>", x=0.5, y=0.95, font=dict(size=13, color="#1E3A8A")),
                   margin=dict(l=30, r=30, t=50, b=30), 
                   height=250,
                   paper_bgcolor='rgba(0,0,0,0)',
                   plot_bgcolor='rgba(0,0,0,0)'
                )
               st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
 
   with g_col2:
       with st.container(border=True):
            if status_dist:
               labels_status = list(status_dist.keys())
               values_status = list(status_dist.values())
                
               total_status = sum(values_status)
               legenda_formatada = [f"{lbl}<br>{val} ({val/total_status*100:.1f}%)" for lbl, val in zip(labels_status, values_status)]
                
                fig2 = go.Figure(data=[go.Pie(
                   labels=legenda_formatada, 
                   values=values_status, 
                   hole=0.5,
                   textinfo='none', 
                   showlegend=True
                )])
               fig2.update_layout(
                   title=dict(text="<b>ALERTAS POR STATUS</b>", x=0.5, y=0.95, font=dict(size=13, color="#1E3A8A")),
                   margin=dict(l=10, r=10, t=50, b=10), 
                   height=250,
                   legend=dict(orientation="v", valign="middle", x=0.85, y=0.5, font=dict(size=9)),
                   paper_bgcolor='rgba(0,0,0,0)',
                   plot_bgcolor='rgba(0,0,0,0)'
                )
               st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
 
   with g_col3:
       with st.container(border=True):
            if defect_dist := defeito_dist:
                df_def = pd.DataFrame(list(defect_dist.items()), columns=['Defeito', 'Qtd']).sort_values(by='Qtd', ascending=True)
                
                fig3 = go.Figure(go.Bar(
                   x=df_def['Qtd'],
                   y=df_def['Defeito'],
                   orientation='h',
                   marker_color='#0E4687',
                   text=df_def['Qtd'], 
                   textposition='outside', 
                   textfont=dict(size=11, color='#374151', weight='bold')
                ))
               fig3.update_layout(
                   title=dict(text="<b>ALERTAS POR TIPO DE DEFEITO</b>", x=0.5, y=0.95, font=dict(size=13, color="#1E3A8A")),
                   margin=dict(l=10, r=30, t=50, b=10), 
                   height=250,
                   xaxis=dict(showgrid=False, visible=False), 
                   yaxis=dict(showgrid=False, tickfont=dict(size=11)),
                   paper_bgcolor='rgba(0,0,0,0)',
                   plot_bgcolor='rgba(0,0,0,0)'
                )
               st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})
 
   with g_col4:
       with st.container(border=True):
            if not df_tempo.empty:
                fig4 = go.Figure()
               fig4.add_trace(go.Scatter(
                   x=df_tempo["Mês"], 
                   y=df_tempo["Dias"], 
                   mode='lines+markers+text',
                   text=df_tempo["Dias"], 
                   textposition='top center', 
                   textfont=dict(size=11, color='#374151', weight='bold'),
                   line=dict(color='#0284C7', width=2.5),
                   marker=dict(size=7, color='#0284C7')
                ))
               fig4.update_layout(
                   title=dict(text="<b>TEMPO MÉDIO DE FECHAMENTO (DIAS)</b>", x=0.5, y=0.95, font=dict(size=13, color="#1E3A8A")),
                   margin=dict(l=20, r=20, t=50, b=10), 
                   height=250,
                   xaxis=dict(showgrid=False),
                   yaxis=dict(showgrid=False, range=[0, 35], tickfont=dict(size=10)),
                   paper_bgcolor='rgba(0,0,0,0)',
                   plot_bgcolor='rgba(0,0,0,0)'
                )
               st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar': False})

# =======================================================
# ====== 2. TELA: PASSO INICIAL DA NOVA ABA ======
# =======================================================
elif menu_opcao == "➕ Inserir Tratativa":
    st.title("➕ INSERIR TRATATIVA DO ALERTA")
    st.markdown("---")
    
    # Gera a lista com os IDs de todos os alertas cadastrados
    lista_aqs = df_alertas["id"].tolist()
    
    # Caixa de seleção para o usuário escolher qual Alerta vai tratar
    aq_selecionada = st.selectbox("Escolha o Nº da AQ para preencher a tratativa:", lista_aqs)
    
    # Puxa os dados da AQ escolhida
    item_aq = df_alertas[df_alertas['id'] == aq_selecionada].iloc[0]
    st.info(f"📋 **AQ Selecionada:** {item_aq['id']} | **Produto:** {item_aq['produto']} | **Defeito:** {item_aq['defeito']}")

# --- 3. TELA: NOVO ALERTA (CADASTRO) ---
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
            status = st.selectbox("Status Inicial", ["EM DIA", "PRÓX. DO PRAZO", "VENCIDO", "ENCERRADO"])
            
        submetido = st.form_submit_button("Gravar Ocorrência no Banco")
        if submetido:
            if not id_alerta or not produto or not lote or not defeito or not responsavel:
                st.warning("⚠️ Preencha todos os campos obrigatórios!")
            else:
                dias_restantes = 0 if status == "ENCERRADO" else (prazo - date.today()).days
                novo_registro = {
                    "id": id_alerta, "produto": produto, "lote": lote, "defeito": defeito,
                    "area": area, "responsavel": responsavel, "prazo": prazo.strftime("%Y-%m-%d"),
                    "dias_restantes": int(dias_restantes), "status": status
                }
                try:
                    supabase.table("alertas").insert(novo_registro).execute()
                    st.success(f"🎉 Alerta {id_alerta} salvo com sucesso!")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
 
# --- Restante das páginas mantido original ---
elif menu_opcao == "🔔 Alertas Abertos":
    st.title("🔔 ALERTAS EM ANDAMENTO")
    df_filtrado = df_alertas[df_alertas['status'] != 'ENCERRADO'].copy()
    if not df_filtrado.empty:
        df_display = df_filtrado[["id", "produto", "lote", "defeito", "area", "responsavel", "prazo", "dias_restantes", "status"]]
        st.dataframe(df_display.style.map(colorir_status, subset=["status"]).map(colorir_dias, subset=["dias_restantes"]), use_container_width=True, hide_index=True)
 
elif menu_opcao == "⏰ Alertas Vencidos":
    st.title("⏰ ALERTAS VENCIDOS E EM ATRASO")
    df_filtrado = df_alertas[df_alertas['status'] == 'VENCIDO'].copy()
    if not df_filtrado.empty:
        df_display = df_filtrado[["id", "produto", "lote", "defeito", "area", "responsavel", "prazo", "dias_restantes", "status"]]
        st.dataframe(df_display.style.map(colorir_status, subset=["status"]).map(colorir_dias, subset=["dias_restantes"]), use_container_width=True, hide_index=True)
    else:
        st.success("Excelente! Não existem alertas vencidos no momento.")
 
elif menu_opcao == "✔️ Encerrados":
    st.title("✔️ HISTÓRICO DE ALERTAS ENCERRADOS")
    df_filtrado = df_alertas[df_alertas['status'] == 'ENCERRADO'].copy()
    if not df_filtrado.empty:
        df_display = df_filtrado[["id", "produto", "lote", "defeito", "area", "responsavel", "prazo", "dias_restantes", "status"]]
        st.dataframe(df_display.style.map(colorir_status, subset=["status"]), use_container_width=True, hide_index=True)
 
elif menu_opcao == "📊 Indicadores":
    st.title("📊 PAINEL GERAL DE INDICADORES (KPIs)")
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.plotly_chart(px.bar(df_alertas, x="area", color="status", title="Volume por Área", barmode="stack"), use_container_width=True)
    with col_g2:
        st.plotly_chart(px.histogram(df_alertas, x="status", title="Distribuição por Status", color="status"), use_container_width=True)
 
elif menu_opcao == "📈 Análises":
    st.title("📈 ANÁLISES CRÍTICAS E PARETO")
    df_pareto = df_alertas["defeito"].value_counts().reset_index()
    df_pareto.columns = ["Defeito", "Qtd"]
    df_pareto["% Acumulada"] = (df_pareto["Qtd"].cumsum() / df_pareto["Qtd"].sum()) * 100
    fig_pareto = go.Figure()
    fig_pareto.add_trace(go.Bar(x=df_pareto["Defeito"], y=df_pareto["Qtd"], name="Quantidade", marker_color="#0E4687"))
    fig_pareto.add_trace(go.Scatter(x=df_pareto["Defeito"], y=df_pareto["% Acumulada"], name="% Acumulada", yaxis="y2", line=dict(color="#EF4444"), mode="lines+markers"))
    fig_pareto.update_layout(title="Diagrama de Pareto", yaxis=dict(title="Qtd"), yaxis2=dict(title="% Acumulada", overlaying="y", side="right", range=[0, 105]))
    st.plotly_chart(fig_pareto, use_container_width=True)
 
elif menu_opcao == "📄 Relatórios":
    st.title("📄 EXTRAÇÃO E EMISSÃO DE RELATÓRIOS")
    st.dataframe(df_alertas, use_container_width=True, hide_index=True)
    csv_data = df_alertas.to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 Exportar Base Completa (CSV)", data=csv_data, file_name="relatorio_alertas.csv", mime="text/csv", use_container_width=True)
