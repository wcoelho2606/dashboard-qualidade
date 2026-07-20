import streamlit as st
from supabase import create_client, Client

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestão de Alertas de Qualidade", page_icon="🛡️", layout="wide")

# --- 2. CONEXÃO COM O SUPABASE ---
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "SUA_URL_SUPABASE")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "SUA_CHAVE_SUPABASE")

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_supabase()

st.title("🛡️ Gestão de Alertas de Qualidade")

# Busca os dados atuais do Supabase
resposta = supabase.table("alertas").select("*").execute()
dados_alertas = resposta.data

# --- 3. CRIAÇÃO DE ABAS (Onde o projeto antigo e o novo se unem) ---
aba_painel, aba_tratativa = st.tabs(["📊 Visão Geral & Tabela", "⚙️ Fluxo de Tratativas por Alerta"])

# --- ABA 1: O SEU PAINEL / TABELA ANTIGA ---
with aba_painel:
    st.subheader("Painel Geral de Alertas")
    if dados_alertas:
        # Exibe os dados que você já puxava do Supabase
        st.dataframe(dados_alertas, use_container_width=True)
    else:
        st.info("Nenhum alerta cadastrado na base de dados.")

# --- ABA 2: O NOVO FLUXO DE TRATATIVAS (Passo a Passo) ---
with aba_tratativa:
    st.subheader("Fluxo de Tratativas e Evolução de Etapas")
    
    if not dados_alertas:
        st.warning("Nenhum alerta cadastrado na base de dados.")
    else:
        # Seleciona o Alerta específico que deseja gerenciar
        ids_alertas = [item["id"] for item in dados_alertas]
        alerta_selecionado_id = st.selectbox("Selecione o ID do Alerta:", ids_alertas, key="select_fluxo")
        
        # Filtra os dados daquele alerta escolhido
        alerta_atual = next(item for item in dados_alertas if item["id"] == alerta_selecionado_id)
        
        st.divider()
        
        # Detalhes do Alerta em colunas
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write(f"**Produto:** {alerta_atual.get('produto')}")
            st.write(f"**Lote:** {alerta_atual.get('lote')}")
            st.write(f"**Defeito Detectado:** {alerta_atual.get('defeito')}")
            st.write(f"**Área Responsável:** {alerta_atual.get('area')}")
            st.write(f"**Responsável Atual:** {alerta_atual.get('responsavel')}")
            st.write(f"**Prazo:** {alerta_atual.get('prazo')} | **Dias Restantes:** {alerta_atual.get('dias_restantes')}")
            
        with col2:
            st.info(f"**Status Atual:** {alerta_atual.get('status')}")
            etapa_atual = alerta_atual.get("etapa_atual", 1)
            if etapa_atual is None:
                etapa_atual = 1
            st.metric(label="Fase do Fluxo", value=f"Etapa {etapa_atual} de 6")

        st.markdown("---")
        
        # Renderização visual das 6 Etapas (Timeline em colunas)
        st.markdown("### 🔄 Andamento do Fluxo")
        etapas_nomes = [
            "1. Alerta Emitido",
            "2. Em Análise",
            "3. Ação Definida",
            "4. Em Implementação",
            "5. Aguardando Validação",
            "6. Encerrado"
        ]
        
        cols_fluxo = st.columns(6)
        for i, nome_etapa in enumerate(etapas_nomes, start=1):
            with cols_fluxo[i-1]:
                if i < etapa_atual:
                    st.success(f"✅\n\n**{nome_etapa}**")
                elif i == etapa_atual:
                    st.warning(f"⏳\n\n**{nome_etapa}**\n*(Atual)*")
                else:
                    st.markdown(f"⚪\n\n_{nome_etapa}_")

        st.markdown("---")

        # Botões de Ação para Atualizar o Banco em Tempo Real
        col_acao1, col_acao2 = st.columns(2)
        
        with col_acao1:
            if etapa_atual < 6:
                if st.button("🚀 Avançar para Próxima Etapa", use_container_width=True):
                    nova_etapa = etapa_atual + 1
                    novo_status = "ENCERRADO" if nova_etapa == 6 else alerta_atual.get('status')
                    
                    # Atualiza diretamente no Supabase
                    supabase.table("alertas").update({
                        "etapa_atual": nova_etapa,
                        "status": novo_status
                    }).eq("id", alerta_selecionado_id).execute()
                    
                    st.success("Alerta avançado com sucesso!")
                    st.rerun()
            else:
                st.success("🎉 Este alerta já concluiu o fluxo e está Encerrado!")

        with col_acao2:
            nova_observacao = st.text_area("Observações / Ação de Contenção:", value=alerta_atual.get("observacoes") or "")
            if st.button("Salvar Observações", use_container_width=True):
                supabase.table("alertas").update({
                    "observacoes": nova_observacao
                }).eq("id", alerta_selecionado_id).execute()
                st.toast("Salvo com sucesso!")
                st.rerun()
