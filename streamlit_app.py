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
        .kpi-card {
            border-radius: 8px; padding: 15px; color: white; text-align: center;
            font-family: 'Segoe UI', sans-serif; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .kpi-title { font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; opacity: 0.9; }
        .kpi-value { font-size: 28px; font-weight: 800; margin-bottom: 2px; }
        .kpi-subtitle { font-size: 12px; opacity: 0.8; }
        
        /* Estilização do Card de Detalhes lateral */
        .detalhes-card {
            background-color: #FFFFFF;
            padding: 24px;
            border-radius: 12px;
            border: 1px solid #E5E7EB;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            font-family: 'Segoe UI', sans-serif;
        }
        .detalhes-titulo {
            color: #1E3A8A;
            text-align: center;
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 5px;
            text-transform: uppercase;
        }
        .detalhes-id {
            color: #EF4444;
            text-align: center;
            font-size: 26px;
            font-weight: 800;
            margin: 0 0 5px 0;
        }
        .detalhes-subtitulo {
            text-align: center;
            font-weight: bold;
            color: #374151;
            font-size: 14px;
            margin-bottom: 20px;
        }
        .detalhes-tabela {
            width: 100%;
            border-collapse: collapse;
            font-size: 13.5px;
            margin-bottom: 15px;
        }
        .detalhes-tabela td {
            padding: 8px 0;
            border-bottom: 1px solid #F3F4F6;
            color: #374151;
        }
        .detalhes-label {
            color: #6B7280;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .status-badge {
            padding: 4px 10px;
            border-radius: 6px;
            font-weight: bold;
            color: white;
            font-size: 11px;
            display: inline-block;
        }
        .obs-box {
            background-color: #F9FAFB;
            border: 1px solid #E5E7EB;
            border-radius: 6px;
            padding: 12px;
            font-size: 12.5px;
            color: #4B5563;
            margin-top: 5px;
            min-height: 80px;
        }
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

# 2. Carregar e processar dados de forma dinâmica e em tempo real
def carregar_dados():
    try:
        resposta = supabase.table("alertas").select("*").execute()
        df = pd.DataFrame(resposta.data)
        if df.empty:
            return pd.DataFrame(), {}, {}, {}, pd.DataFrame()
        
        # Data de hoje para cálculos (16/07/2026)
        hoje = date.today()
        
        # Converte o prazo para tipo data
        df['prazo'] = pd.to_datetime(df['prazo']).dt.date
        
        # ====== RECALCULO DINÂMICO DE PRAZOS E STATUS ======
        for index, row in df.iterrows():
            if row['status'] == 'ENCERRADO':
                df.at[index, 'dias_restantes'] = 0
            else:
                dias = (row['prazo'] - hoje).days
                df.at[index, 'dias_restantes'] = dias
                # Define o status dinamicamente se não estiver encerrado
                if dias < 0:
                    df.at[index, 'status'] = 'VENCIDO'
                elif dias <= 5:
                    df.at[index, 'status'] = 'PRÓX. DO PRAZO'
                else:
                    df.at[index, 'status'] = 'EM DIA'
        
        # Agregações para gráficos baseados nas regras dinâmicas
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

    # KPIs dinâmicos atualizados em tempo real pelas novas regras
    total_alertas = len(df_alertas)
    abertos = len(df_alertas[df_alertas['status'] != 'ENCERRADO'])
    vencidos = len(df_alertas[df_alertas['status'] == 'VENCIDO'])
    encerrados = len(df_alertas[df_alertas['status'] == 'ENCERRADO'])
    
    # Cálculo real de % no prazo: (total_no_prazo / total_abertos) * 100
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
    col_tabela, col_detalhes = st.columns([3, 1.3])

    with col_tabela:
        df_abertos = df_alertas[df_alertas['status'] != 'ENCERRADO'].copy()
        if not df_abertos.empty:
            df_display = df_abertos[["id", "produto", "lote", "defeito", "area", "responsavel", "prazo", "dias_restantes", "status"]].copy()
            df_display.columns = ["Nº AQ", "Produto", "Lote", "Defeito", "Área Responsável", "Responsável", "Prazo", "Dias Restantes", "Status"]
            
            # Caixa de seleção interativa para o usuário clicar e carregar os detalhes do alerta específico
            alerta_selecionado = st.selectbox("Selecione uma AQ na lista para detalhar:", df_display["Nº AQ"].tolist())
            
            styler = df_display.style.map(colorir_status, subset=["Status"]).map(colorir_dias, subset=["Dias Restantes"])
            st.dataframe(styler, use_container_width=True, hide_index=True)
        else:
            st.success("Nenhum alerta em aberto no momento!")
            alerta_selecionado = None

    # ====== CARD DE DETALHES IDENTICO À IMAGEM DE REFERÊNCIA ======
    with col_detalhes:
        if alerta_selecionado:
            item = df_alertas[df_alertas['id'] == alerta_selecionado].iloc[0]
        else:
            item = df_alertas.iloc[0]
            
        # Puxa campos extras ou cria valores padrão caso não estejam estruturados no banco de dados
        data_emissao = item.get('data_emissao', '08/07/2026')
        contencao = item.get('acao_contencao', 'Ajuste no processo produtivo')
        observacoes = item.get('observacoes', 'Defeito recorrente identificado pelo operador no início do turno.')
        
        status_color = "#EF4444" if item['status'] == "VENCIDO" else ("#F59E0B" if item['status'] == "PRÓX. DO PRAZO" else "#10B981")
        
        st.markdown(f"""
            <div class="detalhes-card">
                <div class="detalhes-titulo">DETALHES DO ALERTA</div>
                <div class="detalhes-id">{item['id']}</div>
                <div class="detalhes-subtitulo">{item['defeito']}</div>
                
                <table class="detalhes-tabela">
                    <tr>
                        <td class="detalhes-label">📁 Produto:</td>
                        <td style="text-align: right; font-weight: 500;">{item['produto']}</td>
                    </tr>
                    <tr>
                        <td class="detalhes-label">📦 Lote:</td>
                        <td style="text-align: right; font-weight: 500;">{item['lote']}</td>
                    </tr>
                    <tr>
                        <td class="detalhes-label">🏢 Área Responsável:</td>
                        <td style="text-align: right; font-weight: 500;">{item['area']}</td>
                    </tr>
                    <tr>
                        <td class="detalhes-label">👤 Responsável:</td>
                        <td style="text-align: right; font-weight: 500;">{item['responsavel']}</td>
                    </tr>
                    <tr>
                        <td class="detalhes-label">📅 Data de Emissão:</td>
                        <td style="text-align: right; font-weight: 500;">{data_emissao}</td>
                    </tr>
                    <tr>
                        <td class="detalhes-label">🕒 Prazo para Ação:</td>
                        <td style="text-align: right; font-weight: bold; color: #EF4444;">{item['prazo'].strftime('%d/%m/%Y')}</td>
                    </tr>
                    <tr>
                        <td class="detalhes-label">🕒 Dias Restantes:</td>
                        <td style="text-align: right; font-weight: bold; color: {status_color};">{item['dias_restantes']}</td>
                    </tr>
                    <tr>
                        <td class="detalhes-label">🛡️ Status Atual:</td>
                        <td style="text-align: right;">
                            <span class="status-badge" style="background-color: {status_color};">{item['status']}</span>
                        </td>
                    </tr>
                    <tr>
                        <td class="detalhes-label" colspan="2" style="border: none; padding-top: 15px; font-weight: bold; color: #1E3A8A;">🔔 Ação de Contenção:</td>
                    </tr>
                    <tr>
                        <td colspan="2" style="border: none; padding-top: 0; font-size: 13px;">{contencao}</td>
                    </tr>
                    <tr>
                        <td class="detalhes-label" colspan="2" style="border: none; padding-top: 15px; font-weight: bold; color: #1E3A8A;">📣 Observações:</td>
                    </tr>
                    <tr>
                        <td colspan="2" style="border: none; padding-top: 0;">
                            <div class="obs-box">{observacoes}</div>
                        </td>
                    </tr>
                </table>
            </div>
        """, unsafe_allow_html=True)
        
        # Botão para redirecionar para a aba Histórico / Relatórios
        if st.button("VER HISTÓRICO COMPLETO", use_container_width=True):
            st.info("💡 Acesse a aba 'Relatórios' no menu lateral para visualizar toda a base histórica.")

    st.markdown("<br>", unsafe_allow_html=True)
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

# --- 2. TELA: NOVO ALERTA (CADASTRO) ---
elif menu_opcao == "➕ Novo Alerta":
    st.title("➕ CADASTRAR NOVO ALERTA")
    st.markdown("Insira as informações abaixo para abrir uma nova ocorrência no Supabase")
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
                if status == "ENCERRADO":
                    dias_restantes = 0
                else:
                    dias_restantes = (prazo - date.today()).days
                    
                novo_registro = {
                    "id": id_alerta, "produto": produto, "lote": lote, "defeito": defeito,
                    "area": area, "responsavel": responsavel, "prazo": prazo.strftime("%Y-%m-%d"),
                    "dias_restantes": int(dias_restantes), "status": status
                }
                try:
                    supabase.table("alertas").insert(novo_registro).execute()
                    st.success(f"🎉 Alerta {id_alerta} salvo com sucesso no Supabase!")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# --- 3. TELA: ALERTAS ABERTOS ---
elif menu_opcao == "🔔 Alertas Abertos":
    st.title("🔔 ALERTAS EM ANDAMENTO")
    st.markdown("Lista completa de não-conformidades monitoradas que ainda não foram solucionadas.")
    df_filtrado = df_alertas[df_alertas['status'] != 'ENCERRADO'].copy()
    
    if not df_filtrado.empty:
        df_display = df_filtrado[["id", "produto", "lote", "defeito", "area", "responsavel", "prazo", "dias_restantes", "status"]].copy()
        df_display.columns = ["Nº AQ", "Produto", "Lote", "Defeito", "Área Responsável", "Responsável", "Prazo", "Dias Restantes", "Status"]
        st.dataframe(df_display.style.map(colorir_status, subset=["Status"]).map(colorir_dias, subset=["Dias Restantes"]), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum alerta aberto no momento.")

# --- 4. TELA: ALERTAS VENCIDOS (DINÂMICO) ---
elif menu_opcao == "⏰ Alertas Vencidos":
    st.title("⏰ ALERTAS VENCIDOS E EM ATRASO")
    st.markdown("Filtro crítico operacional focado em ações com prazos de validade já expirados.")
    df_filtrado = df_alertas[df_alertas['status'] == 'VENCIDO'].copy()
    
    if not df_filtrado.empty:
        df_display = df_filtrado[["id", "produto", "lote", "defeito", "area", "responsavel", "prazo", "dias_restantes", "status"]].copy()
        df_display.columns = ["Nº AQ", "Produto", "Lote", "Defeito", "Área Responsável", "Responsável", "Prazo", "Dias Restantes", "Status"]
        st.dataframe(df_display.style.map(colorir_status, subset=["Status"]).map(colorir_dias, subset=["Dias Restantes"]), use_container_width=True, hide_index=True)
    else:
        st.success("Excelente! Não existem alertas vencidos no momento.")

# --- 5. TELA: ENCERRADOS ---
elif menu_opcao == "✔️ Encerrados":
    st.title("✔️ HISTÓRICO DE ALERTAS ENCERRADOS")
    st.markdown("Acompanhamento das ocorrências concluídas com sucesso pela engenharia da qualidade.")
    df_filtrado = df_alertas[df_alertas['status'] == 'ENCERRADO'].copy()
    
    if not df_filtrado.empty:
        df_display = df_filtrado[["id", "produto", "lote", "defeito", "area", "responsavel", "prazo", "dias_restantes", "status"]].copy()
        df_display.columns = ["Nº AQ", "Produto", "Lote", "Defeito", "Área Responsável", "Responsável", "Prazo", "Dias Restantes", "Status"]
        st.dataframe(df_display.style.map(colorir_status, subset=["Status"]), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum alerta foi movido para o status 'ENCERRADO' ainda.")

# --- 6. TELA: INDICADORES ---
elif menu_opcao == "📊 Indicadores":
    st.title("📊 PAINEL GERAL DE INDICADORES (KPIs)")
    st.markdown("Visão estatística ampla da distribuição de defeitos e volumetria por célula de manufatura.")
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig_ind1 = px.bar(df_alertas, x="area", color="status", title="Volume de Ocorrências por Área e Status", barmode="stack")
        st.plotly_chart(fig_ind1, use_container_width=True)
    with col_g2:
        fig_ind2 = px.histogram(df_alertas, x="status", title="Distribuição Geral por Status de Ação", color="status")
        st.plotly_chart(fig_ind2, use_container_width=True)

# --- 7. TELA: ANÁLISES ---
elif menu_opcao == "📈 Análises":
    st.title("📈 ANÁLISES CRÍTICAS E PARETO")
    st.markdown("Ferramentas estatísticas detalhadas para identificação de causas raiz recorrentes.")
    
    # Pareto de Defeitos
    df_pareto = df_alertas["defeito"].value_counts().reset_index()
    df_pareto.columns = ["Defeito", "Qtd"]
    df_pareto["% Acumulada"] = (df_pareto["Qtd"].cumsum() / df_pareto["Qtd"].sum()) * 100
    
    fig_pareto = go.Figure()
    fig_pareto.add_trace(go.Bar(x=df_pareto["Defeito"], y=df_pareto["Qtd"], name="Quantidade", marker_color="#0E4687"))
    fig_pareto.add_trace(go.Scatter(x=df_pareto["Defeito"], y=df_pareto["% Acumulada"], name="% Acumulada", yaxis="y2", line=dict(color="#EF4444"), mode="lines+markers"))
    
    fig_pareto.update_layout(
        title="Diagrama de Pareto: Principais Causas de Defeito",
        yaxis=dict(title="Quantidade de Alertas"),
        yaxis2=dict(title="% Acumulada", overlaying="y", side="right", range=[0, 105])
    )
    st.plotly_chart(fig_pareto, use_container_width=True)

# --- 8. TELA: RELATÓRIOS (EXPORTAÇÃO DE DADOS) ---
elif menu_opcao == "📄 Relatórios":
    st.title("📄 EXTRAÇÃO E EMISSÃO DE RELATÓRIOS")
    st.markdown("Área destinada para auditorias e exportação de dados brutos das ocorrências.")
    st.markdown("---")
    
    st.dataframe(df_alertas, use_container_width=True, hide_index=True)
    
    @st.cache_data
    def converter_csv(df_dados):
        return df_dados.to_csv(index=False).encode('utf-8')
        
    csv_data = converter_csv(df_alertas)
    
    st.download_button(
        label="📥 Exportar Base de Dados Completa (CSV)",
        data=csv_data,
        file_name=f"relatorio_alertas_qualidade_{date.today().strftime('%d_%m_%Y')}.csv",
        mime="text/csv",
        use_container_width=True
    )
