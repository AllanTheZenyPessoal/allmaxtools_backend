from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base  
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime, timezone

Base = declarative_base()

class User(Base):
    __tablename__ = 'User'

    id_user = Column("IdUser", Integer, primary_key=True, autoincrement=True)
    username = Column("UserName", String(250), unique=True, nullable=True)
    password = Column("Password", String(250))
    email = Column("Email", String(250), unique=True)
    phone = Column("Phone", String(45), nullable=True)
    token = Column("Token", String(500), unique=True, nullable=True)
    role = Column("role", String(50), nullable=False, default='user')  # 'superadmin', 'admin', 'user'
    # company_id é NULL apenas para superadmin, obrigatório para admin/user
    company_id = Column("company_id", Integer, ForeignKey('Company.IdCompany'), nullable=True)
    created_at = Column("CreatedAt", DateTime, nullable=True, default=datetime.now())
    updated_at = Column("UpdatedAt", DateTime, nullable=True, default=datetime.now(), onupdate=datetime.now())
    active = Column("Active", Boolean, nullable=True, default=True)

class Company(Base):
    __tablename__ = 'Company'

    id_company = Column("IdCompany", Integer, primary_key=True, autoincrement=True)
    razao_social = Column("RazaoSocial", String(450))
    nome_fantasia = Column("NomeFantasia", String(450))
    cnpj = Column("CNPJ", String(45), unique=True)
    email = Column("Email", String(45), unique=True)
    phone = Column("Phone", String(45))
    active = Column("Active", Boolean)
    created_at = Column("CreatedAt", DateTime, nullable=True, default=datetime.now())
    updated_at = Column("UpdatedAt", DateTime, nullable=True, default=datetime.now(), onupdate=datetime.now())

class Permission(Base):
    __tablename__ = 'permissions'

    id_permission = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(String(250), nullable=True)
    created_at = Column(DateTime, nullable=True, default=datetime.now())

class UserPermission(Base):
    __tablename__ = 'user_permissions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('User.IdUser'), nullable=False)
    permission_id = Column(Integer, ForeignKey('permissions.id_permission'), nullable=False)
