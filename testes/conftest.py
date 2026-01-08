"""
Configurações globais para os testes unitários.
Contém fixtures compartilhadas e configurações do pytest.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os

# Adicionar o diretório app ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from main import app
from database.db_models import Base
from dependencies import get_db
from database import db_models
from datetime import datetime, date

# Criar engine de teste usando SQLite em memória
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override da dependência de banco de dados para usar o banco de teste."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def test_db():
    """Fixture que cria um banco de dados de teste limpo para cada teste."""
    # Criar todas as tabelas
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    yield db
    
    db.close()
    # Limpar todas as tabelas após o teste
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Fixture que cria um cliente de teste com banco de dados isolado."""
    # Criar todas as tabelas
    Base.metadata.create_all(bind=engine)
    
    # Override da dependência de banco de dados
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Limpar após o teste
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_token():
    """
    Fixture que gera um token JWT válido para testes.
    Retorna um token mockado que pode ser usado nos headers das requisições.
    """
    # Token mockado para testes - na prática, seria gerado dinamicamente
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QHRlc3QuY29tIiwidXNlcm5hbWUiOiJ0ZXN0dXNlciIsImlkX3VzZXIiOjEsInJvbGUiOiJzdXBlcmFkbWluIiwiY29tcGFueV9pZCI6MSwiZXhwIjoxOTk5OTk5OTk5fQ.test_signature"


@pytest.fixture
def auth_headers(mock_token):
    """Fixture que retorna headers de autenticação para requisições autenticadas."""
    return {"Authorization": f"Bearer {mock_token}"}


@pytest.fixture
def superadmin_user(test_db):
    """Fixture que cria um usuário superadmin no banco de testes."""
    user = db_models.User(
        username="superadmin",
        email="superadmin@gmail.com",
        password="123123123",
        phone="11999999999",
        role="superadmin",
        company_id=None,
        active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def admin_user(test_db, mock_company):
    """Fixture que cria um usuário admin no banco de testes."""
    user = db_models.User(
        username="admin",
        email="admin@test.com",
        password="hashedpassword",
        phone="11988888888",
        role="admin",
        company_id=mock_company.id_company,
        active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def regular_user(test_db, mock_company):
    """Fixture que cria um usuário regular no banco de testes."""
    user = db_models.User(
        username="regularuser",
        email="user@test.com",
        password="hashedpassword",
        phone="11977777777",
        role="user",
        company_id=mock_company.id_company,
        active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def mock_address(test_db):
    """Fixture que cria um endereço mockado no banco de testes."""
    address = db_models.Address(
        cep="01310100",
        city="São Paulo",
        estate="SP",
        adress="Av. Paulista",
        number=1000,
        neighborhood="Bela Vista",
        complement="Sala 101"
    )
    test_db.add(address)
    test_db.commit()
    test_db.refresh(address)
    return address


@pytest.fixture
def mock_company(test_db, mock_address):
    """Fixture que cria uma empresa mockada no banco de testes."""
    company = db_models.Company(
        razao_social="Empresa Teste LTDA",
        nome_fantasia="Empresa Teste",
        cnpj="12345678000100",
        email="contato@empresa.com",
        phone="1130001000",
        id_address=mock_address.id_address,
        active=True
    )
    test_db.add(company)
    test_db.commit()
    test_db.refresh(company)
    return company


@pytest.fixture
def mock_branch(test_db, mock_company):
    """Fixture que cria uma filial mockada no banco de testes."""
    branch = db_models.CompanyBranch(
        name="Filial Centro",
        code="FIL001",
        id_company=mock_company.id_company
    )
    test_db.add(branch)
    test_db.commit()
    test_db.refresh(branch)
    return branch


@pytest.fixture
def mock_business_partner(test_db, mock_address, mock_company):
    """Fixture que cria um parceiro de negócios mockado no banco de testes."""
    partner = db_models.BusinessPartner(
        razao_social="Parceiro Teste LTDA",
        nome_fantasia="Parceiro Teste",
        cnpj="98765432000199",
        inscricao_estadual="123456789",
        inscricao_municipal="987654321",
        cnae="4712100",
        suframa="",
        regime_especial=0,
        sugestao_limite_credito=10000.00,
        email="parceiro@teste.com",
        phone="1130002000",
        observation="Parceiro para testes",
        id_address=mock_address.id_address,
        id_company=mock_company.id_company
    )
    test_db.add(partner)
    test_db.commit()
    test_db.refresh(partner)
    return partner


@pytest.fixture
def mock_freight(test_db, mock_company):
    """Fixture que cria um frete mockado no banco de testes."""
    freight = db_models.CompanyFreight(
        name="Frete Normal",
        code="FRT001",
        id_company=mock_company.id_company
    )
    test_db.add(freight)
    test_db.commit()
    test_db.refresh(freight)
    return freight


@pytest.fixture
def mock_payment_method(test_db, mock_company):
    """Fixture que cria um método de pagamento mockado no banco de testes."""
    payment_method = db_models.CompanyPaymentMethod(
        name="Cartão de Crédito",
        code="CC001",
        id_company=mock_company.id_company
    )
    test_db.add(payment_method)
    test_db.commit()
    test_db.refresh(payment_method)
    return payment_method


@pytest.fixture
def mock_payment_term(test_db, mock_company):
    """Fixture que cria uma condição de pagamento mockada no banco de testes."""
    payment_term = db_models.CompanyPaymentTerm(
        name="30 dias",
        code="30D",
        id_company=mock_company.id_company
    )
    test_db.add(payment_term)
    test_db.commit()
    test_db.refresh(payment_term)
    return payment_term


@pytest.fixture
def mock_utilization(test_db, mock_company):
    """Fixture que cria uma utilização mockada no banco de testes."""
    utilization = db_models.CompanyUtilization(
        name="Revenda",
        code="REV001",
        id_company=mock_company.id_company
    )
    test_db.add(utilization)
    test_db.commit()
    test_db.refresh(utilization)
    return utilization


@pytest.fixture
def mock_sales_order(test_db, mock_company, mock_business_partner, mock_branch, 
                     mock_freight, mock_payment_method, mock_payment_term, 
                     mock_utilization, superadmin_user):
    """Fixture que cria um pedido de venda mockado no banco de testes."""
    sales_order = db_models.SalesOrder(
        Redespacho=0,
        DataLancamento=date(2026, 1, 8),
        DataEntrega=date(2026, 1, 15),
        Discount=5.0,
        Observation="Pedido de teste",
        CompanyId=mock_company.id_company,
        BusinessPartnerId=mock_business_partner.IdBusinessPartner,
        PaymentMethodId=mock_payment_method.IdCompanyPaymentMethod,
        PaymentTermId=mock_payment_term.IdCompanyPaymentTerm,
        UtilizationId=mock_utilization.IdCompanyUtilization,
        BranchId=mock_branch.IdCompanyBranch,
        FreightId=mock_freight.IdCompanyFreight,
        CreatedByUserId=superadmin_user.id_user
    )
    test_db.add(sales_order)
    test_db.commit()
    test_db.refresh(sales_order)
    return sales_order


# ============================================================================
# DADOS MOCKADOS PARA PAYLOADS DE REQUISIÇÕES
# ============================================================================

@pytest.fixture
def address_payload():
    """Payload mockado para criação de endereço."""
    return {
        "cep": "01310200",
        "city": "São Paulo",
        "estate": "SP",
        "adress": "Rua Augusta",
        "number": 500,
        "neighborhood": "Consolação",
        "complement": "Apto 10"
    }


@pytest.fixture
def company_payload(address_payload):
    """Payload mockado para criação de empresa."""
    return {
        "CompanyBase": {
            "razao_social": "Nova Empresa LTDA",
            "nome_fantasia": "Nova Empresa",
            "cnpj": "11223344000155",
            "email": "nova@empresa.com",
            "phone": "1140001000",
            "id_address": None,
            "active": True
        },
        "AddressBase": address_payload
    }


@pytest.fixture
def branch_payload(mock_company):
    """Payload mockado para criação de filial."""
    return {
        "name": "Nova Filial",
        "code": "NFIL001",
        "id_company": mock_company.id_company
    }


@pytest.fixture
def business_partner_payload(mock_company):
    """Payload mockado para criação de parceiro de negócios."""
    return {
        "razao_social": "Novo Parceiro LTDA",
        "nome_fantasia": "Novo Parceiro",
        "cnpj": "55667788000111",
        "inscricao_estadual": "111222333",
        "inscricao_municipal": "444555666",
        "cnae": "4711300",
        "suframa": "",
        "regime_especial": 0,
        "sugestao_limite_credito": 5000.00,
        "email": "novoparceiro@teste.com",
        "phone": "1150001000",
        "observation": "Novo parceiro para testes",
        "id_address": {
            "cep": "04567890",
            "city": "Rio de Janeiro",
            "estate": "RJ",
            "adress": "Rua Copacabana",
            "number": 200,
            "neighborhood": "Copacabana",
            "complement": None
        },
        "id_company": mock_company.id_company
    }


@pytest.fixture
def freight_payload(mock_company):
    """Payload mockado para criação de frete."""
    return {
        "name": "Frete Expresso",
        "code": "FRTEXP",
        "id_company": mock_company.id_company
    }


@pytest.fixture
def payment_method_payload(mock_company):
    """Payload mockado para criação de método de pagamento."""
    return {
        "name": "PIX",
        "code": "PIX001",
        "id_company": mock_company.id_company
    }


@pytest.fixture
def payment_term_payload(mock_company):
    """Payload mockado para criação de condição de pagamento."""
    return {
        "name": "60 dias",
        "code": "60D",
        "id_company": mock_company.id_company
    }


@pytest.fixture
def utilization_payload(mock_company):
    """Payload mockado para criação de utilização."""
    return {
        "name": "Industrialização",
        "code": "IND001",
        "id_company": mock_company.id_company
    }


@pytest.fixture
def user_payload():
    """Payload mockado para criação de usuário."""
    return {
        "username": "novousuario",
        "email": "novousuario@teste.com",
        "password": "senha123456",
        "phone": "11966666666"
    }


@pytest.fixture
def sales_order_payload(mock_business_partner, mock_branch):
    """Payload mockado para criação de pedido de venda."""
    return {
        "redespacho": 0,
        "data_entrega": "2026-01-20",
        "discount": 10.0,
        "observation": "Novo pedido de teste",
        "id_business_partner": mock_business_partner.IdBusinessPartner,
        "id_company_branch": mock_branch.IdCompanyBranch
    }
