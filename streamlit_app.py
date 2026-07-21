import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from supabase import create_client
import base64
from io import BytesIO
from PIL import Image, ImageOps
from streamlit_paste_button import paste_image_button

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
        
        .fluxo-etapa-ativa {
            background-color: #FEF9C3; border: 2px solid #EAB308; border-radius: 12px; padding: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .fluxo-etapa-concluida {
            background-color: #ECFDF5; border: 2px solid #10B981; border-radius: 12px; padding: 10px; text-align: center;
        }
        .fluxo-etapa-apagada {
            background-color: #F3F4F6; border: 2px dashed #D1D5DB; border-radius: 12px; padding: 10px; text-align: center; opacity: 0.5;
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

# 2. Carregar e processar dados em tempo real
def carregar_dados():
    try:
        resposta = supabase.table("alertas").select("*").execute()
        df = pd.DataFrame(resposta.data)
        if df.empty:
            return pd.DataFrame(), {}, {}, {}, pd.DataFrame()
        
        hoje = date.today()
        df['prazo'] = pd.to_datetime(df['prazo']).dt.date
        
        if 'etapa_atual' not in df.columns:
            df['etapa_atual'] = 1

        for index, row in df.iterrows():
            if row.get('etapa_atual', 1) >= 6 or row['status'] == 'ENCERRADO':
                df.at[index, 'status'] = 'ENCERRADO'
                df.at[index, 'etapa_atual'] = 6
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
        
        area_dist = df["area"].value_counts().to_dict() if "area" in df.columns else {}
        status_dist = df["status"].value_counts().to_dict() if "status" in df.columns else {}
        defeito_dist = df["defeito"].value_counts().to_dict() if "defeito" in df.columns else {}
        
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
    elif val == "ENCERRADO": return 'background-color: #E0E7FF; color: #3730A3; font-weight: bold; text-align: center;'
    return 'background-color: #F3F4F6; color: #374151; text-align: center;'

def colorir_dias(val):
    if val < 0: return 'color: #EF4444; font-weight: bold;'
    elif val <= 5: return 'color: #F59E0B; font-weight: bold;'
    return 'color: #10B981; font-weight: bold;'

def processar_e_converter_imagem(imagem_input, tamanho_alvo=(1000, 600)):
    if imagem_input is not None:
        try:
            if isinstance(imagem_input, Image.Image):
                img = imagem_input
            else:
                img = Image.open(imagem_input)
                
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Mantém a proporção original da imagem (sem cortar o produto) e centraliza com fundo branco
            img.thumbnail(tamanho_alvo, Image.Resampling.LANCZOS)
            fundo = Image.new("RGB", tamanho_alvo, (255, 255, 255))
            
            pos_x = (tamanho_alvo[0] - img.width) // 2
            pos_y = (tamanho_alvo[1] - img.height) // 2
            fundo.paste(img, (pos_x, pos_y))
            
            buffered = BytesIO()
            fundo.save(buffered, format="JPEG", quality=95)
            base64_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            return f"data:image/jpeg;base64,{base64_str}"
        except Exception as e:
            st.error(f"Erro ao processar imagem: {e}")
            return None
    return None

def gerar_proximo_id(df):
    ano_atual = datetime.now().strftime("%Y")
    prefixo = f"AQ-{ano_atual}-"
    
    if df.empty or "id" not in df.columns:
        return f"{prefixo}001"
    
    ids_existentes = df["id"].dropna().astype(str).tolist()
    numeros = []
    
    for i_id in ids_existentes:
        if prefixo in i_id:
            try:
                num_str = i_id.replace(prefixo, "")
                numeros.append(int(num_str))
            except:
                pass
                
    proximo_num = (max(numeros) + 1) if numeros else 1
    return f"{prefixo}{proximo_num:03d}"

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
            "🖼️ Gerenciar Fotos",
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
    
    col_tabela, col_detalhes = st.columns([2.2, 1.8])

    with col_tabela:
        df_abertos = df_alertas[df_alertas['status'] != 'ENCERRADO'].copy()
        aq_selecionada_visao = None
        if not df_abertos.empty:
            df_display = df_abertos[["id", "produto", "lote", "defeito", "area", "responsavel", "prazo", "dias_restantes", "status"]].copy()
            df_display.columns = ["Nº AQ", "Produto", "Lote", "Defeito", "Área Responsável", "Responsável", "Prazo", "Dias Restantes", "Status"]
            styler = df_display.style.map(colorir_status, subset=["Status"]).map(colorir_dias, subset=["Dias Restantes"])
            st.dataframe(styler, use_container_width=True, hide_index=True)
            
            aq_selecionada_visao = st.selectbox("🔍 Selecione o Alerta para ver os Detalhes e Fotos:", df_abertos["id"].tolist())
        else:
            st.success("Nenhum alerta em aberto no momento!")

    with col_detalhes:
        if aq_selecionada_visao:
            item = df_alertas[df_alertas['id'] == aq_selecionada_visao].iloc[0]
            status_cor = "#EF4444" if item['status'] == "VENCIDO" else ("#F59E0B" if item['status'] == "PRÓX. DO PRAZO" else "#10B981")
            
            st.markdown(f"""
            <div style="background-color: #1E3A8A; padding: 12px; border-radius: 8px 8px 0px 0px; color: white; text-align: center;">
                <div style="font-size: 12px; font-weight: 700;">AUDITORIA DO ALERTA</div>
                <div style="font-size: 22px; font-weight: 800;">{item['id']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.container(border=True):
                st.markdown(f"📌 **Defeito:** `{item['defeito']}`")
                st.markdown(f"📁 **Produto:** `{item['produto']}` | 📦 **Lote:** `{item['lote']}`")
                st.markdown(f"🏢 **Área:** `{item['area']}` | 👤 **Resp.:** `{item['responsavel']}`")
                st.markdown(f"🕒 **Prazo:** {item['prazo']} | 🛡️ **Status:** <span style='background-color: {status_cor}; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold;'>{item['status']}</span>", unsafe_allow_html=True)
                
                st.divider()
                st.markdown("🖼️ **REGISTRO FOTOGRÁFICO (PADRÃO OK / NOK)**")
                
                f_col1, f_col2 = st.columns(2)
                with f_col1:
                    st.markdown("<div style='text-align: center; font-weight: bold; color: #10B981; background-color: #ECFDF5; padding: 4px; border-radius: 4px;'>FOTO OK</div>", unsafe_allow_html=True)
                    foto_ok_val = item.get('foto_ok')
                    if foto_ok_val and pd.notnull(foto_ok_val) and str(foto_ok_val).strip() != "":
                        try:
                            st.image(str(foto_ok_val), use_column_width=True)
                        except:
                            st.warning("Erro ao carregar imagem OK.")
                    else:
                        st.info("Nenhuma foto OK cadastrada.")
                        
                with f_col2:
                    st.markdown("<div style='text-align: center; font-weight: bold; color: #EF4444; background-color: #FEE2E2; padding: 4px; border-radius: 4px;'>FOTO NOK</div>", unsafe_allow_html=True)
                    foto_nok_val = item.get('foto_nok')
                    if foto_nok_val and pd.notnull(foto_nok_val) and str(foto_nok_val).strip() != "":
                        try:
                            st.image(str(foto_nok_val), use_column_width=True)
                        except:
                            st.warning("Erro ao carregar imagem NOK.")
                    else:
                        st.info("Nenhuma foto NOK cadastrada.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### INDICADORES E ANÁLISES GRÁFICAS")
    g_col1, g_col2, g_col3, g_col4 = st.columns(4)

    with g_col1:
        with st.container(border=True):
            if area_dist:
                fig1 = go.Figure(data=[go.Pie(labels=list(area_dist.keys()), values=list(area_dist.values()), hole=0.5, textinfo='label+value+percent', showlegend=False)])
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
                fig3 = go.Figure(go.Bar(x=df_def['Qtd'], y=df_def['Defeito'], orientation='h', marker_color='#0E4687', text=df_def['Qtd'], textposition='outside'))
                fig3.update_layout(title=dict(text="<b>ALERTAS POR TIPO DE DEFEITO</b>", x=0.5, y=0.95, font=dict(size=13, color="#1E3A8A")), margin=dict(l=10, r=30, t=50, b=10), height=250, xaxis=dict(showgrid=False, visible=False), yaxis=dict(showgrid=False, tickfont=dict(size=11)), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Sem dados de defeitos.")

    with g_col4:
        with st.container(border=True):
            if not df_tempo.empty:
                fig4 = go.Figure()
                fig4.add_trace(go.Scatter(x=df_tempo["Mês"], y=df_tempo["Dias"], mode='lines+markers+text', text=df_tempo["Dias"], textposition='top center', line=dict(color='#0284C7', width=2.5)))
                fig4.update_layout(title=dict(text="<b>TEMPO MÉDIO DE FECHAMENTO (DIAS)</b>", x=0.5, y=0.95, font=dict(size=13, color="#1E3A8A")), margin=dict(l=20, r=20, t=50, b=10), height=250, xaxis=dict(showgrid=False), yaxis=dict(showgrid=False, range=[0, 35], tickfont=dict(size=10)), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar': False})

    # =========================================================================
    # ====== FLUXO DE TRATATIVAS NA TELA INICIAL (VISÃO GERAL) ========
    # =========================================================================
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### FLUXO DE TRATATIVAS")
    
    if aq_selecionada_visao:
        item_visao = df_alertas[df_alertas['id'] == aq_selecionada_visao].iloc[0]
        etapa_visao = int(item_visao.get("etapa_atual", 1))

        def formatar_data_banco(coluna_db, fallback_str="-"):
            val = item_visao.get(coluna_db)
            if pd.notnull(val) and val != "" and val is not None:
                try:
                    dt_obj = datetime.fromisoformat(str(val).replace('Z', '+00:00'))
                    return dt_obj.strftime('%d/%m/%Y\n%H:%M')
                except:
                    return str(val)
            return fallback_str

        data_padrao_emissao = pd.to_datetime(item_visao.get('prazo')).strftime('%d/%m/%Y\n07:15') if pd.notnull(item_visao.get('prazo')) else "21/07/2026\n07:15"
        data_padrao_analise = pd.to_datetime(item_visao.get('prazo')).strftime('%d/%m/%Y\n08:40') if pd.notnull(item_visao.get('prazo')) else "21/07/2026\n08:40"

        passos_fluxo = [
            {"num": 1, "emoji": "📄", "titulo": "Alerta Emitido", "sub": "Qualidade", "data": formatar_data_banco('data_etapa_1', data_padrao_emissao)},
            {"num": 2, "emoji": "📑", "titulo": "Em Análise", "sub": item_visao.get('responsavel', 'Responsável'), "data": formatar_data_banco('data_etapa_2', data_padrao_analise if etapa_visao >= 2 else "-")},
            {"num": 3, "emoji": "📋", "titulo": "Ação Definida", "sub": item_visao.get('responsavel', 'Responsável'), "data": formatar_data_banco('data_etapa_3')},
            {"num": 4, "emoji": "⚙️", "titulo": "Em Implementação", "sub": item_visao.get('responsavel_implementacao', item_visao.get('responsavel', 'Responsável')), "data": formatar_data_banco('data_etapa_4')},
            {"num": 5, "emoji": "📑", "titulo": "Aguardando Validação", "sub": item_visao.get('validador_qualidade', 'Qualidade'), "data": formatar_data_banco('data_etapa_5')},
            {"num": 6, "emoji": "✅", "titulo": "Encerrado", "sub": "Qualidade", "data": formatar_data_banco('data_etapa_6')}
        ]

        cols_f = st.columns(6)
        for idx, p in enumerate(passos_fluxo):
            with cols_f[idx]:
                if etapa_visao == 6 or p["num"] < etapa_visao:
                    st.markdown(f"""
                        <div class="fluxo-etapa-concluida">
                            <div style="font-size: 24px;">✅</div>
                            <div style="font-weight: bold; font-size: 12px; color: #065F46;">{p['num']}. {p['titulo']}</div>
                            <div style="font-size: 10px; color: #047857;">{p['sub']}</div>
                            <hr style="margin: 5px 0;">
                            <small style="color: #374151; white-space: pre-line;">{p['data']}</small>
                        </div>
                    """, unsafe_allow_html=True)
                elif p["num"] == etapa_visao:
                    st.markdown(f"""
                        <div class="fluxo-etapa-ativa">
                            <div style="font-size: 24px;">⏳</div>
                            <div style="font-weight: bold; font-size: 12px; color: #92400E;">{p['num']}. {p['titulo']}</div>
                            <div style="font-size: 10px; color: #B45309;">{p['sub']} (Atual)</div>
                            <hr style="margin: 5px 0;">
                            <small style="color: #374151; white-space: pre-line;">{p['data'] if p['data'] != '-' else 'Pendente'}</small>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div class="fluxo-etapa-apagada">
                            <div style="font-size: 24px; filter: grayscale(100%);">{p['emoji']}</div>
                            <div style="font-weight: bold; font-size: 12px; color: #6B7280;">{p['num']}. {p['titulo']}</div>
                            <div style="font-size: 10px; color: #9CA3AF;">{p['sub']}</div>
                            <hr style="margin: 5px 0;">
                            <small style="color: #9CA3AF; white-space: pre-line;">-</small>
                        </div>
                    """, unsafe_allow_html=True)

# =======================================================
# ====== 2. TELA: INSERIR TRATATIVA =====================
# =======================================================
elif menu_opcao == "➕ Inserir Tratativa":
    st.title("➕ FLUXO DE TRATATIVAS E REGISTRO")
    st.markdown("Preencha ou ajuste os dados das fases alcançadas. Volte etapas caso necessário.")
    st.markdown("---")
    
    lista_aqs = df_alertas["id"].tolist()
    aq_selecionada = st.selectbox("Escolha o Nº da AQ para gerenciar a tratativa:", lista_aqs)
    
    item_aq = df_alertas[df_alertas['id'] == aq_selecionada].iloc[0]
    etapa_atual = int(item_aq.get("etapa_atual", 1))

    st.markdown("### 🔄 Andamento do Fluxo de Tratativas")
    etapas_nomes = ["1. Alerta Emitido", "2. Em Análise", "3. Ação Definida", "4. Em Implementação", "5. Aguardando Validação", "6. Encerrado"]
    
    cols_fluxo = st.columns(6)
    for i, nome_etapa in enumerate(etapas_nomes, start=1):
        with cols_fluxo[i-1]:
            if etapa_atual == 6 or i < etapa_atual:
                st.success(f"✅\n\n**{nome_etapa}**")
            elif i == etapa_atual:
                st.warning(f"⏳\n\n**{nome_etapa}**\n*(Atual)*")
            else:
                st.markdown(f"⚪\n\n_{nome_etapa}_")

    st.markdown("---")
    
    col_detalhes, col_controles = st.columns([1.2, 1.8])
    
    with col_detalhes:
        st.subheader("📋 Informações do Alerta")
        st.write(f"**Produto:** {item_aq['produto']}")
        st.write(f"**Lote:** {item_aq['lote']}")
        st.write(f"**Defeito:** {item_aq['defeito']}")
        st.write(f"**Área Responsável:** {item_aq['area']}")
        st.write(f"**Responsável Principal:** `{item_aq['responsavel']}`")
        st.write(f"**Prazo:** {item_aq['prazo']}")
        st.info(f"**Status Atual:** {item_aq['status']}")
        
        st.markdown("---")
        st.markdown("🖼️ **Fotos Cadastradas:**")
        f_c1, f_c2 = st.columns(2)
        with f_c1:
            st.caption("Foto OK")
            fo = item_aq.get('foto_ok')
            if fo and pd.notnull(fo) and str(fo).strip() != "":
                try: st.image(str(fo), use_column_width=True)
                except: pass
        with f_c2:
            st.caption("Foto NOK")
            fn = item_aq.get('foto_nok')
            if fn and pd.notnull(fn) and str(fn).strip() != "":
                try: st.image(str(fn), use_column_width=True)
                except: pass

    with col_controles:
        st.subheader("⚙️ Detalhamento por Fase")
        
        causa_db = item_aq.get("causa_raiz") if pd.notnull(item_aq.get("causa_raiz")) and item_aq.get("causa_raiz") != "nan" else ""
        acao_db = item_aq.get("acao_definida") if pd.notnull(item_aq.get("acao_definida")) and item_aq.get("acao_definida") != "nan" else ""
        resp_impl_db = item_aq.get("responsavel_implementacao") if pd.notnull(item_aq.get("responsavel_implementacao")) and item_aq.get("responsavel_implementacao") != "nan" else item_aq['responsavel']
        validador_db = item_aq.get("validador_qualidade") if pd.notnull(item_aq.get("validador_qualidade")) and item_aq.get("validador_qualidade") != "nan" else "Qualidade"

        with st.form("form_tratativa_progressiva"):
            st.markdown(f"**Fase Atual do Alerta:** Etapa {etapa_atual}")
            
            if etapa_atual >= 2:
                st.markdown("---")
                st.markdown("🔍 **Etapa 2 - Causa Raiz / Análise do Problema**")
                nova_causa = st.text_area("Descreva a causa raiz identificada:", value=causa_db)
            else:
                nova_causa = causa_db

            if etapa_atual >= 3:
                st.markdown("---")
                st.markdown("📋 **Etapa 3 - Ação Definida / Corretiva Tomada**")
                nova_acao = st.text_area("Descreva o plano de ação:", value=acao_db)
            else:
                nova_acao = acao_db

            if etapa_atual >= 4:
                st.markdown("---")
                st.markdown("⚙️ **Etapa 4 - Implementação da Correção**")
                novo_resp_impl = st.text_input("Responsável pela Implementação:", value=resp_impl_db)
            else:
                novo_resp_impl = resp_impl_db

            if etapa_atual >= 5:
                st.markdown("---")
                st.markdown("✔️ **Etapa 5 - Validação da Qualidade**")
                novo_validador = st.text_input("Nome do Validador:", value=validador_db)
            else:
                novo_validador = validador_db

            st.markdown("<br>", unsafe_allow_html=True)
            salvar_progresso = st.form_submit_button("💾 Salvar Alterações da Fase", use_container_width=True)
            if salvar_progresso:
                supabase.table("alertas").update({
                    "causa_raiz": nova_causa,
                    "acao_definida": nova_acao,
                    "responsavel_implementacao": novo_resp_impl,
                    "validador_qualidade": novo_validador
                }).eq("id", aq_selecionada).execute()
                st.success("Dados salvos com sucesso!")
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        col_B1, col_B2, col_B3 = st.columns([1.5, 1.5, 1])
        
        with col_B1:
            if etapa_atual > 1:
                if st.button("⬅️ Voltar Etapa Anterior", use_container_width=True):
                    etapa_anterior = etapa_atual - 1
                    dias_atuais = (item_aq['prazo'] - date.today()).days
                    status_calculado = "VENCIDO" if dias_atuais < 0 else ("PRÓX. DO PRAZO" if dias_atuais <= 5 else "EM DIA")
                    
                    dados_volta = {
                        "etapa_atual": etapa_anterior,
                        "status": status_calculado,
                        f"data_etapa_{etapa_atual}": None
                    }
                    if etapa_atual == 6:
                        dados_volta["dias_restantes"] = dias_atuais

                    supabase.table("alertas").update(dados_volta).eq("id", aq_selecionada).execute()
                    st.warning(f"Alerta retornado para a Etapa {etapa_anterior}!")
                    st.rerun()

        with col_B2:
            if etapa_atual < 6:
                if st.button("🚀 Avançar Etapa Atual", use_container_width=True, type="primary"):
                    nova_etapa = etapa_atual + 1
                    agora_iso = datetime.now().isoformat()
                    dados_up = {
                        "etapa_atual": nova_etapa,
                        f"data_etapa_{nova_etapa}": agora_iso
                    }
                    if nova_etapa == 6:
                        dados_up["status"] = "ENCERRADO"
                        dados_up["dias_restantes"] = 0
                    
                    supabase.table("alertas").update(dados_up).eq("id", aq_selecionada).execute()
                    st.success(f"Alerta avançado para a etapa {nova_etapa}!")
                    st.rerun()
            else:
                st.success("Fluxo Concluído!")

        with col_B3:
            if etapa_atual == 6:
                if st.button("🔄 Reabrir", use_container_width=True):
                    dias_atuais = (item_aq['prazo'] - date.today()).days
                    status_reaberto = "VENCIDO" if dias_atuais < 0 else ("PRÓX. DO PRAZO" if dias_atuais <= 5 else "EM DIA")
                    supabase.table("alertas").update({
                        "etapa_atual": 2,
                        "status": status_reaberto,
                        "dias_restantes": dias_atuais
                    }).eq("id", aq_selecionada).execute()
                    st.warning("Alerta retornado para a Etapa 2!")
                    st.rerun()

# =======================================================
# ====== 3. TELA: NOVO ALERTA ===========================
# =======================================================
elif menu_opcao == "➕ Novo Alerta":
    st.title("➕ CADASTRAR NOVO ALERTA")
    st.markdown("---")
    
    proximo_id_sugerido = gerar_proximo_id(df_alertas)
    
    with st.form("form_novo_alerta", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            id_alerta = st.text_input("Nº do Alerta (ID - Gerado Automaticamente)", value=proximo_id_sugerido)
            produto = st.text_input("Código do Produto", placeholder="Ex: 31.9294.35.0")
            lote = st.text_input("Lote", placeholder="Ex: 474950")
            defeito = st.text_input("Defeito Detectado", placeholder="Ex: Peças com deformação")
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
                etapa_inicial = 6 if status == "ENCERRADO" else 1
                agora_iso = datetime.now().isoformat()
                
                novo_registro = {
                    "id": id_alerta, "produto": produto, "lote": lote, "defeito": defeito,
                    "area": area, "responsavel": responsavel, "prazo": prazo.strftime("%Y-%m-%d"),
                    "dias_restantes": int(dias_restantes), "status": status, "etapa_atual": etapa_inicial,
                    "data_etapa_1": agora_iso,
                    "data_etapa_2": agora_iso,
                    "responsavel_implementacao": responsavel,
                    "validador_qualidade": "Qualidade"
                }
                if etapa_inicial == 6:
                    novo_registro["data_etapa_6"] = agora_iso

                try:
                    supabase.table("alertas").insert(novo_registro).execute()
                    st.success(f"🎉 Alerta {id_alerta} salvo com sucesso! Agora adicione as fotos no menu 'Gerenciar Fotos'.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# =======================================================
# ====== 4. TELA: GERENCIAR FOTOS (COM PASTE E APAGAR) ==
# =======================================================
elif menu_opcao == "🖼️ Gerenciar Fotos":
    st.title("🖼️ PAINEL DE GESTÃO DE FOTOS (OK / NOK)")
    st.markdown("Selecione um alerta para atualizar as fotos via upload, colando da área de transferência (Ctrl+V) ou apagando.")
    st.markdown("---")

    lista_aqs_fotos = df_alertas["id"].tolist()
    aq_foto_escolhida = st.selectbox("Selecione o Alerta para gerenciar as imagens:", lista_aqs_fotos)

    if aq_foto_escolhida:
        item_foto = df_alertas[df_alertas['id'] == aq_foto_escolhida].iloc[0]
        
        fc_info1, fc_info2 = st.columns(2)
        with fc_info1:
            st.info(f"**Produto:** {item_foto['produto']} | **Lote:** {item_foto['lote']}")
        with fc_info2:
            st.info(f"**Defeito:** {item_foto['defeito']}")

        st.markdown("---")
        
        col_up1, col_up2 = st.columns(2)
        
        with col_up1:
            st.markdown("### 🟢 FOTO OK (Padrão Ideal)")
            tem_foto_ok = item_foto.get('foto_ok') and pd.notnull(item_foto['foto_ok']) and str(item_foto['foto_ok']).strip() != ""
            if tem_foto_ok:
                try:
                    st.image(str(item_foto['foto_ok']), caption="Foto OK Atual", use_column_width=True)
                except:
                    pass
            
            # Opções para Foto OK: Arquivo, Colar Print ou Apagar
            arquivo_ok = st.file_uploader("📁 Enviar Foto OK (Computador)", type=["jpg", "jpeg", "png"], key="up_ok")
            
            st.markdown("<small>Ou cole da área de transferência:</small>", unsafe_allow_html=True)
            paste_result_ok = paste_image_button(label="📋 Colar Foto OK (Ctrl+V)", key="paste_ok", background_color="#10B981")
            
            remover_ok = st.checkbox("🗑️ Remover/Apagar Foto OK atual", key="del_ok")

        with col_up2:
            st.markdown("### 🔴 FOTO NOK (Problema Encontrado)")
            tem_foto_nok = item_foto.get('foto_nok') and pd.notnull(item_foto['foto_nok']) and str(item_foto['foto_nok']).strip() != ""
            if tem_foto_nok:
                try:
                    st.image(str(item_foto['foto_nok']), caption="Foto NOK Atual", use_column_width=True)
                except:
                    pass
            
            # Opções para Foto NOK: Arquivo, Colar Print ou Apagar
            arquivo_nok = st.file_uploader("📁 Enviar Foto NOK (Computador)", type=["jpg", "jpeg", "png"], key="up_nok")
            
            st.markdown("<small>Ou cole da área de transferência:</small>", unsafe_allow_html=True)
            paste_result_nok = paste_image_button(label="📋 Colar Foto NOK (Ctrl+V)", key="paste_nok", background_color="#EF4444")
            
            remover_nok = st.checkbox("🗑️ Remover/Apagar Foto NOK atual", key="del_nok")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Salvar Alterações e Atualizar Fotos", type="primary", use_container_width=True):
            dados_atualizacao_fotos = {}
            
            # Processamento Foto OK
            if remover_ok:
                dados_atualizacao_fotos["foto_ok"] = None
            elif paste_result_ok.image_data is not None:
                dados_atualizacao_fotos["foto_ok"] = processar_e_converter_imagem(paste_result_ok.image_data, tamanho_alvo=(900, 600))
            elif arquivo_ok is not None:
                dados_atualizacao_fotos["foto_ok"] = processar_e_converter_imagem(arquivo_ok, tamanho_alvo=(900, 600))
                
            # Processamento Foto NOK
            if remover_nok:
                dados_atualizacao_fotos["foto_nok"] = None
            elif paste_result_nok.image_data is not None:
                dados_atualizacao_fotos["foto_nok"] = processar_e_converter_imagem(paste_result_nok.image_data, tamanho_alvo=(900, 600))
            elif arquivo_nok is not None:
                dados_atualizacao_fotos["foto_nok"] = processar_e_converter_imagem(arquivo_nok, tamanho_alvo=(900, 600))
                
            if dados_atualizacao_fotos:
                try:
                    supabase.table("alertas").update(dados_atualizacao_fotos).eq("id", aq_foto_escolhida).execute()
                    st.success("🎉 Fotos atualizadas com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar fotos no banco: {e}")
            else:
                st.warning("Nenhuma alteração foi realizada (nenhuma foto nova enviada, colada ou remoção marcada).")

# --- RESTANTE DAS PÁGINAS DO MENU ---
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
    else:
        st.info("Nenhum alerta encerrado no momento.")

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
