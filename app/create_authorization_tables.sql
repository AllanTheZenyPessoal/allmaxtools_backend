-- Script SQL para criar as tabelas do sistema de autorização
-- Execute este script no banco SQLite para adicionar as novas tabelas

-- Primeiro, adicionar as colunas role e company_id à tabela user existente
ALTER TABLE user ADD COLUMN role TEXT DEFAULT 'user' CHECK(role IN ('user', 'admin', 'superadmin'));
ALTER TABLE user ADD COLUMN company_id INTEGER REFERENCES company(id_company);

-- Criar tabela de telas
CREATE TABLE IF NOT EXISTS screen (
    id_screen INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    route TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Criar tabela de permissões
CREATE TABLE IF NOT EXISTS permission (
    id_permission INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    screen_id INTEGER REFERENCES screen(id_screen),
    active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Criar tabela de permissões de usuário
CREATE TABLE IF NOT EXISTS user_permission (
    id_user_permission INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id_user) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permission(id_permission) ON DELETE CASCADE,
    granted_by INTEGER REFERENCES user(id_user),
    granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, permission_id)
);

-- Criar índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_user_role ON user(role);
CREATE INDEX IF NOT EXISTS idx_user_company ON user(company_id);
CREATE INDEX IF NOT EXISTS idx_permission_key ON permission(key);
CREATE INDEX IF NOT EXISTS idx_permission_screen ON permission(screen_id);
CREATE INDEX IF NOT EXISTS idx_user_permission_user ON user_permission(user_id);
CREATE INDEX IF NOT EXISTS idx_user_permission_permission ON user_permission(permission_id);

-- Inserir dados iniciais de exemplo (executados pelo script Python)
-- Nota: Os dados serão inseridos pelo script setup_authorization.py

-- Verificar criação das tabelas
SELECT name FROM sqlite_master WHERE type='table' AND name IN ('screen', 'permission', 'user_permission');

-- Mostrar estrutura atualizada da tabela user
PRAGMA table_info(user);
