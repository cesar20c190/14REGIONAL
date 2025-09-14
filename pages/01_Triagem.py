import streamlit as st
import database as db
from datetime import datetime
import pandas as pd
import re
from docx import Document
from io import BytesIO
import locale
import os # Importa o módulo 'os' para lidar com caminhos de ficheiros

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Triagem e Consulta")

st.title("📋 Triagem e Consulta de Demandas")
st.markdown("Utilize as abas abaixo para registar uma nova demanda ou para consultar e editar registos existentes.")
st.divider()

# --- FUNÇÕES AUXILIARES ---
def formatar_cpf(cpf):
    """Remove caracteres não numéricos do CPF."""
    if cpf:
        return re.sub(r'[^0-9]', '', cpf)
    return ""

def formatar_cpf_para_exibicao(cpf_numerico):
    """Formata um CPF numérico para o formato 000.000.000-00."""
    if not cpf_numerico or len(str(cpf_numerico)) != 11:
        return "" # Retorna uma string vazia se o CPF for None, vazio ou inválido
    
    cpf_str = str(cpf_numerico)
    return f"{cpf_str[:3]}.{cpf_str[3:6]}.{cpf_str[6:9]}-{cpf_str[9:]}"

def formatar_data_para_extenso(dt):
    """Formata uma data para o formato 'dd de Mês de yyyy' em português, evitando problemas de 'locale'."""
    meses = {
        1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
        5: "maio", 6: "junho", 7: "julho", 8: "agosto",
        9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
    }
    return f"{dt.day} de {meses[dt.month]} de {dt.year}"

# --- CRIAÇÃO DAS ABAS ---
tab_registrar, tab_consultar = st.tabs(["Registrar Nova Demanda", "Consultar e Editar Demandas"])

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
    if 'demanda_desc' not in st.session_state:
        st.session_state.demanda_desc = ""

    # --- LÓGICA DE LIMPEZA ---
    if st.session_state.get('clear_form', False):
        if not st.session_state.pin_status['servidor']:
            st.session_state.pinned_values['servidor'] = None
        st.session_state.nome_assistido = ""
        st.session_state.codigo = ""
        st.session_state.cpf = ""
        st.session_state.demanda_desc = ""
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
    
    def buscar_nome_por_cpf():
        cpf_input = st.session_state.get('cpf', '')
        cpf_formatado = formatar_cpf(cpf_input)
        if len(cpf_formatado) == 11:
            df = db.consultar_demandas()
            if not df.empty and 'cpf' in df.columns:
                assistido = df[df['cpf'] == cpf_formatado]
                if not assistido.empty:
                    nome_encontrado = assistido['nome_assistido'].iloc[0]
                    st.session_state.nome_assistido = nome_encontrado

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

            col_nome, col_cpf, col_cod = st.columns([2,1,1])
            with col_nome:
                st.text_input("Nome do Assistido", placeholder="Nome completo do assistido", key="nome_assistido")
            with col_cpf:
                st.text_input("CPF do Assistido", placeholder="000.000.000-00", key="cpf", on_change=buscar_nome_por_cpf, help="Digite o CPF e tecle Enter para buscar o nome.")
            with col_cod:
                st.text_input("Código de Referência", placeholder="Ex: 12345-67", key="codigo")
            
            st.markdown("**Número do Processo(s)**")
            for i in range(st.session_state.num_processos):
                col_input, col_button = st.columns([0.9, 0.1])
                with col_input: st.text_input(f"Processo {i + 1}", key=f"processo_{i}", label_visibility="collapsed")
                with col_button:
                    if i > 0: st.button("❌", key=f"remover_{i}", on_click=remover_campo_processo, args=(i,))
            st.button("➕ Adicionar processo", on_click=adicionar_campo_processo)
            
            st.divider()

            with st.form(f"form_submit", clear_on_submit=True):
                selecao_demanda_list = []
                if defensor_selecionado in DEFENSORES_COM_DEMANDAS_RAPIDAS:
                    selecao_demanda_list = st.multiselect(
                        "Seleção Rápida de Demanda (Opcional)",
                        options=LISTA_DEMANDAS_RAPIDAS,
                        placeholder="Clique para selecionar uma ou mais demandas"
                    )

                demanda = st.text_area("Descrição da Demanda", height=150, placeholder="Descreva a demanda...", key="demanda_desc")
                
                submitted = st.form_submit_button("✔️ Guardar", use_container_width=True, type="primary")

                if submitted:
                    processos = [st.session_state[f"processo_{i}"] for i in range(st.session_state.num_processos) if st.session_state[f"processo_{i}"].strip()]
                    st.session_state.num_processos_old = st.session_state.num_processos

                    if not st.session_state.servidor or not st.session_state.nome_assistido or not st.session_state.codigo or not demanda:
                        st.warning("Por favor, preencha todos os campos obrigatórios (Servidor, Nome, Código e Demanda).")
                    else:
                        st.session_state.form_data_to_save = {
                            "servidor": st.session_state.servidor, "defensor": defensor_selecionado, "nome_assistido": st.session_state.nome_assistido,
                            "cpf": formatar_cpf(st.session_state.cpf), "codigo": st.session_state.codigo, "demanda": demanda, 
                            "selecao_demanda": "; ".join(selecao_demanda_list), "status": 'Pendente', "data": datetime.now().strftime("%d/%m/%Y"), 
                            "horario": datetime.now().strftime("%H:%M:%S"), "numero_processo": ";".join(processos),
                            "documento_gerado": ""
                        }
                        st.session_state.awaiting_confirmation = True
                        st.rerun()

# --- ABA DE CONSULTA ---
with tab_consultar:
    st.subheader("🔍 Ferramenta de Busca e Edição")

    if 'doc_generator_open_for' not in st.session_state:
        st.session_state.doc_generator_open_for = None

    df_original = db.consultar_demandas()

    if st.session_state.doc_generator_open_for is not None:
        id_demanda = st.session_state.doc_generator_open_for
        demanda_selecionada = df_original[df_original['id'] == id_demanda].iloc[0]

        st.subheader(f"📄 Gerar Documento para: {demanda_selecionada['nome_assistido']}")
        st.caption(f"Registo ID: {id_demanda}")

        if st.button("⬅️ Voltar à Consulta"):
            st.session_state.doc_generator_open_for = None
            st.rerun()

        st.markdown("---")
        tipo_documento = st.selectbox(
            "Tipo de documento:",
            options=["Declaração de comparecimento", "Solicitação de Certidão (CRC)", "Declaração de residência", "Carta convite"],
            index=None, placeholder="Selecione uma opção", key=f"doc_type_{id_demanda}"
        )

        if tipo_documento == "Declaração de comparecimento":
            st.markdown("---")
            st.warning("Atenção: O seu ficheiro modelo .docx deve conter as tags <<horadeinicio>> e <<horafim>>.")
            
            defensor_assinatura = st.text_input("Nome do Defensor(a) para Assinatura", value=demanda_selecionada['defensor'], key=f"defensor_assinatura_{id_demanda}")
            
            col_hora1, col_hora2 = st.columns(2)
            with col_hora1:
                hora_inicio = st.time_input("Hora de início do atendimento", key=f"hinicio_{id_demanda}")
            with col_hora2:
                hora_fim = st.time_input("Hora de fim do atendimento", key=f"hfim_{id_demanda}")

            if st.button("Gerar e Salvar Documento", key=f"gerar_dec_comp_{id_demanda}", type="primary"):
                if not hora_inicio or not hora_fim or len(defensor_assinatura.strip()) < 3:
                    st.warning("Por favor, preencha todos os campos (horas e nome do defensor com pelo menos 3 caracteres).")
                else:
                    try:
                        caminho_modelo = os.path.join('modelos', 'ADM - DECLARAÇÃO DE COMPARECIMENTO.docx')
                        doc = Document(caminho_modelo)
                        data_extenso = formatar_data_para_extenso(datetime.now()) # <-- MUDANÇA AQUI
                        qualificacao_auto = f"CPF/MF: {formatar_cpf_para_exibicao(demanda_selecionada.get('cpf'))}"

                        substituicoes = {
                            "<<NOME PARA ATESTADO DE COMPARECIMENTO>>": demanda_selecionada['nome_assistido'],
                            "<<qualificação>>": qualificacao_auto,
                            "<<dataatendimento>>": data_extenso,
                            "<<COMARCA>>": "Teixeira de Freitas",
                            "<<nomedefensor>>": defensor_assinatura,
                            "<<horadeinicio>>": hora_inicio.strftime("%H:%M"),
                            "<<horafim>>": hora_fim.strftime("%H:%M")
                        }

                        for p in doc.paragraphs:
                            texto_paragrafo = p.text
                            for key, value in substituicoes.items():
                                texto_paragrafo = texto_paragrafo.replace(key, str(value))
                            if p.text != texto_paragrafo:
                                p.clear()
                                p.add_run(texto_paragrafo)

                        bio = BytesIO()
                        doc.save(bio)
                        
                        st.download_button(
                            label="✔️ Documento Pronto! Clique para Descarregar.",
                            data=bio.getvalue(),
                            file_name=f"Declaracao_Comparecimento_{demanda_selecionada['nome_assistido']}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True
                        )
                        
                        db.atualizar_demanda(id_demanda, {"documento_gerado": tipo_documento})
                        st.toast("Documento gerado e registo atualizado!", icon="📄")

                    except FileNotFoundError:
                        st.error("Erro: O ficheiro modelo 'ADM - DECLARAÇÃO DE COMPARECIMENTO.docx' não foi encontrado.")
                    except Exception as e:
                        st.error(f"Ocorreu um erro ao gerar o documento: {e}")
        
        elif tipo_documento == "Solicitação de Certidão (CRC)":
            st.markdown("---")
            st.info(f"""
            **Assistido(a):** {demanda_selecionada['nome_assistido']}  
            **CPF:** {formatar_cpf_para_exibicao(demanda_selecionada.get('cpf'))}
            """)

            tipo_certidao = st.selectbox("Tipo de Certidão", options=["Nascimento", "Casamento", "Óbito"], key=f"tipo_certidao_{id_demanda}")
            
            dados_certidao = {}
            if tipo_certidao == "Nascimento":
                dados_certidao['crc_nome_registrado'] = st.text_input("Nome Completo do Registrado(a)", value=demanda_selecionada['nome_assistido'], key=f"crc_nome_nasc_{id_demanda}")
                dados_certidao['crc_data_nascimento'] = st.date_input("Data de Nascimento", key=f"crc_data_nasc_{id_demanda}", format="DD/MM/YYYY", value=None)
                dados_certidao['crc_local_nascimento'] = st.text_input("Cidade de Nascimento", key=f"crc_local_nasc_{id_demanda}")
                dados_certidao['crc_nome_pai'] = st.text_input("Nome do Pai", key=f"crc_pai_{id_demanda}")
                dados_certidao['crc_nome_mae'] = st.text_input("Nome da Mãe", key=f"crc_mae_{id_demanda}")

            elif tipo_certidao == "Casamento":
                dados_certidao['crc_nome_registrado'] = st.text_input("Nome do(a) Cônjuge 1", value=demanda_selecionada['nome_assistido'], key=f"crc_nome_cas1_{id_demanda}")
                dados_certidao['crc_nome_conjuge2'] = st.text_input("Nome do(a) Cônjuge 2", key=f"crc_nome_cas2_{id_demanda}")
                dados_certidao['crc_data_casamento'] = st.date_input("Data do Casamento", key=f"crc_data_cas_{id_demanda}", format="DD/MM/YYYY", value=None)
                dados_certidao['crc_local_casamento'] = st.text_input("Cidade do Casamento", key=f"crc_local_cas_{id_demanda}")

            elif tipo_certidao == "Óbito":
                dados_certidao['crc_nome_registrado'] = st.text_input("Nome Completo do(a) Falecido(a)", value=demanda_selecionada['nome_assistido'], key=f"crc_nome_obito_{id_demanda}")
                dados_certidao['crc_data_obito'] = st.date_input("Data do Óbito", key=f"crc_data_obito_{id_demanda}", format="DD/MM/YYYY", value=None)
                dados_certidao['crc_local_obito'] = st.text_input("Cidade do Óbito", key=f"crc_local_obito_{id_demanda}")
                dados_certidao['crc_filiacao_obito'] = st.text_input("Filiação do(a) Falecido(a)", key=f"crc_filiacao_obito_{id_demanda}")

            dados_certidao['crc_cartorio'] = st.text_input("Cartório de Registro (se souber)", key=f"crc_cartorio_{id_demanda}")
            dados_certidao['crc_finalidade'] = st.text_input("Finalidade da Certidão", value="Para fins de prova em processo judicial", key=f"crc_finalidade_{id_demanda}")
            
            if st.button("✔️ Enviar Solicitação para Coordenação", key=f"enviar_crc_{id_demanda}", type="primary", use_container_width=True):
                try:
                    dados_para_salvar = {
                        "documento_gerado": f"Solicitação de {tipo_certidao} Enviada",
                        "crc_tipo_certidao": tipo_certidao,
                        "crc_status": "Pendente"
                    }

                    for key, value in dados_certidao.items():
                        if isinstance(value, datetime):
                            dados_para_salvar[key] = value.strftime('%d/%m/%Y')
                        else:
                            dados_para_salvar[key] = value
                    
                    db.atualizar_demanda(id_demanda, dados_para_salvar)
                    st.toast("Solicitação enviada para a coordenação!", icon="🚀")
                    
                    st.session_state.doc_generator_open_for = None
                    st.rerun()

                except Exception as e:
                    st.error(f"Ocorreu um erro ao enviar a solicitação: {e}")

    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            filtro_nome = st.text_input("Buscar por Nome do Assistido")
        with col2:
            filtro_cpf = st.text_input("Buscar por CPF")
        with col3:
            filtro_defensor = st.selectbox("Filtrar por Defensor", options=["Todos"] + LISTA_DEFENSORES, key="consulta_defensor")

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
            st.info(f"{len(df_filtrado)} registo(s) encontrado(s). Clique num registo para ver os detalhes, editar ou gerar documentos.")
            
            for index, row in df_filtrado.iterrows():
                id_demanda = row['id']
                status_color = "green" if row['status'] == 'Pendente' else 'orange'
                doc_icon = "📄" if row.get('documento_gerado') else ""
                
                with st.expander(f"{doc_icon} **{row['nome_assistido']}** |  Data: {row['data']}  |  Status: :{status_color}[{row['status']}]"):
                    
                    with st.form(key=f"form_edit_{id_demanda}"):
                        st.subheader(f"Editando Registo ID: {id_demanda}")
                        dados_editados = {}
                        
                        c1, c2 = st.columns(2)
                        with c1:
                            dados_editados['nome_assistido'] = st.text_input("Nome", value=row['nome_assistido'], key=f"nome_{id_demanda}")
                            dados_editados['cpf'] = st.text_input("CPF", value=row.get('cpf', ''), key=f"cpf_{id_demanda}")
                            dados_editados['servidor'] = st.selectbox("Servidor", options=LISTA_SERVIDORES, index=LISTA_SERVIDORES.index(row['servidor']) if row['servidor'] in LISTA_SERVIDORES else 0, key=f"servidor_{id_demanda}")
                        with c2:
                            dados_editados['codigo'] = st.text_input("Código de Referência", value=row['codigo'], key=f"codigo_{id_demanda}")
                            dados_editados['defensor'] = st.selectbox("Defensor", options=LISTA_DEFENSORES, index=LISTA_DEFENSORES.index(row['defensor']) if row['defensor'] in LISTA_DEFENSORES else 0, key=f"defensor_{id_demanda}")
                            dados_editados['status'] = st.selectbox("Status", options=['Pendente', 'Lido', 'Resolvido', 'Arquivado'], index=['Pendente', 'Lido', 'Resolvido', 'Arquivado'].index(row['status']) if row['status'] in ['Pendente', 'Lido', 'Resolvido', 'Arquivado'] else 0, key=f"status_{id_demanda}")

                        dados_editados['numero_processo'] = st.text_input("Nº Processo", value=row.get('numero_processo', ''), help="Separar múltiplos com (;)", key=f"processo_{id_demanda}")
                        dados_editados['demanda'] = st.text_area("Descrição da Demanda", value=row['demanda'], height=150, key=f"demanda_{id_demanda}")
                        dados_editados['documento_gerado'] = st.text_input("Documento Gerado", value=row.get('documento_gerado', ''), key=f"doc_gerado_{id_demanda}")

                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                           if st.form_submit_button("💾 Salvar Alterações", type="primary", use_container_width=True):
                                try:
                                    dados_editados['cpf'] = formatar_cpf(dados_editados['cpf'])
                                    db.atualizar_demanda(id_demanda, dados_editados)
                                    st.toast(f"Registo de {dados_editados['nome_assistido']} atualizado!", icon="🎉")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao atualizar o registo: {e}")
                        with col_btn2:
                            if st.form_submit_button("📄 Gerar/Enviar Solicitação", use_container_width=True):
                                st.session_state.doc_generator_open_for = id_demanda
                                st.rerun()

