#!/bin/bash
# Script para gerar superuser automaticamente no MySQL
# Este script será executado durante a inicialização do container MySQL

echo "🚀 Gerando superuser com token..."

# Definir configurações
EMAIL="superuser@prototype.com"
USERNAME="superuser"
PASSWORD="123123123"
PHONE="+55 11 99999-9999"

# Token JWT básico (válido por 30 dias a partir de agora)
# Este é um token de exemplo - em produção, usar um gerador JWT adequado
EXPIRY=$(date -d "+30 days" +%s)
CURRENT_TIME=$(date +%s)

# Token básico codificado (substitua por um real em produção)
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InN1cGVydXNlckBwcm90b3R5cGUuY29tIiwidXNlcm5hbWUiOiJzdXBlcnVzZXIiLCJpZF91c2VyIjoxLCJleHAiOiR7RVhQSVJZfX0.example_signature_use_real_jwt_in_production"

# Criar arquivo SQL com superuser
cat > /docker-entrypoint-initdb.d/01_create_superuser_generated.sql << EOF
-- Superuser gerado automaticamente em $(date)
-- Este arquivo é gerado pelo script generate_superuser.sh

USE prototype;

-- Criar endereço padrão para o superuser
INSERT INTO Address (Cep, City, Estate, Adress, Number, Neighborhood, Complement) 
VALUES ('00000-000', 'São Paulo', 'SP', 'Rua Admin', 1, 'Centro', 'Sala Admin')
ON DUPLICATE KEY UPDATE 
    UpdatedAt = CURRENT_TIMESTAMP;

-- Obter ID do endereço
SET @address_id = LAST_INSERT_ID();
IF @address_id = 0 THEN
    SET @address_id = (SELECT IdAddress FROM Address WHERE Cep = '00000-000' LIMIT 1);
END IF;

-- Criar/atualizar superuser
INSERT INTO User (UserName, Password, Email, Phone, Token, Address_IdAddress, Active) 
VALUES (
    '${USERNAME}', 
    '${PASSWORD}',
    '${EMAIL}', 
    '${PHONE}', 
    '${TOKEN}',
    @address_id,
    1
) ON DUPLICATE KEY UPDATE 
    Password = VALUES(Password),
    Token = VALUES(Token),
    Phone = VALUES(Phone),
    Active = VALUES(Active),
    UpdatedAt = CURRENT_TIMESTAMP;

-- Verificar criação
SELECT 
    IdUser, 
    UserName, 
    Email, 
    Phone, 
    Active,
    CASE 
        WHEN Token IS NOT NULL THEN 'Token definido' 
        ELSE 'Sem token' 
    END as TokenStatus,
    CreatedAt
FROM User 
WHERE Email = '${EMAIL}';

-- Mensagem de sucesso
SELECT 
    '✅ Superuser criado com sucesso!' as Status,
    'Email: ${EMAIL}' as Login,
    'Senha: ${PASSWORD}' as Password,
    'Use o endpoint /token_generate para obter um token fresco' as Instructions,
    'Token inicial válido por 30 dias' as TokenInfo;

EOF

echo "✅ Script SQL do superuser gerado com sucesso!"
echo "📧 Email: ${EMAIL}"
echo "🔐 Senha: ${PASSWORD}"
echo "🎯 Use /token_generate para obter tokens atualizados"
