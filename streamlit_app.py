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
    
    # --- PASSO 1: ANÁLISE ---
    st.markdown("### 1️⃣ Passo: Análise Técnica")
    
    with st.container(border=True):
        st.markdown(f"👤 **Responsável pela Análise:** `{item_aq['responsavel']}`")
        st.markdown("Esta etapa consiste na verificação técnica do lote apontado. Por favor, confirme se a análise foi realizada.")
        
        # Formulário para o Responsável confirmar
        with st.form("form_passo1"):
            analise_ok = st.checkbox("✅ Confirmo que a análise técnica foi realizada e os dados estão corretos.")
            obs_analise = st.text_area("Observações da Análise:", placeholder="Digite aqui o parecer técnico...")
            
            botao_salvar = st.form_submit_button("Confirmar Passo 1")
            
            if botao_salvar:
                if analise_ok:
                    # Aqui entra a lógica de salvar no Supabase (ex: atualizar campo 'etapa' para 'CONTENÇÃO')
                    st.success(f"Passo 1 finalizado pelo responsável {item_aq['responsavel']}!")
                    st.balloons()
                else:
                    st.warning("Você precisa marcar o checkbox para confirmar a análise.")
