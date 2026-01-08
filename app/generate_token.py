#!/usr/bin/env python3
"""
Utilitário para gerar tokens JWT para o sistema Prototype
Pode ser usado para criar tokens iniciais para usuários
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from token_utils.apikey_generator import create_access_token
from datetime import timedelta

def generate_superuser_token():
    """Gera um token válido para o superuser"""
    try:
        # Dados do superuser
        email = "superuser@prototype.com"
        username = "superuser"
        id_user = 1
        
        # Token válido por 30 dias
        expires_delta = timedelta(days=30)
        
        # Gerar token
        token = create_access_token(
            email=email,
            username=username,
            id_user=id_user,
            expires_delta=expires_delta
        )
        
        return token
        
    except Exception as e:
        print(f"Erro ao gerar token: {e}")
        return None

def main():
    """Função principal"""
    print("🔑 Gerador de Token JWT - Prototype")
    print("=" * 50)
    
    # Gerar token para superuser
    token = generate_superuser_token()
    
    if token:
        print("✅ Token gerado com sucesso!")
        print(f"\n📧 Email: superuser@prototype.com")
        print(f"🔐 Senha: 123123123")
        print(f"🎯 Token JWT:")
        print(f"   {token}")
        print(f"\n📋 Para usar o token:")
        print(f"   Authorization: Bearer {token}")
        print(f"\n⏰ Token válido por 30 dias")
        
        # Salvar token em arquivo para uso no MySQL
        try:
            with open('/tmp/superuser_token.txt', 'w') as f:
                f.write(token)
            print(f"💾 Token salvo em: /tmp/superuser_token.txt")
        except:
            pass
            
    else:
        print("❌ Falha ao gerar token")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
