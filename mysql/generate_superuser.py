#!/usr/bin/env python3
"""
Script para criar superuser automaticamente com senha bcrypt.
Gera SQL para inserir o superadmin no MySQL.
Use /token_generate/ para obter um token JWT após a criação.
"""

from datetime import datetime
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configurações do superuser
EMAIL = "superadmin@gmail.com"
USERNAME = "superadmin"
PLAIN_PASSWORD = "123123123"
PHONE = "+55 11 99999-9999"


def generate_sql():
    """Gera SQL com senha bcrypt para o superuser"""
    hashed_password = pwd_context.hash(PLAIN_PASSWORD)

    sql = f"""
-- Script para criar superuser com senha bcrypt
-- Gerado em: {datetime.now().isoformat()}

USE prototype;

-- Criar superuser
INSERT INTO User (UserName, Password, Email, Phone, Token, Active, role, company_id, CreatedAt, UpdatedAt)
VALUES (
    '{USERNAME}',
    '{hashed_password}',
    '{EMAIL}',
    '{PHONE}',
    NULL,
    1,
    'superadmin',
    NULL,
    NOW(),
    NOW()
) ON DUPLICATE KEY UPDATE
    Password = VALUES(Password),
    role = VALUES(role),
    Active = VALUES(Active),
    UpdatedAt = CURRENT_TIMESTAMP;

-- Verificação
SELECT 'Superuser created successfully!' as Status,
       'Email: {EMAIL}' as Login,
       'Password: {PLAIN_PASSWORD}' as Password,
       'Use /token_generate/ to get a JWT token' as Instructions;
"""
    return sql


if __name__ == "__main__":
    sql_content = generate_sql()

    # Salvar no arquivo (dentro do container) ou mostrar no console
    output_file = "/docker-entrypoint-initdb.d/01_create_superuser.sql"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(sql_content)
        print(f"Superuser SQL gerado: {output_file}")
    except OSError:
        print("SQL para criar superuser:")
        print(sql_content)

    print(f"\nCredenciais do superuser:")
    print(f"  Email: {EMAIL}")
    print(f"  Senha: {PLAIN_PASSWORD}")
    print(f"  Use POST /token_generate/ para obter um token JWT")
