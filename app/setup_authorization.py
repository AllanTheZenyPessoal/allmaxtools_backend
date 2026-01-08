#!/usr/bin/env python3
"""
Script para criar dados iniciais do sistema de autorização
Execute este script após a migração do banco para configurar o sistema inicial
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime
from passlib.context import CryptContext

# Configuração para hash de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_initial_data():
    """Cria dados iniciais para o sistema de autorização"""
    
    # Caminho para o banco de dados
    db_path = Path(__file__).parent / 'prototype.db'
    
    if not db_path.exists():
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return False
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🚀 Configurando sistema de autorização...")
        
        # 1. Criar telas básicas
        screens_data = [
            ("Users Management", "Gerenciamento de usuários", "/users"),
            ("Companies Management", "Gerenciamento de empresas", "/companies"),
            ("Permissions Management", "Gerenciamento de permissões", "/permissions"),
            ("Dashboard", "Painel principal", "/dashboard"),
            ("Reports", "Relatórios", "/reports")
        ]
        
        print("📱 Criando telas do sistema...")
        for name, description, route in screens_data:
            cursor.execute("""
                INSERT OR IGNORE INTO screen (name, description, route, active, created_at, updated_at)
                VALUES (?, ?, ?, 1, ?, ?)
            """, (name, description, route, datetime.now(), datetime.now()))
        
        # 2. Criar permissões básicas
        permissions_data = [
            # Usuários
            ("user.create", "Criar usuários", "Permissão para criar novos usuários", 1),
            ("user.read", "Visualizar usuários", "Permissão para visualizar dados de usuários", 1),
            ("user.update", "Editar usuários", "Permissão para editar dados de usuários", 1),
            ("user.delete", "Excluir usuários", "Permissão para excluir usuários", 1),
            ("user.list", "Listar usuários", "Permissão para listar todos os usuários", 1),
            
            # Empresas
            ("company.create", "Criar empresas", "Permissão para criar novas empresas", 2),
            ("company.read", "Visualizar empresas", "Permissão para visualizar dados de empresas", 2),
            ("company.update", "Editar empresas", "Permissão para editar dados de empresas", 2),
            ("company.delete", "Excluir empresas", "Permissão para excluir empresas", 2),
            ("company.list", "Listar empresas", "Permissão para listar todas as empresas", 2),
            
            # Permissões
            ("permission.create", "Criar permissões", "Permissão para criar novas permissões", 3),
            ("permission.read", "Visualizar permissões", "Permissão para visualizar permissões", 3),
            ("permission.assign", "Atribuir permissões", "Permissão para atribuir permissões a usuários", 3),
            
            # Dashboard
            ("dashboard.view", "Visualizar dashboard", "Permissão para acessar o dashboard", 4),
            
            # Relatórios
            ("reports.view", "Visualizar relatórios", "Permissão para visualizar relatórios", 5),
            ("reports.export", "Exportar relatórios", "Permissão para exportar relatórios", 5)
        ]
        
        print("🔑 Criando permissões do sistema...")
        for key, name, description, screen_id in permissions_data:
            cursor.execute("""
                INSERT OR IGNORE INTO permission (key, name, description, screen_id, active, created_at, updated_at)
                VALUES (?, ?, ?, ?, 1, ?, ?)
            """, (key, name, description, screen_id, datetime.now(), datetime.now()))
        
        # 3. Atualizar superuser existente com role
        print("👑 Configurando superadmin...")
        cursor.execute("""
            UPDATE user 
            SET role = 'superadmin', company_id = NULL
            WHERE email = 'superadmin@gmail.com'
        """)
        
        # 4. Criar empresa exemplo
        print("🏢 Criando empresa exemplo...")
        cursor.execute("""
            INSERT OR IGNORE INTO company (
                razao_social, nome_fantasia, cnpj, email, phone, active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "Empresa Exemplo LTDA",
            "Empresa Exemplo", 
            "12.345.678/0001-90",
            "contato@exemplo.com",
            "+55 11 99999-0000",
            True,
            datetime.now(),
            datetime.now()
        ))
        
        # 5. Criar usuário admin exemplo
        print("👨‍💼 Criando admin exemplo...")
        admin_password = pwd_context.hash("admin123")
        cursor.execute("""
            INSERT OR IGNORE INTO user (
                username, password, email, phone, role, company_id, active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "admin",
            admin_password,
            "admin@exemplo.com",
            "+55 11 98888-0000",
            "admin",
            1,  # ID da empresa exemplo
            True,
            datetime.now(),
            datetime.now()
        ))
        
        # 6. Criar usuário comum exemplo
        print("👤 Criando usuário comum exemplo...")
        user_password = pwd_context.hash("user123")
        cursor.execute("""
            INSERT OR IGNORE INTO user (
                username, password, email, phone, role, company_id, active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "user",
            user_password,
            "user@exemplo.com",
            "+55 11 97777-0000",
            "user",
            1,  # ID da empresa exemplo
            True,
            datetime.now(),
            datetime.now()
        ))
        
        # 7. Atribuir algumas permissões ao usuário comum
        print("🔐 Atribuindo permissões ao usuário exemplo...")
        user_permissions = [
            "dashboard.view",
            "user.read",
            "reports.view"
        ]
        
        for permission_key in user_permissions:
            # Buscar IDs
            cursor.execute("SELECT id_user FROM user WHERE email = 'user@exemplo.com'")
            user_result = cursor.fetchone()
            
            cursor.execute("SELECT id_permission FROM permission WHERE key = ?", (permission_key,))
            permission_result = cursor.fetchone()
            
            if user_result and permission_result:
                cursor.execute("""
                    INSERT OR IGNORE INTO user_permission (user_id, permission_id, granted_by, granted_at)
                    VALUES (?, ?, ?, ?)
                """, (user_result[0], permission_result[0], 2, datetime.now()))  # Granted by admin (id=2)
        
        conn.commit()
        
        print("\n✅ Sistema de autorização configurado com sucesso!")
        print("\n👥 Usuários criados:")
        print("   🔹 Superadmin: superadmin@gmail.com / 123123123")
        print("   🔹 Admin: admin@exemplo.com / admin123")
        print("   🔹 User: user@exemplo.com / user123")
        
        print("\n🏢 Empresa exemplo criada:")
        print("   🔹 Empresa Exemplo LTDA (CNPJ: 12.345.678/0001-90)")
        
        print("\n📱 Telas configuradas:")
        for name, _, route in screens_data:
            print(f"   🔹 {name} ({route})")
        
        print(f"\n🔑 {len(permissions_data)} permissões configuradas")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao configurar sistema: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("🚀 Configurador do Sistema de Autorização - Prototype")
    print("=" * 80)
    
    create_initial_data()
    print("\n" + "=" * 80)
    print("🎯 Sistema pronto para uso!")
    print("   Use os endpoints /auth/* para autenticação")
    print("   Use os endpoints /authorization/* para gerenciar permissões")
    print("   Use os endpoints /user/* para gerenciar usuários (com permissões)")
