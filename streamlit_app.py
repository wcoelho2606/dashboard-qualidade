import streamlit st
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
        
        for index, row in df.iterrows():
            if row['status'] == 'ENCERRADO':
                df.at[index, 'dias_restantes'] = 0
            else:
                dias = (row['prazo'] - hoje).days
                df.at[index, 'dias_restantes'] = dias
                if dias < 0:
                    df.at[index, 'status_visual'] = 'VENCIDO'
                elif dias <= 5:
                    df.at[index, 'status_visual'] = 'PRÓX. DO PRAZO'
                else:
                    df.at[index, 'status_visual'] = 'EM DIA'
        
        # Garante que se a coluna status_visual não foi criada por falta de linhas, ela exista
        if 'status_visual' not in df.columns:
            df['status_visual'] = df['status']

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
    if val == "VENCIDO": return 'background-color: #FEE2E2; color: #991B1B; font-weight: bold; text-align: center;'
    elif val == "PRÓX. DO PRAZO": return 'background-color: #FEF3C7; color: #92400E; font-weight: bold; text-align: center;'
    elif val == "EM DIA": return 'background-color: #D1FAE5; color: #065F46; font-weight: bold; text-align: center;'
    return 'background-color: #F3F4F6; color: #374151; text-align: center;'

def colorir_dias(val):
    if val < 0: return 'color: #EF4444; font-weight: bold;'
    elif val <= 5: return 'color: #F59E0B; font-weight: bold;'
    return 'color: #10B981; font-weight: bold;'

# --- MENU LATERAL DE NAVEGAÇÃO ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield-with-growth-chart.png", width=80)
    st.markdown("### GESTÃO DE ALERTAS")
    st.markdown("Supabase + Streamlit Cloud")
    st.markdown("---")
    
    menu_opcao = st.radio(
        "Navegação",
        [
            "🏠 Visão Geral", 
            "➕ Inserir Tratativa", 
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
    st.warning("Aguardando carregamento de dados...")
    st.stop()

# ==========================================
# ====== 1. TELA: VISÃO GERAL (IGUAL À FOTO) ======
# ==========================================
if menu_opcao == "🏠 Visão Geral":
    st.title("GESTÃO DE ALERTAS DE QUALIDADE")
    st.markdown("---")

    total_alertas = len(df_alertas)
    abertos = len(df_alertas[df_alertas['status'] != 'ENCERRADO'])
    vencidos = len(df_alertas[df_alertas['status_visual'] == 'VENCIDO'])
    encerrados = len(df_alertas[df_alertas['status'] == 'ENCERRADO'])
    percentual_prazo = (encerrados / total_alertas * 100) if total_alertas > 0 else 100.0

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1: st.markdown(f'<div class="kpi-card" style="background-color: #0E4687;"><div class="kpi-title">TOTAL DE ALERTAS</div><div class="kpi-value">{total_alertas}</div></div>', unsafe_allow_html=True)
    with kpi2: st.markdown(f'<div class="kpi-card" style="background-color: #F59E0B;"><div class="kpi-title">ALERTAS ABERTOS</div><div class="kpi-value">{abertos}</div></div>', unsafe_allow_html=True)
    with kpi3: st.markdown(f'<div class="kpi-card" style="background-color: #EF4444;"><div class="kpi-title">ALERTAS VENCIDOS</div><div class="kpi-value">{vencidos}</div></div>', unsafe_allow_html=True)
    with kpi4: st.markdown(f'<div class="kpi-card" style="background-color: #10B981;"><div class="kpi-title">ALERTAS ENCERRADOS</div><div class="kpi-value">{encerrados}</div></div>', unsafe_allow_html=True)
    with kpi5: st.markdown(f'<div class="kpi-card" style="background-color: #F3F4F6; color: #1F2937; border: 1px solid #D1D5DB;"><div class="kpi-title" style="color: #4B5563;">% NO PRAZO</div><div class="kpi-value" style="color: #111827;">{percentual_prazo:.1f}%</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### ALERTAS EM ABERTO")
    col_tabela, col_detalhes = st.columns([3, 1.4])

    with col_tabela:
        df_abertos = df_alertas[df_alertas['status'] != 'ENCERRADO'].copy()
        if not df_abertos.empty:
            df_display = df_abertos[["id", "produto", "lote", "defeito", "area", "responsavel", "prazo", "dias_restantes", "status_visual"]].copy()
            df_display.columns = ["Nº AQ", "Produto", "Lote", "Defeito", "Área Responsável", "Responsável", "Prazo", "Dias Restantes", "Status"]
            alerta_selecionado = st.selectbox("Selecione uma AQ na lista para detalhar:", df_display["Nº AQ"].tolist())
            st.dataframe(df_display.style.map(colorir_status, subset=["Status"]).map(colorir_dias, subset=["Dias Restantes"]), use_container_width=True, hide_index=True)
        else:
            st.success("Nenhum alerta em aberto!")
            alerta_selecionado = None

    with col_detalhes:
        if alerta_selecionado:
            item = df_alertas[df_alertas['id'] == alerta_selecionado].iloc[0]
            data_emissao = item.get('data_emissao', '08/07/2026')
            status_cor = "#EF4444" if item['status_visual'] == "VENCIDO" else ("#F59E0B" if item['status_visual'] == "PRÓX. DO PRAZO" else "#10B981")
            
            st.markdown(f"""
            <div style="background-color: #FFFFFF; padding: 15px; border-radius: 12px 12px 0px 0px; border: 1px solid #E5E7EB; border-bottom: none; font-family: 'Segoe UI', sans-serif;">
                <div style="color: #1E3A8A; text-align: center; font-size: 13px; font-weight: 700; letter-spacing: 0.5px; margin-bottom: 2px;">DETALHES DO ALERTA</div>
                <div style="color: #EF4444; text-align: center; font-size: 26px; font-weight: 800; margin-bottom: 1px;">{item['id']}</div>
                <div style="text-align: center; font-weight: bold; color: #374151; font-size: 13.5px; margin-bottom: 0px;">{item['defeito']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.container(border=True):
                st.markdown(f"📁 **Produto:** &nbsp;&nbsp; `{item['produto']}`")
                st.markdown(f"📦 **Lote:** &nbsp;&nbsp; `{item['lote']}`")
                st.markdown(f"🏢 **Área Responsável:** &nbsp;&nbsp; `{item['area']}`")
                st.markdown(f"👤 **Responsável:** &nbsp;&nbsp; `{item['responsavel']}`")
                st.markdown(f"📅 **Data de Emissão:** &nbsp;&nbsp; `{data_emissao}`")
                st.markdown(f"🕒 **Prazo para Ação:** &nbsp;&nbsp; <span style='color: #EF4444; font-weight: bold;'>{item['prazo'].strftime('%d/%m/%Y')}</span>", unsafe_allow_html=True)
                st.markdown(f"🕒 **Dias Restantes:** &nbsp;&nbsp; <span style='color: {status_cor}; font-weight: bold;'>{item['dias_restantes']}</span>", unsafe_allow_html=True)
                st.markdown(f"🛡️ **Status Atual:** <span style='background-color: {status_cor}; color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 11px;'>{item['status']}</span>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### INDICADORES E ANÁLISES GRÁFICAS")
    g_col1, g_col2, g_col3, g_col4 = st.columns(4)

    with g_col1:
        with st.container(border=True):
            if area_dist:
                fig1 = go.Figure(data=[go.Pie(labels=list(area_dist.keys()), values=list(area_dist.values()), hole=0.5, textinfo='label+value+percent', textposition='outside', showlegend=False)])
                fig1.update_layout(title=dict(text="<b>ALERTAS POR ÁREA</b>", x=0.5, font=dict(size=13, color="#1E3A8A")), margin=dict(l=30, r=30, t=40, b=30), height=240, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})

    with g_col2:
        with st.container(border=True):
            if status_dist:
                total_status = sum(status_dist.values())
                legenda_formatada = [f"{lbl}<br>{val} ({val/total_status*100:.1f}%)" for lbl, val in zip(status_dist.keys(), status_dist.values())]
                fig2 = go.Figure(data=[go.Pie(labels=legenda_formatada, values=list(status_dist.values()), hole=0.5, textinfo='none', showlegend=True)])
                fig2.update_layout(title=dict(text="<b>ALERTAS POR STATUS</b>", x=0.5, font=dict(size=13, color="#1E3A8A")), margin=dict(l=10, r=10, t=40, b=10), height=240, legend=dict(orientation="v", valign="middle", x=0.85, y=0.5, font=dict(size=9)), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

    with g_col3:
        with st.container(border=True):
            if defeito_dist:
                df_def = pd.DataFrame(list(defeito_dist.items()), columns=['Defeito', 'Qtd']).sort_values(by='Qtd', ascending=True)
                fig3 = go.Figure(go.Bar(x=df_def['Qtd'], y=df_def['Defeito'], orientation='h', marker_color='#0E4687', text=df_def['Qtd'], textposition='outside', textfont=dict(size=11, weight='bold')))
                fig3.update_layout(title=dict(text="<b>ALERTAS POR TIPO DE DEFEITO</b>", x=0.5, font=dict(size=13, color="#1E3A8A")), margin=dict(l=10, r=30, t=40, b=10), height=240, xaxis=dict(showgrid=False, visible=False), yaxis=dict(showgrid=False), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})

    with g_col4:
        with st.container(border=True):
            if not df_tempo.empty:
                fig4 = go.Figure()
                fig4.add_trace(go.Scatter(x=df_tempo["Mês"], y=df_tempo["Dias"], mode='lines+markers+text', text=df_tempo["Dias"], textposition='top center', textfont=dict(size=11, weight='bold'), line=dict(color='#0284C7', width=2.5)))
                fig4.update_layout(title=dict(text="<b>TEMPO MÉDIO DE FECHAMENTO (DIAS)</b>", x=0.5, font=dict(size=13, color="#1E3A8A")), margin=dict(l=20, r=20, t=40, b=10), height=240, xaxis=dict(showgrid=False), yaxis=dict(showgrid=False, range=[0, 35]), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar': False})

# =======================================================
# ====== 2. TELA: PÁGINA "➕ INSERIR TRATATIVA" COMPATÍVEL ======
# =======================================================
elif menu_opcao == "➕ Inserir Tratativa":
    st.title("➕ REGISTRAR PLANO DE TRATATIVAS E RESOLUÇÃO")
    st.markdown("Insira e atualize os passos de análise e validação da ocorrência.")
    st.markdown("---")
    
    lista_aqs = df_alertas["id"].tolist()
    aq_selecionada = st.selectbox("Selecione qual AQ você deseja aplicar a tratativa:", lista_aqs)
    item_aq = df_alertas[df_alertas['id'] == aq_selecionada].iloc[0]
    
    st.info(f"🔎 **AQ Selecionada:** {item_aq['id']} | **Produto:** {item_aq['produto']} | **Defeito:** {item_aq['defeito']}")
    st.markdown("---")
    
    # PASSO 1: Análise do Responsável
    st.markdown("### 👤 PASSO 1: Análise do Responsável Técnico")
    confirmar_analise = st.checkbox("Desejo confirmar o OK mostrando que fiz a análise do alerta emitido.")
    
    st.caption("Adicionar Ações Definidas (Correção do problema encontrado conforme Alerta):")
    # Usamos o campo defeito apenas como guia visual já que o banco não aceita textos novos longos
    st.code(f"Alerta Emitido: {item_aq['defeito']}") 
    
    responsavel_implementar = st.text_input("Quem vai ser o Responsável para implementar esta ação?", value=item_aq.get('responsavel', ''))
    
    st.markdown("---")
    
    # PASSO 2: Validação da Qualidade
    st.markdown("### 🛡️ PASSO 2: Validação da Engenharia da Qualidade")
    confirmar_qualidade = st.checkbox("Desejo confirmar o OK mostrando que foi validado e corrigido com eficácia.")
    encerrar_processo = st.checkbox("Marcar como ENCERRADO pela Qualidade (Finalizar Tratativa)")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("💾 GRAVAR E ATUALIZAR TRATATIVA NO SUPABASE", type="primary", use_container_width=True):
        
        # Define o novo status compatível com seu banco existente
        status_final = item_aq['status']
        if encerrar_processo or confirmar_qualidade:
            status_final = "ENCERRADO"
        elif confirmar_analise:
            status_final = "EM TRATATIVA"
            
        # Atualizamos estritamente colunas nativas do seu banco
        dados_atualizados = {
            "responsavel": responsavel_implementar,
            "status": status_final
        }
        
        try:
            supabase.table("alertas").update(dados_atualizados).eq("id", aq_selecionada).execute()
            st.success(f"🎉 Tratativa da AQ {aq_selecionada} gravada e salva com sucesso no Supabase!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar tratativa: {e}")

# --- OUTRAS TELAS ---
elif menu_opcao == "➕ Novo Alerta":
    st.title("➕ CADASTRAR NOVO ALERTA")
    with st.form("form_novo", clear_on_submit=True):
        id_alerta = st.text_input("Nº do Alerta (ID)")
        produto = st.text_input("Código do Produto")
        lote = st.text_input("Lote")
        defeito = st.text_input("Defeito Detectado")
        area = st.selectbox("Área Responsável", ["Produção", "Ferramentaria", "Processo", "Injeção"])
        responsavel = st.text_input("Nome do Responsável")
        if st.form_submit_button("Gravar Ocorrência"):
            novo = {"id": id_alerta, "produto": produto, "lote": lote, "defeito": defeito, "area": area, "responsavel": responsavel, "prazo": date.today().strftime("%Y-%m-%d"), "status": "EM DIA"}
            supabase.table("alertas").insert(novo).execute()
            st.success("Salvo!")
            st.cache_data.clear()

elif menu_opcao == "🔔 Alertas Abertos":
    st.title("🔔 ALERTAS ABERTOS")
    st.dataframe(df_alertas[df_alertas['status'] != 'ENCERRADO'], use_container_width=True, hide_index=True)

elif menu_opcao == "⏰ Alertas Vencidos":
    st.title("⏰ ALERTAS VENCIDOS")
    st.dataframe(df_alertas[df_alertas['status'] == 'VENCIDO'], use_container_width=True, hide_index=True)

elif menu_opcao == "✔️ Encerrados":
    st.title("✔️ ALERTAS ENCERRADOS")
    st.dataframe(df_alertas[df_alertas['status'] == 'ENCERRADO'], use_container_width=True, hide_index=True)

elif menu_opcao in ["📊 Indicadores", "📈 Análises", "📄 Relatórios"]:
    st.title(f"📄 {menu_opcao}")
    st.dataframe(df_alertas, use_container_width=True, hide_index=True)
