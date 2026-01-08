# Modelo alternativo para trabalhar com MySQL
# Este arquivo define os modelos SQLAlchemy compatíveis com a estrutura MySQL existente

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime, timezone

Base = declarative_base()

class Address(Base):
    __tablename__ = 'Address'

    IdAddress = Column('IdAddress', Integer, primary_key=True, autoincrement=True)
    Cep = Column('Cep', String(45))
    City = Column('City', String(250))
    Estate = Column('Estate', String(250))
    Adress = Column('Adress', String(245))  # Note: mantém o nome original com typo
    Number = Column('Number', Integer)
    Neighborhood = Column('Neighborhood', String(250))
    Complement = Column('Complement', String(250))
    CreatedAt = Column('CreatedAt', TIMESTAMP, default=datetime.now)
    UpdatedAt = Column('UpdatedAt', DateTime, default=datetime.now, onupdate=datetime.now)

class User(Base):
    __tablename__ = 'User'

    IdUser = Column('IdUser', Integer, primary_key=True, autoincrement=True)
    UserName = Column('UserName', String(250))
    Password = Column('Password', String(450))
    Email = Column('Email', String(250))
    Phone = Column('Phone', String(45), nullable=True)
    Token = Column('Token', String(5000), nullable=True)
    Address_IdAddress = Column('Address_IdAddress', Integer, ForeignKey('Address.IdAddress'), nullable=True)
    Active = Column('Active', Boolean, nullable=True)
    CreatedAt = Column('CreatedAt', TIMESTAMP, default=datetime.now)
    UpdatedAt = Column('UpdatedAt', DateTime, default=datetime.now, onupdate=datetime.now)

    # Relacionamento com Address
    address = relationship('Address', foreign_keys=[Address_IdAddress])

    # Propriedades para compatibilidade com o código existente
    @property
    def id_user(self):
        return self.IdUser
    
    @property
    def username(self):
        return self.UserName
    
    @property
    def password(self):
        return self.Password
    
    @property
    def email(self):
        return self.Email
    
    @property
    def phone(self):
        return self.Phone
    
    @property
    def token(self):
        return self.Token
    
    @property
    def active(self):
        return self.Active
    
    @property
    def created_at(self):
        return self.CreatedAt
    
    @property
    def updated_at(self):
        return self.UpdatedAt
