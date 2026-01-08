-- Script para criar superuser automaticamente
-- Este script será executado após a criação das tabelas

USE prototype;

-- Primeiro, vamos criar um endereço padrão para o superuser
INSERT INTO Address (Cep, City, Estate, Adress, Number, Neighborhood, Complement) 
VALUES ('00000-000', 'São Paulo', 'SP', 'Rua Admin', 1, 'Centro', 'Sala Admin')
ON DUPLICATE KEY UPDATE Cep = Cep;

-- Obter o ID do endereço recém criado
SET @address_id = LAST_INSERT_ID();

-- Criar o superuser com token inicial
-- Token gerado para: email=superuser@prototype.com, id_user=1
-- Este é um token JWT de exemplo que deve ser substituído em produção
SET @initial_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InN1cGVydXNlckBwcm90b3R5cGUuY29tIiwidXNlcm5hbWUiOiJzdXBlcnVzZXIiLCJpZF91c2VyIjoxLCJleHAiOjE3MzEyOTM0MDB9.example_signature_replace_in_production';

-- Inserir o superuser
INSERT INTO User (UserName, Password, Email, Phone, Token, Address_IdAddress, Active) 
VALUES (
    'superuser', 
    '123123123',  -- Senha em texto plano (em produção use hash)
    'superuser@prototype.com', 
    '+55 11 99999-9999', 
    @initial_token,
    @address_id,
    1
) ON DUPLICATE KEY UPDATE 
    Password = VALUES(Password),
    Token = VALUES(Token),
    UpdatedAt = CURRENT_TIMESTAMP;

-- Verificar se o usuário foi criado
SELECT 
    IdUser, 
    UserName, 
    Email, 
    Phone, 
    Active,
    CreatedAt
FROM User 
WHERE Email = 'superuser@prototype.com';

-- Mensagem de confirmação (será exibida nos logs do Docker)
SELECT 'Superuser created successfully!' as Status, 
       'Email: superuser@prototype.com' as Login,
       'Password: 123123123' as Password,
       'Use /token_generate endpoint to get a fresh token' as Instructions;
