import sqlite3
import pandas as pd
from datetime import datetime

# Nome do ficheiro da base de dados
DB_NAME = "demandas.db"

def inicializar_banco():
    """
    Cria a base de dados e as tabelas 'demandas' e 'analises_hipossuficiencia' se não existirem.
    Adiciona novas colunas à tabela 'demandas' se necessário para manter a compatibilidade.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # --- Tabela de Demandas ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS demandas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            servidor TEXT NOT NULL,
            defensor TEXT NOT NULL,
            nome_assistido TEXT NOT NULL,
            cpf TEXT,
            codigo TEXT NOT NULL,
            demanda TEXT NOT NULL,
            selecao_demanda TEXT,
            status TEXT NOT NULL,
            data TEXT NOT NULL,
            horario TEXT NOT NULL,
            numero_processo TEXT,
            documento_gerado TEXT 
        )
    """)
    
    cursor.execute("PRAGMA table_info(demandas)")
    columns = [info[1] for info in cursor.fetchall()]
    
    colunas_a_adicionar = {
        'numero_processo': 'TEXT', 'cpf': 'TEXT', 'documento_gerado': 'TEXT',
        'crc_tipo_certidao': 'TEXT', 'crc_nome_registrado': 'TEXT',
        'crc_data_nascimento': 'TEXT', 'crc_local_nascimento': 'TEXT',
        'crc_nome_pai': 'TEXT', 'crc_nome_mae': 'TEXT',
        'crc_nome_conjuge2': 'TEXT', 'crc_data_casamento': 'TEXT',
        'crc_local_casamento': 'TEXT', 'crc_data_obito': 'TEXT',
        'crc_local_obito': 'TEXT', 'crc_filiacao_obito': 'TEXT',
        'crc_cartorio': 'TEXT', 'crc_finalidade': 'TEXT',
        'crc_status': 'TEXT'
    }

    for col, tipo in colunas_a_adicionar.items():
        if col not in columns:
            cursor.execute(f"ALTER TABLE demandas ADD COLUMN {col} {tipo}")

    # --- NOVA: Tabela de Análises de Hipossuficiência ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analises_hipossuficiencia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_pessoa TEXT,
            documento TEXT NOT NULL,
            vulnerabilidades TEXT,
            detalhes TEXT,
            resultado TEXT,
            motivo TEXT,
            data_analise TEXT
        )
    """)

    conn.commit()
    conn.close()

def adicionar_demanda(**kwargs):
    """
    Adiciona um novo registo de demanda à base de dados usando argumentos nomeados.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cols = ', '.join(kwargs.keys())
    placeholders = ', '.join(['?'] * len(kwargs))
    query = f"INSERT INTO demandas ({cols}) VALUES ({placeholders})"
    
    cursor.execute(query, tuple(kwargs.values()))
    
    conn.commit()
    conn.close()

def consultar_demandas():
    """
    Consulta todas as demandas da base de dados e retorna como um DataFrame do Pandas.
    """
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM demandas ORDER BY id DESC", conn)
    conn.close()
    return df

def atualizar_demanda(demanda_id, novos_dados):
    """
    Atualiza um registo existente na base de dados.
    'novos_dados' é um dicionário onde a chave é o nome da coluna e o valor é o novo dado.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    set_clause = ', '.join([f"{key} = ?" for key in novos_dados.keys()])
    values = list(novos_dados.values()) + [demanda_id]
    
    query = f"UPDATE demandas SET {set_clause} WHERE id = ?"
    
    cursor.execute(query, tuple(values))
    
    conn.commit()
    conn.close()

def deletar_demanda(demanda_id):
    """
    Deleta um registo da base de dados com base no seu ID.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    query = "DELETE FROM demandas WHERE id = ?"
    cursor.execute(query, (demanda_id,))
    conn.commit()
    conn.close()

# --- NOVAS FUNÇÕES PARA ANÁLISE ---

def adicionar_analise(**kwargs):
    """
    Adiciona um novo registo de análise de hipossuficiência à base de dados.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cols = ', '.join(kwargs.keys())
    placeholders = ', '.join(['?'] * len(kwargs))
    query = f"INSERT INTO analises_hipossuficiencia ({cols}) VALUES ({placeholders})"
    
    cursor.execute(query, tuple(kwargs.values()))
    
    conn.commit()
    conn.close()

def consultar_analises():
    """
    Consulta todas as análises de hipossuficiência e retorna como um DataFrame do Pandas.
    """
    conn = sqlite3.connect(DB_NAME)
    try:
        df = pd.read_sql_query("SELECT * FROM analises_hipossuficiencia ORDER BY id DESC", conn)
    except pd.io.sql.DatabaseError:
        # Retorna um DataFrame vazio se a tabela ainda não tiver sido criada ou estiver vazia
        df = pd.DataFrame()
    conn.close()
    return df

# --- INICIALIZAÇÃO ---
# Garante que as tabelas e colunas existam ao iniciar a aplicação
inicializar_banco()
