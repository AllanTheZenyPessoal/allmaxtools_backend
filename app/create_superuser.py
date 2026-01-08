#!/usr/bin/env python3
"""
Script para criar superuser no banco SQLite
Execute este script para criar o usuário superadmin automaticamente
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime
from passlib.context import CryptContext

# Configuração para hash de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_superuser():
    """Cria o superuser no banco SQLite"""
    
    # Caminho para o banco de dados
    db_path = Path(__file__).parent / 'prototype.db'
    
    if not db_path.exists():
        print(f"❌ Banco de dados não encontrado: {db_path}")
        print(f"💡 O banco será criado automaticamente quando você iniciar a aplicação.")
        return False
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar estrutura da tabela user
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📋 Colunas da tabela 'user': {column_names}")
        
        # Dados do superuser - você pode passar email e senha customizados
        import sys
        if len(sys.argv) > 2:
            email = sys.argv[1]
            plain_password = sys.argv[2]
            username = email.split('@')[0]
        else:
            email = 'superuser@prototype.com'
            username = 'superuser'
            plain_password = '123123123'
        phone = '+55 11 99999-9999'
        
        # Hash da senha antes de armazenar
        password = pwd_context.hash(plain_password)
        
        # Verificar se o superuser já existe
        cursor.execute("SELECT id_user, email FROM user WHERE email = ?", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            print(f"⚠️  Superuser já existe com ID: {existing_user[0]}")
            response = input("Deseja atualizar a senha? (s/n): ")
            if response.lower() == 's':
                cursor.execute("""
                    UPDATE user 
                    SET password = ?, 
                        username = ?,
                        phone = ?,
                        active = 1,
                        updated_at = ?
                    WHERE email = ?
                """, (password, username, phone, datetime.now(), email))
                conn.commit()
                print("✅ Superuser atualizado com sucesso!")
            else:
                print("ℹ️  Nenhuma alteração realizada.")
            conn.close()
            return True
        
        # Criar novo superuser
        print("🔧 Criando superuser...")
        
        # Montar SQL baseado nas colunas disponíveis
        if 'id_address' in column_names:
            # Tabela tem coluna id_address
            cursor.execute("""
                INSERT INTO user (username, password, email, phone, token, active, id_address, created_at, updated_at)
                VALUES (?, ?, ?, ?, NULL, 1, NULL, ?, ?)
            """, (username, password, email, phone, datetime.now(), datetime.now()))
        else:
            # Tabela sem coluna id_address (versão antiga)
            cursor.execute("""
                INSERT INTO user (username, password, email, phone, token, active, created_at, updated_at)
                VALUES (?, ?, ?, ?, NULL, 1, ?, ?)
            """, (username, password, email, phone, datetime.now(), datetime.now()))
        
        conn.commit()
        
        # Verificar criação
        cursor.execute("""
            SELECT id_user, username, email, phone, active, created_at
            FROM user
            WHERE email = ?
        """, (email,))
        
        user = cursor.fetchone()
        
        if user:
            print("✅ Superuser criado com sucesso!")
            print(f"📋 Detalhes:")
            print(f"   ID: {user[0]}")
            print(f"   Username: {user[1]}")
            print(f"   Email: {user[2]}")
            print(f"   Phone: {user[3]}")
            print(f"   Active: {user[4]}")
            print(f"   Created: {user[5]}")
            print(f"\n🔑 Credenciais:")
            print(f"   Email: {email}")
            print(f"   Senha: {plain_password}")
            print(f"\n🎯 Para obter token JWT:")
            print(f"   POST http://localhost:8000/token_generate/")
            print(f"   Body: username={email}&password={plain_password}")
        else:
            print("❌ Erro ao verificar criação do superuser")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao criar superuser: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

def list_users():
    """Lista todos os usuários no banco"""
    
    db_path = Path(__file__).parent / 'prototype.db'
    
    if not db_path.exists():
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id_user, username, email, active FROM user")
        users = cursor.fetchall()
        
        if users:
            print(f"\n👥 Usuários cadastrados ({len(users)}):")
            print("-" * 80)
            for user in users:
                status = "✅ Ativo" if user[3] else "❌ Inativo"
                print(f"ID: {user[0]:3} | Username: {user[1]:20} | Email: {user[2]:30} | {status}")
        else:
            print("ℹ️  Nenhum usuário cadastrado.")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao listar usuários: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Gerenciador de Superuser - Prototype")
    print("=" * 80)
    
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'list':
        list_users()
    else:
        create_superuser()
        print("\n" + "=" * 80)
        list_users()
