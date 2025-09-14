import sqlite3
import pandas as pd
from datetime import datetime

# Nome do ficheiro da base de dados
DB_NAME = "demandas.db"

def inicializar_banco():
    """
    Cria a base de dados e a tabela 'demandas' se eles não existirem.
    Adiciona novas colunas se necessário para manter a compatibilidade.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Cria a tabela com as colunas necessárias
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
            numero_processo TEXT 
        )
    """)
    
    # --- Verificações de colunas para compatibilidade com versões antigas ---
    cursor.execute("PRAGMA table_info(demandas)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if 'numero_processo' not in columns:
        cursor.execute("ALTER TABLE demandas ADD COLUMN numero_processo TEXT")
    if 'cpf' not in columns:
        cursor.execute("ALTER TABLE demandas ADD COLUMN cpf TEXT")

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

# --- INICIALIZAÇÃO ---
inicializar_banco()

