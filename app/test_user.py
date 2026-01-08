#!/usr/bin/env python3
"""
Teste rápido para verificar se o SQLAlchemy está lendo corretamente os dados
"""

from database import db_models
from database.database import SessionLocal

def test_user_query():
    db = SessionLocal()
    try:
        user = db.query(db_models.User).filter(
            db_models.User.email == "superadmin@gmail.com"
        ).first()
        
        if user:
            print(f"ID User: {user.id_user}")
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Role: {user.role}")
            print(f"Company ID: {user.company_id}")
        else:
            print("Usuário não encontrado")
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_user_query()
