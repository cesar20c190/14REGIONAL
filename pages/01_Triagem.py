import streamlit as st
import database as db
from datetime import datetime
import pandas as pd
import re

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Triagem e Consulta")

st.title("📋 Triagem e Consulta de Demandas")
st.markdown("Utilize as abas abaixo para registar uma nova demanda ou para consultar e editar registos existentes.")
st.divider()

# --- FUNÇÕES AUXILIARES ---
def formatar_cpf(cpf):
    """Remove caracteres não numéricos do CPF."""
    return re.sub(r'[^0-9]', '', cpf)

# --- CRIAÇÃO DAS ABAS ---
tab_registrar, tab_consultar, tab_gerar_documentos = st.tabs(["Registrar Nova Demanda", "Consultar e Editar Demandas", "Gerar Documentos"])

# --- ABA DE REGISTRO ---
with tab_registrar:
    # --- DADOS E LISTAS ---
    LISTA_SERVIDORES = ["THAIS", "RAYSSA", "WELDER"]
    LISTA_DEFENSORES = [
        'Dra. Ana Carolina 1DP', 'Dr. Caio Cesar 2DP', 'Dr. Matheus Rocha 3DP',
        'Dr. Emerson Halsey 4DP', 'Dr. Matheus Bastos 5DP', 'Dra. Janaína Araújo 6DP',
        'Orientação'
    ]
    DEFENSORES_COM_DEMANDAS_RAPIDAS = ['Dra. Ana Carolina 1DP', 'Dra. Janaína Araújo 6DP']
    LISTA_DEMANDAS_RAPIDAS = [
        'Execução de Alimentos', 'Alimentos', 'Divórcio/RDU', 'Inventário',
        'Alvará', 'Curatela', 'Cível geral', 'Prazos geral'
    ]

    # --- INICIALIZAÇÃO DO ESTADO DA SESSÃO ---
    if 'pinned_values' not in st.session_state:
        st.session_state.pinned_values = {"servidor": None}
    if 'pin_status' not in st.session_state:
        st.session_state.pin_status = {"servidor": False}
    if 'awaiting_confirmation' not in st.session_state:
        st.session_state.awaiting_confirmation = False
    if 'form_data_to_save' not in st.session_state:
        st.session_state.form_data_to_save = {}
    if 'clear_form' not in st.session_state:
        st.session_state.clear_form = False
    if 'num_processos' not in st.session_state:
        st.session_state.num_processos = 1

    # --- LÓGICA DE LIMPEZA ---
    if st.session_state.get('clear_form', False):
        if not st.session_state.pin_status['servidor']:
            st.session_state.pinned_values['servidor'] = None
        st.session_state.nome_assistido = ""
        st.session_state.codigo = ""
        st.session_state.cpf = ""
        for i in range(st.session_state.get('num_processos_old', 1)):
            if f"processo_{i}" in st.session_state: st.session_state[f"processo_{i}"] = ""
        st.session_state.num_processos = 1
        st.session_state.clear_form = False

    # --- FUNÇÕES DE CALLBACK ---
    def update_pin_status(field):
        is_pinned = st.session_state[f'pin_{field}']
        st.session_state.pin_status[field] = is_pinned
        if is_pinned: st.session_state.pinned_values[field] = st.session_state[field]

    def update_pinned_value(field):
        if st.session_state.pin_status.get(field, False):
            st.session_state.pinned_values[field] = st.session_state[field]

    def adicionar_campo_processo():
        st.session_state.num_processos += 1

    def remover_campo_processo(index_para_remover):
        for i in range(index_para_remover, st.session_state.num_processos - 1):
            st.session_state[f"processo_{i}"] = st.session_state[f"processo_{i+1}"]
        del st.session_state[f"processo_{st.session_state.num_processos - 1}"]
        st.session_state.num_processos -= 1

    # --- INTERFACE DE REGISTRO ---
    defensor_selecionado = st.selectbox(
        "Selecione o Defensor(a)", options=LISTA_DEFENSORES, index=None,
        placeholder="Escolha um(a) defensor(a) para exibir o formulário", key="registro_defensor"
    )

    if defensor_selecionado:
        if st.session_state.get('awaiting_confirmation', False):
            st.subheader("Confirmar Registo")
            st.warning("Tem a certeza que deseja guardar esta demanda?")
            col1, col2, _ = st.columns([1, 1, 5])
            with col1:
                if st.button("✔️ Sim, guardar"):
                    data = st.session_state.form_data_to_save
                    try:
                        db.adicionar_demanda(**data)
                        st.toast("Demanda registada com sucesso!", icon="✅")
                        st.session_state.clear_form = True
                        st.session_state.awaiting_confirmation = False
                        st.session_state.form_data_to_save = {}
                        st.rerun()
                    except Exception as e: st.error(f"Ocorreu um erro ao salvar a demanda: {e}")
            with col2:
                if st.button("❌ Não, voltar"):
                    st.session_state.awaiting_confirmation = False
                    st.session_state.form_data_to_save = {}
                    st.rerun()
        else:
            st.subheader(f"Atendimento para: {defensor_selecionado}")

            col1, col2 = st.columns([3, 1])
            with col1:
                servidor_val = st.session_state.pinned_values['servidor']
                servidor_index = LISTA_SERVIDORES.index(servidor_val) if servidor_val in LISTA_SERVIDORES else None
                st.selectbox("Servidor", options=LISTA_SERVIDORES, index=servidor_index, placeholder="Selecione o servidor", key="servidor", on_change=update_pinned_value, args=("servidor",))
            with col2:
                st.write("")
                st.checkbox("Fixar", key="pin_servidor", value=st.session_state.pin_status['servidor'], on_change=update_pin_status, args=("servidor",))

            st.text_input("Nome do Assistido", placeholder="Nome completo do assistido", key="nome_assistido")
            st.text_input("CPF do Assistido", placeholder="000.000.000-00", key="cpf")
            st.text_input("Código de Referência", placeholder="Ex: 12345-67.2024.8.05.0001", key="codigo")
            
            st.markdown("**Número do Processo(s)**")
            for i in range(st.session_state.num_processos):
                col_input, col_button = st.columns([0.9, 0.1])
                with col_input: st.text_input(f"Processo {i + 1}", key=f"processo_{i}", label_visibility="collapsed")
                with col_button:
                    if i > 0: st.button("❌", key=f"remover_{i}", on_click=remover_campo_processo, args=(i,))
            st.button("➕ Adicionar processo", on_click=adicionar_campo_processo)
            
            st.divider()

            with st.form(f"form_submit", clear_on_submit=True):
                demanda = st.text_area("Descrição da Demanda", height=150, placeholder="Descreva a demanda...", key="demanda_desc")
                selecao_demanda_list = []
                if defensor_selecionado in DEFENSORES_COM_DEMANDAS_RAPIDAS:
                    with st.expander("Seleção Rápida de Demanda (Opcional)"):
                        cols_checkbox = st.columns(4)
                        for j, demanda_rapida in enumerate(LISTA_DEMANDAS_RAPIDAS):
                            if cols_checkbox[j % 4].checkbox(demanda_rapida, key=f"demanda_rapida_{j}"):
                                selecao_demanda_list.append(demanda_rapida)
                
                submitted = st.form_submit_button("✔️ Guardar", use_container_width=True, type="primary")

                if submitted:
                    processos = [st.session_state[f"processo_{i}"] for i in range(st.session_state.num_processos) if st.session_state[f"processo_{i}"].strip()]
                    st.session_state.num_processos_old = st.session_state.num_processos

                    if not st.session_state.servidor or not st.session_state.nome_assistido or not st.session_state.codigo or not demanda:
                        st.warning("Por favor, preencha todos os campos obrigatórios.")
                    else:
                        st.session_state.form_data_to_save = {
                            "servidor": st.session_state.servidor, "defensor": defensor_selecionado, "nome_assistido": st.session_state.nome_assistido,
                            "cpf": formatar_cpf(st.session_state.cpf), "codigo": st.session_state.codigo, "demanda": demanda, 
                            "selecao_demanda": ", ".join(selecao_demanda_list), "status": 'Pendente', "data": datetime.now().strftime("%d/%m/%Y"), 
                            "horario": datetime.now().strftime("%H:%M:%S"), "numero_processo": ";".join(processos)
                        }
                        st.session_state.awaiting_confirmation = True
                        st.rerun()

# --- ABA DE CONSULTA ---
with tab_consultar:
    st.subheader("🔍 Ferramenta de Busca e Edição")

    # --- Filtros ---
    col1, col2, col3 = st.columns(3)
    with col1:
        filtro_nome = st.text_input("Buscar por Nome do Assistido")
    with col2:
        filtro_cpf = st.text_input("Buscar por CPF")
    with col3:
        filtro_defensor = st.selectbox("Filtrar por Defensor", options=["Todos"] + LISTA_DEFENSORES, key="consulta_defensor")

    # --- Carregar e Filtrar Dados ---
    df_original = db.consultar_demandas()
    df_filtrado = df_original.copy()

    if filtro_nome:
        df_filtrado = df_filtrado[df_filtrado['nome_assistido'].str.contains(filtro_nome, case=False, na=False)]
    if filtro_cpf:
        df_filtrado = df_filtrado[df_filtrado['cpf'].str.contains(formatar_cpf(filtro_cpf), case=False, na=False)]
    if filtro_defensor != "Todos":
        df_filtrado = df_filtrado[df_filtrado['defensor'] == filtro_defensor]

    if df_filtrado.empty:
        st.info("Nenhum registo encontrado com os filtros aplicados.")
    else:
        # --- Editor de Dados ---
        st.info(f"{len(df_filtrado)} registo(s) encontrado(s). Pode editar os dados diretamente na tabela abaixo.")
        
        # Garante que o 'id' não seja editável
        df_filtrado.set_index('id', inplace=True)
        
        df_editado = st.data_editor(df_filtrado, use_container_width=True)

        # --- Lógica para Salvar Alterações ---
        if st.button("💾 Salvar Alterações", type="primary"):
            alteracoes_count = 0
            for demanda_id, linha in df_editado.iterrows():
                linha_original = df_filtrado.loc[demanda_id]
                if not linha.equals(linha_original):
                    novos_dados = linha.to_dict()
                    # Formata o CPF caso tenha sido alterado
                    if 'cpf' in novos_dados and novos_dados['cpf']:
                        novos_dados['cpf'] = formatar_cpf(novos_dados['cpf'])
                    db.atualizar_demanda(demanda_id, novos_dados)
                    alteracoes_count += 1
            
            if alteracoes_count > 0:
                st.toast(f"{alteracoes_count} registo(s) atualizado(s) com sucesso!", icon="🎉")
                st.rerun()
            else:
                st.toast("Nenhuma alteração detetada para salvar.", icon="ℹ️")

# --- ABA GERAR DOCUMENTOS ---
with tab_gerar_documentos:
    st.subheader("📄 Gerador de Documentos")
    
    tipo_documento = st.selectbox(
        "Selecione o tipo de documento que deseja gerar:",
        options=[
            "Declaração de comparecimento",
            "Declaração de residência",
            "Carta convite"
        ],
        index=None,
        placeholder="Selecione uma opção"
    )

    if tipo_documento:
        st.write(f"Você selecionou: **{tipo_documento}**")
        st.info("O próximo passo será criar os formulários e a lógica para gerar este documento.")

