-- Script SQL para criar superuser no SQLite
-- Execute este script manualmente ou via script Python

-- Deletar superuser se já existir (para recriar)
DELETE FROM user WHERE email = 'superuser@prototype.com';

-- Criar superuser
INSERT INTO user (username, password, email, phone, token, active, created_at, updated_at)
VALUES (
    'superuser',
    '123123123',
    'superuser@prototype.com',
    '+55 11 99999-9999',
    NULL,  -- Token será gerado via endpoint
    1,     -- Ativo
    datetime('now'),
    datetime('now')
);

-- Verificar criação
SELECT 
    id_user,
    username,
    email,
    phone,
    active,
    created_at
FROM user
WHERE email = 'superuser@prototype.com';

-- Instruções
SELECT 'Superuser criado com sucesso!' as status,
       'Email: superuser@prototype.com' as login,
       'Senha: 123123123' as password,
       'Use POST /token_generate/ para obter token' as instructions;
