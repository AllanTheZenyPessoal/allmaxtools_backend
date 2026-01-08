from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float, Date, Text
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

class SalesOrder(Base):
    __tablename__ = 'SalesOrder'

    IdSalesOrder = Column("IdSalesOrder", Integer, primary_key=True, autoincrement=True)
    Redespacho = Column("Redespacho", Integer, default=0)
    DataLancamento = Column("DataLancamento", DateTime, nullable=True)
    DataEntrega = Column("DataEntrega", DateTime, nullable=True)
    Discount = Column("Discount", Float, default=0)
    Observation = Column("Observation", String(5000), nullable=True)
    CompanyId = Column("CompanyId", Integer, nullable=True)
    BusinessPartnerId = Column("BusinessPartnerId", Integer, nullable=True)
    PaymentMethodId = Column("PaymentMethodId", Integer, nullable=True)
    PaymentTermId = Column("PaymentTermId", Integer, nullable=True)
    UtilizationId = Column("UtilizationId", Integer, nullable=True)
    BranchId = Column("BranchId", Integer, nullable=True)
    FreightId = Column("FreightId", Integer, nullable=True)
    RedespachoSalesOrderId = Column("RedespachoSalesOrderId", Integer, nullable=True)
    SynchronizationStatusId = Column("SynchronizationStatusId", Integer, nullable=True)
    CreatedByUserId = Column("CreatedByUserId", Integer, nullable=True)
    CreatedAt = Column("CreatedAt", DateTime, nullable=True, default=datetime.now)
    UpdatedAt = Column("UpdatedAt", DateTime, nullable=True, default=datetime.now, onupdate=datetime.now)

class Address(Base):
    __tablename__ = 'address'
    
    id_address = Column("id_address", Integer, primary_key=True, autoincrement=True)
    cep = Column("cep", String(10), nullable=False)
    city = Column("city", String(100), nullable=False)
    estate = Column("estate", String(2), nullable=False)
    adress = Column("adress", String(255), nullable=False)
    number = Column("number", Integer, nullable=False)
    neighborhood = Column("neighborhood", String(100), nullable=False)
    complement = Column("complement", String(255), nullable=True)

class Company(Base):
    __tablename__ = 'company'
    
    id_company = Column("id_company", Integer, primary_key=True, autoincrement=True)
    razao_social = Column("razao_social", String(255), nullable=False)
    nome_fantasia = Column("nome_fantasia", String(255), nullable=False)
    cnpj = Column("cnpj", String(18), nullable=False, unique=True)
    email = Column("email", String(255), nullable=False)
    phone = Column("phone", String(20), nullable=False)
    id_address = Column("id_address", Integer, nullable=True)
    active = Column("active", Boolean, nullable=False, default=True)
    created_at = Column("created_at", DateTime, nullable=True, default=datetime.now)
    updated_at = Column("updated_at", DateTime, nullable=True, default=datetime.now, onupdate=datetime.now)

class BusinessPartner(Base):
    __tablename__ = 'businesspartner'
    
    IdBusinessPartner = Column("IdBusinessPartner", Integer, primary_key=True, autoincrement=True)
    razao_social = Column("razao_social", String(255), nullable=False)
    nome_fantasia = Column("nome_fantasia", String(255), nullable=False)
    cnpj = Column("cnpj", String(18), nullable=False)
    inscricao_estadual = Column("inscricao_estadual", String(50), nullable=True)
    inscricao_municipal = Column("inscricao_municipal", String(50), nullable=True)
    cnae = Column("cnae", String(20), nullable=True)
    suframa = Column("suframa", String(50), nullable=True)
    regime_especial = Column("regime_especial", Integer, nullable=True, default=0)
    sugestao_limite_credito = Column("sugestao_limite_credito", Float, nullable=True, default=0)
    email = Column("email", String(255), nullable=False)
    phone = Column("phone", String(20), nullable=False)
    observation = Column("observation", Text, nullable=True)
    id_address = Column("id_address", Integer, nullable=True)
    id_company = Column("id_company", Integer, nullable=True)
    IdSynchronizationStatus = Column("IdSynchronizationStatus", Integer, nullable=True)
    created_at = Column("created_at", DateTime, nullable=True, default=datetime.now)
    updated_at = Column("updated_at", DateTime, nullable=True, default=datetime.now, onupdate=datetime.now)

class CompanyBranch(Base):
    __tablename__ = 'companybranch'
    
    IdCompanyBranch = Column("IdCompanyBranch", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(255), nullable=False)
    code = Column("code", String(50), nullable=False)
    id_company = Column("id_company", Integer, nullable=False)
    IdSynchronizationStatus = Column("IdSynchronizationStatus", Integer, nullable=True)
    created_at = Column("created_at", DateTime, nullable=True, default=datetime.now)
    updated_at = Column("updated_at", DateTime, nullable=True, default=datetime.now, onupdate=datetime.now)

class CompanyFreight(Base):
    __tablename__ = 'companyfreight'
    
    IdCompanyFreight = Column("IdCompanyFreight", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(255), nullable=False)
    code = Column("code", String(50), nullable=False)
    id_company = Column("id_company", Integer, nullable=False)
    IdSynchronizationStatus = Column("IdSynchronizationStatus", Integer, nullable=True)
    created_at = Column("created_at", DateTime, nullable=True, default=datetime.now)
    updated_at = Column("updated_at", DateTime, nullable=True, default=datetime.now, onupdate=datetime.now)

class CompanyPaymentMethod(Base):
    __tablename__ = 'companypaymentmethod'
    
    IdCompanyPaymentMethod = Column("IdCompanyPaymentMethod", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(255), nullable=False)
    code = Column("code", String(50), nullable=False)
    id_company = Column("id_company", Integer, nullable=False)
    IdSynchronizationStatus = Column("IdSynchronizationStatus", Integer, nullable=True)
    created_at = Column("created_at", DateTime, nullable=True, default=datetime.now)
    updated_at = Column("updated_at", DateTime, nullable=True, default=datetime.now, onupdate=datetime.now)

class CompanyPaymentTerm(Base):
    __tablename__ = 'companypaymentterm'
    
    IdCompanyPaymentTerm = Column("IdCompanyPaymentTerm", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(255), nullable=False)
    code = Column("code", String(50), nullable=False)
    id_company = Column("id_company", Integer, nullable=False)
    IdSynchronizationStatus = Column("IdSynchronizationStatus", Integer, nullable=True)
    created_at = Column("created_at", DateTime, nullable=True, default=datetime.now)
    updated_at = Column("updated_at", DateTime, nullable=True, default=datetime.now, onupdate=datetime.now)

class CompanyUtilization(Base):
    __tablename__ = 'companyutilization'
    
    IdCompanyUtilization = Column("IdCompanyUtilization", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(255), nullable=False)
    code = Column("code", String(50), nullable=False)
    id_company = Column("id_company", Integer, nullable=False)
    IdSynchronizationStatus = Column("IdSynchronizationStatus", Integer, nullable=True)
    created_at = Column("created_at", DateTime, nullable=True, default=datetime.now)
    updated_at = Column("updated_at", DateTime, nullable=True, default=datetime.now, onupdate=datetime.now)
