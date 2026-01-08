#!/usr/bin/env python3
"""
Script para criar superuser automaticamente com token válido
Este script pode ser executado após o build do MySQL para criar o usuário inicial
"""

import jwt
import hashlib
from datetime import datetime, timedelta
import os

# Configurações
SECRET_KEY = "AppS3rcr3t"  # Mesmo secret do backend
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 43200  # 30 dias

def create_access_token(email: str, username: str, id_user: int, expires_delta: timedelta = None):
    """Criar token JWT"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "email": email,
        "username": username, 
        "id_user": id_user,
        "exp": expire
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def hash_password(password: str) -> str:
    """Hash da senha (se necessário)"""
    # Por enquanto retorna a senha em texto plano como está sendo usado
    # Em produção, implementar hash seguro
    return password

def generate_superuser_token():
    """Gera token para o superuser"""
    email = "superuser@prototype.com"
    username = "superuser"
    id_user = 1
    
    # Token com validade de 30 dias
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(email, username, id_user, expires_delta)
    
    return token

def generate_sql_with_token():
    """Gera SQL com token válido"""
    token = generate_superuser_token()
    password = hash_password("123123123")
    
    sql = f"""
-- Script para criar superuser com token válido
-- Gerado em: {datetime.now().isoformat()}

USE prototype;

-- Criar endereço padrão
INSERT INTO Address (Cep, City, Estate, Adress, Number, Neighborhood, Complement) 
VALUES ('00000-000', 'São Paulo', 'SP', 'Rua Admin', 1, 'Centro', 'Sala Admin')
ON DUPLICATE KEY UPDATE Cep = Cep;

SET @address_id = LAST_INSERT_ID();

-- Criar superuser com token válido
INSERT INTO User (UserName, Password, Email, Phone, Token, Address_IdAddress, Active) 
VALUES (
    'superuser', 
    '{password}',
    'superuser@prototype.com', 
    '+55 11 99999-9999', 
    '{token}',
    @address_id,
    1
) ON DUPLICATE KEY UPDATE 
    Password = VALUES(Password),
    Token = VALUES(Token),
    UpdatedAt = CURRENT_TIMESTAMP;

-- Verificação
SELECT 'Superuser created successfully!' as Status,
       'Email: superuser@prototype.com' as Login,
       'Password: 123123123' as Password,
       'Token válido por 30 dias' as TokenInfo;
"""
    
    return sql

if __name__ == "__main__":
    # Gerar SQL com token válido
    sql_content = generate_sql_with_token()
    
    # Salvar no arquivo
    output_file = "/docker-entrypoint-initdb.d/01_create_superuser.sql"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(sql_content)
        print(f"✅ Superuser SQL gerado: {output_file}")
    except:
        # Se não conseguir escrever no docker-entrypoint, mostrar o SQL
        print("📋 SQL para criar superuser:")
        print(sql_content)
    
    # Mostrar o token gerado
    token = generate_superuser_token()
    print(f"\n🔑 Token gerado: {token}")
    print(f"\n📋 Credenciais do superuser:")
    print(f"   Email: superuser@prototype.com")
    print(f"   Senha: 123123123")
    print(f"   Token válido até: {(datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).isoformat()}")
