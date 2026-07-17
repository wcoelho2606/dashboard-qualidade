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
        
        /* Estilos do Fluxo de Tratativas Visual */
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
            if row['status'] == '6. Encerramento':
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

# --- MENU LATERAL DE NAVEGAÇÃO ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield-with-growth-chart.png", width=80)
    st.markdown("### GESTÃO DE ALERTAS")
    st.markdown("---")
    menu_opcao = st.radio(
        "Navegação", 
        [
            "🏠 Visão Geral", 
            "➕ Cadastrar Novo Alerta", 
            "⚙️ Responder Tratativa (Responsável)", 
            "🔔 Alertas Abertos", 
            "⏰ Alertas Vencidos", 
            "✔️ Encerrados", 
            "📊 Indicadores"
        ]
    )

if df_alertas.empty:
    st.warning("Aguardando dados da base Supabase...")
    st.stop()

# ==========================================
# ====== 1. TELA: VISÃO GERAL (DASHBOARD) ======
# ==========================================
if menu_opcao == "🏠 Visão Geral":
    st.title("GESTÃO DE ALERTAS DE QUALIDADE")
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

    # Tabela Executiva Ocupando a Largura Ideal
    st.markdown("### 📋 ALERTAS ATIVOS EM FÁBRICA")
    df_abertos = df_alertas[df_alertas['status'] != '6. Encerramento'].copy()
    if not df_abertos.empty:
        df_display = df_abertos[["id", "produto", "lote", "defeito", "area", "responsavel", "prazo", "dias_restantes", "status", "status_visual"]].copy()
        df_display.columns = ["Nº AQ", "Produto", "Lote", "Defeito Detectado", "Área Responsável", "Responsável", "Prazo", "Dias Restantes", "Etapa Atual", "Status"]
        st.dataframe(df_display.style.map(colorir_status, subset=["Status"]).map(colorir_dias, subset=["Dias Restantes"]), use_container_width=True, hide_index=True)
    else:
        st.success("🎉 Excelente! Nenhum alerta em aberto no momento.")

    # ====== 4 GRÁFICOS INTEGRADOS ======
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

# ===================================================
# ====== 2. TELA: ABERTURA DE ALERTA ======
# ===================================================
elif menu_opcao == "➕ Cadastrar Novo Alerta":
    st.title("➕ REGISTRO DE NOVA NÃO-CONFORMIDADE")
    st.markdown("Área destinada para a emissão e abertura de novas Ordens de AQ.")
    st.markdown("---")
    
    with st.form("form_cadastro_usuarios", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            id_alerta = st.text_input("Nº do Alerta (ID AQ)", placeholder="Ex: AQ-2026-035")
            produto = st.text_input("Código do Produto", placeholder="Ex: 41.6830.010")
            lote = st.text_input("Lote de Produção", placeholder="Ex: 474900")
        with col2:
            defeito = st.text_input("Defeito Detectado", placeholder="Ex: Pinho quebrado")
            area = st.selectbox("Área Notificada", ["Produção", "Ferramentaria", "Processo", "Injeção"])
            responsavel = st.text_input("Responsável pela Área")
            
        if st.form_submit_button("Gravar Ocorrência e Iniciar Fluxo"):
            if not id_alerta or not produto or not lote or not defeito or not responsavel:
                st.warning("⚠️ Preencha todos os campos obrigatórios!")
            else:
                novo = {
                    "id": id_alerta, "produto": produto, "lote": lote, "defeito": defeito,
                    "area": area, "responsavel": responsavel, "prazo": date.today().strftime("%Y-%m-%d"),
                    "status": "1. Alerta Emitido"
                }
                try:
                    supabase.table("alertas").insert(novo).execute()
                    st.success(f"🎉 Alerta {id_alerta} cadastrado e enviado para o fluxo com sucesso!")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# ==========================================================
# ====== 3. NOVA TELA EXCLUSIVA: WORKFLOW DE TRATATIVAS ======
# ==========================================================
elif menu_opcao == "⚙️ Responder Tratativa (Responsável)":
    st.title("⚙️ FLUXO DE TRATATIVAS E EVOLUÇÃO DE STATUS")
    st.markdown("Painel operacional para atualização de planos de ação, prazos e encerramento.")
    st.markdown("---")
    
    df_abertos = df_alertas[df_alertas['status'] != '6. Encerramento'].copy()
    
    if df_abertos.empty:
        st.success("Não existem alertas abertos aguardando tratativa!")
    else:
        # Combo para seleção do alerta a ser tratado
        lista_opcoes = df_abertos.apply(lambda r: f"{r['id']} - {r['defeito']} ({r['responsavel']})", axis=1).tolist()
        selecao_texto = st.selectbox("Escolha a AQ para lançar as informações:", lista_opcoes)
        
        # Resgatar o ID correto selecionado
        id_selecionado = selecao_texto.split(" - ")[0]
        item_aq = df_alertas[df_alertas['id'] == id_selecionado].iloc[0]
        status_atual = item_aq.get('status', '1. Alerta Emitido')
        
        # Bloco de Resumo da Ocorrência
        with st.container(border=True):
            c_info1, c_info2, c_info3 = st.columns(3)
            c_info1.markdown(f"**Nº AQ:** `{item_aq['id']}`")
            c_info1.markdown(f"**Componente:** `{item_aq['produto']}`")
            c_info2.markdown(f"**Área Responsável:** `{item_aq['area']}`")
            c_info2.markdown(f"**Responsável Atual:** `{item_aq['responsavel']}`")
            c_info3.markdown(f"**Defeito:** `{item_aq['defeito']}`")
            c_info3.markdown(f"**Data Limite:** `{item_aq['prazo'].strftime('%d/%m/%Y')}`")
            
        # Linha do Tempo Visual do Status
        st.markdown("### 🔄 Linha de Evolução do Status:")
        fases = {"1. Alerta Emitido": 1, "2. Em Análise": 2, "3. Ação Definida": 3, "4. Em Implementação": 4, "5. Aguardando Validação": 5, "6. Encerramento": 6}
        num_fase = fases.get(status_atual, 1)
        
        def get_classe(p): return "step-active" if num_fase == p else ("step-done" if num_fase > p else "step-todo")

        with st.container(border=True):
            c1, s1, c2, s2, c3, s3, c4, s4, c5, s5, c6 = st.columns([1, 0.2, 1, 0.2, 1, 0.2, 1, 0.2, 1, 0.2, 1])
            with c1: st.markdown(f'<div class="fluxo-step {get_classe(1)}">1</div><p style="font-size:10px; text-align:center; font-weight:bold;">Alerta Emitido</p>', unsafe_allow_html=True)
            with s1: st.markdown("<h4 style='text-align:center; color:gray;'>➔</h4>", unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="fluxo-step {get_classe(2)}">2</div><p style="font-size:10px; text-align:center; font-weight:bold;">Em Análise</p>', unsafe_allow_html=True)
            with s2: st.markdown("<h4 style='text-align:center; color:gray;'>➔</h4>", unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="fluxo-step {get_classe(3)}">3</div><p style="font-size:10px; text-align:center; font-weight:bold;">Ação Definida</p>', unsafe_allow_html=True)
            with s3: st.markdown("<h4 style='text-align:center; color:gray;'>➔</h4>", unsafe_allow_html=True)
            with c4: st.markdown(f'<div class="fluxo-step {get_classe(4)}">4</div><p style="font-size:10px; text-align:center; font-weight:bold;">Em Implementação</p>', unsafe_allow_html=True)
            with s4: st.markdown("<h4 style='text-align:center; color:gray;'>➔</h4>", unsafe_allow_html=True)
            with c5: st.markdown(f'<div class="fluxo-step {get_classe(5)}">5</div><p style="font-size:10px; text-align:center; font-weight:bold;">Aguardando Validação</p>', unsafe_allow_html=True)
            with s5: st.markdown("<h4 style='text-align:center; color:gray;'>➔</h4>", unsafe_allow_html=True)
            with c6: st.markdown(f'<div class="fluxo-step {get_classe(6)}">6</div><p style="font-size:10px; text-align:center; font-weight:bold;">Encerrado</p>', unsafe_allow_html=True)

        # Formulário Dinâmico baseado no Status Atual
        col_cam, col_obs = st.columns([2.5, 1.5])
        with col_cam:
            st.markdown("### 📥 Ações Disponíveis para este Status:")
            
            if status_atual == "1. Alerta Emitido":
                st.info("📌 Alerta aberto recentemente. O **Responsável** mapeado deve confirmar ciência para iniciar a análise técnica.")
                if st.button("✔️ Confirmar Início da Análise (Avançar para Etapa 2)", use_container_width=True, type="primary"):
                    supabase.table("alertas").update({"status": "2. Em Análise"}).eq("id", id_selecionado).execute()
                    st.cache_data.clear()
                    st.rerun()
                    
            elif status_atual == "2. Em Análise":
                st.warning("⚙️ **Definição de Ações corretivas:**")
                act = st.text_area("Descreva a Ação Corretiva Proposta (Bloqueio da Causa Raiz):")
                resp = st.text_input("Defina quem irá implementar fisicamente esta ação na fábrica:")
                if st.button("💾 Gravar Plano e Avançar para Ação Definida", use_container_width=True, type="primary"):
                    if act and resp:
                        txt = f"AÇÃO DEFINIDA: {act}. Executor: {resp}."
                        supabase.table("alertas").update({"status": "3. Ação Definida", "observacoes": txt}).eq("id", id_selecionado).execute()
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Por favor, preencha a descrição da ação e o executor.")
                        
            elif status_atual == "3. Ação Definida":
                st.info("🚀 Plano de Ação aprovado. Clique abaixo assim que der o start na implementação em linha de produção.")
                if st.button("🔧 Iniciar Implementação Físico-Fabril (Ir para Etapa 4)", use_container_width=True, type="primary"):
                    supabase.table("alertas").update({"status": "4. Em Implementação"}).eq("id", id_selecionado).execute()
                    st.cache_data.clear()
                    st.rerun()
                    
            elif status_atual == "4. Em Implementação":
                st.info("👍 Ações em andamento na área produtiva. Ao concluir a alteração, envie para a auditoria da Qualidade.")
                if st.button("✔️ Concluir Execução e Chamar Engenharia da Qualidade", use_container_width=True, type="primary"):
                    supabase.table("alertas").update({"status": "5. Aguardando Validação"}).eq("id", id_selecionado).execute()
                    st.cache_data.clear()
                    st.rerun()
                    
            elif status_atual == "5. Aguardando Validação":
                st.subheader("🛡️ Validação de Eficácia (Exclusivo Qualidade)")
                st.markdown("Auditoria de processo realizada para assegurar o bloqueio definitivo da não-conformidade.")
                if st.button("🔒 Validar Eficácia e Arquivar (ENCERRAR DEFINITIVAMENTE)", use_container_width=True, type="primary"):
                    supabase.table("alertas").update({"status": "6. Encerramento"}).eq("id", id_selecionado).execute()
                    st.cache_data.clear()
                    st.rerun()

        with col_obs:
            st.markdown("**📜 Histórico / Notas de Evolução:**")
            st.info(item_aq.get('observacoes', 'Nenhuma anotação inserida para este alerta ainda.'))

# --- OUTRAS ABAS DO PROJETO MANTIDAS ---
elif menu_opcao == "🔔 Alertas Abertos":
    st.title("🔔 ALERTAS ABERTOS")
    st.dataframe(df_alertas[df_alertas['status'] != '6. Encerramento'], use_container_width=True, hide_index=True)

elif menu_opcao == "⏰ Alertas Vencidos":
    st.title("⏰ ALERTAS VENCIDOS")
    st.dataframe(df_alertas[df_alertas['status_visual'] == 'VENCIDO'], use_container_width=True, hide_index=True)

elif menu_opcao == "✔️ Encerrados":
    st.title("✔️ ALERTAS ENCERRADOS")
    st.dataframe(df_alertas[df_alertas['status'] == '6. Encerramento'], use_container_width=True, hide_index=True)

elif menu_opcao == "📊 Indicadores":
    st.title("📊 BASE INTEGRAL DE DADOS")
    st.dataframe(df_alertas, use_container_width=True, hide_index=True)
