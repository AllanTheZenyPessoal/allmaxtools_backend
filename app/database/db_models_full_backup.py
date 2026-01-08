from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base  
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime, timezone

Base = declarative_base()

class SincronizationStatus(Base):
    __tablename__ = 'sincronization_status'

    id_sincronization_status = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(String(45))
    error = Column(String(45))
    code_error = Column(String(45))
    created_at = Column(DateTime, nullable=True, default=datetime.now())
    updated_at = Column(DateTime, nullable=True, default=datetime.now(), onupdate=datetime.now())

class Address(Base):
    __tablename__ = 'address'

    id_address = Column(Integer, primary_key=True, autoincrement=True)
    cep = Column(String(45))
    city = Column(String(250))
    estate = Column(String(250))
    adress = Column(String(245))
    number = Column(Integer)
    neighborhood = Column(String(250))
    complement = Column(String(250))
    created_at = Column(DateTime, nullable=True, default=datetime.now())
    updated_at = Column(DateTime, nullable=True, default=datetime.now(), onupdate=datetime.now())

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
    # id_address comentado temporariamente para compatibilidade com SQLite antigo
    # Descomente após executar migrate_database.py
    # id_address = Column(Integer, ForeignKey('address.id_address'), nullable=True)
    active = Column("Active", Boolean, nullable=True, default=True)

    # Relacionamentos comentados temporariamente para evitar problemas de mapeamento
    # company = relationship('Company', back_populates='users')
    # user_permissions = relationship('UserPermission', back_populates='user', foreign_keys='UserPermission.user_id')
    # granted_permissions = relationship('UserPermission', back_populates='granter', foreign_keys='UserPermission.granted_by')
    # address = relationship('Address')

class Company(Base):
    __tablename__ = 'Company'

    id_company = Column("IdCompany", Integer, primary_key=True, autoincrement=True)
    razao_social = Column(String(450))
    nome_fantasia = Column(String(450))
    cnpj = Column(String(45), unique=True)
    email = Column(String(45), unique=True)
    phone = Column(String(45))
    active = Column(Boolean)
    id_address = Column(Integer, ForeignKey('address.id_address'))  
    created_at = Column(DateTime, nullable=True, default=datetime.now())
    updated_at = Column(DateTime, nullable=True, default=datetime.now(), onupdate=datetime.now())

    # Relacionamentos comentados temporariamente
    # users = relationship('User', back_populates='company')

class Screen(Base):
    __tablename__ = 'screen'

    id_screen = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(250), nullable=True)
    route = Column(String(200), nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=True, default=datetime.now())
    updated_at = Column(DateTime, nullable=True, default=datetime.now(), onupdate=datetime.now())

    # Relacionamentos comentados temporariamente
    # permissions = relationship('Permission', back_populates='screen')

class Permission(Base):
    __tablename__ = 'permissions'

    id_permission = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)  # Ex: "user.create", "button.delete_user"
    name = Column(String(100), nullable=False)
    description = Column(String(250), nullable=True)
    # screen_id = Column(Integer, ForeignKey('screen.id_screen'), nullable=True)  # Comentado temporariamente
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=True, default=datetime.now())
    updated_at = Column(DateTime, nullable=True, default=datetime.now(), onupdate=datetime.now())

    # Relacionamentos comentados temporariamente
    # screen = relationship('Screen', back_populates='permissions')
    # user_permissions = relationship('UserPermission', back_populates='permission')

class UserPermission(Base):
    __tablename__ = 'user_permissions'

    id_user_permission = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('User.IdUser'), nullable=False)
    permission_id = Column(Integer, ForeignKey('permissions.id_permission'), nullable=False)
    granted_by = Column(Integer, ForeignKey('User.IdUser'), nullable=True)  # Quem concedeu a permissão
    granted_at = Column(DateTime, nullable=True, default=datetime.now())

    # Relacionamentos comentados temporariamente
    # user = relationship('User', back_populates='user_permissions', foreign_keys=[user_id])
    # permission = relationship('Permission', back_populates='user_permissions')
    # granter = relationship('User', foreign_keys=[granted_by])

class CompanyAPIConfiguration(Base):
    __tablename__ = 'company_api_configuration'

    id_company_api_configuration = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(3000))
    access_json = Column(String(3000))
    created_at = Column(DateTime, nullable=True, default=datetime.now())
    updated_at = Column(DateTime, nullable=True, default=datetime.now(), onupdate=datetime.now())

class CompanyPlanConfiguration(Base):
    __tablename__ = 'company_plan_configuration'

    id_company_plan_configuration = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, nullable=True, default=datetime.now())
    updated_at = Column(DateTime, nullable=True, default=datetime.now(), onupdate=datetime.now())
    max_solicitation = Column(Integer)
    valid_until = Column(DateTime)

class CompanyBranch(Base):
    __tablename__ = 'company_branch'

    id_company_branch = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(250))
    code = Column(String(250), unique=True)
    id_company = Column(Integer, ForeignKey('Company.IdCompany'))
    id_sincronization_status = Column(Integer, ForeignKey('sincronization_status.id_sincronization_status'))
    created_at = Column(DateTime, nullable=True, default=datetime.now())
    updated_at = Column(DateTime, nullable=True, default=datetime.now(), onupdate=datetime.now())

    # company = relationship('Company')
    # sincronization_status = relationship('SincronizationStatus')

class CompanyFreight(Base):
    __tablename__ = 'company_freight'

    id_company_freight = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(250))
    code = Column(String(250))
    id_company = Column(Integer, ForeignKey('company.id_company'))
    id_sincronization_status = Column(Integer, ForeignKey('sincronization_status.id_sincronization_status'))
    created_at = Column(DateTime, nullable=True, default=datetime.now())
    updated_at = Column(DateTime, nullable=True, default=datetime.now(), onupdate=datetime.now())

    # company = relationship('Company')
    # sincronization_status = relationship('SincronizationStatus')

class CompanyPaymentMethod(Base):
    __tablename__ = 'company_payment_method'

    id_company_payment_method = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(250))
    code = Column(String(250))
    id_company = Column(Integer, ForeignKey('Company.IdCompany'))
    id_sincronization_status = Column(Integer, ForeignKey('sincronization_status.id_sincronization_status'))
    created_at = Column(DateTime, nullable=True, default=datetime.now())
    updated_at = Column(DateTime, nullable=True, default=datetime.now(), onupdate=datetime.now())

    # company = relationship('Company')
    # sincronization_status = relationship('SincronizationStatus')

class CompanyPaymentTerm(Base):
    __tablename__ = 'company_payment_term'

    id_company_payment_term = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(250))
    code = Column(String(250))
    id_company = Column(Integer, ForeignKey('company.id_company'))
    id_sincronization_status = Column(Integer, ForeignKey('sincronization_status.id_sincronization_status'))
    created_at = Column(DateTime, nullable=True, default=datetime.now())
    updated_at = Column(DateTime, nullable=True, default=datetime.now(), onupdate=datetime.now())

#    company = relationship('Company')
#    sincronization_status = relationship('SincronizationStatus')

class CompanyProduct(Base):
    __tablename__ = 'company_product'

    id_product = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(250))
    name = Column(String(250))
    weight = Column(Float)
    size = Column(Float)
    id_company = Column(Integer, ForeignKey('company.id_company'))
    id_sincronization_status = Column(Integer, ForeignKey('sincronization_status.id_sincronization_status'))
    created_at = Column(DateTime, nullable=True, default=datetime.now())
    updated_at = Column(DateTime, nullable=True, default=datetime.now(), onupdate=datetime.now())

#    company = relationship('Company')
#    sincronization_status = relationship('SincronizationStatus')

class CompanyProductStock(Base):
    __tablename__ = 'company_product_stock'

    id_company_product_stock = Column(Integer, primary_key=True, autoincrement=True)
    quantity = Column(Float)
    code_product = Column(Float)
    id_sincronization_status = Column(Integer, ForeignKey('sincronization_status.id_sincronization_status'))
    id_product = Column(Integer, ForeignKey('company_product.id_product'))
    created_at = Column(DateTime, nullable=True, default=datetime.now())
    updated_at = Column(DateTime, nullable=True, default=datetime.now(), onupdate=datetime.now())

#    sincronization_status = relationship('SincronizationStatus')
#    product = relationship('CompanyProduct')

class CompanyUtilization(Base):
    __tablename__ = 'company_utilization'

    id_company_utilization = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(250))
    code = Column(String(250))
    id_company = Column(Integer, ForeignKey('company.id_company')) 
    id_sincronization_status = Column(Integer, ForeignKey('sincronization_status.id_sincronization_status'))
    created_at = Column(DateTime, nullable=True, default=datetime.now())
    updated_at = Column(DateTime, nullable=True, default=datetime.now(), onupdate=datetime.now())

#    company = relationship('Company')
#    sincronization_status = relationship('SincronizationStatus')

class CompanyHasUser(Base):
    __tablename__ = 'company_has_user'

    id_company_has_user = Column(Integer, primary_key=True, autoincrement=True)
    id_company = Column(Integer, ForeignKey('company.id_company'))
    id_user = Column(Integer, ForeignKey('user.id_user'))

#    company = relationship('Company')
#    user = relationship('User')

class BusinessPartner(Base):
    __tablename__ = 'business_partner'

    id_business_partner = Column(Integer, primary_key=True, autoincrement=True)
    razao_social = Column(String(450))
    nome_fantasia = Column(String(450))
    cnpj = Column(String(45), unique=True)
    inscricao_estadual = Column(String(45))
    inscricao_municipal = Column(String(45))
    cnae = Column(String(45))
    suframa = Column(String(45))
    regime_especial = Column(Integer)
    sugestao_limite_credito = Column(Float)
    email = Column(String(45))
    phone = Column(String(45))
    observation = Column(String(3000))
    id_address = Column(Integer, ForeignKey('address.id_address'))
    id_company = Column(Integer, ForeignKey('company.id_company'))
    id_sincronization_status = Column(Integer, ForeignKey('sincronization_status.id_sincronization_status'))
    created_at = Column(DateTime, nullable=True, default=datetime.now())
    updated_at = Column(DateTime, nullable=True, default=datetime.now(), onupdate=datetime.now())

#    address = relationship('Address')
#    company = relationship('Company')
#    sincronization_status = relationship('SincronizationStatus')

class SalesOrderRedespacho(Base):
    __tablename__ = 'sales_order_redespacho'

    id_sales_order_redespacho = Column(Integer, primary_key=True, autoincrement=True)
    cnpj = Column(String(45))
    nome_transportadora = Column(String(250))
    id_address = Column(Integer, ForeignKey('address.id_address'))
    created_at = Column(DateTime, nullable=True, default=datetime.now())
    updated_at = Column(DateTime, nullable=True, default=datetime.now(), onupdate=datetime.now())

#    address = relationship('Address')

class SalesOrder(Base):
    __tablename__ = 'sales_order'

    id_sales_order = Column(Integer, primary_key=True, autoincrement=True)
    have_redespacho = Column(Integer)
    data_lancamento = Column(DateTime)
    data_entrega = Column(DateTime)
    discount = Column(Float)
    observation = Column(String(3000))
    id_company = Column(Integer, ForeignKey('company.id_company'))
    id_business_partner = Column(Integer, ForeignKey('business_partner.id_business_partner'))
    id_sincronization_status = Column(Integer, ForeignKey('sincronization_status.id_sincronization_status'))
    id_company_payment_method = Column(Integer, ForeignKey('company_payment_method.id_company_payment_method'))
    id_company_payment_term = Column(Integer, ForeignKey('company_payment_term.id_company_payment_term'))
    id_company_utilization = Column(Integer, ForeignKey('company_utilization.id_company_utilization'))
    id_company_branch = Column(Integer, ForeignKey('company_branch.id_company_branch'))
    id_company_freight = Column(Integer, ForeignKey('company_freight.id_company_freight'))
    id_sales_order_redespacho = Column(Integer, ForeignKey('sales_order_redespacho.id_sales_order_redespacho'))
    created_at = Column(DateTime, nullable=True, default=datetime.now())
    updated_at = Column(DateTime, nullable=True, default=datetime.now(), onupdate=datetime.now())

#    company = relationship('Company')
#    business_partner = relationship('BusinessPartner')
#    sincronization_status = relationship('SincronizationStatus')
#    company_payment_method = relationship('CompanyPaymentMethod')
#    company_payment_term = relationship('CompanyPaymentTerm')
#    company_utilization = relationship('CompanyUtilization')
#    company_branch = relationship('CompanyBranch')
#    company_freight = relationship('CompanyFreight')
#    sales_order_redespacho = relationship('SalesOrderRedespacho')

class SalesOrderProduct(Base):
    __tablename__ = 'sales_order_product'

    id_product = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(250))
    name = Column(String(250))
    data_lancamento = Column(DateTime)
    data_entrega = Column(DateTime)
    discount_copy1 = Column(Float)
    weight = Column(Float)
    size = Column(Float)
    quantity = Column(Float)
    discount = Column(Float)
    price = Column(Float)
    estoque = Column(Float)
    id_sales_order = Column(Integer, ForeignKey('sales_order.id_sales_order'))
    created_at = Column(DateTime, nullable=True, default=datetime.now())
    updated_at = Column(DateTime, nullable=True, default=datetime.now(), onupdate=datetime.now())

#    sales_order = relationship('SalesOrder')
 