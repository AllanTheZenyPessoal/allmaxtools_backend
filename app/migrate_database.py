"""
Script de migração para adicionar coluna id_address na tabela user (SQLite)
Execute este script para atualizar o banco de dados SQLite existente
"""

import sqlite3
import os
from pathlib import Path

def migrate_database():
    """Adiciona coluna id_address à tabela user se não existir"""
    
    # Caminho para o banco de dados
    db_path = Path(__file__).parent / 'prototype.db'
    
    if not db_path.exists():
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return False
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar estrutura atual da tabela user
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📋 Colunas atuais da tabela 'user': {column_names}")
        
        # Verificar se id_address já existe
        if 'id_address' in column_names:
            print("✅ Coluna 'id_address' já existe!")
            conn.close()
            return True
        
        # Adicionar coluna id_address
        print("🔧 Adicionando coluna 'id_address'...")
        cursor.execute("""
            ALTER TABLE user 
            ADD COLUMN id_address INTEGER NULL
        """)
        
        conn.commit()
        print("✅ Coluna 'id_address' adicionada com sucesso!")
        
        # Verificar novamente
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        print(f"📋 Colunas após migração: {column_names}")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao migrar banco de dados: {e}")
        return False

def recreate_user_table():
    """Recria a tabela user com todas as colunas corretas"""
    
    db_path = Path(__file__).parent / 'prototype.db'
    
    if not db_path.exists():
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Fazer backup dos dados existentes
        print("💾 Fazendo backup dos dados...")
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()
        
        # Obter estrutura da tabela antiga
        cursor.execute("PRAGMA table_info(user)")
        old_columns = [col[1] for col in cursor.fetchall()]
        print(f"📋 Colunas antigas: {old_columns}")
        
        # Criar tabela temporária
        print("🔧 Criando nova estrutura da tabela...")
        cursor.execute("""
            CREATE TABLE user_new (
                id_user INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                token TEXT UNIQUE,
                created_at DATETIME,
                updated_at DATETIME,
                id_address INTEGER,
                active BOOLEAN,
                FOREIGN KEY (id_address) REFERENCES address(id_address)
            )
        """)
        
        # Migrar dados
        if users:
            print(f"📦 Migrando {len(users)} usuários...")
            for user in users:
                # Mapear colunas antigas para novas
                placeholders = ['?' for _ in range(len(old_columns) + 1)]  # +1 para id_address
                
                # Inserir dados (sem id_address, será NULL)
                cursor.execute(f"""
                    INSERT INTO user_new 
                    (id_user, username, password, email, phone, token, created_at, updated_at, id_address, active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
                """, (
                    user[0],  # id_user
                    user[1],  # username
                    user[2],  # password
                    user[3],  # email
                    user[4] if len(user) > 4 else None,  # phone
                    user[5] if len(user) > 5 else None,  # token
                    user[6] if len(user) > 6 else None,  # created_at
                    user[7] if len(user) > 7 else None,  # updated_at
                    user[8] if len(user) > 8 else 1,     # active
                ))
        
        # Substituir tabela antiga
        print("🔄 Substituindo tabela antiga...")
        cursor.execute("DROP TABLE user")
        cursor.execute("ALTER TABLE user_new RENAME TO user")
        
        conn.commit()
        print("✅ Tabela 'user' recriada com sucesso!")
        
        # Verificar resultado
        cursor.execute("PRAGMA table_info(user)")
        new_columns = [col[1] for col in cursor.fetchall()]
        print(f"📋 Novas colunas: {new_columns}")
        
        cursor.execute("SELECT COUNT(*) FROM user")
        count = cursor.fetchone()[0]
        print(f"👥 Total de usuários: {count}")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao recriar tabela: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("🚀 Iniciando migração do banco de dados SQLite...")
    print("=" * 60)
    
    # Tentar adicionar coluna primeiro (mais seguro)
    print("\n📌 Método 1: Tentando adicionar coluna...")
    success = migrate_database()
    
    if not success:
        print("\n📌 Método 2: Recriando tabela...")
        response = input("Deseja recriar a tabela 'user'? (s/n): ")
        if response.lower() == 's':
            success = recreate_user_table()
    
    if success:
        print("\n🎉 Migração concluída com sucesso!")
    else:
        print("\n❌ Migração falhou. Verifique os erros acima.")
