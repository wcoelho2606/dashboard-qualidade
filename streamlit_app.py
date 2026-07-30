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
import streamlit.components.v1 as components
import zipfile
import xml.etree.ElementTree as ET

# Configuração da página executiva
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
        
        [data-testid="stSidebar"] {
            background-color: #0F172A;
            color: #ffffff;
            padding-top: 10px;
        }
        
        [data-testid="stSidebar"] .stRadio label, 
        [data-testid="stSidebar"] .stRadio p, 
        [data-testid="stSidebar"] .stRadio span {
            color: #FFFFFF !important;
            font-size: 14px !important;
            font-weight: 500 !important;
        }
        
        [data-testid="stSidebar"] hr {
            border-color: #334155;
        }
        
        .kpi-card {
            border-radius: 8px; padding: 15px; color: white; text-align: center;
            font-family: 'Segoe UI', sans-serif; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .kpi-title { font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; opacity: 0.9; }
        .kpi-value { font-size: 28px; font-weight: 800; margin-bottom: 2px; }
        .kpi-subtitle { font-size: 12px; opacity: 0.8; }
    </style>
""", unsafe_allow_html=True)

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

@st.cache_data(ttl=300)
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

# --- MENU LATERAL ---
with st.sidebar:
    st.markdown("<h3 style='color: white; margin-bottom: 0px;'>🛡️ GESTÃO DE ALERTAS</h3>", unsafe_allow_html=True)
    st.markdown("<small style='color: #94A3B8;'>Supabase + Streamlit Cloud</small>", unsafe_allow_html=True)
    st.markdown("---")
    
    opcoes_menu = [
        "🏠 Visão Geral", 
        "🔍 Alertas de Qualidade",
        "➕ Novo Alerta",
        "⚙️ Inserir Tratativa",
        "🔔 Alertas Abertos", 
        "⏰ Alertas Vencidos", 
        "✔️ Encerrados", 
        "📊 Indicadores", 
        "📈 Análises", 
        "📄 Relatórios"
    ]
    
    menu_opcao = st.radio(
        "Navegação",
        opcoes_menu,
        index=1,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("<small style='color: #64748B;'>Painel Sincronizado</small>", unsafe_allow_html=True)

if df_alertas.empty and menu_opcao != "➕ Novo Alerta":
    st.warning("Aguardando carregamento ou sem dados cadastrados no Supabase.")
    if menu_opcao != "➕ Novo Alerta":
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

# =======================================================
# ====== 2. TELA: ALERTAS DE QUALIDADE (RELATÓRIO OFICIAL)
# =======================================================
elif menu_opcao == "🔍 Alertas de Qualidade":
    st.title("🔍 RELATÓRIO OFICIAL DE ALERTAS DE QUALIDADE")
    st.markdown("Selecione o Alerta, informe o link corporativo, anexe o arquivo Excel correspondente e clique em salvar.")
    st.markdown("---")

    col_tabela, col_detalhes = st.columns([1.5, 2.5])

    with col_tabela:
        aq_selecionada_visao = None
        if not df_alertas.empty:
            df_display = df_alertas[["id", "produto", "lote", "defeito", "area", "responsavel", "prazo", "dias_restantes", "status"]].copy()
            df_display.columns = ["Nº AQ", "Produto", "Lote", "Defeito", "Área Responsável", "Responsável", "Prazo", "Dias Restantes", "Status"]
            styler = df_display.style.map(colorir_status, subset=["Status"]).map(colorir_dias, subset=["Dias Restantes"])
            st.dataframe(styler, use_container_width=True, hide_index=True)
            
            aq_selecionada_visao = st.selectbox("🔍 Selecione o Alerta:", df_alertas["id"].tolist())
            
            if 'last_aq_selected' not in st.session_state:
                st.session_state.last_aq_selected = aq_selecionada_visao

            if st.session_state.last_aq_selected != aq_selecionada_visao:
                st.session_state.last_aq_selected = aq_selecionada_visao
                st.session_state.excel_cliente = ""
                st.session_state.excel_area = ""
                st.session_state.excel_foto_ok = []
                st.session_state.excel_foto_nok = []
                st.session_state.excel_link = ""
                st.rerun()

            if 'excel_cliente' not in st.session_state:
                st.session_state.excel_cliente = ""
            if 'excel_area' not in st.session_state:
                st.session_state.excel_area = ""
            if 'excel_foto_ok' not in st.session_state:
                st.session_state.excel_foto_ok = []
            if 'excel_foto_nok' not in st.session_state:
                st.session_state.excel_foto_nok = []
            if 'excel_link' not in st.session_state:
                st.session_state.excel_link = ""
            
            st.markdown("---")
            st.markdown("🔗 **Vincular Link e Carregar Fotos do Alerta:**")
            
            link_input = st.text_input("Link do Arquivo / Alerta (SharePoint, Drive, etc):", value=st.session_state.excel_link, placeholder="https://...")
            if link_input:
                st.session_state.excel_link = link_input
            
            up_excel = st.file_uploader("Anexar arquivo Excel (.xlsx) do Alerta para ler as fotos", type=["xlsx"], key=f"up_excel_{aq_selecionada_visao}")
            
            if up_excel:
                try:
                    import openpyxl
                    
                    wb = openpyxl.load_workbook(up_excel, data_only=True)
                    if '2 Alerta da Qualidade' in wb.sheetnames:
                        sh_aq = wb['2 Alerta da Qualidade']
                        
                        st.session_state.excel_cliente = str(sh_aq['I5'].value or "").strip() if sh_aq['I5'].value else ""
                        st.session_state.excel_area = str(sh_aq['E5'].value or "").strip() if sh_aq['E5'].value else ""
                        
                        fotos_ok_list = []
                        fotos_nok_list = []
                        
                        up_bytes = BytesIO(up_excel.getvalue())
                        with zipfile.ZipFile(up_bytes, 'r') as z:
                            if 'xl/drawings/drawing2.xml' in z.namelist() and 'xl/drawings/_rels/drawing2.xml.rels' in z.namelist():
                                d2_xml = z.read('xl/drawings/drawing2.xml')
                                d2_rels = z.read('xl/drawings/_rels/drawing2.xml.rels')
                                
                                rels_root = ET.fromstring(d2_rels)
                                rid_map = {rel.attrib['Id']: rel.attrib['Target'].replace('../', 'xl/') for rel in rels_root.findall('{http://schemas.openxmlformats.org/package/2006/relationships}Relationship')}
                                
                                root_d2 = ET.fromstring(d2_xml)
                                ns = {'xdr': 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing', 'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
                                
                                for anchor in root_d2.findall('.//xdr:twoCellAnchor', ns) + root_d2.findall('.//xdr:oneCellAnchor', ns):
                                    from_tag = anchor.find('xdr:from', ns)
                                    if from_tag is not None:
                                        r_row = int(from_tag.find('xdr:row', ns).text) if from_tag.find('xdr:row', ns) is not None else 0
                                        r_col = int(from_tag.find('xdr:col', ns).text) if from_tag.find('xdr:col', ns) is not None else 0
                                        
                                        if r_row >= 7:
                                            blip = anchor.find('.//a:blip', ns)
                                            if blip is not None:
                                                embed = blip.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                                                if embed in rid_map:
                                                    img_path = rid_map[embed]
                                                    if img_path in z.namelist():
                                                        img_bytes_data = z.read(img_path)
                                                        if len(img_bytes_data) > 30000:
                                                            buffered = BytesIO()
                                                            Image.open(BytesIO(img_bytes_data)).save(buffered, format="PNG")
                                                            img_str = base64.b64encode(buffered.getvalue()).decode()
                                                            final_str = f"data:image/png;base64,{img_str}"
                                                            
                                                            if r_col < 8:
                                                                fotos_ok_list.append(final_str)
                                                            else:
                                                                fotos_nok_list.append(final_str)
                        
                        st.session_state.excel_foto_ok = fotos_ok_list
                        st.session_state.excel_foto_nok = fotos_nok_list
                        
                        st.success(f"Extracão concluída! Encontradas {len(fotos_ok_list)} foto(s) OK e {len(fotos_nok_list)} foto(s) NOK.")
                    else:
                        st.error("A aba '2 Alerta da Qualidade' não foi encontrada no arquivo.")
                except Exception as e:
                    st.error(f"Erro ao processar arquivo: {e}")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 Salvar Fotos e Dados na AQ Selecionada", type="primary", use_container_width=True):
                dados_update = {}
                if st.session_state.excel_cliente:
                    dados_update["cliente"] = st.session_state.excel_cliente
                if st.session_state.excel_area:
                    dados_update["area"] = st.session_state.excel_area
                if st.session_state.excel_foto_ok:
                    dados_update["foto_ok"] = str(st.session_state.excel_foto_ok) if len(st.session_state.excel_foto_ok) > 1 else st.session_state.excel_foto_ok[0]
                if st.session_state.excel_foto_nok:
                    dados_update["foto_nok"] = str(st.session_state.excel_foto_nok) if len(st.session_state.excel_foto_nok) > 1 else st.session_state.excel_foto_nok[0]
                    
                if dados_update:
                    try:
                        supabase.table("alertas").update(dados_update).eq("id", aq_selecionada_visao).execute()
                        st.cache_data.clear()
                        st.toast("Informações salvas no Supabase com sucesso!", icon="🚀")
                        st.rerun()
                    except Exception as db_err:
                        st.error(f"Erro ao salvar no banco de dados: {db_err}")
                else:
                    st.warning("Nenhum dado novo ou foto para salvar.")
        else:
            st.warning("Nenhum alerta cadastrado.")

    with col_detalhes:
        if aq_selecionada_visao:
            item = df_alertas[df_alertas['id'] == aq_selecionada_visao].iloc[0]
            status_cor = "#EF4444" if item['status'] == "VENCIDO" else ("#F59E0B" if item['status'] == "PRÓX. DO PRAZO" else "#10B981")
            
            cliente_exibir = st.session_state.get('excel_cliente', '') if st.session_state.get('excel_cliente') else item.get('cliente', '')
            area_exibir = st.session_state.get('excel_area', '') if st.session_state.get('excel_area') else item['area']
            
            link_db = st.session_state.get('excel_link', '')

            # Fotos OK
            f_ok = st.session_state.get('excel_foto_ok', [])
            if not f_ok and item.get('foto_ok'):
                val_db = item.get('foto_ok')
                f_ok = val_db.strip("[]").replace("'", "").split(", ") if str(val_db).startswith("[") else [val_db]
            
            if f_ok:
                img_ok_tag = "".join([f'<img src="{f}" style="width: 100%; height: 240px; object-fit: contain; background-color: #fff; margin-bottom: 5px;">' for f in f_ok if f])
            else:
                img_ok_tag = '<div style="text-align:center; padding:80px; color:#666;">Sem Foto OK</div>'

            # Fotos NOK
            f_nok = st.session_state.get('excel_foto_nok', [])
            if not f_nok and item.get('foto_nok'):
                val_db_nok = item.get('foto_nok')
                f_nok = val_db_nok.strip("[]").replace("'", "").split(", ") if str(val_db_nok).startswith("[") else [val_db_nok]
            
            if f_nok:
                img_nok_tag = "".join([f'<img src="{f}" style="width: 100%; height: 240px; object-fit: contain; background-color: #fff; margin-bottom: 5px;">' for f in f_nok if f])
            else:
                img_nok_tag = '<div style="text-align:center; padding:80px; color:#666;">Sem Foto NOK</div>'

            link_html = f'<div style="margin-top: 5px; font-size: 11px;"><b>Link do Arquivo:</b> <a href="{link_db}" target="_blank">{link_db}</a></div>' if link_db and pd.notnull(link_db) else ''

            html_relatorio = f"""<div style="border: 2px solid #1E3A8A; border-radius: 6px; background-color: white; font-family: 'Segoe UI', sans-serif; color: #000; box-shadow: 0 4px 6px rgba(0,0,0,0.1);"><div style="display: flex; border-bottom: 2px solid #1E3A8A; background-color: #f8fafc;"><div style="padding: 10px; border-right: 2px solid #1E3A8A; width: 20%; display: flex; align-items: center; justify-content: center; font-weight: bold; color: #1E3A8A; font-size: 14px; text-align: center;">ITW<br><span style="font-size: 9px; font-weight: normal;">Automotivo do Brasil</span></div><div style="padding: 10px; width: 60%; display: flex; align-items: center; justify-content: center;"><h2 style="color: #DC2626; margin: 0; font-size: 20px; font-weight: 800; letter-spacing: 1px; text-align: center;">ALERTA DA QUALIDADE</h2></div><div style="padding: 10px; border-left: 2px solid #1E3A8A; width: 20%; text-align: center; background-color: #f1f5f9;"><span style="font-size: 11px; font-weight: bold;">Nº :</span><br><span style="color: #2563EB; font-size: 16px; font-weight: bold;">{item['id']}</span></div></div><div style="display: flex; border-bottom: 2px solid #1E3A8A; font-size: 11px;"><div style="width: 35%; padding: 8px; border-right: 1px solid #cbd5e1;"><b>DESCRIÇÃO DO PROBLEMA:</b><br><span style="color: #2563EB; font-weight: 600; font-size: 12px;">{item['defeito']}</span></div><div style="width: 15%; padding: 8px; border-right: 1px solid #cbd5e1; text-align: center;"><b>Cliente:</b><br>{cliente_exibir}</div><div style="width: 15%; padding: 8px; border-right: 1px solid #cbd5e1; text-align: center;"><b>Área:</b><br>{area_exibir}</div><div style="width: 18%; padding: 8px; border-right: 1px solid #cbd5e1; text-align: center;"><b>Código da Peça:</b><br><span style="color: #2563EB; font-weight: bold;">{item['produto']}</span></div><div style="width: 17%; padding: 8px; text-align: center;"><b>Data / Prazo:</b><br>{item['prazo']}</div></div><div style="display: flex; border-bottom: 2px solid #1E3A8A;"><div style="width: 50%; border-right: 1px solid #1E3A8A;"><div style="background-color: #10B981; color: white; text-align: center; font-weight: bold; padding: 4px; font-size: 13px;">FOTO OK</div><div style="max-height: 280px; overflow-y: auto;">{img_ok_tag}</div></div><div style="width: 50%;"><div style="background-color: #EF4444; color: white; text-align: center; font-weight: bold; padding: 4px; font-size: 13px;">FOTO NOK</div><div style="max-height: 280px; overflow-y: auto;">{img_nok_tag}</div></div></div><div style="padding: 10px; background-color: #f8fafc; font-size: 11px;"><div style="display: flex; justify-content: space-between; align-items: center;"><div><b>Responsável:</b> {item['responsavel']}</div><div><b>Lote:</b> {item['lote']}</div><div><b>Status:</b> <span style="color: white; background-color: {status_cor}; padding: 2px 6px; border-radius: 3px; font-weight: bold;">{item['status']}</span></div></div>{link_html}</div></div>"""
            
            components.html(html_relatorio, height=560, scrolling=True)

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
                    st.cache_data.clear()
                    st.toast(f"Alerta {id_alerta} cadastrado com sucesso!", icon="🎉")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# =======================================================
# ====== 4. TELA: INSERIR TRATATIVA =====================
# =======================================================
elif menu_opcao == "⚙️ Inserir Tratativa":
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
                st.cache_data.clear()
                st.toast("Dados salvos com sucesso!", icon="✅")
                st.rerun()

# --- 5. TELA: ALERTAS ABERTOS ---
elif menu_opcao == "🔔 Alertas Abertos":
    st.title("🔔 ALERTAS EM ANDAMENTO")
    df_filtrado = df_alertas[df_alertas['status'] != 'ENCERRADO'].copy()
    if not df_filtrado.empty:
        df_display = df_filtrado[["id", "produto", "lote", "defeito", "area", "responsavel", "prazo", "dias_restantes", "status"]]
        st.dataframe(df_display.style.map(colorir_status, subset=["status"]).map(colorir_dias, subset=["dias_restantes"]), use_container_width=True, hide_index=True)

# --- 6. TELA: ALERTAS VENCIDOS ---
elif menu_opcao == "⏰ Alertas Vencidos":
    st.title("⏰ ALERTAS VENCIDOS E EM ATRASO")
    df_filtrado = df_alertas[df_alertas['status'] == 'VENCIDO'].copy()
    if not df_filtrado.empty:
        df_display = df_filtrado[["id", "produto", "lote", "defeito", "area", "responsavel", "prazo", "dias_restantes", "status"]]
        st.dataframe(df_display.style.map(colorir_status, subset=["status"]).map(colorir_dias, subset=["dias_restantes"]), use_container_width=True, hide_index=True)
    else:
        st.success("Excelente! Não existem alertas vencidos no momento.")

# --- 7. TELA: ENCERRADOS ---
elif menu_opcao == "✔️ Encerrados":
    st.title("✔️ HISTÓRICO DE ALERTAS ENCERRADOS")
    df_filtrado = df_alertas[df_alertas['status'] == 'ENCERRADO'].copy()
    if not df_filtrado.empty:
        df_display = df_filtrado[["id", "produto", "lote", "defeito", "area", "responsavel", "prazo", "dias_restantes", "status"]]
        st.dataframe(df_display.style.map(colorir_status, subset=["status"]), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum alerta encerrado no momento.")

# --- 8. TELA: INDICADORES ---
elif menu_opcao == "📊 Indicadores":
    st.title("📊 PAINEL GERAL DE INDICADORES (KPIs)")
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.plotly_chart(px.bar(df_alertas, x="area", color="status", title="Volume por Área", barmode="stack"), use_container_width=True)
    with col_g2:
        st.plotly_chart(px.histogram(df_alertas, x="status", title="Distribuição por Status", color="status"), use_container_width=True)

# =======================================================
# ====== 9. TELA: ANÁLISES (DIAGRAMA DE PARETO 80/20) ===
# =======================================================
elif menu_opcao == "📈 Análises":
    st.title("📈 ANÁLISE DE PARETO (PRINCÍPIO 80/20)")
    st.markdown("Identifique os principais tipos de defeitos que geram o maior impacto na operação de qualidade.")
    st.markdown("---")

    if not df_alertas.empty and "defeito" in df_alertas.columns:
        df_pareto = df_alertas["defeito"].value_counts().reset_index()
        df_pareto.columns = ["Defeito", "Quantidade"]
        df_pareto = df_pareto.sort_values(by="Quantidade", ascending=False)
        
        df_pareto["Acumulado (%)"] = df_pareto["Quantidade"].cumsum() / df_pareto["Quantidade"].sum() * 100

        fig_pareto = go.Figure()
        
        fig_pareto.add_trace(go.Bar(
            x=df_pareto["Defeito"], 
            y=df_pareto["Quantidade"], 
            name="Quantidade", 
            marker_color="#0E4687",
            yaxis="y1"
        ))
        
        fig_pareto.add_trace(go.Scatter(
            x=df_pareto["Defeito"], 
            y=df_pareto["Acumulado (%)"], 
            name="Acumulado (%)", 
            mode="lines+markers", 
            line=dict(color="#EF4444", width=3),
            yaxis="y2"
        ))

        fig_pareto.update_layout(
            title="<b>Diagrama de Pareto - Ocorrências por Defeito</b>",
            xaxis=dict(title="Tipo de Defeito"),
            yaxis=dict(title="Número de Ocorrências", side="left", showgrid=False),
            yaxis2=dict(title="Porcentagem Acumulada (%)", side="right", overlaying="y", range=[0, 105], showgrid=False),
            legend=dict(orientation="h", x=0.3, y=1.15),
            margin=dict(l=40, r=40, t=60, b=40),
            height=450,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        st.plotly_chart(fig_pareto, use_container_width=True)
        
        st.info("💡 **Dica de Gestão:** Os itens que se encontram antes da linha de 80% do acumulado representam as prioridades máximas para ações corretivas na engenharia e produção.")
    else:
        st.warning("Sem dados suficientes para gerar a análise de Pareto.")

# =======================================================
# ====== 10. TELA: RELATÓRIOS (CENTRAL DE AUDITORIA) ====
# =======================================================
elif menu_opcao == "📄 Relatórios":
    st.title("📄 CENTRAL DE RELATÓRIOS E AUDITORIA")
    st.markdown("Filtre, visualize e exporte o consolidado de todos os alertas de qualidade registrados.")
    st.markdown("---")

    if not df_alertas.empty:
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            status_filtro = st.multiselect("Filtrar por Status:", options=df_alertas["status"].unique().tolist(), default=df_alertas["status"].unique().tolist())
        with c_f2:
            area_filtro = st.multiselect("Filtrar por Área:", options=df_alertas["area"].unique().tolist(), default=df_alertas["area"].unique().tolist())

        df_relatorio = df_alertas[df_alertas["status"].isin(status_filtro) & df_alertas["area"].isin(area_filtro)].copy()

        st.markdown(f"**Total de registros filtrados:** `{len(df_relatorio)}`")
        
        st.dataframe(df_relatorio, use_container_width=True, hide_index=True)

        csv_data = df_relatorio.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Relatório em Formato CSV",
            data=csv_data,
            file_name=f"relatorio_alertas_qualidade_{date.today()}.csv",
            mime="text/csv",
            type="primary"
        )
    else:
        st.info("Nenhum dado disponível para relatórios.")
