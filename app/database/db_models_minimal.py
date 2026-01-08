from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base  
from datetime import datetime

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
    company_id = Column("company_id", Integer, nullable=True)  # Removendo ForeignKey temporariamente
    created_at = Column("CreatedAt", DateTime, nullable=True, default=datetime.now())
    updated_at = Column("UpdatedAt", DateTime, nullable=True, default=datetime.now(), onupdate=datetime.now())
    active = Column("Active", Boolean, nullable=True, default=True)

class Permission(Base):
    __tablename__ = 'permissions'

    id_permission = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(String(250), nullable=True)
    created_at = Column(DateTime, nullable=True, default=datetime.now())

class UserPermission(Base):
    __tablename__ = 'user_permissions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)  # Removendo ForeignKey temporariamente
    permission_id = Column(Integer, nullable=False)  # Removendo ForeignKey temporariamente
