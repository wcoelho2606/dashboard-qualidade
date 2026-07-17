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

# Estilização CSS customizada corporativa (Layout, KPIs e Cards)
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
        
        /* Containers nítidos para gráficos */
        .graph-card {
            background-color: #FFFFFF;
            padding: 12px;
            border-radius: 12px;
            border: 2px solid #CBD5E1;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        }
        
        /* Estilos do Fluxo de Tratativas Visual */
        .fluxo-container {
            background-color: #FFFFFF; padding: 15px; border-radius: 12px; border: 2px solid #E2E8F0; margin-bottom: 20px;
        }
        .fluxo-step {
            text-align: center; padding: 10px; border-radius: 50%; width: 50px; height: 50px; line-height: 30px; margin: 0 auto 5px auto; font-size: 18px; font-weight: bold; border: 3px solid #E5E7EB;
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

# 2. Carregar e processar dados dinamicamente
def carregar_dados():
    try:
        resposta = supabase.table("alertas").select("*").execute()
        df = pd.DataFrame(resposta.data)
        if df.empty:
            return pd.DataFrame(), {}, {}, {}, pd.DataFrame()
        
        hoje = date.today()
        df['prazo'] = pd.to_datetime(df['prazo']).dt.date
        
        # Recálculo dinâmico baseado na data atual (17/07/2026)
        for index, row in df.iterrows():
            if row['status'] == 'ENCERRADO':
                df.at[index, 'dias_restantes'] = 0
            else:
                dias = (row['prazo'] - hoje).days
                df.at[index, 'dias_restantes'] = dias
                if dias < 0 and row['status'] not in ['5. Aguardando Validação', '6. Encerramento']:
                    df.at[index, 'status_visual'] = 'VENCIDO'
                elif dias <= 5 and row['status'] not in ['5. Aguardando Validação', '6. Encerramento']:
                    df.at[index, 'status_visual'] = 'PRÓX. DO PRAZO'
                else:
                    df.at[index, 'status_visual'] = 'EM DIA'
                    
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

# --- MENU LATERAL COMPLETO CONFORME A FOTO ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield-with-growth-chart.png", width=80)
    st.markdown("### GESTÃO DE ALERTAS")
    st.markdown("---")
    menu_opcao = st.radio(
        "Navegação", 
        ["🏠 Visão Geral", "🔄 Fluxo de Tratativa", "➕ Novo Alerta", "🔔 Alertas Abertos", "⏰ Alertas Vencidos", "✔️ Encerrados", "📊 Indicadores", "📈 Análises", "📄 Relatórios"]
    )

if df_alertas.empty:
    st.warning("Aguardando carregamento de dados do Supabase...")
    st.stop()

# ==========================================
# ====== 1. TELA: VISÃO GERAL (MODELO ANTERIOR) ======
# ==========================================
if menu_opcao == "🏠 Visão Geral":
    st.title("PAINEL GERAL - ALERTAS DE QUALIDADE")
    st.markdown("---")

    # KPIs Superiores
    total_alertas = len(df_alertas)
    abertos = len(df_alertas[df_alertas['status'] != '6. Encerramento'])
    vencidos = len(df_alertas[df_alertas['status_visual'] == 'VENCIDO'])
    encerrados = len(df_alertas[df_alertas['status'] == '6. Encerramento'])
    percentual_prazo = (encerrados / total_alertas * 100) if total_alertas > 0 else 100.0

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1: st.markdown(f'<div class="kpi-card" style="background-color: #0E4687;"><div class="kpi-title">TOTAL DE ALERTAS</div><div class="kpi-value">{total_alertas}</div></div>', unsafe_allow_html=True)
    with kpi2: st.markdown(f'<div class="kpi-card" style="background-color: #F59E0B;"><div class="kpi-title">ALERTAS ABERTOS</div><div class="kpi-value">{abertos}</div></div>', unsafe_allow_html=True)
    with kpi3: st.markdown(f'<div class="kpi-card" style="background-color: #EF4444;"><div class="kpi-title">ALERTAS VENCIDOS</div><div class="kpi-value">{vencidos}</div></div>', unsafe_allow_html=True)
    with kpi4: st.markdown(f'<div class="kpi-card" style="background-color: #10B981;"><div class="kpi-title">ALERTAS ENCERRADOS</div><div class="kpi-value">{encerrados}</div></div>', unsafe_allow_html=True)
    with kpi5: st.markdown(f'<div class="kpi-card" style="background-color: #F3F4F6; color: #1F2937; border: 1px solid #D1D5DB;"><div class="kpi-title" style="color: #4B5563;">% ENCERRADOS</div><div class="kpi-value" style="color: #111827;">{percentual_prazo:.1f}%</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabela Centralizada + Painel Lateral de Detalhes
    col_tabela, col_detalhes = st.columns([2.8, 1.4])

    with col_tabela:
        st.markdown("### ALERTAS DE QUALIDADE - ABERTOS")
        df_abertos = df_alertas[df_alertas['status'] != '6. Encerramento'].copy()
        if not df_abertos.empty:
            df_display = df_abertos[["id", "produto", "lote", "defeito", "area", "responsavel", "prazo", "dias_restantes", "status_visual"]].copy()
            df_display.columns = ["Nº AQ", "Produto", "Lote", "Defeito Detectado", "Área Responsável", "Responsável", "Prazo", "Dias Restantes", "Status"]
            
            alerta_selecionado = st.selectbox("Selecione uma AQ na lista para carregar os detalhes:", df_display["Nº AQ"].tolist())
            st.dataframe(df_display.style.map(colorir_status, subset=["Status"]).map(colorir_dias, subset=["Dias Restantes"]), use_container_width=True, hide_index=True)
        else:
            st.success("Nenhum alerta em aberto!")
            alerta_selecionado = None

    with col_detalhes:
        if alerta_selecionado:
            item = df_alertas[df_alertas['id'] == alerta_selecionado].iloc[0]
            data_emissao = item.get('data_emissao', '08/07/2026')
            contencao = item.get('acao_contencao', 'Fechamento de cavidades / Correção no processo')
            observacoes = item.get('observacoes', 'Nenhuma observação extra registrada.')
            status_cor = "#EF4444" if item['status_visual'] == "VENCIDO" else ("#F59E0B" if item['status_visual'] == "PRÓX. DO PRAZO" else "#10B981")
            
            with st.container(border=True):
                st.markdown(f"<div style='text-align:center; font-weight:bold; color:#1E3A8A;'>DETALHES DO ALERTA</div>", unsafe_allow_html=True)
                st.markdown(f"<h2 style='text-align:center; color:#EF4444; margin:0;'>{item['id']}</h2>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align:center; font-weight:bold;'>{item['defeito']}</p>", unsafe_allow_html=True)
                st.divider()
                st.markdown(f"📁 **Produto:** &nbsp;&nbsp; `{item['produto']}`")
                st.markdown(f"📦 **Lote:** &nbsp;&nbsp; `{item['lote']}`")
                st.markdown(f"🏢 **Área Responsável:** &nbsp;&nbsp; `{item['area']}`")
                st.markdown(f"👤 **Responsável:** &nbsp;&nbsp; `{item['responsavel']}`")
                st.markdown(f"📅 **Data de Emissão:** &nbsp;&nbsp; `{data_emissao}`")
                st.markdown(f"🕒 **Prazo para Ação:** &nbsp;&nbsp; <span style='color: #EF4444; font-weight: bold;'>{item['prazo'].strftime('%d/%m/%Y')}</span>", unsafe_allow_html=True)
                st.markdown(f"🕒 **Dias Restantes:** &nbsp;&nbsp; <span style='color: {status_cor}; font-weight: bold;'>{item['dias_restantes']}</span>", unsafe_allow_html=True)
                st.markdown(f"🛡️ **Status Atual:** <span style='background-color: {status_cor}; color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 11px;'>{item['status_visual']}</span>", unsafe_allow_html=True)
                st.divider()
                st.markdown("⚠️ **Ação de Contenção:**")
                st.caption(contencao)
                st.markdown("📣 **Observações:**")
                st.info(observacoes)

    # 4 Gráficos com as Bordas Contornadas
    st.markdown("<br>", unsafe_allow_html=True)
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
                legenda_formatada = [f"{lbl}<br>{val} ({val/total_status*105:.1f}%)" for lbl, val in zip(status_dist.keys(), status_dist.values())]
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

# ==========================================
# ====== 2. TELA: NOVA ABA - FLUXO DE TRATATIVA ======
# ==========================================
elif menu_opcao == "🔄 Fluxo de Tratativa":
    st.title("🔄 WORKFLOW E FLUXO DE TRATATIVAS")
    st.markdown("Interface interativa para apontamento e evolução das não-conformidades.")
    st.markdown("---")
    
    # Dropdown para selecionar qual AQ tratar
    lista_aqs = df_alertas["id"].tolist()
    aq_tratar = st.selectbox("Selecione a AQ que deseja interagir ou dar andamento:", lista_aqs)
    
    item_aq = df_alertas[df_alertas['id'] == aq_tratar].iloc[0]
    status_atual = item_aq.get('status', '1. Alerta Emitido')
    
    # Pipeline Visual Exibido no Topo
    fases = {"1. Alerta Emitido": 1, "2. Em Análise": 2, "3. Ação Definida": 3, "4. Em Implementação": 4, "5. Aguardando Validação": 5, "6. Encerramento": 6}
    num_fase = fases.get(status_atual, 1)
    
    def get_classe(p): return "step-active" if num_fase == p else ("step-done" if num_fase > p else "step-todo")

    with st.container(border=True):
        st.markdown("<h6 style='text-align: center; color: #1E3A8A;'>PIPELINE DO FLUXO OPERACIONAL</h6>", unsafe_allow_html=True)
        c1, s1, c2, s2, c3, s3, c4, s4, c5, s5, c6 = st.columns([1, 0.2, 1, 0.2, 1, 0.2, 1, 0.2, 1, 0.2, 1])
        with c1: st.markdown(f'<div class="fluxo-step {get_classe(1)}">1</div><p style="font-size:10px; text-align:center; font-weight:bold;">Alerta Emitido<br>Qualidade</p>', unsafe_allow_html=True)
        with s1: st.markdown("<h4 style='text-align:center; color:gray;'>➔</h4>", unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="fluxo-step {get_classe(2)}">2</div><p style="font-size:10px; text-align:center; font-weight:bold;">Em Análise<br>Responsável</p>', unsafe_allow_html=True)
        with s2: st.markdown("<h4 style='text-align:center; color:gray;'>➔</h4>", unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="fluxo-step {get_classe(3)}">3</div><p style="font-size:10px; text-align:center; font-weight:bold;">Ação Definida<br>Responsável</p>', unsafe_allow_html=True)
        with s3: st.markdown("<h4 style='text-align:center; color:gray;'>➔</h4>", unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="fluxo-step {get_classe(4)}">4</div><p style="font-size:10px; text-align:center; font-weight:bold;">Em Implementação<br>Responsável</p>', unsafe_allow_html=True)
        with s4: st.markdown("<h4 style='text-align:center; color:gray;'>➔</h4>", unsafe_allow_html=True)
        with c5: st.markdown(f'<div class="fluxo-step {get_classe(5)}">5</div><p style="font-size:10px; text-align:center; font-weight:bold;">Aguardando Validação<br>Qualidade</p>', unsafe_allow_html=True)
        with s5: st.markdown("<h4 style='text-align:center; color:gray;'>➔</h4>", unsafe_allow_html=True)
        with c6: st.markdown(f'<div class="fluxo-step {get_classe(6)}">6</div><p style="font-size:10px; text-align:center; font-weight:bold;">Encerrado<br>Qualidade</p>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Formulários Condicionais de Tratativa
    col_campos, col_info = st.columns([2.5, 1.5])
    
    with col_campos:
        st.subheader("📝 Ações de Avanço do Processo")
        
        # Etapa 1 -> 2
        if status_atual in ["1. Alerta Emitido", "1"]:
            st.info("📌 O alerta foi emitido. O **Responsável** deve confirmar o recebimento e iniciar a análise.")
            if st.button("✔️ [RESPONSÁVEL] Confirmar Análise Iniciada (Dar OK)", use_container_width=True, type="primary"):
                supabase.table("alertas").update({"status": "2. Em Análise"}).eq("id", aq_tratar).execute()
                st.success("OK gravado! Status alterado para: Em Análise.")
                st.cache_data.clear()
                st.rerun()
                
        # Etapa 2 -> 3
        elif status_atual == "2. Em Análise":
            st.warning("⚙️ **Responsável**, inclua a ação de engenharia recomendada e o responsável técnico pela execução:")
            acao_input = st.text_area("Descreva a Ação Definida (Correção do Problema):")
            resp_acao_input = st.text_input("Defina quem vai ser o Responsável por implementar esta ação:")
            
            if st.button("💾 Adicionar Ação e Avançar Status", use_container_width=True, type="primary"):
                if not acao_input or not resp_acao_input:
                    st.error("Preencha todos os campos antes de salvar!")
                else:
                    texto_final = f"AÇÃO DEFINIDA: {acao_input}. Executor: {resp_acao_input}."
                    supabase.table("alertas").update({"status": "3. Ação Definida", "observacoes": texto_final}).eq("id", aq_tratar).execute()
                    st.success("Ação registrada com sucesso!")
                    st.cache_data.clear()
                    st.rerun()
                    
        # Etapa 3 -> 4
        elif status_atual == "3. Ação Definida":
            st.info("📌 Ação planejada. Clique abaixo para sinalizar o início da execução em fábrica.")
            if st.button("🚀 Iniciar Implementação da Ação em Fábrica", use_container_width=True, type="primary"):
                supabase.table("alertas").update({"status": "4. Em Implementação"}).eq("id", aq_tratar).execute()
                st.cache_data.clear()
                st.rerun()
                
        # Etapa 4 -> 5
        elif status_atual == "4. Em Implementação":
            st.warning("📌 Ação em execução física. Assim que finalizar a correção, envie para a auditoria.")
            if st.button("✔️ Concluir Execução e Solicitar Validação da Qualidade", use_container_width=True, type="primary"):
                supabase.table("alertas").update({"status": "5. Aguardando Validação"}).eq("id", aq_tratar).execute()
                st.cache_data.clear()
                st.rerun()

        # Etapa 5 -> 6 (Validação e Encerramento)
        elif status_atual == "5. Aguardando Validação":
            st.subheader("🛡️ Validação da Engenharia da Qualidade")
            st.caption("Verifique a eficácia e encerre permanentemente a não-conformidade.")
            if st.button("🔒 Validar Eficácia e Dar OK (ENCERRAR ALERTA)", use_container_width=True, type="primary"):
                supabase.table("alertas").update({"status": "6. Encerramento"}).eq("id", aq_tratar).execute()
                st.success("🎉 Alerta validado e mudado para status ENCERRADO com sucesso!")
                st.cache_data.clear()
                st.rerun()
                
        elif status_atual == "6. Encerramento":
            st.success("✅ Este Alerta já foi completamente corrigido e encontra-se com status de ENCERRADO.")

    with col_info:
        with st.container(border=True):
            st.markdown("##### 🔍 Resumo Técnico do Alerta")
            st.write(f"**Código AQ:** {item_aq['id']}")
            st.write(f"**Produto:** {item_aq['produto']}")
            st.write(f"**Lote:** {item_aq['lote']}")
            st.write(f"**Defeito:** {item_aq['defeito']}")
            st.write(f"**Histórico/Observações:**")
            st.caption(item_aq.get('observacoes', 'Sem observações gravadas.'))

# ==========================================
# ====== OUTRAS ABAS MANTIDAS INTEGRALMENTE ===
# ==========================================
elif menu_opcao == "➕ Novo Alerta":
    st.title("➕ CADASTRAR NOVO ALERTA")
    with st.form("form_novo", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            id_alerta = st.text_input("Nº do Alerta (ID)")
            produto = st.text_input("Código do Produto")
            lote = st.text_input("Lote")
        with c2:
            defeito = st.text_input("Defeito Detectado")
            area = st.selectbox("Área", ["Produção", "Ferramentaria", "Processo", "Injeção"])
            responsavel = st.text_input("Responsável Técnico")
        if st.form_submit_button("Gravar no Supabase"):
            novo = {"id": id_alerta, "produto": produto, "lote": lote, "defeito": defeito, "area": area, "responsavel": responsavel, "prazo": date.today().strftime("%Y-%m-%d"), "status": "1. Alerta Emitido"}
            supabase.table("alertas").insert(novo).execute()
            st.success("Salvo com sucesso!")
            st.cache_data.clear()

elif menu_opcao == "🔔 Alertas Abertos":
    st.title("🔔 ALERTAS ABERTOS")
    st.dataframe(df_alertas[df_alertas['status'] != '6. Encerramento'], use_container_width=True, hide_index=True)

elif menu_opcao == "⏰ Alertas Vencidos":
    st.title("⏰ ALERTAS VENCIDOS")
    st.dataframe(df_alertas[df_alertas['status_visual'] == 'VENCIDO'], use_container_width=True, hide_index=True)

elif menu_opcao == "✔️ Encerrados":
    st.title("✔️ ALERTAS ENCERRADOS")
    st.dataframe(df_alertas[df_alertas['status'] == '6. Encerramento'], use_container_width=True, hide_index=True)

elif menu_opcao == "📊 Indicadores" or menu_opcao == "📈 Análises" or menu_opcao == "📄 Relatórios":
    st.title(f"📄 {menu_opcao}")
    st.dataframe(df_alertas, use_container_width=True, hide_index=True)
